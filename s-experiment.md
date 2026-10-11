<!-- E176_CURRENT_BEGIN -->
# E176 最新实验索引（2026-10-10）

**当前最新实测：E176 原 M5 成本优化与剩余遗漏条件补全。160点/480完整wall批次、800比较、60机制与独立整数/wall/trace审计实际完成；有限版本 STOP。默认仍为 E99 GT10，原 M5 保留。** 下方原 E175/E174/E173 与更早完整索引正文保全。

- 历史/判断：[176_m5_residual_completion_curve_v1.md](/data/netg/ACSG/experiment_history/176_m5_residual_completion_curve_v1.md)。固定入口：[campaign README](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/README.md)。
- 范围：两dataset各已曝光public10K；真实K1/K100，L200/400/800/1000/1200；`NSG/GT/M5/M5OPT/M5REG96/REGOPT96/WIDE12/M5RES12`；串行CPU15/T1、三轮normal Batch完整wall。新FIT只用旧合法20K，原raw-IP/主图/GT10/原M5完整C保留，无新confirmation。
- 主结论：M5RES12对原M5 Recall14升/6平/0降，12460 query–GT成员救回/0损伤；两个point QPS中位数严格双升8/20，冻结paired口径9/20。WebK100五L组合+R0.1543..0.4168pp、pointmedian QPS+0.3769%..1.8872%。M5OPT与原M5全返回words20点相同；对M5OPT补全双升0/20，增R点均降速。PAIR对WIDE12 R1升/5平/14降、双升0，离线容量未配平，不能作纯条件键因果证明。
- 默认边界：RES对GT仅Y K100/L1200有弱sameL信号（+0.0064pp，pointmedian+0.082284%，paired+0.176726%），三轮非全更快、range不分离。跨L12方法双升只为原M5已有的两WebK1预算对，无新K100/Y joint；不插值、不替换默认。
- 费用：明确批准本次≤900秒/数据集新增FIT，实际Web469.143610/Y472.986268秒；旧TRAIN debt保留，累计22194.116446/16062.191988秒。预算timer含native/compiler child完整生命周期，后续manifest/hash/closing不含且未知不填0。正式native整job6970.796179/7089.322895秒；采样RSS非精确peak，分母/整job/inner与outer不重复相加。
- 证据限界：单次全量untimed fresh scalar/linear oracle、main包/优化参考逐词门；无第二整批native replay、timed packets未保留；固定256计数与完整10K候选trace分开。CI描述性且独审未重生，已曝光单role无新确认；U外成员不是跨模态泛化证明。

科学原件：[report](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/analysis/final_v1/report.md)、[metrics](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/analysis/final_v1/metrics.json)、[points](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/analysis/final_v1/points.csv)、[comparisons](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/analysis/final_v1/comparisons.csv)、[mechanisms](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/analysis/final_v1/mechanisms.csv)。[全部800解释](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/analysis/final_v1/interpretation.csv)保留原paired flags及pointmedian字段，两定义整体3个joint分歧不删选；[实际费用账](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/analysis/final_v1/cost_ledger_supplement.md)保留所有未知边界。

交付：[主曲线PNG](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/analysis/final_v1/figures_delivery_v3/recall_qps_budget_curves.png) / [SVG](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/analysis/final_v1/figures_delivery_v3/recall_qps_budget_curves.svg)、[机制曲线PNG](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/analysis/final_v1/figures_delivery_v3/mechanism_budget_curves.png) / [SVG](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/analysis/final_v1/figures_delivery_v3/mechanism_budget_curves.svg)、[独立结果审计](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/reviews/independent_result_audit/report.json)、[最终交付复核](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/reviews/final_delivery_review.json)。原source/锁/raw/报告/首版图与历史保留；不恢复旧队列、不新增fit/方法适配/确认。
<!-- E176_CURRENT_END -->

<!-- E175_CURRENT_BEGIN -->
## E175｜2026-10-10｜M5区域补全的公共10K五档预算曲线｜COMPLETE，未新增双升预算组合

实际完成两集×真实K1/K100×五L(200/400/800/1000/1200)×NSG/GT10/原M5/M5REG96的80点/240T1完整wall；200比较、20全量机制、独立结果审计与四panel PNG/SVG交付，0TRAIN。原三方法420份raw资格逐位回归；正式full replay/oracle通过，原M5保留。

