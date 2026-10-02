# 157 固定Energy选样的两批新源检索验证

2026-09-30，`COMPLETED_NO_STABLE_ENERGY_RECALL_GAIN_RETAIN_COST_CANDIDATE`。每集2×4096新query，Default／同预算Uniform／Shuffled／Energy及参数在源读取前冻结；真实K1/K100、CPU15实际单线程、全部96轮完整wall和输出核验通过。

| Energy相对 | Web ΔR1 / ΔR100 (pp) | Y ΔR1 / ΔR100 (pp) |
|---|---:|---:|
| Uniform | +0.012207 / −0.001343 | −0.061035 / +0.003784 |
| Shuffled | +0.036621 / +0.005127 | −0.048828 / −0.004639 |
| Default | −0.109863 / −0.026123 | −0.048828 / −0.003174 |

Energy相对Uniform四个描述区间均跨0；Web R1仅净+1、Y净−5，R100两集都跨批异号。相对Default的Web两点、两批均负，合并未校正95%区间分别[−0.219727,−0.012207]／[−0.039185,−0.014526]。不能把训练方向改善写成稳定召回增益。停止本版选择器参数探索，保留低成本候选，默认不变。

合并Default R1/QPS1、R100/QPS100：Web91.198730%/412.839、90.605103%/334.329；Y91.516113%/2335.782、91.037231%/1306.000。Energy分别Web91.088867%/413.549、90.578979%/334.938；Y91.467285%/2339.041、91.034058%/1303.324。Energy对Uniform四点QPS均值略高，但全部轮次保留、固定点非完整曲线或统计速度保证。每方法／每批绝对表见完整报告。

完整构建沿154／156：Default336.051/1519.754秒，Energy131.133/259.137秒，单次少60.98%/82.95%；原默认已同享QGT按需优化。共享Faiss计算路径另列待测，不外推新费用。Uniform的Web控制和Shuffled共享增量不合成独立完整成本。

全部GT、mask、返回、E99、线程、身份和区间先核验再解释。新GT16384、32条float64全库检查；全部命中变化且小间隔名单为空，没有额外GT、删行或改标签。131072返回、256组分数、72个分布检查及37身份通过；分析3.649秒、主审计16.915秒。原生NSG655872含512 E99、ANN655360；0新模型／图。

固定来源不是全源随机／语义独立；72个描述比较未作家族校正，一个Shuffled模型不构成置乱检验，query区间不含训练种子不确定性。下一步只读分解画像→实际入口→主返回，然后检查共享精确标注工程费用；不按已曝光query补标或调参。

[完整报告](../entry_method_exploration/20260930_theory_until2200_v1/research/energy_fresh_transfer_v1/report.md) · [协议](../entry_method_exploration/20260930_theory_until2200_v1/research/energy_fresh_transfer_v1/protocol.md) · [全部结果](../entry_method_exploration/20260930_theory_until2200_v1/research/energy_fresh_transfer_v1/results/summary.json) · [主核验](../entry_method_exploration/20260930_theory_until2200_v1/research/energy_fresh_transfer_v1/reviews/independent_audit.json)。
