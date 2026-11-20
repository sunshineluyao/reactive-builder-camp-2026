# D4 必做 · 跨链回调三步走

用 **Base Sepolia → Lasna → Base Sepolia** 完成。Base Sepolia 同时作为源链和目标链，钱包只需切换两张测试网。源链用自己部署的 CampOrigin 发出 Ping 事件。Lasna 的 CampReactive 收到事件后执行 react()，目标端 CampCallback 记录结果。D5 的 Cron100 材料可以复用钱包和领币设置，这次单独保留 Ping 链路和钱包直调被拒的凭证。

~~~mermaid
flowchart TD
    O["Base Sepolia · CampOrigin"] -->|"Ping 事件，值为 500"| R["Lasna · CampReactive.react()"]
    R -->|"请求回调"| P["Base Sepolia · 官方 Callback Proxy"]
    P -->|"调用 onEvent"| C["Base Sepolia · CampCallback"]
    W["MetaMask 测试钱包"] -.->|"直接调用被拒绝"| C
~~~

## 1. 准备 MetaMask 和测试币

1. 沿用 D5 的测试账户。在 MetaMask 确认两张网的 Chain ID 分别为 **Base Sepolia 84532** 和 **Reactive Lasna 5318007**。钱包交易只用两张测试网的测试币。[添加网络和领取测试币](../cron100/README.md#1-在-metamask-添加两条测试网)
2. 检查两张网的钱包余额。下面复用模板的合约预算，需要 **0.02 测试 ETH 加 Base Sepolia gas**，以及 **0.5 lREACT 加 Lasna gas**。如果两张网都要补币，可先在 OpenFaucet 领取约 **0.04 Base Sepolia 测试 ETH**，再在 Base Sepolia 向官方水龙头 **0x2afaFD298b23b62760711756088F75B7409f5967** 发送 **0.01 测试 ETH**。同一地址会在 Lasna 收到 **1 lREACT**。[OpenFaucet](https://openfaucet.org/) · [Reactive 官方领币方法](https://dev.reactive.network/reactive-mainnet#reactive-faucet)

## 2. 在 Remix 编译三份合约

1. [在 Remix 打开 CampRoundTrip.sol](https://app.remix.live/#url=https://github.com/sunshineluyao/reactive-builder-camp-2026/blob/main/experiments/cross-chain-callback/remix/CampRoundTrip.sol)。文件合并了官方模板的三个合约，SDK 依赖固定为模板的版本。若链接只打开首页，用 Remix 首页的 **GitHub** 导入 [CampRoundTrip.sol](remix/CampRoundTrip.sol) 的 GitHub URL。
2. 打开左侧 **Compile**，选择 Solidity **0.8.29**。在 **Settings** 中把 EVM Version 设为 **cancun**，打开 **Optimizer**，Runs 填 **200**。点击 **Compile**，等三个合约都可在部署面板选择。
3. 打开 **Deploy & Run Transactions**，将环境切到 **Browser Extension**，选择 **MetaMask** 并连接测试账户。部署前查看 Remix 显示的链和 MetaMask 的确认页。[Remix 部署说明](https://remix-ide.readthedocs.io/en/latest/run.html) · [官方模板](https://github.com/ethpanda-org/reactive-builder-camp/tree/87675f45bdaf7b944028bd6231e463f869b453c8/starter)

## 3. 部署三个合约并绑定

依次在 Remix 选择合约、输入 Value 和构造参数，在 MetaMask 签名。每笔部署成功后，从 **Deployed Contracts** 复制新地址。Remix 的 Value 单位选 **wei** 时可直接填写下表的整数。

| 顺序 | MetaMask 网络 | 合约 | Value（wei） | 构造参数 |
| --- | --- | --- | --- | --- |
| 1 | Base Sepolia | CampOrigin | 0 | 无 |
| 2 | Reactive Lasna | CampReactive | 500000000000000000（0.5 lREACT） | 按下表设置 |
| 3 | Base Sepolia | CampCallback | 20000000000000000（0.02 测试 ETH） | proxy_ 填 Base Sepolia 官方 Proxy，reactive_ 填第 2 步的 CampReactive 地址 |

| CampReactive 构造参数 | 填入 |
| --- | --- |
| originChainId_ | 84532 |
| originContract_ | 第 1 步部署的 CampOrigin 地址 |
| originTopic0_ | 114684359751101065429392085520984714040648842024659507369580916668773914000541 |
| destChainId_ | 84532 |
| threshold_ | 100 |
| limit_ | 5 |

Base Sepolia 的 **Callback Proxy** 是 **0x476F44b11F5C942c58f4c8E3d0300E5710743585**。表里的 originTopic0_ 以十进制表示 **Ping(address,uint256)** 事件签名的哈希，十六进制为 **0xfd8d0c1dc3ab254ec49463a1192bb2423b3b851adedec1aa94dcd362dc063c9d**。[官方 Proxy 表](https://dev.reactive.network/origins-and-destinations#testnet-chains)

切回 **Lasna**，把 Remix 的 **Value 改回 0**。在 CampReactive 上展开 **setRecipient**，粘贴第 3 步的 **CampCallback** 地址并确认交易。再读取 **recipient**，确保它等于你自己的 CampCallback 地址。

如切网后实例没有显示，先在 **Deploy** 下拉框选对应合约，再到 **Deployed Contracts → Add Contract** 输入已部署地址。旧版 Remix 将加载实例的操作称为 **At Address**。

## 4. 触发一次 Ping，找到三笔交易

切回 **Base Sepolia**。在 CampOrigin 上调用 **ping(500)**，Value 保持 **0**。这笔交易成功后复制 BaseScan 链接。500 达到阈值 100，Lasna 会请求目标链回调。等网络投递完成，再按以下顺序取证。

| 证据 | 去哪里查 | 要看见什么 |
| --- | --- | --- |
| ① 源链交易 | BaseScan 的 ping(500) 交易页，也可从 Remix 的交易记录打开 | 成功回执且 CampOrigin 发出了 Ping 事件 |
| ② Lasna react() | Reactscan 搜索 CampReactive 地址，进入 **Reactive Executions**，打开与①源哈希匹配的 Lasna 交易 | 在同一笔 Lasna 执行中看到 Seen 和 CallbackRequested，复制 Lasna 的交易页 URL |
| ③ 目标链回调 | 同一个 Lasna 地址页打开 **Callbacks**，从②的记录找到 Base Sepolia 目的链交易 | BaseScan 回执成功且 CampCallback 发出了 Handled。Remix 读取 count() 应为 1、lastValue() 应为 500 |

建议用源交易哈希把三笔回执串起来。Seen 和 Handled 都携带 originTxHash。若浏览器没有解码事件，可检查各事件 **Data** 的前 32 字节，这一段与①的交易哈希相同。[Lasna Reactscan](https://lasna.reactscan.net/) · [Base Sepolia BaseScan](https://sepolia.basescan.org/) · [Reactive 如何查回调](https://dev.reactive.network/economy#inspecting-callbacks)

## 5. 用自己的钱包做失败实验

1. 保持 MetaMask 在 **Base Sepolia**，保持当前测试钱包连接。在 Remix 打开 **CampCallback**，确认 **Value = 0**，展开 **onEvent**。
2. 参数依次填 **刚才的 CampReactive 地址**、**84532**、**0**、**500**，点击调用。reactive_ 刻意使用正确的 CampReactive 地址，以便单独验证钱包在第一道调用者检查中被拒绝。
3. Remix 或 MetaMask 通常会在估算 gas 时报告 **NotAuthorized** 或 **execution reverted**。截下包含函数名、Base Sepolia 和实际报错的界面，然后关闭交易提示。若这笔失败交易已广播，也可保留失败交易的 BaseScan 链接。回到 Remix 再读一次 **count() = 1**。

**一句话解释。** 钱包直调时 msg.sender 是我的测试钱包地址，onlyServiceProvider 要求它是 Base Sepolia 的官方 Callback Proxy，因此合约拒绝调用。正常回调还通过 onlyCallbackSender 校验 payload 中由代理注入的 CampReactive 地址。[官方回调鉴权说明](https://dev.reactive.network/callback-contracts)

## 6. 粘贴到作业提交框

将四个括号里的位置换成自己的记录，截图另行上传。

~~~text
跨链回调三步走
链路：Base Sepolia → Lasna → Base Sepolia
源链 CampOrigin.ping(500) 事件交易：[BaseScan 交易 URL]
Lasna CampReactive.react() 执行交易：[Reactscan 交易 URL]
目标链 CampCallback.onEvent() 回调交易：[BaseScan 交易 URL]
失败实验：[已上传钱包直调被拒的报错截图，或填写失败交易 URL]
原因：钱包直调时 msg.sender 是我的测试钱包地址，onlyServiceProvider 只接受 Base Sepolia 的官方 Callback Proxy，因此调用被拒绝。
~~~

如果只看到 Ping，先核对 CampReactive 的源合约地址、chain ID 和事件 topic。若已看到 Lasna 执行，继续核对 recipient、目标链官方 Proxy 和接收合约余额。源链和目标链都用 Base Sepolia 时，两笔 BaseScan 交易仍分别对应事件和回调。[模板排查表](https://github.com/ethpanda-org/reactive-builder-camp/blob/87675f45bdaf7b944028bd6231e463f869b453c8/starter/README.md#4-常见报错)