REG−M5同L：Recall17升3平，QPS20降，无同L双升。80跨L比较仅4双升，对应WebVid K1两组L800→GT1000、L1000→GT1200；原M5在相同两组已双升，REG无新增组合，WebK100/Y无双升。历史已曝光公共10K单role，非新confirm；GT10默认不变。native两job共8798.964398秒，评价/独审/绘图另计，有限扫描完成后停止；E173/E174原件和结论保留。

详细记录：[175_m5_region_budget_curve_v1.md](experiment_history/175_m5_region_budget_curve_v1.md)；[报告](entry_method_exploration/20261010_m5_region_budget_curve_v1/analysis/final_v1/report.md)、[曲线](entry_method_exploration/20261010_m5_region_budget_curve_v1/analysis/final_v1/figures/recall_qps_budget_curves.png)、[80点CSV](entry_method_exploration/20261010_m5_region_budget_curve_v1/analysis/final_v1/points.csv)、[终态](entry_method_exploration/20261010_m5_region_budget_curve_v1/state.json)。
<!-- E175_CURRENT_END -->

# ACSG 历史实验概览

<!-- E174_CURRENT_BEGIN -->
174 已完成：[M5残差区域扩展](experiment_history/174_m5_residual_regions.md)，[完整报告](entry_method_exploration/20261010_m5_residual_regions_v1/analysis/final_v1/report.md)。保留原M5及完整C，0新TRAIN；pilot72点、confirm40点，共112点/336正式批次，完整4096评价与另行整数/wall/trace独审PASS。主M5REG96相对M5同L14点Recall增/2点平、16点QPS均降0.13%–0.70%；仅WebK1 b跨L观测双升，a负且原M5 b已有优势，原协议与严格报告主门均0。停止本冻结区域版，保留M5研究，GT10默认不变。E173及以下记录保持历史身份。
<!-- E174_CURRENT_END -->

<!-- E173_CURRENT_BEGIN -->
173 已完成：[直接公共测试复测](entry_method_exploration/20261009_nsg_gt_m5_test_v1/analysis_v2/report.md)、[详细复盘](experiment_history/173_nsg_gt_m5_public_test_retest.md)。WebVid/Yandex各10K；NSG、GT10、正在研究的M5，K1/K100、实际L200/400/800/1000/1200，60点/180轮完整单线程wall，0新增训练。同L M5/GT 20点Recall全增、成员损伤0、配对QPS约降0.16%–4.85%；WebVid K1有两对实际跨L双升，其他三场景没有。GT默认保留。新用户直接test授权不沿用旧CAL停止门；旧171/172记录及停止边界保留原身份。下文为此前历史概览。
<!-- E173_CURRENT_END -->

当前见[Git结论交接](research_snapshots/20261006_results/README.md)和[八方法详细报告](research_snapshots/20261006_results/report.md)，核实时点2026-10-06T21:32:45.619435+08:00。

每dataset跨全部方法TRAIN限7200秒；历史已超额，禁止新增训练。

阶段快照：8方向均已开始探索，7有阶段边界；已接受134/288 native（120normal+14audit），正式评价1/4；无可靠默认替换。

第12行起均为历史快照；旧预算解释、旧运行状态与未执行描述不覆盖上述当前结论。


2026-10-04 最新用户约束：用户原话“一个数据集的训练预算是两个小时以内吧”。Root按当前多方法探索上下文解读为每个方法×单个数据集的累计训练／拟合不超过7200秒；这是root解释，不是用户逐字说了“每方法”。同方法同数据集的K1/K100、FIT0、FIT1、refit及全部轮次共用一项累计预算，不按K点、轮次或阶段重置。监督／标签生成、构建、验证分别计时披露；用户未确认整条离线流水线总成本也是7200秒。详见[训练预算约束记录](entry_method_exploration/20261003_all_methods_experiments_v1/m2/training_budget_constraint_20261004_v1.json)。

