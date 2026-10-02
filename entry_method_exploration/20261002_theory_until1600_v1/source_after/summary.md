# ACSG 当前结果摘要

当前项目目标为**可靠的 Recall–QPS 综合改进**，具体判定见[s-target.md](s-target.md)。截至性能记录166尚未达成；构建费用与代理指标改善不能替代完整线上收益。默认不变。

2026-10-02下午新指令：“再研究到下午四点，先完善理论，不开始实验”。[168独立纯理论阶段](experiment_history/168_theory_proxy_information_local_certificate.md)已按16:00（Asia/Shanghai，UTC+8）截止收口，COMPLETED_THEORY_ONLY_NO_EXPERIMENTS；只做手推证明/反例、原论文与静态源码/封存结论审阅。已交叉手审GT10代理的失配及正面条件、实际多入口/目标rank、局部返回保护/容量前缀、完整原评分组证书、策略校准/迁移及收费决策。[报告](entry_method_exploration/20261002_theory_until1600_v1/report.md)与[命题台账](entry_method_exploration/20261002_theory_until1600_v1/proof_ledger.md)区分解析结论与真实未知前件；线上可得性/数值界/覆盖率/净费用仍HOLD。0真实/合成实验、枚举及旧数组新诊断，上午167原件保持封存，没有新性能或默认替换。

用户随后明确：“不需要节省训练时间甚至可以增加训练时间，但是综合qps recall要提高”。训练/离线准备可以增加投入；以真实Recall与计全部新增费用的完整在线QPS评价，默认须共享相同优化机会。本轮继续理论，不开始训练或预处理。

2026-10-02用户授权先探索理论与方法，并阅读相关论文，至今天13:00（UTC+8）。本次[独立研究协议](entry_method_exploration/20261002_theory_until1300_v1/protocol.md)已冻结：研究历史/原论文、条件理论与反例，以及仅用旧ID/slot/已存响应的桶访问可行性诊断；不读取新query向量，不启动真实ANN/NSG、GT、训练、构图或正式性能。本轮理论研究已于13:00结束并封存，性能实验保持暂停，最新实测仍为166。

[167研究结论](experiment_history/167_theory_search_response_access_cost.md)已补有限pool发现/安全前沿/合法返回类与native区间条件，核对直接前作；只读三桶物理M均值Web107.330/Y86.837，旧TargetBank slot仅覆盖33.765%/45.728%，Web主R1旧50次救回40次桶外。已补读20篇原论文相关章节，包括已在E96/E97/E103适配的GATE和需改变图/搜索合同的PSP/MAG。该覆盖不是新Recall/QPS；粗筛不能继承旧局部收益。优先保留原路由距离memo的成本隔离问题，但须与原版/UpperHandoff/同memo默认中更快版本比较，旧Web主R1完整wall缺口约23.282μs/query。memo、原阈值拒绝、三桶及新联合动作均HOLD、未实现/运行；[主报告](entry_method_exploration/20261002_theory_until1300_v1/report.md)与[具体后继门](entry_method_exploration/20261002_theory_until1300_v1/candidate_gates.md)分开于真实性能。

2026-09-30 19:44按用户“先停下来”暂停该日作业；原22:00推进安排已暂停。已完成至记录166并封存。目标桶粗筛仅保留设计，未实现或运行，默认不变。

[166冻结目标库曲线](experiment_history/166_target_bank_frozen_curve.md)已完成36点/108轮完整wall与独立核验。**冻结目标库保留WebVid R1的质量/速度取舍，尚无已测点的稳定Recall–QPS综合改善；结束本次有限曲线核验，不扩网格、ef、样本或重复。默认保持Web GT10-soft-t1、Yandex GT10-hard与生产E99。**

下表为166共享span+batch4研究核的默认入口策略/TargetBank实测；原E99输出回归通过，绝对QPS不作为生产E99现场计时，生产未切核。

| 组合 | 各自最快实测R90的L | 默认实际Recall / QPS | TargetBank实际Recall / QPS |
|---|---:|---:|---:|
| WebVid R1 | 1000 | 90.454102% / 417.190 | 90.991211% / 413.177 |
| WebVid R100 | 1250 | 90.581543% / 334.895 | 90.576416% / 333.291 |
| Yandex R1 | 128 | 90.625000% / 2364.615 | 90.625000% / 2283.658 |
| Yandex R100 | 256 | 91.044434% / 1289.884 | 90.885010% / 1264.985 |

Web R1三个预算的质量差+0.659180/+0.537109/+0.390625pp，QPS−1.8363/−0.9620/−1.0204%；保留局部取舍。12个同预算点目标库均更慢，72个跨预算比较无经验支配，未实测同Recall更快。历史4096开发query/稀疏网格，不外推全预算或独立确认。全部147456返回及统计复算通过。

