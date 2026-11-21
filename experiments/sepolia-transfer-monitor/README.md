# Sepolia 转账监控 · 浏览器复现

在 Lasna 部署监控合约，观察 Ethereum Sepolia 的公开测试 LINK 转账。满足金额条件的第一笔转账会写入计数和源交易哈希，随后自动取消订阅。

- [实测交易与 Mermaid 工作流](../../assignments/d3-sepolia-transfer-monitor.md)
- [可直接粘贴的提交文本](../../assignments/d3-sepolia-transfer-monitor-submission.txt)

## 1. 准备 MetaMask 和 lREACT

在 MetaMask 选择 **Reactive Lasna**，链 ID 为 `5318007`。钱包余额需要覆盖部署 gas 和给合约的 `0.025 lREACT` 预充值。在此配置下，源事件来自 Ethereum Sepolia 的公开交易。可以在浏览器查看源链回执。[Lasna 网络和领币方式](https://dev.reactive.network/reactive-mainnet)

## 2. 编译和部署

1. 在 Remix 打开合约文件。选择 Solidity **0.8.29**，EVM Version 选 **Cancun**，Optimizer 设置为 **200 runs** 并编译。[在 Remix 打开](https://app.remix.live/#url=https://github.com/sunshineluyao/reactive-builder-camp-2026/blob/main/experiments/sepolia-transfer-monitor/remix/SepoliaTransferMonitor.sol)
2. 在 **Deploy & Run Transactions** 选择 **Browser Extension**，连上 MetaMask 测试账户，核对网络为 Lasna。
3. 选择 **BoundedTransferMonitor**，填入下表参数，将 Value 单位设为 **wei**，确认部署交易。部署完成后记录合约地址。

| 字段 | 本实验参数 |
| --- | --- |
| token_ | `0x779877A7B0D9E8603169DdbD7836e478b4624789`，Ethereum Sepolia 的测试 LINK |
| minimumAmount_ | `1`，一个最小单位，计入所有非零转账 |
| maximumTransfers_ | `1`，计满一次即退订 |
| Value | `25000000000000000`，即 `0.025 lREACT` |

若实验使用另一个 Ethereum Sepolia ERC-20，可将 `token_` 换成它的合约地址，并按该代币的 decimals 换算 `minimumAmount_`。[Chainlink 测试代币地址](https://docs.chain.link/resources/link-token-contracts)

## 3. 等待转账并核验

1. 部署后，等待该 LINK 合约的下一笔非零 `Transfer`。在 Lasna Reactscan 打开监控合约的地址页，从 **Reactive Executions** 打开本次 `react()` 的交易。
2. 查看交易的 `TransferCounted` 日志。它记录了 Ethereum Sepolia 的源交易哈希、发送方、接收方、转账值和计数。同一笔 Lasna 交易也记录了停止监控。
3. 在合约读取面板核对 `count() = 1`、`subscribed() = false`。将收集到的 **Lasna 合约地址页** 和 **Lasna react 交易页** 两个链接填到作业提交框，再附一句订阅条件。

## 合约如何过滤

构造函数订阅 `(11155111, LINK 合约地址, Transfer topic0)`，其余三个 topic 使用 `REACTIVE_IGNORE`。`react()` 使用 `onlySystem`，校验来源、合约地址和 ERC-20 日志结构后解码金额。符合条件就发出 `TransferCounted`。计满一次时用相同条件调用 `SYSTEM.unsubscribe()`。[Omni Xfers 示例](https://github.com/Reactive-Network/reactive-smart-contract-demos/blob/d1d854b4d8ded359d73dcd85cda882ec5c9aab49/src/micro-demos/Xfers.sol) · [Reactive 合约文档](https://dev.reactive.network/reactive-contracts)
