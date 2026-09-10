# 入口选择调研：优先证伪真实入口组合的可预测性

2026-09-08。状态：`RESEARCH_COMPLETE_DESIGN_ONLY`。本轮完成源码、已有结果、原论文和作者实现核查，只保存研究设计；没有训练、构图、ANN 性能实验、扫参、新 GT、依赖安装或方法源码修改，也没有打开原始 validation/held-out 查询或 GT。`20260908_v1` 和全部旧 gate/state 保留。

**唯一推荐：固定一个 Fast view 和小短名单，保留 Fast 主入口，研究能否低成本预测两个补充入口的真实联合收益。** 主检验固定三个入口，避免把少选入口的收益混成组合学习；一至三入口的 29 种含主入口集合用于诊断，实际模型只在 21 种三入口组合中选择。先做有界证伪，暂不推荐把它直接升级为论文方法。算法价值、可预测性、新颖性和完整 Recall–QPS 收益目前均未证实。

理由有三点。旧候选池已显示选择空间，尚无优先重建池的证据；“短名单内学单入口 utility”已经跨数据集失败；旧 oracle 的三入口来自独立命中并集代理，没有枚举真实共享搜索池下的组合。最后一项是清楚的未测缺口。**但修正监督对象并没有增加在线信息：真实联合效用可能比单入口更难预测。** 如果小门槛失败，应结束这个有限家族，不靠更大网络、更多 views 或在线 probe 挽救。

快速入口：[三方案及唯一推荐](recommendation.md)、[最小 gate、接口和命令草案](minimum_gate.md)、[相关工作比较表](related_work.md)。详细本地与论文证据在 `reviews/`；本文区分【实现事实】【已测事实】【论文/作者描述】【推断/设计】，不把不同证据等级混用。

## 1. 当前方法究竟做了什么

```text
独立 QGT 5K + 既有 exact GT100
    → normalized-query spherical k-means
    → 每簇从接近中心的 query 的 GT 顺序取未重复 base ID
    → H = 815 个 WebVid / 821 个 Yandex raw hubs

独立 prototype queries + 每 query 的 GT1 base vector
    → 用 GT1 与 normalized raw hub 的 cosine 分 basin
    → p_h = normalize(normalized raw-hub prior + Σ normalized queries)

在线 query
    → 单个 Micro-HNSW 搜 prototype
    → hub local ID 映射为真实 base ID
    → search_new(mode=2) 最多消费三个入口
    → 按原始 query–base IP 排序种子、共享 visited 和容量 L 的搜索池
    → 原 frozen NSG 上搜索，返回 top-K
```

【实现事实】`benches/run/build_fast_entry_variants.py:180–238` 的 QGT-Cover 不计算搜索效用，不是严格 set cover；按簇逐 query 扫 GT 选唯一 ID，不足时从 GT 展平顺序补齐。`:144–164,293,323–332` 显示 basin 使用 GT1 和 cosine，而非真正的图可达分区；单画像是归一化查询和加 raw-hub prior 后再归一化。原始 Yandex base/query 的搜索和 exact GT 仍是 raw IP，辅助路由归一化不能等同于修改搜索 metric。

【实现事实】旧 Fast 训练画像使用 30K；未来同协议 paired Fast 必须只用 `router_train[10000:30000)` 的 20K。已保存两份 compatible 20K 画像的 manifest 在 `hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p1/paired_fast20k/<dataset>/manifest.json`；本轮只读了元数据。旧 wrapper 带已结束的 deadline，不能成为新执行入口。5K QGT raw hubs 可依兼容身份复用，旧 30K prototype 不进入新训练链。

【实现事实】旧 `benches/test.cpp:353–357` 直接弹 HNSW 最大堆；oracle 和新 paired router 已反转成近到远。`ACSG/ACSG.cpp:1517–1537` 只消费前 `min(n,3)`，先截断再去重；`:1565` 又按真实 base-query 距离排序。所以，同三个唯一 ID、无真实距离 tie 时，不能把反转顺序直接当作性能变化原因。对大于三入口、重复和 tie 必须独立验收。源码旧注释中的“前 1/3 或 5 个”不代表当前常量，实际是 3。

