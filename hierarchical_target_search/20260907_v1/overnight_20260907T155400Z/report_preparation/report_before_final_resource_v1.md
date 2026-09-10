# 实验总结

本轮完成P0–P2及P3完整实验，P3搜索收益gate未通过。目标更集中没有带来有效端到端性能改善，WebVid主对照反而退化。已完成三项失败诊断并保存复现证据。P4–P8及正式验证未开展，长期研究仍未完成。

报告在北京时间2026-09-08 07:00停止核验后创建。研究版本为 `hierarchical_target_search/20260907_v1`，本轮产物目录：`/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z`。本文的结果均来自本轮已保存的CPU开发pilot与诊断；没有截止后补跑的实验。

## 1. 完成到哪里，为什么停止

| 阶段 | 状态 | 实际完成与判断 |
| --- | --- | --- |
| P0 输入审计 | PASS | 输入SHA、形状、图编号、split完整性/隔离及嵌入base抽样核验；未打开held-out |
| P1 实现与测量 | PASS | 新搜索、计数/纯wall/trace及真实同入口parity通过；P3的256叶区新增验收也通过 |
| P2 核心机制 | 有限PASS | 真实区域路由退化；oracle区域保护提高Recall但更慢。定位预测差距，允许一次表示/划分修订 |
| P3 结构与门户 | 完整运行，NOPASS | 训练结构子条件通过，预注册主搜索收益条件失败；全部2数据集×2λ×2门户模型完成 |
| 负结果诊断 | COMPLETE | 门户暴露、目标泛化、实际局部目标尺度三项有限诊断及独立解释核验完成 |
| P4–P8 | NOT_STARTED | P3 gate未通过，未训练层次预测器，未进入端到端正式曲线、稳定性、冻结测试或论文完成阶段 |

权威gate：[P0](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/gates/P0.json)、[P1](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/gates/P1.json)、[P2](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/gates/P2.json)、[P3新增P1](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/gates/P1_P3_reacceptance.json)、[P3 NOPASS](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/gates/P3.json)。P3在北京时间02:00:52已判定失败，不是被07:00截止打断。未降低门槛、事后替换主对照或将不显著结果反复重跑。

实际时序：09-07 23:53:57建立控制配置；09-08 00:01:04开始首个注册输入审计；02:46:07最后一个注册诊断结束；03:02:48因本版本负结果和有限诊断已完成，提前关闭新实验入口。此后只做既有证据/文档复核与截止监控，**这段等待不是持续训练时间**。07:00完成最终截止核验后撰写本报告。完整时序见[执行台账](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/ledger.md)、[54项注册任务记录](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/control/jobs)及[提前关闭记录](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/control/CLOSED.json)；短命令不全包含在54项注册任务计数中。

## 2. 实现了什么，如何验证

新增/完善的区域搜索让所有队列共享visited、真实距离计算和全局top-K结果，并严格分配固定总容量。统一池与区域池都走相同的结果收集规则，保留跨区边访问。区域内按真实距离排序，队列之间按权重轮转；L表示保留候选的容量，不是距离计算或扩展次数上限。

| 实现 | 用途与范围 |
| --- | --- |
| [ACSG/RegionalSearch.h](/data/netg/ACSG/ACSG/RegionalSearch.h)、[test_regional_search.cpp](/data/netg/ACSG/benches/test_regional_search.cpp) | 统一/区域候选池、容量分配、共享visited/top-K、跨区扩展、trace及边界测试 |
| [bench_hierarchical_eval.cpp](/data/netg/ACSG/benches/bench_hierarchical_eval.cpp) | P2真实路由/oracle适配、独立count、纯wall、预选trace |
| [bench_hierarchical_eval_p3.cpp](/data/netg/ACSG/benches/bench_hierarchical_eval_p3.cpp) | 256叶区与P3固定2×2模型的独立评测入口 |
| [bench_hierarchical_portals.cpp](/data/netg/ACSG/benches/bench_hierarchical_portals.cpp) | 固定候选/fit查询的单门户覆盖代理和greedy选择 |
| [P2 partition_graph.cpp](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p2/partition_graph.cpp)、[P3 partition_hierarchy.cpp](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p3/partition_hierarchy.cpp) | 严格容量的图分区、共同层次初始化与λ0/λ1精确整数目标下降 |
| [控制与stage runner](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/control)、[分析及诊断](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p3) | 单重任务、输入/gate/输出边界、截止保护、完整分析与失败解释 |

