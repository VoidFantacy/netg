# 110｜E113实际搜索比较对支持

2026-09-20。由同GT1内部搜索分支反例，先检查实际比较节点对是否能形成跨query共享特征。仅E104 fit2048/集，原anchor及相同56标签中的最大等K teacher，真实K1/K100/L128。原kernel控制与记录fork的全部ID/距离bits/NDC均恢复历史动作，K1/K100比较集合一致。

Web/Y分别14,407,197/18,430,741个不同节点对；97.7842%/99.2891%只被一条query比较，最大支持48/27。预锁每对≥32query、两符号各≥8不同GT1，要求32个非零差向量覆盖半数query；Web仅10对覆盖7.2754%，Y0，整体STOP_EXACT_PAIR_FEATURE_DICTIONARY。不改阈值/规模、扩数据或转选单集训练。

32768次NSG为原4096条fit query的重复动作/K/控制核验；0ANN/GT/新图/梯度或画像训练/QPS。记录进程含加载约39.60秒、分析5.660秒。原件/8192行/全部输出SHA核验通过；include相对依赖在首次编译前显式补全，无失败搜索。具体ID对支持不足不等于所有图条件抽象不可共享，也不是GT10最优证明。默认Web soft/Y hard、生产E99保持；整体任务仍至19:00。

[完整报告](../entry_method_exploration/20260920_until1900_theory_v1/stages/e113_comparison_support/report.md) · [原始门](../entry_method_exploration/20260920_until1900_theory_v1/stages/e113_comparison_support/results/gate.json) · [全部统计](../entry_method_exploration/20260920_until1900_theory_v1/stages/e113_comparison_support/results/shared_support.csv)。
