# E91 最终评估工具准备（0新增ANN）

当前交付入口为 `src/run_frozen_v3.py`、`src/analyze_frozen_v3.py`；它们使用 `contracts_v3.py`、`scoring_v3.py`、`plot_results_v2.py`。v1/v2与各自测试冻结保留。工具已通过既有结果与非执行元数据夹具检验，**尚未进行真正的最终控制器执行、实际best_all/best_new选择或最终载荷读取**。

既有E74完整55点/112640行集合与mask、45小图、275旧wall及完整轮换顺序/逐轮秒数、同入口返回、跨L路由、原kernel/parity核验通过，旧全部点逐值复现。内存2000行评分夹具110000行通过，不计算2000-QPS。v3有32项负例（重复/非法ID、mask、线程/CPU、预算、distinct、未选择/反馈回流、空规则/tie、七类raw形状/类型损坏）全部拒绝；此外固定3画像/variable1..3结构、先拒绝draft后才hash、best_all控制候选拒绝也单独通过。最终输出同时检查每字段shape/dtype，不能由空数组的isfinite通过验收。

新增零查询。`results/v3`是既有E74软件重分析，QPS图只重画旧2048批；图例`best_new`仍指E74原compact，绝非今天重新选出的best。补齐完整414条query失败并集、825个query×L事件、4627个query×L×method单元，包含所有方法同为零的行；不与E89/E90辅助7952合并计数。原E74报告只展示配对状态变化，两者统计对象不同。

最终唯一写入者需要完成下列实际步骤：

1. 从`../candidate_inventory_v11.json`的76记录及原开发证据中，形成真实候选池资格、得分、规则和tie说明，冻结best_all/best_new。控制/零更新不可入选；E73二进制只接受兼容声明的普通小图方法，E72 distinct或不同评测器SHA直接拒绝，需新兼容实现与协议才能进入。
2. 在**新独立最终目录**写`protocol.md`、`selection.json`、`config.locked.json`、每集`inputs/<dataset>/config.json`、空`logs/jobs.json`、`reviews/base_graph_identity.json`。所有要求基线取第9会话`matrix_metadata_draft.json`；每集2000、五L、五轮、CPU15/threads1。相同配置角色用alias，只测一次。
3. `selection.json`要求status=FINAL_SELECTION_FROZEN、final_feedback_used=false、selection_rule/tie_rule非空、candidate_inventory/candidate_score_table路径；每集datasets含best_all、best_new（实际model_name）、best_new_inventory_name，以及inventory_names（所有新增model_name→候选目录name）。目录记录必须含真实configuration及同E73 evaluator SHA。规则/得分科学合理性仍需实际审查，非空字符串测试不能替代选型审查。
4. `config.locked.json`要求threads1/query_cpu15、planned_NSG/planned_HNSW/points/timing_batches按实际不同配置数计算、output_cap_MiB≤64、free_min_GiB≥6.45、latest_launch/query_stop/per_job_seconds，以及dataset_operation_budget_seconds按集预留。query_stop不得晚于20:40 epoch1789303200，per_job≤1800s；启动还要求剩余时间够完整剩余矩阵。2000行每点14016 NSG、每非NSG点14000 HNSW；45点630720/490000、55点770880/630000，分别225/275完整wall。预留实际时间，旧1101.761秒只是规划参考。
5. **实际选择/规则/模型先冻结，才读取/hash E34最终输入**，最终输入路径与size/mtime取第9会话元数据，配置必须是exact2000而非prefix。建立`reviews/prequery_freeze.json`覆盖选择/评分表/目录/协议/config/全部模型文件/全部E91 src.py/E73二进制/最终queries、GT和row身份，另记录最终输入第一次读取时间与预选择seal。底层base/NSG沿E74身份，只stat核验；不重新hash数GiB大图。
6. 设OMP/OPENBLAS/MKL/NUMEXPR/BLIS线程1、OMP_DYNAMIC=FALSE、MPLCONFIGDIR=/tmp适当路径，用taskset CPU15依次运行v3控制器Web、Y（命令见下）。每个工具terminal0后才启动下一集；全部完成再执行v3分析器。分析生成完整原点/每轮wall/配对/全部零query全GT与返回/三组QPS图/失败图/成本；最后需要作者对完整前沿作诚实结论、补入继承离线成本、实际进程/最终文件封存和根文档同步。

```bash
# 仅在另一个实际最终目录完成上述选择与冻结后使用；不要对本工具夹具运行。
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 BLIS_NUM_THREADS=1 OMP_DYNAMIC=FALSE taskset -c 15 .venv_cpu/bin/python -B entry_method_exploration/20260913_until2100_v1/stage32_final_tooling_v1/src/run_frozen_v3.py /data/netg/ACSG/entry_method_exploration/20260913_until2100_v1/ACTUAL_FINAL_RUN webvid2_5m_light_v1
# Web terminal0后同样运行Y；两集terminal0后调用analyze_frozen_v3.py ACTUAL_FINAL_RUN。
```

`results/non_executable_metadata_fixture*`是纯软件夹具，含E34路径但只stat；hash hook被测试替身替代，最后留成无效控制选择、缺SHA身份。**它不是实际选择，不能复制它的伪评分/伪规则用于最终运行。** v3元数据测试确认控制best_all在最终payload hash之前被拒绝。

[前瞻协议](protocol.md) · [v3完整核验](results/v3/tooling_verification.json) · [元数据闸核验](results/frozen_metadata_verification_v3.json) · [候选目录核验](results/inventory_verification.json) · [既有批完整失败全表](results/v3/failures.csv)。最终实测仍未运行，E91不是性能改善或最终GO。

兼容范围说明：evaluator SHA不等是本工具要求先做语义兼容审查的停止条件，不证明旧方法本质不支持。最终候选池只能声称实际核对/评分的那一部分；不能说76项都排过名。若证据选择了旧二进制候选，应核对实现语义或建立相应明确工具版本，不为方便而静默删去该候选。
