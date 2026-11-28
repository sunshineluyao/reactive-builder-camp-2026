# Reactive PegPulse 三笔回执复核一条告警

[English](PROOF.md) · **简体中文**

**看到 0.9930 的报价，要通知财库吗？** Base 写入一条告警。签名时没有足够行情，模型暂缓评分。回溯同一时点的真实行情后，模型建议**继续观察**。报价由测试合约模拟，三笔交易均在公开测试网完成。

[观看 2 分 30 秒参赛录像](https://cdn.jsdelivr.net/gh/sunshineluyao/reactive-builder-camp-2026@e3793927f18683f811bf17db4ec07589045ea14d/track3/video/public/demo.mp4) · [打开交互核验页](https://rawcdn.githack.com/sunshineluyao/reactive-builder-camp-2026/e3793927f18683f811bf17db4ec07589045ea14d/track3/review/index.html?lang=zh)

| 2026 年 11 月 27 日（UTC） | 链上发生了什么 | 回执 |
|---|---|---|
| 13:38:12 · Ethereum Sepolia | QuoteSource 发布 0.9930 USDT/USDC 的报价，源日志序号为 2。 | [PriceObserved](https://sepolia.etherscan.io/tx/0xd97a9579a96a20c9868dd7f759079975e2ff1603eb903e42d3fd5ddfbbcc6604) |
| 13:38:12 · Reactive Lasna | ReactiveAlert 识别发布者和 70 个基点的偏离，去重后请求回调。 | [QuoteRouted](https://lasna.reactscan.net/tx/0x63639779506a135ff8cba06c4d8aff5230d029aed5dc781f8f902868f54e8d27) |
| 13:38:14 · Base Sepolia | AlertSink 写入告警，记录源交易及源日志序号。 | [PriceDeviation](https://sepolia.basescan.org/tx/0x5e2a48caaf7ab64dd3f25c4f4b804cf30d09aabc6f885efb44033b91ce3ce602) |

事件 ID 以 `0x38b66270` 开头，以 `d38ac554` 结尾。Base 回执中事件自身的日志序号是 **0**，事件内容记录的**源**日志序号是 **2**。[完整事件 ID、合约地址与原始回执](evidence/public-run.json)

## 做出判断

测试报价比平价低 70 个基点。Bitstamp 的 USDC/USD 收盘价为 **0.999870 美元**，Coinbase 的 USDT/USD 为 **0.998720 美元**。两根分钟线均在签名前 12 秒收盘。币安此前 15 次有成交的收盘价中，**没有一次**同向跌破阈值。先作出选择，再展开理由。

<details><summary><strong>我会继续观察。</strong></summary>

这与冻结模型一致。独立行情未印证 70 个基点的下跌。Base 上的告警仍可查看，有新证据时复核人可继续升级。

</details>

<details><summary><strong>我会升级人工复核。</strong></summary>

如果财库无法承受漏报，这也有理由。模型在本例中建议观察。在历史对照中，模型对 3 次持续偏离建议观察，对另 1 次暂缓判断。人可以独立决定是否升级。

</details>

[带时间戳的模型输入](evidence/market/public-context.json) · [运行输出](evidence/market/public-assessment.json) · [比较模型与两种简单策略](evidence/market/README.zh-CN.md)

## 自行复现

在 `track3/` 运行 `python3 scripts/market_evidence.py --live`。命令只读核验三链回执、获取行情并运行冻结模型。交互页默认展示经过匹配的回执快照，也可另行实时核验公网 RPC。首次进入交互页时，托管服务可能显示 **Open the page**，无需连接钱包。[安装与完整复现说明](README.md)
