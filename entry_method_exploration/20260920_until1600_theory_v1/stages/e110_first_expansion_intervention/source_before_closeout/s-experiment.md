# ACSG 历史实验概览与复盘索引

2026-09-20 **E110首展开机制干预运行中**：全4096既有query，固定相同GT10三入口只改变第一次展开节点，原1/3入口双控制、K1/K100全部五/四L；不是失败子集调参，无新训练/GT/图/QPS。[记录105](experiment_history/105_first_expansion_intervention.md)。

2026-09-20 **E109完美代理门完成并停止训练投入**：Yandex有正信号、Web无转化，两个代理均未过跨集门。Web区域覆盖大增但Recall不增，明确代理与有限beam效用缺口；66304 NSG，0训练/GT/图/QPS，默认保持。[记录104](experiment_history/104_perfect_proxy_information_gate.md)。

2026-09-20 **E108真实单位hub小图对照完成**：54点/162轮完整wall，Web小幅质量信号、Y K100损伤，无跨集稳定替换。GT10小图精确入口成员召回更高、路由NDC更少，说明画像还改变小图可检索性；18点精确/ANN质量分解通过。1106688 NSG/4图，0新GT/训练/K10，默认保持。[记录103](experiment_history/103_unit_hub_online.md)。

2026-09-20 **E107初始化因素对照完成**：原单位hub单入口已获得对固定NSG的大部分均值收益，Web画像并未稳定优于单位hub；GT10增加两个入口的18点均值17负/1正，多数区间跨0。强连通反例及144点/1181184次真实NSG核验完成，0新GT/图/训练/QPS，默认保持。接续先补简单对照的真实小图与wall。[记录102](experiment_history/102_initialization_factorial.md)。

2026-09-20 **E106条件机制检验完成，STOP_GROUPMEAN_CANDIDATE**。精确分解与匹配支持置换通过；六项机制Recall区间均跨0。GroupMean相对匹配GT10 exact的主R1/R100为Web−0.0488/−0.0222pp、Y+0.2441/+0.0063pp，四校正区间均跨0，两集门失败。真实K1/K100/L128，各4096已曝光query；361856 NSG，0新GT/图/梯度训练/正式QPS。停止该候选，原默认及生产保持；当前机制解释仍有缺口。[复盘101](experiment_history/101_gt10_conditional_mechanism.md)。

2026-09-20新增[研究记录100](experiment_history/100_gt10_theory_review.md)：复核GT10构造/E27机制及E104/E105失败，给出闭式代理最优解、ESS反例、目标覆盖与有限预算真实效用的条件界；明确尚未证明代理误差小或跨query可迁移。只读源码/汇总和符号分析，0新训练/检索/GT/构图/QPS，不计E106。当前研究转为理论解释与可识别性优先，最新候选性能仍E105，五集完整比较仍E103。

2026-09-20最新完成 **E105冻结WFree独立复验**：两集各4096新源行query、新GT100、真实K1/K100各16预算，共128点384轮单线程wall。两集质量与吞吐门均失败，7个共同可达门槛平均QPS全负，状态STOP_WFREE_REPLICATION；2,621,824次NSG、0重训/新图/K10，默认及生产E99保持。[复盘99](experiment_history/99_wfree_frozen_replication.md)。E104查询MLP已在此前停止，WFree原开发正值的独立接续现也完成；研究记录97保留设计阶段历史身份。

2026-09-20新增[研究记录97](experiment_history/97_query_representation_research.md)：查询侧非线性方案的源码/文献审查、表示推导、16个历史fit集合几何witness与最小证伪协议；0新训练/ANN/GT/构图/QPS，尚无新方法效果。此项不是E104检索实验，最新正式性能仍E103。

方法研究专题：[GT10：OOD 入口选择方法与实验总结](研究方向.md) · [PDF（7页）](GT10研究总结.pdf)（2026-09-17更新）。88行原文按“当前方法→重测图→改进实验→NSG优化→阶段总结”组织；效果部分仅保留四张完整重测图，实验开头说明尚无稳定替代 GT10 的新方法，结尾区分公共提速与入口收益。仅整理既有结果，无新增实验。

E103五集优化重测已完成：800配置、2400轮单线程计时、3280万次搜索，约13小时；Recall@1/100、排除LAION。可达的25个90/95/99%门槛组合中，GT10-hard/soft家族平均QPS最快22个；不是单一模型胜率或显著性结论。WebVid/Yandex收益较清楚，Deep/SIFT较小到中等，GIST相对NSG基本持平或落后。 搜索完成后汇总K字段冲突已通过独立后处理修复，无重跑；评分、图表和总览目视检查完成，旧源码/结果保留。[报告与新图](entry_method_exploration/20260916_optimized_five_dataset_r1_r100_v1/report.md) · [复盘96](experiment_history/96_optimized_five_dataset_retest.md)。

E102于2026-09-16完成统一优化公平比较：NSG、GT10-hard/soft、GATE均使用相同span+batch4，WebVid四预算各新旧内核及同轮HNSW共36配置108plain。NSG自身四点平均QPS变化+18.58%至+27.28%；K100/L1250从252.11变为320.90QPS，Recall@100保持90.4456%。同内核soft为324.95QPS/90.6868%，GATE为319.69QPS/90.6317%；HNSW为271.54QPS/90.3718%。 其它四集64配置的ID/距离bits/入口/逐query NDC全部一致；2296000search、0新训练/构图/GT/合成搜索，原E101封存保持。[报告与图](entry_method_exploration/20260916_shared_span_batch4_v1/report.md) · [复盘95](experiment_history/95_shared_span_batch4_comparison.md)。

E101于2026-09-16完成内置Faiss1.9.0同图比较：WebVid四点、十版本、120轮plain/2000000search；GT10的span+batch4组合相对当前E99四点QPS变化+13.10%至+26.56%，各GT10控制返回和NDC相同。高预算K100/L1250组合341.45QPS、Recall@100 90.6868%，当前GT10 269.80QPS；原生Faiss 230.52QPS/90.4819%。另做80000次真实batch4计数核验及496000次四集一致性回归，其它四集64配置的输出ID/距离bits/入口/逐query NDC全部与E99一致。 [报告与图](entry_method_exploration/20260916_faiss_nsg_comparison_v1/report.md) · [复盘94](experiment_history/94_faiss_nsg_comparison.md)。 合计2576000真实搜索，另有两次12960合成搜索；图和模型保持，原生库结果不覆盖历史NSG标签。

E100（2026-09-16完成）：E99后剩余成本及NSG库核查，80000次单线程诊断、0新正式QPS。NSG邻接检查约HNSW的3.095倍，71.82%为空槽；新采样图循环/visited/预取区域26.98%，路由0.50%，输出/NDC一致。确认已用Faiss组件、线上为项目多入口改造，原生库独立对照未测；生产和默认保持。[详细复盘93](experiment_history/93_residual_search_cost_research.md) · [报告与图](entry_method_exploration/20260916_residual_cost_research_v1/report.md)。

