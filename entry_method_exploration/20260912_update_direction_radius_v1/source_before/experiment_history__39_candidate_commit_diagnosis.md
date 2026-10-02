# 39. E50 候选到均值转化诊断

2026-09-12，`COMPLETE_CANDIDATE_COMMIT_DIAGNOSIS_UPDATE_TRANSFER_BOTTLENECK`，接续门`PASS_CANDIDATE_COMMIT_CONTROL_GATE`。

| 数据集（RL两seed） | 有净正候选步骤/400 | 其中均值命中全空 | J-best单步净值和 | 原均值净值和 | 越界选中候选 |
|---|---:|---:|---:|---:|---:|
| WebVid | 214 (53.50%) | 184 (85.98%) | 1207 | 51 | 0 |
| Yandex | 97 (24.25%) | 93 (95.88%) | 409 | 10 | 0 |

已测候选到确定更新的转化是明确瓶颈，不能再把主要原因说成完全没有局部可用动作。WebVid RL两seed 400步中214步有净正候选，其中184步（85.98%）Adam均值命中完全不变；Yandex97步有净正候选，其中93步（95.88%）均值不变。J-best包含不动并使用原完整目标，在两个数据集的独立单步反事实净值和为1207/409，原实际均值为51/10。前者不能串成同一条新训练轨迹，不能作为新模型Recall；它只证明原状态中存在已观测而均值未利用的机会。

原目标的成本/失败/漂移项没有在这些状态中让J-best放弃最大净命中：所有八run的J-best净命中和等于hit-best，逐step的hit-best净值按定义不小于J-best，故逐step均相等。不能由此否认成本对方向或新状态的影响。J-best选中系数全部在±2内，不需要扩大旧确定参数边界才得到这些候选。

冲突仍在，但不是“无可提交动作”的证据。RL两seed中，WebVid J-best累计gain1394/loss187；Yandex421/12。逐query有限oracle与hit-best之间，WebVid2012−1207=805分成未覆盖618、自身损伤187；Yandex489−409=80分成未覆盖68、自身损伤12。不同状态或重复query的合计仅作诊断，tie按净命中/J/原序决定，差额不能等同全表示不可避免的冲突。

## 核验与范围

固定E47全部1600状态/12800候选，不挑正例。重建原完整train4096缓存，保留每条真实route NDC/原NSG返回，原J/reward完整恢复；C+八候选的J-best和hit-best、实际均值M分别计算。14400分支cache hash及135648条冷启动/变化patch独立集合评分通过，原画像漂移/失败/NDC和有限oracle分解保持。0新NSG/HNSW/构图/优化/开发/GT，耗时39.760s；原E37–E49全SHA保护。

该结果证明转化缺口存在，尚未因果证明只需放大Adam就能解决，也未验证持续提交候选后的泛化。原E49的WebVid局部正值和Yandex五L平值保持，默认未替换。

## 接续

下一步实施独立固定状态步长/方向控制：RL双seed两集step20/40/…/200，40个原状态；沿实际Adam系数方向放大到GT无关原候选半径的1/4、1/2、1倍，沿原J-best候选方向取1/4、1/2，保留原端点。全部真实路由与合法缓存补测，区分原步长未跨边界、方向错过候选和有限半径内无响应。该控制不能凭较大一步正值代替连续学习。

E50预锁的候选择优提交接续门双集通过，随后做同样σ/两seed/200×8/full4096的连续贪心局部搜索对照：原J在已测候选+不动中择优，越界候选不提交；新状态真实重测、缓存随实际提交更新，不使用旧分岔反馈。明确该对照不是RL，不扩原E47训练预算。最终仍按用户要求与NSG/Fast/FastGT作同批QPS/Recall/失败率比较，21:15前冻结最终候选窗口，21:40停止新查询，22:00收口。


[协议](../entry_method_exploration/20260912_candidate_commit_diagnosis_v1/protocol.md)、[全部1600步骤](../entry_method_exploration/20260912_candidate_commit_diagnosis_v1/results/steps.csv)、[八run统计](../entry_method_exploration/20260912_candidate_commit_diagnosis_v1/results/runs.csv)、[接续门](../entry_method_exploration/20260912_candidate_commit_diagnosis_v1/results/gate.json)、[独立核验](../entry_method_exploration/20260912_candidate_commit_diagnosis_v1/reviews/verification.json)、[实现](../entry_method_exploration/20260912_candidate_commit_diagnosis_v1/src/analyze_verify.py)。