【实现事实及推断】`benches/hnswlib/hnswalg.h:1308–1326` 先按 `max(ef_,k)` 搜索，再截断结果。固定 ef10 时，k3/k8 使用相同搜索池规模，这使单 view top8 成本值得检查；**不是零成本保证**。top32 会扩大到 ef32。新的设计必须核验 top3 前缀、真实 anchor、实际 NDC、count/plain 和 wall，不能直接沿用旧 QPS。

完整调用链证据与行号见[本地审计](reviews/local_evidence_and_gate_review.md)。

## 2. 证据支持到哪里

| 问题 | 已保存证据 | 能支持什么；不能支持什么 |
| --- | --- | --- |
| 池中有没有有用入口 | 旧 WebVid validation 1K、815 hubs、K10/L64：Fast3 Recall .6523、graph NDC 923.564；免费 single oracle .8024、913.376 | 支持该历史池存在选择空间；不证明新20K/双数据集/完整成本的收益，也不是全图最优上界 |
| 多入口能否简单取并集 | 同一结果的 union-greedy3 重放 Recall .7617、NDC 907.98；源码先跑所有 single，再按 hit mask 并集选三 | 没有测最佳联合三入口。共享 beam 下的组合结果不能用独立命中并集替代；“.7617 < .8024”也不证明所有多入口策略更差 |
| 换成真实 single 标签是否够 | search-aware centroid 在旧 WebVid1K 只带来约 .35–.82 pp 的 Recall@1/10 收益，NDC 增 .36–.71%；该路线已停 | 单个 oracle 类别压成均值画像没有回收大部分空间；不是全部监督学习不可能 |
| 轻量 single utility 排序 | top32、单入口 R10/NDC、diagonal listwise、top3部署；WebVid小收益，Yandex近 graph-NDC 时低预算 Recall −.158～−.402 pp 且成本仍高 | 旧目标已经含真实搜索和成本，换损失/模型名不构成新方案；因果上尚未证明失败由单入口监督错位造成 |
| 在线 trace 是否有信息 | paid L10 probe 提升 failure detection；alternate chooser及frontier/topology扩展仍失败 | 可以预测部分失败，不等于可以找对替代入口；不能写“trace 没信息”，也不再开启 probe 分支 |
| 不在线 probe 的历史效用查表 | cost-first reachability atlas 四点 utility CI 都跨零 | 相近历史查询、top8、保守均值/SE成本约束也已尝试；不是尚未探索的廉价补救 |
| 多路候选是否值得成本 | Multi-view E1b routing NDC 为 WebVid642.337、Yandex549.376；四点等 total-NDC Recall 全败 | 保留 `NO_GO_ROUTING_COST`。后两路 exact top8 recall 高达 .987～.998，不能把失败归咎于短名单完全失真 |
| GATE是否提供部署证据 | 本地 frozen raw-IP 适配：512 hubs、10K train、validation选checkpoint、dense cosine3；12个validation点质量/NDC均弱于Fast | 是这个适配的负结果；不同训练量、候选和路由后端，不能代表作者全部实现，也不是新20K公平结果 |

数字来自既有文件，本轮没有重算性能/统计。主要原件：[oracle](../../oracle_entry_diagnostics/webvid_validation_1k_current_hubs_v1/results.json)、[centroid](../../search_aware_entry_results/webvid_train5k_l64_r10_prior1_v1/analysis.md)、[ranker](../../sparse_utility_ranker_results/analysis.md)、[probe](../../probe_reroute_results/analysis.md)、[atlas](../../finite_beam_reachability_diagnostics/v2_distillation/decision.json)、[Multi-view](../../target_basin_formalization/20260907_v1/pilot/hnsw/report.md)、[GATE适配](../../gate_baseline_artifacts/webvid2_5m_frozen_r64_v2/analysis.md)。

因此，“单画像抹平结构”“单入口监督不适合联合部署”“anchor限制了搜索”“池构造缺乏可导航性”目前都只是候选解释。不能把任何一个直接写成已定位根因。

## 3. 原论文和作者实现改变了哪些判断