E99于2026-09-16完成共享NSG实现优化：WebVid四个预算、四种NSG入口方法的新旧对照，QPS变化+10.51%至+13.53%；五集100个组合的返回ID/距离bits/入口和逐query NDC均与E97一致。 先Git备份`2739b09a`，再生产源码优化；E98短池控制的等距反例已修复，E98旧证据保留。Web四点公平比较NSG/hard/soft/GATE旧新内核和完整HNSW，其他四集只做完整query回归，原模型默认与历史产物不变。[报告](entry_method_exploration/20260916_nsg_search_optimization_v1/report.md) · [Recall–QPS图](entry_method_exploration/20260916_nsg_search_optimization_v1/figures/webvid_recall_qps.png) · [复盘92](experiment_history/92_nsg_search_optimization.md)。

E98（2026-09-16完成）：WebVid GT10-soft/完整HNSW成本诊断，550000次search、36轮plain。路由0.47%；预取+7.81%、组合+13.15%，单独候选池+0.95%在波动范围内；逐query NDC/输出一致，主代码与默认未改。[详细复盘](experiment_history/91_webvid_search_cost_diagnosis.md) · [报告](entry_method_exploration/20260916_search_cost_diagnosis_v1/report.md)。

E97（2026-09-15启动，2026-09-16完成）：GATE disjoint-label修复；WebVid/Yandex/Deep/BIGANN-SIFT/GIST五方法Recall@1/100，共800点、2400次单线程wall，正式阶段15.826小时。[详细复盘](experiment_history/90_gate_disjoint_five_datasets_r1_r100.md)、[逐集分析](entry_method_exploration/20260915_gate_l2_r1_r100_v1/analysis.md)、[Yandex前缀修正与等待中断](experiment_history/90a_yandex_test_prefix_fix.md)。旧默认不变。

2026-09-15 E96后续GATE审查完成（0新训练/ANN/QPS）：核心合理适配保留，确认约0.25%–0.40%实际triplet存在正负语义冲突，后继先排除交集。新三集建议GT10-hard主线/soft-t1辅助；旧数据接入须修split/L2/K，未来只测Recall@1/100。见[89 审查记录](experiment_history/89_gate_reproduction_audit.md)，不是新的性能实验，E96封存不改。

2026-09-15最新完成E96：三数据集、四方法、16预算至1500、192点576轮单线程；Web/Y GT10在全部预算支配GATE的Recall/平均QPS，LAION高预算存在质量速度取舍，默认未替换。见[复盘88](experiment_history/88_gate_three_dataset_comparison.md)及[完整报告](entry_method_exploration/20260914_gate_new_ood_v1/report.md)。E95固定H增强分支停止结论保留，E94是更早的旧分支最终矩阵。

> 更新截至2026-09-20。本文负责历史概览与复盘索引；原协议、源码、配置和实测产物决定实现与结论，原始证据保留原处。当前结果见[summary](summary.md)，实现合同见[spec](spec.md)，后续任务见[s-target](s-target.md)。

## 1. 已执行的实验与诊断

状态针对具体版本和证据范围。实现验收、诊断信号、依赖准备、方法性能通过分别记录；同L Recall或oracle改善不等于端到端成功。

