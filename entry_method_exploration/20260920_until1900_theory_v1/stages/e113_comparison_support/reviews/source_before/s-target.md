# ACSG 当前任务与后续边界

2026-09-20用户已将活动目标改为持续推进到北京时间19:00。E107–E111及首阶段理论综合完成并封存，后继见[19:00版本](entry_method_exploration/20260920_until1900_theory_v1/state.json)与[资源/截止合同](entry_method_exploration/20260920_until1900_theory_v1/config.locked.json)。E112首行覆盖H信息门已完成并停止：Web通过、Y开发覆盖与失败恢复不足，0新搜索/画像训练。目标支持审查与4次query分支反例已完成；后继先审查实际搜索比较边界是否能跨不同目标重复提供信息，尚无新模型或运行队列；不扩本版H/跳数/seed或转选单集训练。新增真实NSG上限1,200,000，两阶段合计不超过原4M；18:50禁止新搜索，19:00交付。原停止候选与默认保持。

后继研究优先回答：固定大图和真实raw-IP有限预算下，什么不依赖在线GT的信息，能预测可索引入口的净搜索收益，并保留基线质量及完整wall？先给可检验的图/查询/预算条件、反例与跨数据覆盖，再判断同监督的简单模型和MLP/双塔/RL。E109两个区域代理、E110首展开候选、E111当前m64/100证书及E112首行H设计均按门停止，不降低门槛、不扩m/路径/seed/ef或转选单个数据集继续。E106及旧WFree/QMLP版本也不重启。[理论证据与边界](entry_method_exploration/20260920_until1600_theory_v1/research/learning_objective_and_search_contract.md) · [前作条件](entry_method_exploration/20260920_until1600_theory_v1/research/literature_scope.md)。后文为历史接续，当前状态以这两段为准。

2026-09-20用户活动目标“按解释机制 → 推导改进 → 实验检验 走吧”的第一轮闭环已由独立E106完成。精确B/D分解、严格匹配支持置换与唯一GroupMean候选均经真实K1/K100检验；结果为STOP_GROUPMEAN_CANDIDATE，两集质量门失败，不进入其条件实际ANN/独立完整wall阶段，不追加alpha/seed/组数或切换Web主族。无待运行任务，原默认保持。它完成了一轮可证伪研究，并未找到稳定改进或解释GT10全部收益。[报告](entry_method_exploration/20260920_gt10_conditional_mechanism_v1/report.md) · [记录101](experiment_history/101_gt10_conditional_mechanism.md)。

后续理论优先回答：要解释的是GT10相对NSG的系统收益，还是相对GT1的多目标增量，以及哪段预算下的Recall或wall收益。E106在L128发现后一Recall增量混合；匹配支持置换的区间全跨0，不能写成细节无用。新方法必须给出相关性代理到三入口联合搜索轨迹的条件与反例，解释它如何改变有效动作且避免跨query增损抵消，并区别于已失败的E104真实效用监督/E105 WFree。当前不指定新网络或调参队列；旧文档中的历史计划以本页首段为当前状态。

2026-09-20当前优先级由用户明确调整为**理论与机制先行**。[第一轮理论复盘](entry_method_exploration/20260920_gt10_theory_review_v1/report.md)已完成：厘清GT10闭式目标及其相对GT1/NSG的不同增量，给出平滑反例、保序条件和区域覆盖到联合搜索效用的误差定义；这些基础推导不等于搜索最优/泛化证明。接续先解决三个问题：真实多目标对应与一般平滑如何被独立识别；什么图/查询/预算条件让目标区域相关性代表可搜索性；相应信息能否在实际部署动作族上迁移并保留原GT10收益。以E27已有机制证据和E20/E40/E50/E60/E104/E105已知缺口为起点，不重复已经完成的诊断，不先指定网络或超参。

