# 怎样制作一场可以复核的科学动画演示

这次制作围绕一个可以当场判断的问题展开。模拟报价从 0.9990 走到 0.9950，再走到 0.9930，哪一步会触发告警？先用动画解释规则，再切到程序的实际输出。字幕、讲稿、幻灯片和主持人的时间表使用同一组数字。最后把展示和模拟问答编入一个文件。

## 各个画面的证据

| 画面 | 来源 | 可以从中得出什么 |
| --- | --- | --- |
| 绿带与三个报价点 | Wanim 运行项目的 Python 场景，使用整数基点计算阈值 | 边界也属于观察区间。两个示例间的连续运动是插值，0.9950 是讲解边界用的示例。 |
| 三笔交易 | 复核器读取三个网络，核对交易回执和相应区块。源日志序号为 2。 | 三条记录属于同一条 0.9930 模拟报价。首尾区块时间戳在本次运行中相差 2 秒。 |
| AI 的三个结果 | 公网事件缺同期参考价，随后在复核器里依次选择两组标明为合成的数据 | 暂缓评分是公网运行结果。升级复核与继续观察是在同一事件上进行的两次对照演示。 |
| 金额上限和失败恢复 | 单独运行新版 Solidity 合约的 15 项 Foundry 测试 | 测试证明新版本的保护规则。上面的公网交易来自加设费用上限前的部署。 |
| 蓝帽讲者与问答 | 讲者本人提供参考照。两幅生成姿态配通用普通话合成旁白，问答为预先撰写。 | 这是获讲者授权的预录数字分身。现场观众提出的问题由主持人另行收集。 |

[Wanim 场景](../visual/threshold.py) · [三份原始回执](../evidence/public-run.json) · [模型卡](../model/MODEL_CARD.md) · [保护测试](../tests/StablecoinGuards.t.sol)

## 软件与输入输出

| 环节 | 本次使用的软件或素材 | 输入与输出 |
| --- | --- | --- |
| 校验公开数据 | Python 3.12.14、项目 RPC 核验器、Foundry 1.7.1、Solidity 0.8.29 | 核验源交易哈希、规范区块、事件 ID、金额和日志索引。独立运行新版合约的测试。 |
| 画科学动画 | Wanim 0.1.3、numpy-ts 1.7.0 | 浏览器把 Manim 风格的 Python 场景编译并绘制到 Canvas。轨迹的纵坐标、标记颜色与触发状态由同一报价计算。项目按 SHA-512 校验网页运行库。 |
| 录真实界面 | Python Playwright 1.62.0、Chrome for Testing 158.0.8127.88 | 无头浏览器驱动真实控件，录下两个边界过渡和三个复核结果。脚本在三份公链回执全部通过校验后才采集应用画面。 |
| 制作数字分身 | ChatGPT 图像生成、FFmpeg 裁切 | 根据讲者选定的蓝帽会议照生成一张双姿态图，分别导出闭口和轻微张口图。公开制作素材为生成后的姿态。 |
| 生成普通话旁白 | sherpa-onnx 1.12.30、MeloTTS Chinese/English 单讲者模型、ONNX INT8 | 逐句朗读中文讲稿，日期、价格和代币名有独立的发音处理。用同一通用声音朗读模拟提问和回答。 |
| 制作幻灯片 | ChatGPT Spaces、Artifact Tool 2.8.194、python-pptx 1.0.2 | 一份布局定义供在线编辑稿和离线 PowerPoint 使用。文字、表格、演讲备注和外链可以编辑。离线复现仅需开源 Python 写入器。 |
| 输出 PDF 和视频底稿 | LibreOffice Impress（本次为 26.8 开发版）、PyMuPDF 1.26.6 | 直接从离线 PPTX 导出十页 PDF，按 1280 × 720 光栅化，保证视频与投影幻灯片使用同一布局。 |
| 对时、合成与字幕 | NumPy 2.3.5、Pillow 13.0.0、FFmpeg/ffprobe 7.1.5、libx264、AAC、libass、Fontconfig | 对齐声音、姿态、实际录屏和双语字幕。投影字体为 Noto Sans CJK SC 和 DejaVu Sans。输出一个 H.264/AAC MP4，并写入章节。 |

