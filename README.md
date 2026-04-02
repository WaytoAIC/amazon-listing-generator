# amazon-listing-generator

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
curl -fsSL https://raw.githubusercontent.com/WaytoAIC/amazon-listing-generator/main/install.sh | bash -s -- --target codex
```

```bash
# OpenClaw
curl -fsSL https://raw.githubusercontent.com/WaytoAIC/amazon-listing-generator/main/install.sh | bash -s -- --target openclaw
```

```bash
# Version-pinned
curl -fsSL https://raw.githubusercontent.com/WaytoAIC/amazon-listing-generator/v1.0.0/install.sh | bash -s -- --target codex --ref v1.0.0
```

复制即用。安装后重启 Codex / OpenClaw。

---

一个面向亚马逊卖家的 Listing 生成 skill，用于把产品资料、竞品结论、评论洞察和关键词池整理成完整的 Amazon Listing 产出包。

它默认支持完整 8 模块一键生成，也支持只生成单个模块，以及基于已有 Listing 草稿做审查和局部重写。
如果系统已经接入 Sorftime、卖家精灵等 Amazon 数据 MCP，这个 skill 会优先利用它们补强关键词、竞品、评论和类目数据，再进入 Listing 起草。

## 中文

### 这个 skill 会帮你做什么

- 生成标题、五点、Search Terms、主附图 Brief、A+ Brief、视频脚本、Rufus 问答验证和 Listing 自查
- 把零散产品信息先归一化，再按模块顺序输出，避免漏字段和模块间冲突
- 兼顾前台转化、移动端可读性、SEO 覆盖和 Rufus 可回答性
- 在已有 Listing 场景下，先识别事实缺口、风险和改写优先级，再只改指定模块
- 如果接了 Sorftime、卖家精灵等 MCP，会先补关键词证据、竞品结构、评论痛点和类目定位

### 它的核心方法

- 用户体验优先：标题、前两条五点、主图和前 3 张图优先保证一眼看懂
- 双读者逻辑：同时写给用户和亚马逊系统
- Rufus 明示原则：只基于 Listing 中明确存在的信息回答
- 最小追问原则：只有关键信息缺失时才追问阻塞项，不编造参数、认证、兼容范围或售后承诺

### 支持的 8 个模块

1. 标题
2. 五点
3. Search Terms
4. 主附图设计需求
5. A+设计需求
6. 视频脚本
7. Rufus问答验证
8. Listing自查

### 仓库内容

- 主 skill 入口：[SKILL.md](./SKILL.md)
- UI 元数据：[agents/openai.yaml](./agents/openai.yaml)
- SOP 与工作流说明：[references/workflow.md](./references/workflow.md)
- 输入归一化规范：[references/intake-schema.md](./references/intake-schema.md)
- MCP 数据补强规范：[references/mcp-data-enrichment.md](./references/mcp-data-enrichment.md)
- 8 模块提示骨架：[references/module-prompts.md](./references/module-prompts.md)
- 一键安装脚本：[install.sh](./install.sh)

### 推荐使用方式

直接在 Codex 里说：

- `用 $amazon-listing-generator 根据这份产品资料生成完整 Listing 8 模块`
- `用 $amazon-listing-generator 只生成亚马逊美国站标题和五点`
- `用 $amazon-listing-generator 检查这份现有 Listing，先告诉我缺口，再重写标题和 Search Terms`
- `用 $amazon-listing-generator 从 Rufus 视角检查这份 Listing 有没有回答不出来的问题`

### 许可说明

- 当前仓库是公开可见、可学习和可使用的 `source-available` 仓库
- 默认不允许商用
- 如果你基于本仓库进行修改、二次分发或合并进更大的功能并对外提供，需要公开对应源码

---

## English

This skill turns product facts, competitor insights, review findings, and keyword pools into a structured Amazon Listing workflow.

It supports both full-pack generation across eight modules and targeted single-module output, while also handling existing-listing audits and partial rewrites.
When Sorftime, Sellersprite, or similar Amazon data MCPs are connected, the skill enriches keyword, competitor, review, and category data before drafting.

### What it helps with

- generating titles, bullets, Search Terms, image briefs, A+ briefs, video scripts, Rufus validation, and listing self-checks
- normalizing fragmented inputs before drafting so modules stay consistent
- improving mobile-first readability, SEO coverage, and Rufus answerability at the same time
- auditing an existing draft first, then rewriting only the requested modules
- enriching the brief with connected Amazon data MCPs before writing when more evidence is needed

### Included files

- Main skill entry: [SKILL.md](./SKILL.md)
- UI metadata: [agents/openai.yaml](./agents/openai.yaml)
- Workflow reference: [references/workflow.md](./references/workflow.md)
- Intake normalization schema: [references/intake-schema.md](./references/intake-schema.md)
- MCP enrichment guide: [references/mcp-data-enrichment.md](./references/mcp-data-enrichment.md)
- Module prompt skeletons: [references/module-prompts.md](./references/module-prompts.md)
- Installer: [install.sh](./install.sh)

### Suggested prompts

- `Use $amazon-listing-generator to generate the full 8-module Amazon Listing pack from this product brief.`
- `Use $amazon-listing-generator to generate only the title and bullet points for Amazon US.`
- `Use $amazon-listing-generator to audit this existing listing draft, then rewrite the title and Search Terms only.`
- `Use $amazon-listing-generator to validate whether Rufus can answer real buyer questions from this listing.`

### License note

- This repository is public and source-available
- Commercial use is not allowed by default
- Public redistribution or derivative distribution must keep the same license set and publish the corresponding source code
