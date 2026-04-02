---
name: amazon-listing-generator
description: 生成和优化亚马逊 Listing 全套内容的内部团队技能。用于根据产品资料、竞品结论、评论洞察和关键词池，生成或重写标题、五点、Search Terms、主附图 Brief、A+ Brief、视频脚本、Rufus 问答验证和 Listing 自查；也用于移动端优先优化、SEO 与 Rufus 协同改写、已有 Listing 审核和局部重写。
---

# Amazon Listing Generator

## 概述

先把零散产品资料整理成统一字段，再按任务选择全套生成、单模块生成或已有 Listing 优化。协作说明默认用中文，面向亚马逊前台的最终文案必须按目标站点语言输出。

## 使用顺序

1. 先读 [references/intake-schema.md](./references/intake-schema.md)，把用户提供的信息整理成统一输入结构。
2. 再读 [references/workflow.md](./references/workflow.md)，确认移动端优先、双读者、Rufus 明示和完整生成顺序。
3. 最后只读取 [references/module-prompts.md](./references/module-prompts.md) 中与当前任务有关的模块章节，不要把全部模块一起加载。

## 任务判断

- 如果用户要“整套 Listing”“完整产出”“一键生成”，走全套生成模式。
- 如果用户只点名标题、五点、Search Terms、主图需求、A+、视频脚本、Rufus 验证或 Listing 自查，走单模块模式。
- 如果用户提供已有 Listing 草稿，且目标是优化、改写、审查或补齐，先做缺口识别，再只处理被要求的模块。

## 执行规则

- 全套生成固定按以下顺序输出：
  1. 标题
  2. 五点
  3. Search Terms
  4. 主附图设计需求
  5. A+设计需求
  6. 视频脚本
  7. Rufus问答验证
  8. Listing自查
- 单模块模式只输出用户点名的模块，不顺带生成其他模块。
- 已有 Listing 优化模式先做缺口识别，再只重写用户指定模块；如果未指定模块，优先给出审查结论和改写优先级。
- Search Terms 必须依赖已生成或已提供的标题与五点，确保正确排除 `used_terms`。
- Rufus 验证只能基于 Listing 中明确写出的文本、参数和属性回答，不能用常识补完。
- 自查模块必须输出结构化检查表，覆盖标题、图片、五点、描述、后台关键词、A+ 与整体一致性。

## 缺失信息处理

- 缺失信息时，先判断是否阻塞当前模块。
- 只追问阻塞项，不要做宽泛访谈。
- 凡是用户可能会问“具体是多少”的参数，都应要求明确化。
- 绝不编造规格、兼容范围、认证、保修、售后、材质、安全结论或任何合规声明。
- 用户提供的事实优先于常见市场写法；如果事实彼此冲突，先指出冲突再继续。

## 输出要求

- 默认先用中文说明思路、缺口和风险，再输出目标站点语言的前台文案或结构化 Brief。
- 如果用户明确指定只要最终文案，则只输出目标产物。
- 如果用户给的是已有 Listing，先给差距判断，再输出改写结果。
- 如果用户要求图片、A+、视频模块，输出必须足够结构化，能直接给设计师或视频团队使用。

## 参考文件

- [references/intake-schema.md](./references/intake-schema.md)
  - 统一输入字段、字段归一化规则、各模块阻塞项判断。
- [references/workflow.md](./references/workflow.md)
  - 好 Listing 的判断标准、SOP 流程、移动端优先和 Rufus 视角约束。
- [references/module-prompts.md](./references/module-prompts.md)
  - 8 个模块的适用场景、必填输入、输出契约、硬规则和提示词骨架。

## 质量底线

- 用户可读性优先于机械埋词，尤其是标题、前两条五点、主图与前 3 张图、A+ 首屏。
- 前台表述、后台属性和 Rufus 可回答信息必须一致。
- 所有结论都应来自明确事实、竞品提炼、评论洞察或关键词语义，不要用空泛形容词堆砌。
