# D4 必做 · 跨链回调三步走

路线采用 **Base Sepolia → Lasna → Base Sepolia**。当源链的 CampOrigin 发出值为 500 的 Ping 事件时，Lasna 上的 CampReactive 执行 react()，由官方 Callback Proxy 在 Base Sepolia 调用 CampCallback。

按 [浏览器实操指南](../experiments/cross-chain-callback/README.md) 在 Remix 部署和触发。以下位置待补入本次测试网实操的交易链接与失败截图。

## 提交文本

替换待填项后，把这段文字粘贴到训练营的 D4 提交框，并上传钱包直调的报错截图。

```text
跨链回调三步走
链路：Base Sepolia → Lasna → Base Sepolia
源链 CampOrigin.ping(500) 事件交易：（粘贴 BaseScan 交易 URL）
Lasna CampReactive.react() 执行交易：（粘贴 Reactscan 交易 URL）
目标链 CampCallback.onEvent() 回调交易：（粘贴 BaseScan 交易 URL）
失败实验：（上传报错截图，如果有失败交易 URL 也可填写）
失败原因：钱包直调时，msg.sender 是我的测试钱包地址，onlyServiceProvider 只允许 Base Sepolia 官方 Callback Proxy 调用，因此本次调用被拒绝。
```

## 核验三笔交易

| 顺序 | 链 | 核验内容 |
| --- | --- | --- |
| 1 | Base Sepolia | CampOrigin 发出 Ping，值为 500 |
| 2 | Lasna | CampReactive 执行 react()，发出 Seen 和 CallbackRequested |
| 3 | Base Sepolia | CampCallback 发出 Handled，lastValue() 为 500 |

三笔链接对应同一次 Ping。用 Reactscan 的 **Reactive Executions** 和 **Callbacks** 按源交易哈希配对。失败实验用同一个测试钱包直接调用 `onEvent(你的 CampReactive 地址, 84532, 0, 500)`，Value 为 0。截图保留实际拒绝提示。[回调权限](https://dev.reactive.network/callback-contracts)

## 在 GitHub 补充截图

在 `assignments/` 目录点击 **Add file → Upload files**，上传 `d4-wallet-revert.png`。回到本页，点铅笔编辑并填好交易 URL，在提交文本下方插入这一行，然后点 **Commit changes**。

```markdown
![钱包直调 CampCallback 被拒绝](d4-wallet-revert.png)
```
