# ACSG 五方法与三联动实验报告

当前见[Git结论交接](../../research_snapshots/20261006_results/README.md)和[八方法详细报告](../../research_snapshots/20261006_results/report.md)，核实时点2026-10-06T21:32:45.619435+08:00。

每dataset跨全部方法TRAIN限7200秒；历史已超额，禁止新增训练。

阶段快照：8方向均已开始探索，7有阶段边界；已接受134/288 native（120normal+14audit），正式评价1/4；无可靠默认替换。

第12行起均为历史快照；旧预算解释、旧运行状态与未执行描述不覆盖上述当前结论。


2026-10-04 最新用户约束：用户原话“一个数据集的训练预算是两个小时以内吧”。Root按当前多方法探索上下文解读为每个方法×单个数据集的累计训练／拟合不超过7200秒；这是root解释，不是用户逐字说了“每方法”。同方法同数据集的K1/K100、FIT0、FIT1、refit及全部轮次共用一项累计预算，不按K点、轮次或阶段重置。监督／标签生成、构建、验证分别计时披露；用户未确认整条离线流水线总成本也是7200秒。详见[训练预算约束记录](m2/training_budget_constraint_20261004_v1.json)。

训练预算已确认，但累计账本、实际timeout与执行guard尚未实现或运行，精确cost-check上限仍null；此前1小时只是历史root工作假设。不能靠阶段改名规避用户拒绝天级工期，预计整条路线仍需天级时不推进。M2原stage03未进入训练；最近进程事实只引用root于2026-10-04 10:32:35（上海）的观察：PGID 90589/100130可逆SIGSTOP、原六PID T/Ts，partial proof仅STAT为129566205B／inode1319835／mtime10:32:32.040776279，原件保留、未终止或恢复、不是完整六stage成功。本次没有fresh进程／proof核实，挂起不能替代实际终态；见[此前成本挂起记录](m2/runtime_budget_hold_20261004_v1.json)。

本报告仍覆盖M2/M5/M4/C1-F2/B4与J25/J45/JBP完整八方向，目标未完成；既有实测表、M5局部信号及其证据限制、默认与原停止范围全部保持。本次只记录用户预算及SOURCE候选状态，没有新的训练、性能、方法STOP或默认替换。 [M2等价几何降成本源码独审](reviews/m2_exact_geometry_budget_source_v1_independent_static_v1.json)与[B4精确拟合降成本源码独审](m4/b4_exact_fit_budget_source_v1_independent_static_v1.json)均仅条件SOURCE-only；两候选尚未执行，实际等价、提速及≤2h训练满足均未证明。saved-M5审计v1 canonical-state lease执行路线已被root拒绝；独立local-state只作静态建议，未实现或放行。

本段及新预算记录是当前约束；以下“预算待回复／pending”“1小时假设”“仍live／离线投入不限”等完整保留此前时点，不覆盖本次预算和挂起边界。


2026-10-04 10:32:35（上海）最新状态：当前M2原stage03已经Root可逆SIGSTOP，六个原进程均停止，partial保留、没有删除或终止；完整四Ω/compiler/checker及六阶段/root终态仍未完成，partial不能计作合格结果或方法失败。[离线成本挂起记录](m2/runtime_budget_hold_20261004_v1.json)只记录Root已观察元数据，本轮不查询进程／读取proof。

用户明确不接受天级离线工期。此前3–4天是M2全量精确证明生成＋复核的预计成本，未进入该作业的方法训练，并非实测训练3天；单方法训练／构建／验证合计预算仍待确认。原五方法三联动完整探索继续作为ACTIVE目标，生产E99/Web soft-t1/Y hard及下面既有SELECT Recall/QPS保持；SOURCE-only等价优化或合法重排尚待评估，未实现／测得提速、不授actual ready，停止占用CPU也不能直接启动后续实验。下文旧live表述保留其历史身份。


JBP 自有启动观察V3已有[根组合 SOURCE 审查](reviews/jbp_capture_own_startup_source_v3_root_composed_source_review_v1.json)/[独审](reviews/jbp_capture_own_startup_source_v3_independent_static_v1.json)：实际helper完整来源图与probe→join当前stat身份已修复，[V1 HOLD](reviews/jbp_capture_own_startup_source_v1_independent_static_hold_v1.json)/[V2 HOLD](reviews/jbp_capture_own_startup_source_v2_independent_static_hold_v1.json)及原封件保留。当前仅SOURCE_ONLY_UNCOMPILED_UNRUN，16实际refs null／16flags false，首K1零评分观察及独立join尚未执行；原双K/40K/七计划/全E、σ、Γ保持，完整采集与联合性能待验证。M2原第3/6阶段继续，完整五方法三联动未完成；下面M5实测、停止范围、费用口径及E99/Web soft-t1/Y hard默认保持。