| ID / 实验家族 | 做过的主要内容 | 当前保留的历史判断 | 详细复盘 |
|---|---|---|---|
| E109 完美代理信息 | 预锁fit2048、目标均值/区域覆盖、两强控制与投入门 | 执行中；不可部署代理、非Recall上界、0新训练 | [104 完美代理门](experiment_history/104_perfect_proxy_information_gate.md) |
| E108 单位hub实际小图 | 原GT10/同seed重建/单位hub、54点162轮完整wall及精确质量分解 | 完成；Web质量微正、Y K100损伤，小图可检索性差异明确，默认保持 | [103 普通小图对照](experiment_history/103_unit_hub_online.md) |
| E107 表示×入口数 | 三表示×1/3入口、NSG/默认ANN、真实K1/K100完整144点 | 完成；单位hub为必须补强的简单对照，GT10多入口均值多为负，原默认保持、无新QPS | [102 初始化因素](experiment_history/102_initialization_factorial.md) |
| E106 条件机制与条件聚合 | GT1组内权重置换、共享/组内矩分解、一个闭式候选，完整K1/K100机制比较 | STOP_GROUPMEAN_CANDIDATE；两集门失败，机制区间跨0，原默认保持 | [101 条件机制](experiment_history/101_gt10_conditional_mechanism.md) |
| E105 冻结WFree独立复验 | 原E104模型/图，双集各4096新源行，独立GT100与完整K1/K100单线程曲线 | STOP_WFREE_REPLICATION；两集质量/wall门均失败，0重训/新图，默认保持 | [99 冻结复验](experiment_history/99_wfree_frozen_replication.md) |
| E104 查询侧表示pilot | 两集真实56集合监督，QLinear/QMLP/WFree六模型，精确/ANN路由与配对开发门 | STOP_REPRESENTATION；QMLP未超过GT10，WFree仅局部正值，0新QPS/默认变更 | [98 查询表示验证](experiment_history/98_query_representation_pilot.md) |
| E103 优化后五集完整曲线 | 原五集五方法各K16预算，统一span+batch4与同轮HNSW | 800配置2400plain；状态与结果见复盘 | [96 优化完整重测](experiment_history/96_optimized_five_dataset_retest.md) |
| E102 统一span+batch4方法比较 | NSG/hard/soft/GATE各新旧内核，Web36点108plain及四集64一致性 | 2296000search；共同内核收益与入口差异分列，生产保持 | [95 共享优化公平比较](experiment_history/95_shared_span_batch4_comparison.md) |
| E101 原生Faiss同图与实现控制 | Web四点十版本120plain；另四集共享入口兼容性 | 2576000search；组合本地提速，生产默认保持，跨集边界见报告 | [94 库与内核比较](experiment_history/94_faiss_nsg_comparison.md) |
| E100 优化后剩余成本与库核查 | Web10K、soft/HNSW、分项/采样/结构插桩及全图padding审计 | 80000search、输出/NDC一致；空槽71.82%，无新QPS或生产改动；原生Faiss对照待验证 | [93 剩余成本](experiment_history/93_residual_search_cost_research.md) |
| E96 GATE三数据集完整比较 | 三套完整base/10K query、四方法、16预算、192点576次单线程wall | Web/Y全部GATE点被GT10支配；LAION高预算质量/速度取舍，默认未替换；失败率与完整成本边界保留 | [88 完整对照](experiment_history/88_gate_three_dataset_comparison.md) |
| E95 查询二阶统计构图 | full/diag闭式C构图后恢复原P；两集7952、L64/128及两半实测 | 四组合门全失败、八全量Recall负且失败增；194304 NSG/6build/0QPS，停止当前固定H增强分支 | [87 构图与停止](experiment_history/87_query_moment_graph_and_branch_stop.md) |
| E94 冻结最终完整矩阵 | Web6/Y4方法、五L五轮、401完整失败query | 50点250wall；Web组合相对compact质量修复，仍不及P，Y高L损伤；无稳定整体收益 | [83 最终对照](experiment_history/83_frozen_final_comparison.md) |
| E93 最终候选选型 | 77项目录、41项独立同源质量评分 | E93仅选型、0ANN；Web选E92反证/P保留，Y选compact；最终实测见E94 | [82 最终选型](experiment_history/82_final_candidate_selection.md) |
| E92 固定补边/父恢复组合 | Web四格实测、Y零更新别名 | Web对compact+97/失败−10，对P+38但后半−7/失败+1，完整门FAIL；80960NSG/0QPS | [81 组合修复](experiment_history/81_composed_repair.md) |
| E91 最终工具准备 | 2000参数化控制/分析v3、既有E74完整回归、76项目录 | 0ANN/QPS；112640旧评分+110000内存2000夹具、32负例通过；实际最终选择/运行仍待完成 | [80 最终工具](experiment_history/80_final_tooling_preparation.md) |
| E90 双来源父画像恢复 | E89固定13/8动作，另3976训练支持筛选5/0，实际双源合并与后半接受 | 双集门FAIL；Web接受对compact+21/失败−1，仍对P−22/+2，Y零更新；163858NSG/0QPS | [79 双来源恢复](experiment_history/79_cross_source_parent_restore.md) |
| E89 局部父画像恢复 | 32hub/集实际两子行恢复、13/8效用筛选、并图与随机控制 | `COMPLETE_LOCAL_PARENT_RESTORE`；Web aux对compact+18/失败−6，Y−39/+5，双集门FAIL，182698NSG/0QPS | [78 父画像恢复](experiment_history/78_local_parent_restore.md) |
| E88 提议排名与实际响应诊断 | 冻结fit七slot/目标排名及实际边响应 | `COMPLETE_CACHED_PROPOSAL_RANK_DIAGNOSIS`；167/19支持事件中19/0目标可进前三，0新ANN/QPS | [77 排名诊断](experiment_history/77_proposal_rank_diagnosis.md) |
| E87 真实策略收益提议目标 | P优于compact完整策略提议、53/9实际边、16/0合并 | `COMPLETE_UTILITY_PROPOSALS`；Web对compact+16/失败−3仍不及P，Y零更新，194718 NSG/0QPS | [76 效用提议](experiment_history/76_utility_proposals.md) |
| E86 真实单边效用筛边 | 固定64/47边全fit真实响应、29/3边合并与双集aux | `COMPLETE_EDGE_UTILITY`；Web对compact+18/失败−3、Y−4/0，双集门FAIL，170336 NSG/0QPS | [75 单边效用](experiment_history/75_edge_utility.md) |
| E85 query向量路由前选择 | 前3976拟合固定岭、后3976接受、缓存P/compact完整选择 | `COMPLETE_QUERY_GATE_CACHE_FEASIBILITY`；双集门FAIL，原收益保留约58%，0新ANN/QPS，未原生实现 | [74 查询选择](experiment_history/74_query_gate_feasibility.md) |
| E84 fit查询排名缺口补边 | 首返回slot遗漏目标投票、每源最多1边，双集7952 | `COMPLETE_QUERY_SHORTCUTS`；Web对compact+42/失败−4但仍不及P，Y−4/0，双集门FAIL | [73 查询补边](experiment_history/73_query_shortcuts.md) |
| E83 compact同hub补边 | 原全部边保留，追加同hub边/同节点度近邻控制，双集7952 | `COMPLETE_SIBLING_LINKS`；双集门FAIL，Web对compact−1/失败−1、Y0/0，129536 NSG/4边安装 | [72 同hub补边](experiment_history/72_sibling_links.md) |
| E82 新目标完整排名效用 | 三bank完整排名/同三入口缓存补3593缺口、双集7952 | `COMPLETE_TARGET_EXACT_DIAGNOSIS`；六原门失败，7762 NSG/0HNSW/0build/0QPS | [71 完整排名](experiment_history/71_target_exact_utility.md) |
| E81 query/条件GT联合分组 | 从原Q分配出发、等权双视角20轮、双集aux7952 | `COMPLETE_JOINT_VIEW_PARTITION`；双集原门失败，停止本等权版本；129536 NSG/2build/0QPS | [70 联合分组](experiment_history/70_joint_view_partition.md) |
| E80 同hub条件GT目标分组 | 原rank权重/A/P恢复、条件目标逐hub流式分组、双集aux7952 | `COMPLETE_HUB_CONDITIONED_TARGETS`；双集原门失败，本条件均值版本停止；129536 NSG/2build/0QPS | [69 条件目标](experiment_history/69_hub_conditioned_targets.md) |
| E79 GT10目标空间分组 | 原A/P/Q全复现、目标/固定置换两分组、双集aux7952 | `COMPLETE_TARGET_SPACE_MODES`；两集预锁门失败，停止本目标分组版本；129536 NSG/0QPS | [68 目标空间分组](experiment_history/68_target_space_modes.md) |
| E78 固定图子质量范数 | rho^(1/d)与同平均log缩放对照；P/图/方向保持 | `COMPLETE_CHILD_MASS_NORM`；Web对compact净0，Y−44/失败+3，双集原门失败；129536 NSG/0QPS | [67 子质量范数](experiment_history/67_child_mass_norm.md) |
| E77 子画像半收缩四格 | 固定alpha半、P首槽保持、C/A/S/T+P辅助实测 | `COMPLETE_CHILD_SHRINK_FACTORIAL`；Web修复部分、Y评分损伤，A双集原门失败，161920 NSG/0QPS | [66 子画像收缩](experiment_history/66_child_shrink_factorial.md) |
| E76 子模态支持缓存诊断 | fit/compact辅助/exact辅助、6比较与72cohort | `COMPLETE_CHILD_SUPPORT_DIAGNOSIS`；低ESS非共同损伤源，辅助方向迁移不稳，0新ANN | [65 子画像支持](experiment_history/65_child_profile_support.md) |
| E75 精简保留原随机层级 | 固定compact画像/顺序，原slot随机流跳过、两新图、aux7952 | `COMPLETE_PRESERVED_LEVEL_DEVELOPMENT`；全部层级恢复，质量接续门见历史64，97152 NSG/0QPS | [64 层级保留](experiment_history/64_preserved_compact_levels.md) |
| E74 精简画像完整开发wall | compact/fullmode及规定基线、同批五L五轮 | `COMPLETE_DEVELOPMENT_WALL_VERIFIED`；55点275wall，Y局部前沿信号、Web损伤，无稳定整体结论 | [63 精简wall](experiment_history/63_compact_wall.md) |
| E73 同hub重复画像精简 | 原mode字节去重、1–3槽/真实hub、两小图、aux7952 | `COMPLETE_COMPACT_MODE_DEVELOPMENT`；Y质量门过，Web相对P负、相对完整mode正，97152 NSG/无QPS | [62 精简画像](experiment_history/62_compact_modes.md) |
| E72 真实hub计宽 | 原P/duplicate/mode固定图、普通与distinct10六控制 | `COMPLETE_DISTINCT_HUB_CONTROL`；Y相对P局部正，但双集完整接续门失败，194304 NSG/0QPS | [61 distinct控制](experiment_history/61_distinct_hub_width.md) |
| E71 多画像加宽完整开发wall | mode10/mode30/P30与规定基线同批五L五轮 | `COMPLETE_DEVELOPMENT_WALL_VERIFIED`；65点325wall，局部质量及损伤保留，无稳定整体前沿改善 | [60 加宽wall](experiment_history/60_width_wall.md) |
| E70 固定图单次ef宽度控制 | P/duplicate/mode各ef10/30，aux7952/L128 | `COMPLETE_WIDTH_CONTROL`；Y辅助质量门过、Web未过，路由成本明显增加，194304 NSG/0QPS | [59 width控制](experiment_history/59_width_control.md) |
| E69 精确画像三入口真实NSG | 同入口缓存补缺、原P全回放、两半效用 | `COMPLETE_EXACT_TRIPLE_UTILITY`；Y有限质量门通过、Web未过，38942 NSG/0QPS | [58 精确三入口](experiment_history/58_exact_triple_utility.md) |
| E68 完整画像排序诊断 | 原P/duplicate/mode完整分数参照、0新ANN | `COMPLETE_PROFILE_RANKING_DIAGNOSIS`；近似缺口明确，效用未反事实测量 | [57 排序诊断](experiment_history/57_profile_ranking_diagnosis.md) |
| E67 多画像完整开发wall | mode3P/duplicate3P与NSG/Fast/GT10，55点275轮 | `COMPLETE_MULTIMODE_DEVELOPMENT_WALL`；局部正负与旧门保持，未最终验证 | [56 多画像wall](experiment_history/56_multimode_wall.md) |
| E66 GT10多画像单小索引 | 固定3H画像/7slot去重、原P和duplicate3P控制、全fit/aux | `COMPLETE_MULTIMODE_DEVELOPMENT`；337248 NSG，原方法及局部正负/控制分开 | [55 多画像](experiment_history/55_multimode_index.md) |
| E65 今日候选开发集完整wall | NSG/Fast/GT10及真实新候选、45点225轮、失败query | `COMPLETE_DEVELOPMENT_WALL_LOCAL_WEB_SIGNAL_NO_REPLACEMENT`；Web局部正但失败增加，Y混合，无最终validation | [54 开发wall](experiment_history/54_development_wall.md) |
| E64 固定候选扩大历史开发 | 7模型×7952辅助行、预锁两半及失败门 | `COMPLETE_FIXED_POOL_AUX_NO_GATE_PASS`；WebT净+38/失败+2，Y新端点全负；222880 NSG | [53 扩大开发](experiment_history/53_frozen_pool_aux.md) |
| E63 零命中query质量重权 | 原GT10归属、2倍zero-hit质量及随机query对照 | `COMPLETE_ZERO_MASS_FIT_SIGNAL_NO_CAL_GO`；fit双集正，cal净−1/−2命中，9142新NSG/0QPS | [52 零命中质量](experiment_history/52_zero_hit_mass_v2.md) |
| E62 遗漏画像评分/拓扑四格 | 固定E61端点交叉W/G，full-fit与历史cal/audit、34灾难案例 | `COMPLETE_MISSING_FACTORIAL_NO_CAL_GO`；S/T双集cal失败，混合责任，19030新NSG/0QPS | [51 遗漏画像四格](experiment_history/51_missing_profile_factorial.md) |
| E61 遗漏GT成员全fit画像 | 原基线真实遗漏成员驱动lambda0.5聚合，原P+真实/随机目标三模型 | `COMPLETE_MISSING_TARGET_DEVELOPMENT_NO_CAL_GO`；双集cal负且各净增3零命中，audit小正值保留；28484新NSG | [50 遗漏画像](experiment_history/50_missing_target_profiles.md) |
| E60 固定动作辅助支持 | E53双seed每集40状态及原三个确定动作，历史cal/audit实测 | `COMPLETE_VERIFIED_FIXED_ACTION_SUPPORT`；双集0/40，约束全不动，17830新NSG，停止相同动作连续扩大 | [49 固定动作支持](experiment_history/49_fixed_action_support.md) |
| E59 冻结池迁移复核 | 19模型×train/monitor/cal已有输出，全量有限池上界和损伤 | `COMPLETE`；233472集合评分、0新搜索；cal有限空间稀疏，最终选择保持 | [48 冻结池迁移](experiment_history/48_frozen_pool_transfer.md) |
| E58 接受动作冲突诊断 | E52/E53/E56完整12条轨迹，train/monitor逐query增损 | `COMPLETE`；2400步/908接受，3146新NSG，0训练 | [47 接受动作冲突](experiment_history/47_accepted_action_conflicts.md) |
| E57 扩展池最终比较 | 原17候选加纯构图RL双seed，19模型cal选型 | `COMPLETE_EXPANDED_POOL_FINAL_COMPARISON`；新增88768 NSG/0性能点，最终45点225轮可追溯 | [46 扩展池最终比较](experiment_history/46_expanded_final_comparison.md) |
| E56 纯构图RL | RL优化离线C产生G(C)，全部查询恒P评分 | `COMPLETE_CONSTRUCTION_ONLY_RL_LOCAL_SIGNAL`；85204 NSG/19224build/800梯度，8图全部P字节核验 | [45 纯构图RL](experiment_history/45_construction_only_rl.md) |
| E55 固定池最终比较 | 17候选cal选型，NSG/Fast/FastGT完整五L五轮 | `COMPLETE_FROZEN_POOL_FINAL_METHOD_COMPARISON`；45最终点225wall、710144 NSG，三指标已交付 | [44 最终比较](experiment_history/44_final_method_comparison.md) |
| E54 完整模型四格 | E52/E53全部selected固定W/G交换 | `COMPLETE_WHOLE_LEARNED_MODEL_FACTORIAL`；26物理图，12424 NSG，0训练 | [43 完整模型四格](experiment_history/43_learned_model_factorial.md) |
| E53 RL反馈步长接受 | 原RL方向，r/4、r/2、r+不动真实择优 | `COMPLETE_FEEDBACK_STEP_RL_LOCAL_SIGNAL`；125577 NSG/800梯度/352接受 | [42 RL反馈步长](experiment_history/42_feedback_step_rl.md) |
| E52 连续候选择优提交 | 原RL同候选预算/日程，原J在合法已测候选+不动中择优 | `COMPLETE_DIRECT_CANDIDATE_COMMIT_LOCAL_SIGNAL_SEED_INSTABILITY`；Web双seed正，Y一正一负；113950 NSG/800决策295提交，0梯度 | [41 连续提交控制](experiment_history/41_direct_candidate_commit.md) |
| E51 更新方向/半径 | 原E47 RL40状态，Adam方向三半径与最佳候选方向两中间点 | `COMPLETE_UPDATE_DIRECTION_RADIUS_DISCRETE_STEP_AND_DAMAGE`；放大救回9/12与4/4空更新机会，最大半径也伤害Yandex；3416 NSG | [40 步长方向控制](experiment_history/40_update_direction_radius.md) |
| E50 候选到均值转化 | E47全1600状态/12800候选的原J-best、hit-best和Adam均值 | `COMPLETE_CANDIDATE_COMMIT_DIAGNOSIS_UPDATE_TRANSFER_BOTTLENECK`；有正候选时均值空响应Web86%/Yandex96%，直接提交控制门通过；0新搜索 | [39 更新转化诊断](experiment_history/39_candidate_commit_diagnosis.md) |
| E49 冻结局部画像性能 | E47全部selected固定，cal选seed后audit及五L五轮 | `COMPLETE_FROZEN_LOCAL_RL_EVALUATION_NO_DUAL_FRONTIER_GAIN`；WebVid局部正值，Yandex质量全平；423680 NSG/80点250wall | [38 冻结模型评测](experiment_history/38_frozen_local_rl_evaluation.md) |
| E48 评分/邻接四格 | 原E44全部20状态/160动作补齐评分独变与拓扑独变 | `COMPLETE_SCORE_TOPOLOGY_FACTORIAL_MIXED_MECHANISM`；WebVid邻接响应更多，Yandex评分更多，两因素均未过单独训练接续门；7525 NSG | [37 四格因果控制](experiment_history/37_score_topology_factorial.md) |
| E47 局部画像完整反馈训练 | 同局部表示/σ/步数/两臂双seed，完整4096反馈与逐均值精确缓存 | `COMPLETE_FULL_FEEDBACK_PROFILE_RL_LOCAL_RL_SIGNAL_AGGREGATE_GATE_STOP`；RL双集有选中正值，WebVid ES未过统一门；228832 NSG/1600更新完成 | [36 完整反馈训练](experiment_history/36_full_feedback_profile_rl.md) |
| E46 完整三入口精确反馈复用 | 180图全池路由，仅入口变化新NSG；全部原E44返回/奖励/梯度恢复 | `COMPLETE_EXACT_FEEDBACK_CACHE_FULL_RECOVERY`；候选补测1333/655360，种子/路由另计；3061新NSG、0训练，可进入完整反馈对照 | [35 精确反馈复用](experiment_history/35_exact_feedback_cache.md) |
| E45 确定均值单步完整反馈 | 固定20状态只替换原八方向的query梯度，原/全确定行真实全池查询 | `COMPLETE_MEAN_UPDATE_CONTROL_SMALL_FULL_FEEDBACK_SIGNAL`；WebVid净0→+1、Yandex−2→+3，小正值/避损；167040 NSG、20独立反事实步，0连续训练 | [34 确定单步](experiment_history/34_mean_update_control.md) |
| E44 局部动作全池/采样诊断 | 固定20状态/原八方向，180图完整train4096；原128回归与精确条件方差 | `COMPLETE_LOCAL_SAMPLING_DIAGNOSIS_STOP_STRATIFIED_SAMPLER`；漏反馈与稀疏并存，方差比1.074/0.978，停止原入口分层；739008 NSG，0训练 | [33 全池与采样](experiment_history/33_local_sampling_diagnosis.md) |
| E43 局部画像RL/ES | 原P/B/H，一次一行系数动作，同日程/预算两臂双seed完成 | `COMPLETE_LOCAL_PROFILE_RL_STOP_MONITOR_GATE`；WebVid ES局部+0.0781pp，Yandex未过monitor门；反馈稀疏、每hub多为一次更新，默认保持 | [32 局部画像](experiment_history/32_local_profile_rl.md) |
| E42 被移除画像责任控制 | 固定新目标1627796/8309868，双集八格与全2048条件信用 | `COMPLETE_REMOVED_PROFILE_ATTRIBUTION_CONTEXT_DEPENDENT_CREDIT`；WebVid必要不充分/Yandex充分不必要，明确背景依赖；8576 NSG、0更新 | [31 被移除画像](experiment_history/31_removed_profile_factorial.md) |
| E41 目标/其余画像2×2 | 双集C/F/S/R八格普通HNSW→NSG，原案例和全1024、逐query交互 | `COMPLETE_TARGET_REST_FACTORIAL_WEBVID_LOCAL_SIGNAL_YANDEX_TARGET_NULL`；WebVid仅目标+4无损，Yandex目标命中无效；8576 NSG、0更新，默认保持 | [30 画像隔离](experiment_history/30_profile_factorial.md) |
| E40 画像动作收益损伤归因 | 对E39九配置逐query上界、单一最佳、覆盖/损伤分解及入口/相似query关联；全部缓存复算 | `COMPLETE_PAYOFF_ATTRIBUTION_LOCAL_OPPORTUNITY_WITH_CANCELLATION`；局部机会稀疏、正负抵消明确，未证共享表示硬冲突；0新搜索/训练 | [29 收益损伤](experiment_history/29_profile_payoff_attribution.md) |
| E39 固定参数批次诊断 | 固定双集两μ/各八扰动，以train另取1024检查互斥批次方向；36静态图真实查询 | `COMPLETE_FIXED_PROFILE_BATCH_DIAGNOSIS_STOP_BUDGET_EXPANSION`；四点主512方向全负，扩大批次未过稳定门；38592次NSG、0更新，默认保持 | [28 固定批次](experiment_history/28_fixed_profile_batch_diagnosis.md) |
| E38 离线画像反馈诊断 | 复算E37全部反馈/梯度，固定方向query二分、贡献集中性、80组精确μ匹配及全部中心 | `COMPLETE_OFFLINE_PROFILE_DIAGNOSIS_NO_NEW_SEARCH`；反馈稀疏/批次方向不稳，惩罚非主导，表示与部署失配未定因；0新搜索/训练 | [27 反馈诊断](experiment_history/27_offline_profile_diagnosis.md) |
| E37 离线画像策略优化 | 真实候选画像重建HNSW→原NSG奖励，两臂双seed共8×200更新，静态导出、50点250轮单线程wall | `COMPLETE_OFFLINE_PROFILE_RL`；主RL双集cal负值、audit混合，开发门停止；ES局部正值，无稳定RL增量，默认未换 | [26 离线画像RL](experiment_history/26_offline_profile_rl.md) |
| E36 query相关三入口换点 | 当前GT10一次top8、真实56联合标签、RL/同策略Exact双seed共8×3000更新，38部署点和30轮单Lwall | `COMPLETE_QUERY_SWAP_POLICY`；Yandex局部正值/WebVid开发门失败，RL QPS下降8%～9%，无新validation/held-out，默认未换 | [25 query换点](experiment_history/25_query_swap_policy.md) |
| E35 HNSW选点最小验证 | 双集128个pilot，当前GT10访问旁路、exact/ef40与当前C8全部56个真实三入口 | `COMPLETE_HNSW_SELECTION_DIAGNOSIS`；强连通且已评分好点漏选，exact增量小/联合oracle有空间；没有新RL/QPS | [24 HNSW选点](experiment_history/24_hnsw_selection_diagnosis.md) |
| E34 冻结RL图性能补测 | 用户另授权原NSG/Fast30K/GT10-hard及RL，WebVid另起点GT10-soft；45点225轮单线程wall与失败率 | `COMPLETE_FROZEN_RL_BENCHMARK`；全量结果保留，90000输出复核，未重训/改选/替换默认 | [23 HNSW-RL性能](experiment_history/23_hnsw_rl_benchmark.md) |
| E33 HNSW图边强化学习 | 两集双RL seed、4×600更新，真实HNSW→NSG奖励与静态图导出；20开发点含逐节点同出度随机控制 | `HNSW_EDGE_RL_COMPLETE_WEBVID_SIGNAL_NO_DUAL_GAIN`；WebVid主图局部门通过、audit未胜随机，Yandex失败；无新validation/QPS | [22 HNSW图边RL](experiment_history/22_hnsw_edge_rl.md) |
| E32 直接真实收益策略 | 同模型/候选/标签、teacher与精确期望Recall共4次1200步；在线C8与21个真实fit/开发点 | `DIRECT_REWARD_POLICY_COMPLETE_FIT_GAIN_MIXED_DEVELOPMENT_STOP`；双集缓存门通过、相对teacher开发四正，WebVid cal未胜默认且路由成本高，停止validation/QPS | [21 直接收益策略](experiment_history/21_direct_reward_policy.md) |
| E31 有界训练有效性检查 | 同E30教师/模型/λ100，固定优化日程4次×1200步，302.73s；旧/新模型独立恢复、缓存真实标签与全H界 | `TRAINING_EFFECTIVENESS_COMPLETE_OPTIMIZATION_IMPROVED_CACHE_GATE_FAILED`；WebVid有进一步局部收益，Yandex未提升，双集缓存门失败；新NSG/QPS为0 | [20 训练有效性](experiment_history/20_training_effectiveness.md) |
| E30 等效三入口教师 | 严格并列G、单/多教师4次训练与漂移控制；完整fit/开发、120正式点五轮wall | `EQUIVALENT_TEACHER_SETS_COMPLETE_NO_RELIABLE_REPLACEMENT`；描述性最快与推荐分开，原方法及全部正负保留 | [19 等效教师](experiment_history/19_equivalent_teacher_sets.md) |
| E29 教师与目标对齐 | 原/保留教师×CE/margin的8次共享linear训练；完整fit、开发及110正式点三轮wall | `TEACHER_OBJECTIVE_ALIGNMENT_COMPLETE_NO_STABLE_DUAL_GAIN`；拟合/实际检索与因素交互分别记录，原模型恢复并保留全部正负 | [18 教师与目标对齐](experiment_history/18_teacher_objective_alignment.md) |
| E28 GT10共享入口变换 | C8完整三入口教师、共享linear/MLP/free同目标12次训练；冻结选择后90正式点三轮wall | `SHARED_TRANSFORM_EXPLORATION_COMPLETE_NO_FORMAL_GO`；教师有空间但共享模型loss下降未提高教师top3重合；完整正负保留，版本收口 | [17 共享入口变换](experiment_history/17_gt10_shared_transform.md) |
| E27 GT10收益机制分析 | 重建fit归属并连接108个既有点；限定shuffle/局部exact诊断及WebVid两硬画像五L三次wall | `GT10_MECHANISM_ANALYSIS_COMPLETE_WITH_BOUNDED_DIAGNOSTICS`；两个正点在exact下保留，WebVid速度缩小但复现；信息与平滑未完全分离，本轮收口 | [16 GT10机制](experiment_history/16_gt10_mechanism.md) |
| E26 单路画像收缩 | E24两端点间三alpha；新cal/audit、冻结alpha0.75、validation50点三次单线程wall及新增损失分解 | `SHRINKAGE_DID_NOT_STABILIZE_SELECTIVITY_NO_FORMAL_GO`；损伤减少伴随收益流失和新损伤，十点九个Recall低于E24；本版本收口 | [15 画像收缩](experiment_history/15_profile_shrinkage.md) |
| E25 两固定画像的选择性改道 | fit8192真实A0/A1三入口配对；Base/Dual门控、cal选/audit报、双数据集validation60点各三次单线程wall | `SELECTIVITY_NOT_GENERALIZED_NO_FORMAL_GO`；WebVid局部修复不抵双路成本，Yandex主规则丢失大多数收益；本版本收口 | [14 选择性改道](experiment_history/14_selective_profile_gate.md) |
| E24 固定H的GT-topK硬/软画像 | fit GT闭式构建GT1/GT10×硬/软，双数据集各8候选；cal选/audit报、validation2K×五L×六方法，单线程60点完成 | `EXPLORATORY_LOCAL_FRONTIER_SIGNAL_NO_FORMAL_GO`；两主候选各3/5点同时提高Recall/QPS，存在负点及开发波动，软并非普遍更好；本版本收口 | [13 GT-topK画像](experiment_history/13_gt_topk_profiles.md) |
| E23 真实三入口收益排序 | 固定真实入口，88万实际组合标注、Full/rank8各三λ；双数据集validation2K五L、五方法、单线程50点全部完成 | `EXPLORATORY_SMALL_RECALL_SIGNAL_NO_CLEAR_QPS_GAIN`；Full目标更优但最终未胜rank8，Yandex rank8五L Recall均高于matched Fast；未形成明确QPS优势，本版本收口 | [12 三入口排序](experiment_history/12_three_entry_rank_exploration.md) |
| E01 旧NETG/ACO/DPC/Router | 节点权重、hub发现、逐query×hub搜索标签、离线Router；旧Deep/SIFT/Gist/Yandex等报告 | 已使用真实搜索监督；ACO-Max有实现缺陷，旧数据/成本不可直接混入新official-IP协议 | [01 Fast与legacy](experiment_history/01_fast_and_legacy.md) |
| E02 Fast WebVid/Yandex | QGT-Cover＋GT1 basin画像，正式held-out、多seed/timing与逐query对照 | 已有基线结果；WebVid质量收益、Yandex主要归一化QPS收益，完整GT-inclusive构建成本另有缺口 | [01](experiment_history/01_fast_and_legacy.md) |
| E03 LAION迁移 | validation与held-out均完成；修正首轮raw口径后使用unit-IP | 已完成跨base corpus/scale控制；与WebVid共用public query来源，不是独立第三query任务 | [01](experiment_history/01_fast_and_legacy.md) |
| E04 三view早期质量 | 三个build作一个ensemble，固定anchor、三路top8合并 | 同L有小收益，早期阶段GO不是最终方法GO | [02 Multi-view](experiment_history/02_multiview_and_attention.md) |
| E05 Multi-view正式E0/E1/E1b | 路由parity、dense成本、固定后两路Micro-HNSW与等total-NDC对照 | `NO_GO_ROUTING_COST`；E2–E4依gate未跑；旧E0计时证明范围后来收窄 | [02](experiment_history/02_multiview_and_attention.md) |
| E06 confidence attention | 按置信度调整view权重，检验共享alpha | 两数据集偏好相反；当前共享公式NO_GO，不是否定全部attention | [02](experiment_history/02_multiview_and_attention.md) |
| E07 sparse utility ranker | Fast32候选、真实Recall/NDC、soft labels与交互打分 | 局部小正信号未形成跨数据集成本收益，停止该模型路线 | [04 效用与表示](experiment_history/04_utility_and_representation.md) |
| E08 search-aware centroid | WebVid5K全815入口真实标签，按赢家重新聚合画像 | 有局部同L Recall提升，未证同成本/跨数据收益；不能称未用过真实效用监督 | [04](experiment_history/04_utility_and_representation.md) |
| E09 utility residual | signed utility残差修正原prototype | WebVid微弱正收益，缺双数据/完整成本验证；不写成已证跨数据失败或方法GO | [04](experiment_history/04_utility_and_representation.md) |
| E10 residual basin modes | v1多模式与v2 anchored校正两轮 | 分别保留机制/成本/结果边界，未形成稳定改进；不是confidence或Multi-view同一实验 | [04](experiment_history/04_utility_and_representation.md) |
| E11 BTG v1–v4 | raw-topology/BFS转移与多版纠偏、跨数据效用检验 | 静态拓扑扩散路线NO_GO；各版修正与局部正值不丢失 | [04](experiment_history/04_utility_and_representation.md) |
| E12 原existing-hub oracle | 旧WebVid validation1K，全H single及独立命中并集组合代理 | 确认候选内有空间；免费oracle/并集不是部署点或真实最优联合搜索 | [05 Oracle与reroute](experiment_history/05_probe_reroute.md) |
| E13 paid probe失败检测 | 只支付L10，识别可能从改道受益的query | 风险检测有增量信息；早期L10/16/32却只收费L10的版本无效 | [05](experiment_history/05_probe_reroute.md) |
| E14 restart/merged rerouter | 候选32、merged Recall/NDC、trace/frontier/topology选择器 | 替代入口选择失败；不能把已用监督误记为独立single或仅几何标签 | [05](experiment_history/05_probe_reroute.md) |
| E15 finite-beam v1与审计 | GT-free trace的增量信息、成本和收益集中性 | 正式解释为信息增量通过、成本对齐失败；旧“没有增量”判定被纠正 | [06 finite-beam/Atlas](experiment_history/06_finite_beam_and_atlas.md) |
| E16 v2 cost-first distillation/Atlas | 64-query近邻搬运top8真实效用，在线不probe | 四点utility差区间跨0；不能据此否定任意重教师到轻模型蒸馏 | [06](experiment_history/06_finite_beam_and_atlas.md) |
| E17 GATE同图适配 | WebVid原图上的作者方法受限适配；无效HBKM版本另存 | 本地适配未胜Fast，Yandex扩展未跑；不等于论文全方法被证伪 | [03 基线](experiment_history/03_baselines.md) |
| E18 分层P2 | 64区域、门户与统一/均匀/概率候选池、有限oracle | 真实区域保护退化；oracle有质量但更慢，仅机制门槛允许一次P3修订 | [07 层次P2/P3](experiment_history/07_hierarchical_p2_p3.md) |
| E19 分层P3及诊断 | 16×16结构/768门户；门户暴露、seen/unseen、局部尺度、23trace补齐 | P3搜索收益NOPASS；诊断完成，P4–P8未跑；停止不等于长期研究完成 | [07](experiment_history/07_hierarchical_p2_p3.md) |
| E20 Fast根因诊断 | 两数据集各512pilot、全H single/C8 pair-triple、最近fit/随机控制 | 实现检查通过；几何代理缺口、短名单损失，撤下固定anchor/3；未证一般不可学习 | [08 Fast诊断](experiment_history/08_fast_router_diagnosis.md) |
| E21 C同状态有限动作 | C0成本锁、独立state-machine C1、每dataset2K drl_train单checkpoint C2 oracle | C1通过；WebVid两点实质门通过，Yandex +0.230/+0.140pp不足+0.5pp，`NO_GO_UNCONDITIONAL_HEADROOM_STOP_C`；C3/C4未跑 | [10 C真实执行](experiment_history/10_c_state_intervention.md) |
| E22 A+B固定槽位入口选择 | 全入口效用标签、12个模型拟合；用户收缩为双数据集validation2K、单seed、单线程NSG/Fast/A+B五L比较 | 同一模型五L入口完全不变；相对NSG质量改善，但相对Fast小L退化且十点QPS均较低，`EXPLORATORY_NO_OVERALL_FAST_GAIN`；旧大矩阵取消 | [11 A+B五点探索](experiment_history/11_ab_fixed_slot_exploration.md) |

