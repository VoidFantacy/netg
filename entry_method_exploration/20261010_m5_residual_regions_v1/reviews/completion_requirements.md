# E174 完整完成要求：静态检查清单

本清单仅依据冻结协议、三份锁、root E174块及已有源码整理，不读取本轮GT、返回、Recall或QPS，不执行任何脚本。**以下全部实测/产物要求均为待验**；源码审查、smoke或路径名称不能代替正式完成。该清单不增加策略、参数或实验门。

路径约定：`C=/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_regions_v1`；`P=/data/netg/ACSG`；`J=C/jobs/{role}.{dataset}.json`；`O=J.out`；`T=O/k{K}/{method}_L{L}`；`A=C/analysis/final_v1`；`I=C/reviews/independent_result_audit`。这些是待核验路径模板，不表示其终态已经存在。

## 执行、身份与实现

| 状态 | 具体完成要求 | 权威路径/字段 | 覆盖范围与局限 |
| --- | --- | --- | --- |
| 待验 | 完成冻结全部112点、336正式批次；a九方法、b五方法，两集各真实K1/K100及两L；不得由a反馈取消b或换参数。 | `protocol.md`；`parameter_lock.json.jobs/primary_method/no_adaptive_cancel_or_selection`；四个J；四个`O/complete.json.results/wall_rounds/formal_order`及`timing_progress.json`。 | a72点、b40点；Web L800/1000，Yandex L1000/1200。只覆盖这些离散点，不插值或外推。 |
| 待验 | 四个独立job成功退出且无活动子进程，实际单线程CPU15、固定轮转、warmup256一次、每点三轮。 | `run_state.json.status/active/completed[*].exit_code/max_threads_observed/job_sha256/elapsed_seconds`；`O/native_environment.json.threads`；逐批`formal_order.threads/cpu/round`；`O/complete.json.native_calls`；源码`src/run_serial.py`。 | GT评价前必须满足`NATIVE_COMPLETE_PENDING_INDEPENDENT_GT_EVALUATION`、active=null及4个exit0；native_calls核warm/timed/plain/replay/count的主查询次数，不是总dot数。job≤7200s；失败/超限保留partial，不冒充完整矩阵。 |
| 待验 | 协议、job、native源码/ELF及后处理源码保持冻结身份。 | `parameter_lock.json.protocol_sha256/jobs`；`execution_lock.json.source_and_binary_sha256`；`auxiliary_lock.json.files`；`reviews/build.json`及源码独审收据。 | 三份锁分别负责策略/角色、正式执行、后处理。静态PASS不是实际评价PASS；本清单不重新hash。 |
| 待验 | 注册109项依赖/输入身份闭合，正式期前后stat稳定；原画像/labels、表、原图/metric和注册base不变。 | `execution_lock.json.input_stats/inputs_sha_closure`；`reviews/data_preflight.json`及`data_preflight_large_sha.receipt.json`；J的query/GT/rows/table SHA；`O/native_environment.json.loaded_base_words_checked/graph_N/graph_degree/router`。 | 四个大base/index的当前完整SHA在性能前闭合，性能期stat守卫；109项含原方法依赖与身份收据，不等于109个新训练输入。source-row/注册字节排除不是语义IID或全项目未曝光。 |
| 待验 | 编译和原GT/M5回归资格与正式证据分开。 | `reviews/build.json`；`reviews/smoke_execution.json`；`reviews/preexecution_acceptance.json`；`reviews/native_source_independent_review.json`。 | 两集16-query/点smoke、原GT/M5逐位回归及extra0 intervention只证明相应程序范围，不证明全分布Recall/QPS；不得用smoke填正式点。 |
| 待验 | 保留原GT主搜索和原M5完整C及合并；实现冻结seed/cap/arrival规则与回退。 | `src/runtime.hpp.plan/apply`；`src/region.hpp`；T收据`extra_cap/first_seed/original_GT_route_words_unchanged`；`raw/region_trace_schema.json`及full oracle收据。 | C≤24，每行query-best、≤3seed、去重不补位；X≤24/96，排main-vt/C/X重复、原rawIP严格合并且X优先级晚于R/C。R/C非有限保GT；X非有限保成功的对应direct完整返回，M5分支即原M5。不是续搜或改图；普通异常为fatal，不能泛称所有失败都事务回退。 |
| 待验 | 完整wall计入正常输出生命周期及全部附加query工作；正式计时不采集trace/oracle。 | T收据`normal_output_release_before_stop=true/timed_output_retained=false/timing_seconds`；`src/benchmark.cpp.timed_normal_batch/run`；`O/complete.json.wall_boundary`。 | 包含allocate/init/release、route/main/guard/post/seed/neighbor/filter/score/merge；加载、hash、评价、写盘与审计单列。timed输出不留存，不宣称每轮timed bits已核验。 |
| 待验 | 每点保存完整4096 plain，并完成独立全量replay逐位相等及direct/region相应全量oracle。 | `T/raw/{ids.i32,distances.f32,entry_ids.i32,profile_distances.f32}`；T收据`full_plain_return_n/full_plain_independent_replay_n/full_plain_independent_replay_bits_equal/independent_original_linear_merge/independent_region_linear_oracle/linear_merge_audit_n`。 | direct保原线性merge oracle；region独立重建C/seed/X、逐ID新DC重评分逐位核验及linear-worst合并。原direct oracle保留注册有限域假设，不作全域普遍保证。 |
| 待验 | 全64区域点完整trace、容量/来源/唯一性与全量费用一致；主M5REG96共16点。 | `T/raw/region_trace.i32`及schema；`T/trace_summary.json/full_region_audit_stats.json`；native候选oracle；独审trace明细。 | 每query128个i32：seed3、nC、nX、nSeeds、m5_committed、extension_aborted、C24、X96，padding=-1；4096条2MiB/点。scalar words在进程内核验，不在离线trace中保存；原seen不能泛称expanded。 |
| 待验 | 固定均匀256 plain/count词一致及物理调用账一致。 | `T/raw/{audit_query_ids.i32,route_ndc.u64,graph_ndc.u64}`；T收据`plain_count_bits_equal/count_audit_n/stats_scope/stats`；`analysis_schema.md`。 | sample公式floor(i×4095/255)；计数不是全4096 NDC或计数版性能。post_dots=实际R+C调用，new_distances=X；graph_ndc已包含附加费，不重复相加。 |