JBP构建接口V2已完成[根条件SOURCE复核](reviews/jbp_capture_build_admin_source_v2_root_full_source_review_v1.json)及[独审](reviews/jbp_capture_build_admin_source_v2_independent_static_v1.json)，修复四处终态来源分类和完整16字段构建环境；[原V1 HOLD](reviews/jbp_capture_build_admin_source_v1_independent_static_hold_v1.json)及原封件保留。当前只完成未编译／未运行接续，未来实际配置须完整73来源闭包（当前代码最低直验capture44，外部root实际前件尚未满足）；16实际refs仍null/14flags全false。原完整教师、生成/编译、own机器/费用/域/capture、五控制求解和联合实测仍待。M2原stage03运行，现有M5四点Recall/QPS、科学范围、默认和八项未完成判断不变。

JBP V1已完成[根条件整链SOURCE审查](reviews/jbp_actual_capture_backend_final_root_composed_source_review_v1.json)与[组合独审](reviews/jbp_actual_capture_backend_full_independent_composed_source_v1.json)，66/65显式安全身份闭合，无新确定源码阻塞。独审明确8份当前全文+1份完整旧admin/453行修正基准，作者sidecar由另一独审组合。当前仍SOURCE_ONLY、未编译／未运行；通过范围仅条件代码契约与InputsV2接口接线。13实际前件全null、14flags全false，原完整教师、own image/机器、原费用/布局/签名资格、实际capture及五控制求解/native评测均未完成。两K/40K/七计划/完整E/σ/Γ不缩，两模式均完整枚举签名类，实际基数/资源可行性未知，工程超界只能记全范围UNRESOLVED。本轮V1“整包审进行中”和登记窄审头部完整保存在[V1阶段备份](source_before/root_before_jbp_capture_composed_source_sync_v2/original/entry_method_exploration/20261003_all_methods_experiments_v1/report.md)；下文UNIMPLEMENTED属于此前阶段。

当前M2原同六stage仍在stage03 Web K1全Ω几何，其他实际数值/性能阶段等待完整终态/root审查和串行空窗。完整M2/M5/M4/C1-F2/B4与J25/J45/JBP尚未完成，目标仍可靠Recall–QPS综合改进。此次不增加任何Recall/QPS结果；下面M5四点实测、固定族停止边界、成本及E99/Web soft-t1/Y hard默认保持。后文“采集后端未完成／UNIMPLEMENTED”记录此前源码阶段，不表示当前已获得实际采集资格。

当前 J25 V2 的[根全文源码审查](reviews/j25_joint_source_v2_root_full_source_review_v1.json)及[独审](b4/j25_joint_source_v2_independent_static_v1.json)已关闭原64MiB whole Export 误作总RAM门的源码错配；导出文件限额恢复、额外内存完整另报，原四点43控制与科学体保持。V1/HOLD保留。V2 只完成 SOURCE_ONLY，22项实际前件全null，未编译/运行或生成联合性能；JBP真实采集后端及实际FIT/五控制求解仍待。全五方法、三联合未完成，已有实测和默认不变。下文“V2正在修”保留先前状态身份。

当前新增SOURCE_ONLY进度：[G1求解/五控制导出根源码审查](reviews/jbp_global_reference_solver_source_v1_root_full_source_review_v1.json)及[独审](m4/jbp_global_reference_solver_source_v1_independent_static_v1.json)和[Inputs V2独审](b4/jbp_global_reference_inputs_source_v2_independent_static_v1.json)已补原五强控制的完整接续源（两阶段、F-only、fixedA、fixedpi2、full G1）；完整整数复核/有理下界、原π2/表byte导出及独立reader已写齐，actual费用/全签名采集后端仍UNIMPLEMENTED，未采集/求解/生成真实native或测QPS。[原envelope部署范围勘误](b4/jbp_global_reference_solver_source_v1_export_metadata_erratum_v1.md)保留原envelope全grid/metadata并完整计预算。

