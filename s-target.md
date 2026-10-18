<!-- E183_CURRENT_BEGIN -->
# E183 授权范围完成：七集与详细PDF收口（2026-10-17）

用户要求的全面测试与详细PDF已完成：七集含Deep/SIFT/GIST非多模态L2、645点/1935完整单线程批次，GT10和残差分项、全L、失败救损/分层/级联/频次/来源覆盖及费用均有原始证据和独审。[最终报告](entry_method_exploration/20261017_gt10_residual_comprehensive_v1/analysis/delivery_v2/report_zh.md) · [32页PDF](entry_method_exploration/20261017_gt10_residual_comprehensive_v1/analysis/delivery_v2/NETG_E183_GT10与残差_七数据集及失败查询_详细报告_20261017.pdf) · [状态](entry_method_exploration/20261017_gt10_residual_comprehensive_v1/state.json)。当前没有待恢复性能队列，默认仍E99 GT10。

实际判断：GT10可迁移至Deep/SIFT；当前静态残差在两集的测试源覆盖不足，GIST为路由/容量限制和混合收益；Web/COCO保留补全曲线收益，Flickr/Yandex不作普遍正结论。后续问题是合法新训练遗漏源能否覆盖未知失败，以及容量/可部署困难识别是否值得在线费用；本轮诊断不启动新模型、追加teacher、种子、门控或补测。新的研究问题另定范围，旧历史原件保持。
2026-10-18 简版交付：[四页PDF](entry_method_exploration/20261017_gt10_residual_comprehensive_v1/analysis/concise_v1/NETG_E183_NSG_GT10_残差_简版报告_20261018.pdf) · [简版文字](entry_method_exploration/20261017_gt10_residual_comprehensive_v1/analysis/concise_v1/report_zh.md)。每图仅NSG、GT10、GT10＋残差三线，另有统一L200失败查询表；315点全部复用既有结果，固定同家族B32，无新增实验，详细版保留。
<!-- E183_CURRENT_END -->

<!-- E176_CURRENT_BEGIN -->
# E176 当前目标与停止边界（2026-10-10）

**E176 本次授权范围已完成：两数据集已曝光公共10K、K1/K100、五L、八方法的160点/480完整wall批次，800比较/60机制及独立审计与报告实际完成；有限版本 STOP。** 默认保留 E99 GT10（Web soft-t1/Y hard），原 M5 保留。下方旧目标/STOP/预算文本完整保全，不作为仍在执行的队列。

本轮完成了原 M5 费用优化与原 M5 剩余遗漏补全，完整原 C没有被替换。M5OPT与原M5全部20点full packet逐词相同；M5RES12对原M5 14Recall升/6平/0降、12460成员救回/0损伤，按曲线两个点QPS中位数严格双升8/20（原配对口径9/20）。WebK100五L均有组合收益，但M5RES12对同成本基础M5OPT双升0/20，所有质量提升点更慢。PAIR对同在线上限route-only WIDE12仅1升/5平/14降，离线容量未配平；winner条件化、泛化机制与跨模态独有性均未被证明。

跨L只见两个原M5已覆盖的WebK1预算对，未解锁新K100/Y双升。同L对GT仅Y K100/L1200的弱点中位数信号（+0.0064pp/+0.082284%），不是全三轮更快，速度范围未分离。本轮只有既有public_test角色，无新确认、不推广未测L，不替换默认。完整原800比较及两种QPS中位口径均保留，不用后处理解释重新选策略。

用户新增授权是**本次每数据集额外900秒FIT**，实际Web469.143610秒/Y472.986268秒；旧TRAIN债不清零，累计Web22194.116446秒/Y16062.191988秒。实际900秒timer覆盖native/compiler完整child生命周期，后续manifest load/hash和行政收尾在计时外且未知费用保留null。它不是后续新fit额度，也不能将补全表训练说成0TRAIN。正式native6970.796179/7089.322895秒另列；嵌套阶段不重复相加，采样RSS不等于精确peak。

当前动作边界：不恢复任何旧runner/队列，不追加监督拟合、改方法或开始新确认，不改旧 E173/E174/E175 科学源、锁、raw与原历史结论。后续若获新研究授权，应首先分离等价工程优化与残差质量贡献，核完整wall及实际阶段费用，避免以未配平离线容量或已曝光公共角色证明创新/可靠替换；这些限制不是已启动的新方案或新门。

权威入口：[E176历史](/data/netg/ACSG/experiment_history/176_m5_residual_completion_curve_v1.md)、[冻结报告](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/analysis/final_v1/report.md)、[全部解释](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/analysis/final_v1/interpretation.csv)、[费用与未知边界](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/analysis/final_v1/cost_ledger_supplement.md)、[独立结果审计](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/reviews/independent_result_audit/report.json)、[最终交付复核](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/reviews/final_delivery_review.json)。[主曲线](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/analysis/final_v1/figures_delivery_v3/recall_qps_budget_curves.png)与[机制曲线](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/analysis/final_v1/figures_delivery_v3/mechanism_budget_curves.png)只连接五个真实预算点，原图和科学端点保留。
<!-- E176_CURRENT_END -->

<!-- E175_CURRENT_BEGIN -->
## E175有限扩展已完成，可靠综合收益目标尚未达成（2026-10-10）

本次用户授权的五L网格已全部执行：两集公共前10K、真实K1/K100、L=200/400/800/1000/1200、四法NSG/GT10/原M5/M5REG96，80点/240T1完整wall，0新增TRAIN。200比较、20全量机制、独立结果审计及PNG/SVG四panel、CSV/报告均完成。原M5保留在图中，GT10仍为当前默认。

M5REG96相对同L原M5：Recall17升3平、QPS20降，无同L双升。跨L仅WebVid K1的L800→GT1000和L1000→GT1200两组，两组原M5也已双升；区域扩展没有新增双升预算组合，WebK100/Y均无跨L双升。因此本轮完成的是预算曲线交付，未完成可靠Recall–QPS综合改进或默认替换。

**有限E175到此停止**；不根据本轮公共曲线继续追加L/cap、重拟合、训练或新角色。未来继续研究须有实质方法区别和另立冻结范围，优先验证额外候选工作是否能替代主图搜索支出；保留完整费用和原M5独立对照，并用未参与选择的确认数据检验综合收益。本轮已曝光公共单角色、20K TRAIN监督及原native-binding边界均不因增加预算点而消失。历史E173/E174 STOP和原件不回改。

交付：[曲线](entry_method_exploration/20261010_m5_region_budget_curve_v1/analysis/final_v1/figures/recall_qps_budget_curves.png)、[完整报告](entry_method_exploration/20261010_m5_region_budget_curve_v1/analysis/final_v1/report.md)、[协议](entry_method_exploration/20261010_m5_region_budget_curve_v1/protocol.md)、[终态](entry_method_exploration/20261010_m5_region_budget_curve_v1/state.json)。
<!-- E175_CURRENT_END -->

# ACSG 下一阶段目标

<!-- E174_CURRENT_BEGIN -->
2026-10-10：E174有限尝试已完成预锁112点/336批次、评价与独立审计。目标仍是可靠Recall–QPS综合改进；本轮没有达成主方法的两角色局部双升门。主M5REG96同L相对原M5为14点Recall增/2点平而全部QPS降；WebK1 b跨档正信号对应a负，且b原M5已具优势。**停止本冻结一跳/seed/cap版本**，不根据a/b响应追加参数、角色或门；不恢复旧队列。保留原M5研究与历史产物，GT10继续默认。新增TRAIN=0，历史每dataset跨方法TRAIN7200秒超额保留，不按K/role/阶段重置。