原 `ACSG.cpp/h` 和旧Fast默认评测源码保留；`benches/CMakeLists.txt`在原内容后增加三个目标。新的paired Fast明确按正确的HNSW入口优先顺序消费入口；“相同入口的搜索核与legacy一致”不等于旧端到端Fast的入口顺序与新路径完全相同。

验证已完成：11组合成搜索测试、1200个kernel parity实例（含800个同分实例），visited epoch回绕和随机region/trace检查；非法ID、空区域、重复入口、容量边界及K>L拒绝；新代码ASan/UBSan检查；两个数据集各512个pilot查询×L64/128的结果/NDC/count/plain/legacy一致性；m4/6/8真实入口消费。P3另做P2兼容性、真实256叶区模型验收以及分区精确ΔC/ΔS、共同初始化、两轮下降和容量约束核对。sanitizer证据针对所编译的新路径，不能称为所有旧静态库已全面重编译审计。

纯wall在开始计时前分配工作区和结果缓冲；计时内包括查询归一化、实际路由、去重/重置、队列调度、搜索及结果写入，计时外评分GT、hash、trace和JSON。count/trace独立运行，逐查询ID与plain核对；GT不会进入真实路由或搜索API。独立计时边界和验收见[P1搜索审计](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p1/search_audit.json)、[evaluator审计](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p1/evaluator_independent_review.json)、[真实parity](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p1/real_parity_v1/report.json)及[P3验收gate](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/gates/P1_P3_reacceptance.json)。

## 3. 实际实验设置

| 项目 | 本轮实际值 |
| --- | --- |
| 数据 | WebVid `webvid2_5m_light_v1`：2,505,000×512；Yandex `yandex_t2i_official10M_ip_v1`：10,000,000×200 |
| 图与距离 | 原冻结directed NSG，原raw-IP契约；分区的对称辅助邻接不替换搜索图 |
| fit / pilot | 原router_train后20K `[10000,30000)`拟合；前10K `[0,10000)`为历史已使用的development pilot |
| Fast配对 | 独立5K QGT raw hubs复用；只用同20K重建prototype，不输入旧30K prototype |
| 运行 | 全CPU，搜索16线程；K=10，L=64/128；各方法每L先warm-up 128查询 |
| 重复与区间 | count一次、纯wall五轮；10K逐查询配对bootstrap 10,000次，普通95%探索性区间 |
| 种子 | P2分区/模型、P3初始化/门户查询选择/分析基础seed=2026090711；P3的16个子分区使用同一固定seed；Micro-HNSW seed=100 |
| P2 | 64图区域，每区2门户、20K区域查询画像、激活4区；Fast加5项统一/区域池对照 |
| P3 | 16粗×16细区域，共同初始化；λ0/1各两轮确定性严格下降，粗细全局容量≤平均值1.2倍；每叶3门户，共768；frequency3/greedy3固定2×2 |
| 门户代理 | 每叶最多8候选、128条fit查询，K10/L32离线单门户搜索；按覆盖增量greedy选3个 |
| 搜索容量 | 共享队列占25%；其余给4个活跃区域，每区至少4槽，余量按概率最大余数分配 |

配置入口：[P2及测量协议](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/protocol.json)、[P3冻结协议](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p3/protocol.json)。五轮计时不是五个独立Recall样本。本文QPS统一显示五轮整批wall QPS的算术平均；routing-only wall是另外一次16线程整批测量，不能当作单查询延迟。没有运行独立1线程p50/p95/p99、三独立build或正式校正后的性能门槛验证。

**数据访问范围：** validation未用于拟合、模型/参数选择或ANN性能评测，但P0读取其query/GT做文件头和完整SHA、查询逐行指纹去重/跨split重叠及finite检查、GT编号范围/行内重复检查。held-out文件未打开。此前交接中笼统的“validation/held-out未读”已经更正，旧日志保留，见[P0访问范围补充](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p0/validation_access_scope_addendum_v1.json)。pilot不是新的未见测试集。

## 4. 测量结果与配对对照

### P2：真实方法没有改善，oracle有质量潜力但更慢