[J25新joint接线v1独审HOLD](b4/j25_joint_source_v1_independent_static_hold_v1.json)确认64MiB Export误作总RAM的实现问题；原V1保留，V2正在修，不能记actual联合STOP。完整M2/M5/M4/C1-F2/B4与J25/J45/JBP仍未完成；生产E99/Web soft-t1/Y hard和既有实测不变。M2原同六stage作业仍在stage03 Web K1全Ω几何，未重启。

当前源码进度：[J25 lower reference v3根源码审查](reviews/j25_lower_reference_source_v3_root_full_source_review_v1.json)及[v3独审](b4/j25_lower_reference_source_v3_independent_static_v1.json)已关闭lower唯一全四first-freeze/full48四filter前端的源码缺口；原all6→原四lower SELECT硬链保持。v1差异文件runtime-map、v2把atime纳入首hash稳定性的SOURCE HOLD原件保留；v3只修稳定stat与行政身份，保留四lower/primary Y K1/20K/4096、全部48功能/23计数、8原价格和7 whole-plan。[JBP全局参考core根审查](reviews/jbp_global_reference_model_core_v1_root_full_source_review_v1.json)及[core独审](b4/jbp_global_reference_model_core_v1_independent_static_v1.json)保持SOURCE_ONLY，实际完整输入/排他费用与签名资格、solver/bound/native导出仍待。J25实际all6/all4、唯一首锁及full48未运行，distinct12factor/provider/caller及完整Recall-QPS仍待；源码审通过不授实际资格或收益。

[M5 startup v7根源码审查](reviews/m5_cal_confirm_own_startup_v7_root_full_source_review_v1.json)及[v7独审](m4/m5_cal_confirm_own_startup_v7_independent_static_v1.json)已关闭原CAL/confirm自有startup接线：同原gate/role/4096-prefix/source闭包后，同sealed memfd送原v9子进程，恢复后继续原warmup/五wall，phase→CAL→confirm消费同binding。v5遗漏context两路径键、v6遗漏相对目录引用的SOURCE HOLD保留，v7修正两项；原12job/16版本、有限非空S事前锁/全4-8 ledger、CAL1/80和confirm1/160保持。own registry/allpath/unsigned6角色+2profile/外部root六资格等实际前件仍null，未prepare/执行CAL或confirm。JBP unposted FIT1 v3源审保持；[JBP 44 post教师v2根源码审查](reviews/jbp_post_teacher_own_startup_source_v2_root_full_source_review_v1.json)及[v2独审](b4/jbp_post_teacher_own_startup_source_v2_independent_static_v1.json)已关闭三项行政源码缺口：NONE哨兵、完整probe/unsigned来源根绑定、actual/expected SHA分列；v1 SOURCE HOLD原件保留。原140任务/44教师/20K/三tick及全部控制保持，实际own registry/六义务/all44 probe仍缺，未prepare或执行；真实FIT/求解/联合仍待。原M2同六stage作业仍在stage03；本次仅SOURCE_ONLY/安全元数据，完整八方向目标、已测结果和E99/Web软t1/Y硬默认保持。

当前为E172执行中报告，完整范围M2/M5/M4/C1-F2/B4与J25/J45/JBP尚未完成。目标是可靠的 Recall–QPS 综合改进；生产E99、Web GT10-soft-t1、Yandex GT10-hard保持，尚无可靠新综合收益或默认替换。

J45独立caller v4已通过[根全文源码/最终身份复核](reviews/j45_fullcaller_v4_root_full_source_review_v1.json)及[独立静审](m4/j45_fullcaller_v4_independent_static_v1.json)；267安全来源前后闭合，另核固定两image的SHA身份。原四点、四角色、16×42全部对象/顺序、M5强控制和科学函数保持。初次三seal原字节另存，仅修正非消费cache_schema标签V1→V2后重封；10核心代码不改。[近似provider](reviews/j45_approx_provider_source_root_full_review_v1.json)、[独立cached-R oracle](reviews/j45_cached_packet_oracle_source_root_full_review_v1.json)、[SHA bootstrap](reviews/j45_buffer_sha_bootstrap_source_root_full_review_v1.json)、[四点trace空结果](reviews/j45_trace_empty_results_root_acceptance_v1.json)均已具各自根/独审范围，并已集成到v4源码。四点trace为typed empty/lookup-disabled，proof未构造；源码PASS不签实际ELF、实例、完整cap/驻留、reuse或性能。尚未编译/运行，没有新增Recall/QPS或默认变化。

