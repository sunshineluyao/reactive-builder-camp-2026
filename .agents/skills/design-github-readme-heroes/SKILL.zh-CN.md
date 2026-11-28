---
name: design-github-readme-heroes
description: Create, redesign, or audit the lead figure in a GitHub repository's root README. Use for project covers, architecture heroes, visual abstracts, and README banners that need a distinctive project identity, an accurate first-glance explanation, and legible desktop and phone layouts. Also use when a user supplies a reference cover and wants its visual quality carried across projects.
---

# 设计 GitHub README 首图

[English](SKILL.md) · **简体中文**

让初次访问的人看懂一个问题、图中的答案，以及可以亲自核对的证据。

## 决定首屏讲什么

1. 打开实际的根 README 及其引用的首图，以仓库中能证明核心结论的最少材料为依据，例如合约、运行记录、评估、样例输出或设计说明。重做首图时，先按 README 的实际列宽查看旧图。
2. 用一句话说明读者是谁、项目的独特机制、已观察的结果及其适用范围。标明设计、模拟、部署与实测的区别。沿用项目公开名称和署名。概念项目也可以用一个明确标记的设计问题来组织首图。
3. 按实际显示宽度观察参考图。提取阅读顺序、视觉中心、留白、色彩角色、字体和领域符号，再为本项目重新绘制。只有得到授权的个人或非公开素材才可进入公开交付件。

## 构图

- 让项目名和简短问题或发现首先进入视野。把最醒目的空间留给项目的独特机制。
- 让证据决定构图。流程可以展示路径，阈值适合标在刻度上，数据集可以放大一个真实样本，实验比较应写明单位。见[构图示例](references/layout-recipes.zh-CN.md)。
- 设计一个读者能认出的项目专属图形。使用一致网格、克制的底色和少数各有意义的强调色。用文字或形状重复颜色的含义，让标签与连线各有空间。技术题材可试用深色底配薄荷绿、紫色和琥珀色。
- 先做小幅配色试验。用最深色压住背景，略微提亮关键机制，把最高饱和度留给支持结论的标记。根据真实对象画出轮廓和两三个有意义的内部细节，可用定向光、暗面或刻线增加体积感。光晕和纹理应避开小字。
- 标签使用日常语言。较长的标识符、细节、致谢或操作说明放在邻近正文中。读者可能误判项目成熟度或证据来源时，标注状态。用具体结果或核验入口收尾。
- 按实际显示尺寸构图。桌面稿可从约 2:1 开始，在 README 列宽下查看，目标文字约 14–18 CSS 像素或更大。手机版重新堆叠或精简信息，保留标题、机制、结果与证据限制。

## 制作和嵌入

1. 精确的标签、数据和连线使用可编辑原生 SVG。写明 viewBox、尺寸、内嵌样式、标题、描述和系统字体回退，内部引用使用片段。两种布局共享测量数据时可用确定性的生成脚本。插画和精确文字数据分层，记录实际工具与证据来源。
2. 首图放在项目标题下，详细技术图保留在相关章节。替代文本应简洁具体，与 README 读者的语言一致；旁边放可核验证据的普通链接。
3. 手机构图不同时，使用 GitHub 支持的 picture 元素，窄屏来源在前，宽屏图兜底。在内容开始难读处设置断点，另附手机版直接链接。投影片、社交分享或静态预览可用 PNG。

```html
<picture>
  <source media="(max-width: 720px)" srcset="docs/hero-mobile.svg">
  <img src="docs/hero.svg" width="100%" alt="说明项目的机制与结果。">
</picture>
```

## 发布前核对

- 用 Python 3、Playwright 和 Chromium 运行检查器，例如 `python scripts/check_hero.py docs/hero.svg --mobile docs/hero-mobile.svg --out /tmp/hero-review`。使用 `--browser` 指定浏览器，`--breakpoint` 与 README 对齐，`--export-wide cover.png` 输出 PNG。检查器验证 SVG 自包含、响应式布局、深浅主题、文字出界、过小标签和疑似重叠。
- 打开预览，沿每条箭头查看走向。在真实底色上检查文字对比和对齐，以正常大小阅读，再看缩略图和灰度版。仔细核对每个数值、单位、分支和状态。过小的文字可放大或移至旁边正文。
- 检查托管平台实际显示的 README，包括手机选图和备用图。交付首图、可编辑源文件和所在位置，并说明实际做过的验证。
