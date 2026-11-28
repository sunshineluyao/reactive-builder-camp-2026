# Stablecoin Alerts · Demo Day

**[播放完整预录视频（4 分 40 秒）](https://cdn.jsdelivr.net/gh/sunshineluyao/reactive-builder-camp-2026@main/track3/demo-day/Stablecoin-Alerts-Demo-Day.mp4)**

张露瑶（Luyao “Sunshine” Zhang），昆山杜克大学。Reactive Builder Camp 营内展示，2026 年 11 月 29 日。视频将 **2 分 50 秒项目展示**与 **1 分 50 秒预录模拟问答**连在一起。普通话旁白配中英双语画面字幕，下载视频后可离线连续播放。

**训练营提交材料**　[演示幻灯片 PDF](Stablecoin-Alerts-Demo-Day.pdf) · [可编辑 PowerPoint，含双语讲者备注](Stablecoin-Alerts-Demo-Day.pptx) · [预录演示截图](demo-screenshot.jpg)

![演示视频中核对 Ethereum Sepolia、Reactive Lasna 和 Base Sepolia 三笔回执的画面](demo-screenshot.jpg)

### 主持人播放说明

11 月 29 日 15:00–16:00（北京时间）期间，讲者将在另一场学术会议现场作报告，无法实时出席。烦请主持人在本组时段从 **00:00** 播放视频并共享电脑声音。**02:50** 会自动进入模拟问答，**04:40** 结束。新增的现场问题可由主持人记录，讲者会后书面回复。网络不稳时，可以事先将同一 MP4 下载到播放电脑。

| 视频时间 | 内容 | 评委可以核对什么 |
| --- | --- | --- |
| 00:00 | DAO 财库面对一条 0.9930 报价 | 只记录预警，再分配人工复核时间 |
| 00:25 | Wanim 动画演示三种报价 | 0.9990 和边界 0.9950 继续观察，0.9930 请求回调 |
| 00:52 | 三份公开测试网回执 | 源报价、Lasna 执行、Base 回调对应同一事件 |
| 01:29 | 复核器切换输入证据 | 公网缺证时暂缓评分，合成对照展示另外两个决定 |
| 02:00 | 防重复与费用保护 | 新版合约 15 项本地 Foundry 测试通过 |
| 02:29 | 下一步 | 接入独立报价并评估人工复核队列的误报率 |
| **02:50** | **预录模拟问答开始** | **Execution**　怎样证明目标链写入告警？ |
| 03:16 | Integration | 哪两步由 Reactive 和跨链回调自动执行？ |
| 03:41 | Usefulness | 单池报价下降够不够认定稳定币脱锚？ |
| 04:10 | Craft | 回调失败、重复事件和预算耗尽如何处理？ |

### 登记与制作材料

[登记表四栏可复制答案](registration.txt) · [科学动画与数字讲者制作手册](production.md) · [主持人中英讲稿和模拟问答](script.md) · [中文字幕](captions.zh.srt) · [English subtitles](captions.en.srt)

讲者数字分身依据本人提供的蓝帽照片生成，普通话由独立的合成声音朗读。四道模拟问题是针对评审标准准备的预设问题。项目的公链回执和合约地址可独立核对。[源报价交易](https://sepolia.etherscan.io/tx/0xd97a9579a96a20c9868dd7f759079975e2ff1603eb903e42d3fd5ddfbbcc6604) · [Lasna 执行交易](https://lasna.reactscan.net/tx/0x63639779506a135ff8cba06c4d8aff5230d029aed5dc781f8f902868f54e8d27) · [Base 回调交易](https://sepolia.basescan.org/tx/0x5e2a48caaf7ab64dd3f25c4f4b804cf30d09aabc6f885efb44033b91ce3ce602) · [主办方评审标准](https://blog.reactive.network/reactive-omni-buildathon-thirty-days-to-find-out-what-one-second-buys/)