## 2. 准备与设计：不能计作方法实验

2026-09-09在E21停止后，用户先将A+B指定为下一阶段主线并要求只读研究，随后另行授权真实执行，形成E22及后续E23。下表保留各旧设计原件的未执行身份，不能把其继任版本的实现/结果回写到旧设计；当前最近完成记录为E95开发验证与分支停止，完整性能比较仍为E94，当前状态以[s-target.md](s-target.md)为准。

| 记录 | 已完成 | 尚未执行/不能声称 | 详细入口 |
|---|---|---|---|
| 9月13日收口后的RL方向复盘 | 依据E50更新转化、E52/E53对照、E60支持、E89交互与E94结果，下调现有RL/局部修补分支，保留离线学习索引目标 | 本次只更新交接；新方法比较/设计及实验未执行，不是E95，不证明RL整体无效 | [86 收口后复盘](experiment_history/86_post_closeout_rl_direction_review.md)、[下一阶段](s-target.md) |
| E26后GT10收益机制分析计划原件 | 2026-09-10按用户要求冻结下一步归因目标；当时只更新文档 | 计划原件保留未执行身份；2026-09-11继任E27已完成既有分析与限定补测，见上表，不将原计划本身计作实验 | [当前目标](s-target.md)、[历史16](experiment_history/16_gt10_mechanism.md) |
| E23后GT入口/聚类/rank/OOD微型图调研 | 核对当前builder、E20/E23既有证据和14项一手工作；推荐固定H的GT-topK软画像、真实效用分组备选及保分数成对拉伸效率支线 | `RESEARCH_COMPLETE_METHOD_UNSELECTED_UNRUN`；未重新聚类、标注、训练、构建ANN或评测，rank8仍未证最优，无方法/性能GO | [四问题报告](entry_method_exploration/20260910_ood_hubs_clustering_router_research_v1/report.md)、[09研究记录](experiment_history/09_research_designs_not_experiments.md) |
| 四问题调研后的详细实验交接 | 按用户要求在s-target展开全部优先级：固定H软画像、真实效用分组/入口及联合评分、微型图拉伸/建边，另列聚类器、rank和范数消融；各含方法、对照、阶段、成本、停止依据与新对话指令 | `NEXT_EXPERIMENT_DIRECTION_DEFINED_UNRUN`；只有文档交接，该交接原件当时未执行；用户随后授权第一方向E24，已冻结并完成，见历史13；不回写研究原件状态 | [当前目标](s-target.md)、[09接续记录](experiment_history/09_research_designs_not_experiments.md) |
| E22后梯度/低秩/MLP方法复核 | 阅读11篇相关论文的方法章节及GATE/LRSG作者代码，复核原训练与既有结果；提出真实三入口排序、Fast锚定完整W参考和离线共享MLP备选 | 该只读原件保留`RESEARCH_COMPLETE_METHOD_UNSELECTED_UNRUN`；后续用户另授权继任实验E23，不能将后续执行回写为原研究已运行 | [研究报告](entry_method_exploration/20260910_optimizer_research_v1/report.md)、[E22补充](experiment_history/11_ab_fixed_slot_exploration.md) |
| 比较依赖准备 | METIS/GKlib、独立Python、gp-ann/MIPS、RoarGraph、局部MKL与smoke | 依赖就绪不是RoarGraph/kRt/LIRA等正式同机结果 | [03 基线与环境](experiment_history/03_baselines.md) |
| 文献复审R0–R2 | 原文/代码/本地假设复核与筛查建议 | R0–R2未执行且已被后续方向替代 | [09 设计记录](experiment_history/09_research_designs_not_experiments.md) |
| 入口v1/v2 | 指令、相关工作、C8固定anchor三入口/40维草案 | 未训练该模型；相关默认限制被E20撤下 | [09](experiment_history/09_research_designs_not_experiments.md) |
| v3离线重/在线轻 | 澄清训练与推理成本边界 | 没有新标签/模型/实验 | [09](experiment_history/09_research_designs_not_experiments.md) |
| v4效用树 | 原生搜索收益/多叶同hub的树设计与gate | 尚未实现训练器、未生成完整20K×H标签、无性能GO | [09](experiment_history/09_research_designs_not_experiments.md) |
| v5四方向 | 近期前作、机制/成本/风险与独立复核 | v5设计原版的A/B/C/D均未实施；A+B及C后来完成更细R0，其中C的独立stage1继任执行见E21，不能回写成v5原版已运行 | [09](experiment_history/09_research_designs_not_experiments.md) |
| A/B独立R0与联合理论 | A、B分别完成组件碰撞审计和未执行协议；随后按用户意见改用方法层原创性标准，形成fixed-M、Fast可恢复的flat slot/action联合理论 | 这些旧设计原件未运行；后续只读研究推荐自由低秩W=P0+VZ，实际继任实现/训练/五点评测另记E22，不混同旧共享affine设计 | [09](experiment_history/09_research_designs_not_experiments.md)、[E22](experiment_history/11_ab_fixed_slot_exploration.md) |
| C独立R0 | 补查QING/ANNiE等最近前作，核对E13–E16与当前kernel，冻结同状态有限动作、state×reuse析因和A+B条件接口 | R0原版本未实现未运行；后续新授权stage1已执行C0–C2并按实质门停止，见E21；无C3/C4或A+B联动GO | [09](experiment_history/09_research_designs_not_experiments.md) |