训练预算已确认，但累计账本、实际timeout与执行guard尚未实现或运行，精确cost-check上限仍null；此前1小时只是历史root工作假设。不能靠阶段改名规避用户拒绝天级工期，预计整条路线仍需天级时不推进。M2原stage03未进入训练；最近进程事实只引用root于2026-10-04 10:32:35（上海）的观察：PGID 90589/100130可逆SIGSTOP、原六PID T/Ts，partial proof仅STAT为129566205B／inode1319835／mtime10:32:32.040776279，原件保留、未终止或恢复、不是完整六stage成功。本次没有fresh进程／proof核实，挂起不能替代实际终态；见[此前成本挂起记录](entry_method_exploration/20261003_all_methods_experiments_v1/m2/runtime_budget_hold_20261004_v1.json)。

172的完整五方法三联动目标仍ACTIVE；本次只更新预算和执行边界，既有实测、默认、原实验编号与停止范围保持。完整历史仍见172复盘。 [M2等价几何降成本源码独审](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/m2_exact_geometry_budget_source_v1_independent_static_v1.json)与[B4精确拟合降成本源码独审](entry_method_exploration/20261003_all_methods_experiments_v1/m4/b4_exact_fit_budget_source_v1_independent_static_v1.json)均仅条件SOURCE-only；两候选尚未执行，实际等价、提速及≤2h训练满足均未证明。saved-M5审计v1 canonical-state lease执行路线已被root拒绝；独立local-state只作静态建议，未实现或放行。

本段及新预算记录是当前约束；以下“预算待回复／pending”“1小时假设”“仍live／离线投入不限”等完整保留此前时点，不覆盖本次预算和挂起边界。


2026-10-04 10:32:35（上海）最新状态：[172离线成本挂起记录](entry_method_exploration/20261003_all_methods_experiments_v1/m2/runtime_budget_hold_20261004_v1.json)登记M2原stage03的可逆SIGSTOP及完整partial保留；全六阶段尚未成功完成，不能把停止占用CPU当作终态或方法失败。3–4天估计属于全量精确证明与复核、不是已实测训练耗时；用户拒绝天级工期，可接受单方法训练／构建／验证合计预算仍pending。完整五方法三联动目标ACTIVE、默认和已测结果不变，下一步仅源码／行政评估更短的合法路径，暂无actual ready或新收益。下文旧live与“离线投入不限”属于历史快照。


172新增JBP首K1自有启动观察接口V3：[根组合源码审查](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/jbp_capture_own_startup_source_v3_root_composed_source_review_v1.json)与[独审](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/jbp_capture_own_startup_source_v3_independent_static_v1.json)完成，实际helper及完整before/body/after来源图、probe→join当前stat连续性已源级闭合。[V1 HOLD](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/jbp_capture_own_startup_source_v1_independent_static_hold_v1.json)、[V2 HOLD](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/jbp_capture_own_startup_source_v2_independent_static_hold_v1.json)及原件保留；根123/独审112项安全来源稳定。仅SOURCE_ONLY_UNCOMPILED_UNRUN，16实际refs null／16flags false，无新增性能或默认替换，全五方法三联动继续；详见[172复盘](experiment_history/172_all_methods_experiment_campaign.md)。

172新增JBP构建V2条件SOURCE接续：[根全文复核](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/jbp_capture_build_admin_source_v2_root_full_source_review_v1.json)与[独审](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/jbp_capture_build_admin_source_v2_independent_static_v1.json)完成，修复四处固定终态来源分类并使用完整16字段非继承环境；[V1分类HOLD](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/jbp_capture_build_admin_source_v1_independent_static_hold_v1.json)及八件原封保持。原配方、完整科学范围和全部控制不改；实际完整73来源配置是待核root前件，当前仅SOURCE_ONLY_UNCOMPILED_UNRUN，16实际refs null/14flags false，零生成/编译/新性能。M2原stage03继续，已有M5实测、默认和八项未完成状态保持。

