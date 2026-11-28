# Reactive PegPulse · 主持人讲稿

[English](script.en.md) · **简体中文**

One quote. Three chains. Anyone can verify.　一条报价，三链共证，人人可验。

Sunshine · Sunshine Swarm Superintelligence (3S) Lab

Reactive Builder Camp Demo Day · 2026 年 11 月 29 日

从 00:00 播放即可。02:50 自动进入预录模拟问答，04:40 结束。讲者同期在另一场会议现场作报告。欢迎主持人记录观众的追问，交由 Sunshine 会后答复。

## 项目演示

### 00:00　一条报价，三链共证

大家好，我是 Sunshine，来自 3S Lab。我们的项目叫 Reactive PegPulse。一条报价，三链共证，人人可验。假如你是社区财库的志愿者，一枚 USDC 现在只能换到 0.9930 枚 USDT。你会请大家马上复核吗？我们先查这条告警有没有上链，再看市场证据是否足够。手机上能打开区块浏览器，就能跟着核对。

<details><summary>English transcript</summary>

Hello, I’m Sunshine from 3S Lab. Our project is Reactive PegPulse. One quote. Three chains. Anyone can verify. Imagine volunteering for a community treasury. One USDC buys only 0.9930 USDT. Would you ask others to review it? First, check that the alert reached the chain. Then ask whether market evidence is sufficient. Anyone with a mobile browser can follow the receipts.

</details>

### 00:28　报价的触发门槛

来看这段价格动画。中间的参考线是一比一，绿色区间的上下边界各离它半个百分点。第一笔模拟报价 0.9990，偏离十个基点，只留下源链记录。动画里的 0.9950 恰好碰到下边界，也继续观察。当报价来到 0.9930，偏离扩大到七十个基点。只有越过这条线，合约才会请求回调。

<details><summary>English transcript</summary>

The center line is parity. The green band extends half a percent on either side. The control quote, 0.9990, is ten basis points below parity. The animation’s 0.9950 sits exactly on the boundary. Both stay quiet. At 0.9930, the gap reaches seventy basis points. Crossing the threshold makes the contract request a callback.

</details>

### 00:54　三份公开回执

看实际交易。我在以太坊测试网发布模拟报价。拉斯纳上的合约订阅了指定发布者的报价事件。网络调用 react()，合约核对来源、阈值和重复事件，再向贝斯请求回调。接收合约自动写下一条告警。这三份回执如何对应？看源交易哈希和日志序号二。三个区块的时间依次是十三点三十八分十二秒、十二秒和十四秒。这一次首尾相差两秒。这是一次观察。每笔回执都可以打开区块浏览器独立核对。

<details><summary>English transcript</summary>

These are real testnet transactions. I published a simulated quote on Ethereum Sepolia. The Lasna contract subscribes to that publisher’s quote events. Reactive calls react() on Lasna. The contract checks the source, threshold and duplicates, then requests a callback. Base Sepolia records the alert automatically. To match the event, compare the source transaction hash and log index two. The three UTC block times are 13:38:12, 13:38:12 and 13:38:14. The first and last block timestamps differ by two seconds in this run. Each receipt has its own explorer link.

</details>

### 01:29　告警如何进入人工复核

写下告警之后，链下模型负责安排复核顺序。它需要此前的价格走势，以及两种币各自对美元的同期报价。这次公开运行没有附上美元证据，所以系统保留告警、暂缓评分。这里看到的就是这次运行的结果。为了演示另外两种结果，我固定同一条链上告警，切换有标记的合成数据。美元报价也走弱时升级复核。两个参考价都接近一美元时继续观察。

<details><summary>English transcript</summary>

An off-chain model prioritizes review. It needs earlier pair history and contemporaneous independent dollar references for both coins. The public run had no dollar references. The alert was retained and the score withheld. That is the observed outcome. For the two alternatives I keep the on-chain alert fixed and switch labeled synthetic evidence. Corroborating dollar weakness escalates review. Near-par references support observation.

</details>

### 02:00　自动化的边界

这套工具只记告警，不动用稳定币本金。同一条源日志来两次，只发一次回调。回调送达两次，也只记一次。我还给新版合约加了单笔和累计服务费上限。余额或预算用完就停止新工作，充值也不会重置累计额度。十五项本地测试全部通过，覆盖正常、拦截、重放和充值恢复。刚才的三笔公开交易来自加设费用上限前的版本。

