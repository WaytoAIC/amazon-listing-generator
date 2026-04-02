# Module Prompts

## 使用原则

- 只读取当前任务需要的模块章节。
- 先完成输入归一化，再按模块骨架组织提示。
- 如果用户要求“整套输出”，按文末列出的固定顺序依次执行。

## MCP 联动总规则

- 如果系统接了 Sorftime、卖家精灵等 Amazon 数据 MCP，且用户没有给足关键词、竞品、评论或类目资料，先做数据补强。
- 关键词类数据优先喂给标题、五点、Search Terms、A+ 和视频脚本。
- 竞品结构类数据优先喂给标题、主附图 Brief、A+ 和现有 Listing 改写。
- 评论与问答类数据优先喂给五点、图片、视频脚本和 Rufus 验证。
- 市场与类目定位类数据优先喂给标题措辞、卖点排序和 A+ 价值主张。
- 任何销量、BSR、PPC、点击率、评论比例等数据只用于内部决策，不直接写进面向买家的文案。

## 1. 标题

### 适用场景

- 从零生成标题
- 重写标题
- 做移动端优先标题优化

### 必填输入

- `country_site`
- `language`
- `product_name`
- `brand` 可选
- `usps`
- `specs`
- `keyword_pool`
- `banned_terms`

### 输出格式

- 只输出 1 行标题
- 默认长度控制在 100 到 125 字符

### 硬性规则

- 开头放品类主词
- 自然融入 1 到 2 个主流词、1 到 2 个差异点和关键参数
- 不写夸大词、医疗承诺、注册符号、型号堆砌
- 可读性优先于关键词覆盖

### 提示词骨架

```text
【角色】
你是亚马逊 SEO 标题优化专家。

【输入】
- 国家/站点: {country_site}
- 语言: {language}
- 产品名(品类词): {product_name}
- 品牌(可选): {brand}
- 核心卖点/差异点: {usps}
- 关键参数: {specs}
- 关键词池: {keyword_pool}
- 禁用词/限制: {banned_terms}
- 参考竞品信息: {competitor_insights}
- 评论总结: {review_insights}

【任务】
生成 1 个适合 {country_site} 站的标题，移动端可读性强，兼顾 SEO 与可读性。

【输出】
仅输出标题一行。
```

## 2. 五点

### 适用场景

- 从零生成 5 条五点
- 改写五点的转化层级
- 强化前两条移动端表现

### 必填输入

- `language`
- `audience_scenarios`
- `usps`
- `specs`
- `keywords_optional`
- `compliance_notes`

### 输出格式

- 严格输出 5 行
- 每行 1 条五点
- 前 2 条偏转化，后 3 条偏埋词与 Rufus 支撑

### 硬性规则

- 每条只讲 1 个主题
- 尽量用动词开头
- 包含具体事实或数字
- 避免和标题重复堆砌
- 不允许医疗、极限词和无法证实的承诺

### 提示词骨架

```text
【角色】
你是亚马逊转化文案专家，熟悉移动端展示逻辑。

【输入】
- 语言/站点: {language}
- 用户人群/场景: {audience_scenarios}
- 核心卖点: {usps}
- 关键参数: {specs}
- 辅助关键词: {keywords_optional}
- 合规限制: {compliance_notes}
- 评论重点: {review_insights}

【任务】
生成 5 条五点。前 2 条承担转化，后 3 条承担索引、扩展语义和 Rufus 支撑。

【输出】
严格输出 5 行，每行 1 条五点。
```

## 3. Search Terms

### 适用场景

- 生成后台 Search Terms
- 在已有标题与五点基础上做未覆盖语义补位

### 必填输入

- `language`
- `country_site`
- `keyword_pool`
- `used_terms`
- `semantic_buckets`

### 输出格式

- 仅输出 1 行 Search Terms 字符串
- 总长度不超过 249 字节

### 硬性规则

- 只用空格分隔
- 不要品牌词、竞品词、标点和重复词根
- 必须先排除标题与五点中已使用词
- 优先装入未覆盖高价值词、同义词、错拼和拼写差异

### 提示词骨架

```text
【角色】
你是亚马逊后台关键词优化专家。

【输入】
- 语言/站点: {language}/{country_site}
- 关键词池: {keyword_pool}
- 已使用词: {used_terms}
- 需覆盖的语义域: {semantic_buckets}

【任务】
生成一条 Search Terms 字符串，长度不超过 249 字节。

【输出】
仅输出一行 ST 字符串。
```

## 4. 主附图设计需求

### 适用场景

- 生成主图与 6 张附图的设计 Brief
- 为设计师或 AI 作图工具准备信息结构

### 必填输入

- `country_site`
- `product_name`
- `usps_specs`
- `keyword_pool`
- `brand_tone`
- `image_constraints`

### 输出格式

- Markdown 表格
- 固定 7 行：主图、图 2 到图 7

### 硬性规则

- 主图纯白背景，无文字、Logo、水印
- 整体按移动端优先设计
- 图 2 和图 3 是转化关键位
- 图 4 到图 6 承接需求暗示、参数特写和信任建立
- 图 7 承接品牌与变体引导

### 提示词骨架

