# C 第一阶段：同状态一次有限动作诊断

**C0/C1通过，C2完成后按预注册门停止。** 状态：`NO_GO_UNCONDITIONAL_HEADROOM_STOP_C`。

当前C为第一优先级并已执行首阶段。WebVid L64/L128 oracle无条件增益为+0.980/+0.635pp；Yandex为+0.230/+0.140pp，未达到四点均≥+0.5pp的实质门。该结果只针对共同额外graph-NDC cap的冻结配置，不是等成本或Pareto GO。

- [完整报告](report.md)：C0/C1/C2结果、校正区间、覆盖、逐动作比例、NDC envelope、机制与clone/state成本。
- [实际命令](commands.md)、[机器命令台账](logs/commands.jsonl)、[状态](state.json)。
- [协议](protocol.md)、[锁定配置](config.locked.json)、[协议锁SHA](protocol_lock.json)、[保护manifest](source_manifest.json)。
- [C1 gate](results/c1_gate.json)、[C2主统计](results/analysis_v1/report.json)、[C2 gate](results/analysis_v1/gate.json)。
- [WebVid原始分支/完整prefix state](results/c2_main_webvid_v1/)、[Yandex原始分支/完整prefix state](results/c2_main_yandex_v1/)。
- [独立kernel终审](reviews/kernel_final_review.md)、[统计预审](reviews/c2_statistics_pre_review.md)；独立统计终审及文档终审均保存于`reviews/`。

没有运行C3 learner/state×reuse、C4正式Recall–QPS、validation/held-out、全H动作、多checkpoint、多步RL或A+B联动。未修改原search_new、冻结base/graph/metric/GT或Fast/A+B产物。旧C R0目录保留设计历史身份。
