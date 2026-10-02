# 130 决策遗憾与GT监督关联的只读机制检查

2026-09-22，22:00活动目标中的两项机制检查，不新增性能实验号。

E122主模型的全H召回遗憾精确分成“固定最高分入口的排序遗憾”和“是否采用该入口的开关遗憾”。即使给免费正确开关，当前排序只覆盖全H机会的Web K1/K100 13.01%/19.56%、Y21.82%/23.46%；排序项占总遗憾76%–86%。因此没有依据只调回退阈值。四图正则控制的逐query动作平均预测完全一致，符合L1=0的正规方程推论；局部平滑没有改变这一公共成分。1024标量检查、206输入身份通过，2.830秒，0新模型/搜索。

随后固定同4096 query和H，恢复原GT1/GT10归属，与实际R1/R100作同样本量分半的中心化query—动作交叉协方差重复性比较。GT10-hard为Web0.6680/Y0.6986、Web soft0.7381；真实R1为0.3914/0.3036，R100为0.4000/0.4034；打乱标签约0。全部六个1024折配对也保留，非独立重复。不同监督总体目标不同，不能仅由稳定性归因全部性能或承诺更多数据能解决。

事后交叉对齐为正但弱，GT10监督与实际响应的矩阵余弦约0.06–0.11。说明稳定语义与真实搜索的桥仍不足，促成E123单独冻结的目标区域—服务检验。已核对当前Web t1温度实际为0.016201而非1，没有按高温Taylor假设改画像。

81920目标归属恢复原件，608标量检查与18个独立双Gram核算通过，最大差4.17e−17；147小输入SHA保持，大base只声明stat及消费目标SHA。主分析2.693秒、审计1.830秒，0新ANN/NSG/GT/画像/图/模型/QPS。

证据：[决策分解报告](../entry_method_exploration/20260922_until2200_improvement_v1/research/decision_decomposition_v1/report.md)、[监督稳定性报告](../entry_method_exploration/20260922_until2200_improvement_v1/research/supervision_moment_stability_v1/report.md)、[原协议](../entry_method_exploration/20260922_until2200_improvement_v1/research/supervision_moment_stability_v1/protocol.md)、[后继排重](../entry_method_exploration/20260922_until2200_improvement_v1/literature/successor_screening.md)。
