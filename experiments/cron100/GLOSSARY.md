# Cron100 实验术语表

按完成实验的顺序查阅。最后一列提供官方资料或本实验源码，便于核对定义和继续阅读。

## 1. 网络、账户与钱包

| 术语 | 在本实验中的含义 | 核验与延伸阅读 |
| --- | --- | --- |
| 区块链 / EVM | 链保存交易和状态。EVM 是执行 Solidity 编译产物的环境，实验的两条链都支持 EVM 合约。 | [Ethereum EVM](https://ethereum.org/developers/docs/evm/) |
| 测试网 / 主网 | 测试网供实验和部署演练。本实验只使用 Lasna 和 Base Sepolia 的测试币。 | [Ethereum 网络](https://ethereum.org/developers/docs/networks/) |
| Base Sepolia | Base 的测试网，链 ID 为 84532，原生测试币的符号是 ETH。接收合约在这条链上运行。 | [Base 网络参数](https://docs.base.org/get-started/connect-to-base) |
| Ethereum Sepolia | Ethereum 的测试网，链 ID 为 11155111。名字与 Base Sepolia 相似，余额和交易各属自己的链。 | [Ethereum Sepolia](https://ethereum.org/developers/docs/networks/#sepolia) |
| Reactive Network / Lasna | Reactive Network 提供链上事件驱动执行。Lasna 是其实验网络，链 ID 为 5318007，定时合约部署于此。 | [Reactive 主网与 Lasna](https://dev.reactive.network/reactive-mainnet) |
| MetaMask | 管理账户、选择链、签署部署和启动等交易的浏览器钱包。 | [MetaMask 网络设置](https://support.metamask.io/configure/networks/) |
| 账户、公开地址、合约地址 | 公开地址是可分享的 0x 标识。钱包账户可用私钥签名，合约地址指向链上程序。一个钱包地址在两条链上各有自己的余额。 | [Ethereum 账户](https://ethereum.org/developers/docs/accounts/) |
| 助记词 / 私钥 | 助记词可恢复一组钱包账户，私钥能控制对应账户和签署交易。领取测试币和查询证据使用公开地址即可。 | [MetaMask 账户保护](https://support.metamask.io/start/user-guide-secret-recovery-phrase-password-and-private-keys/) |
| RPC / Chain ID | RPC 是钱包或应用访问节点的接口。Chain ID 是区分网络的数字，选择网络和交易签名时会用到。 | [Ethereum JSON-RPC 规范](https://eips.ethereum.org/EIPS/eip-1474) · [Base 网络配置](https://docs.base.org/get-started/connect-to-base) |
| 区块浏览器 | 网页上按地址、交易哈希或区块号查询链上信息。实验用 Reactscan 看 Lasna，BaseScan 看 Base Sepolia。 | [Lasna Reactscan](https://lasna.reactscan.net/) · [Base Sepolia BaseScan](https://sepolia.basescan.org/) |

## 2. 资金、原生测试币与费用

| 术语 | 在本实验中的含义 | 核验与延伸阅读 |
| --- | --- | --- |
| 水龙头 / OpenFaucet | 水龙头发放测试币。OpenFaucet 在浏览器计算小型工作量证明，累计后可把测试 ETH 发到选定网络的公开地址。 | [OpenFaucet](https://openfaucet.org/) |
| Base Sepolia 测试 ETH | Base Sepolia 的原生余额，也是该链部署与回调费用的支付单位。 | [Base 网络参数](https://docs.base.org/get-started/connect-to-base) |
| Chainlink LINK | Chainlink 生态使用的代币。Chainlink 水龙头可以发放测试 LINK，Base Sepolia 本实验的 gas 由原生测试 ETH 支付。 | [Chainlink 水龙头](https://faucets.chain.link/) · [Ethereum gas](https://ethereum.org/developers/docs/gas/) |
| Reactive 水龙头 / lREACT | Reactive 水龙头在 Base Sepolia 收测试 ETH，再在 Lasna 发放原生测试币 lREACT。按 1 ETH 对 100 lREACT 的比例，0.01 测试 ETH 对应 1 lREACT。 | [Reactive 水龙头](https://dev.reactive.network/reactive-mainnet#reactive-faucet) |
| wei / ether / Value | wei 是 EVM 的最小记账单位。1 ether 等于 10¹⁸ wei。Remix 的 Value 字段按这个尺度传入当前链的原生币，Lasna 上是 lREACT。 | [Solidity 单位](https://docs.soliditylang.org/en/v0.8.29/units-and-global-variables.html#ether-units) · [Remix Value](https://remix-ide.readthedocs.io/en/latest/run.html) |
| gas / gas limit | gas 衡量计算量，gas limit 约束可消耗的 gas 单位。本实验每次请求的回调上限为 300,000，实际费用还取决于 gas 价格与用量。 | [Ethereum gas](https://ethereum.org/developers/docs/gas/) · [Reactive 费用](https://dev.reactive.network/economy) |
| 钱包余额与合约余额 | 钱包余额用于部署和启动。构造函数中的 Value 成为新合约在该链的余额，分别用于 Lasna 执行费和 Base Sepolia 回调费。 | [Reactive 费用](https://dev.reactive.network/economy) |
| minimumReserve / 费用储备 / 欠费 | minimumReserve 是定时合约发新请求前检查的余额底线，实验填 0.1 lREACT。Reactive 的储备与欠费由系统合约或回调代理记账。 | [本实验余额检查](src/BoundedCron.sol) · [Reactive 费用记账](https://dev.reactive.network/economy) |

## 3. 合约、事件与跨链执行

| 术语 | 在本实验中的含义 | 核验与延伸阅读 |
| --- | --- | --- |
| 智能合约 / Solidity | 智能合约是发布到链上的程序。Solidity 是本实验用来编写它的语言。 | [Ethereum 智能合约](https://ethereum.org/developers/docs/smart-contracts/) · [Solidity 文档](https://docs.soliditylang.org/en/v0.8.29/) |
| 部署 / constructor / payable | 部署创建合约地址。构造函数部署时执行一次，payable 允许部署交易同时附带原生测试币。 | [Solidity 合约](https://docs.soliditylang.org/en/v0.8.29/contracts.html) |
| 源链 / 目的链 | Lasna 发出 Cron100 事件并发起请求，Base Sepolia 接收回调和写入记录。 | [Reactive 源链与目的链](https://dev.reactive.network/origins-and-destinations) |
| BoundedCron / CronReceiver | BoundedCron 是 Lasna 上的定时合约，订阅、计数并停止。CronReceiver 是 Base Sepolia 上的接收合约，记录每轮的源区块与时间戳。 | [本实验合约源码](src/BoundedCron.sol) |
| 系统合约 / 回调代理 | Lasna 系统合约管理订阅和请求，Base Sepolia 官方回调代理把数据提交给接收合约。本实验分别检查两者的调用权限。 | [Reactive 合约](https://dev.reactive.network/reactive-contracts) · [回调代理地址](https://dev.reactive.network/origins-and-destinations#testnet-chains) |
| 区块 / 区块号 / Cron100 | 区块是链上的一批有序记录，区块号标识其位置。Lasna 每 100 个区块产生 Cron100 事件，实际经过的秒数会变化。 | [Ethereum 区块](https://ethereum.org/developers/docs/blocks/) · [Reactive Cron](https://dev.reactive.network/reactive-contracts#cron) |
| 订阅 / 取消订阅 | 订阅把源链、发出事件的地址及事件 topic 交给系统合约过滤。实验达到次数或余额条件时用相同过滤条件取消订阅。 | [Reactive 合约与订阅](https://dev.reactive.network/reactive-contracts) · [本实验合约源码](src/BoundedCron.sol) |
| LogRecord / react | 系统合约把匹配事件整理为 LogRecord 并交给 react。定时合约使用 LogRecord.blockNumber 获取源区块，另外检查链 ID、事件地址和 topic。 | [Reactive 合约](https://dev.reactive.network/reactive-contracts) · [本实验合约源码](src/BoundedCron.sol) |
| requestCallbackV_1_0 / 回调 | 指定目的链、接收地址、gas 上限和调用数据，请求系统把调用交给目的链代理。本实验的调用数据带轮次和源区块。 | [Reactive 回调与费用](https://dev.reactive.network/economy) · [本实验合约源码](src/BoundedCron.sol) |
| arm / stop | 部署者用 arm 绑定接收合约并启动订阅。stop 可提前停止，或在首次取消订阅失败后重试。 | [本实验合约源码](src/BoundedCron.sol) |
| attempts / stopped / subscribed | 三个可读状态，分别是已占用的尝试数、是否已停止发新请求、订阅是否仍在。实验正常结束时依次为 2、true、false。 | [合约源码](src/BoundedCron.sol) · [实际回执](../../assignments/d5-cron100.md) |
| 去重 / 幂等 | 定时合约对同一源区块最多请求一次。接收合约重复收到同一轮次时保留原结果。 | [本实验测试](test/BoundedCron.t.sol) |
| record / executedAt / block.timestamp | record 校验调用方后用 Base Sepolia 当前区块的 Unix 秒数写入 executedAt。读取映射可查看每轮第一次记录的时间。 | [Solidity 全局变量](https://docs.soliditylang.org/en/v0.8.29/units-and-global-variables.html#block-and-transaction-properties) · [本实验合约源码](src/BoundedCron.sol) |

## 4. 交易证据与核验

| 术语 | 在本实验中的含义 | 核验与延伸阅读 |
| --- | --- | --- |
| 交易 / 交易哈希 | 交易是提交到链的操作，交易哈希是查询该笔操作的标识。Lasna 请求与 Base Sepolia 执行各有自己的哈希。 | [Ethereum 交易](https://ethereum.org/developers/docs/transactions/) |
| 交易回执 / Success | 回执包含执行状态、gas 和事件日志。核验时要同时确认目的链交易成功，并且接收合约发出了预期事件。 | [Ethereum JSON-RPC 回执规范](https://eips.ethereum.org/EIPS/eip-1474#eth_gettransactionreceipt) |
| Event / Logs / topic | 事件是合约写入交易回执的结构化日志。对本实验的非匿名事件，topic 0 是事件签名的 Keccak-256 哈希，topic 1 和 2 分别编码带 indexed 的轮次与源区块号。 | [Solidity ABI 事件规范](https://docs.soliditylang.org/en/v0.8.29/abi-spec.html#events) |
| CallbackRequested / CallbackRequestFailed | Lasna 定时合约分别在请求提交成功和调用失败时写入的事件。两类事件都对应一次已占用的尝试。 | [本实验合约源码](src/BoundedCron.sol) |
| CronRecorded / CronStopped | CronRecorded 证明某一轮已在 Base Sepolia 记录。CronStopped 证明 Lasna 定时合约完成取消订阅。两次跨链结果还要核对各自的轮次和源区块号。 | [本实验合约源码](src/BoundedCron.sol) · [实际回执](../../assignments/d5-cron100.md) |
| Reactive Executions / Callbacks | Reactscan 上的两个页签，分别列出 Lasna 反应执行和目的链回调记录，可按请求配对交易。 | [实际 Reactive Executions](https://lasna.reactscan.net/address/0x201E13106fDf34Fb8FEc9174D4e3DFd95b63CC2b?screen=reactive_executions) · [实际 Callbacks](https://lasna.reactscan.net/address/0x201E13106fDf34Fb8FEc9174D4e3DFd95b63CC2b?screen=callbacks) |

## 5. 浏览器开发、测试与部署

| 术语 | 在本实验中的含义 | 核验与延伸阅读 |
| --- | --- | --- |
| 仓库 / Fork / 分支 / Commit | 仓库保存文件版本。Fork 是在自己账号下的仓库副本。分支用于独立实验，commit 记录一次可追踪的改动。 | [GitHub 术语表](https://docs.github.com/en/get-started/learning-about-github/github-glossary) |
| github.dev | GitHub 在浏览器里提供的文件编辑与提交界面。从仓库按句点可进入。 | [github.dev 网页编辑器](https://docs.github.com/en/codespaces/the-githubdev-web-based-editor) |
| GitHub Actions / workflow / runner | Actions 根据 YAML 定义的 workflow 自动或手动执行任务。本实验由 GitHub 托管的 runner 安装工具、运行测试并生成 Remix 源码。 | [GitHub Actions](https://docs.github.com/en/actions/get-started/understand-github-actions) · [本实验工作流](../../.github/workflows/cron100.yml) |
| workflow_dispatch / Run workflow / Summary | workflow_dispatch 允许从网页手动运行工作流。选择分支启动后，Summary 展示任务状态和可复制的 Remix 源码。 | [运行 GitHub 工作流](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow) |
| Foundry / Forge / 单元测试 | Foundry 是合约开发工具，Forge 在 Actions 上运行六个测试，检查重复事件、失败重试、权限和两次运行上限等条件。 | [Foundry 测试文档](https://getfoundry.sh/forge/testing) · [本实验测试](test/BoundedCron.t.sol) |
| SDK / 固定依赖 | SDK 提供现成的接口和基础合约。实验引用 Reactive SDK 的确定提交，保证读者重现时使用同一份依赖。 | [实验固定的 Reactive SDK](https://github.com/Reactive-Network/reactive-lib-omni/tree/3ade0dcf1d27e67e5783ef807e73a1b9e0c0cce8) |
| Remix / Browser Extension / Add Contract | Remix 是网页版合约 IDE。Browser Extension 连接 MetaMask，Add Contract 可按地址加载已有合约的交互界面。 | [Remix 部署与合约交互](https://remix-ide.readthedocs.io/en/latest/run.html) |
| Solidity 编译器 / Cancun / 优化 Runs | 编译器生成部署用字节码和 ABI。指南和 Actions 都使用 Solidity 0.8.29，目标 EVM 为 Cancun，优化参数为 200 runs，用于平衡代码大小和执行 gas。 | [Solidity 编译器设置](https://docs.soliditylang.org/en/v0.8.29/using-the-compiler.html) · [实验 Foundry 配置](foundry.toml) |
| ABI | 合约接口的机器可读描述。Remix 根据 ABI 显示构造参数、函数按钮及返回值。 | [Solidity ABI 规范](https://docs.soliditylang.org/en/v0.8.29/abi-spec.html) |
| GitHub Copilot Chat | 可选的代码学习助手，可在 GitHub 网页解释源码和测试。合约改动仍用 Actions 运行实际测试。 | [网页版 Copilot Chat](https://docs.github.com/en/copilot/how-tos/copilot-on-github/chat-with-copilot/chat-in-github) |
| Mermaid | 用文本定义并由 GitHub 渲染图表。本实验的资金流图用分组显示两条链及其原生测试币流向。 | [GitHub Mermaid 图表](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams) · [本实验资金流图](README.md#测试币如何流动) |