J25四点discovery队列已实际生成并封签，[v3独审](reviews/j25_lower_registration_v3_root_independent_static_v1.json)和[root实际准备核对](reviews/j25_lower_discovery_actual_materialization_root_v1.json)通过；原20K四lower点、primary Y K1、科学job和源ELF保持。root随后在CPU0–5[实际生成六个continuation DRAFT](reviews/j25_lower_continuation_actual_draft_root_v1.json)：四点几何、全四汇总和route-word桥，cache未来SHA全null，未封/run；125份独审身份及root前后127安全来源闭合，原active M2全部82来源保持。准备无数组/GTK/raw/native/几何或route核验，SELECT未封。实际执行仍等原M2六stage完成/root审查及串行空窗。旧[M2完成门v1独审HOLD](m4/m2_core_v10_terminal_gate_v1_independent_static_v1.json)保留；v2已通过[固定metadata/真实receipt join源码独审](reviews/m2_core_v10_terminal_gate_v2_root_independent_static_v1.json)，snapshot未调用、actual terminal/root审查尚无，不把源码PASS写为实际完成。

M5原16版本×四点SELECT完整native及原五stage评估已完成：Web @1冻结主候选Recall +0.146484pp、五轮配对QPS比中位+24.1638%，召回差描述95%区间[−0.341797,+0.634766]pp跨零；Web @100/Y @1/Y @100分别损失1.008301/1.757813/2.239990pp，虽提速但未达到主质量门。Web @1 missing_frequency简单控制达到相同Recall/392.316 QPS，主候选信息优势未建立。独立实现/GT/全强控制审计尚待，未执行CAL/confirm或切默认。

C1两集原ELF零query对象探针、A0/A1标量与A2自身batch4资格独审/实际汇总及root资格已闭合；原四组/clean补测完整packet和source核验后，按唯一clean Web @100/L1250首1024五wall总和全局冻结M0=scalar-span、Bcmp=strong166/span-batch4，两集共用。五wall总和依次20.380581246/18.781061241/15.852274359秒；其他点不参与选择。真实CLASSMAP/16384 witness/编图/replay及CAL尚未执行，未来不同ELF/角色仍须自有绑定。

B4原九stage first128及四点c/B已实际完成，完整source/terminal闭合、单线程无quota；Web K1(c=500,B=4928)、Web K100(625,5952)、Y K1(65,1152)、Y K100(129,2176)。c/B仅用原FIT0首128观察，不解码GTK作选择；完整20K全部七计划教师、原有限Π精确fit及JBP真实两阶段仍待。

原C1/B4 v14教师的自有startup观察已获[M4两份独审及root全文复核](reviews/c1_b4_own_teacher_v2_root_full_source_review_v1.json)，[C1原FIT条件决定](reviews/c1_b4_own_teacher_conditional_phase_decisions_v1/C1_FIT_AFTER_M0_FROZEN.decision.json)和[B4原教师/精确fit条件决定](reviews/c1_b4_own_teacher_conditional_phase_decisions_v1/B4_FIT0_TRUE_TEACHER_EXACT_POLICY.decision.json)保留原六/六十八science argv及18原native job。新11/73 stage未prepare/run；真实执行仍等M2完整终态/root审查、固定M5终态、空窗、各自probe/join及每个真实教师自身首评分前的DC/机器/全words/严格FP。止于原graph/model seals，不能自动CAL/confirm或切默认。新增行政观察/扫描成本计入作业wall；B4原三tick不含停顿，实际factory RET 0xdf4bf与caller return 0xb30fe的[措辞勘误](b4/teacher_own_qualification_v2.observer_stop_erratum_v1.md)保留原README。

M5 CAL/confirm v2已通过[root源码复核](reviews/m5_cal_confirm_frontends_v2_root_source_review_v1.json)：原12job/16版本及六科学函数AST未变，三项行政HOLD修复；saved-record v3实际审计、v9自身六评分义务、根全四scope决定与IID前提仍缺，零新queue/stage/CAL/confirm。上述根证据已另作[独立安全metadata核对](b4/root_conditional_teacher_and_m5_independent_metadata_v3.json)，不读取数组/GTK，不代替实际资格或性能。

