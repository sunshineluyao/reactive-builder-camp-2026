# Reactive PegPulse

<picture>
  <source media="(max-width: 860px)" srcset="track3/visual/hero/mobile.svg">
  <img src="track3/visual/hero/desktop.svg" width="100%" alt="两笔 USDC/USDT 模拟报价中，0.9990 留在源链。0.9930 偏离平价 70 个基点，超过 50 个基点的阈值，Reactive Lasna 请求回调，Base Sepolia 写入一条告警。链下 AI 因缺少匹配的美元报价证据而暂缓评分。">
</picture>

**One quote. Three chains. Anyone can verify.**　一条报价，三链共证，人人可验。

Sunshine · Sunshine Swarm Superintelligence (3S) Lab · Reactive Builder Camp 2026 · Reactive Meets AI（赛道 3）

当 USDC/USDT 模拟报价偏离 1:1 超过 0.5% 时，Ethereum Sepolia 提供报价证据，Reactive Lasna 请求跨链回调，Base Sepolia 记录告警。赛道 3 的链下模型根据可核对的美元报价和价格走势决定是否升级人工复核。

**[公开测试网演示视频 · 2 分 30 秒](https://cdn.jsdelivr.net/gh/sunshineluyao/reactive-builder-camp-2026@main/track3/video/public/demo.mp4)** · **[三个合约地址、三笔交易与复现说明](track3/README.md)** · [原始回执 JSON](track3/evidence/public-run.json) · [复制训练营提交链接](assignments/hackathon-submission.txt)

[11 月 29 日营内 Demo Day · 展示与模拟问答（4 分 40 秒）](track3/demo-day/README.md) · [含双语备注的 PowerPoint](track3/demo-day/Reactive-PegPulse-Demo-Day.pptx)

2026 年 11 月 27 日完成六次测试网签名。0.9990 的对照报价只产生源链记录。0.9930 的测试报价触发了 Lasna 的回调请求，Base Sepolia 记下一条预警。公开运行缺少同期美元证据，复核程序暂缓评分。录屏还演示了模型在合成价格证据齐全时给出的两种建议。

[从报价到人工复核的完整流程图](track3/README.md#从报价到人工复核) · [手机竖版封面](track3/visual/hero/mobile.svg)

<details>
<summary>查看本地三链演练动画（2 分 30 秒，中文字幕）</summary>

![本地回放中的阈值、三笔回执与复核决定](track3/video/demo.gif)

[本地演练音频、字幕和截图](track3/video/README.md) · [新增代码的 MIT 许可证](track3/LICENSE)

</details>

## 训练营作业

Reactive Builder Camp 2026 的个人学习笔记与作业。

- [学员实操手册](docs/handbook.md)
- [Day 0 作业 · 测试钱包、Foundry 与 lREACT](assignments/d0-environment-setup.md) · [可粘贴提交文本](assignments/d0-environment-setup-submission.txt)
- [Day 1 作业 · 稳定币价差的跨链预警](notes/d1-use-case.md)
- [Day 2 作业 · 读懂 Lasna 费用](assignments/d2-lasna-fees.md)
- [Day 3 作业 · 监控 Sepolia 代币转账](assignments/d3-sepolia-transfer-monitor.md) · [可粘贴提交文本](assignments/d3-sepolia-transfer-monitor-submission.txt) · [浏览器实操指南](experiments/sepolia-transfer-monitor/README.md)
- [Day 4 作业 · 跨链回调三步走](assignments/d4-cross-chain-callback.md) · [可粘贴提交文本](assignments/d4-cross-chain-callback-submission.txt) · [浏览器实操指南](experiments/cross-chain-callback/README.md)
- [Day 5 场景小实验 · 两次 Cron100 回调后停止](assignments/d5-cron100.md) · [可粘贴提交文本](assignments/d5-cron100-submission.txt) · [浏览器复现与资金流图](experiments/cron100/README.md)
- [Day 6 项目方向卡 · 稳定币跨链告警与证据核验](assignments/d6-project-direction.md)
- [给项目加保护 · 防误触发、防重复、设上限](track3/README.md#三条自动化保护) · [Foundry 测试截图](track3/evidence/forge-guards.png) · [出问题怎么办](track3/README.md#出问题怎么办) · [可粘贴提交文本](assignments/automation-guards-submission.txt)
