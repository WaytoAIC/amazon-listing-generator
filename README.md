# waytoaic-amazon-listing-generator

## Way to AIC | 通往AI电商之路

Fixed README prefix for Way to AIC repositories.

- 官网 / Website: [waytoaic.com](https://waytoaic.com) | [www.waytoaic.com](https://www.waytoaic.com)
- 社群招募 / Community: `Way to AIC社群招募 | WaytoAIC.com`
- 公众号 / WeChat Official Account: `维正 WaytoAIC`
- 知识星球 / Xiaozhixing: `AI电商之路 WaytoAIC`
- AIC = `AI Commerce`

在 AI 重塑商业的时代，我们希望和每一个拥抱 AI 的卖家，找到场景，定义问题，积累能力，设计系统，共同通往 AI 电商之路。

Way to AIC 不是教学，不是工具，而是一条所有电商人共同走的进化之路。

后续 Way to AIC 相关 GitHub 项目，默认都应在 README 顶部保留这一前缀区块。

### WaytoAIC 理念 | Principles

| 中文 | English |
|---|---|
| 场景先于方法 | Context before method |
| AI 的价值来自真实业务场景，而不是技术本身。 | AI creates value through real business contexts, not through technology alone. |
| 问题先于答案 | Problem before answer |
| 定义问题，比拥有工具更重要。 | Defining the problem matters more than collecting tools. |
| 系统胜过技巧 | System over tricks |
| 技巧是术，系统才是道，决定卖家的上限。 | Tricks are tactical; systems define long-term leverage and ceiling. |
| 共创优于独行 | Co-creation over solo progress |
| 我们相信，真正的进化发生在共同探索的过程中。 | Real evolution happens through shared exploration. |

---

中文 | [English](#english)

## Quick Install

```bash
# Codex
curl -fsSL https://raw.githubusercontent.com/WaytoAIC/waytoaic-amazon-listing-generator/main/install.sh | bash -s -- --target codex
```

```bash
# OpenClaw
curl -fsSL https://raw.githubusercontent.com/WaytoAIC/waytoaic-amazon-listing-generator/main/install.sh | bash -s -- --target openclaw
```

```bash
# Version-pinned
curl -fsSL https://raw.githubusercontent.com/WaytoAIC/waytoaic-amazon-listing-generator/v2.0.1/install.sh | bash -s -- --target codex --ref v2.0.1
```

复制即用。安装后重启 Codex / OpenClaw。

---

一个面向亚马逊卖家的 Listing 生成 skill：把产品资料、竞品结论、评论洞察和关键词池，做成一份能直接上架、经得起买家和 Alexa 购物助手（原 Rufus）追问的 Listing 交付包。

支持整套一键生成、只做单个模块、改旧稿、按上线数据复盘迭代。
如果系统已经接入 Sorftime、卖家精灵等 Amazon 数据 MCP，会先补强关键词、竞品、评论和类目数据，再进入起草。

## 中文

### v2.0 有什么不一样

- 先定问题再动笔：写之前先列出买家必答问题，写完逐条验证答上了没有；没依据的问题不回答、不暗示，记进待办
- 买家问什么不靠猜，直接问 Alexa：流水线第一步就是 Alexa 问答采集，问竞品摸清买家在意什么，问自己已上架的商品看它到底怎么答。三条路——你把 [amazon-alexa-insight](https://github.com/WaytoAIC/amazon-alexa-insight) 插件导出的 CSV / Excel / JSON 直接丢进来；或者本机装了它的命令行让 skill 自己跑；两样都没有就退回自己出题，流程照跑
- 补上后台属性表：先把准确数值定下来，文案照着写，前台和后台不打架
- 卖点先翻成用户故事：五点、图片、A+、视频共用一张表，不再各写各的
- 图片、A+、视频需求单升级：每张图只担一个任务、写明禁入元素、配英文生图提示词；视频给分镜表和一致性规则。只出需求单和提示词，不绑定任何作图或视频工具
- 长度交给脚本数：`scripts/check_listing.py` 检查长度、禁用字符、重复和表格是否齐全，检查结果由脚本写进交付文件
- 平台规则集中在一个文件：每条标明是硬性、建议还是经验，附帮助页出处和核对日期
- 新增变体族规则、复盘迭代模式（一轮最多改 2 个模块）、搜索覆盖版和转化表达版两个版本、缺品牌调性时的兜底

### 已适配的亚马逊 2026 规则

- 2026-07-27 起，除媒体类外，标题不得超过 75 字符（含空格）；新增 Item Highlights 字段，最多 125 字符
- 2026-05-13 起，Rufus 改名 Alexa for Shopping
- 含写实风格 AI 生成人物的图片和视频，上传前必须打元数据标签
- 2026-02-12 起，变体之间的评论共享范围收窄
- 规则核对日期 2026-09-18，出处见 [references/platform-rules.md](./references/platform-rules.md)。规则会变，拿不准时以亚马逊卖家后台帮助页的最新内容为准

### 流程

1. 准备：买家必答问题表 → 卖点翻成用户故事 → 关键词四层分配 → 后台属性表
2. 文字：标题和 Item Highlights → 五点和商品描述 → Search Terms
3. 视觉：图片需求单 → A+ 需求单 → 视频分镜表
4. 检查：Alexa 问答覆盖验证 → 合规检查（脚本最后跑）

交付物是一个按固定模板填好的 Markdown 文件：文案、后台属性表、关键词分配表、必答问题表、用户故事表、宣称依据表、上架前待办、三份需求单和检查结果。

### 它的核心方法

- 用户体验优先：标题、前两条五点、主图和前 3 张图优先保证一眼看懂
- 双读者：同时写给买家和亚马逊系统
- 明示原则：Alexa 购物助手只认 Listing 里明确写出的信息，所以买家会问的都要写清楚
- 不编造：每条宣称都要在你给的资料里找得到依据；只追问卡住当前模块的信息

### 仓库内容

- 主入口：[SKILL.md](./SKILL.md)
- 交付模板：[assets/listing-package-template.md](./assets/listing-package-template.md)
- 检查脚本：[scripts/check_listing.py](./scripts/check_listing.py)
- 平台规则：[references/platform-rules.md](./references/platform-rules.md)
- 输入规范：[references/intake-schema.md](./references/intake-schema.md)
- 方法说明：[references/workflow.md](./references/workflow.md)
- 12 个模块文件：[references/modules/](./references/modules/)
- 按需读的参考：[改旧稿与复盘迭代](./references/existing-listing.md)、[变体族](./references/variation-family.md)、[品牌调性兜底](./references/brand-os.md)、[MCP 数据补强](./references/mcp-data-enrichment.md)
- UI 元数据：[agents/openai.yaml](./agents/openai.yaml)
- 一键安装脚本：[install.sh](./install.sh)

### 检查脚本

只用 Python 标准库，3.8 以上即可。没有 Python 也能用这个 skill，只是长度改由 AI 人工估算并会注明。

```bash
python3 scripts/check_listing.py 你的交付文件.md --full --write-report
```

脚本只查长度、字符、重复和表格是否齐全，不判断宣称真假、类目特殊规则和图片视频。脚本通过不等于合规。

### 推荐使用方式

直接在 Codex 里说：

- `用 $waytoaic-amazon-listing-generator 根据这份产品资料生成整套 Listing`
- `用 $waytoaic-amazon-listing-generator 只生成亚马逊美国站标题、Item Highlights 和五点`
- `用 $waytoaic-amazon-listing-generator 把这条超过 75 字符的旧标题拆成合规标题和 Item Highlights`
- `用 $waytoaic-amazon-listing-generator 检查这份现有 Listing，先告诉我缺口，再重写标题和 Search Terms`
- `用 $waytoaic-amazon-listing-generator 验证 Alexa 购物助手能不能只靠这份 Listing 答上买家的问题`
- `用 $waytoaic-amazon-listing-generator 根据这份上线数据做一轮复盘迭代`

沿用旧说法也可以，比如“9 模块”“Rufus 问答验证”“Listing 自查”。

### 许可说明

- 当前仓库是公开可见、可学习和可使用的 `source-available` 仓库
- 默认不允许商用
- 如果你基于本仓库进行修改、二次分发或合并进更大的功能并对外提供，需要公开对应源码

---

## English

A listing-generation skill for Amazon sellers. It turns product facts, competitor insights, review findings, and keyword pools into a ready-to-upload listing package that holds up when shoppers and Alexa for Shopping (formerly Rufus) ask questions.

It supports full-pack generation, single-module output, existing-listing rewrites, and review-and-iterate rounds driven by post-launch data.
When Sorftime, Sellersprite, or similar Amazon data MCPs are connected, the skill enriches keyword, competitor, review, and category data before drafting.

### What is new in v2.0

- Questions first, copy second: the skill lists the questions a buyer must get answered before writing, then verifies each one after writing. Questions with no supporting facts are neither answered nor implied, and go to a to-do list
- Buyer questions are asked, not guessed: the pipeline opens with an Alexa question-collection step — competitors, to learn what buyers care about, and your own live product, to see what Alexa actually tells shoppers. Three ways in: hand over a CSV / Excel / JSON exported from the [amazon-alexa-insight](https://github.com/WaytoAIC/amazon-alexa-insight) extension, let the skill run its CLI if you have it installed, or skip it — the skill then writes its own questions and the pipeline still runs
- A backend attribute sheet: exact values are fixed first and the copy follows them, so the front end and the back end agree
- Selling points become user stories: bullets, images, A+, and video share one table instead of drifting apart
- Upgraded image, A+, and video briefs: one job per image, explicit forbidden elements, an English image-generation prompt per slot, and a video shot list with consistency rules. Briefs and prompts only; no image or video tool is called
- Lengths are counted by a script: `scripts/check_listing.py` checks lengths, banned characters, repetition, and table completeness, and writes its result into the deliverable
- One platform-rules file: every rule is marked as hard, recommended, or practice, with its help-page source and the date it was verified
- New: variation-family rules, a review-and-iterate mode (at most two modules per round), a search-coverage version and a conversion version on request, and a fallback when brand tone is missing

### Amazon 2026 rules covered

- Since July 27, 2026, titles must be 75 characters or fewer, including spaces, in all categories except media; the new Item Highlights field adds up to 125 characters
- Since May 13, 2026, Rufus is called Alexa for Shopping
- Images and videos with photorealistic AI-generated people must carry a metadata tag before upload
- Since February 12, 2026, review sharing across variations has been narrowed
- Rules were verified on 2026-09-18; sources are listed in [references/platform-rules.md](./references/platform-rules.md). Rules change; when in doubt, follow the latest Amazon Seller Central help pages

### Flow

1. Prepare: must-answer question table → selling points as user stories → four-layer keyword allocation → backend attribute sheet
2. Text: title and Item Highlights → bullets and product description → Search Terms
3. Visual: image brief → A+ brief → video shot list
4. Check: Alexa question coverage verification → compliance check (the script always runs last)

The deliverable is one Markdown file filled from a fixed template: copy, backend attribute sheet, keyword allocation table, must-answer question table, user story table, claim-evidence table, pre-launch to-do list, three briefs, and check results.

### Core method

- User experience first: the title, the first two bullets, the main image, and the first three images must be understood at a glance
- Two readers: write for the shopper and for Amazon's systems at the same time
- Explicit information: Alexa for Shopping only uses what the listing states, so everything a buyer may ask must be written down
- No fabrication: every claim must trace back to the facts you supplied; the skill only asks for information that blocks the current module

### Included files

- Main skill entry: [SKILL.md](./SKILL.md)
- Deliverable template: [assets/listing-package-template.md](./assets/listing-package-template.md)
- Checker script: [scripts/check_listing.py](./scripts/check_listing.py)
- Platform rules: [references/platform-rules.md](./references/platform-rules.md)
- Intake schema: [references/intake-schema.md](./references/intake-schema.md)
- Method: [references/workflow.md](./references/workflow.md)
- Twelve module files: [references/modules/](./references/modules/)
- Read on demand: [existing listings and iteration](./references/existing-listing.md), [variation families](./references/variation-family.md), [brand tone fallback](./references/brand-os.md), [MCP enrichment](./references/mcp-data-enrichment.md)
- UI metadata: [agents/openai.yaml](./agents/openai.yaml)
- Installer: [install.sh](./install.sh)

### Checker script

Python standard library only, 3.8 or later. The skill still works without Python; lengths are then estimated by the AI and labelled as such.

```bash
python3 scripts/check_listing.py your-package.md --full --write-report
```

The script only checks lengths, characters, repetition, and table completeness. It does not judge whether claims are true, category-specific rules, or images and video. A passing script does not mean the listing is compliant.

### Suggested prompts

- `Use $waytoaic-amazon-listing-generator to generate the full Amazon listing package from this product brief.`
- `Use $waytoaic-amazon-listing-generator to generate only the title, Item Highlights, and bullet points for Amazon US.`
- `Use $waytoaic-amazon-listing-generator to split this over-75-character title into a compliant title plus Item Highlights.`
- `Use $waytoaic-amazon-listing-generator to audit this existing listing draft, then rewrite the title and Search Terms only.`
- `Use $waytoaic-amazon-listing-generator to verify whether Alexa for Shopping can answer real buyer questions from this listing alone.`
- `Use $waytoaic-amazon-listing-generator to run one review-and-iterate round from this post-launch data.`

Older wording still works, such as "9 modules", "Rufus validation", or "listing self-check".

### License note

- This repository is public and source-available
- Commercial use is not allowed by default
- Public redistribution or derivative distribution must keep the same license set and publish the corresponding source code