进入新方法实验前，研究需产出明确假设、成立条件与反例、相对既有工作的实质区别、同监督简单基线，以及能区分竞争解释的最小证伪设计。当前仅理论研究，无待运行训练/标签/ANN/GT/构图/QPS；原默认保持。旧K10证据只作历史机制材料，新性能仍真实K1/K100/单线程完整wall；E105查询现已曝光。详见[研究记录100](experiment_history/100_gt10_theory_review.md)。以下是已完成实验及更早阶段的历史接续，新的优先级以本段为准。

2026-09-20 用户“试试”授权的 **E105已完成并停止于STOP_WFREE_REPLICATION**。各4096新源行query、独立GT100、真实K1/K100完整128点/384轮已评分核验；两集L128质量门及完整wall门均失败。WFree原512条cal正值未复现为稳定收益，7个共同可达门槛平均QPS全负。停止本版WFree投入及追加seed、epochs、归一化、预算网格或失败query子集，不恢复本runner；原模型/图/完整负点保留，Web soft/Yandex hard及生产E99保持，当前无待运行任务。[完整报告](entry_method_exploration/20260920_wfree_frozen_replication_v1/report.md) · [复盘99](experiment_history/99_wfree_frozen_replication.md) · [状态](entry_method_exploration/20260920_wfree_frozen_replication_v1/state.json)。

当前方法研究边界：E104查询MLP及E105静态WFree均已完成各自冻结验证，本轮不产生后续训练/评测队列。若继续面向CCF B的方法研究，先提出实质不同的假设，解释真实三入口联合效用监督为何能跨query保留净收益；不能仅换网络/优化器名称或扩大调参。E105的8192条query现已用于复验，不得再标作未曝光测试。新的研究设计须明确简单对照、全流程成本、数据角色与停止门；本次结果不否定全部离线学习/MLP/RL，也不保证论文创新或录用。

E104历史接续：用户“验证吧”授权的查询表示pilot已停止于表示门，QMLP在cal的K1/K100未超过GT10，精确路由也失败，未进入其条件160配置/480plain；事后C8限定诊断未恢复明显收益。辅助WFree随后由独立E105完成复验，不回改E104的0新QPS历史事实。[E104报告](entry_method_exploration/20260920_query_representation_pilot_v1/report.md)。以下“尚未实现/下一步”为更早阶段的历史状态，均由本页首段接续。

2026-09-20 当前接续：用户确认 CCF B 类会议目标，并同意先推进方法研究。本轮[源码/文献与表示研究](entry_method_exploration/20260920_query_representation_research_v1/report.md)及16个历史训练样本的几何检查已完成；推荐验证一次查询侧非线性残差，保持真实入口、画像、小图及底层 NSG 固定，与同监督的 query 线性残差/静态 W 比较。查询网络本身尚非论文创新或已验证改进。

下一步按[最小证伪协议](entry_method_exploration/20260920_query_representation_research_v1/protocol.md)落实独立输入身份和 K1/K100 真实联合效用余量，再决定是否进入最多两集六次训练；只在迁移门通过后做完整单线程 wall。协议明确了开发数据的历史曝光、入口顺序、全部预算、简单对照、成本和停止标准。当前训练/C++路由/评测 runner 尚未实现，pilot 未启动；不把研究阶段的几何 witness 写成性能通过，不恢复旧 E95 runner，也不修改当前默认。独立测试来源是扩大论文证据前必须解决的问题。以下为已完成阶段及其历史边界，新的方法研究优先级以本段为准。

2026-09-17 用户明确研究定位为**面向 OOD 的入口点选择，底层大图固定**。[方法与实验总结](研究方向.md)及[7页PDF](GT10研究总结.pdf)已按用户要求重排：当前方法之后直接放 E103 四张重测图，再汇总尚未稳定超越 GT10 的改进实验、NSG 实现优化，最后说明公共提速和 GT10 入口收益仍在。本轮仅文档与既有结果整理。