| 数据 | L | 方法 | Recall@10 (%) | QPS | 路由NDC | 图NDC | 总NDC |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| WebVid | 64 | paired Fast | 65.657 | 32,079.8 | 124.747 | 922.031 | 1046.777 |
| WebVid | 64 | 真实几何路由＋区域概率池 | 59.929 | 19,573.6 | 188.747 | 1504.883 | 1693.630 |
| WebVid | 64 | oracle＋区域概率池 | 71.354 | 21,352.3 | 124.747 | 1348.915 | 1473.662 |
| WebVid | 128 | paired Fast | 74.698 | 17,421.8 | 124.747 | 1652.090 | 1776.837 |
| WebVid | 128 | 真实几何路由＋区域概率池 | 70.642 | 12,003.5 | 188.747 | 2394.311 | 2583.058 |
| WebVid | 128 | oracle＋区域概率池 | 80.081 | 13,744.2 | 124.747 | 2084.242 | 2208.989 |
| Yandex | 64 | paired Fast | 82.832 | 27,390.7 | 119.313 | 1649.605 | 1768.918 |
| Yandex | 64 | 真实几何路由＋区域概率池 | 75.652 | 16,508.9 | 183.313 | 2681.210 | 2864.523 |
| Yandex | 64 | oracle＋区域概率池 | 86.248 | 19,062.9 | 119.313 | 2352.717 | 2472.030 |
| Yandex | 128 | paired Fast | 89.655 | 15,947.7 | 119.313 | 2862.009 | 2981.323 |
| Yandex | 128 | 真实几何路由＋区域概率池 | 85.974 | 10,033.1 | 183.313 | 4214.951 | 4398.264 |
| Yandex | 128 | oracle＋区域概率池 | 93.183 | 11,780.0 | 119.313 | 3635.672 | 3754.985 |

NDC是每查询实际距离计算数；路由/图/总量分列。oracle读取真实GT区域占比，只作机制诊断，其点**不能作为可部署性能点**。统一池、均匀池和完整逐点结果都保存在[全部72个测量行及60个固定对照](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/report_preparation/measurement_tables_v1.md)，其中P2为24行测量/28个对照，P3为48行/32个对照；表格与原来源指针已[独立核对](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/report_preparation/measurement_tables_independent_review_v1.json)。

同一实际route下，真实概率区域池相对统一池，WebVid L64/128退化5.431/3.640 pp，Yandex退化6.867/3.488 pp；oracle区域池分别提高5.413/5.252 pp与3.155/3.359 pp，四个普通95%区间下界均为正，但同时增加NDC、降低QPS。所有真实P2方法在当前两个点都被paired Fast支配。P2因此只支持“存在oracle质量潜力且预测差距可定位”，不支持有效端到端改善。完整CI、计时轮次与路由一致性见[P2分析](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p2/analysis_v1/report.md)。

![P2全部六方法的Recall与QPS；oracle只作诊断](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/report_preparation/figures_v1/p2_recall_qps.png)

原预注册23个query ID的trace已全部完成：初批0–15，之后使用冻结实现补齐其余7条；合计460条trace、276个配对重放通过。原P2 gate的16/23是决策时的历史证据，不覆写；当前完整性以[trace完成补充](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p2/trace_completion_addendum_v1.json)为准。固定trace不是随机代表样本；同路由队列对照同时改变保留与调度，不能声称隔离了单一保留机制的因果效应。

### P3：预注册搜索收益条件失败

目标为 `J=C/M+λ·S/(9Q)`，C为有向跨叶边槽数，M为有效非自边槽数，S为fit各查询的“GT10覆盖叶数减一”之和，Q=20,000。λ1使fit平均GT10跨叶数从λ0的WebVid4.33285/Yandex3.00925降为2.60275/1.96480，结构子条件通过。

主对照固定为 **oracle_probability下λ1_greedy3−λ0_greedy3**：

| 数据 | L | λ | Recall@10 (%) | QPS | 路由NDC | 图NDC | 总NDC |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| WebVid | 64 | 0 | 74.140 | 24,081.4 | 124.747 | 1200.248 | 1324.995 |
| WebVid | 128 | 0 | 82.119 | 15,054.2 | 124.747 | 1913.379 | 2038.126 |
| WebVid | 64 | 1 | 73.274 | 25,354.9 | 124.747 | 1197.612 | 1322.359 |
| WebVid | 128 | 1 | 81.329 | 15,156.1 | 124.747 | 1908.785 | 2033.532 |
| Yandex | 64 | 0 | 87.994 | 19,858.1 | 119.313 | 2232.038 | 2351.351 |
| Yandex | 128 | 0 | 93.990 | 12,036.2 | 119.313 | 3490.392 | 3609.706 |
| Yandex | 64 | 1 | 87.899 | 19,741.7 | 119.313 | 2248.817 | 2368.130 |
| Yandex | 128 | 1 | 93.973 | 12,123.0 | 119.313 | 3507.601 | 3626.914 |