本轮确认有限表外真实救回：K100每点仅3–6个原20K TRAIN GT100并集之外的新增真成员，K1对应点为0；大量U外候选不等于净Recall或跨模态泛化。通用邻接扩展尚未隔离跨模态语义因素。后续理论应围绕如何利用M5已有的跨模态漏失信号，在保留质量的同时替代主搜索工作并支付全部附加费用；提出不同机制及可证伪的冻结合同后再安排新的有限试验。该方向不是已实现收益或本轮继续运行授权。见[完整报告](entry_method_exploration/20261010_m5_residual_regions_v1/analysis/final_v1/report.md)、[M5关系](entry_method_exploration/20261010_m5_residual_regions_v1/m5_relationship.md)、[独立解释](entry_method_exploration/20261010_m5_residual_regions_v1/reviews/result_interpretation_independent.md)及[当前入口](entry_method_exploration/20261010_m5_residual_regions_v1/README.md)。
<!-- E174_CURRENT_END -->

<!-- E173_CURRENT_BEGIN -->
2026-10-09：用户授权的 NSG/GT10/M5 两集五档 L 直接复测与曲线报告已经完成，见[最新结果](research_snapshots/20261009_nsg_gt_m5/README.md)。**M5 正在研究**；同L小幅提高质量但增加耗时，WebVid K1有两个离散跨L综合优势，Yandex增益很小。当前默认仍为WebVid GT10-soft-t1、Yandex GT10-hard；本次不自动改默认、不追加test调参或新训练、不恢复旧八方法队列。

本轮后续工作是结果/方法说明、图表与Git交接。若后续继续研究，先说明要验证的具体跨场景问题和预算；公共test不得转作调表选择集，已有历史训练超额不能通过本轮0训练回改。下文为此前阶段目标与边界。
<!-- E173_CURRENT_END -->

当前见[Git结论交接](research_snapshots/20261006_results/README.md)和[八方法详细报告](research_snapshots/20261006_results/report.md)，核实时点2026-10-06T21:32:45.619435+08:00。

每dataset跨全部方法TRAIN限7200秒；历史已超额，禁止新增训练。

继续原C1 WebK100剩余audit/compact/merge/双参照评价，再推进Yandex K1/K100；当前134/288 native、正式评价1/4。

第12行起均为历史快照；旧预算解释、旧运行状态与未执行描述不覆盖上述当前结论。


2026-10-04 最新用户约束：用户原话“一个数据集的训练预算是两个小时以内吧”。Root按当前多方法探索上下文解读为每个方法×单个数据集的累计训练／拟合不超过7200秒；这是root解释，不是用户逐字说了“每方法”。同方法同数据集的K1/K100、FIT0、FIT1、refit及全部轮次共用一项累计预算，不按K点、轮次或阶段重置。监督／标签生成、构建、验证分别计时披露；用户未确认整条离线流水线总成本也是7200秒。详见[训练预算约束记录](entry_method_exploration/20261003_all_methods_experiments_v1/m2/training_budget_constraint_20261004_v1.json)。

训练预算已确认，但累计账本、实际timeout与执行guard尚未实现或运行，精确cost-check上限仍null；此前1小时只是历史root工作假设。不能靠阶段改名规避用户拒绝天级工期，预计整条路线仍需天级时不推进。M2原stage03未进入训练；最近进程事实只引用root于2026-10-04 10:32:35（上海）的观察：PGID 90589/100130可逆SIGSTOP、原六PID T/Ts，partial proof仅STAT为129566205B／inode1319835／mtime10:32:32.040776279，原件保留、未终止或恢复、不是完整六stage成功。本次没有fresh进程／proof核实，挂起不能替代实际终态；见[此前成本挂起记录](entry_method_exploration/20261003_all_methods_experiments_v1/m2/runtime_budget_hold_20261004_v1.json)。

下一步先收口累计训练计时与硬限时执行方案、独立披露标签／构建／验证成本，并在训练前验证完整路线的合理工期；不得直接恢复原作业、把SIGSTOP当完整终态、绕过既有实际资格或启动新数值阶段。完整五方法三联动范围、原四点、角色、强控制与质量门保持。 [M2等价几何降成本源码独审](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/m2_exact_geometry_budget_source_v1_independent_static_v1.json)与[B4精确拟合降成本源码独审](entry_method_exploration/20261003_all_methods_experiments_v1/m4/b4_exact_fit_budget_source_v1_independent_static_v1.json)均仅条件SOURCE-only；两候选尚未执行，实际等价、提速及≤2h训练满足均未证明。saved-M5审计v1 canonical-state lease执行路线已被root拒绝；独立local-state只作静态建议，未实现或放行。

本段及新预算记录是当前约束；以下“预算待回复／pending”“1小时假设”“仍live／离线投入不限”等完整保留此前时点，不覆盖本次预算和挂起边界。


2026-10-04 10:32:35（上海）最新状态：下一步先明确可接受的单方法训练／构建／验证总工期，再评估更短的合法离线路径；用户已拒绝天级工期，具体预算仍pending，未采用任何询问选项。3–4天估计指M2全量精确证明与复核、不是已测训练耗时。当前M2原stage03已可逆SIGSTOP，partial保留、六阶段成功/root终态仍缺，详见[挂起记录](entry_method_exploration/20261003_all_methods_experiments_v1/m2/runtime_budget_hold_20261004_v1.json)。

完整五方法三联动目标仍ACTIVE，默认及原角色／参数／强控制不变。SOURCE-only等价优化（如重复精确几何复用、固定整数路径下的冗余变量处理）和合法任务重排仅待研究／独审，不承诺提速或达标；原wrappers仍硬等M2完整六阶段，独立M5审计或C1/B4先行如需调整依赖，必须另封行政版本并保留原科学门，不能直接绕过。挂起不等于串行终态或actual ready，不恢复／终止原进程、不启动新数值作业。下文旧“离线投入不限／不设省训练门”不能覆盖本次成本约束。


JBP own-startup V3的[根组合 SOURCE 审查](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/jbp_capture_own_startup_source_v3_root_composed_source_review_v1.json)及[独审](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/jbp_capture_own_startup_source_v3_independent_static_v1.json)已关闭 helper 完整来源图和当前→历史 stat 接线缺口，原两版/HOLD保持。下一实际顺序仍先完成 M2 全六阶段/root核验与串行空窗，运行原 M5 saved-record 独审，再按冻结依赖推进 C1/B4 全量教师与三联动。JBP后续在真实 B2 build接受、完整原角色桥、自有 image 静态 stops/layout/RTTI 与零评分安全证明、完整99来源绑定和既有跨卷 meter之后，执行当前image的首K1观察、独立监控join与root事实核验；随后另核正常全path/NUM_STATE/B-SIM/CapturedDC/排他费用/签名及完整capture。当前无 runnable config／新队列／实际资格，16refs null、16flags false；M2 live期间保持CPU0–5安全源码边界。原双K/40K/七计划/全E、σ、Γ与全5+3范围保持，目标仍可靠端到端 Recall–QPS 综合改进。