E103用户授权的完整五集优化重测、分析和图表检查均已完成，没有待运行的E103测试。可达的25个90/95/99%门槛组合中，GT10-hard/soft家族平均QPS最快22个；不是单一模型胜率或显著性结论。WebVid/Yandex收益较清楚，Deep/SIFT较小到中等，GIST相对NSG基本持平或落后。 当前结果支持继续整理GT10的适用范围和论文证据，不支持宣称全部数据集全面支配NSG。没有自动授权额外训练、扩预算、换默认或部署；生产仍E99，Web soft/Yandex hard保持。[报告与新图](entry_method_exploration/20260916_optimized_five_dataset_r1_r100_v1/report.md) · [复盘96](experiment_history/96_optimized_five_dataset_retest.md)。

E102用户要求的统一优化测试已完成。E102于2026-09-16完成统一优化公平比较：NSG、GT10-hard/soft、GATE均使用相同span+batch4，WebVid四预算各新旧内核及同轮HNSW共36配置108plain。NSG自身四点平均QPS变化+18.58%至+27.28%；K100/L1250从252.11变为320.90QPS，Recall@100保持90.4456%。同内核soft为324.95QPS/90.6868%，GATE为319.69QPS/90.6317%；HNSW为271.54QPS/90.3718%。 同内核低预算K1/L96和K100/L100，GT10-soft相对NSG分别增加4.73/1.64pp Recall与11.68%/11.28%平均QPS；高预算速度差缩小，结合三轮范围判断，不支持“GT10无效”或“全面第一”。 下一步若扩大结论，应以相同优化后的NSG作为入口方法基线；公共内核提速不能计为GT10独有优势。当前交付限Web四固定预算、其它四集一致性，无自动追加全网格、重训或生产部署；默认仍Web软/Y硬。若后续合入主API，保留trace、特殊值/未知DC回退与图生命周期。[报告与图](entry_method_exploration/20260916_shared_span_batch4_v1/report.md) · [复盘95](experiment_history/95_shared_span_batch4_comparison.md)。

E101比较任务已完成，E101于2026-09-16完成内置Faiss1.9.0同图比较：WebVid四点、十版本、120轮plain/2000000search；GT10的span+batch4组合相对当前E99四点QPS变化+13.10%至+26.56%，各GT10控制返回和NDC相同。高预算K100/L1250组合341.45QPS、Recall@100 90.6868%，当前GT10 269.80QPS；原生Faiss 230.52QPS/90.4819%。另做80000次真实batch4计数核验及496000次四集一致性回归，其它四集64配置的输出ID/距离bits/入口/逐query NDC全部与E99一致。 下一步优先按本轮收益与跨集兼容性选择小范围共享内核落地；span和batch4应分别保留控制，不能直接用库替换推断加速。预取过滤、纯代码精简的价值按报告实测范围判断，不追加网格追逐小差异。原生Faiss初始化不同，单独命名；后继生产接入需补API/trace、特殊值/未知DC、生命周期和全部共享方法公平性能验收。当前生产仍E99，无自动部署、训练或下一轮查询队列。[报告与图](entry_method_exploration/20260916_faiss_nsg_comparison_v1/report.md) · [复盘94](experiment_history/94_faiss_nsg_comparison.md)。

E100“还能优化及NDC少但速度慢”的研究已完成，[报告](entry_method_exploration/20260916_residual_cost_research_v1/report.md)给出80000次诊断、一致性核验、结构计数和两张图。当前无待恢复查询；生产实现仍E99。下一步优先补同图原生Faiss NSG对照，并区分其填满初始L的语义与项目最多三入口；再研究保序跳过尾部空槽、预取组织/batch4，最后考虑大幅候选结构/布局修改。原生库也有固定容量遍历，换库不保证自动更快。新方案先独立版本锁定预算与计时边界；无语义改动先通过逐位输出、入口、NDC/距离顺序与边界回归，再按原用户范围重点验证WebVid Recall@1/100、其余四集一致性，所有共享NSG方法公平更新。原生库语义不同，单独命名并以Recall–QPS评估，不以逐位相等为其准入要求。不因本轮诊断自动启动五集完整网格或模型重训；E100没有新的加速结论，E99局部收益保留。

