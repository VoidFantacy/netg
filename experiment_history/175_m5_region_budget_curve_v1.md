# E175：M5区域补全的公共10K五档预算曲线

2026-10-10，用户要求“多测几个点，最后画一个类似这种的图”。新版本完整执行80点/240计时批次、200比较/20机制、独立结果审计与四panel PNG/SVG。当前身份为 `research/state-20261002` / `96cf05d5410cf51272048cd1f90b4bb194e23c62` 的未提交独立扩展；无新提交或发布。E173/E174原协议、锁、结果、停止不回改。

## 问题与固定范围

比较随搜索预算变化的完整Recall/QPS曲线，保留原NSG、当前GT10、原M5及新M5REG96。E174区域增量同L增加小幅Recall并付出QPS，未建立两角色可靠综合双升。本轮是用户另行授权的五L有限扩展，固定原公共窗口和原区域机制；不是按部分响应追加到通过。

公共test单role：Web原public10K，Y原public100K前10K，source-file窗口位置0..9999。真实K=1/100、L=200/400/800/1000/1200、四法共80点。raw-IP、base/主图/GT10画像和residual_joint表冻结。原M5完整C≤24保留；REG沿E174三header，每路由行query-best候选，最多3个去重seed，一跳round-robin、main-vt/无效/padding/C/X重复过滤，额外fresh scalar X≤96。原R重评分、C/X评分、合并及normal输出生命周期均付费，不因“相同主L”宣称总工作相同。

两job CPU15、T1串行，OpenMP/BLAS/MKL等均1，实际最大线程数1；各方法/K/L warmup256，三轮完整normal Batch allocate/init/release wall，旋转四法执行次序。QPS取每点三轮中位与min–max；加载/hash/写盘/oracle/GT评价属于阶段成本。四法在本轮同条件重测，E173旧timing不拼入新曲线。

每点全10K保存plain，full native replay在内存逐词比较，原M5全量线性oracle通过；20REG点完整seed/邻接/visited/fresh scalar/线性oracle和10000×128 i32 trace通过。CountDC/plain词及physical NDC只覆盖固定均匀256查询，post/X已计入graph_ndc。正式timed返回未保留；不是full10K CountDC或各轮timed bits核验。

## 实际结果与判定

80点、240正式完整wall均完成，两dataset exit0。独立结果审计实核80点/240轮/200比较/20机制，曲线独核80真实点、16条五档线、80组min–max与中文可读性，均PASS。

| 同L比较（各20点） | Recall升/平/降 | 配对QPS升/平/降 | ΔRecall范围pp | 配对QPS变化范围 | 救回/损伤成员次数和 |
| --- | --- | --- | --- | --- | --- |
| REG−原M5 | 17/3/0 | 0/0/20 | 0～+0.1600 | −3.261940%～−0.034929% | 4138/0 |
| REG−GT | 20/0/0 | 0/0/20 | +0.0087～+2.0800 | −5.988874%～−0.344272% | 30517/0 |
| 原M5−GT | 20/0/0 | 0/0/20 | +0.0042～+1.9200 | −4.764435%～−0.158252% | 26379/0 |

三组均无同L双升。REG的主要观察是小幅额外Recall和完整速度支出，不能称为可靠综合改进。

80个预锁跨L比较只观察到以下4个双升，全部WebVid K1：

| 较小L候选 / 较大L GT | 候选/GT Recall% | 候选/GT QPS中位 | ΔRecall pp | 配对QPS变化 |
| --- | --- | --- | --- | --- |
| M5 L800 / GT L1000 | 91.94 / 91.66 | 422.463 / 340.983 | +0.28 | +23.893320% |
| REG L800 / GT L1000 | 91.96 / 91.66 | 421.332 / 340.983 | +0.30 | +23.459832% |
| M5 L1000 / GT L1200 | 92.68 / 92.33 | 339.487 / 285.545 | +0.35 | +18.886987% |
| REG L1000 / GT L1200 | 92.70 / 92.33 | 339.343 / 285.545 | +0.37 | +18.822102% |

四比较各三轮皆快且范围分离，但仅对应两组实际预算对；原M5在两组已经双升，REG各多救回2个真实成员，**未新增双升预算组合**。WebK100/YK1/YK100均无跨L双升。配对QPS为逐轮比值的中位，和图中两点QPS中位的比值是不同统计量；crossL只按保存的round序号顺序配对，不能称并行或随机重复确认。

20机制按L=200/400/800/1000/1200：

| 数据集/K | 新增救回成员 | 原M5全局U外救回 | 原TRAIN_GT100全局U外救回 |
| --- | --- | --- | --- |
| Web/K1 | 16/8/2/2/2 | 11/5/1/1/1 | 0/0/0/0/0 |
| Web/K100 | 1117/856/573/492/461 | 876/654/425/359/331 | 36/23/15/14/12 |
| Y/K1 | 2/2/0/0/0 | 2/2/0/0/0 | 1/1/0/0/0 |
| Y/K100 | 299/138/67/56/45 | 295/134/65/54/43 | 126/44/16/13/7 |

全部三类damage及extension_aborted为0。合计新救回4138，其中旧M5 U外3259、旧TRAIN U外308；为跨工作点incidence和，不是全局唯一ID或独立泛化。候选X跨U计数和命中rescue跨U计数分开保留，前者不能代替后者。

## 准备、冻结与独审范围