## 评价、独审与来源

| 状态 | 具体完成要求 | 权威路径/字段 | 覆盖范围与局限 |
| --- | --- | --- | --- |
| 待验 | 所有native完成后实际生成完整评价，不以静态脚本代替运行；112 points、288 comparisons、64 mechanisms。 | `A/metrics.json.status=COMPLETE_E174_FROZEN_112_POINT_EVALUATION`及三数组；`points.csv/comparisons.csv/mechanisms.csv`；`A/scored/*.npz`；`src/evaluate.py`。 | 每点全4096实际返回相对真实K的既有exact GT；同L/跨L比较均来自真实点，hit/member交叉核对。结果不得在native结束前打开。 |
| 待验 | 独立整数/成员/wall/trace/费用/收据审计实际通过，并与JSON及CSV完整一致。 | `I/report.json.status=PASS_INDEPENDENT_112_POINT_INTEGER_WALL_TRACE_AUDIT`；`point_count=112/comparison_count=288/formal_timed_batches=336/full_region_trace_points=64/primary_full_region_trace_points=16`；`independent_{points,comparisons,mechanisms}.csv`。 | 不import evaluator，不生成新距离/GT；另核固定轮转、全返回/route words、采样DC费、C计划与trace域/唯一/预算。seed评分与ordered graph/visited X由先前native scalar oracle负责，不由整数独审重算。 |
| 待验 | 既有角色GT、原TRAIN支持及U来源准确绑定；质量差异与机制覆盖分开。 | J的`GT/GT_dtype/GT_width/GT_sha256/rows/query_sha256`；原`compile_manifest.json.input_sha256`中的`/fit/gt.i64`；`metrics.source_sha256`；`I/report.json.teacher_support_sources/source_sha256_and_stat4`；`analysis_schema.md`。 | 角色GT是4096×100既有exact rawIP成员；原TRAIN是20K×100。U_M5为原posting并集，U_TRAIN为原TRAIN GT100并集；U外量是每query incidence，非全局distinct或跨模态泛化证明。 |
| 待验 | 全方法实际救回/损伤以comparisons为权威；M5-only机制字段不得误用于MF/GEO。 | `comparisons.recall_delta_pp/rescue_members/damage_members`；`mechanisms.new_rescues_vs_M5/new_rescues_outside_*`；辅助独审mechanisms CSV。 | evaluate的new_rescues三字段仅M5REG24/96/FIRST96计算；MF/GEO初始化0表示未计算。U外damage未单列不能填0；新候选/真目标覆盖不是净Recall。 |
| 待验 | 既定paired统计与速度标签真实、范围披露准确。 | `comparisons.delta_ci.seed/repeats/low_pp/high_pp/scope`；`paired_qps_ratio_rounds/all_rounds_faster/speed_ranges_separated/observed_joint_gain`；独审CI元数据检查。 | 2000次paired query bootstrap为描述区间，无语义IID/同时多比较保证；整数独审不独立重采样端点。cross-L仅round-index顺序对齐，不是同时或随机配对。 |
| 待验 | 新TRAIN/fit/teacher/表/画像/图构建增量0，历史债保持，实际工程/查询成本完整披露。 | 三锁`no_new_TRAIN`；`run_state.training_increment_seconds`；`metrics.training_increment_seconds`；`I/report.new_training_seconds/new_distance_or_GT_generated`；协议及root当前TRAIN说明。 | 当前每dataset跨方法TRAIN7200历史已超额；不借K/role/阶段重置，不恢复旧队列。编译、query、hash、验证/审计、存盘分别披露，不将新TRAIN0称总离线成本0。 |

