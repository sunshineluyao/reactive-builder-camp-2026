# 稳定币偏离告警的复核分流模型

目标链的 `PriceDeviation` 事件记录 USDC/USDT 报价。浏览器收到事件后，将事件与一份同 ID 的价格证据交给模型。模型的运行时决策是将告警升级给人工复核（`escalate`），或保留在观察队列（`observe`）。证据门控还可以返回 `insufficient`，指出需要补齐的项目。模型在链下运行，交易签名和链上事件处理由各自组件完成。

## 输入与证据出处

输入事件包含 `evidenceId`、`observedAt` 和 `priceBps`。价格 10000 代表 1 USDT/USDC，9930 代表每枚 USDC 值 0.9930 USDT。时间戳均使用 Unix 秒。外部 JSON 必须携带 `schema: "stablecoin-evidence/v1"`、`pair: "USDC/USDT"`，其 `alertId` 必须与当前事件 ID 完全一致。示例文件已匹配仓库本地 EVM 回放的事件和时间，可在回放页面直接导入。文件中的美元报价和币对历史均为合成数据。[context-example.json](context-example.json)

| 字段 | 单位与要求 |
| --- | --- |
| `history[]` | 2 至 24 个早于事件的 USDC/USDT 观测。每项含整数 `priceBps`、`observedAt` 和 `source`。按时间严格递增，最多回看 900 秒，最新一条距事件至多 300 秒。 |
| `references["USDC/USD"]` 和 `references["USDT/USD"]` | 各自独立于该池的美元报价。每项含整数 `usdMicros`、`observedAt` 和 `source`。1000000 代表一美元，报价时间应在事件前 300 秒至事件时刻之间。 |
| `provenance` | `synthetic` 标识构造数据，支持 `fixture:` 标识或 HTTPS 来源。`observed` 表示提供方声明为实测，需给出可复查的 HTTPS 来源。来源说明和时间戳可供复核，模型仅本地读取 JSON，数据真伪和独立性依赖提供方及核查人。 |

## 决策与解释

1. 币对报价在 1 的上下 50 个基点以内时（含边界），返回 `observe / no_threshold_crossing`。报价越界且证据通过校验后，模型才计算分数。缺失、过期或不匹配的输入会触发“证据不足”，具体原因见 `code` 和中英文说明。
2. 模型读取的四个特征分别是当前币对偏离的绝对基点数、两项美元报价相对一美元的最大绝对偏离、两项美元报价比值沿当前偏离方向的基点数，以及历史样本中同向超过 50 个基点的比例。四项分别按 200、150、150 和 1 缩放并截断到 [0, 1]。
3. 冻结的 `sc-triage-mlp-v1` 是 4 输入、6 个 tanh 隐藏单元、1 个 sigmoid 输出的神经网络。原始决策分数达到 0.5 时升级，低于 0.5 时继续观察。分数尚未用真实市场数据进行概率校准。结果同时给出特征、版本、证据来源和时间。门控结果的 `inferenceRan` 为 false，`score` 为 null。

下表的前三种情形均可用同一个 0.9930 事件重放。切换场景不产生新的链上交易。

| 合成场景 | 美元证据与历史 | 返回结果 |
| --- | --- | --- |
| `corroborated` | USDC 为 $0.9904，USDT 为 $1.0001。三条历史报价同向越界。 | 升级复核 |
| `pool-only` | USDC 为 $0.9999，USDT 为 $1.0001。三条历史报价均在区间内。 | 继续观察 |
| `missing` 或 `stale` | USDT/USD 缺失，或其采样早于事件 20 分钟。 | 证据不足 |

单独改变参考报价也会改变决策。测试保留相同事件和全部三条越界历史，仅将美元报价改为 $0.9999 和 $1.0001，决策即从升级转为观察。[test_model.py](../tests/test_model.py)

## 训练与验证

训练器用固定种子 72517 初始化权重，对 1200 条合成样本训练 70 轮，优化二元交叉熵。样本覆盖美元报价都靠近锚点、主要由 USDC 变化、主要由 USDT 变化，以及两者均变化的四种情况。生成合成标签时，最大美元偏离至少 85 个基点即可标记为升级。如果最大美元偏离至少 38 个基点、同向美元比价偏离至少 26 个基点且历史持续比例至少 0.4，也标记为升级。运行时用训练所得系数进行推理。

冻结权重在独立种子的 400 条同分布合成样本上与标注规则一致 383 次（95.75%）。这个数字衡量对合成规则的拟合程度。真实市场的告警质量与跨市场泛化能力仍待实证。

从 `track3/` 目录运行，依赖 Python 3 和 Node.js。两种语言分别实现预处理和推理，测试会比较样例与随机输入的决策、特征及分数，并重新训练检查两份权重文件逐字节一致。

```sh
python3 model/reference.py model/cases.json
python3 model/train.py --output /tmp/reactive-triage-weights
python3 -m unittest discover -s tests -p 'test_model.py' -v
```

浏览器依次加载 `model/weights.js` 和 `model/runtime.js`，调用 `StablecoinAI.assess(alert, context)`。本地演示可用 `StablecoinAI.demoContext(alert, "corroborated")` 生成与事件绑定的合成证据。实测回放应传入该事件真实时刻的证据文件。