172新增源码交付：[JBP V1最终登记根核对](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/jbp_actual_capture_final_registration_root_consumption_v1.json)及[登记窄独审](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/jbp_actual_capture_final_registration_independent_metadata_v1.json)确认功能源码已补齐/封稳，仅SOURCE_ONLY、未编译/采集/运行，整包条件代码契约/接口审查现已由[根组合SOURCE审查](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/jbp_actual_capture_backend_final_root_composed_source_review_v1.json)及[组合独审](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/jbp_actual_capture_backend_full_independent_composed_source_v1.json)关闭，66/65安全身份闭合；实际前件仍缺。64/49安全身份及42→44→45登记链不授实际GTK/机器/费用/完整签名资格或性能；两模式仍需完整签名枚举，实际资源可行性未知。详细调用链、四项行政修复及证据边界见[172复盘](experiment_history/172_all_methods_experiment_campaign.md)。原M2同六stage继续，全八方向未完成，已有实测/默认保持；下文“后端未实现”保留当时阶段。

172 追加源码记录：J25 V2 的[根全文源码审查](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/j25_joint_source_v2_root_full_source_review_v1.json)及[独审](entry_method_exploration/20261003_all_methods_experiments_v1/b4/j25_joint_source_v2_independent_static_v1.json)已关闭 V1 原64MiB whole Export 与新增总RAM门的错配；完整 Export 限额恢复、额外内存全报。完整15源码/12AST/7科学体与原四点43控制保持，V1/HOLD原件保留。这是 SOURCE_ONLY 实现修正，22 项实际前件全 null；无新增实际预算/运行/Recall-QPS或默认改变。完整八方向实验及 JBP 真实采集后端仍待完成，下文旧修复进度保留历史身份。

172追加源码记录：[G1求解/五控制导出根源码审查](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/jbp_global_reference_solver_source_v1_root_full_source_review_v1.json)及[独审](entry_method_exploration/20261003_all_methods_experiments_v1/m4/jbp_global_reference_solver_source_v1_independent_static_v1.json)、[Inputs V2独审](entry_method_exploration/20261003_all_methods_experiments_v1/b4/jbp_global_reference_inputs_source_v2_independent_static_v1.json)及[原envelope部署范围勘误](entry_method_exploration/20261003_all_methods_experiments_v1/b4/jbp_global_reference_solver_source_v1_export_metadata_erratum_v1.md)，完整6源/原五控制/精确有理界/原格式byte接口仅SOURCE_ONLY，actual采集/模型/solver/native/perf全未运行。[J25新joint接线v1独审HOLD](entry_method_exploration/20261003_all_methods_experiments_v1/b4/j25_joint_source_v1_independent_static_hold_v1.json)记录新增接线cap实现错配，V1留存，V2另修；不改原方法结论、不新增性能结果。完整M2/M5/M4/C1-F2/B4与J25/J45/JBP仍未完成；生产E99/Web soft-t1/Y hard和既有实测不变。M2原同六stage作业仍在stage03 Web K1全Ω几何，未重启。

172新增源码记录：[J25 lower reference v3根源码审查](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/j25_lower_reference_source_v3_root_full_source_review_v1.json)及[v3独审](entry_method_exploration/20261003_all_methods_experiments_v1/b4/j25_lower_reference_source_v3_independent_static_v1.json)已关闭lower唯一全四first-freeze/full48四filter前端的源码缺口；原all6→原四lower SELECT硬链保持。v1差异文件runtime-map、v2把atime纳入首hash稳定性的SOURCE HOLD原件保留；v3只修稳定stat与行政身份，保留四lower/primary Y K1/20K/4096、全部48功能/23计数、8原价格和7 whole-plan。[JBP全局参考core根审查](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/jbp_global_reference_model_core_v1_root_full_source_review_v1.json)及[core独审](entry_method_exploration/20261003_all_methods_experiments_v1/b4/jbp_global_reference_model_core_v1_independent_static_v1.json)保持SOURCE_ONLY，实际完整输入/排他费用与签名资格、solver/bound/native导出仍待。J25实际all6/all4、唯一首锁及full48未运行，distinct12factor/provider/caller及完整Recall-QPS仍待；源码审通过不授实际资格或收益。

