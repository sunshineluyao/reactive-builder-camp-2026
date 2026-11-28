# 场景小实验 · 两次 Cron100 回调后停止

[English](d5-cron100.en.md) · **简体中文**

选择 **A. 定时执行**。Lasna 上的 `BoundedCron` 订阅 `Cron100`，在两个新的 Cron 区块各请求一次回调。Base Sepolia 上的 `CronReceiver` 记录运行序号、源 Cron 区块号和 `block.timestamp`。

## 链上提交凭证

| 项目 | 凭证 |
| --- | --- |
| Lasna 定时合约 `BoundedCron` | [0x201E13106fDf34Fb8FEc9174D4e3DFd95b63CC2b](https://lasna.reactscan.net/address/0x201E13106fDf34Fb8FEc9174D4e3DFd95b63CC2b) · [部署交易](https://lasna.reactscan.net/tx/0xb685edbf16e21a5ffa06bc1614fec32cf4b549a8f7498d5333234a4398370e5b) |
| Base Sepolia 接收合约 `CronReceiver` | [0x1F6C0517c73b8E36fEfe298dBb099a5377D9AE21](https://sepolia.basescan.org/address/0x1F6C0517c73b8E36fEfe298dBb099a5377D9AE21) · [部署交易](https://sepolia.basescan.org/tx/0xf2539ab5eed34d23ab9d12590699cf9b15dd4be20e4f60862b170099f6cd44e6) |
| 启动 Cron100 | [Lasna 启动交易](https://lasna.reactscan.net/tx/0x2fcbbbb6e6b459620b412ac9f2dcfe75edcc8b009d57fcb03de02d1eee8c9d2d) |
| 第 1 次触发 · Lasna 区块 8797900 | [Lasna 触发](https://lasna.reactscan.net/tx/0xcf027168df6970bbf14de08b5f3231f2007ef2da8254d7452480cec1de52f52c) · [Base Sepolia 回调](https://sepolia.basescan.org/tx/0x5e81250cfe684865fb933836223078ce9d18add2f83d71b4fa9f0dbdd255e02f) · 16:31:47（新加坡时间） |
| 第 2 次触发 · Lasna 区块 8798000 | [Lasna 触发](https://lasna.reactscan.net/tx/0x18357019ea70c69ad627fbb2f7980459b2c013eff35540acc8a3abdd0872feb6) · [Base Sepolia 回调](https://sepolia.basescan.org/tx/0x71358f482aeaeade2d6de0dee2d57c386de71f702d879949dfebc5a83fc6716e) · 16:33:34（新加坡时间） |
| 自动停止 | [第二次请求和 `CronStopped` 事件](https://lasna.reactscan.net/tx/0x18357019ea70c69ad627fbb2f7980459b2c013eff35540acc8a3abdd0872feb6) |

2026 年 11 月 20 日核验了两组交易回执。两条 Base Sepolia 回调记录的区块源分别与 Lasna 的第 1、2 次请求匹配，记录间隔为 107 秒。最终 `attempts() = 2`，`stopped() = true`，`subscribed() = false`。

本次通过 [OpenFaucet](https://openfaucet.org/base-sepolia) 领取 [0.014 Base Sepolia 测试 ETH](https://sepolia.basescan.org/tx/0xbaf09a3b591d8bad4299da988656aee1c92a5e703974024428c5437564bd57f4)，再经 [Reactive 官方水龙头的兑换交易](https://sepolia.basescan.org/tx/0xd22bdf121fa66fece4e0820052803afd5621ad133eeac5e5166709ba0ed3579b) 获得 1 lREACT。

Solidity 0.8.29 编译通过，6 项 Foundry 测试通过。

## 如何防止无限执行或耗尽余额

Lasna 只处理新的 Cron 区块，同一区块的重复通知不增加次数。每次请求占用一个名额，请求失败也计入。第二次尝试后合约停止发出新请求，并用原订阅条件调用 `unsubscribe`。余额低于设定的底线时提前停止。若取消订阅失败，本地停止状态仍有效，管理员可调用 `stop()` 完成取消。

两条链的费用分别从预先划定的测试预算支付。每次回调的 gas 上限是 300,000。Base Sepolia 接收端校验官方回调代理和授权的 Lasna 合约，每个序号只写入一次，并用 `block.timestamp` 记录执行时间。

## 提交和复现

- [提交框可粘贴的纯文本](d5-cron100-submission.txt)含合约地址、两次触发的原始交易 URL 和防失控说明。
- [浏览器复现指南](../experiments/cron100/README.md)含 MetaMask 领币、Remix 部署、GitHub Actions 开发者练习和两条测试网间的资金流图。
- [分类术语表](../experiments/cron100/GLOSSARY.md)汇集所用网络、费用、合约、证据和开发工具的定义与核验来源。
- [合约源码](../experiments/cron100/src/BoundedCron.sol) · [测试代码](../experiments/cron100/test/BoundedCron.t.sol)

## 参考资料

- [Cron100 与 Omni 订阅](https://dev.reactive.network/reactive-contracts#cron)
- [Base Sepolia 回调代理及链 ID](https://dev.reactive.network/origins-and-destinations#testnet-chains)
- [回调费用及交易链路查询](https://dev.reactive.network/economy#inspecting-callbacks)
- [Lasna 测试币水龙头](https://dev.reactive.network/reactive-mainnet#reactive-faucet)
- [Lasna 浏览器](https://lasna.reactscan.net/) · [Base Sepolia 浏览器](https://sepolia.basescan.org/)
