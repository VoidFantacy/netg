# ACSG 实验与研究索引

2026-11-20 完成 E211 并切换默认。标准 Flat raw-IP 的 `ACSG::search_new(mode=2)` 默认走 SPAN4，L2 等其他距离路径走标量。四个真实数据集各3,072条，真实K1/K100各7个L，224点、448个完整CPU15单线程批次。112个新旧配对返回逐字节相同，112/112个配对通过逐点速度筛选。纯GT10完整QPS变化+13.74%至+28.35%，GT10+B32变化+13.16%至+27.94%。 [E211 历史卡片](experiment_history/211_span4_production_default_v1.md)

2026-11-20 完成 [E210 四集 SPAN4 复测](experiment_history/210_span4_four_dataset_retest_v1.md)。COCO、Flickr30k、WebVid、Yandex first10M 四集各3,072条真实公开查询。真实K1/K100，各7个L，224点、448个完整CPU15单线程批次、1,376,256次正式查询，每点两遍。112个优化点返回与各自对照逐字节一致。纯GT10 QPS变化+12.64%至+30.40%，56/56点过预设筛选。接完整B32变化+11.75%至+29.65%，56/56点过筛选。四集全部已测同L预算支持内核替换候选。生产发布合同仍为E99 GT10。

2026-11-20 完成 [E209 WebVid两项等价复测](experiment_history/209_webvid_b32_span_confirmation_v1.md)。WebVid soft-t1 两个各2,048条查询窗口，真实K1/K100、L100/200/400，K100另测L960。71个点、142个单线程完整批次、290,816次正式查询，每点两遍。E208三个连续正向组合中0个按冻结口径在确认窗复现。SPAN4＋原B32 的完整 QPS 各点提升16.96%至22.24%，两个窗口同通过的预算为7/7。全部优化点与现用控制逐字节一致。默认 E99 GT10。

2026-11-20 完成 [E208 四集 B32 等价优化](experiment_history/208_b32_equivalent_speed_v1.md)。COCO、Flickr30k、WebVid、Yandex 共四集，各取公共最前3,072条。真实 K1/K100，L100/200/400，96个点、192个完整CPU15单线程批次、589,824次正式查询，每点两遍。48个优化点均与原 B32 逐字节一致。9个点通过局部正向条件，0个点通过镜像下降条件。连续两个预算达到正向条件的组合有3个，包括WebVid K1 B32-PF4、WebVid K100 B32-PF4、WebVid K100 B32-BOTH。默认 E99 GT10，原 B32 作为固定补点强对照。

2026-11-20 完成 [E207 B32补点分段计时](experiment_history/207_b32_stage_cost_v1.md)。COCO hard 和 WebVid soft-t1，各取公共10K的前3,072条，真实 K1/K100，L100/200/400。12个配置、48个正常批次和24个分段批次，合计221,184次计时查询。CPU15单线程，每点两遍。12个配置中，额外精算均是最大的残差阶段，占分段残差时间的60.6%–94.2%。K100/L200下，COCO/WebVid的额外精算为14.55/22.01微秒/query，查表去重1.97/2.51，合并5.29/6.07。

2026-11-20 完成 [E206 按较小预算构建固定残差表](experiment_history/206_residual_budget_matched_table_v1.md)。COCO/WebVid 离线验证真实 K1/K100，生成128,000次真实训练 ANN，完成384,000次表合并。仅 WebVid K100 通过预锁继续条件并完成32点、64个完整CPU15单线程批次，每点两遍。WebVid K100，B32-L184 在 L184 为 73.4082% / 1469.37 QPS，旧完整 B32 在 L192 为 74.1992% / 1407.59 QPS，变化为 -0.7910 个百分点和 +4.39% QPS。本轮未建立 L184 对旧完整 B32 L192 的替换依据。当前默认采用 E99 GT10（WebVid soft-t1），保留完整 B32 已验证的条件有效区间。