[M5 startup v7根源码审查](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/m5_cal_confirm_own_startup_v7_root_full_source_review_v1.json)及[v7独审](entry_method_exploration/20261003_all_methods_experiments_v1/m4/m5_cal_confirm_own_startup_v7_independent_static_v1.json)已关闭原CAL/confirm自有startup接线：同原gate/role/4096-prefix/source闭包后，同sealed memfd送原v9子进程，恢复后继续原warmup/五wall，phase→CAL→confirm消费同binding。v5遗漏context两路径键、v6遗漏相对目录引用的SOURCE HOLD保留，v7修正两项；原12job/16版本、有限非空S事前锁/全4-8 ledger、CAL1/80和confirm1/160保持。own registry/allpath/unsigned6角色+2profile/外部root六资格等实际前件仍null，未prepare/执行CAL或confirm。JBP unposted FIT1 v3源审保持；[JBP 44 post教师v2根源码审查](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/jbp_post_teacher_own_startup_source_v2_root_full_source_review_v1.json)及[v2独审](entry_method_exploration/20261003_all_methods_experiments_v1/b4/jbp_post_teacher_own_startup_source_v2_independent_static_v1.json)已关闭三项行政源码缺口：NONE哨兵、完整probe/unsigned来源根绑定、actual/expected SHA分列；v1 SOURCE HOLD原件保留。原140任务/44教师/20K/三tick及全部控制保持，实际own registry/六义务/all44 probe仍缺，未prepare或执行；真实FIT/求解/联合仍待。原M2同六stage作业仍在stage03；本次仅SOURCE_ONLY/安全元数据，完整八方向目标、已测结果和E99/Web软t1/Y硬默认保持。

172新增J45 v4源码收口：[根全文/身份审查](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/j45_fullcaller_v4_root_full_source_review_v1.json)及[独立静审](entry_method_exploration/20261003_all_methods_experiments_v1/m4/j45_fullcaller_v4_independent_static_v1.json)通过，原16×42/四点/四角色保持；近似provider、cached-R oracle、SHA bootstrap与四点typed empty集成，仅修非消费cache_schema标签并保留初封三文件。actual ELF/唯一实例冻结/完整cap/资格/42运行及联合性能未执行。原M2同六stage队列继续，完整八项目标/默认及已测Recall-QPS保持。

[172五方法与三联动实验](experiment_history/172_all_methods_experiment_campaign.md)仍ACTIVE：M5原16版本×四点SELECT完整native及原五stage评估已完成：Web @1冻结主候选Recall +0.146484pp、五轮配对QPS比中位+24.1638%，召回差描述95%区间[−0.341797,+0.634766]pp跨零；Web @100/Y @1/Y @100分别损失1.008301/1.757813/2.239990pp，虽提速但未达到主质量门。Web @1 missing_frequency简单控制达到相同Recall/392.316 QPS，主候选信息优势未建立。独立实现/GT/全强控制审计尚待，未执行CAL/confirm或切默认。 C1两集原ELF零query对象探针、A0/A1标量与A2自身batch4资格独审/实际汇总及root资格已闭合；原四组/clean补测完整packet和source核验后，按唯一clean Web @100/L1250首1024五wall总和全局冻结M0=scalar-span、Bcmp=strong166/span-batch4，两集共用。五wall总和依次20.380581246/18.781061241/15.852274359秒；其他点不参与选择。真实CLASSMAP/16384 witness/编图/replay及CAL尚未执行，未来不同ELF/角色仍须自有绑定。 B4原九stage first128及四点c/B已实际完成，完整source/terminal闭合、单线程无quota；Web K1(c=500,B=4928)、Web K100(625,5952)、Y K1(65,1152)、Y K100(129,2176)。c/B仅用原FIT0首128观察，不解码GTK作选择；完整20K全部七计划教师、原有限Π精确fit及JBP真实两阶段仍待。 M2实际geometry/check_all/formal与三联合接续仍待；M4/J45仅停冻结共同族准入，J25条件必要上界不冒充actual联合STOP。资源失败、迁卷、归档修正及重叠组原件保留；科学范围不缩。见[172当前报告](entry_method_exploration/20261003_all_methods_experiments_v1/report.md)。下文旧交接/历史阶段保持各自身份。