JBP构建SOURCE V2已获[根条件复核](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/jbp_capture_build_admin_source_v2_root_full_source_review_v1.json)及[独审](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/jbp_capture_build_admin_source_v2_independent_static_v1.json)，关闭V1终态来源分类与构建环境缺口；[V1 HOLD](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/jbp_capture_build_admin_source_v1_independent_static_hold_v1.json)保留。下一实际接续先取得原M2全六stage完整终态/root审查及串行空窗，再按原教师/build依赖核完整73来源实际配置和authority（代码最低直验capture44，不能接受真子集）、独立完整toolchain/16环境/GNU ABI、原跨卷meter及owner，执行真实生成/编译/完整unsigned输出并独立审查；随后每个新对象/机器/全域费用及capture仍另核。当前16实际前件仍null、14flags全false，未prepare/调用gate/生成/编译；M2 live期间安全源码边界保持。全五方法三联动和可靠Recall–QPS目标继续，默认不变。

JBP V1 [根条件整链SOURCE审查](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/jbp_actual_capture_backend_final_root_composed_source_review_v1.json)与[组合独审](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/jbp_actual_capture_backend_full_independent_composed_source_v1.json)已完成，无新确定源码阻塞；源码功能及接口接续已具备，尚未编译/运行，实际13前件全null/14flags全false。SOURCE阶段的8当前全文+1旧admin修正与外部sidecar独审组合不能授own机器/域/费/资源或采集资格。以下原执行关口保持：[最终登记根核对](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/jbp_actual_capture_final_registration_root_consumption_v1.json)与[登记窄独审](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/jbp_actual_capture_final_registration_independent_metadata_v1.json)已完成并保留窄范围；条件源码审查不直接准入实际build/capture。当前M2原六stage仍在stage03，先完成其全真实终态/root校验及串行空窗，再按原合同继续M5 saved-record实际独审、C1/B4完整教师和三联动。M2 live期间只推进安全源码/静态AST/行政文档，不调用target、gate snapshot、collector、prepare、compile、数值或native。

JBP下一实际链为原FIT0/FIT1/all44完整教师与各自own资格→新诊断image当前对象/全path/严格FP/NUM_STATE/B-SIM→完整原packet桥及root接受→独立排他primitive/六cold/完整lifecycle/layout与固定mode结构前件→完整监控capture→全部sidecar/数值或实际signature/外部factorability及真实monitor的root后验→原Inputs V2与五个同监督控制求解/原格式导出→实际plan+A/原Π重拟及SELECT/CAL/confirm完整wall。具体build/教师依赖按原阶段合同，不借旧ELF资格。两模式均保完整签名枚举；实际基数/资源未测，超界仅全范围UNRESOLVED，不改原E/σ/Γ/两K/40K/七计划/科学cap。13actual refs仍null，尚无实际采集/求解/新增性能。目标仍完整五方法三联动探索报告及可靠Recall–QPS综合改进，未达成、默认保持；下文旧UNIMPLEMENTED表述保留阶段身份。

J25 V2 已由[根全文源码审查](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/j25_joint_source_v2_root_full_source_review_v1.json)及[独审](entry_method_exploration/20261003_all_methods_experiments_v1/b4/j25_joint_source_v2_independent_static_v1.json)关闭原 Export cap 误作总 RAM 门的源码缺口，原 V1/HOLD 保留。下一步仍等原 M2 六stage完整终态/root核验和串行空窗，再完成原 all6→all4→唯一 first freeze→full48、当前自有 ELF/12 因素及 provider/完整实际预算，再冻结并执行原四点43控制的 SELECT，按原门接 CAL/confirm。不得将源码闭合或额外内存账本声明当实际资格，22 项实际前件仍 null。JBP 真实采集后端尚未完成，原实际 FIT/五控制求解/native/完整wall均仍待；全五方法三联合范围与可靠 Recall–QPS 目标保持。

下一实际缺口仍是全范围实验：[G1求解/五控制导出根源码审查](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/jbp_global_reference_solver_source_v1_root_full_source_review_v1.json)及[独审](entry_method_exploration/20261003_all_methods_experiments_v1/m4/jbp_global_reference_solver_source_v1_independent_static_v1.json)及[Inputs V2独审](entry_method_exploration/20261003_all_methods_experiments_v1/b4/jbp_global_reference_inputs_source_v2_independent_static_v1.json)仅关闭SOURCE_ONLY接续，未签实际输入/全路径fee/signature/预算/native或性能。M2完整真实终态与串行空窗后，继续原FIT0/FIT1/44 post教师及实际采集后端→完整root输入/当前布局→五控制同域求解与byte复核→native packet/完整费用→原SELECT/CAL/confirm；不因proxy最优改变角色/门/参数，也不以源码审代替真实实验。

[J25新joint接线v1独审HOLD](entry_method_exploration/20261003_all_methods_experiments_v1/b4/j25_joint_source_v1_independent_static_hold_v1.json)须在保留V1基础上另V2恢复Export-only64MiB并全报额外驻留/暂存费用，独审未闭合前不执行；[原envelope部署范围勘误](entry_method_exploration/20261003_all_methods_experiments_v1/b4/jbp_global_reference_solver_source_v1_export_metadata_erratum_v1.md)保持原envelope完整部署计账。完整M2/M5/M4/C1-F2/B4与J25/J45/JBP仍未完成；生产E99/Web soft-t1/Y hard和既有实测不变。M2原同六stage作业仍在stage03 Web K1全Ω几何，未重启。

下一接续源码门：[J25 lower reference v3根源码审查](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/j25_lower_reference_source_v3_root_full_source_review_v1.json)及[v3独审](entry_method_exploration/20261003_all_methods_experiments_v1/b4/j25_lower_reference_source_v3_independent_static_v1.json)已关闭lower唯一全四first-freeze/full48四filter前端的源码缺口；原all6→原四lower SELECT硬链保持。v1差异文件runtime-map、v2把atime纳入首hash稳定性的SOURCE HOLD原件保留；v3只修稳定stat与行政身份，保留四lower/primary Y K1/20K/4096、全部48功能/23计数、8原价格和7 whole-plan。[JBP全局参考core根审查](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/jbp_global_reference_model_core_v1_root_full_source_review_v1.json)及[core独审](entry_method_exploration/20261003_all_methods_experiments_v1/b4/jbp_global_reference_model_core_v1_independent_static_v1.json)保持SOURCE_ONLY，实际完整输入/排他费用与签名资格、solver/bound/native导出仍待。J25实际all6/all4、唯一首锁及full48未运行，distinct12factor/provider/caller及完整Recall-QPS仍待；源码审通过不授实际资格或收益。

[M5 startup v7根源码审查](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/m5_cal_confirm_own_startup_v7_root_full_source_review_v1.json)及[v7独审](entry_method_exploration/20261003_all_methods_experiments_v1/m4/m5_cal_confirm_own_startup_v7_independent_static_v1.json)已关闭原CAL/confirm自有startup接线：同原gate/role/4096-prefix/source闭包后，同sealed memfd送原v9子进程，恢复后继续原warmup/五wall，phase→CAL→confirm消费同binding。v5遗漏context两路径键、v6遗漏相对目录引用的SOURCE HOLD保留，v7修正两项；原12job/16版本、有限非空S事前锁/全4-8 ledger、CAL1/80和confirm1/160保持。own registry/allpath/unsigned6角色+2profile/外部root六资格等实际前件仍null，未prepare/执行CAL或confirm。JBP unposted FIT1 v3源审保持；[JBP 44 post教师v2根源码审查](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/jbp_post_teacher_own_startup_source_v2_root_full_source_review_v1.json)及[v2独审](entry_method_exploration/20261003_all_methods_experiments_v1/b4/jbp_post_teacher_own_startup_source_v2_independent_static_v1.json)已关闭三项行政源码缺口：NONE哨兵、完整probe/unsigned来源根绑定、actual/expected SHA分列；v1 SOURCE HOLD原件保留。原140任务/44教师/20K/三tick及全部控制保持，实际own registry/六义务/all44 probe仍缺，未prepare或执行；真实FIT/求解/联合仍待。原M2同六stage作业仍在stage03；本次仅SOURCE_ONLY/安全元数据，完整八方向目标、已测结果和E99/Web软t1/Y硬默认保持。

