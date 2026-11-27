# Reactive Builder Camp 2026

## 黑客松项目 · Stablecoin Alerts

当 USDC/USDT 模拟报价偏离 1:1 超过 0.5% 时，Ethereum Sepolia 提供报价证据，Reactive Lasna 请求跨链回调，Base Sepolia 记录告警。赛道 3 的链下模型根据可核对的美元报价和价格走势决定是否升级人工复核。

### 项目演示 · 2 分 30 秒

![完整无声演示，含中文字幕：0.9930 的模拟报价触发一次跨链告警，模型根据美元参考证据给出三种复核结果。](track3/video/demo.gif)

[下载英文解说 MP4](https://raw.githubusercontent.com/sunshineluyao/reactive-builder-camp-2026/main/track3/video/demo.mp4) · [截图、中英文字幕与分段时间](track3/video/README.md) · [项目、安装与验证](track3/README.md) · [新增代码的 MIT 许可证](track3/LICENSE)

当前演示提供三条独立本地 EVM 的原始回执、可重复的合约运行和 AI 决策。项目 README 标明公开测试网部署的核验状态。

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