<details><summary>English transcript</summary>

The tool records alerts and moves zero stablecoin principal. Repeating a source log sends one callback. Redelivering it records one alert. The newer contracts cap both individual and lifetime service payments. An empty balance or budget stops new work. Top-ups do not reset the lifetime cap. All fifteen local tests passed, including valid runs, rejection, replay and recovery. The public receipts shown earlier predate the added fee caps.

</details>

### 02:28　谁能独立核验

谁能复核？社区志愿者可以直接读三笔回执，无需连接钱包或支付手续费。中英字幕和逐字稿让大家按自己的节奏核对。我们把包容参与和透明问责作为设计目标，对应可持续发展目标十和十六。下一步请社区成员试用，记录有多少人能独立核对告警。

<details><summary>English transcript</summary>

Community volunteers can read all three receipts without connecting a wallet or paying a fee. Bilingual captions and a transcript let people check at their own pace. Our design goals are wider participation and transparent accountability, aligned with SDGs 10 and 16. Next we will test how many community members can verify an alert unaided.

</details>

## 预录模拟问答

### 02:50　Execution

下面是预录模拟问答。第一问，评委怎么确认目标链真的执行了？打开 Base Sepolia 回执，找到接收合约发出的 PriceDeviation 日志。它携带源交易哈希和日志序号二，再对照拉斯纳回执里的同一事件编号。这样可以核对业务告警确实写入。两秒只是这次首尾区块时间戳的差。

<details><summary>English transcript</summary>

This is a prerecorded simulated Q&A. First question: how can a judge verify that the destination executed? Open the Base Sepolia receipt and find the recipient’s PriceDeviation event. Match its source transaction hash and log index two to the event ID on Lasna. This verifies that the alert was recorded. Two seconds is the difference between the endpoint block timestamps in this run.

</details>

### 03:15　Integration

第二问，已经有价格预言机，为什么还需要 Reactive？价格预言机可以提供美元参考价。我们的合约订阅的是具体报价事件，越界才请求跨链回调。社区可用三笔回执核对同一事件。这次用模拟报价跑通了真实回调。接入实时预言机是下一步。这次没有美元参考价，复核器保留告警、暂缓评分。

<details><summary>English transcript</summary>

Second question: if we have price oracles, what does Reactive add? Price oracles can supply dollar references. Our contract subscribes to a specific quote event and requests a cross-chain callback when the threshold is crossed. Anyone can match the three receipts. The simulated quote triggered a real callback. Live oracle feeds are a next step. Without dollar references, the review tool retained the alert and withheld a score.

</details>

### 03:42　Usefulness

第三问，社区志愿者看到一个池子的报价下降，就能断定稳定币脱锚了吗？一个池子的报价只够触发调查。模型还需要历史走势和两项独立美元价格。这次公开运行缺少这些证据，保留了告警，也明确告诉分析员需要补什么。志愿者可以标出缺失的价格证据，也可以用同一条告警比较两组合成输入，核查模型何时升级复核。

<details><summary>English transcript</summary>

Third question: when volunteers see one pool quote fall, can they conclude that a stablecoin lost its peg? One pool quote warrants investigation. The model also needs history and independent dollar prices for both coins. The public run kept the alert and identified the missing inputs. Volunteers can flag the missing prices and use the same alert with two synthetic inputs to check when the model escalates review.

</details>

### 04:12　Craft

最后一问，回调失败，或者同一个事件来了两次怎么办？失败不会增加目标链告警数。核对代理状态和目标事件，检查余额、欠费和剩余预算，再处理后续合格事件。授权重投同一事件最多写入一次。大家可以从仓库独立重跑十五项测试。欢迎主持人记下其他问题，我会在会后书面回复。

<details><summary>English transcript</summary>

Final question: what if a callback fails or an event arrives twice? A failed call leaves the destination count unchanged. Inspect the proxy, target event, balance, debt and remaining budget. Authorized redelivery can record that event once. You can rerun all fifteen tests from the repository. Please collect additional questions for my written follow-up.

</details>