J45独立v4已完成[根全文/最终身份审查](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/j45_fullcaller_v4_root_full_source_review_v1.json)及[独立源码审查](entry_method_exploration/20261003_all_methods_experiments_v1/m4/j45_fullcaller_v4_independent_static_v1.json)，下一步先等原M2六stage真实whole/root终态、固定M5成功终态和串行空窗，再按原合同逐阶段核自有build/零query观察、完整原20K GT-free来源、实际ABI/allocator/完整cap与external预算，形成唯一四点cache部署冻结。source/build登记保持不变，所有role消费同一首次预算/前缀；后续CAL/confirm先核原角色准入，不由源码PASS或新的winner规则放行。每个真实对象及fresh评分factory、原lower provenance、fullword/strict FP/自有helper机器、JOIN/NUM_STATE/B-SIM/once/failure费用、完整42 wall/packet/quality仍须实际闭合。[近似provider](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/j45_approx_provider_source_root_full_review_v1.json)、[独立cached-R oracle](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/j45_cached_packet_oracle_source_root_full_review_v1.json)、[SHA bootstrap](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/j45_buffer_sha_bootstrap_source_root_full_review_v1.json)、[四点trace空结果](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/j45_trace_empty_results_root_acceptance_v1.json)已具各自源码或empty结构范围；trace proof未构造。尚无实际新ELF/queue/复用/性能；完整五方法三联动目标保持。

## 172五方法与三联动实验接续

J25下一步已具实际封签的四stage discovery queue（源v3、行政namespace v2）；原四点/primary Y K1保持。root又实际生成四点几何、全四汇总及route-word桥六个不可执行DRAFT，未来cache SHA全null，未封/未run。M2完成门v2已通过源码独审，但未调用且尚无实际完整终态/root审查；必须先关闭这个真实门并取得串行空窗，再运行全四lower收集、各自实际Ω完整几何/check_all及价格来源route-word桥，才可封SELECT。准备不关闭same-R/provider来源门或签actual联合STOP。见[discovery准备](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/j25_lower_discovery_actual_materialization_root_v1.json)、[六DRAFT实际生成](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/j25_lower_continuation_actual_draft_root_v1.json)及[M2完成门v2源码独审](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/m2_core_v10_terminal_gate_v2_root_independent_static_v1.json)。

C1/B4原教师自有startup源已获[独审及root复核](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/c1_b4_own_teacher_v2_root_full_source_review_v1.json)，root对[原C1 FIT阶段](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/c1_b4_own_teacher_conditional_phase_decisions_v1/C1_FIT_AFTER_M0_FROZEN.decision.json)及[原B4教师/精确fit阶段](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/c1_b4_own_teacher_conditional_phase_decisions_v1/B4_FIT0_TRUE_TEACHER_EXACT_POLICY.decision.json)签有条件继续；新11/73 stage仍未prepare。下一执行顺序先关闭M2实际六stage/fullN/allΩ/root审查、固定M5终态并取得串行空窗，再按各自零query probe/join及每个真实教师自有对象/严格FP/全word观察执行原六/六十八科学任务。C1止于两集全16384双K witness/compile/replay/graph seal，B4止于四点全20K/24列/三tick原有限Π model seal；之后另签CAL/confirm。新增行政费用据实计作业wall，[B4实际RET/返回地址勘误](entry_method_exploration/20261003_all_methods_experiments_v1/b4/teacher_own_qualification_v2.observer_stop_erratum_v1.md)不改原科学clock。M5 CAL/confirm v2[源码复核](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/m5_cal_confirm_frontends_v2_root_source_review_v1.json)仅关闭行政源缺口；actual saved-record v3/v9六义务/全四scope决定/IID仍待，无新CAL/confirm stage。

用户已授权“开始实验吧，把这些方法都探索一遍并给出报告”；完整范围M2/M5/M4/C1-F2/B4、J25/J45/JBP继续，目标是可靠完整Recall–QPS改善，默认保持、尚未达成。最新实测以实际receipt为准，下面171理论/旧暂停/旧期限均为历史，不能缩小当前授权。

1. C1两集原ELF零query对象探针、A0/A1标量与A2自身batch4资格独审/实际汇总及root资格已闭合；原四组/clean补测完整packet和source核验后，按唯一clean Web @100/L1250首1024五wall总和全局冻结M0=scalar-span、Bcmp=strong166/span-batch4，两集共用。五wall总和依次20.380581246/18.781061241/15.852274359秒；其他点不参与选择。真实CLASSMAP/16384 witness/编图/replay及CAL尚未执行，未来不同ELF/角色仍须自有绑定。 下一实际门为M2完整终态/空窗→原CLASSMAP→自身probe/join→每真实FIT自有startup资格→16384双K见证/编图/replay；M8按已冻Bcmp，其他数据点不参与再选。原风险/费用/角色与44格合同保持。
2. M5原16版本×四点SELECT完整native及原五stage评估已完成：Web @1冻结主候选Recall +0.146484pp、五轮配对QPS比中位+24.1638%，召回差描述95%区间[−0.341797,+0.634766]pp跨零；Web @100/Y @1/Y @100分别损失1.008301/1.757813/2.239990pp，虽提速但未达到主质量门。Web @1 missing_frequency简单控制达到相同Recall/392.316 QPS，主候选信息优势未建立。独立实现/GT/全强控制审计尚待，未执行CAL/confirm或切默认。 原metadata checker及四评估器全实际成功；先独立核GTK/mask/有效ID/完整packet、救回损伤/五wall与全部强控，明确旧plus外部桥缺失；再按原冻结协议决定CAL/confirm，不改表或挑控制。
3. M2四点完整20K Ω及8参考费用已冻结，执行全N exact-native96缓存、全部Ω factored几何/48B proof和独立全checker；后端32源独审v3已闭合first SELECT freeze全root成功链与future recipe/11因子进实际child前后；M2原core_v10两集全N exact-native96缓存生成及逐原ID检查已实际完成：Web N=2,505,000/d=512，Y N=10,000,000/d=200，均96B、sampled=false、实际线程1/无quota。原Web根/独审保持，[Y stage02根核对](entry_method_exploration/20261003_all_methods_experiments_v1/reviews/m2_core_v10_y_fullN_actual_stage02_root_metadata_v1.json)及[Y独审](entry_method_exploration/20261003_all_methods_experiments_v1/b4/m2_y_fullN_actual_stage02_root_independent_metadata_v1.json)已闭合；cache/base payload未由根或metadata独审重读，payload SHA是producer声明。原同一六stage队列当前执行stage03 Web K1/L1000全部Ω几何；后四项Ω/compiler/checker与whole/root完整终态仍待。这是离线生成与检查进度，不是helper税或线上QPS。 等待全六stage完整终态/root审查并核全部checker，再collect/freeze并将实际五份SHA交新plans producer v2；四filter分别生成singleton/full-plan完整计数、精确密度cap及参考准入，再签actual helper/source/caller后进入真正formal wall。不能用参考OFF推实际QPS失败。
4. B4原九stage first128及四点c/B已实际完成，完整source/terminal闭合、单线程无quota；Web K1(c=500,B=4928)、Web K100(625,5952)、Y K1(65,1152)、Y K100(129,2176)。c/B仅用原FIT0首128观察，不解码GTK作选择；完整20K全部七计划教师、原有限Π精确fit及JBP真实两阶段仍待。 原69stage已生成但未执行，经已审新73 stage适配器逐真实进程闭合B4 v14自身DC/严格FP/机器startup观察，root不得直接运行旧69队列；四旧FIT0 GT/row仅SHA读取例外单列。后续原68科学任务保留全部20K/七计划/三tick及budget/startup强控，精确原深度3有限Π fit；JBP按FIT0→FIT1全七missing→共享A→真实plan+A→原Π重拟，监督匹配40K默认、SELECT固定J03、CAL只accept/reject。
5. M4两集全81,920,000 keyfree配对均排除，独审支持STOP_THIS_FROZEN_COMMON_M4_FAMILY_SELECT_ADMISSION；不改17原轴/尺度重开。J45原四lower-L点的原共同族几何lineage已封签/独审，root已STOP_THIS_REGISTERED_J45_COMMON_FAMILY_SELECT_CERTIFICATE_HIT_ADMISSION；只关闭固定SELECT证书命中机会，lower-L response/recipe、实际目录及普通融合/缓存/miss caller与R+C完整费用另核，不记整个联合失败。J25原范围为Web K1/L800、Web K100/L1000、Y K1/L100、Y K100/L200四个lower-L点，primary固定Y K1；各点独立原Ω/几何/费及盲SELECT/actual caller，不将L0产物重命名。Y K1 same-R/same-U/≤24条件类的必要质量上限尚欠69成员；当前实际联合same-R与provider来源门未闭合，不记actual J25 STOP、不取消四点准备。