[Wanim 使用文档](https://wanim.org/docs/usage/) · [Playwright Python](https://playwright.dev/python/) · [Chrome for Testing](https://googlechromelabs.github.io/chrome-for-testing/) · [MeloTTS](https://github.com/myshell-ai/MeloTTS) · [转换后的 ONNX 模型](https://huggingface.co/csukuangfj/vits-melo-tts-zh_en/tree/a0d5c6a264c0ef92d70d8661d8cc502d79627cd6) · [sherpa-onnx](https://k2-fsa.github.io/sherpa/onnx/tts/) · [python-pptx](https://python-pptx.readthedocs.io/) · [FFmpeg](https://ffmpeg.org/documentation.html)

## 制作顺序

1. **按评委的问题编排叙事。** 前六页从财库人员看到 0.9930 开始，依次回答门槛、链上执行、人工复核和付款保护。后四页分别回答 Execution、Integration、Usefulness 和 Craft。中文是播出稿，英文是字幕与备注的译文。[双语讲稿](source/story.json)
2. **先验证，再录屏。** 价格门槛使用 `abs(priceBps - 10000) > 50`。控制组、边界值、触发值和两个过渡分别截图。浏览器随后检查公开回执，依次读取“证据不足”“升级复核”“继续观察”。录制程序断言页面状态和三笔外链都存在。[采集脚本](source/capture.py)
3. **制作两种讲者姿态。** 人物视觉简报是保留参考照中的脸部特征、蓝色棒球帽与紫色边光，以深蓝工作台背景和休闲外套表现 hacker house 氛围。要求画面左右各一名相同尺寸的同一讲者，保持机位、眼睛和肩膀的位置，只改变嘴部姿态。冻结导出的两幅图，后续重剪可以直接复用。[静态姿态](media/avatar.jpg) · [说话姿态](media/avatar-speaking.jpg)
4. **先确定语句时长，再加运动。** 合成器逐句输出音频，去掉前后过长的静音，再由 FFmpeg 统一语速。成片对整轨人声做两遍响度归一化，目标为 −16 LUFS，方便会场播放。段内与换页采用不同停顿。每秒采样 24 次声音强弱，平滑后在两种嘴部姿态间混合。这个方法按音量近似开合，不做逐音素口型识别。屏幕上的“数字分身与合成旁白”向观众披露制作方式。[对时与字幕](source/audio.py) · [视频合成](source/film.py)
5. **出两种交付格式。** 讲者和主持人获得可编辑的 PowerPoint 与带链接的 PDF。视频将其与真实 Wanim 帧、复核器画面和数字讲者合成，在同一条时间线上写入中英字幕。00:00–02:50 展示项目，02:50–04:40 播放预设问答。[离线幻灯片生成器](source/layout.py) · [在线版布局适配](source/native.mjs)
6. **验收后分享。** 复查十页 PDF、演示截图、公开数据版本差异、价格标签、字幕安全区、视频时长、音轨、章节和播放器的跳转。训练营作业可提交幻灯片链接。登记表只需填写一个视频链接。[逐栏登记文本](registration.txt)

## 本地复现

下面的命令从仓库根目录开始。使用 Python 3.12、FFmpeg（含 libass、libx264 和 AAC）、LibreOffice、Fontconfig 及上述字体。Foundry 用于复核保护测试。首次构建需要下载浏览器、Wanim 包和语音模型。已发布的 MP4、PPTX 和 PDF 可直接离线使用。

```sh
cd track3
forge test
python3 scripts/verify_receipts.py evidence/public-run.json --destination-rpc https://base-sepolia-rpc.publicnode.com
cd demo-day
python3 -m venv /tmp/alerts-venv
. /tmp/alerts-venv/bin/activate
python -m pip install -r source/requirements.txt
python -m playwright install chromium
WORK="$(mktemp -d)"
mkdir -p "$WORK/pdf"
python source/get_voice.py "$WORK/melo"
DESTINATION_RPC=https://base-sepolia-rpc.publicnode.com python source/capture.py "$WORK/capture"
python source/audio.py "$WORK/sound" "$WORK/melo"
python source/layout.py "$WORK/Stablecoin-Alerts-Demo-Day.pptx"
soffice --headless --convert-to pdf --outdir "$WORK/pdf" "$WORK/Stablecoin-Alerts-Demo-Day.pptx"
python source/film.py "$WORK" "$WORK/pdf/Stablecoin-Alerts-Demo-Day.pdf" "$WORK/Stablecoin-Alerts-Demo-Day.mp4"
ffprobe -v error -show_entries format=duration:stream=codec_name,width,height -show_chapters "$WORK/Stablecoin-Alerts-Demo-Day.mp4"
```

如需指定浏览器，可为 `capture.py` 增加 `--chrome /path/to/chrome-headless-shell`。公网 RPC 可按脚本说明用 `ORIGIN_RPC`、`REACTIVE_RPC` 和 `DESTINATION_RPC` 切换。音频程序会写出双语 SRT，视频程序会写出本目录的演示截图。要让离线 PowerPoint 使用重录截图，将采集目录的 `chart-2.png`、`trace.png`、`model-insufficient.png` 依次复制到 `media/wanim-still.png`、`media/trace.png`、`media/decision.png`，再导出幻灯片。重新合成语音和使用不同浏览器、编码器或字体版本时，画面与语音的字节可能不同。固定的节目时长、报价分类和三种复核状态可逐项核验。

语音下载脚本固定了 ONNX 模型的仓库修订及 SHA-256。讲稿与项目新代码沿用项目 MIT 许可。MeloTTS 和转换模型附 MIT 许可。分发人物形象时请保留数字分身说明，人物肖像按讲者授权用于本次展示。[语音模型许可](https://huggingface.co/csukuangfj/vits-melo-tts-zh_en/blob/a0d5c6a264c0ef92d70d8661d8cc502d79627cd6/LICENSE) · [项目许可证](../LICENSE)
