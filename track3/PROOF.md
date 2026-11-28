# Reactive PegPulse in one transaction trail

**English** · [简体中文](PROOF.zh-CN.md)

**Would you page the treasury over a 0.9930 quote?** The contract recorded one alert on Base. At signing the model withheld its score. With archived market prices for that instant, it recommended **continue observing**. The quote was simulated and the three transactions settled on public testnets.

[Watch the 2:30 competition film](https://cdn.jsdelivr.net/gh/sunshineluyao/reactive-builder-camp-2026@e3793927f18683f811bf17db4ec07589045ea14d/track3/video/public/demo.mp4) · [Open the interactive reviewer](https://rawcdn.githack.com/sunshineluyao/reactive-builder-camp-2026/e3793927f18683f811bf17db4ec07589045ea14d/track3/review/index.html?lang=en)

| November 27, 2026 (UTC) | What happened | Open the receipt |
|---|---|---|
| 13:38:12 · Ethereum Sepolia | QuoteSource published 0.9930 USDT per USDC. The source event is log 2. | [PriceObserved](https://sepolia.etherscan.io/tx/0xd97a9579a96a20c9868dd7f759079975e2ff1603eb903e42d3fd5ddfbbcc6604) |
| 13:38:12 · Reactive Lasna | ReactiveAlert recognized the publisher and the 70 bp deviation, checked for a duplicate and requested a callback. | [QuoteRouted](https://lasna.reactscan.net/tx/0x63639779506a135ff8cba06c4d8aff5230d029aed5dc781f8f902868f54e8d27) |
| 13:38:14 · Base Sepolia | AlertSink recorded the alert, including its source transaction and source log index. | [PriceDeviation](https://sepolia.basescan.org/tx/0x5e2a48caaf7ab64dd3f25c4f4b804cf30d09aabc6f885efb44033b91ce3ce602) |

The event ID starts `0x38b66270` and ends `d38ac554`. The Base receipt’s own log index is **0**. Inside that event, the recorded **source** log index is **2**. [Exact event ID, contract addresses and raw receipts](evidence/public-run.json)

## Make the decision

The test quote was 70 basis points below parity. The USDC/USD close on Bitstamp was **$0.999870** and USDT/USD on Coinbase was **$0.998720**. Both minute bars closed 12 seconds before the signed quote. **Zero of 15** preceding Binance USDC/USDT closes crossed the lower threshold. Choose what you would do, then open the explanation.

<details><summary><strong>I would keep monitoring.</strong></summary>

That agrees with the frozen model. Independent prices did not corroborate a 70 bp fall. The alert remains visible on Base, and a reviewer can escalate if new evidence arrives.

</details>

<details><summary><strong>I would escalate for a human review.</strong></summary>

That is a defensible choice for a treasury with a high cost of missed incidents. The model recommended observation here. In the historical comparison it also assigned three persistent crossings to observation and abstained on one more. A reviewer can override its recommendation.

</details>

[See timestamped model inputs](evidence/market/public-context.json) · [Open the computed result](evidence/market/public-assessment.json) · [Compare the model with two simpler rules](evidence/market/README.md)

## Repeat the check

From `track3/`, run `python3 scripts/market_evidence.py --live`. This read-only command verifies the receipts against public chains, fetches the market prices and runs the frozen model. The interactive reviewer shows a checked local copy of the published receipts and offers a separate live RPC check. Its host may ask first-time visitors to select **Open the page**. No wallet is required. [Installation and full reproduction](README.en.md)