E99于2026-09-16完成共享NSG实现优化：WebVid四个预算、四种NSG入口方法的新旧对照，QPS变化+10.51%至+13.53%；五集100个组合的返回ID/距离bits/入口和逐query NDC均与E97一致。 用户授权的WebVid重点验证、其他四集一致性、绘图分析和修改前Git备份均已完成。[报告](entry_method_exploration/20260916_nsg_search_optimization_v1/report.md) · [Recall–QPS图](entry_method_exploration/20260916_nsg_search_optimization_v1/figures/webvid_recall_qps.png) · [复盘92](experiment_history/92_nsg_search_optimization.md)。 本轮仅四个预锁预算，不能代替优化后完整前沿或跨五集吞吐结论；不追加网格、LAION、Recall@10或重训。生产源和可独立链接的优化库已交付，原构建库可继续对照。当前E99无待恢复的查询任务，默认仍Web软/Y硬。

E98性能归因任务已完成：[报告](entry_method_exploration/20260916_search_cost_diagnosis_v1/report.md)。优先级转为共享NSG内核的预取与候选维护工程验证；路由仅0.47%，不以本次速度差距为由重训GT10。组合控制在WebVid K100/L1250局部提升13.15%，尚未部署或验证完整前沿；候选池单项约0.95%在波动范围内。若接续正式落地，先补等距/边界一致性回归，再按原单线程Recall@1/100协议公平重测全部受影响的NSG/GT10/GATE。当前没有待恢复的训练/评测进程，旧默认和E97封存不变。

E97授权工作已完成：五集修复、GATE重训、Recall@1/100重测、绘图和[逐集分析](entry_method_exploration/20260915_gate_l2_r1_r100_v1/analysis.md)。保留hard为预先指定研究主线、固定soft作辅助；不根据这轮公开测试自动更换Web软/Y硬默认或按预算拼赢家。没有待补的LAION、Recall@10、新网格或后续训练。下一步先根据用户提出的新问题确定独立验证范围；当前结果不能支持“GATE全面无效”“hard全面最优”或“完整HNSW全面支配”。

E97执行前的审查任务（历史）是先审查GATE，再告知Deep/SIFT/GIST方法选择；接受核心机制正确的合理复现，不要求照搬作者代码缺陷。[审查已完成](entry_method_exploration/20260915_gate_reproduction_audit_v1/report.md)，当时新三集未启动。下一轮主方法建议GT10-hard，soft-t1只作一份预锁辅助；旧Web软/Y硬默认不回改。

审查提出的接续条件（现由E97按锁定协议落实）：在独立版本从GATE负例排除正例，过滤后断言互斥；明确独立QGT/fit/monitor/cal/test来源；核对SIFT实际11164866行的base与GT身份；准备原L2度量的兼容图和K1/K100评测入口。已有hop缓存仅在完整身份兼容时复用，不覆盖E96模型/结果。保留batch-first、CPU与统一kernel适配，并披露1000节点子图截断；不为追论文数值扩大超参网格。

从本次指令起，新开发选择和正式比较只测 **Recall@1、Recall@100**，K1/K100分别真实搜索并计完整端到端QPS；K100的L/ef至少100，不再测Recall@10。GT10训练目标数仍为10。新数据/模型/预算/选型规则在正式测试前冻结，仍同机单线程串行；不能按正式结果选hard/soft或按L拼赢家。当时的“先检查告知”不产生后台训练/测试队列；后续用户已明确授权本页首段的E97执行与后台运行。