最接近的 [GATE，KDD2025，v1](https://arxiv.org/pdf/2506.15986v1) 已覆盖 hub 构造、拓扑表征、搜索监督和小导航图。核对其 [v0.0.1 在线源码](https://github.com/jacksondca/gate/blob/229f18dadb791ddede22597e44d5ceb028b104ba/tests/test_gate_search.cpp) 后，应纠正“GATE在线跑query MLP”的潜在误读：公开路径直接拿 query 搜离线生成的 hub embeddings。Fast 的明确区别是省掉 ACO/DPC、逐hub标签和 optimizer，不能笼统说相对 GATE 省掉在线 query 神经推理。

GATE 论文与公开 release 还存在正样本轴向、启用损失、hop 语义的差异。报告分别记录，不推定论文实验究竟采用哪个未公开配置。尤其首次发现 hop 不是 NDC，也不能自动当严格最短路径。五个具体文件、行号、release身份及本地适配限制见[作者实现审计](reviews/entry_papers_and_author_code.md)。

旧 NETG 本地稿 `ACSG/NETG_XM_KDD2026_ (5).pdf` §3.4/Alg.2、PDF pp.5–6 已明确逐hub真实搜索、成功后最小NDC标签、离线hub变换和Micro-HNSW top3；当前 `bench_generate_labels.cpp:187–207` 与 `train_router.py:400–407` 证实搜索监督及损失链。它是本地匿名稿，文件名不证明会议接受；稿中的“0ms/零开销”不等于完整路由免费，旧实验设置也不是本轮 raw-IP/20K 契约。本轮没有修改论文稿。

新补的直接候选前作是 [Adaptive Entry Selection，2024v1](https://arxiv.org/html/2402.04713v1) 和 [PSP/Spherical Navigation，2025v2](https://arxiv.org/pdf/2503.06882v2)：分别覆盖几何代表入口、方向与范数候选。PSP作者默认脚本关闭SN，可选路径预读query-cluster，不能据该脚本确认完整在线路由成本。GPU上的 [PilotANN FES](https://arxiv.org/html/2503.21206v1) 和 [PathWeaver ghost staging](https://arxiv.org/html/2507.17094v1) 进一步说明“小导航层先找入口”本身并不新。

另完整阅读了 [EDBT2026的Adaptive Query-Aware Hybrid Search](https://www.openproceedings.org/2026/conf/edbt/paper-253.pdf) 及作者8个相关源码文件。它复用历史query答案作入口，但公开range路径在搜索后用当前GT更新后续状态，过滤/特征预计算与计时也有不同边界。它既不能作为本项目无在线GT的现成方案，也不能被误写成“当前query直接用自身GT挑初始入口”。具体版本和证据见[2026补充](reviews/recent_2026_entry_addendum.md)。

[kRt](https://www.vldb.org/pvldb/vol18/p1649-gottesbueren.pdf)、[LIRA](https://zheng-kai.com/paper/2025_www_zeng.pdf) 的多代表/学习分片路由，以及 [SOAR](https://arxiv.org/html/2404.00774v1) 的互补冗余，可以启发表示和补充选择，但分片包含目标的覆盖关系不同于共享图搜索。SOAR 的残差公式依特定分布假设，不能直接当入口竞争理论。[RoarGraph](https://www.vldb.org/pvldb/vol17/p2735-chen.pdf) 改图；[MAG](https://arxiv.org/pdf/2504.14861v2) 还改变导航metric和预搜索，均不混入纯入口归因。

本轮未发现这些实读工作给出本项目“有限样本、固定原始IP图、同一小短名单、真实共享beam组合效用”的完整答案，**但这不是检索穷尽或新颖性证明**。期刊全文缺口、未确认作者代码的工作、硬件/metric差异见[相关工作表](related_work.md)。

## 4. 三个实质不同方向

| 方向 | 优化对象与机制 | 离线/在线成本 | 当前取舍 |
| --- | --- | --- | --- |
| A. 按搜索效用重选固定预算候选池 | 从限定额外base候选中，以训练query的最佳单入口搜索效用覆盖选H个hub；重新构建query画像 | 标签近 Q×候选数×预算点；重选池、画像和索引另计。部署仍可单Micro-HNSW | 真正改变候选集合，但缺池尚未证实；覆盖代理仍不保证可路由/联合有效，暂不优先 |
| B. 固定池和短名单的单入口偏好学习 | 在同一C8中预测单入口效用，再独立排三个 | Q×8×预算点标签、单router加8项打分 | 成本可控，但已被旧ranker/centroid/atlas覆盖大半；无新信息依据，保留为对照 |
| **C. 固定主入口的真实组合选择** | C8中保留a，直接预测每个 `{a,b,c}` 的真实R10/NDC；固定21个动作中选一组 | Q×21×预算点主标签；单router、显式8个prototype加8个raw分数、小型pair表查询及21组打分 | **唯一优先证伪推荐**。变的是实际监督/决策单元；尚无收益与泛化证据 |

C 的主假设是：在相同query/anchor/候选/预算下，补入口的价值依赖另一个补入口，且其中一部分依赖可以由在线廉价特征预测。不是“入口越多越好”，不是“独立命中并集最大”，也不声称单调或子模。具体目标、固定小模型、对照、新颖性限制及风险见[推荐说明](recommendation.md)。

## 5. 最小证伪怎样作出决定

先绑定两数据集CPU/raw-IP、原NSG、20K paired Fast及固定样本。128个历史pilot query做限定扩展池/全池/短名单的单入口分解；512个历史pilot query枚举36个不同搜索动作（8个single加29个含anchor集合、合并重复single）。固定64个query额外查无anchor的92个一至三入口集合，单列anchor限制。主模型固定m=3；只有21组真实联合oracle有剩余空间，才考虑2048个fit查询上的一次小模型可预测性检查。

比较必须包含：Fast1/2/3、同C8的single utility排序及命中并集代理的真实重放、同一组输入的可加模型、真实组合模型。组合模型要在固定m=3时胜过可加对照；否则不能把收益归因于交互。模型在线只看query及训练阶段模型，GT和Fast实际搜索成本只作离线标签。

通过小样本只允许检查历史10K pilot上的完整路由加搜索成本，仍不允许宣称最终收益。成本筛查固定16个点/数据集、五轮纯wall和独立count，不因无匹配而补扫。最小版本总上限300万次完整搜索调用、4小时、8GiB新产物、一个重数据集进程；资源耗尽记INCONCLUSIVE。精确计数、阈值、比较族、多重校正、匹配失败处理和命令均在[gate草案](minimum_gate.md)。这些阈值是拟议的筛查标准，不是已通过的实验gate。

最终仍须另立正式协议：双数据集至少两个相邻工作点，同Recall QPS≥+10%或同QPS Recall@10≥+1pp并有校正区间支持；三独立构建、tail、强基线与方法冻结后的held-out 10K×3。新pilot没有降低这个标准，也没有继承旧夜间授权。

## 6. 完整成本与最可能的失败

`T_offline = T_exact_train_GT + T_QGT + T_prototype + T_router_index + T_action_labels + T_pair_features + T_fit`。报告复用GT与从零两种口径；已存在但耗时不明的项写null及原因，不能写0。有限oracle遍历、失败分支和诊断成本也入研究成本台账。公共NSG构建另列，做整系统生命周期比较时加回。

`T_online = T_normalize + T_shortlist + T_raw_scores + T_action_features/selection + T_reset/dedup + T_graph + T_output`。GT评分、hash、trace、JSON不进timer，输出写入和必要状态重置在内。routing/graph/total NDC、模型MAC、模型/索引字节、整批wall和独立1-thread尾延迟分开报告；NDC不是所有CPU成本的代理。

最可能失败的是**在线特征无法预测路径竞争**，其次是C8漏入口、anchor排除好入口、20K数据对组合结构过稀、以及增量路由吞掉微小收益。若只有oracle好或只在WebVid好，应明确关闭/收窄，不承诺整体提高。即使成功，方法仍需证明相对可加模型的机制贡献，并继续检索相关工作；不能仅凭“联合”二字确认论文新颖性。

本轮结论是一个具体、可被否决的研究选择，尚没有新方法GO。下一步由新的执行任务决定，本轮到报告与交接结束。