172新增离线实测进度：M2原core_v10两集全N exact-native96缓存生成及逐原ID检查已实际完成：Web N=2,505,000/d=512，Y N=10,000,000/d=200，均96B、sampled=false、实际线程1/无quota。原Web根/独审保持，[Y stage02根核对](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/m2_core_v10_y_fullN_actual_stage02_root_metadata_v1.json)及[Y独审](entry_method_exploration/20261003_all_methods_experiments_v1/b4/m2_y_fullN_actual_stage02_root_independent_metadata_v1.json)已闭合；cache/base payload未由根或metadata独审重读，payload SHA是producer声明。原同一六stage队列当前执行stage03 Web K1/L1000全部Ω几何；后四项Ω/compiler/checker与whole/root完整终态仍待。这是离线生成与检查进度，不是helper税或线上QPS。

172窄行政更新：C1/B4自有v14教师观察源已通过[独审/root全文复核](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/c1_b4_own_teacher_v2_root_full_source_review_v1.json)，原阶段具条件授权，新11/73 stage未prepare；M2实际终态、空窗及每真实教师自身对象/严格FP仍须闭合，原六/六十八科学任务不改。M5 CAL/confirm v2[源码复核](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/m5_cal_confirm_frontends_v2_root_source_review_v1.json)通过，actual saved审计/自有六义务/scope/IID仍待，零CAL/confirm。原README停点措辞另存[勘误](entry_method_exploration/20261003_all_methods_experiments_v1/b4/teacher_own_qualification_v2.observer_stop_erratum_v1.md)，不增加性能结果或默认资格。

