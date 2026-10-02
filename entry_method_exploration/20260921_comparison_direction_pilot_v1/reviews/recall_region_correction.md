# 搜索区域与Recall不变条件的补充

在全量Web标签仍运行、模型训练与接受载荷物化前，复核method.md发现原文把“相同返回集合”直接推到“相同Recall”，没有显式要求不同query的GT也相同。原文已保留在[修改前快照](recall_region_correction_before/method.md)，四份文档身份见[快照清单](recall_region_correction_before/identity.json)。

更正后的推导区分两个区域：只固定搜索中所有相关比较的结果，可以归纳保证搜索状态、返回ID及图工作量相同；若还固定精确GT排序，才保证Recall相同。把全部base点对的排序超平面也加入分区、使用固定tie规则，是后一条件的充分构造。实际32个抽样共享方向不具备这个自动保证，召回的可预测性仍是经验假设。

最小逻辑例子是固定动作在q1、q2上都返回a，但GT1(q1)=a、GT1(q2)=b，故两次Recall@1不同。例子仅澄清缺失的条件，不声称其在当前真实数据上的频率，也不构成新的性能实验。

已核对原生标签实现experiment.cpp的labels函数：每个query以qi=lo+j索引自己的GT100，hits1使用该query的GT1，hits100/mask使用该query的GT100成员关系。实现没有用“同返回即同Recall”替代GT评分。因此本次只修正理论说明，不修改搜索、GT、标签文件、特征、学习规则、预算、接受条件或已冻结的原生代码；无需因该文字错误重跑标签。后续仍执行既定的独立GT/mask与实际返回审计。
