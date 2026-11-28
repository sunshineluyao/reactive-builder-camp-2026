# 主持人讲稿 · Stablecoin Alerts

张露瑶（Sunshine Zhang）｜Reactive Builder Camp Demo Day｜2026 年 11 月 29 日

从 00:00 播放一个文件即可。02:50 自动进入预录模拟问答，04:40 播放结束。讲者同时在另一场学术会议现场作报告。主持人可以记录观众临时提出的问题，交给讲者会后答复。

## 项目演示

### 00:00　财库的复核问题

大家好，我是昆山杜克大学的张露瑶。这是我的数字分身，今天带你看一条稳定币告警。假如你管理一家 DAO 的财库，一枚 USDC 忽然只能换到 0.9930 枚 USDT。要请同事马上复核吗？我想先回答两个问题。这条告警真的发生了吗？有什么证据值得占用同事的时间？

<details><summary>English transcript</summary>

Hello, I’m Luyao Zhang from Duke Kunshan University. My digital avatar will walk you through a stablecoin alert. Imagine running a DAO treasury. One USDC now buys only 0.9930 USDT. Should a colleague review it right away? I wanted to answer two questions. Did the alert actually happen? What evidence makes it worth a colleague’s time?

</details>

### 00:25　报价的触发门槛

来看这段价格动画。中间的参考线是一比一，绿色区间的上下边界各离它半个百分点。第一笔模拟报价 0.9990，偏离十个基点，只留下源链记录。动画里的 0.9950 恰好碰到下边界，也继续观察。当报价来到 0.9930，偏离扩大到七十个基点。只有越过这条线，合约才会请求回调。

<details><summary>English transcript</summary>

The center line is parity. The green band extends half a percent on either side. The control quote, 0.9990, is ten basis points below parity. The animation’s 0.9950 sits exactly on the boundary. Both stay quiet. At 0.9930, the gap reaches seventy basis points. Crossing the threshold makes the contract request a callback.

</details>

### 00:52　三份公开回执

现在看真实的测试网交易。我用测试钱包在以太坊测试网发布报价。拉斯纳上的合约订阅了这个发布合约的报价事件。拉斯纳核对来源和阈值，发出回调请求。随后，目标链的接收合约写下一条告警。这两步由网络自动执行。这三份回执如何对应？看源交易哈希和日志序号二。三个区块的时间依次是十三点三十八分十二秒、十二秒和十四秒。这一次首尾相差两秒。这是一次观察。每笔回执都可以打开区块浏览器独立核对。

<details><summary>English transcript</summary>

These are actual testnet transactions. I published the simulated quote on Ethereum Sepolia. The Lasna contract subscribes to this publisher’s events. Lasna checks the source and threshold, then requests a callback. The recipient on Base Sepolia records the alert. Both steps run automatically. To match the event, compare the source transaction hash and log index two. The three UTC block times are 13:38:12, 13:38:12 and 13:38:14. The first and last block timestamps differ by two seconds in this run. Each receipt has its own explorer link.

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

### 02:29　下一次复核

回到最初的问题。如果财库团队看到 0.9930，现在可以先查三份回执，再决定哪些市场证据还需要补齐。我的下一步，是接入独立市场报价，检验多少告警真正值得人工处理。代码、回执和复现方法都在项目仓库。谢谢大家。

<details><summary>English transcript</summary>

Back to the treasury desk. At 0.9930 the team can first verify the three receipts, then identify the missing market evidence. Next I want to connect independent market feeds and measure how many alerts warrant a human review. The repository contains the code, receipts and reproduction steps. Thank you.

</details>

## 预录模拟问答

### 02:50　Execution

下面是预录模拟问答。第一问，评委怎么确认目标链真的执行了？打开 Base Sepolia 回执，找到接收合约发出的 PriceDeviation 日志。它携带源交易哈希和日志序号二，再对照拉斯纳回执里的同一事件编号。这样可以核对业务告警确实写入。两秒只是这次首尾区块时间戳的差。

<details><summary>English transcript</summary>

This is a prerecorded simulated Q&A. First question: how can a judge verify that the destination executed? Open the Base Sepolia receipt and find the recipient’s PriceDeviation event. Match its source transaction hash and log index two to the event ID on Lasna. This verifies that the alert was recorded. Two seconds is the difference between the endpoint block timestamps in this run.

</details>

### 03:16　Integration

第二问，为什么需要 Reactive？它持续订阅指定合约的事件，核对来源、阈值和事件编号，再跨链请求回调。换掉它，团队就要自己运行监听、中继和重放管理服务。公开测试时，我用钱包发布两笔报价。越界之后，中继和目标链写入都没有再要求我签名。

<details><summary>English transcript</summary>

Second question: what work does Reactive actually do? It subscribes to the designated contract, checks source, threshold and event identity, then requests the cross-chain callback. Otherwise the team would operate its own listener, relay and replay controls. I signed two quotes during the public test. Once the threshold was crossed, the relay and target write needed no further signature from me.

</details>

### 03:41　Usefulness

第三问，一个交易池的价格下降，就说明稳定币脱锚了吗？一个池子的报价只够触发调查。模型还需要历史走势和两项独立美元价格。这次公开运行缺少这些证据，保留了告警，也明确告诉分析员需要补什么。我们可以固定同一条告警，改变两项美元参考报价，独立检查模型是否改变复核建议。

<details><summary>English transcript</summary>

Third question: does one pool quote establish a depeg? One pool quote warrants investigation. The model also needs history and independent dollar prices for both coins. The public run kept the alert and identified the missing inputs. Holding the same alert fixed, we can change the two dollar references and test whether the recommendation changes.

</details>

### 04:10　Craft

最后一问，回调失败，或者同一个事件来了两次怎么办？失败不会增加目标链告警数。核对代理状态和目标事件，检查余额、欠费和剩余预算，再处理后续合格事件。授权重投同一事件最多写入一次。大家可以从仓库独立重跑十五项测试。欢迎主持人记下其他问题，我会在会后书面回复。

<details><summary>English transcript</summary>

Final question: what if a callback fails or an event arrives twice? A failed call leaves the destination count unchanged. Inspect the proxy, target event, balance, debt and remaining budget. Authorized redelivery can record that event once. You can rerun all fifteen tests from the repository. Please collect additional questions for my written follow-up.

</details>