| 数据 | L | λ1−λ0 (pp) | 普通95%配对区间 (pp) |
| --- | ---: | ---: | --- |
| WebVid | 64 | -0.866 | [-1.083, -0.647] |
| WebVid | 128 | -0.790 | [-0.960, -0.621] |
| Yandex | 64 | -0.095 | [-0.207, +0.016] |
| Yandex | 128 | -0.017 | [-0.080, +0.048] |

WebVid两点的区间均为负；Yandex未证实改善，不能写成等效。四格无一满足预注册正下界，故P3 NOPASS。跨模型wall只是固定顺序实测描述，不能将同轮编号当成独立配对计时设计；即使表中某个QPS更高，也不能代替失败的主搜索条件。

8个固定门户对照的普通95%区间全部含0，未证实收益；16个同route的oracle区域保护对照提高Recall但增加NDC、降低QPS，同样不能救回P3。没有事后把λ0消融改为胜出主方法。完整分析和gate复核见[P3报告](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p3/analysis_v1/report.md)及[独立gate审查](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p3/gate_independent_review_v1.json)。

![P3四个主结构对照与八个门户对照的既有95%区间](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/report_preparation/figures_v1/p3_fixed_contrasts.png)

两个计量解释已单列补充：Fast的部分expanded/rejected/evicted字段是未测量占位，不是真实零；P3分析内bootstrap嵌套status残留初始值，但32个10,000-draw文件、完成标记和全部CI已独立核对一致。原产物均保留，见[计数语义](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p3/measurement_semantics_addendum_v1.json)与[分析完成核验](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p3/analysis_completion_addendum_v1.json)。

## 5. 三项失败诊断：确认了什么，仍不知道什么

**门户已经进入实际route。** 8个固定对照、每格10K查询的实际入口集合全部改变，排除“新门户根本没被使用”。返回top10集合仍有68.34%–93.36%相同，但不能推出访问/扩展轨迹相同、门户必然冗余或图连通性因果。实测不存在完全相同route样本，相同route的不变性检查在这里无样本，不作为新增实值验收。WebVid λ1有6个查询的加权代理因正权重区域无fit支持而记未定义，没有补零或重归一。见[门户暴露诊断](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p3/portal_exposure_diagnosis_v1/analysis.json)与[独立解释](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p3/portal_exposure_interpretation_review_v1.json)。

**WebVid有部分区域集中度传递，但丢失主要在seen目标。** M4表示真实GT10中落在所选4叶区的比例；搜索仍可跨区，因此它不是Recall上界。seen指base目标ID在fit GT10出现，不是查询重复或泄漏。

| 数据 | fit平均跨叶数 λ0→λ1 | pilot平均跨叶数 λ0→λ1 | pilot M4变化 | pilot中seen目标槽位占比 |
| --- | --- | --- | ---: | ---: |
| WebVid | 4.33285→2.60275 | 4.3194→4.0209 | +1.808 pp | 57.258% |
| Yandex | 3.00925→1.96480 | 3.0181→3.0193 | −0.004 pp | 10.163% |

WebVid主Recall差−0.866/−0.790 pp，分解为seen贡献−0.870/−0.753、unseen贡献+0.004/−0.037 pp，不能全部归因于未见目标。Yandex在总体pilot上几乎没有集中度传递；这不证明每个子组不变或等效。原GT与返回ID的命中重算、40对照及440个固定支持分组的贡献/均值复核均通过。分组分析是描述性的，没有新增CI，见[目标泛化诊断](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p3/target_generalization_diagnosis_v1/diagnosis.json)及[独立解释](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p3/target_generalization_interpretation_review_v1.json)。

**当前λ1目标在局部实际上先比较GT分散变化，再比较图切边。** 只读原邻接、fit GT10和保存标签的诊断显示，两个数据集全部fit见过的独立目标都满足严格条件 `d(u)·9Q<M`：

| 数据 | fit见过的独立目标数 | 最大入出边槽总数d | 严格阈值M/(9Q) | 满足条件 |
| --- | ---: | ---: | ---: | ---: |
| WebVid | 118,811 | 168 | 275.619206 | 100% |
| Yandex | 188,913 | 162 | 1638.026633 | 100% |

两组各200,000个fit目标出现次数也全部满足。全库WebVid仅17个例外且均未见于fit GT；Yandex全库满足。所有λ1/λ0终态标签不同节点52,305/72,107也满足。d按原有向有效非自边的入出槽计数，保留重复边；两数据集各31个固定分组与紧凑直方图守恒核验通过。

