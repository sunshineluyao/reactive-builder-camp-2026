# Model card · Stablecoin alert triage

**English** · [简体中文](MODEL_CARD.md)

A destination `PriceDeviation` records the USDC/USDT quote. The browser passes that event and a matching evidence packet to an off-chain model. Its decision places the alert in human review (`escalate`) or continued observation (`observe`). The evidence gate can return `insufficient` with the missing requirements. The wallet signs transactions and the contracts process on-chain events.

## Inputs and provenance

An alert contains `evidenceId`, `observedAt` and `priceBps`. The integer 10000 means 1 USDT per USDC and 9930 means 0.9930. Timestamps use Unix seconds. External JSON requires `schema: "stablecoin-evidence/v1"`, `pair: "USDC/USDT"` and an `alertId` that exactly matches the event. The example matches the local EVM replay and contains synthetic dollar prices and pair history. [Example packet](context-example.json)

| Field | Units and requirements |
| --- | --- |
| `history[]` | 2–24 USDC/USDT observations preceding the event. Each has integer `priceBps`, `observedAt` and `source`. Times strictly increase. Lookback is at most 900 seconds and the newest sample is at most 300 seconds old. |
| `references["USDC/USD"]` and `references["USDT/USD"]` | Each dollar quote is independent of the pool and contains integer `usdMicros`, `observedAt` and `source`. One dollar is 1000000. Sample time must fall in the 300 seconds up to and including the event. |
| `provenance` | Use `synthetic` for constructed data, with a `fixture:` identifier or HTTPS source. `observed` means the provider declares a measurement and must give a checkable HTTPS source. Reviewers assess authenticity and independence. The model reads the supplied JSON locally. |

## Decisions and interpretation

1. At or within 50 bp of parity, return `observe / no_threshold_crossing`. A score requires a crossing and valid evidence. Missing, stale or mismatched inputs produce insufficient evidence with a reason code and explanations in both languages.
2. Four features describe the absolute pair deviation in bp, the maximum absolute USD deviation of either asset, the ratio of the USD references in the direction of the pair’s move, and the fraction of prior samples beyond 50 bp in that direction. Scale by 200, 150, 150 and 1 respectively and clip to [0, 1].
3. Frozen network `sc-triage-mlp-v1` has four inputs, six tanh hidden units and one sigmoid output. A raw score of at least 0.5 recommends escalation. Lower scores stay under observation. Real-market probability calibration remains open. The result includes features, version, sources and times. When the evidence gate decides, `inferenceRan` is false and `score` is null.

Replay these scenarios against the same 0.9930 event. Switching scenarios creates no new transaction.

| Synthetic scenario | USD evidence and history | Result |
| --- | --- | --- |
| `corroborated` | USDC $0.9904, USDT $1.0001, and three preceding quotes beyond the threshold in the same direction | Escalate |
| `pool-only` | USDC $0.9999, USDT $1.0001, and three preceding quotes inside the band | Observe |
| `missing` or `stale` | USDT/USD missing or sampled 20 minutes before the event | Insufficient evidence |

One test keeps the event and all three out-of-band history points fixed. Changing only the USD references to $0.9999 and $1.0001 changes escalation to observation. [Model test](../tests/test_model.py)

## Training and validation

Seed 72517 initializes the network. Training minimizes binary cross-entropy for 70 epochs on 1,200 synthetic samples covering four regimes: both dollar prices near parity, mainly USDC moving, mainly USDT moving, or both moving. The labeling rule escalates at a maximum USD deviation of at least 85 bp. It also escalates at 38 bp or more if the directional reference ratio deviates by at least 26 bp and persistence is at least 0.4. Runtime inference uses learned weights.

On 400 held-out synthetic samples from the same distribution with a separate seed, the frozen model agreed with the labeling rule 383 times (95.75%). This measures agreement with the synthetic rule. In a separate seven-window comparison of historical market prices, the model referred 200 of 208 crossings. The written training policy referred 202 on the same inputs. Real treasury outcomes and generalization to other markets remain unmeasured. [Market comparison, misses and abstentions](../evidence/market/README.md)

From `track3/`, use Python 3 and Node.js. Tests compare preprocessing, decisions, features and scores in the two implementations on fixture and randomized inputs. Retraining checks both weight files byte for byte.

```sh
python3 model/reference.py model/cases.json
python3 model/train.py --output /tmp/reactive-triage-weights
python3 -m unittest discover -s tests -p 'test_model.py' -v
```

The browser loads `model/weights.js`, then `model/runtime.js`, and calls `StablecoinAI.assess(alert, context)`. Use `StablecoinAI.demoContext(alert, "corroborated")` for synthetic evidence tied to the event. For an observed replay, import evidence from the event’s actual time.
