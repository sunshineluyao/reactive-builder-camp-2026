# Would you page the treasury?

**English** · [简体中文](README.zh-CN.md)

A controlled Sepolia quote fell to **0.9930 USDT per USDC**. Reactive routed it to Base. The original run kept the alert and withheld its score. We subsequently recovered market observations from before the signed event. The same frozen model ran on those observations and recommended **continue observing**. The treasury reviewer retains the decision. [Three receipts](../public-run.json) · [Computed decision and model fingerprint](public-assessment.json)

| Evidence available by 13:38:12 UTC on November 27, 2026 | Observation | What it contributes |
|---|---:|---|
| [Bitstamp USDC/USD](https://www.bitstamp.net/api/v2/ohlc/usdcusd/?step=60&limit=15&end=1795786620) | $0.999870 | A dollar reference for USDC. The traded minute closed at 13:38:00. |
| [Coinbase Exchange USDT-USD](https://api.exchange.coinbase.com/products/USDT-USD/candles?start=2026-11-27T13:23:00Z&end=2026-11-27T13:37:00Z&granularity=60) | $0.998720 | A separately traded dollar reference for USDT with the same close boundary. |
| [Binance USDCUSDT](https://data-api.binance.vision/api/v3/klines?symbol=USDCUSDT&interval=1m&startTime=1795785780000&endTime=1795786679999&limit=15) | 0 of 15 prior closes | None confirmed a drop greater than 50 bp. The largest deviation in the two USD references was 12.8 bp. |

The test publisher supplied the 70 bp fall. The three venues supplied external prices. Both reference bars closed 12 seconds before the event. Each candle is timestamped at the end of its minute. The acquisition script excludes open and zero-volume candles. The archive documents market time and does not establish when an exchange first made a bar available. The frozen model's output is a review score, without probability calibration. [Model inputs](public-context.json) · [Exchange responses, request URLs and SHA-256 hashes of canonical JSON](provider-responses.json) · [Frozen model card](../../model/MODEL_CARD.en.md)

## What did triage change?

We replayed every available one-minute Kraken USDC/USDT close from 13:00 through 13:59 UTC on March 10–15, 2023, spanning the USDC banking stress and recovery, and on the public demo date. We used the same Bitstamp and Coinbase USD markets as inputs. Kraken has an archive throughout this interval, including before Binance resumed trading the pair on March 11. The model weights and training policy were frozen before this comparison. [Issuer’s account of the bank event](https://www.circle.com/pressroom/3-3-billion-of-usdc-reserve-risk-removed-dollar-de-peg-closes) · [Per-day results](comparison.json)

Out of **420 scheduled minutes**, 402 had pair trades. Of 231 strict threshold crossings, 208 had trades in all five following minutes. We classified a crossing as persistent if at least three of those five closes remained more than 50 bp from parity in the original direction. The model and reference rule received only inputs available through the trigger minute. We excluded 23 crossings with incomplete follow-up from all three policies.

| On the same 208 crossings | Referrals | Referrals followed by short-lived moves | Persistent moves assigned to observation | Abstentions (persistent) |
|---|---:|---:|---:|---:|
| Refer every crossing | 208 | 14 | 0 | 0 |
| Written rule used to label training data | 202 | 12 | 3 | 1 (1) |
| Frozen neural network | 200 | 10 | 3 | 1 (1) |

The model referred two fewer short-lived moves than the written rule. Against referring every crossing it saved eight referrals, while assigning three persistent moves to observation and withholding a decision on a fourth. Of the 208 windows, 194 were persistent. Neighboring windows overlap. These counts measure workload against a five-minute price proxy. They cannot establish reduced losses, independent incident-level accuracy or volunteer performance. A treasury can choose the all-crossings rule if missing a persistent move is more costly than an additional review.

## Reproduce or try the decision

Run from `track3/` with Python 3 and Node.js 18 or later. The first two commands use only the checked-in files. The last one verifies public chain inclusion, requests exchange records for the signed event and runs inference without a wallet. With missing evidence, the triage returns `insufficient`. With an unverified chain event, the command stops before scoring.

```bash
python3 scripts/market_evidence.py
python3 scripts/market_benchmark.py
python3 scripts/market_evidence.py --live
```

The live command also accepts `--run PATH_TO_PUBLIC_MANIFEST`. For a fresh acquisition, each script supports `--refresh`. The comparison rebuilds minute closes from Kraken trade IDs and verified page cursors. [Acquisition, timestamp alignment and inference](../../scripts/market_evidence.py) · [Historical comparison](../../scripts/market_benchmark.py) · [Archived comparison responses](comparison-sources.json.gz)

**Treasury reviewer task.** Open the public reviewer from the root README. Find the Base callback, identify the two external price sources, then choose whether to escalate. Compare your choice with the model and inspect the three underlying exchange links. The exercise runs in your browser and collects no participant data. Human usability has yet to be measured.
