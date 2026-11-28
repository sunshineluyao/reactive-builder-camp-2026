# Project direction · Cross-chain stablecoin alerts and evidence review

**English** · [简体中文](d6-project-direction.md)

**Stablecoin Risk Alerts with Verifiable Cross-Chain Evidence**

## 1. Use case

When the Ethereum Sepolia test contract emits `PriceObserved` and the simulated USDC/USDT quote deviates by more than 0.5% from parity, Reactive Lasna requests a Base Sepolia callback. The resulting `PriceDeviation` alert retains the source hash and log index.

## 2. Track 3 · Reactive Meets AI

The proposed off-chain workflow reads the source evidence, recent pair history and contemporaneous USD references, then labels the alert for escalation, observation or insufficient evidence. The design envisages Reactive MCP for transaction traces and optional Aave MCP lending context such as USDC and USDT reserve liquidity and rates. Review priority is evaluated as the alert arrives and the page cites the evidence used.

## 3. Users and scenario

DAO treasury and DeFi risk teams need to align an unusual DEX quote with explorer evidence and contemporary USD prices. Displaying quotes, timestamps, provenance and verification helps distinguish a transient pool spread from an event worth investigating.

## 4. Minimum demo by the end of week two

Before November 29, demonstrate Ethereum Sepolia → Reactive Lasna → Base Sepolia → the off-chain review queue. Use a fixed sequence of simulated quotes.

| Input | Expected observation |
| --- | --- |
| Test quote 0.999 | Source event remains, with no destination alert. |
| Test quote 0.993 with complete references | One Base alert. Show the model decision and three transaction hashes. |
| Test quote 0.993 with missing USD references | The destination alert remains verifiable and AI reports insufficient evidence. |

Label simulated quotes, sources and observation times. Include addresses, explorer links, reproduction steps and a demo under three minutes.

## 5. Team plan

The original plan was a solo entry open to collaborators. Sunshine would own the use case, risk definition, contract integration, AI review and demo. If others joined, roles could cover contracts and observation, data and AI, or frontend accessibility. Credit confirmed contributors.

## References

- [Day 1 use case](https://github.com/sunshineluyao/reactive-builder-camp-2026/blob/main/assignments/d1-use-case.en.md)
- [Reactive Omni Buildathon rules](https://blog.reactive.network/reactive-omni-buildathon-thirty-days-to-find-out-what-one-second-buys/)
- [Supported networks](https://dev.reactive.network/origins-and-destinations)
- [Reactive MCP tools](https://dev.reactive.network/reactive-mcp)
- [Aave MCP tools](https://aave.com/docs/mcp/tools)