[165查询→真实目标迁移](experiment_history/165_query_target_transfer_online.md)已完成独立核验。**直接查询→GT1迁移未形成相对默认的稳定Recall–QPS综合提高，停止本固定迁移版本；保留目标侧简单对照的Web R1质量/速度取舍。默认仍为Web GT10-soft-t1、Yandex GT10-hard与生产E99。**

| 工作点 | Default3 Recall / QPS | QueryTarget1 Recall / QPS | ΔRecall pp及95%描述区间 | ΔQPS |
|---|---:|---:|---|---:|
| WebVid R1/L1000 | 90.454102% / 423.710 | 90.551758% / 416.559 | +0.097656 [-0.292969, +0.488281] | -1.6878% |
| WebVid R100/L1250 | 90.581543% / 335.485 | 90.591064% / 332.523 | +0.009521 [-0.063477, +0.083252] | -0.8828% |
| Yandex R1/L128 | 90.625000% / 2386.805 | 90.112305% / 2260.786 | -0.512695 [-1.098633, +0.097656] | -5.2799% |
| Yandex R100/L256 | 91.044434% / 1329.735 | 90.688232% / 1276.806 | -0.356201 [-0.634033, -0.082269] | -3.9804% |

目标侧简单控制在Web R1为90.991211%/420.254 QPS，相对默认+0.537109pp [0.122070,0.952148]、QPS−0.8156%，保留局部质量/速度取舍；未证明同Recall更快或跨集稳定。Web查询配对相对打乱有局部信息，仍不足以超过默认与简单控制。全98304返回/映射/四图/原生/统计核验通过，停止本版扩实例/ef/近邻/GT数/模型。

[164状态/rank完整在线验证](experiment_history/164_router_rank_pareto_online.md)已核验。**本固定状态/rank版本没有形成稳定的Recall–QPS综合改善，停止继续调状态、trace、支持阈值、深度、L、样本或seed。默认仍为Web GT10-soft-t1、Yandex GT10-hard与生产E99。**

| 数据集/工作点 | Default Recall / QPS | StatePareto Recall / QPS | ΔRecall pp及95%描述区间 | ΔQPS |
|---|---:|---:|---|---:|
| WebVid R1/L1000 | 90.722656% / 419.773 | 90.600586% / 418.127 | -0.122070 [-0.292969, +0.024414] | -0.3922% |
| WebVid R100/L1250 | 90.679443% / 339.305 | 90.649902% / 340.938 | -0.029541 [-0.067139, -0.006836] | +0.4812% |
| Yandex R1/L128 | 91.577148% / 2391.821 | 91.455078% / 2373.680 | -0.122070 [-0.415039, +0.170898] | -0.7585% |
| Yandex R100/L256 | 91.399658% / 1314.626 | 91.302002% / 1322.325 | -0.097656 [-0.197272, -0.016846] | +0.5856% |

两K1区间跨零、两K100区间负；K100轻微提速伴随召回下降，未证明相同Recall更快。State四点召回均未超过置换控制。完整在线/原生/64规则与全部统计复算通过；历史开发数据和OOF模型切换不冒充独立确认。

用户于2026-09-30 17:44明确：**主目标是完整端到端Recall–QPS综合提高，构建费用不是优化重点。** 下列构建费用收益只保留为附属事实，不视为主要目标完成。尚未执行的目标质量压缩诊断已取消；接下来回到廉价入口信息与真实线上效用，见[目标修订](entry_method_exploration/20260930_theory_until2200_v1/online_priority_steering.md)。

2026-09-30原定理论研究至22:00，现已按用户指令暂停。**默认保持Web GT10-soft-t1／Yandex GT10-hard、生产E99；Energy选样未获得稳定新源召回改善，停止本版调参，低标签成本候选继续保留。** [157四模型两批新源验证](experiment_history/157_energy_selection_two_source_batches.md)已全部核验，每集8192 query、真实K1/K100、CPU15实际单线程：

| 数据集／点 | 默认Recall／QPS | Energy Recall／QPS | ΔRecall (pp)及描述95%区间 |
|---|---|---|---|
| WebVid R1/L1000 | 91.198730%／412.839 | 91.088867%／413.549 | -0.109863 [-0.219727, -0.012207] |
| WebVid R100/L1250 | 90.605103%／334.329 | 90.578979%／334.938 | -0.026123 [-0.039185, -0.014526] |
| Yandex R1/L128 | 91.516113%／2335.782 | 91.467285%／2339.041 | -0.048828 [-0.195312, +0.097656] |
| Yandex R100/L256 | 91.037231%／1306.000 | 91.034058%／1303.324 | -0.003174 [-0.088989, +0.080203] |

