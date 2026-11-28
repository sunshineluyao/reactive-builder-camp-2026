# Deploy a Sepolia transfer monitor in a browser

**English** · [简体中文](README.md)

Use the test LINK token on Ethereum Sepolia as the event source and deploy the monitor on Lasna. When the first positive transfer matches, the monitor records its source transaction hash and count, then unsubscribes.

- [Completed on-chain run](../../assignments/d3-sepolia-transfer-monitor.en.md)
- [Copy-ready submission](../../assignments/d3-sepolia-transfer-monitor-submission.en.txt)

## 1. Prepare MetaMask and lREACT

Select **Reactive Lasna** (5318007). Allow for deployment gas and the 0.025 lREACT contract deposit. The source is a public Ethereum Sepolia transaction, which can be checked in its explorer. [Network and faucet guide](https://dev.reactive.network/reactive-mainnet)

## 2. Compile and deploy

1. Open the contract in Remix. Compile with Solidity **0.8.29**, **Cancun** and **200 optimizer runs**. [Open in Remix](https://app.remix.live/#url=https://github.com/sunshineluyao/reactive-builder-camp-2026/blob/main/experiments/sepolia-transfer-monitor/remix/SepoliaTransferMonitor.sol)
2. Under **Deploy & Run Transactions**, select **Browser Extension** and connect the test account in MetaMask. Check that the selected network is Lasna.
3. Choose **BoundedTransferMonitor**, enter the following constructor arguments, set the Value unit to **wei**, confirm deployment, and record the address.

| Field | Experiment value |
| --- | --- |
| token_ | `0x779877A7B0D9E8603169DdbD7836e478b4624789`, test LINK on Ethereum Sepolia |
| minimumAmount_ | `1`, the smallest token unit, to count all nonzero transfers |
| maximumTransfers_ | `1`, unsubscribe after the first match |
| Value | `25000000000000000`, equal to 0.025 lREACT |

For another Ethereum Sepolia ERC-20, substitute its address and convert the threshold using that token’s decimals. [Chainlink test tokens](https://docs.chain.link/resources/link-token-contracts)

## 3. Wait for a transfer and verify

1. Wait for the next positive LINK Transfer. Open the monitor’s Lasna Reactscan address and select the `react()` transaction under **Reactive Executions**.
2. Inspect `TransferCounted`. It records the source hash, sender, recipient, value and count. The same Lasna transaction records unsubscription.
3. Check `count() = 1` and `subscribed() = false`. Submit the Lasna address link, Lasna execution link and a sentence describing the filter.

## How the filter works

The constructor subscribes to chain 11155111, the LINK address and the Transfer topic0, with `REACTIVE_IGNORE` for three remaining topics. `onlySystem` protects `react()`. It checks the source, token and ERC-20 log layout before decoding the amount. It emits `TransferCounted` on a match and calls `SYSTEM.unsubscribe()` with the original filter at the limit. [Omni Xfers example](https://github.com/Reactive-Network/reactive-smart-contract-demos/blob/d1d854b4d8ded359d73dcd85cda882ec5c9aab49/src/micro-demos/Xfers.sol) · [Reactive contracts](https://dev.reactive.network/reactive-contracts)
