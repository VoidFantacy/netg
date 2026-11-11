# E188：补全费用、等价优化与硬访问预算

2026-10-28，用户在现状/费用方案讨论后授权“可以，开始实验吧”。独立目录实现并完成COCO raw-IP/Deep10M squared-L2真实K100：正式100点/300完整T1轮、校准100点/300轮；不改原base/图/GT10/metric/主核。默认E99 GT10保持。

24个硬预算区域点中24个被实测GT10同时覆盖Recall与QPS；速度筛选通过0点、预算召回筛选通过0点。

Deep L200：REG-R平均扫码26134.2，BLOCK-R2048降至1962.3；额外平均耗时361.46→135.77μs，Recall增量0.4821→0.2247pp。扫描减少与救回保留必须一起判断，不把访问次数下降当完整性能收益。

分段诊断区分粗路由/特征/LUT/扫码/精算/合并；legacy诊断复用扫描缓冲，不能当原完整wall严格分解。OPT-R缓存模型/公共特征/工作空间，三L全部10K返回与REG-R逐字一致。块按PQ重构向量最大方差坐标递归划分，最多128点；每区域B/2码和48候选，B=512/2048/8192。BLOCK-C2048以12K实际预算内救回标签及非负费用模型选区，所有固定模型迁移L100/200/400。三档块法内部保持相同配额，原REG-R共同96对新每区48不属于纯扫码消融。

校准原六项均选B32，但旧16K表含末4K校准标签，属于角色设计缺陷；保留原协议/冻结/校准结果和选择，正式前另冻修正自动资格，B32仍正式参考，自动选择排除它。修正六项均选更大L GT10。没有按正式test调参或改矩阵，角色修正不包装成算法提升。

全部实际返回/三轮SHA、预算上限、旧包一致、真实主包合并oracle、stdlib二实现整数质量和float64原metric评分核验通过。E187 689文件seal保持。二实现为同一执行者，非独立人员审查。单图/模型、历史曝光test、训练角色局限和时间波动保留；无K1/其他五集新验证或逐query门控。

[完整报告](../entry_method_exploration/20261028_completion_cost_budget_v1/report_zh.md) · [六页PDF](../entry_method_exploration/20261028_completion_cost_budget_v1/ACSG_补全成本与硬预算实验_20261028.pdf) · [协议](../entry_method_exploration/20261028_completion_cost_budget_v1/protocol.md) · [角色修正](../entry_method_exploration/20261028_completion_cost_budget_v1/calibration_role_correction.md) · [冻结](../entry_method_exploration/20261028_completion_cost_budget_v1/freeze.json) · [核验](../entry_method_exploration/20261028_completion_cost_budget_v1/reviews/results_audit.json)。