```text
【角色】
你是一名资深亚马逊电商视觉策划总监。

【输入】
- 国家/站点: {country_site}
- 产品名称: {product_name}
- 卖点与功能: {usps_specs}
- 核心关键词: {keyword_pool}
- 品牌调性: {brand_tone}
- 限制条件: {image_constraints}

【任务】
输出主图 + 6 张附图的视觉设计 Brief，要求可直接交付设计师或 AI 作图工具。

【输出】
仅输出 Markdown 表格。
```

## 5. A+设计需求

### 适用场景

- 生成 A+ 结构化 Brief
- 规划品牌模块、对比模块、功能模块和结尾 CTA

### 必填输入

- `country_site`
- `product_name`
- `brand_name`
- `usps`
- `audience`
- `keyword_pool`
- `brand_tone`
- `compliance_notes`

### 输出格式

- 表格形式
- 至少 6 个模块

### 硬性规则

- 模块化输出
- 必须覆盖品牌形象、价值主张、功能拆解、用户体验、品质安全、品牌故事或 CTA
- 文案简洁直白
- 不写促销、侵权、医疗或无根据承诺

### 提示词骨架

```text
【角色】
你是一名亚马逊 A+ 内容架构专家。

【输入】
- 国家/站点: {country_site}
- 产品名称: {product_name}
- 品牌名称: {brand_name}
- 核心卖点: {usps}
- 用户人群/场景: {audience}
- 关键词池: {keyword_pool}
- 品牌调性: {brand_tone}
- 合规限制: {compliance_notes}

【任务】
生成一份完整的 A+ 设计 Brief，至少 6 个模块。

【输出】
用表格输出每个模块的设计内容、文案重点、目标与素材规格。
```

## 6. 视频脚本

### 适用场景

- 生成 Listing 视频脚本
- 为 15 秒、30 秒或其他时长的视频制作分镜

### 必填输入

- `product_name`
- `title`
- `bullet_points`
- `other_product_info` 可选
- `duration` 可选

### 输出格式

- Markdown 表格
- 默认 30 秒
- 以 3 秒为一个分镜

### 硬性规则

- 先提炼产品卖点、目标人群、使用场景和视频创意点
- 脚本要能展示产品特点，不只是读文案
- 分镜要有动作、画面和信息目标

### 提示词骨架

```text
【角色】
你是电商产品视频脚本策划。

【输入】
- 产品名称: {product_name}
- 产品标题: {title}
- 产品五点: {bullet_points}
- 其他产品信息: {other_product_info}
- 视频时长: {duration}

【任务】
基于产品卖点和使用场景，输出适合 Listing 的产品视频脚本。

【输出】
按 Markdown 表格输出分镜脚本。
```

## 7. Rufus问答验证

### 适用场景

- 检查 Listing 是否覆盖高频购买疑问
- 发现 Rufus 无法稳定回答的缺口

### 必填输入

- `title`
- `bullet_points`
- `description`
- `backend_terms`
- `usps_specs`

### 输出格式

- Markdown 表格
- 至少 20 条问题

### 硬性规则

- 问题必须是完整自然语言
- 覆盖功能、兼容、安装、维护、安全、差异、售后等维度
- 回答只能基于明确存在的信息
- 如果无法确定，必须明确写“无法回答”或“部分可回答”

### 提示词骨架

```text
【背景】
Rufus 不会猜测商品能力，只会基于 Listing 中明确存在的信息作答。

【角色】
你是一名亚马逊 Listing 质检官，从 Rufus 视角验证当前 Listing 的可回答性。

【输入】
- 产品标题: {title}
- 五点描述: {bullet_points}
- 产品描述: {description}
- Search Terms & 后台属性: {backend_terms}
- 卖点与规格: {usps_specs}

【任务】
生成不少于 20 条真实买家问题，并基于 Listing 信息模拟 Rufus 作答。

【输出】
以表格输出 Question、Answer、Confidence、Missing Info。
```

## 8. Listing自查

### 适用场景

- 做生成前后的合规审查
- 检查潜在违规、信息冲突和移动端问题

### 必填输入

- `title`
- `images_info`
- `bullet_points`
- `description`
- `backend_keywords`
- `a_plus_content`

### 输出格式

- Markdown 表格
- 列固定为：模块、检查点、状态、问题说明、修改建议

### 硬性规则

- 必须检查标题、图片、五点、描述、后台关键词、A+、整体一致性
- 状态只用：合规 / 风险 / 违规
- 优先指出具体问题，不写空泛提醒

### 提示词骨架

```text
【角色】
你是一名亚马逊 Listing 合规审查官。

【输入】
- 标题: {title}
- 主图与附图: {images_info}
- 五点: {bullet_points}
- 产品描述: {description}
- 后台关键词: {backend_keywords}
- A+ 内容: {a_plus_content}

【任务】
逐项检查潜在违规、风险和信息不一致问题，并给出修改建议。

【输出】
以表格输出：模块 | 检查点 | 状态 | 问题说明 | 修改建议
```

## 全套生成顺序

1. 标题
2. 五点
3. Search Terms
4. 主附图设计需求
5. A+设计需求
6. 视频脚本
7. Rufus问答验证
8. Listing自查
