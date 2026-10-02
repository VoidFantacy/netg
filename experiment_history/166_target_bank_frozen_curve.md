# 166 冻结目标库的相邻预算曲线

2026-09-30完成。`COMPLETE_FROZEN_CURVE_RETAIN_WEB_R1_TRADEOFF`；默认与E99保持。165的查询样本迁移仍停止。本项只核对简单TargetBank控制的质量余量能否形成完整线上收益。

原20K物理目标图、映射/ef10不变，原三入口/完整原路由后rank1/目标单入口三方法；每个原点及E105旧网格前后邻一次固定，共36点/108轮wall。E105历史4096条/集，真实K1/K100、CPU15实际1线程、串行。0新GT、训练、图或held-out访问。

| 组合 | 各自最快实测R90的L | 默认实际Recall / QPS | TargetBank实际Recall / QPS |
|---|---:|---:|---:|
| WebVid R1 | 1000 | 90.454102% / 417.190 | 90.991211% / 413.177 |
| WebVid R100 | 1250 | 90.581543% / 334.895 | 90.576416% / 333.291 |
| Yandex R1 | 128 | 90.625000% / 2364.615 | 90.625000% / 2283.658 |
| Yandex R100 | 256 | 91.044434% / 1289.884 | 90.885010% / 1264.985 |

Web R1在L800/1000/1250相对默认分别+0.659180/+0.537109/+0.390625pp，QPS−1.8363/−0.9620/−1.0204%；前两描述区间正、第三下界0，保留局部质量/速度取舍。Web R100微负近似持平；Y无稳定质量优势。目标库12个同预算点都更慢，全部72个预定跨预算比较无经验支配点，四组合最快实测90%点均未加速。网格稀疏，既不外推所有可能预算，也不靠插值称同Recall收益。

147456返回行独立评分、真实成员增损、72比较/R90选择/整数bootstrap通过，最大区间差0。全部原生、Default3历史回归、中心三方法165回归、图/输入/源码身份通过。新增596160 NSG/595584 ANN，作业1010.691秒、编译8.178秒。关闭有限曲线，不扩L/ef/样本/重复调到通过。

[报告](../entry_method_exploration/20260930_theory_until2200_v1/research/target_bank_frozen_curve_v1/report.md) · [协议](../entry_method_exploration/20260930_theory_until2200_v1/research/target_bank_frozen_curve_v1/protocol.md) · [全部表](../entry_method_exploration/20260930_theory_until2200_v1/research/target_bank_frozen_curve_v1/results/tables.md) · [统计](../entry_method_exploration/20260930_theory_until2200_v1/research/target_bank_frozen_curve_v1/results/analysis.json) · [独立核验](../entry_method_exploration/20260930_theory_until2200_v1/research/target_bank_frozen_curve_v1/reviews/independent_audit.json)。
