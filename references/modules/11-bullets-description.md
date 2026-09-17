# 11 五点和商品描述

五点前两条管转化，后三条管埋词和回答问题。商品描述只在没有 A+（brand_registered 为 no）或用户要求时才写。条数、长度、禁用字符和禁用声明，读 platform-rules.md 的「五点」「商品描述」两节。

## 用到的字段

language、audience_scenarios、not_suitable_for、usps、specs、compatibility、package_contents、must_answer、user_stories、keyword_allocation.bullets_aplus、banned_terms、compliance_notes、review_insights、variation_family

## 五点怎么写

- 默认写 5 条，每条只讲一件事，尽量动词开头，带具体事实或数字。
- 前两条写给人看：最强的卖点 + 关键适配信息 + 数字化参数，用用户故事里的那个“时刻”开场。
- 后三条兼顾埋词和答题：每条正面回答必答问题表里计划放在五点的一个问题；差评里的高频问题放进前三条。
- 至少有一处写清“适合谁、不适合谁，或什么情况下别用”。
- 要埋的搜索词只用分给五点的使用场景词和购买理由词。关键词分配只管搜索词埋在哪，不限制写事实：材质、参数、兼容范围、使用限制该写就写，否则 Alexa 购物助手答不上来。
- 格式跟官方建议走：小标题 + 冒号 + 描述；结尾不加标点；一条里多个短语用分号隔开。
- 不整句照搬标题和 Item Highlights；不写医疗词、极限词和无法证实的承诺；待核实的事实默认不写。
- 变体族：全族共享的卖点写族级表达，本子体独有的卖点至少出现 1 条。

## 商品描述怎么写

- 接住五点放不下的必答问题和使用说明：怎么装、怎么用、怎么清洁、注意事项、包装内含物。
- 用短段落，少和五点重复；不用 HTML，换行规则见平台规则。

## 产出

交付模板的 `### Bullet Points`（编号 1 到 5）和可选的 `### Product Description`。
