# 既有WFree的锚定几何审查

2026-09-20。只读E104每集原fit2048/cal512 query、C8/teacher mask/原P/最终WFree，以及E105已曝光的全部4096条query；E105不读GT或失败标签。用于检验“score anchor在新query上严重失控”的具体解释，不改任何模型。

先冻结全部输入、源码与下述统计，再计算新指标：逐hub有效C8 query支持数及其监督秩上界；fit/cal/E105单位query的二阶矩；最终Delta在三组中的全H平均平方分数漂移和比值；以正定fit二阶矩求cal/E105的最坏方向广义特征值。若fit矩阵数值不正定，记录该条件不成立，不加ridge或筛维度补做。单独逐query保存平均漂移，不能根据它选择样本或模型。

直接QDelta与trace(Delta C Deltaᵀ)两种算法互验，fit原training_runs score_drift用明确浮点容差复原；不把线性分数计算当作新的ANN/NSG或新Recall。新query均已曝光，不标作盲测。无论统计结果如何均无自动训练分支。

CPU15/所有数值库线程1，最多30秒、输出≤16MiB；原query/权重/标签全SHA前后核验；保存全部结果与条件不成立项。0新模型训练/GT/图/搜索，旧WFree保持停止，成本为只读矩阵统计。