[160共享三方完整构建](experiment_history/160_shared_batch_full_build_identity.md)已审计：Web Default／Uniform／Energy为332.954／119.980／130.046秒，完整身份都恢复；Yandex为602.533／149.230／163.878秒，但新Default因1条近并列目标跨hub变化，W两行及图改变，不能沿用旧质量。两份Y候选身份恢复；本轮0新线上性能。原默认不变，费用与身份不合并判定。

[163误差条件链](experiment_history/163_soft_mass_transport_pipeline_conditions.md)已补齐目标/温度、平均归属、归一化、评分间隔、实际入口到固定搜索的保真条件，并通过独立合成核验；不能推出召回提升或费用保证，0新真实数据/模型。

[162单球/单hub证书](experiment_history/162_single_hub_geometric_certificate_opportunity.md)在两集各20K训练query均0通过，exact阈值也远低于上界；全量独立核验通过，停止这份过松的固定球界，不调参续跑。0新搜索/模型，默认不变。

[161完整hard质量条件](experiment_history/161_hard_mass_interval_certificate.md)的固定枚举与独立子集核验通过：ID不定仍可计数固定，多数类别稳定则不足够。这只是数学条件，真实界/成本未证；没有新模型或搜索。

[159共享精确标签检查](experiment_history/159_exact_label_batch_and_rank_dispatch.md)已核验：batch1024/k100对原batch256/k100的Web/Y费用比0.9796/0.3489，消费前10有序ID改变0/0条；主费用门通过。这是各1024条的离线微测，旧完整费用不外推替换，完整模型身份仍需验证。

[158只读连接诊断](experiment_history/158_energy_profile_routing_search_bridge.md)进一步确认：Energy对默认分数的平方差较Uniform低13.3%／28.0%，但648／772条换入口只改变11／24条R1返回。几何改善在新query上存在，仍非Recall保证；观察性分组不归因于拓扑。另澄清[145旧R100计数](entry_method_exploration/20260930_theory_until2200_v1/research/routing_member_count_clarification_v1/report.md)为每query净差累计，真成员增损已补表，旧净Recall不变。

Energy相对同2048预算Uniform的ΔR1/R100为Web+0.012207/−0.001343pp、Y−0.061035/+0.003784pp，四区间均跨0；Web R1净+1／Y净−5，R100都跨批异号。Web相对Default两点两批均负，质量损失保留；Y仍有较大不确定性。相对Shuffled也未形成稳定信息优势，一个打乱模型不是随机化检验。完整QPS、全部轮次、两批与全部6方法对均保留，不自动称非劣／线上更快或切默认。

[156固定r0完整构建](experiment_history/156_energy_selection_actual_full_build.md)Energy131.133／259.137秒，对[154同享按需QGT的默认](experiment_history/154_fair_default_demand_build_cost.md)336.051／1519.754秒，单次少60.98%／82.95%；包含教师、选择、两次载入和补标，未清缓存、非随机重复。[148原均匀混合](experiment_history/148_demand_qgt_full_build_cost.md)114.023／243.072秒及[151原主混合新源质量](experiment_history/151_frozen_hybrid_two_source_batches.md)保留各自身份，不把不同Web温度候选的费用拼接。共享批处理微测已完成，原完整构建费用仍保持实测身份。

[155训练信息门](experiment_history/155_energy_selection_without_exact_temperature.md)的方向误差均值少6.811%／23.330%仍成立，但没有保证检索收益；复杂LOO原153失败不回改。四模型分数到搜索的只读分解已完成，不按曝光query继续补标。[145二阶矩用语澄清](entry_method_exploration/20260930_theory_until2200_v1/research/routing_bridge_clarification_v1/theory.md)和[152温度／标签交叉项](experiment_history/152_temperature_label_error_interaction.md)保留理论边界。

2026-09-22晚间。**原默认保持；ApproxTarget10保留为低成本候选，不再因一个区间未过而直接停止探索。** Web默认GT10-soft-t1，Yandex默认GT10-hard，生产主搜索E99。

## 9月22日历史单批复测

用户要求的E125冻结模型Web单组复测已于21:21前完成核验。4096条新源query、K1/L1000、CPU15实际1线程、三次完整wall：

| 方法 | Recall@1 | 命中 | 完整QPS |
|---|---:|---:|---:|
| GT10-soft-t1 | 90.795898% | 3719/4096 | 419.559 |
| ApproxTarget10 | 90.649414% | 3713/4096 | 419.121 |

候选救回6/损伤12，差−0.146484pp，95%配对bootstrap描述区间[−0.341797,+0.048828]；QPS−0.104439%，三轮范围重叠。旧批同点为−0.097656pp、3救回/7损伤；两批均小幅为负，不能说无损或线上更快，但仍可评估费用与质量取舍。新批与登记split、旧E105整个20K窗口及原画像拟合输入字节互斥，源顺序窗口不是全源随机/语义独立。全返回、原E99、线程/身份、精确GT和区间独立复核通过。[记录138](experiment_history/138_e125_web_fresh_check_and_policy.md) · [复测报告](entry_method_exploration/20260922_until2200_improvement_v1/stages/e125_web_fresh_check_v1/report.md)。