## 3. 容易误读的版本与证据

E72协议列有“不足3hub拒绝”合成负例，但实际只测引用计数下溢；运行时有检查不等于已覆盖。原封存保持，见[独立更正](entry_method_exploration/20260913_until2100_v1/reviews/e72_synthetic_scope_correction_session5.md)。E73/E74使用普通variable画像路径，不含distinct回调。

- finite-beam v1以`v1_audit`纠正后的状态为正式解释；原decision保留但不单独作为最终判断。
- Fast诊断正式引用`analysis/v2`和`costs_v2.json`；v1保留其统计/事件计时修正过程。
- P2原gate是在16条trace时作出的，后续按原名单补齐23条；两件事分别记录，不能覆写当时gate或说trace仍欠7条。
- 分层夜间P0读取validation字节作完整性检查，未作方法性能评测；Fast根因诊断未打开原始validation/held-out。不同分支使用历史必须逐条查，不能说全项目从未用过validation。
- 原`实验总结.md`是分层夜间报告，原`总结.md`是早期NETG评审记录，`aco_router_fast_entry.md`是Fast转向复盘；都保留原名与内容，通过01/07追溯，不与当前`summary.md`抢职责。
- 旧文件中的待执行/GO/当前计划和spec章节号属于当时版本；当前目标以`s-target.md`为准。历史失败只约束已测试机制与设置，不能扩为数学不可能，也不能换名绕过证据。