[M5实际元数据](reviews/m5_select16_all_four_and_postmortem_actual_root_metadata_v1.json) · [C1实际全局冻结](c1/primary_global_after_actual_object_v1/primary.frozen.json) · [B4实际first128](b4/root_first128_storage_v4_v1/root_controller_v2.actual.json)

|项目|实际完成|当前判断与下一门|
|---|---|---|
|M2保序区间评分省略|四点全部未抽样20K Ω、8项原参考费用已测/独审/冻结；全N/Ω/checker源已封|两集全N缓存/逐ID检查已完成，原stage03 Web K1全部Ω几何运行；后四Ω/checkers与whole/root终态→四filter/actual helper→formal未完成；参考OFF不是QPS失败|
|M5残差posting补输出|共享表/全TRAIN独审/八输出事前锁；16版本×四点原完整wall和GTK/成员配对评估完成|Web @1局部信号，其余三点质量损失；独立实现/GT/强控制核验→原冻结CAL/confirm门|
|M4响应证书复用|两集各81,920,000跨key配对与17尺度上限独审|停止该冻结共同族SELECT准入，可能覆盖上限0；不外推其他几何/总体或QPS|
|C1-F2图编译|原默认四组/clean补测、原ELF全域资格/实际对象闭合；全局M0/Bcmp已冻结|原CLASSMAP→16384双K witness/编图/replay→原风险/强控制与完整wall仍待|
|B4有限预算独立前沿|正式实现/独审与原九stage first128/四c-B已实际完成|完整20K×七计划×三tick教师→原有限Π exact fit→冻结强控/CAL/完整wall仍待|
|J25 M2+M5|原四lower-L注册/原价source桥已审；primary Y K1、same-R/same-U条件上界保留|四点新Ω/几何/全checker/route来源及actual联合caller尚待，不借L0输出、不记actual联合STOP|
|J45 M4+M5一次评分|原四lower-L同族几何lineage/独审及root准入停止|只关闭该族SELECT证书命中机会；v4根/独立源码审查已完成，普通融合/缓存/miss caller实际资格和完整联合费用仍未知|
|JBP B4+M5重拟|原全七计划missing共享表/实际plan+A/原Π重拟及监督匹配合同已封|FIT0→FIT1完整teacher→共享A/强控制→实际plan+A→重拟π1→原SELECT/CAL/confirm均待|

接续状态：M2原core_v10两集全N exact-native96缓存生成及逐原ID检查已实际完成：Web N=2,505,000/d=512，Y N=10,000,000/d=200，均96B、sampled=false、实际线程1/无quota。原Web根/独审保持，[Y stage02根核对](reviews/m2_core_v10_y_fullN_actual_stage02_root_metadata_v1.json)及[Y独审](b4/m2_y_fullN_actual_stage02_root_independent_metadata_v1.json)已闭合；cache/base payload未由根或metadata独审重读，payload SHA是producer声明。原同一六stage队列当前执行stage03 Web K1/L1000全部Ω几何；后四项Ω/compiler/checker与whole/root完整终态仍待。这是离线生成与检查进度，不是helper税或线上QPS。 M5 saved-record独审v3已完成root全文及242安全源码/元数据身份复核，实际审计仍待串行空窗。B4原69stage队列已实际生成（重复语义门+原68任务），四点全20K/24列/三真实tick及原17次tie solve保持；队列尚未执行，C1/B4教师各自ELF的实际DC对象/严格FP/机器观察仍待执行，不能借v15、另一ELF或独立probe地址；新源码/有条件授权不代表实际资格。原B4生成器还对两集旧FIT0 GTK和行号四文件做SHA校验，未解码或执行teacher/solver；该例外已单列保留，不声称生成器零数值字节读取。

[M2实际原队列启动](reviews/m2_fullN_all_Omega_core_v10_actual_root_launch_v1.json) · [M5独审v3 root排期](reviews/m5_saved_record_audit_v3_root_readiness_v1.json) · [B4原69stage生成与SHA例外](reviews/b4_fit0_original_69_queue_root_materialization_v2.json)

## M5四点实际SELECT结果

四native作业全部退出0、实际1线程、无quota，启动/比较/独立untimed核验总耗时分别1630.865/2038.278/281.236/505.878秒。这些是作业费用，正式QPS只由各方法完整正常batch的五轮wall计算。原metadata checker与四评估器随后串行成功，parent source before/after及实际metadata闭合；root收据仅完成实际来源/monitor/评估身份核验，独立质量审计仍待。

