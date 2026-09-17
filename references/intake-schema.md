# Intake Schema

## 使用方式

任何任务开始前，先把用户提供的内容归一化为下面这套字段。不要直接拿原始长文本或原始表格逐模块硬套。

## 统一输入结构

```yaml
task_mode: full_pack | single_module | optimize_existing
requested_modules:
  - 标题
  - 五点
marketplace: US
language: en-US
product_name: ""
brand: ""
category_term: ""
audience_scenarios:
  - ""
usps:
  - ""
specs:
  - ""
compatibility:
  supported:
    - ""
  unsupported:
    - ""
package_contents:
  - ""
materials:
  - ""
certifications:
  - ""
keyword_pool:
  core:
    - ""
  secondary:
    - ""
  long_tail:
    - ""
semantic_buckets:
  - 功能
  - 场景
  - 人群
  - 材质
  - 兼容
keyword_allocation:
  title:
    - ""
  item_highlights:
    - ""
  bullets_aplus:
    - ""
  search_terms:
    - ""
  unused:
    - ""
competitor_insights:
  - ""
review_insights:
  pains:
    - ""
  expectations:
    - ""
  misuse:
    - ""
compliance_notes:
  - ""
brand_tone: ""
image_constraints:
  - 主图白底无字
  - 移动端优先
existing_listing:
  title: ""
  item_highlights: ""
  bullets: []
  description: ""
  search_terms: ""
  images_info: ""
  a_plus_content: ""
data_sources:
  user_materials:
    - ""
  marketplace_urls:
    - ""
  mcp:
    sorftime:
      enabled: false
      own_product_data: []
      keyword_data: []
      competitor_data: []
      review_data: []
      category_data: []
    sellersprite:
      enabled: false
      own_product_data: []
      keyword_data: []
      competitor_data: []
      review_data: []
      market_data: []
market_positioning:
  category: ""
  price_band: ""
  competitor_patterns:
    - ""
keyword_evidence:
  core:
    - ""
  supporting:
    - ""
  long_tail:
    - ""
review_evidence:
  pains:
    - ""
  expectations:
    - ""
  misuse:
    - ""
```

## 字段归一化规则

### 基础信息

- `marketplace` 和 `language` 必须明确，不能只写“美国站”而不落到输出语言。
- `product_name` 用用户搜索会理解的品类表达，不要只写内部型号。
- `brand` 允许为空；若为空，不要擅自补品牌。

### 事实字段

- `usps` 只保留真实卖点，不放营销口号。
- `specs` 优先转成“参数名 + 数值 + 单位 + 条件”的形式。
- `compatibility` 必须区分支持和不支持，避免把“不确定”写成“支持”。
- `package_contents` 只列实际随包装附带内容。
- `certifications` 只保留已确认的证据型信息。

### 洞察字段

- `competitor_insights` 写“什么信息值得前置”，不要只写竞品卖得好不好。
- `review_insights` 按痛点、期待、误用拆分，便于直接映射到五点、图片和 Rufus 问答。
- `semantic_buckets` 用于 Search Terms 和后 3 条五点的语义补位。
- `keyword_allocation` 是关键词四层分配的结果：核心产品词进 `title`，功能属性和材质词进 `item_highlights`，使用场景和购买理由词进 `bullets_aplus`，长尾词和同义词进 `search_terms`。禁用词、品牌或竞品品牌部分，以及资料里找不到依据的宣称类词进 `unused`，并写明原因。一条关键词只进一个位置，`unused` 里的词不进任何位置；用户没给时由前置步骤生成，不要求用户自己填。
- `market_positioning` 用于判断产品要站在哪个价格带、风格带和竞品带上说话。
- `keyword_evidence` 用于存放 Sorftime、卖家精灵等 MCP 跑出来的关键词证据，用户自带的搜索量或热度数据也放这里，不要和最终前台文案混写。
- `review_evidence` 用于存放评论抓取后的原始问题类型，便于回溯结论依据。

### MCP 数据字段

- `data_sources.mcp.sorftime` 和 `data_sources.mcp.sellersprite` 只记录“从哪里拿到什么类型的数据”，不要求逐条抄工具原始返回。
- `own_product_data` 可用于补事实，但如果与用户提供的官方资料冲突，必须先标冲突。
- `keyword_data`、`competitor_data`、`review_data`、`category_data`、`market_data` 属于辅助证据，主要用于排序、筛词和找缺口。
- 如果系统里有多个 Amazon 数据 MCP，可组合使用，但要避免把同一类结论当作多个独立事实重复叠加。

### 现有 Listing

- 只有在优化已有 Listing 时才填 `existing_listing`。
- 现有标题超过 75 字符时照原样填入，不要先行截短；拆分交给标题和 Item Highlights 模块处理。
- 如果用户只给了部分现有内容，只填写已知字段，不要脑补其余字段。

## 模块阻塞项

| 模块 | 最低阻塞输入 |
|---|---|
| 关键词四层分配（前置步骤） | product_name、keyword_pool、usps、specs |
| 标题 | marketplace、language、product_name、usps、specs、keyword_pool |
| Item Highlights | marketplace、language、已达标的标题、usps、specs、keyword_pool |
| 五点 | language、audience_scenarios、usps、specs |
| Search Terms | language、marketplace、keyword_pool、used_terms 或现有标题/Item Highlights/五点 |
| 主附图设计需求 | marketplace、product_name、usps_specs、brand_tone 或产品调性 |
| A+设计需求 | marketplace、product_name、brand、usps、audience_scenarios |
| 视频脚本 | product_name、标题或核心卖点、五点或场景信息 |
| Rufus问答验证 | title、bullets、description 或等价前台文本、backend_terms、usps_specs |
| Listing自查 | 至少要有被检查模块的现有内容 |

## 缺失信息处理

- 如果缺失项不阻塞当前模块，用“信息不足，已按现有事实保守输出”继续。
- 如果缺失项会导致核心结论失真，只追问最少量字段。
- 追问优先级：
  1. 站点 / 语言
  2. 产品是什么
  3. 关键参数
  4. 兼容 / 限制
  5. 用户场景
  6. 关键词池

## 事实与推断分离

- 用户原始资料、官方规格、包装清单、认证信息属于事实。
- 竞品总结、评论洞察、关键词意图属于推断性辅助信息。
- MCP 抓到的商品详情、关键词结果、评论结果和市场数据默认属于“外部证据”，除非用户确认，否则不要自动升级成前台事实。
- 最终前台文案只可以把推断用于“表达排序”和“卖点前置”，不能把推断写成新事实。
