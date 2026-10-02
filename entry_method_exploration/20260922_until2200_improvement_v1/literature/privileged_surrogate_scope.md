# 特权教师与决策代理：一手文献适用范围

2026-09-22晚间核对原文方法和条件。以下不产生新的训练路线。

[Lopez-Paz等，ICLR2016，Unifying distillation and privileged information](https://leon.bottou.org/publications/pdf/iclr-2016.pdf)：核对§3、§4.1和§4.3。论文区分重建特权表示与学习教师软标签；其优势分析显式含教师误差、学生拟合教师的误差和学习速率假设。因此有用教师并不自动保证学生能低成本继承收益。E123/E124符合这一警示，但本地服务表并非该论文实验，不能借文献证明此处更大模型会成功。传统蒸馏/特权学习不是本项目新颖性。

[Liu、Grigas，NeurIPS2021，Risk Bounds and Calibration for a Smart Predict-then-Optimize Method](https://proceedings.neurips.cc/paper_files/paper/2021/file/b943325cc7b7422d2871b345bf9b067f-Paper.pdf)：核对§2–3及Theorem2.1。它将预测误差与实际决策损失区分，并给定分布/几何条件下的校准界；所引Fisher一致性定理需要条件连续、关于均值中心对称、唯一最优等前件，不能未经验证套到当前离散确定性搜索标签。论文也明确最小二乘在真实成本预测问题有风险传递结果，不应把本地有限样本失败写成MSE普遍不一致。当前更关键的是E124拟合的服务代理本身不同于真实效用；改成SPO名称不会自动修复标签偏差。

[Elmachtoub、Grigas，Smart Predict, then Optimize原文](https://arxiv.org/abs/1710.08005)的摘要与以上原文给出直接决策损失的前作。项目E29结构化margin、E32精确期望收益、E119多损失与强模型已存在；本轮不以换损失重启。新的只读分解和反例见[语义决策几何](../research/semantic_decision_geometry_v1/theory.md)。