主候选始终residual_joint@Lminus，对照default_main@L0。QPS各为五轮中位数；速度增幅为五轮配对QPS比的中位数，与两QPS中位数相除可略有差异。

|工作点：lower→main L|默认Recall / QPS|主候选Recall / QPS|ΔRecall pp / 描述95%区间|配对QPS变化|救回 / 损伤成员|
|---|---:|---:|---:|---:|---:|
|Web @1：800→1000|90.454102% / 315.446|90.600586% / 390.916|+0.146484 / [−0.341797,+0.634766]|+24.1638%|55 / 49|
|Web @100：1000→1250|90.581543% / 253.032|89.573242% / 311.864|−1.008301 / [−1.105225,−0.919189]|+23.0143%|1715 / 5845|
|Y @1：100→128|90.625000% / 1995.753|88.867188% / 2361.232|−1.757813 / [−2.221680,−1.318359]|+19.9034%|9 / 81|
|Y @100：200→256|91.044434% / 1074.530|88.804443% / 1299.515|−2.239990 / [−2.404053,−2.090332]|+19.2487%|86 / 9261|

全部16版本均报告，不反馈选最优控制。Web @1 missing_frequency控制同为90.600586%/392.316 QPS；原L0补全只作diagnostic，不代替lower-L主比较。全部真实返回、五轮wall、描述区间/成员细节见[Web @1](results/m5_fullcontrols/webvid2_5m_light_v1/select/k1/evaluation.json)、[Web @100](results/m5_fullcontrols/webvid2_5m_light_v1/select/k100/evaluation.json)、[Y @1](results/m5_fullcontrols/yandex_t2i_official10M_ip_v1/select/k1/evaluation.json)、[Y @100](results/m5_fullcontrols/yandex_t2i_official10M_ip_v1/select/k100/evaluation.json)。历史SELECT已曝光，窗口与bootstrap不提供IID/总体保证。旧scalar lower/main可作外部独立逐字桥接；旧独立plus packet不存在，不能称其外部桥PASS，v9自身原默认调用/linear审计及source资格另留。当前没有CAL/confirm或默认替换。

## 必要门实测

M5历史SELECT各4096；成员计数上限假设零损伤，不能冒充真实merge或质量通过。

|数据/指标|lower L→L0|质量债务|full U最优≤24 rescue上限|原A rescue上限|固定版本结论|
|---|---:|---:|---:|---:|---|
|Web @1|800→1000|52|138|58|上限余6，必要门开，仍须实际输出/费用验证|
|Web @100|1000→1250|5974|6530|1844|原A不能偿债，fullU未排除|
|Yandex @1|100→128|83|14|11|同U也不能偿债|
|Yandex @100|200→256|9278|249|103|同U也不能偿债|

[两集门与独审](m4/m5_upper_fixed_scope_independent_v1.json)仅支持对应固定来源、原lower-L输出、同U/A和≤24补全停止；新U、全库几何和Uprime强控制不自动继承。

M4每集全部81,920,000跨key配对均由保守最大尺度外包盒排除，UNKNOWN=0/possible=0；原17尺度精确嵌套，故全族可能SELECT hit上限0。[Web实测](m4/webvid2_5m_light_v1.keyfree_union_upper_v2.json)、[Yandex实测](m4/yandex_t2i_official10M_ip_v1.keyfree_union_upper_v2.json)与两份keyfree_union_independent_scope_v1独审支持停止该冻结共同族。此结果不是完整程序证书生成、其他几何、CAL/confirm、人口/IID或QPS失败。

J45的[原共同族lineage](m4/j45_common_family_lineage_v1.json)和[独审](m4/j45_common_family_lineage_independent_v1.json)已明确proposal几何不依赖K/L/response，原四lower-L点共享同一20K/17尺度/32peer/RMS来源与原SELECT4096。[Root决定](reviews/j45_common_family_select_hit_admission.root_decision_v1.json)仅停止该注册族的SELECT证书命中准入：每点上限0、UNKNOWN=0。Lower-L response/recipe/实际目录/native资格不能继承；普通融合、合法缓存和miss caller仍另核，不据此声称整个J45路线或联合Recall/QPS失败。本次只读源码/JSON并引用既有实测，没有新增数组/GT/native实验。

