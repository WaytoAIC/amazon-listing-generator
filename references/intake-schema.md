# 输入规范

任何任务开始前，先把用户给的内容整理成下面这套字段。不要拿原始长文本或表格逐模块硬套。全 skill 只用这一套字段名。

## 字段

```yaml
task_mode: full_pack | single_module | optimize_existing | review_iterate
requested_modules: []
output_versions: single            # 或 two_versions，只在用户要求时用

# 基础
marketplace: US
language: en-US
product_name: ""                   # 买家搜得懂的品类叫法，不是内部型号
brand: ""                          # 可空，不要替用户补
brand_registered: unknown          # yes | no | unknown，决定能不能做 A+
category_term: ""
variation_family:                  # 没有变体就留空
  theme: []                        # 颜色、尺寸、件数……
  children: []                     # 每个子体：名称 + 和兄弟不同的事实

# 事实（只收用户资料里有的；拿不准的在后面标“待核实”）
usps: []
specs: []                          # 参数名 + 数值 + 单位 + 条件
compatibility: {supported: [], unsupported: []}
package_contents: []
materials: []
certifications: []
attribute_template: []             # 用户类目模板里的属性名，可空

# 人群与场景
audience_scenarios: []
not_suitable_for: []               # 不适合谁、什么情况下别买

# 关键词与限制
keyword_pool: {core: [], secondary: [], long_tail: []}   # 每条可带热度和出处
semantic_buckets: []               # 功能、场景、人群、材质、兼容
banned_terms: []                   # 能机器核对的禁用词
compliance_notes: []               # 其余用文字写的限制

# 市场
competitor_insights: []            # 写“什么信息值得前置”，不写谁卖得好
review_insights: {pains: [], expectations: [], misuse: []}   # 每条可带出处
buyer_questions: []                # 实测或实采的 Alexa 问答、竞品问答、客服高频问题；每条记来源
market_positioning: {category: "", price_band: "", competitor_patterns: []}

# 品牌与视觉
brand_tone: ""
product_photos: []                 # 手上有哪些角度和素材
visual_references: []              # 参考图、参考品牌、竞品链接
image_constraints: []
video_plan: {channel: "", duration: "", production: ""}   # production：AI 生成 | 实拍

# 现有 Listing 与复盘
existing_listing:
  title: ""
  item_highlights: ""
  bullets: []
  description: ""
  search_terms: ""
  backend_attributes: []
  images_info: ""
  a_plus_content: ""
performance_data: {}               # 曝光、点击率、转化率、退货和差评主题、上次改了什么
iteration_log: []                  # 以前各轮的迭代记录

# 数据来源
data_sources:
  user_materials: []
  marketplace_urls: []
  mcp: {sorftime: {enabled: false}, sellersprite: {enabled: false}}
  alexa_insight: {enabled: false, runs: []}   # Alexa 问答采集，见 alexa-insight.md
```

过程产物由前置步骤生成，不要求用户填：`must_answer`（必答问题表）、`user_stories`（用户故事表）、`keyword_allocation`（title / item_highlights / bullets_aplus / search_terms / unused）、`backend_attributes`（后台属性表）。

## 整理规则

- `marketplace` 和 `language` 必须明确，不能只写“美国站”。
- 事实字段只放真实信息，不放营销口号。`compatibility` 必须分开写支持和不支持，“不确定”不能写成“支持”。
- 每条事实默认“已确认”，用户自己测的数据也算。数据工具抓来的、供应商口头说的、推断出来的，在后面标“待核实”；待核实的事实默认不写进文案，记进「上架前待办」（核实）。
- `banned_terms` 放能逐词核对的词；说不清词、只能描述的限制放 `compliance_notes`。
- `existing_listing.title` 超长也照原样填，不要先行截短。用户只给了部分现有内容时，只填已知字段。
- 竞品总结、评论洞察、关键词意图都是辅助判断，只能影响“先写什么、怎么排序”，不能变成新事实。

## 各模块最低输入和前置步骤

| 模块 | 缺了就不能做的输入 | 需要先做的准备步骤 |
|---|---|---|
| 必答问题表 | product_name、usps、specs | — |
| 用户故事表 | usps、audience_scenarios | 必答问题表 |
| 关键词四层分配 | product_name、keyword_pool、usps、specs | — |
| 后台属性表 | specs、materials、compatibility、package_contents | — |
| 标题、Item Highlights | marketplace、language、product_name、usps、specs | 关键词四层分配 |
| 五点、商品描述 | language、audience_scenarios、usps、specs | 必答问题表、用户故事表、关键词四层分配 |
| Search Terms | language、marketplace、keyword_pool | 关键词四层分配；已写好或用户提供的标题、Item Highlights、五点 |
| 图片需求单 | marketplace、product_name、usps、specs | 必答问题表、用户故事表 |
| A+ 需求单 | 同上，且 brand_registered 不是 no | 必答问题表、用户故事表 |
| 视频分镜表 | product_name、usps、product_photos | 必答问题表、用户故事表 |
| Alexa 问答覆盖验证 | 被检查的文案 | 必答问题表（没有就先建） |
| 合规检查 | 被检查的文案 | — |

单模块任务只补做表里列出的准备步骤，不把整条流水线跑一遍。

## 做图片、A+、视频前先清点六类输入

缺哪类就提醒用户会有什么后果，不因此停工。

| 输入 | 至少要有 | 缺了会怎样 |
|---|---|---|
| 产品素材 product_photos | 白底图、实拍图、配件图，最好有多个角度 | 主体不稳，换个角度就画错 |
| 产品信息 | 标题、五点、材质、参数、场景、人群 | 出图普通，卖点不聚焦 |
| 品牌调性 brand_tone | 主色、风格、语气 | 没有品牌感；缺失时见 brand-os.md |
| 参考体系 visual_references | 参考图、参考品牌、竞品链接 | 知道不对，但说不清哪不对 |
| 用户故事 | 用户故事表 | 只能摆产品，没有代入感 |
| 输出约束 image_constraints | 尺寸、比例、平台规则 | 返工，或上线后不合规 |

## 缺信息怎么办

- 不卡住当前模块的，注明“信息不足，已按现有事实保守输出”，继续做，并记进「上架前待办」。
- 会让核心结论失真的，只追问最少的字段。追问顺序：站点和语言 → 产品是什么 → 关键参数 → 兼容和限制 → 使用场景 → 关键词池。
- 凡是买家会问“具体是多少”的参数，都要明确到数字。

## 旧叫法对照

用户沿用旧说法时照常受理：Rufus 问答验证 = Alexa 问答覆盖验证；Listing 自查 = 合规检查；视频脚本 = 视频分镜表；主附图设计需求 = 图片需求单；A+设计需求 = A+ 需求单；“9 模块”“8 模块”“全套” = 全套生成。
