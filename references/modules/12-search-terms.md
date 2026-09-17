# 12 Search Terms

补前台没覆盖到的搜索词。字节上限、超限后果和写法清单，读 platform-rules.md 的「Search Terms」一节。

## 用到的字段

language、marketplace、keyword_allocation.search_terms、semantic_buckets、brand、banned_terms，以及已写好或用户提供的标题、Item Highlights、五点

## 做法

- 先按单词列出标题、Item Highlights、五点里已经用过的词，这些词不再放进来。
- 优先装分给 Search Terms 的词：长尾词、同义词、拼写变体。
- 还有空间时，按 semantic_buckets 补同义词和拼写变体；补的词必须和产品事实相符，不能带进资料里没有依据的功能。
- 拼写变体指英美拼写、连写与分写（如 32oz）这类写法差异，不算重复词根。
- 分配表里标“不用”的词不放；品牌词、竞品词不放；不收常见错拼。
- 不用为了填满而硬凑，贴合度低的词宁可不放。
- 超了就整词删除，不拆断词。
- 变体族：兄弟子体的 Search Terms 应各不相同，各自埋本子体的规格词。

## 产出

交付模板的 `### Search Terms`，一行，空格分隔。字节数由检查脚本数。
