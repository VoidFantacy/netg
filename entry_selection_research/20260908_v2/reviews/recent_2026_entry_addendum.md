# 2026 补充：Adaptive Query-Aware Hybrid Search 的入口机制与证据边界

核查日期：2026-09-08。本笔记只补充一篇入口相关近作；读取原论文与作者源码，没有编译、训练、构图、ANN 评测、安装依赖或读取本地原始 query/GT/base/图。源码结论均指下列固定 commit，不推定为论文每条曲线实际使用的配置。

**判断：这篇工作覆盖了“复用历史 query 的答案作为图搜索入口”的直接相关思路，但不能支持本项目引入在线 recall 反馈，也不能证明冻结图、unfiltered raw-IP、固定三个入口下的收益。公开 range 路径确实读取当前 query 的 GT，更新回归和历史索引；默认示例还有预计算成本与状态隔离问题。它应进入相关工作和成本反例，暂不升级为优先实现方案。**

## 1. 文献身份与实际覆盖

- Adeel Aslam、Rizwan Khan、Giovanni Simonini、George Konstantinidis，*Adaptive Query-Aware Hybrid Search in Vector Databases*，EDBT 2026 Short，proceedings pp.530–536，DOI [10.48786/edbt.2026.42](https://doi.org/10.48786/edbt.2026.42)。完整阅读 7 页，包括方法 §2.3–3.3、实验 §4.1–4.2、Algorithm 1、表 1 和全部图注。[官方 PDF](https://www.openproceedings.org/2026/conf/edbt/paper-253.pdf)
- 论文脚注指向 [AdeelAslamSoton/QueryAwareIndexing](https://github.com/AdeelAslamSoton/QueryAwareIndexing)。本次在线固定 master commit `e6dfc9a34698e036f11b9baf2a73b6ba0f4c9909`（commit 日期 2025-12-26），读取 README、point/range 示例、两个搜索 header、BST、回归和 query-property 定义，共 8 个小型文件；未下载作者数据。
- 原文保存在 [paper-253.pdf](../sources/recent_2026_entry/paper-253.pdf)，逐页抽取在 [paper-253.txt](../sources/recent_2026_entry/paper-253.txt)。原文来源与 SHA-256 见 [download_manifest.json](../sources/recent_2026_entry/download_manifest.json)；代码 URL、commit、字节数与 SHA-256 见 [author_code_manifest.json](../sources/recent_2026_entry/author_code_manifest.json)。

## 2. 原文机制、实验和适用范围

以下为原文事实和作者报告，不是本地复现。

| 项目 | 原文内容与页节 |
|---|---|
| 入口生成 | 按属性或范围 bin 建历史 query BST；综合 query 间距离与预测 recall 遍历，收集历史答案作为 HNSW layer 0 入口，再作过滤 two-hop 搜索。§3.1–3.2，PDF pp.2–3。 |
| recall 信息 | 新 query 用随机 base 样本的最近距离、selectivity 预测 recall；每次搜索后用实际 recall 更新回归和 BST。Algorithm 1 的第 6–9 行明确包含实际 recall。§2.3、§3.1.3、§3.3，pp.2–3。 |
| 训练与推理特征 | §3.3 区分训练时返回 top-K 的平均距离与推理时全局样本最近距离；作者将两者视为相关代理，并未证明等价。p.3。 |
| 实验范围 | 表 1 含六个数据集、七种数据配置；实验为 point/range/AND/OR 过滤查询，HNSW M=64、efConstruction=400、efSearch=20–1500，声明使用 40 线程。§4，pp.4–6。 |
| 路由成本反例 | Paper 数据上，原始 HNSW 高层导航比原始 BST 遍历快 1.8 倍。冷启动 pre-filter 的摊销另按查询批次观察。§4.2.2–4.2.3，p.6。 |

[原文方法与实验](https://www.openproceedings.org/2026/conf/edbt/paper-253.pdf)

**研究推断：** 它最直接的启发是保存“相似历史 query → 已找到的 base IDs”。预测的是 query 的过滤检索 recall，不是针对候选入口的固定预算增益 `u(q,e;L)`。历史答案缓存、recall 反馈、属性分组、two-hop 搜索同时参与，不能把完整系统表现拆解为单独入口选择收益。过滤条件提供的历史分组在当前 unfiltered 场景中也不存在。

## 3. 作者源码：GT 确实进入在线状态更新

### 3.1 Range 的有效路径

`example_query_aware_range.cpp:314–327` 加载全体 `gts_ids` 和预计算 `avg_dis_selectivity`，传入搜索对象。`:437–452` 用该 query 的 distance/selectivity 预测，然后调用 `search` 或冷启动函数。[初始化](https://github.com/AdeelAslamSoton/QueryAwareIndexing/blob/e6dfc9a34698e036f11b9baf2a73b6ba0f4c9909/hnswlib/examples/cpp/example_query_aware_range.cpp#L314)、[调用](https://github.com/AdeelAslamSoton/QueryAwareIndexing/blob/e6dfc9a34698e036f11b9baf2a73b6ba0f4c9909/hnswlib/examples/cpp/example_query_aware_range.cpp#L437)

`query_aware_range_filter_hnswlib.h:167–202` 在拿到搜索结果后按 `id=query_num+batch_start` 读取 `gts_ids[id]`，计算命中比例，然后执行 `linear_reg->update(avg_dist_sel, match_count)`，并把该真实 recall 加入入树分数。冷启动 `:517–548` 也执行同类反馈。[普通路径](https://github.com/AdeelAslamSoton/QueryAwareIndexing/blob/e6dfc9a34698e036f11b9baf2a73b6ba0f4c9909/hnswlib/query_aware_hnsw/query_aware_range_filter_hnswlib.h#L167)、[冷启动](https://github.com/AdeelAslamSoton/QueryAwareIndexing/blob/e6dfc9a34698e036f11b9baf2a73b6ba0f4c9909/hnswlib/query_aware_hnsw/query_aware_range_filter_hnswlib.h#L517)

**边界：** 这是搜索结果产生后的 GT 反馈，不能说成每个新 query 直接用自身 GT 选初始入口；但反馈确实改变后续 query 的模型和历史索引。当前 held-out GT 只能用于离线评测的合同不允许这种更新。若只用 train 阶段构建缓存并冻结，或者改用不依赖 GT 的反馈，便是需要单独验证的新变体；不能继承原文曲线。

### 3.2 Point 默认配置与论文公式有差异

- `example_query_aware_point.cpp:369–370` 默认只有 `ef=560`；`:496–500` 注释掉预测，把 `score=0`，距离归一化常量固定为 `2.8`。不能把这个默认配置视为完整 recall 预测方法。[示例](https://github.com/AdeelAslamSoton/QueryAwareIndexing/blob/e6dfc9a34698e036f11b9baf2a73b6ba0f4c9909/hnswlib/examples/cpp/example_query_aware_point.cpp#L369)
- `query_aware_hnswlib.h:191–255` 仍计算 GT recall 并更新回归，但普通命中路径的 recall 入树项已注释；入树 embedding 取某个返回 base 节点的向量，并固定复制 200 个 float，原 query 入树调用被注释。这是可见研究配置残留，迁移其他维度前须处理。[搜索与插入](https://github.com/AdeelAslamSoton/QueryAwareIndexing/blob/e6dfc9a34698e036f11b9baf2a73b6ba0f4c9909/hnswlib/query_aware_hnsw/query_aware_hnswlib.h#L191)

因此，“源码存在 GT 更新”与“point 默认预测已启用”是两个不同命题；后者在该 commit 不成立。上述差异不能推出作者所有实验实际采用同一个残留配置。

## 4. 完整在线成本与可复现性问题

| 成本或状态 | 已核实事实 | 对公平比较的影响 |
|---|---|---|
| 距离/selectivity 特征 | 两个示例在计时前读入 `DISTANCE_SELECTIVITY`；公开 `compute_distance_for_queries` 每 query 随机取 10 个 base 节点计算最小距离，并写文件。 | 这是 query 相关预计算，不是免费常量；不能把只含线性回归求值的成本当完整路由成本。也不能认定该 distance 特征直接来自 GT。 |
| predicate mask | range 在 timer 前生成或加载 `(batch query 数)×(base 数)` 字节的完整过滤表，逐 query 扫描 metadata。 | 在线元数据过滤准备及内存必须单列；如沿用预缓存，需明示缓存前提。 |
| 计时包含项 | range `:421–457`、point `:486–508` 包住搜索调用；header 在调用内比较 GT、更新模型/BST、创建目录并逐 query 写 CSV。 | 当前示例计时既漏掉部分预计算，又混入评测/输出成本；不等于本项目要求的纯 wall 路由加图搜索计时。 |
| 历史树大小 | `bst.h` 保存 embedding 与历史结果 IDs，普通插入无平衡旋转、淘汰或容量限制；沿遍历路径把结果 IDs 全部并入集合。 | 原文的平均 `log Q` 叙述不能充当严格延迟/内存上界；每个访问节点还需向量距离和 ID 合并，入口数量也不固定为 3。 |
| Range 的 ef 状态隔离 | range `:362` 仅一次初始化 BST；其后 batch 外层、ef 内层循环复用同一对象，模型虽按 ef 分开，历史 BST 没有相应重置。 | 后一个 ef 可见同批 query 在前一个 ef 的历史结果。该示例不提供每个 ef 相互隔离的冷启动曲线；不能据此推断论文曲线也使用此流程。 |

代码依据：[随机距离特征生成](https://github.com/AdeelAslamSoton/QueryAwareIndexing/blob/e6dfc9a34698e036f11b9baf2a73b6ba0f4c9909/hnswlib/query_aware_hnsw/query_aware_hnswlib.h#L1642)、[range 预处理与循环](https://github.com/AdeelAslamSoton/QueryAwareIndexing/blob/e6dfc9a34698e036f11b9baf2a73b6ba0f4c9909/hnswlib/examples/cpp/example_query_aware_range.cpp#L362)、[range 内部输出](https://github.com/AdeelAslamSoton/QueryAwareIndexing/blob/e6dfc9a34698e036f11b9baf2a73b6ba0f4c9909/hnswlib/query_aware_hnsw/query_aware_range_filter_hnswlib.h#L208)、[BST 保存与插入](https://github.com/AdeelAslamSoton/QueryAwareIndexing/blob/e6dfc9a34698e036f11b9baf2a73b6ba0f4c9909/hnswlib/query_aware_hnsw/bst.h#L11)、[BST 遍历](https://github.com/AdeelAslamSoton/QueryAwareIndexing/blob/e6dfc9a34698e036f11b9baf2a73b6ba0f4c9909/hnswlib/query_aware_hnsw/bst.h#L157)。

另外两个静态差异进一步限制默认示例的证据强度：range 在 `:446/:451` 传入最大距离 `0`；BST 将其下限设为 `1e-6` 后计算并截断相似度，因此距离大于该阈值时距离项全为零。两个示例的查询 `ParallelFor` 都显式使用 1 线程，不能将源码默认查询配置直接标为论文声明的 40 线程。没有运行程序，所以本笔记不估计这些差异的实际性能影响。

## 5. 对当前入口路线的判定

1. **作为前作保留。** 新方案若声称“历史 query 答案复用”“query-aware 入口索引”或“recall 辅助入口”，应与该工作明确区分。仅换成一个小型索引或回归器不构成独立机制证据。
2. **不迁移在线 GT 反馈。** 如果未来考察 train-only 的历史答案缓存，必须明确缓存条目来源、去重与容量，冻结后再用于独立查询；这属于新适配，当前没有实验授权或收益证据。
3. **不把过滤场景优势外推到当前问题。** 固定原 NSG、raw IP、三个入口和原搜索语义时，必须舍去或改写属性 BST、two-hop、动态历史状态等成分，完整方法的收益不能跟随迁移。
4. **不改变当前优先级。** 这篇近作补强了“入口检索自身可能比原图高层导航更贵”的成本警示，但没有提供当前候选可学性、总成本改进或两数据集共享有效性的证据。继续维持研究待定，不把文献新颖性误当实现 GO。

这些结论只依赖已读公开文本和源码；没有对作者代码作本地修复，也没有联系作者或声称复现其性能。