固定当前标签、所考虑候选与可行性时，两个候选的切边变化差最多为d，而整数ΔS至少差1；上述严格界使λ1先比较ΔS，再比较ΔC。unseen节点所有候选ΔS均为0，也符合该局部规则。源码使用精确整数分数；与stay完全零同分时保持原标签，严格改善移动同分才取较小叶ID。图仍影响候选与同ΔS选择，容量、源叶最小规模和更新顺序仍影响结果。**这不是全局最优证明，也不能单独解释Recall退化**，不能据此直接调λ、重做表示或启动辅助图。见[局部尺度诊断](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p3/objective_local_scale_diagnosis_v1/diagnosis.json)、[纯代数补充](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p3/objective_lexicographic_addendum_v1.md)及[独立解释审查](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p3/objective_local_scale_interpretation_review_v1.json)。

三项诊断各自冻结范围后才运行；没有新增模型/搜索性能点/CI或更改gate。源码、合成验收和访问范围在各诊断目录。剩余的关键未知是：怎样的区域与门户目标才能在实际有限容量、跨区搜索中可靠保留命中；现有证据没有建立失败的单一因果解释。

## 6. 成本、资源、工程失败与停止核验

### 离线成本边界

| 实际程序 | WebVid | Yandex | 含义 |
| --- | ---: | ---: | --- |
| P2严格64区分区 | 27.7803 s | 171.6399 s | 已有原图下的分区程序wall |
| P2区域画像/门户模型程序 | 0.2293 s | 0.1814 s | 在已有分区和GT后的模型程序工作时间 |
| paired Fast 20K prototype | 0.1831 s | 0.0659 s | 在复用GT与QGT raw hubs之后 |
| P2测得的Fast router index初始化 | 0.0527 s | 0.0448 s | 单次evaluator初始化记录；独立于在线批wall |
| P3层次分区程序 | 40.0332 s | 262.2502 s | 共同初始化及λ0/λ1两个分支，不能称单个部署模型成本 |

P2主分析内partition字段为null是该汇总没有嵌入分区manifest，不是未运行：实际证据在[WebVid strict-v3](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p2/webvid_partition_strict_v3/manifest.json)和[Yandex strict-v3](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p2/yandex_partition_strict_v3/manifest.json)。P3成本见[结构分析](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p3/structure_analysis_v1/analysis.json)。

| 数据 | λ | 程序wall (s) | 其中加载图 (s) | probe＋评分批wall (s) | greedy (s) |
| --- | ---: | ---: | ---: | ---: | ---: |
| WebVid | 0 | 9.3434 | 4.1359 | 3.6997 | 0.003401 |
| WebVid | 1 | 8.4327 | 4.1365 | 2.8510 | 0.002648 |
| Yandex | 0 | 17.1438 | 10.9726 | 4.6697 | 0.003503 |
| Yandex | 1 | 16.5417 | 10.9766 | 4.0932 | 0.003143 |

成本含该程序内输入/图加载、probe、评分、写出等；不含上游fit抽取/候选选择、exactGT或分区。程序wall记录截至最后manifest写出前。不要把线程累计CPU秒与wall相加，也不要重复计算共享probe。

完整从零成本仍须包含 `T_exactGT + T_partition + T_portal + T_router`，并说明原NSG构建；本轮复用exact-GT、QGT raw hubs和原图，相关历史成本未知，记录为null，不能称完整训练只花上述秒数，也没有据此计算从零break-even。原始分项与来源指针见[完整成本记录](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/report_preparation/measurement_tables_v1_costs.csv)。缓存状态为已有文件/已有GT下的运行，在线计时经过warm-up，不能把结果称为冷启动性能。

### 失败与未完成的分类

