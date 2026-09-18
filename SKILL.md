---
name: amazon-listing-generator
description: 生成和优化亚马逊 Listing 全套内容。先定买家必答问题、用户故事、关键词分配和后台属性，再写标题（不超过 75 字符）、Item Highlights、五点、商品描述、Search Terms，出图片、A+、视频需求单，最后做 Alexa 购物助手（原 Rufus）问答覆盖验证和带脚本的合规检查。也用于只做单个模块、把超长旧标题拆成合规标题加 Item Highlights、审核和改写已有 Listing、按上线数据复盘迭代。接入 Sorftime、卖家精灵等 Amazon 数据 MCP 时先做数据补强。
metadata:
  version: "2.0.0"
---

# Amazon Listing Generator

一句话：针对特定场景 × 特定人群 × 特定需求，讲清楚这个产品给出了什么解决办法。Listing 是买家和 Alexa 购物助手（原 Rufus）回答问题用的资料库，写清楚的才会被用上。协作说明用中文，面向亚马逊前台的文案按目标站点语言输出。

## 先判断任务

| 用户要什么 | 模式 | 怎么走 |
|---|---|---|
| “整套”“完整产出”“一键生成”“9 模块” | 全套生成 | 按下面的流水线从头走到尾 |
| 只点名某个模块 | 单模块 | 查 references/intake-schema.md 的“最低输入和前置步骤”表，只补做表里列出的准备步骤，只写点名的模块。为它做的准备表照常留在交付文件里 |
| 给了现有 Listing，要优化、改写、审查 | 改旧稿 | 读 references/existing-listing.md |
| 给了上线后的数据，要复盘、迭代 | 复盘迭代 | 读 references/existing-listing.md |

同时符合两行时，给了现有 Listing 的一律先走改旧稿流程，再在里面做用户点名的事。所有模式都先读 references/intake-schema.md 整理输入。资料明显不够时读 references/workflow.md。系统接了 Sorftime、卖家精灵等数据工具，且用户给的关键词、竞品或评论资料不够时，读 references/mcp-data-enrichment.md 先补强。

## 流水线

下表是全套生成的顺序。单模块任务做哪些准备步骤，以 references/intake-schema.md 的表为准，不看这里的最后一列。每一步只读它自己的文件，做完再读下一个。平台的数字（长度、条数、字节、像素）只在 references/platform-rules.md，按需读对应小节。

| 段 | 步骤 | 读哪个文件 | 全套生成时什么情况跳过 |
|---|---|---|---|
| 准备 | 买家必答问题表 | references/modules/00-must-answer-questions.md | — |
| 准备 | 卖点 → 用户故事 | references/modules/01-user-stories.md | — |
| 准备 | 关键词四层分配 | references/modules/02-keyword-allocation.md | — |
| 准备 | 后台属性表 | references/modules/03-backend-attributes.md | — |
| 文字 | 标题 + Item Highlights | references/modules/10-title-highlights.md | — |
| 文字 | 五点 + 商品描述 | references/modules/11-bullets-description.md | 描述：能做 A+ 且用户没要时不写 |
| 文字 | Search Terms | references/modules/12-search-terms.md | — |
| 视觉 | 图片需求单 | references/modules/20-image-brief.md | — |
| 视觉 | A+ 需求单 | references/modules/21-aplus-brief.md | brand_registered 为 no |
| 视觉 | 视频分镜表 | references/modules/22-video-shotlist.md | — |
| 检查 | Alexa 问答覆盖验证 | references/modules/30-alexa-coverage-check.md | — |
| 检查 | 合规检查（跑脚本） | references/modules/31-compliance-check.md | — |

按需读：有变体读 references/variation-family.md；要做视觉模块而没有品牌调性，读 references/brand-os.md；要拿买家真实问过的问题，读 references/alexa-insight.md。

## 交付

- 把 assets/listing-package-template.md 复制到用户的工作目录再填；不改各级标题和表头；任务没涉及的小节整节删掉；开头那段用法说明填完后删掉。边做边写，不要攒到最后。
- 单模块任务里，用户已有、且没要求改的标题、Item Highlights 等，照原样填进对应小节（脚本顺带检查，去重也要用到），并说明哪些是用户给的、没动。改旧稿时不这样做：旧文案只放在旧稿文件里，交付文件只放这次改的模块。
- 交付文件命名：`listing-<商品英文简称>-<站点>.md`。
- 思路、缺口和风险用中文在对话里说；改旧稿和复盘迭代另把结论写进交付文件的「体检结论」。用户说只要最终文案时：该做的准备照做，交付文件只留文案小节、「上架前待办」和检查结果，其余表格不给。
- 用户要两个版本时（output_versions 为 two_versions）：搜索覆盖版给新品期，关键词覆盖优先；转化表达版给成熟链接，可读性和说服力优先。只有标题、Item Highlights、五点、Search Terms 不同，第二版另存一个文件，其余表和需求单共用。

## 检查和回头改

- 单模块任务：合规检查照做，脚本只查文件里有的小节；Alexa 问答覆盖验证只在任务包含五点、描述或 A+，或用户点名时才做。
- 用户说只检查、先不改文案时：两道检查只出结论，不补写，不为了通过去改了重跑；脚本报的不通过项就是要报告的问题。
- 问答覆盖验证发现“有依据却没覆盖”的，回去补写一次。
- 最后一次改文案之后，必须跑过检查脚本。不通过就改了重跑，最多两轮，之后如实报告还差什么。脚本通过后不再改文案。
- 脚本是 `scripts/check_listing.py`，路径从本文件所在目录算起。没有 python 时人工核对，并注明“人工估算”。

## 红线

- 不编造：规格、兼容范围、认证、保修、材质、安全结论，资料里没有的一个字不写；没依据的买家问题不回答，也不暗示。
- 用户给的事实优先；事实互相冲突时先指出来。
- 待核实的事实（供应商口头说的、数据工具抓来的、推断的）默认不写进买家可见的文案：记进「上架前待办」（核实），附上核实后可以直接加的那句话；用户明确要写才写。用户自己测的数据算已确认。
- 数据工具来的销量、排名、点击率、评论比例只用于内部判断，不进买家可见的文案。
- 平台数字只认 references/platform-rules.md；今天距它的核对日期超过 6 个月，先提醒用户规则可能已变。
- 图上出现的卖点，文案里要有，后台属性里要填。
- 图片、A+、视频只出需求单和提示词，不调用作图或视频工具。
- 复盘迭代一轮最多改 2 个模块。
- 缺信息只追问卡住当前模块的项，不做宽泛访谈。