2026-11-20 完成 [E205 公共前缀分数诊断](experiment_history/205_residual_prefix_signal_v1.md)。COCO/WebVid，真实 K1/K100，回放 L100/200/400。384,000 个表与查询状态，3,840,000 次十配额实际合并。B32-FIT 下 L100 四个数据集与 K 单元均未过门，正式点为0。

2026-11-19 完成 [E204 三路残差表预算分配](experiment_history/204_residual_budget_allocation_v1.md)。COCO/WebVid，144点、288个完整CPU15单线程批次，288万查询，真实K1/K100，每点两遍。ADAPT48 的12个点中 8 点被同期强控制或固定方案覆盖，同L相对 FIXED48 严格双升 4/12。默认保持 E99 GT10。

2026-11-19存储维护：[旧数据简档](experiment_history/_maintenance/20261119_obsolete_payload_prune_v1/archive_index.md)。用户授权直接删除过旧实体数据，保留原研究卡片、报告、配置、manifest和CSV汇总。清单内旧模型/原始返回当前已不可直接重放；历史验收代表当时核验，不改变已测结论。当前七集和最近E200–E203冻结依赖保留。

2026-11-17 完成 E203 两数据集残差查询双原型：COCO/WebVid，236点/472完整CPU15单线程批次，真实K1/K100、每点两遍。三个新版本36点中36/36被同期GT10/B32/SQ覆盖；两次描述性时长范围比较仍覆盖36/36。默认保持E99 GT10（WebVid soft-t1）。 [详细记录](experiment_history/203_residual_query_prototypes_v1.md)。

2026-11-17完成四多模态E202：COCO、Flickr30k、WebVid、Yandex official first10M；544点/1088完整CPU15单线程批次，952万正式查询，真实K1/K100，每点两遍QPS算术平均。 固定共享表示新版未取得Recall–QPS改进，不替换旧QR3/B32，默认保持E99 GT10。 [E202详细记录](experiment_history/202_shared_residual_value_v1.md)。

2026-11-13完成[E201查询条件残差首版](experiment_history/201_query_conditioned_residual_v1.md)：COCO/WebVid、172点/344完整CPU15单线程批次，每点两遍。当前稀疏树不替换B32；同入口遗漏异质性成立，QR对K100略正、K1负。全网格覆盖44/60、同阶段41/60，未覆盖点保留为取舍；默认保持，无待恢复队列。原理论设计保留当时身份，首版未实现强教师蒸馏。

同日后续[方法诊断](experiment_history/_maintenance/20261113_query_conditioned_residual_diagnosis_v1/README.md)：无新ANN/QPS，复算36个原生叶trace与两集全部K/L合法角色。K100/L200当前QR3支持2096/1785，GT质量引导同beam3为22103/36368；第8层已丢约82%–85%目标，不能只归因深层回退。固定完整q遗漏迁移探针在12个K100 dev/cal组合均高于QR3，cal/L200为375→968、360→1053；普通GT标签仅208/470。支持继续改表示/监督/路径训练，尚无新部署收益；该诊断时教师与压缩后继仅设计，K1两项反例保留；后续实现及正式四集测量另见E202。

前一E200于2026-11-10完成[E200四多模态四方法加密重测](entry_method_exploration/20261110_multimodal_four_method_retest_v1/analysis/final_v1/report_zh.md)：640点/1280完整CPU15单线程批次、1120万正式查询，每点两遍、每K20档L。COCO/WebVid残差有明确有效区间，Flickr按目标取舍，Yandex优先GT10；GATE160点均被同期其他方法覆盖。完整数值与实际图形已核验，默认不变。前一实验E199及复杂残差分支停止决定保留历史身份。当前结论读summary，实现读spec，后继读s-target。