## 4. 后续维护

新增实验或停止阶段时，先在`experiment_history/`新增或扩充对应详细卡片，保存协议/输入身份、实际配置/命令、主要结果、成本/未知项、停止理由及原证据索引，再在本表登记。必要的更正保留前后版本；概览不抹平局部正信号、未执行部分或数据口径差异。

当前根四文件、详细卡片和原证据形成“概览→复盘→原件”链。目录说明与卡片要求见[README](experiment_history/README.md)；本次文档整理的旧版本、保护与审查保存在[_maintenance](experiment_history/_maintenance/20260908_document_reorganization/)。

2026-09-12 [今晚完整收口](entry_method_exploration/20260912_until2000_v1/closeout/final_report.md)汇总E50–E59机制证据、19候选最终选择和NSG/Fast/FastGT三指标，新增下一轮设计保持未运行身份；原48份历史卡片均保留。

2026-09-13第6会话[E75–E78综合报告](entry_method_exploration/20260913_until2100_v1/session6_report/report.md)汇集四阶段和454个失败query并集（237个失败状态变化），0新ANN；各原实验卡片和seal不改。

2026-09-13第12会话补充E94既有返回的15组成员/失败复算，50,000返回独立评分全部一致，0新增ANN/QPS；[短报告](entry_method_exploration/20260913_until2100_v1/session12_report_v1/report.md)，原阶段结论保持。

2026-09-13第13会话完成[整日中文汇报](entry_method_exploration/20260913_until2100_v1/session13_report_v1/report.md)、六页PDF及401查询离线浏览；全部50原点/10730呈现单元与实际浏览器下载验收通过，0新增训练/ANN/QPS。独立[详细记录84](experiment_history/84_campaign_20260913_report.md)承接报告与机制边界，不增加实验编号，不改E94封存或整日完成状态。

2026-09-13第14会话核验交付封存，补入监督208实际六页PDF查看及监督211第13退出/第14串行接续证据；原报告/历史卡保持。新增[交付入口](entry_method_exploration/20260913_until2100_v1/session14_closeout_v1/delivery.md)及[详细记录85](experiment_history/85_campaign_delivery_readiness.md)，0新实验/训练/ANN/QPS；当时待监督接续，随后监督器于21:00:01退出并完成限时任务检查，见[收口后复盘86](experiment_history/86_post_closeout_rl_direction_review.md)。旧会话快照不回写。