## 近似监督的价值与成本口径

原E125两集12点、三次完整wall中，所有召回均值损失不超过0.10pp，QPS差−0.2161%至+0.0893%；只有Web主点旧98.75%非劣下界没有过预定−0.25pp。原STOP门/结果保留。现在按用户修订策略，将探索与默认替换分开，状态为**RETAIN_LOW_COST_CANDIDATE**。单点区间未过不一票否决；保留实际损失及不确定性，不把放宽探索资格写成统计通过。[策略](entry_method_exploration/20260922_until2200_improvement_v1/research_decision_policy.md)。

20K画像近似目标完整作业Web64.591秒、Y28.040秒；对应exact20K搜索312.862/1417.293秒。近似单线程、exact受8个CPU限制，阶段/资源不同，不称同资源加速比。QGT5K精确监督仍保留。GT-inclusive当前默认核心构建合计403.997/1780.232秒，其中exact GT占97.94%/99.43%；不含公共底图、嵌入/下载/历史选型。[成本135](experiment_history/135_gt10_gt_inclusive_build_cost.md) · [原试验137](experiment_history/137_approximate_target_profile_cost_pilot.md)。

补充费用范围：Web继承的soft温度源于原20K精确GT1，Y-hard无该依赖。当前是固定既有H/参数下的近似标签费用改进，尚非新数据集从零构建验证；新复测有效性不变。[依赖与纠偏方向](experiment_history/139_approximate_supervision_scope.md)。

## 本轮机制结论

GT10的优势有具体证据：真实GT选H、十目标形成较稳定且保留语义对应的query方向、静态画像和廉价小图推理。固定20K两半下，Web GT1/hard10/soft10的画像夹角中位24.5°/12.1°/8.5°，Y GT1/hard10为27.2°/16.5°；去共同方向后仍保持，真实对应跨半亲和胜置换。闭式亲和最优与稳定性不等于Recall最优。[记录134](experiment_history/134_gt10_profile_direction_stability.md)。

E123真实目标区域服务策略有正值；E124预测更准仍未形成净收益，原因需要区分代理偏差与学生预测误差，不能仅归为模型弱。目标预算固定256-query全H诊断仍有余量，Web/Y K100 single+默认oracle为+1.586/+2.641pp，但只是历史query事后上限，不是可部署收益。[记录133](experiment_history/133_privileged_surrogate_decision_geometry.md) · [记录136](experiment_history/136_target_budget_fullH_opportunity.md)。

只读训练缓存已补核算：随机残差校正要在合力归一化的向量总和MSE上优于直接近似，Web/Y解析临界m约3269/8517，占20K的16.34%/42.58%。残差方差虽小，直接近似偏差也已部分抵消，少量补标不必更好。没有据此训练模型或选择m；这不是Recall门或否定混合监督，只用于评估投入。 [记录140](experiment_history/140_approximate_target_residual_variance.md)。

已有入口/返回的补充只读对齐显示：新Web1150/4096条换三入口集合，只有21条最终K1返回ID改变；当前预算下路由改变不等于搜索增益，不说明轨迹相同或全H无余量。[记录138](experiment_history/138_e125_web_fresh_check_and_policy.md)。

## 完整性能证据的位置

E103仍是最新完整五数据集重测，E118是最近宽预算候选比较；今晚E125是双集三预算及Web单点补测，不冒充五集新前沿。E103最快已测R90达标点上，Web K1/K100 QPS520.79/340.46（对NSG+24.99%/+0.79%），Y为2406.16/1241.64（+9.63%/+6.96%）；实际Recall分别90.7500%/90.6868%、91.0500%/90.9805%，方法L/Recall并非完全一致，非同Recall显著性结论。GIST收益基本持平，不能称所有数据全面占优。

当前无默认替换。9月22日流水已完成；9月30日研究已按用户指令暂停，已完成实验的原协议和证据保留。下一步见[s-target.md](s-target.md)。本轮[总报告](entry_method_exploration/20260922_until2200_improvement_v1/report.md) · [PDF](entry_method_exploration/20260922_until2200_improvement_v1/GT10理论与性能改进研究.pdf) · [理论](entry_method_exploration/20260922_until2200_improvement_v1/theory.md) · [改进方向](entry_method_exploration/20260922_until2200_improvement_v1/directions.md)。此前流水摘要已完整保存在[原文快照](entry_method_exploration/20260922_until2200_improvement_v1/reviews/root_docs_before_closeout/summary.md)，历史事实由[s-experiment.md](s-experiment.md)与详细卡片索引维护。