J25的[必要质量继承审查](m2/J25_NECESSARY_INHERITANCE_V2.md)保留原四lower-L点与primary Y K1。若实际main有效ID集合保持原L100响应R，补全候选仅来自同固定U且≤24，则原SELECT4096质量债83、full-U救回上界14，净成员差最多−69；同原A更紧为−72。该结论不要求IID或组件性能PASS，仅限这一条件类。实际新联合仍缺same-R跨caller/M2全状态保真及primary provider固定来源核验；当前不是actual联合STOP，其他U/全库/强控制不继承，四点独立准备继续。

## 完整来源与参考费用

M2四点Ω完整保留，采样false：Web K1/L1000 11,719,386 sites、K100/L1250 14,312,870；Y K1/L128 2,353,236、K100/L256 4,410,798，共32,796,290 sites。Y资格使用新discovery_storage_v2完整输出，旧discovery的K100 partial不能消费。[完整收集核对](reviews/m2_full_omega_collection_after_recovery_v1.json)不推几何或性能通过。

8个m2/norm/coord/hull参考费用用64固定位置discovery query、每位置4096个实际原callback；完整原route-token在全部价格clock前锁SHA，所有样本原样保留。四实际DC槽/factory/loaded代码与有序G0、全部25类exact ceil归因、before/after和串行线程均通过[root核验](reviews/m2_prices_root_full_review_v1.json)及[独审](m4/m2_pricing_actual_metadata_independent_v1.json)，[8价冻结](reviews/m2_all_prices_frozen_v1.json)已完成。热地址callback和代表指令税不是actual helper费用界；Jhat=0/参考OFF均不能判断真实QPS或整个方法失败。

历史20K训练/4096开发只作discovery/SELECT。新FIT1=20K、CAL32768、confirm-A/B各4096按预锁窗口在GT前source/byte去重；两集121920条full-base raw-IP GT和64条独立float64全库抽检完成。确认窗口来自同公共train/learn源，语义独立/IID仍不成立，报告只给分组复现与描述区间。

## 计时与工程成本

正式CPU15实际单线程、方法串行；normal owned batch的分配/初始化、route/main/post、guard/cache/lookup/membership、失败/fallback、helper、merge、输出和实际释放均计入wall。启动加载/fullword绑定及GT/hash/计数审计在wall外；5轮基础、7轮联合确认，原默认获得相同合法优化机会。timed输出释放后不保留，独立全packet审计另跑同一正常body，不声称逐轮保存words。

已测离线/核验成本：全GT5687.911秒；M2原Ω Web384.677秒、Y恢复96.241秒；M4全keyfree Web389.924秒、Y157.322秒；M5强控构建Web106.850秒、Y235.235秒；全N cache/逐ID检查Web4412.073秒、Y7343.720秒。它们均不是正式QPS。完整启动/结构/临时文件/实际resident在各root job与方法receipt分别保存，后续上线收益不能借离线费用替代。

存储事故按行政v2修复：仅任务树7772份产物逐SHA/link/mode/mtime复制核验并绑定到另一持久卷，原路径保持。总12GiB、双卷空闲6GiB、进程组RSS32GiB；方法Export/resident/参数/数据/质量门不变。原2.5GiB quota -15及Y partial完整保留，不归因方法失败。v15小native首stage因旧tiny源迁卷dev/inode变化正确拒绝，原日志FORMAL15_SYN_827c18e25c_000保留；新收据必须重新全SHA/word核验，不关闭身份门。

## 未完成与替换判断

M5已完成四点SELECT实际Recall/QPS，独立核验、后续CAL/confirm和可靠收益仍未完成；其余方法/联合正式性能仍缺实测。C1全局primary已冻结，真实见证/编图待执行；B4四c/B已冻，完整teacher/fit待执行。J45同族准入已停止，普通融合/缓存/miss caller与J25实际继承仍待核验。性能不能从必要上限、几何、构建成本或合成parity补齐。完整八项任务继续，项目目标未达成，默认不变。

[协议](protocol.md) · [冻结科学配置](config.locked.json) · [当前状态](state.json) · [当前必要门/价格收口](reviews/necessary_gates_closeout_and_fees_frozen_v1.json) · [历史172](../../experiment_history/172_all_methods_experiment_campaign.md)。旧版本报告已保存在source_before，原170/171/DOCX和旧seal不回改。
