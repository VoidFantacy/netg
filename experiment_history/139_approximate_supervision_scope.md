# 139 近似监督费用依赖与有限总体纠偏方向

2026-09-22只读源码/文献审查，0新搜索、标签、拟合、图或性能点。E125 Web温度0.016201138496398926来自原20K精确GT1的真实hub最高/次高分数gap中位，候选直接继承；Y-hard为None。原近似标签作业计时真实，新源复测有效；费用结论限于继承H/参数，尚无新数据集从零低成本构建验证。原画像脚本还读exact GT做控制/诊断，不能称整个实验完全无旧GT。

提出但未实施经典差值估计：固定教师/H/参数，v_hat=u+Σz_i+(N/m)Σ_S(y_i−z_i)，S为N中均匀无放回m个精确补标。向量总和设计无偏，均方误差N²(1−m/N)tr(S_residual)/m；unit后的方向与Recall无无偏或改善保证，稀少残差可能使校正更差。需比较同精确样本预算简单基线，不能用新测试选择规则。PPI第1.2–1.4节/附录B与经典差值估计前作已核对，不声称新发明。

当前仍保留低成本候选、不改原默认；没有复测之外的新候选或队列。[报告/推导](../entry_method_exploration/20260922_until2200_improvement_v1/research/approximate_supervision_scope_v1/report.md) · [源码身份](../entry_method_exploration/20260922_until2200_improvement_v1/research/approximate_supervision_scope_v1/source_review.json)。