2026-09-15 E96用户任务已完成：三集完整四方法192点/576轮、Recall–QPS与失败率图、原始CSV、成本、报告和身份/单线程/逐query验收均已交付；不需要继续当前runner或追加网格。Web/Y GT10优于本轮GATE适配，LAION高预算保留质量与速度取舍；默认保持，后续工作以新的用户目标为准。[结果报告](entry_method_exploration/20260914_gate_new_ood_v1/report.md) · [完成记录](entry_method_exploration/20260914_gate_new_ood_v1/complete.json)。以下为E95已结束增强分支的历史停止范围。

2026-09-14，状态：**STOP_CURRENT_FIXED_H_PROFILE_GRAPH_BRANCH**。用户要求持续推进到“有更好的方法，或停止当前分支”。本轮已完成方法比较和E95实际验证；没有得到可替换GT10的新方法，现停止当前分支。默认保持Web GT10-soft-t1 / Yandex GT10-hard。[停止决定](entry_method_exploration/20260914_query_moment_graph_v1/decision.md) · [完整证据](entry_method_exploration/20260914_query_moment_graph_v1/report.md) · [复盘87](experiment_history/87_query_moment_graph_and_branch_stop.md)。

## E95历史停止范围

结束当前固定H815/821、围绕GT10的参数扰动型RL、多画像/目标分组、补边、父画像恢复和组合局部修补，以及E95 full/diag查询统计构图。没有待执行的训练、ANN、构图、QPS、依赖安装或后台会话；不恢复9月13日旧runner，不追加尺度、seed、步长、簇数、ef或训练预算来延续本分支。

E95使用原P评分恒定、查询统计仅作用离线构图，已经实际检验一个不同于局部扰动的闭式方案。两集各7952 query、两L、两半的四个候选–数据集组合全部未过冻结开发门；条件wall未启动。原E50/E52/E53/E56/E60/E89/E90诊断/对照和E94完整性能结论也已完成，不能重新列为待做首步。

此停止是当前分支的投入决策，不证明全部离线画像学习、图构造或RL无解，不终止整个ACSG。原GT10、Web局部正信号与所有负点分开保留。

## E95历史后继研究约束

当前没有必须补跑的研究产物或实验。若以后出现实质不同的研究问题，可另立新分支；先说明新的表示/动作、真实三入口联合收益、原GT10收益保留及可迁移依据。仅换优化器名称、超参数或对已有compact退化作修复，不满足重新立项的依据。不得把一般图非加性当作多步RL必然有效的证明。

新分支须在执行前冻结数据角色、预算、完整线上流程、简单对照、接受/停止条件和版本身份。相同候选/反馈数不等于相同训练wall，几何排名或未知三元组不等于已测联合效用。新方案改变base/metric/图/kernel/输入时依spec重建受影响产物。

## 数据、性能与封存

P-fit含历史train/monitor；aux/cal/audit反复使用，接受反馈计开发/训练信息。E94历史validation有既往暴露；不能按其最终坏例选动作/子集或调参。E95未打开E94最终载荷用于新实验，held-out保持未开。不得把旧开发集改名为新盲集。

如未来新分支进入性能阶段，继续同机单线程、数值库单线程、方法串行，以完整线上wall比较Recall–QPS和零命中失败；保留对应新协议的全部预算点和每轮计时，单L、NDC、插值或monitor均不构成性能GO。时间重复和跨L不增加独立query数。

原模型、NSG/base/GT、全部raw/日志/计时/选择/封存保持。9月13日限时任务早已结束；其历史state和交接不要求恢复。当前根文档可继续演进，旧snapshot/seal不改。旧下一阶段计划已保存在[E95 source_before](entry_method_exploration/20260914_query_moment_graph_v1/source_before/s-target.md)；本轮[方法比较](entry_method_exploration/20260914_query_moment_graph_v1/research.md)、[冻结最小实验](entry_method_exploration/20260914_query_moment_graph_v1/protocol.md)、[结果](entry_method_exploration/20260914_query_moment_graph_v1/report.md)及[完成核验](entry_method_exploration/20260914_query_moment_graph_v1/reviews/completion_audit.json)已经接续该计划。
