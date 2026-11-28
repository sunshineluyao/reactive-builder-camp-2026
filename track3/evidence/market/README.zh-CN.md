# 你会通知财库团队吗？

[English](README.md) · **简体中文**

Sepolia 测试合约将报价设为 **1 USDC 兑换 0.9930 USDT**。Reactive 在 Lasna 发起回调，Base 记录告警。签名时没有独立行情，模型保留告警并暂缓评分。我们随后调取事件之前已经收盘的行情，用同一冻结模型复算，结果是**继续观察**。是否升级仍由财库复核人决定。[三链回执](../public-run.json) · [模型版本、评分与特征](public-assessment.json)

| 2026 年 11 月 27 日 13:38:12 UTC 之前的证据 | 结果 | 解释 |
|---|---:|---|
| [Bitstamp USDC/USD](https://www.bitstamp.net/api/v2/ohlc/usdcusd/?step=60&limit=15&end=1795786620) | 0.999870 美元 | USDC 的独立美元报价，分钟线在 13:38:00 收盘。 |
| [Coinbase Exchange USDT-USD](https://api.exchange.coinbase.com/products/USDT-USD/candles?start=2026-11-27T13:23:00Z&end=2026-11-27T13:37:00Z&granularity=60) | 0.998720 美元 | 同一收盘时刻，另一交易所的 USDT 美元报价。 |
| [币安 USDCUSDT](https://data-api.binance.vision/api/v3/klines?symbol=USDCUSDT&interval=1m&startTime=1795785780000&endTime=1795786679999&limit=15) | 0 / 15 | 15 条此前有成交的分钟收盘价均未同向下跌超过 50 个基点。两项美元参考价的最大偏离为 12.8 个基点。 |

70 个基点的下跌来自测试合约，外部市场观察来自三个交易所。两项美元参考价都在事件前 12 秒收盘。程序采用分钟结束时间，排除未收盘及成交量为零的记录。事后归档无法确定交易所首次发布某根分钟线的时刻。模型输出的是复核评分，其概率校准尚未验证。[模型输入](public-context.json) · [交易所响应、查询地址和规范化 JSON 的 SHA-256 摘要](provider-responses.json) · [模型说明](../../model/MODEL_CARD.md)

## 分流减少了多少次复核？代价是什么？

固定取 2023 年 3 月 10–15 日及 2026 年 11 月 27 日每天 UTC 13:00–13:59 的一分钟收盘价。前六天覆盖 USDC 银行事件及恢复期。采用整个考察期都有历史交易记录的 Kraken USDC/USDT，美元参考源仍为 Bitstamp 和 Coinbase。比较前已冻结模型及训练标注规则。[发行方对银行事件的说明](https://www.circle.com/pressroom/3-3-billion-of-usdc-reserve-risk-removed-dollar-de-peg-closes) · [逐日结果](comparison.json)

计划观察 420 分钟，其中 402 分钟有交易。231 次越界中，208 次在其后连续五分钟均有交易。若其中至少三个收盘价同向偏离平价超过 50 个基点，就记为持续偏离。模型只能使用触发时刻及之前的行情。23 次后续记录不完整的越界从三组对照中一起排除。

| 同样的 208 次越界 | 升级复核 | 升级后只出现短暂偏离 | 持续偏离却判为观察 | 暂缓判断（其中持续偏离） |
|---|---:|---:|---:|---:|
| 每次越界都升级 | 208 | 14 | 0 | 0 |
| 用于标注训练样本的书面规则 | 202 | 12 | 3 | 1（1） |
| 冻结神经网络 | 200 | 10 | 3 | 1（1） |

相比分流规则，模型少升级了 2 次随后仅出现短暂偏离的报价。与全部升级相比，模型少转介 8 次，同时将 3 次持续偏离判为观察，对另 1 次持续偏离暂缓判断。208 个窗口中有 194 个符合持续偏离定义。相邻窗口重叠，指标衡量五分钟价格走势，不能据此推算独立事件准确率、财库损失或志愿者实际绩效。若漏报代价较高，财库也可以选择对所有越界逐一复核。

## 复现与体验

在 `track3/` 下使用 Python 3 和 Node.js 18 或以上版本。前两条命令只需仓库内文件。第三条实时核验三链、获取签名事件对应的历史行情并运行模型，无需钱包。行情不足时输出 `insufficient`。若链上事件未通过核验，则停止评分。

```bash
python3 scripts/market_evidence.py
python3 scripts/market_benchmark.py
python3 scripts/market_evidence.py --live
```

实时命令可加 `--run 公开回执清单路径`。两个脚本均可用 `--refresh` 重新采集公开数据。历史对照根据 Kraken 成交编号和分页游标重建分钟线。[行情采集与推断](../../scripts/market_evidence.py) · [对照程序](../../scripts/market_benchmark.py) · [历史响应归档](comparison-sources.json.gz)

**财库复核任务。** 从仓库首页打开核验页，查找 Base 回调，核对两个美元报价来源，再选择是否升级。可以比较自己的选择和模型建议，或打开三家交易所的原始数据。练习仅在浏览器内运行，不收集参与者数据。尚未对真人复核表现做测量。