所有正式CPU15实际1线程、串行完整wall，新增费用全部计入；5轮基础/7轮联合确认、最强简单控制、配对不确定性、成员救回/损伤与源窗口限制据实报告。参数/角色/科学cap不反馈改动；原2.5GiB资源事故只另签行政12GiB修复并保留失败产物。逐项关闭合法停止或完整评测门，再交报告；整个范围未完成时不标complete。

## 2026-10-03 新对话接续入口（171历史阶段）

用户在08:00理论交付后要求“同步信息到相对应的文件里，然后我要开启新的对话了”。本次仅同步交接文档，不增加实验编号，不修改171封存目录、170原件或指定DOCX；[同步记录与身份核验](experiment_history/_maintenance/20261003_new_conversation_handoff/README.md)另存。下文三首版、170四方案和历史截止时间均保留原身份；**当前总交付为五种机制，联动不另计方法数**。

**当时状态**：171为`COMPLETED_THEORY_ONLY_NO_EXPERIMENTS`，不是Recall–QPS项目目标已达成。最新真实性能仍166；生产E99、WebVid GT10-soft-t1、Yandex GT10-hard保持。五方法均未实现，未产生新模型、表、证书或图；实际程序/数值/状态合同为`THEOREM_ONLY_UNBOUND`，创新、可靠收益及CCF B投稿充分性均未确认。原08:00研究期限已经结束；本次同步不授权实验或恢复历史runner。

新会话阅读顺序：

1. 先完整读`AGENTS.md`、`summary.md`、`spec.md`、本文件、`s-experiment.md`；以各文件当前顶部决策为准。
2. 再读[最终五方法与联动合并报告](entry_method_exploration/20261002_overnight_algorithm_audit_v1/combined_report.md)，这里是全部八项方案、比较表、前三排序与DOCX去重的总入口。[171详细记录](experiment_history/171_overnight_algorithm_collision_and_certificates.md)保留形成过程；阶段措辞不覆盖最终状态。
3. 原三方法的IO/离线与在线步骤/公式/完整伪代码在[独立三首版报告](entry_method_exploration/20261002_overnight_algorithm_audit_v1/report.md)及[current_algorithms.md](entry_method_exploration/20261002_overnight_algorithm_audit_v1/current_algorithms.md)。它们只定义M2/M5/M4；C1-F2必须另读[图编译完整稿](entry_method_exploration/20261002_overnight_algorithm_audit_v1/docx_c1_graph_comparison.md)，B4必须另读[有限前沿完整稿](entry_method_exploration/20261002_overnight_algorithm_audit_v1/docx_b4_complete_method.md)。
4. 联动先读[组合语义、条件证明和全费用合同](entry_method_exploration/20261002_overnight_algorithm_audit_v1/joint_composition_contract.md)，JBP再读[全部七计划missing→共享A→重拟π的两阶段方案](entry_method_exploration/20261002_overnight_algorithm_audit_v1/joint_policy_posting_two_pass.md)和[同信息全局代理强控制](entry_method_exploration/20261002_overnight_algorithm_audit_v1/joint_policy_posting_global_proxy_control.md)。
5. [原三方法冻结协议](entry_method_exploration/20261002_overnight_algorithm_audit_v1/frozen_validation.md)、C1稿内的独立协议、[三联合冻结协议](entry_method_exploration/20261002_overnight_algorithm_audit_v1/joint_frozen_validation.md)分别保留，不互换L、CAL/确认计数、caller或置信族。完整性与未知项见[最终要求审计](entry_method_exploration/20261002_overnight_algorithm_audit_v1/research_requirement_final_audit.md)及[171封存状态](entry_method_exploration/20261002_overnight_algorithm_audit_v1/state.json)。这些是未来验证设计，不是执行授权或已具备数据。
6. 根据所讨论方法回查详细实验卡及其原协议/结果，并沿调用链读实际源码。先核[本地源码身份](entry_method_exploration/20261002_overnight_algorithm_audit_v1/local_source_identity_refresh.md)和[Faiss本地补丁](research_snapshots/20261002/faiss_worktree.patch)，不能只用上游gitlink。指定743ee8c61b8dce435e51a77546b7d784635f1fc8在本地缺失；本轮实际HEAD为96cf05d5410cf51272048cd1f90b4bb194e23c62。本地身份与请求快照的差异已记录，不用云端Git替代或自动切换工作树。

基础推荐顺序为**M2→M5→M4**，保留另外两条独立机制：