E199：[结论](entry_method_exploration/20261104_gate_timing_cost_v1/findings_zh.md) · [报告](entry_method_exploration/20261104_gate_timing_cost_v1/report_zh.md) · [PDF](entry_method_exploration/20261104_gate_timing_cost_v1/E199_残差门控时机与精排成本_20261104.pdf)。E199四个多模态数据集的门时机与精排成本实验已完成736点/2208完整单线程批次；主门策略80个窗口点中79个被同期强控制覆盖。 无待恢复队列。

2026-11-05文档交付：[8页当前方法/残差收益/低召回修复/局限修订PDF](reports/20261105_method_benefits_limits_v3/README.md)。直接保留原3页方法，后接E199四集K1/K100曲线、E183完整窗三阶段修复与同L200成本、两项限定范围的局限；不把已停止双塔列入当前方法。依用户要求去掉收益图A/B浅线，合并点数值不变；另复核COCO七L/21份原包，新增失败来自GT10，B32未新增也未救回。原v2综合版、3页方法版、无PDF尾部分析与旧实验卡片均保持原件，无新实验编号、性能、训练或默认变更。

2026-11-05后续分析：[严格低于10%的GT10/B32三阶段分解](reports/20261105_low_recall_stage_attribution_v1/README.md)。无PDF，复用E183完整窗口与七L，分别核救出/新增、B32修复原NSG遗留或GT10新增问题、平均召回贡献和完整费用；49组三阶段、392状态另由原GT/实际返回复算通过。已有数据足够，无新ANN/计时/实验编号，默认与研究收敛边界保持。

2026-11-01设计汇报：[学习残差导航入口与拒绝筛选](entry_method_exploration/20261101_learned_residual_navigation_design_v1/report_zh.md)。按用户最新优先级，不限制离线训练费用，区分直接答案与导航价值，设计真实收益监督/多代表/条件组合选择。该设计当时为THEORY_ONLY_UNIMPLEMENTED_UNTESTED，仅复算E195已有探针；当时最新完成E196。其后部分机制在E197、E198分别实现/测量，旧设计封存不回写。

2026-10-28解释与接续补充：[单位新增召回的访问成本](experiment_history/_maintenance/20261028_completion_cost_handoff_v1/conclusion_zh.md)。仅整理E187已有证据、未实施的省费方向和新对话入口，无新增实验编号或性能。

2026-10-29结论同步：[历史有效残差场景](experiment_history/_maintenance/20261029_residual_positive_evidence_sync_v1/conclusion_zh.md)单列E173 M5、E191 B32/SQ的实际正面证据和边界。E193有限门控未过门不撤销这些结果；本次纯整理，无新性能。

2026-10-30理论同步：[残差补全与补点导航价值](entry_method_exploration/20261030_residual_navigation_theory_v1/theory_zh.md)，状态THEORY_ONLY_UNIMPLEMENTED_UNTESTED。区分答案/入口价值、入/出方向与密度代理，记录E174已测一跳机制及未验证的导航代表/路径修复/主搜索评分提案。该次无新实验编号或性能，当时最新完成为E194；当前顺序见s-target，原字节和封存桥接见[同步入口](entry_method_exploration/20261030_residual_navigation_theory_v1/README.md)。

## 最近研究与当前依赖