## 报告、决定与交付

| 状态 | 具体完成要求 | 权威路径/字段 | 覆盖范围与局限 |
| --- | --- | --- | --- |
| 待验 | 实际生成报告和两role四panel图，填入所有点及主same-L/cross-L、pilot强控、机制救/损和费用；SVG/PNG实际视觉检查。 | `A/report.md`；`A/figures/{pilot,confirm}.{svg,png}`；冻结`src/render_report.py`；成本阶段小收据及run/build/smoke/hash/audit真实elapsed。 | QPS median与三轮min/max xerr，无连线插值；PNG同图dpi160。cross-L并列小L原M5及其对大GT差额，再列REG−M5增量；不能把原M5已有双升全部归给区域扩展。缺计时标缺，native总费中的正式wall不重复相加。 |
| 待验 | 报告“已独审”绑定实际选用metrics文件，而非旧/其他评价。 | `I/report.json.source_sha256_and_stat4[str(metrics.resolve())].stat4`；renderer当前文件`[dev,inode,size,mtime_ns]` guard；`auxiliary_lock.files`。 | 缺登记或metadata变化fail closed；renderer复用已记录身份，不新hash/raw/GT。无审计时不能标已审局部复现。 |
| 待验 | 给出有限保留/停止决定、默认保持；不强造双升、不根据反馈扩网格。 | `protocol.md`判定与停止；报告；`metrics.default_replacement=false/primary_method=M5REG96`。 | 协议较强局部门为两roles正、confirm Recall CI.low>0且三轮更快。报告另显式要求两侧observed_joint_gain，并附加最慢/最快范围分离；这是更严格报告资格，不倒写为协议原文或新增实验策略。未达成停止本冻结一跳/seed/cap版本，不等于丢弃M5；局部正结果仍不替默认。 |
| 待验 | 同步四root文档、E174历史及campaign README，使状态/合同/结果入口一致。 | `P/{summary.md,spec.md,s-target.md,s-experiment.md}`的E174块；`P/experiment_history/174_m5_residual_regions.md`；`C/README.md`；必要时`C/state.json`。 | summary载实测决定；spec载实际合同与核验范围；s-target载目标/预算/停止；s-experiment载状态与导航；history载完整证据及成本；README给固定阅读入口。未验项保持待验，不用“实现/编译通过”代替收益完成。 |
| 待验 | 保全科学锁、旧M5/GT10/原图数据、原E172/E173及其他历史记录；交付后停止本冻结范围。 | 三锁及原依赖身份；`P/experiment_history`旧记录；当前原表/图路径；E174真实产物与日志。 | 不覆写旧资产、不删除partial、不恢复旧队列；仅更新E174对应现状及链接。原预算债、原证据限制与最近实测结论保留到新实际终态成立。 |

资源合同仍为总产物≤512MiB、min free1GiB、RSS≤64GiB、每job≤7200s；性能期不并发训练、GT、构图、编译或数值分析。该清单未执行以上任何核验，也未宣称任何待验项通过。