- **工程启动失败1项：** 首次evaluator构建因PATH找不到cmake而未启动；随后使用既有隔离环境的绝对cmake路径成功，没有为此升级依赖。见[原启动失败](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/control/jobs/p1_evaluator_build_v1.json)和[修复后构建](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/control/jobs/p1_evaluator_build_v2.json)。
- **注册分区失败2项：** WebVid原METIS结果触发严格容量检查；诊断版保存了12区各超2节点的证据。查明库内额外容差后做输入补偿以满足原1.2硬上限，未放宽门槛；strict-v3通过。原失败manifest/标签/日志保留，其中[首轮INCOMPLETE manifest](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p2/webvid_partition/manifest.json)明确不作为有效模型。契约修复见[METIS容差补充](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p2/partition_contract_amendment_v1.json)。
- **短命令/合成阶段问题：** 同分顺序、sanitizer首次缺include路径、trace分析器合成检查等曾失败后修复并验收；不与完整P3算法负结果混算。完整索引见[报告证据索引](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/report_preparation/report_evidence_index_v1.md)。
- **算法证据失败：** P3完整pilot NOPASS；实现正确和训练目标下降没有保证搜索收益传递。没有截止造成的研究任务INCOMPLETE。
- **按gate未运行：** P4学习预测器、P5完整工作曲线、P6三构建/关键消融/强基线/tail、P7 held-out与LAION复验、P8论文完成。依赖已安装或smoke test通过，不代表GATE/LIRA/kRt/RoarGraph等本轮强基线已经正式复验。

### 资源、文件保护和任务停止

全程CPU，单重数据集任务控制；注册任务最大子进程rusage_maxrss为Yandex P3分区37,355,416 KiB（约35.625 GiB），不将轮询RSS或这个记录称为全部短命令的全夜内存上界。截止前产物约3.34 GiB，/data余约16.67 GiB，满足本轮8 GiB产物和10 GiB余量限制。最后的源码/配置、任务区间与资源核验会随本报告收口，入口为 `/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/report_preparation/final_protection_resources_v1.json`。

主动文件删除记录：**无**。未清理源码、base、GT、冻结图、历史结果、日志或唯一备份；没有reset/clean、推送或覆盖原有未提交工作。原核心源码与旧Fast路径的开始快照、评测版本校验和、CMake增量和原git状态保留在[源码保护证据](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/report_preparation/source_protection_preclose_v1.json)；git状态列表本身不证明整个checkout所有文件内容都不变。本次方法产物隔离保存，既有失败结果没有删除。

截止保护自开始运行，保存每个注册任务的命令、PGID、PID启动身份、独立日志、超时与资源检查。03:02提前关闭新任务入口；06:40/06:59全进程核验均为零，保存[06:40记录](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/control/milestone_0640.json)、[06:59检查点](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/control/milestone_0659.json)及[等待期间监控](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/control/idle_monitor.jsonl)。

07:00:00.312，北京时间硬截止后的核验记录确认全部注册研究进程已停止；07:01:24独立检查再次按全部任务token、PGID、PID启动身份和新增研究可执行程序扫描，活跃匹配为零，watchdog同一身份也不再活跃。没有任务结束时间跨越截止，没有向其他进程发信号，没有关机或重启。证据：[watchdog停止核验](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/control/stop_verification.json)、[独立最终进程核验](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/control/final_process_verification_v1.json)。截止后只读取既有证据/源码和文件元数据、整理文档，没有补跑训练、构图、ANN或方法开发。

## 7. 复现入口与下一步

读取顺序：[summary.md](/data/netg/ACSG/summary.md) → [spec.md](/data/netg/ACSG/spec.md) → [s-target.md](/data/netg/ACSG/s-target.md) → [冻结协议](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/protocol.json) / [P3协议](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p3/protocol.json) → [当前研究判断](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/current_findings.md)。全部关键证据的路径、SHA来源、大小和限制由[机器证据索引](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/report_preparation/report_evidence_index_v1.json)提供；其中截止前快照由P0访问范围及最终停止/保护记录补充。

历史命令与精确参数在每个 `control/jobs/*.json` 的 `command` 数组，日志及输出路径同文件给出。P2入口为[run_p2_evaluation.py](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p2/run_p2_evaluation.py)，P3为[run_p3_evaluation.py](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p3/run_p3_evaluation.py)；分析入口为[analyze_p2.py](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p2/analyze_p2.py)和[analyze_p3.py](/data/netg/ACSG/hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p3/analyze_p3.py)。本轮控制目录已关闭，历史输出作为冻结证据保留；未来复现必须新输出并遵守上游gate、split和兼容性契约。

**下一次唯一最高优先行动：** 依据“WebVid目标更集中但seen命中下降”的反例，先审查优化目标与实际有限容量搜索是否一致，提出一个可证伪的小gate，再决定是否另立方法版本。当前不支持直接调λ、事后选λ0为主方法、再做同类划分扫参、绕过P3训练P4或启动辅助图。三份交接与机器台账在本报告完成时同步；本次有截止的执行与报告交付结束，整个长期研究目标仍未完成。