| 记录 | 主题 | 状态与一句话判断 | 详细复盘 |
| --- | --- | --- | --- |
| E202 | 四多模态共享表示与补点净收益选块 | 544点/1088批完成；新168/168点被强控制覆盖，S32主配置24点全慢于旧QR3；默认保持 | [详细记录](experiment_history/202_shared_residual_value_v1.md) |
| E201 | 查询/主返回条件的在线小叶块树残差首版 | 两集172点/344两遍T1完成；新QR3费用接近B32而救回更少；默认不变，保留条件取舍 | [详细记录](experiment_history/201_query_conditioned_residual_v1.md) |
| E200 | 四多模态NSG/GT10/直接残差/GATE加密重测 | 完成640点/1280两遍T1；COCO/WebVid残差有效，Flickr条件性，Yandex优先GT10；默认保持 | [详细记录](experiment_history/200_multimodal_four_method_retest_v1.md) |
| E199 | 四多模态集STATIC/PRE/POST门、F/N语义与精排分段 | 完成736/2208；主门79/80被覆盖；当前复杂分支停止扩展，另交付5页图解 | [原卡片](experiment_history/199_gate_timing_cost_v1.md) · [收敛记录](experiment_history/_maintenance/20261104_residual_pruning_graphs_v2/README.md) |
| E198 | 状态匹配监督、双塔短名单、前置门与0/96/384动作 | 完成1480/4440；112/112新学习窗口点被强控制覆盖，默认保持 | [卡片](experiment_history/198_conditional_residual_policy_v1.md) |
| E197 | 候选支持、可预测性、执行路径/时机 | 完成9434/28302；336学习窗口被强控制覆盖，默认保持 | [卡片](experiment_history/197_residual_bottleneck_separation_v1.md) |
| E196 | 费用邻近GT10/OPT-B32强控制 | 完成837点/2511T1；51固定配置成本复核，默认保持 | [卡片](experiment_history/196_residual_navigation_cost_controls_v1.md) |
| E195 | 七集残差来源、搜索轨迹与导航增量 | 完成1260点/3780T1；分数据/预算保留实际效应，默认不变 | [卡片](experiment_history/195_residual_navigation_diagnosis_v1.md) |
| E194 | 残差后端等价省费与查询稳定性 | 完成256点/768T1；2/28配置两窗通过，返回等价，默认不变 | [卡片](experiment_history/194_residual_optimization_stability_v1.md) |
| E193 | 自适应残差开关最小验证 | 完成102点/306T1；收益集中与理想/学习费用分开验证，默认不变 | [卡片](experiment_history/193_adaptive_completion_gate_v1.md) |
| E192 | 共享必要条件、支持上界与重配对照 | 三集39点/117T1＋七集32重配诊断完成；支持集必要条件成立，目标ID共享并非所有块法必要条件，默认不变 | [卡片](experiment_history/192_sharing_necessity_v1.md) |
| E191 | 七集两K来源与评分综合测试 | 原448点/1344T1＋密集541点；保留探索筛选12点，默认不变，交付PDF | [卡片](experiment_history/191_seven_dataset_scoring_v1.md) |
| E190 | 固定候选SQ8评分与完整费用 | 38点/114T1；原网格3个新评分点：2个被GT10覆盖，速度筛选1点通过。 密集GT10补充：唯一阳性L400点速度门0、预算Recall门0。默认不变 | [卡片](experiment_history/190_coco_fixed_candidate_scoring_v1.md) |
| E189 | 入口/主返回提出稀疏区域与块 | 正式70点/210T1；新18点中18点被GT10覆盖，默认不变 | [卡片](experiment_history/189_reuse_completion_routing_v1.md) |
| E188 | 补全分段费用、等价省费与硬访问预算 | 正式100点/300T1；硬预算24/24点被GT10覆盖，默认不变；保留校准角色修正 | [卡片](experiment_history/188_completion_cost_budget_v1.md) |
| E187 | 全base区域残差补全pilot | 52点/156完整T1（原46+6控制）；18/18区域点被实测GT10覆盖，默认不变 | [卡片](experiment_history/187_adaptive_completion_pilot_v1.md) |
| E186 | 按遗漏特征适配补全来源/预算的设计 | THEORY_ONLY_UNIMPLEMENTED_UNTESTED；先验证全base区域候选，再做动作选择，无新性能 | [卡片](experiment_history/186_adaptive_completion_design_v1.md) |
| E185 | 流形相关局部几何与遗漏共享 | 3584固定样本/56K分层；支持局部连续性关联，无简单低维规律或净收益准入器 | [卡片](experiment_history/185_manifold_residual_probe_v1.md) |
| E184 | 空间分布与失败修复 | 离线诊断完成；七集56K，无新性能，默认不变 | [卡片](experiment_history/184_residual_geometry_diagnosis_v1.md) · [低于10%全L修正版PDF](reports/20261024_failure_rescue_residual_lt10_v2/ACSG_低于10%召回的查询比例_全L修正版_20261024.pdf) |
| E183 | 七集GT10与残差综合评测 | 645点/1935完整T1；七集两K综合证据，默认不变 | [卡片](experiment_history/183_gt10_residual_comprehensive_v1.md) |
| E182 | 同源规模与容量密度 | 216点单轮；固定H小库优势在密度控制后不再单调 | [卡片](experiment_history/182_m5_scale_control_v1.md) |
| E181 | COCO/Flickr独立迁移 | 120点单轮；COCO受益、Flickr K100交叉 | [卡片](experiment_history/181_m5_multimodal_transfer_v1.md) |
| E180 | K100来源与嵌套扩容 | 扩容有质量收益；曲线解释以E181修正及E183新矩阵为准 | [卡片](experiment_history/180_m5_k100_capacity_v1.md) |
| E179 | 同16K目标对齐 | 小幅Recall收益，没有稳定QPS增益 | [卡片](experiment_history/179_m5_k100_objective_v1.md) |
| E178 | 画像路由风险 | 局部小L选择失配；范数匹配影响有限，未替换默认 | [卡片](experiment_history/178_profile_routing_risk.md) |
| E177 | 真实入口/代表query表示 | 有限测试无可靠默认替换依据 | [卡片](experiment_history/177_entry_representation_quick.md) |
| E176 | M5工程省费与剩余遗漏补全 | 对M5OPT无严格双升；速度和残差质量贡献分开 | [卡片](experiment_history/176_m5_residual_completion_curve_v1.md) |
| E175 | 区域补全五L曲线 | Recall多升但同L全慢，未新增双升预算组合 | [卡片](experiment_history/175_m5_region_budget_curve_v1.md) |
| E174 | 一跳区域补全 | 独立版本完成；不把邻域几何机会当净收益 | [卡片](experiment_history/174_m5_residual_regions.md) |
| E173 | 原M5公开测试 | 历史60点/180批已完成；不是当前正在执行 | [卡片](experiment_history/173_nsg_gt_m5_public_test_retest.md) |
| E172 | 五方法及三联动旧阶段 | 保留未完成范围和来源/成本记录，不作为当前恢复队列 | [卡片](experiment_history/172_all_methods_experiment_campaign.md) |
| E171 | 五机制理论与DOCX联动 | 理论阶段已完成；不把提案当已实现或新性能 | [卡片](experiment_history/171_overnight_algorithm_collision_and_certificates.md) |
| E99 | 共享NSG实现优化 | 保留当前共享核优化；旧绝对QPS不能拼入E183 | [卡片](experiment_history/92_nsg_search_optimization.md) |

## 完整历史与理论

[全部详细卡片](experiment_history/README.md)按文件原编号索引；早期卡片编号和正文实验E编号不一定相同，不按文件名前缀擅自重编号。

旧的多视角/注意力、probe-reroute、A+B、RL、多画像、有限beam及证书路线均保留其原协议、失败、修正和证据。理论文稿、SOURCE_ONLY、工具准备/验收与正式实验不是同一状态。

[范数敏感画像路由理论](entry_method_exploration/20261011_norm_aware_profile_theory_v1/theory.md)仍为THEORY_ONLY_UNIMPLEMENTED_UNTESTED；不能因有文档或源码审查就称性能通过。

查旧方法时从卡片进入协议、配置、state/gate、结果和修正，证据不足写未知。旧进程状态、期限和恢复命令已从当前入口移出，完整旧索引[归档](experiment_history/_maintenance/20261024_current_state_cleanup_v1/archive/s-experiment.md)供复核。
