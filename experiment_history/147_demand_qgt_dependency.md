# 147：按需QGT精确标签的依赖核验

2026-09-30完成。原QGT5K选H程序只实际读取815/821行GT，全部是非空簇首代表，无query或平铺回退；4185/4179行没有消费。保持原cluster/query排序和第一个未使用真实ID逻辑后，H逐位恢复；完整数组控制和新生成GT独立重放均通过。

Web实际最高用到rank3，Y为rank1，但后续仍保留原top100，不能把观察结果当普遍上限。少数代表亲和并列须保留原argsort语义。按需缓存oracle与全量物化可用程序状态归纳证明等价，前提是GT排序一致；最坏仍可能需要全量标签。

2次固定QGT聚类、0新GT/NSG/ANN/画像，分析0.726秒，1636行独立选择核验通过。尚无本方法实测wall，不按标签数量比例换算；下一步独立冻结真实构建。此为消除未消费标签的工程优化，不声称新主动学习方法，默认与线上候选不变。

证据：[报告](../entry_method_exploration/20260930_theory_until2200_v1/research/demand_qgt_v1/report.md) · [等价性推导](../entry_method_exploration/20260930_theory_until2200_v1/research/demand_qgt_v1/theory.md) · [统计](../entry_method_exploration/20260930_theory_until2200_v1/research/demand_qgt_v1/results/summary.json)。