- **M2保序区间评分省略**：离线编译有序物理邻接区间的支持界，在线仅在实际阈值/native/状态证明齐备时跳过整组；原route/init、满池前评分及全部metadata/prefetch费用必须支付。首版每(dataset,K,L0)64MiB；几何界不直接证明实际保真或QPS。
- **M5残差posting补输出**：由训练GT和正常lower-L实际响应的missing生成共享slot表，新query只用合法在线key查表，对R与最多24个新增候选一次RESCORE/选择。共享双K表128KiB；每个K分别偿还lower-L质量债务及完整访问/评分/输出税，weighted覆盖不是双K保证。
- **M4完整响应证书复用**：离线证明全执行分支/原输出recipe，在线付费定位单key的一cell，检查当前query成员资格并按原recipe评分；首版17尺度、16MiB。RMS定标不保证32-peer覆盖，实数区域、集合相同或理想概率均不直接证明实际COMMIT/新query覆盖/支付。
- **C1-F2两类行末义务图编译**：保护训练实际搜索的行末pool义务和保守整行fallback，独立改变底图而非入口替换。前作碰撞及新query损伤风险仍待解决；行末证明不能直接移植B4的partial cap，新图须重编译关联metadata并匹配图控制。
- **B4有限预算独立前沿**：在已冻结c/B与七计划内选择继续或预算分叉，branch各自seen/pool，仅共享score-only memo；当前query资格、DEFAULT_ONLY/NATURAL及失败均纳入总体费用。memo只可能节省跨S0/S1重叠请求，不节省S0首次请求；七标签别名、逻辑cap与原init位置语义均须保持。

联动推荐为**J25（M2+M5）→J45（M4+M5一次评分融合）→JBP（B4+M5全部七计划补债后重拟）**。J25须在lower-L重签M2并保M5可见状态；J45用无评分认证ID包与R+C的单次reference评分/提交，最强简单控制包括合法缓存与融合；JBP先FIT0冻计划和π0，再FIT1用全部实际计划missing造一张A、永久冻A后按plan+A的真实质量/完整费用重拟π1，不回流CAL。组合不能相加组件QPS、重复计救回或省掉失败/后续query状态；组件正确性是前件，组件独立性能PASS不是联合验证的必要门。

下一轮若仍研究理论，先检查实际绑定缺口、最强同信息简单控制及联动新增步骤是否足以区分前作；只做文档、论文、静态源码与手推。若用户另行明确要求实验，再据对应独立协议冻结数据角色、实际caller和计费身份。未来统一单线程、方法串行、完整wall；分别报告真实Recall@1/@100、QPS、重复波动、配对不确定性及救回/损伤，在未参与选型的数据上确认，原默认获同等优化机会。离线投入不限；一升一降先记取舍，不以MSE/NDC/几何/oracle/构建费用宣告综合改善。缺实际程序、数据或角色身份即HOLD，不通过调seed/阈值/预算重启失败版本。

可复制到新对话：

> 接续本地 `/data/netg/ACSG` 的171理论交付。先完整读AGENTS.md、summary.md、spec.md、s-target.md、s-experiment.md，再按s-target.md“2026-10-03 新对话接续入口”读combined_report.md及各完整方案/联动合同。当前五机制M2/M5/M4/C1-F2/B4，基础前三M2→M5→M4，联动J25→J45→JBP；最新实测仍166，默认E99/Web软/Y硬不变。先继续理论与静态分析，不启动训练、GT、构图、ANN、性能、合成数值、旧数组新统计或历史runner；不改171/170/DOCX封存，不预设创新和Recall–QPS收益成立。原三首版参数与各联合冻结协议保持独立；按照现有总报告具体查缺口和强对照，不重新做方向清单。

## 夜间理论与DOCX联动分析已于2026-10-03 08:00完成

最新用户“先分析吧，有些方案可能联动起来更好，分析分析，到早上八点”的期限已按2026-10-03 **08:00 Asia/Shanghai**完成。[171协议](entry_method_exploration/20261002_overnight_algorithm_audit_v1/protocol.md)为COMPLETED_THEORY_ONLY_NO_EXPERIMENTS，“给出理论方法，先不进行实验”保持；其后只行政封存，不自动执行未来协议。170及更早封存保持；历史13/16/22/06点不恢复为本轮计划。

三首版闭合后已只读提取指定[DOCX](entry_method_exploration/20261002_gt10_paper_theory_v1/ACSG理论研究报告与最小验证协议_2026-10-03.docx)，原件与563个公式结构保持，[来源/身份](entry_method_exploration/20261002_overnight_algorithm_audit_v1/docx_review_source.json)可核。C1-F2与B4作为图编译/独立有限前沿的不同机制补充审查；JAC/UCS与M1/teacher消融合并，D3与M2安全评分类竞争而不凑数。当前未根据DOCX直接改首版或宣布创新/收益。

新增[联动接口与证明/费用](entry_method_exploration/20261002_overnight_algorithm_audit_v1/joint_composition_contract.md)、[B4完整方案](entry_method_exploration/20261002_overnight_algorithm_audit_v1/docx_b4_complete_method.md)、[B4+M5两阶段反向质量债务方案](entry_method_exploration/20261002_overnight_algorithm_audit_v1/joint_policy_posting_two_pass.md)。先核M2+M5的同输出支付链、M4+M5认证ID包的一次评分提交、C1实际类图metadata重编译及M2/B4 logical cap/cache origin义务；不把组件wall/QPS收益相加。联合策略再拟合是另立未来版本：FIT0冻Π/π0，FIT1用全部七实际计划missing造一张A、冻A后按真实plan+post重拟π1，不回流CAL，不回改原冻结项。[合并五方法报告](entry_method_exploration/20261002_overnight_algorithm_audit_v1/combined_report.md)保留M2/M5/M4/C1-F2/B4，[三优先联合最小协议](entry_method_exploration/20261002_overnight_algorithm_audit_v1/joint_frozen_validation.md)已列完整费用/强控/来源/配对族。基础推荐仍前三，联合推荐J25→J45→JBP；已完成交叉审查及纯理论交付，0实验。

[独立三首版交付](entry_method_exploration/20261002_overnight_algorithm_audit_v1/report.md)及[统一首版伪代码](entry_method_exploration/20261002_overnight_algorithm_audit_v1/current_algorithms.md)保留三个机制，推荐M2保序区间评分省略→M5残差posting补输出→M4响应证书复用；结合DOCX后的当前总交付为上方五方法报告。M1整体动作和M3容量cut/add因原作重合及有限搜索反例降为强控制，不否定其整体路线；容量约束服务归属仍仅提案。所有创新和真实收益未知。

已补M2唯一64MiB artifact合同、精确整数几何checker、方位/恢复/离散/native裕量分层及满池前必付评分；M5固定lower-L质量债务/RESCORE税、activation非次模和新query迁移/置信族；M4全执行响应覆盖、同caller负IP输出recipe、集合/quiet/格点域边界和全库几何控制。整批epoch/counter/FP反馈与actual比较均单列前件，专题稿和独立审查索引留报告。它们未生成表、证书、价格、数据角色或实现，也不改首版冻结项。

最近补齐[M5共享双K/整数可行性](entry_method_exploration/20261002_overnight_algorithm_audit_v1/m5_joint_support_and_integrality.md)及[source有限main见证](entry_method_exploration/20261002_overnight_algorithm_audit_v1/m5_integrality_finite_main_witness.md)、既存H815/821的[完整字段装载见证](entry_method_exploration/20261002_overnight_algorithm_audit_v1/m5_static_table_storage_admission.md)、[R首ID强控制](entry_method_exploration/20261002_overnight_algorithm_audit_v1/m5_return_key_posting_control.md)与[只读visited过滤](entry_method_exploration/20261002_overnight_algorithm_audit_v1/m5_original_neighbor_row_redundancy.md)。它们深化M5而不加方法数/改首版；GAR/SATURATE等具体前作已有相关工具，新增信息/表/当前评分和失败税全计。已手推的质量或结构性可装载不推current native、actual router、迁移或QPS，未来所有简单对照获同合法优化机会。当前仍0实验。