2026-10-03[新对话交接同步](experiment_history/_maintenance/20261003_new_conversation_handoff/README.md)为行政文档维护，不增加172或新实验结果；最新理论记录171、最新实测166不变。当前五方法与三联动、阅读顺序和下一轮边界见[s-target.md](s-target.md#2026-10-03-新对话接续入口)，三首版/170四方案保留历史身份，171/170/DOCX封存不改。

2026-10-02 Git接续补充：[状态快照](research_snapshots/20261002/README.md)及[新候选说明](research_snapshots/20261002/current_method.md)保存169之后的对话提案。没有新实验编号或实测结果；最新真实性能166，167–169保持原理论研究身份。

当前结果以[summary.md](summary.md)为准，下一阶段以[s-target.md](s-target.md)为准。2026-09-22用户修订研究判定：历史STOP保留当时身份，不再因一个区间未过而永久禁止有价值的冻结复测。详见[新策略](entry_method_exploration/20260922_until2200_improvement_v1/research_decision_policy.md)。本页只索引，不代替原配置/结果/成本证据。

## 最新记录

| 记录 | 内容与边界 |
|---|---|
| [172 五方法与三联动实验](experiment_history/172_all_methods_experiment_campaign.md) | ACTIVE；J25四点discovery已封，六continuation DRAFT实际生成、cache SHA全null且未封/run；M2两集全N cache已完成、原stage03全Ω几何运行；余四Ω/checkers及whole/root终态仍待；J45 v4根/独立源码审查通过、actual未run；M5四点SELECT实测/评估完成、saved独审未run；C1全局primary与B4四c/B已冻，自有teacher源码/原阶段条件已审、新11/73未prepare；实际对象/FP与完整教师仍待；M4族必要门停止；完整八项交付未完成 |
| [171 夜间原作碰撞/证书接续](experiment_history/171_overnight_algorithm_collision_and_certificates.md) | 已研究至2026-10-03 08:00并完成纯理论交付；三首版后结合DOCX保留五机制，基础M2→M5→M4；三联合及all-plan补债重拟有完整冻结协议；首版参数/170/DOCX保持，0实验，native/创新/收益未知 |
| [170 Recall–QPS多机制算法理论](experiment_history/170_recall_qps_algorithm_theory.md) | 四个完整算法（联合动作码本/区间支持编译/容量闭包图手术/轨迹响应区域）、比较与前三最小冻结协议；手推交叉审查与原作排重，0实验，创新/收益未成立，最新实测166 |
| [169 GT10算法与CCF B论文理论](experiment_history/169_gt10_algorithm_paper_theory.md) | 完整算法/主稿、真实rank hard/median-t1 soft两图收益反转、actual质量/组件/完整费用链与原作/期刊审查；交叉手审，0实验，真实机制/投稿充分性未确认 |
| [168 代理/信息/局部证书理论](experiment_history/168_theory_proxy_information_local_certificate.md) | 已按16:00截止收口；GT10代理/多入口rank、局部搜索/原组证书、策略校准/完整费用经独立手审；0实验，真实前件HOLD，上午167封存保持 |
| [167 搜索响应与访问成本理论](experiment_history/167_theory_search_response_access_cost.md) | 理论/原论文与旧数组只读审查至13:00；安全闭包/返回类/成本门、三桶覆盖反证；0新真实性能，候选HOLD，已按13:00截止封存 |
| [166 冻结目标库曲线](experiment_history/166_target_bank_frozen_curve.md) | 36点/108轮wall；Web R1质量取舍保留，72跨预算比较无经验支配，有限核验结束 |
| [165 查询→真实目标迁移](experiment_history/165_query_target_transfer_online.md) | 主候选四点更慢、未获稳定综合收益；目标侧Web R1局部质量/速度取舍保留，独立核验完成 |
| [164 状态/rank完整在线验证](experiment_history/164_router_rank_pareto_online.md) | 四点Recall均值负、K100小幅提速但质量损失；独立核验完成，停止本固定版本，默认不变 |
| [163 Soft质量条件链](experiment_history/163_soft_mass_transport_pipeline_conditions.md) | 目标/温度→归一化→评分间隔→实际路由的保真条件；独立合成核验，0真实搜索/模型 |
| [162 单hub球界机会](experiment_history/162_single_hub_geometric_certificate_opportunity.md) | 双集fit20K均0通过、完整独立核验；停止固定球界，0新搜索/模型 |
| [161 hard质量区间证书](experiment_history/161_hard_mass_interval_certificate.md) | 独立盒内充要条件/两种tie穷举核验；0真实搜索，界与费用未知 |
| [160 共享完整构建身份](experiment_history/160_shared_batch_full_build_identity.md) | 六格实际费用、5/6身份恢复；Y新Default近并列跨hub改变W/图，旧质量不可拼接 |
| [159 精确标签批处理四格](experiment_history/159_exact_label_batch_and_rank_dispatch.md) | 固定微测费用比0.9796/0.3489，身份核验；0新ANN，不外推完整构建 |
| [158 Energy分数到搜索连接](experiment_history/158_energy_profile_routing_search_bridge.md) | 新源分数差下降13.3%/28.0%仍无稳定Recall增益；入口吸收与真成员计数核验，0新搜索 |
| [157 Energy两批新源验证](experiment_history/157_energy_selection_two_source_batches.md) | 同预算Uniform无稳定召回改善；Web对Default两点两批负，停止本版调参，保留成本候选 |
| [156 Energy实际完整构建](experiment_history/156_energy_selection_actual_full_build.md) | 原r0费用131.133/259.137秒，选择与四份画像恢复；0新线上性能，待四模型新源验证 |
| [155 无旧温度能量选样](experiment_history/155_energy_selection_without_exact_temperature.md) | 同预算训练方向误差少6.811%/23.330%，冻结信息门通过；0新性能，原r0完整构建待测 |
| [154 公平默认按需构建](experiment_history/154_fair_default_demand_build_cost.md) | 默认完整336.051/1519.754秒，同享QGT后混合仍省66.07%/84.01%；单次描述、身份恢复、0新性能 |
| [153 方向收益选样与简单控制](experiment_history/153_replacement_alignment_and_simple_control.md) | 主LOO未过双集门；Energy同预算训练方向误差少6.864%／23.330%，无新性能，旧温度依赖保留 |
| [152 温度与标签交叉项](experiment_history/152_temperature_label_error_interaction.md) | 固定r0分解与导数核验；温度更准不等于画像／Recall更好，0新性能 |
| [151 两批新源混合确认](experiment_history/151_frozen_hybrid_two_source_batches.md) | 主混合ΔR1/R100 Web−0.073/−0.023pp、Y−0.098/−0.023pp，保留成本候选、默认不变 |
| [150 两温度候选完整构建](experiment_history/150_temperature_candidates_full_build.md) | 两份冻结W独立恢复；主121.432秒含全20K教师，控制增量3.007秒，0新线上性能 |
| [149 温度CDF校准](experiment_history/149_temperature_cdf_calibration.md) | 温度MSE降78.96%，简单全近似中位数更好；0新画像/性能，后继须保留控制 |
| [148 按需QGT完整构建](experiment_history/148_demand_qgt_full_build_cost.md) | 114.023/243.072秒恢复同候选，消费前缀相同/未用尾部浮点差披露；0新线上性能 |
| [147 按需QGT依赖](experiment_history/147_demand_qgt_dependency.md) | 全5000只消费815/821行且H相同；0新GT/性能，实际按需费用待测 |
| [146 低标签完整构建](experiment_history/146_hybrid_full_build_cost.md) | 从无标签重建190.552/547.282秒，H/W/图恢复；0新线上性能，默认保持 |
| [145 画像到有限搜索的连接](experiment_history/145_profile_routing_search_bridge.md) | 小图变化与主搜索吸收分解；12原生反例，0新真实搜索/性能；二阶矩用语后补，原数值不变 |
| [144 标签替换与温度因素](experiment_history/144_hybrid_target_temperature_factorial.md) | 预定候选Web−0.049/−0.015pp、Y+0.146/+0.005pp，完整QPS接近；保留候选、费用未测 |
| [143 少量精确目标替换](experiment_history/143_partial_exact_target_replacement.md) | 2048直接替换使双集16种子方向误差均降，平均18.72%/11.44%；0新搜索/性能 |
| [142 廉价残差信息](experiment_history/142_cheap_residual_information.md) | 2048标签浅树使接受方差降约9%/26%；Y局部信息信号，0画像/性能 |
| [141 方向误差与补标机会](experiment_history/141_directional_error_and_sampling_opportunity.md) | 训练诊断：均匀切向补标门槛7462/9501；非均匀oracle有空间，0新性能，9月30日研究继续 |
| [140 近似贡献残差方差](experiment_history/140_approximate_target_residual_variance.md) | 只读训练统计，校正的向量MSE临界精确比例16.34%/42.58%；非Recall门，无新性能 |
| [139 近似监督费用依赖与纠偏](experiment_history/139_approximate_supervision_scope.md) | Web继承精确GT温度；费用限定与未执行的差值校正理论，0新性能 |
| [138 E125冻结Web复测与策略](experiment_history/138_e125_web_fresh_check_and_policy.md) | 新4096query，−0.1465pp/QPS−0.1044%；保留低成本候选，旧门不一票否决 |
| [137 E125近似目标构建费用](experiment_history/137_approximate_target_profile_cost_pilot.md) | 两集12点完整wall、标签费用显著下降；原旧门STOP，后继见138 |
| [136 目标预算全H余量](experiment_history/136_target_budget_fullH_opportunity.md) | 固定256-query完整单入口响应与迁移，oracle非部署收益 |
| [135 包含GT的默认构建成本](experiment_history/135_gt10_gt_inclusive_build_cost.md) | 5万exactGT恢复、H/W/图/路由核验，GT占核心97.9%/99.4% |
| [134 GT10画像方向稳定性](experiment_history/134_gt10_profile_direction_stability.md) | 同20K平分、置换和共同支持控制，非Recall保证 |
| [133 特权代理到真实决策分解](experiment_history/133_privileged_surrogate_decision_geometry.md) | 预测更准与真实效用改善并不等价 |
| [132 E124语义服务静态编译](experiment_history/132_semantic_service_linear_compile.md) | query-out未获净收益，已核验 |
| [131 E123目标服务特权门](experiment_history/131_target_service_privileged_gate.md) | 真实GT区域有正价值，非线上可用信息 |
| [130 监督稳定性与排序分解](experiment_history/130_gt_supervision_and_decision_decomposition.md) | 旧标签机制，非新增性能 |
| [129 E122动作图函数正则](experiment_history/129_action_coupled_ridge.md) | 结构信号存在，主候选仍低于默认 |
| [128 E121原路由状态表](experiment_history/128_router_state_table.md) | 有状态信号，主候选低于默认 |

此前叠加前言完整保存在[快照](entry_method_exploration/20260922_until2200_improvement_v1/reviews/root_docs_before_closeout/s-experiment.md)，下列历史表保持。

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
