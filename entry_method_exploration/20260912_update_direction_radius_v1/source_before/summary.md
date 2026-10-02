# ACSG 当前结果摘要

2026-09-12，最近完成E50，`COMPLETE_CANDIDATE_COMMIT_DIAGNOSIS_UPDATE_TRANSFER_BOTTLENECK`。[报告](entry_method_exploration/20260912_candidate_commit_diagnosis_v1/report.md)、[历史39](experiment_history/39_candidate_commit_diagnosis.md)。

| 数据集（RL两seed） | 有净正候选步骤/400 | 其中均值命中全空 | J-best单步净值和 | 原均值净值和 | 越界选中候选 |
|---|---:|---:|---:|---:|---:|
| WebVid | 214 (53.50%) | 184 (85.98%) | 1207 | 51 | 0 |
| Yandex | 97 (24.25%) | 93 (95.88%) | 409 | 10 | 0 |

已测候选到确定更新的转化是明确瓶颈，不能再把主要原因说成完全没有局部可用动作。WebVid RL两seed 400步中214步有净正候选，其中184步（85.98%）Adam均值命中完全不变；Yandex97步有净正候选，其中93步（95.88%）均值不变。J-best包含不动并使用原完整目标，在两个数据集的独立单步反事实净值和为1207/409，原实际均值为51/10。前者不能串成同一条新训练轨迹，不能作为新模型Recall；它只证明原状态中存在已观测而均值未利用的机会。

原目标的成本/失败/漂移项没有在这些状态中让J-best放弃最大净命中：所有八run的J-best净命中和等于hit-best，逐step的hit-best净值按定义不小于J-best，故逐step均相等。不能由此否认成本对方向或新状态的影响。J-best选中系数全部在±2内，不需要扩大旧确定参数边界才得到这些候选。

冲突仍在，但不是“无可提交动作”的证据。RL两seed中，WebVid J-best累计gain1394/loss187；Yandex421/12。逐query有限oracle与hit-best之间，WebVid2012−1207=805分成未覆盖618、自身损伤187；Yandex489−409=80分成未覆盖68、自身损伤12。不同状态或重复query的合计仅作诊断，tie按净命中/J/原序决定，差额不能等同全表示不可避免的冲突。

1600状态/14400缓存分支及135648独立集合评分通过，0新搜索。最近完整Recall–QPS仍E49：WebVid RL仅L128局部正，Yandex五L质量平；没有双集前沿增益，默认保持WebVid GT10-soft-t1 / Yandex GT10-hard。

接续固定状态步长/方向反事实与独立连续候选择优提交，详见[s-target](s-target.md)。用户目标至22:00并要求最终最佳候选对NSG/Fast/FastGT的QPS/召回/失败率，最终完整比较尚未执行。