到期前已审阅裕量与helper分支、评分省略上界与完整付费、监督/在线可見信息、最强简单控制、当前q资格/默认回退与RMS覆盖/跨branch复用机会。实际canonical binary/helper/FP/address/comparator/caller、query分布/IID、费用J及真实覆盖/迁移保持未知，不以独立手审或参考正值替代。后续先按已写协议绑定与冻结；没有新的实验执行授权或自动runner。

[前三最小冻结方案](entry_method_exploration/20261002_overnight_algorithm_audit_v1/frozen_validation.md)只列未来验证：单线程/方法串行、完整wall与五轮、四主工作点、配对不确定性和救回/损伤、默认同机会、未参与选型双来源确认。当前0训练/GT/构图/ANN/性能/合成数学/旧数组新统计，不恢复runner；新源读取、构表及验证待后续实验任务。最新实测166及默认生产E99/Web GT10-soft-t1/Yandex GT10-hard保持。

## 170历史阶段：四个理论算法已交付，实验保持未启动

2026-10-02用户本次要求先广泛探索理论并交付3–10个完整方法，随后强调“给出理论方法，先不进行实验”。[170完整交付](entry_method_exploration/20261002_recall_qps_algorithm_theory_v2/report.md)保留四种机制；下文13/16/22点及旧runner均是历史边界，不约束或授权当前任务。范围已扩展到入口、评分执行、图与响应辅助结构；原入口替换路线仍固定底图/主搜索便于归因。

170当时推荐的最小验证优先级为：①M2有序邻接区间支持函数编译，先建立native包络与原组保真，再问metadata/查表能否支付；②M1完整三入口动作码本，先检真实joint信息相对同S/同监督简单控制，再问native分区迁移及fallback税；③M4完整轨迹响应区域，先完成比较见证/原输出recipe和非空区域，再问新来源覆盖与完整支付。M3容量闭包cut/add图手术保留第四，须先排除PIGR等价与闭包支持不足。这是保留的历史排序；当前采用171五机制及M2→M5→M4/J25→J45→JBP，不把历史排序恢复成当前计划。排序是验证优先，不是已成立收益或论文充分性。

[共同冻结方案](entry_method_exploration/20261002_recall_qps_algorithm_theory_v2/frozen_validation.md)已具体列前三参数、四主点与附加预算、强控制、1线程/方法串行/完整wall/5轮、真实R1/R100/配对不确定性/救回损伤及未参与选型来源确认。算法未实现，证书/监督/模型/图未生成，当前没有实验GO。容量约束归属已单独审查：并集容量和不保证top3覆盖/GT100，保留M1可选teacher审查而非独立主线。

当前完成的是理论交付；可靠Recall–QPS主目标仍未达成，CCF B充分创新仍未确认。离线投入不限，不设省训练门。最新实测166，默认生产E99/Web GT10-soft-t1/Yandex GT10-hard不变；后续执行必须来自新的用户实验指令，不自动恢复任何旧作业。

## 下列为既有阶段原计划与边界

2026-10-02对话后补充候选：[容量约束图服务归属](research_snapshots/20261002/current_method.md)。拟用同一评分阈值下的容量受限可达组件替换几何归属，保持原画像规模和线上三入口链；下一理论门是联合容量前件、预测top3覆盖/跨query迁移以及相对E08/E28的实质区别。候选尚未实现或实验，不把理论条件当完整QPS保证；本次Git整理不授权训练或性能测试。

## 当前目标：可靠的 Recall–QPS 综合改进

2026-10-02用户追加“具体算法和创新点，或完善GT10理论支撑B刊”，已确认**CCF B类期刊**。[169独立任务](entry_method_exploration/20261002_gt10_paper_theory_v1/protocol.md)选择GT10论文理论路线，完整算法/主稿、真实rank正反构造（hard与median-t1 soft）、actual质量/组件/完整费用链和前作审查已完成手推与交叉手审；不是新方法性能GO。下一论文门为重要且不被前作覆盖的方法区分、真实rank–图服务解释力和独立来源完整Recall@1/@100–QPS证据，详见[证据清单](entry_method_exploration/20261002_gt10_paper_theory_v1/evidence_gate.md)。当前仅理论稿及既有证据，不能保证CCF B发表；未启动上述测试，不自动恢复旧runner，最新性能166和现行默认保持。

2026-10-02下午新授权研究至16:00，**先完善理论，不开始实验**。[168协议](entry_method_exploration/20261002_theory_until1600_v1/protocol.md)独立于上午167：GT10代理/实际响应、局部返回保护、原评分组证书、可见信息/策略校准及收费决策已完成条件推导、前作对照、独立手审与交接，已按16:00截止收口。[命题台账](entry_method_exploration/20261002_theory_until1600_v1/proof_ledger.md)记录未知真实前件；没有实现或性能GO。0真实/合成实验、枚举、旧数组新诊断、训练/GT/构图/性能，不自动推进后续工作。旧性能暂停与上午原件保持；默认/生产E99不变，最新实测仍166。

最新训练费用口径：“不需要节省训练时间甚至可以增加训练时间，但是综合qps recall要提高”。可以用更充分的离线训练、合法监督和完整metadata准备换在线收益；不设省训练门，不以拟合/构建便宜判成功。目标仍是完整在线Recall–QPS，线上获取/推理/访问/路由/搜索/输出全部计费，同机会最快默认不能省。本轮仅研究上述可能性，不执行训练或metadata构建。

当前保留两个理论对象：[把同部署合同联合动作的相对质量/完整费用压缩为便宜可见表示](entry_method_exploration/20261002_theory_until1600_v1/decision_information_theory.md)，以及[更重事前metadata支持逐ID保真的完整原组拒收](entry_method_exploration/20261002_theory_until1600_v1/certified_group_elision_theory.md)。[离线投入说明](entry_method_exploration/20261002_theory_until1600_v1/offline_training_and_online_gain.md)明确更多训练/更紧实数界均不保证线上净收益；已有直接前作和本地同监督方法不换名重启。二者缺真实可得性、迁移/数值、覆盖率及共享最快默认后费用，继续HOLD。

2026-10-02新授权：先探索完善理论或可改善完整Recall–QPS的方法，可以阅读相关论文，至今天13:00（Asia/Shanghai，UTC+8）。本轮独立版本[20261002_theory_until1300_v1](entry_method_exploration/20261002_theory_until1300_v1/protocol.md)已冻结：历史实质差异与原论文对照、有限搜索效用条件/反例、目标库访问费用及仅旧ID/slot/响应的只读可行性诊断；形成一个有最强简单控制、全费用条件和结束门的方法方案。0新真实ANN/NSG、GT、训练、画像/图、正式性能，不读新源query/held-out。原9月30日runner/22:00计划不恢复，性能实验仍暂停；默认与生产E99保持。本轮已于13:00结束并封存，未确认项保持HOLD。

本轮[167理论与方法结论](entry_method_exploration/20261002_theory_until1300_v1/report.md)已把四候选具体化。优先问题是原路由内native距离memo能否严格保输出、计全部缓存费用，并超过原版/UpperHandoff/同memo Default3中更快者；真实重复trace和matched full wall缺失，保持HOLD。安全提前拒绝需原ef阈值/native区间和费用证明；三桶旧slot覆盖低，未产生新选择/响应；直接20Kraw-target访问与rank1/2联合需真实联合反馈及访问前件。见[最小控制/结束门](entry_method_exploration/20261002_theory_until1300_v1/candidate_gates.md)。不因此授权性能，不扩旧失败版ef/模型/seed/桶数/样本。

