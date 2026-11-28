# 项目方向卡 · 稳定币跨链告警与证据核验

[English](d6-project-direction.en.md) · **简体中文**

**Stablecoin Risk Alerts with Verifiable Cross-Chain Evidence**

## 1. 一句话用例

当 Ethereum Sepolia 上的测试报价合约发出 `PriceObserved` 事件且 USDC/USDT 模拟报价偏离 1:1 超过 0.5% 时，Reactive Lasna 请求回调，在 Base Sepolia 记录 `PriceDeviation` 告警并保留源链交易哈希和日志索引。

## 2. 赛道 3 · Reactive Meets AI

Base Sepolia 告警一到，链下 AI 就读取源交易证据、近期报价走势和同一时点的美元参考数据，将告警标为「升级复核」「继续观察」或「证据不足」，并更新人工复核队列。Reactive MCP 提供交易链路证据。Aave MCP 提供可选的借贷市场背景，例如 USDC 与 USDT 储备的可用流动性和利率。风险判断在告警到达时运行，并在页面上引用用到的证据。

## 3. 目标用户和场景

目标用户是需要核对跨链稳定币敞口的 DAO 财库及 DeFi 风控人员。收到单池报价异常后，他们需要把 DEX 报价、区块浏览器和美元参考价对在同一时点，判断是否值得跟进。页面显示报价、数据时间、来源和核验结果，帮助用户区分短时池内价差与需要复核的稳定币风险。

## 4. 第 2 周结束前的最小 Demo

在 11 月 29 日前跑通 Ethereum Sepolia → Reactive Lasna → Base Sepolia → AI 复核队列。用固定的模拟报价序列重复以下演示。

| 输入 | 可观察的结果 |
| --- | --- |
| 测试报价 0.999 | 保留源链报价事件，目标链无告警。 |
| 测试报价 0.993，参考证据齐全 | 在 Base Sepolia 产生一条告警。现场查看模型的复核决定及源链、Lasna、目标链三笔交易哈希。 |
| 测试报价 0.993，美元参考缺失 | 目标链告警仍可核对，AI 将该条标为「证据不足」。 |

演示页面标明测试网模拟报价和所用参考数据的来源与时间。提交包保留合约地址、交易浏览器链接、复现步骤和三分钟以内的演示视频。

## 5. 单人或组队

拟单人报名并开放组队。本人负责用例与风险定义、测试网合约联调、AI 复核流程和演示。若后续组队，可按合约与链上观测、数据与 AI、前端与可访问性分工，并在成员确认后补充姓名。

## 参考

- [Day 1 用例拆解卡](https://github.com/sunshineluyao/reactive-builder-camp-2026/blob/main/assignments/d1-use-case.md)
- [Reactive Omni Buildathon 规则](https://blog.reactive.network/reactive-omni-buildathon-thirty-days-to-find-out-what-one-second-buys/)
- [Reactive 支持的网络](https://dev.reactive.network/origins-and-destinations)
- [Reactive MCP 工具](https://dev.reactive.network/reactive-mcp)
- [Aave MCP 工具](https://aave.com/docs/mcp/tools)
