# 112｜统计目标、教师量化与锚定几何审查

2026-09-20，纯理论/历史复核及两项只读缓存分析；不是新的性能候选。E114完成后，继续明确GT10的统计意义与学习器失败的解释边界。0新NSG/ANN/GT/图/训练；默认Web soft/Y hard、生产E99保持。

GT10归一化加权平均不需要vMF假设即可给出单位query均值的方差恒等式与总体亲和风险界；须条件于固定H和IID query，GT10的十个目标不是十个独立样本。方向一致性和支持量共同影响估计，仍无真实搜索效用保证。Good–Turing单例统计与旧未见GT1比例数量级相符，表明精确目标ID记忆很稀疏；这不是GT10/图搜索的Recall上界或IID验证。

5120条旧fit/cal、56动作整数审查确认原等K最大值teacher等价于先最大K1再最大K100。两集cal的单独K100 oracle相对原teacher只多0.185547/0.064453pp；原teacher的更大收益本已存在，不能用按K拆模型解释学生未迁移。全部旧oracle/teacher harm比例恢复，0.128秒。

旧WFree分数锚定的矩阵形式及监督支持核验：cal/E105平均平方漂移相对fit为Web0.9356/0.9314、Y0.9752/0.9759，没有整体放大。最坏方向协方差界与实际模型漂移分开；每hub非恒定C8教师支持中位数13/10，全部少于参数维度，但全H锚定仍约束模型，未作失败因果定论。10,889,216个旧模型分数残差坐标，0.411秒，原fit漂移与矩阵恒等式恢复。

源码回查确认全H集合CE、结构化margin、保留teacher、多teacher、延长优化、精确期望真实收益及query二阶矩构图均已有实测版本；固定线性图特征/线性双塔还需排除评分折叠等价。不能把换损失、网络名称或统计量当成新的方法贡献。终点闭合的后处理无变化结论明确依赖边界tie保留；不同ID并列可带来不同后续出边。

[统计推导](../entry_method_exploration/20260920_until1900_theory_v1/research/weighted_mean_statistical_scope.md) · [缺失目标质量](../entry_method_exploration/20260920_until1900_theory_v1/research/missing_target_mass.md) · [教师审查](../entry_method_exploration/20260920_until1900_theory_v1/research/objective_quantization_v1/report.md) · [锚定审查](../entry_method_exploration/20260920_until1900_theory_v1/research/score_anchor_geometry_v1/report.md) · [前作排除](../entry_method_exploration/20260920_until1900_theory_v1/research/prior_work_and_representation_exclusions.md) · [终点后处理边界](../entry_method_exploration/20260920_until1900_theory_v1/research/terminal_closure_implications.md)。