2026-09-30用户更新目标：“我们的目标是可靠的 Recall–QPS 综合改进”。后续研究以相对当前默认的、可复现且有实际意义的完整线上Recall–QPS改善为成功标准。理论分析、论文阅读、入口选择和模型设计服务于这一结果；不以完成某个实验或某种方法作为目标完成。

- **综合收益**：按事前声明的工作区间、召回/吞吐要求和比较方式，验证更高QPS或更高Recall带来的实际前沿改善。两者同时提高是直接证据；一升一降只记为取舍，须进一步证明目标工作区间内的净收益。全部比较保留真实工作点，不用插值或更换阈值制造成功。
- **可靠证据**：冻结方法和数据角色后，真实测量Recall@1、Recall@100与完整端到端QPS；统一单线程、串行比较，新增信息获取、推理、路由、主搜索和输出都计入wall。报告效应量、配对不确定性、救回/损伤及重复计时波动，核验实现/GT/身份。候选须在未参与选型的查询来源复核，在声明适用范围的相关工作点验证；WebVid/Yandex均保留完整结果，单集收益只作该集结论，不要求所有探索点同时显著。
- **研究优先级**：训练和构建成本是附属指标，可以增加以换取线上收益。构建更便宜、训练误差更低、入口几何更好或NDC更少，均不替代线上综合收益。测试前固定最小有意义收益、比较范围与结束边界，不在反馈后不断追加至通过。有价值但不确定的局部信号可保留，不把它写成已达成可靠改进或默认替换。

当前判断：尚未达到这一目标，原默认保持。9月30日暂停后的目标更新没有恢复旧实验；10月2日上午与下午理论阶段分别已按13:00/16:00截止，后续169算法/论文任务也只有理论与文档；不自动进入实验，不重新启用原22:00时限或旧性能runner。

2026-09-30 19:44按用户“先停下来”暂停。当前无后台实验，原22:00推进安排暂停；已完成至记录166并封存。目标桶粗筛仅保留设计，未实现或运行，默认不变。

历史任务最初授权2026-09-30理论、论文与小实验研究至22:00，19:44已暂停；17:44明确的优先级继续有效：**构建成本不是优化重点，重点是完整端到端QPS和Recall综合提高。** 默认仍Web GT10-soft-t1/Yandex GT10-hard、生产E99。已完成记录141–166保留；费用下降、训练方向误差下降或数学条件核验都不等于主目标完成。[本次目标修订](entry_method_exploration/20260930_theory_until2200_v1/online_priority_steering.md)。

## 优先一：找到能改善实际 Recall–QPS 的方法

入口选择是当前研究路径；评估这类方法时保持底图、主搜索、每个比较点的L、展开和停止规则。先从历史详细记录核对信息是否已用、动作是否相同、监督/工作预算是否对齐，再锁一个能被简单控制推翻的假设。具体路线按其对最终综合收益的证据排序，不以模型名字或oracle余量代替证据。

[164状态到相对rank版本](experiment_history/164_router_rank_pareto_online.md)已结束并通过实现审计：四点Recall均值负、两个K100描述区间负，State未形成相对固定/置换/六特征的稳定综合增量。按冻结协议停止本版，不增状态/trace/支持阈值/深度/L/样本/seed继续调。它关闭E126原目标预算/完整wall缺口，不支持默认替换，也不证明所有入口信息都无用。

[165查询→真实目标迁移](experiment_history/165_query_target_transfer_online.md)已完成六方法完整wall及独立核验：主候选四点QPS都降，Web召回微正不确定、Y均值负；停止固定版本的案例数/ef/近邻数/GT数/模型调参。Web配对信息相对打乱有效，但没有超过默认和目标侧控制。目标侧Web R1的+0.537109pp/−0.8156%QPS取舍独立保留，未证明同Recall更快，不自动追加新源或切默认。

[166冻结曲线](experiment_history/166_target_bank_frozen_curve.md)已完成并核验：目标库Web R1三个L的正质量均值保留，但12个同预算点均更慢、72跨预算比较无经验支配；四组合最快实测90%点不加速。结束本项，不扩L/ef/样本/重复。原查询迁移不重开，默认不变。

暂停期间保留一个尚未实现、仍待评估的[目标库粗筛访问机制](entry_method_exploration/20260930_theory_until2200_v1/research/target_bank_coarse_access_design.md)：原GT10路由筛目标桶，再做raw目标精排。训练桶大小已只读核算；粗细/监督分桶已有IVF及学习路由前作，不能包装成独立创新。尚无runner或性能结果，只有在访问费用与最小控制明确后另立冻结小实验。

## 优先二：用真实目标预算与完整wall验证综合改善

只在具体信息假设与最小控制明确后制定小实验。数据角色、方法、预算与结束边界在读反馈前冻结；只测真实Recall@1/@100，K100要求L≥100，CPU15实际单线程、方法串行、完整路由+主搜索+输出wall。训练/缓存中的graph-only时间、NDC、预测MSE和插值预算不能冒充线上QPS。

探索与默认替换分开。非劣区间未通过记为证据不足，不一票否决有实际价值的方向；同时保留明显损伤、跨来源/工作点差异和费用。旧版本门与结果不回改，新源一经观察不再参与后继选型。固定模型、同监督简单控制和独立实现核验先于负结果归因。[研究判定策略](entry_method_exploration/20260922_until2200_improvement_v1/research_decision_policy.md)。

## 优先三：理论解释服务于真实搜索效用

163已补全目标/温度→平均归属→归一化→评分间隔→实际路由→固定搜索的保真条件，不能由此推出超过默认的Recall或完整QPS。下一理论重点是廉价可见信息能否预测相对默认的救回−损伤，并支付全流程新增费用；通用统计/运输/球面均值工具明确注明前作。

单球/单hub证书162在两集各20K均无通过机会，固定版停止；Energy157在新源上相对同2048预算Uniform无稳定Recall改善，停止特征/深度/seed/温度/预算调参。141–160的低标签费用候选与全部数据保持，不作为当前首要优化路线。未执行的target_mass_compression_v1因目标纠正取消，不把取消当方法反证。

## 资源与交接

以下是已暂停的9月30日作业历史边界，保留审计身份；未来恢复时重新确定时间与资源预算，不将原时限视为正在运行的计划。

全部旧源码、模型、图、GT、日志、标签及seal保留；每项新工作独立版本与manifest。164前自定新增上限由1GiB增加64MiB；新迁移阶段构图前再增加192MiB，总上限1.25GiB，原阶段协议保持。空余6GiB继续检查，新阶段编译/构图300秒、搜索1800秒且21:00前结束；21:30后不启动可能超时作业，22:00结束并清空后台队列。正式性能期间无并发训练/标注/其他性能作业。164/165已完成核验并封存。冻结曲线已完成并封存，执行前新增80MiB预算至1360MiB（1.328125GiB）；此项0构图/GT/训练，无后台作业。所有旧上限/产物保持历史身份。

[当前结果](summary.md) · [历史索引](s-experiment.md) · [实现合同](spec.md)。修订前完整目标保存在本日root_docs_before_online_priority.zip，原历史边界不丢失。