协议/scope先于固定窗口复制。原公共source fresh SHA；旧109件输入采用E174完整SHA加当前exact stat，明确不称全部fresh大件重hash。加上4原公共source及6派生raw共119输入身份，运行前后/后处理均核stat。行政复制已读取历史曝光GT整数，0新GT/teacher。新TRAIN=0，旧M5监督/构建及历史跨方法TRAIN费用债保留。

编译与n16资格通过；新80点完整oracle/replay，原E173控制60点420份raw逐位相等。所有科学源与binary在execution_lock冻结。未执行旧plot/report源保留，执行plot_curves_v2及write_report_v2仅是事前冻结的文字精确化补充，统计内核与原锁不变。全部native完成后，才顺序打开新返回执行evaluate→independent_audit→plot→report，各退出0。

预锁200比较：每dataset/K/L六方向sameL共120，所有small<big十对L×四dataset/K×M5/REG对大L GT共80；无事后选点。20region机制逐query计算命中成员/rescue/damage及三类实际新damage。评价沿固定seed做2000次描述配对bootstrap；独审重算整数/wall/QPS/trace及CSV身份，检查CI元信息/seed/范围并保留已存端点，不重复随机bootstrap。无语义IID或同时多重比较保证。

独审逐ID核原GT100前10K与派生GT、rows0..9999一致；原/派生query向量不在评价/独审/绘图/报告中重读，沿预检SHA和当前stat。仅历史已曝光public_test单角色，无新confirm或本窗口新MF/GEO/FIRST强控。原native callback符号绑定未决限制保持；源码、图像offset及全scalar oracle不能声称符号绑定完全解决。

## 实际费用与资源

| 阶段 | 记录elapsed秒 | 原收据/口径 |
| --- | --- | --- |
| 固定窗口/数据预检 | 0.439083 | data_preflight内部阶段 |
| 编译 | 8.632061 | build |
| n16资格与旧词回归 | 55.201368 | smoke_regression内部阶段 |
| 正式native Web | 4362.911620 | job子进程生命周期，含加载/warmup/oracle/正式批次/保存 |
| 正式native Y | 4436.052779 | 同上 |
| 评价 | 25.032714 | evaluation_execution，wrapper子进程生命周期 |
| 独立结果审计 | 35.906468 | independent_audit_execution，同上 |
| 绘图 | 0.920985 | plot_curves_execution内部阶段；wrapper为0.988960 |
| 报告生成 | 0.039355 | report_execution内部阶段；wrapper为0.062329 |
| 首次行政准备失败 | 未计（非0） | administrative_failure_1保留None |

native两job合计8798.964398秒；普通查询调用总4,040,960含warmup/正式/plain/replay/count，正式2,400,000查询/240批次。不要把内含formal wall和native elapsed再次相加，script内部与wrapper范围也不相加。上述费用不是全部开发/源码审/失败的完整项目wall。首次系统python缺numpy在import时失败，尚未创建锁/复制/GT读取；转现有.venv_cpu成功，未计行政耗时不填写0。

实际观测最大线程均1；约0.25秒/proc VmRSS采样Web9232728064B、Y17509609472B，非精确峰值；两job均低于7200秒/64GiB门。native结束时版本加四根文档/history175合计489116589B；最终分析/图/文档及至少1GiB磁盘剩余按终态资源检查收据，512MiB总cap保持。未用旧timestamp、预计耗时代替本轮实际成本。

## 交付、当前默认和停止

[PNG主图](../entry_method_exploration/20261010_m5_region_budget_curve_v1/analysis/final_v1/figures/recall_qps_budget_curves.png) · [SVG](../entry_method_exploration/20261010_m5_region_budget_curve_v1/analysis/final_v1/figures/recall_qps_budget_curves.svg) · [全部80点](../entry_method_exploration/20261010_m5_region_budget_curve_v1/analysis/final_v1/points.csv) · [200比较](../entry_method_exploration/20261010_m5_region_budget_curve_v1/analysis/final_v1/comparisons.csv) · [20机制](../entry_method_exploration/20261010_m5_region_budget_curve_v1/analysis/final_v1/mechanisms.csv) · [完整报告](../entry_method_exploration/20261010_m5_region_budget_curve_v1/analysis/final_v1/report.md)。四panel横Recall百分比/纵完整单线程QPS，蓝NSG/橙GT10/红原M5/紫M5REG96，五真实L线段，无拟合/jitter/中间L推断。

[终态](../entry_method_exploration/20261010_m5_region_budget_curve_v1/state.json) · [原生阶段收据](../entry_method_exploration/20261010_m5_region_budget_curve_v1/run_state.json) · [独立结果审计](../entry_method_exploration/20261010_m5_region_budget_curve_v1/reviews/independent_result_audit/report.json) · [图像独核](../entry_method_exploration/20261010_m5_region_budget_curve_v1/reviews/final_curve_delivery_review.json) · [资源/历史保护终核](../entry_method_exploration/20261010_m5_region_budget_curve_v1/reviews/final_resource_and_preservation_check.json) · [协议](../entry_method_exploration/20261010_m5_region_budget_curve_v1/protocol.md) · [参数锁](../entry_method_exploration/20261010_m5_region_budget_curve_v1/parameter_lock.json)。run_state保留native完成时“待评价”历史字样，当前质量/交付已在state及执行收据中闭合。

默认仍production E99、Web GT10-soft-t1、Y GT10-hard；原M5和REG均为研究方法。有限E175实测、独审、曲线/报告已完成，停止本轮；可靠Recall–QPS综合改进/默认替换尚未达成。后续方法差异及未参与选择的确认数据须另立冻结范围。本轮不自动加L/cap、训练、选点或新role。
