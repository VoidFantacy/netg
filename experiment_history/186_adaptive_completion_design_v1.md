# E186：不同遗漏特征的补全来源与预算适配设计

2026-10-27，用户讨论“根据数据特征不同采用不同残差补全，改进适配不同数据集的新方案”。本轮完成理论设计与验证顺序，状态**THEORY_ONLY_UNIMPLEMENTED_UNTESTED**。没有新ANN/GT/训练/构图/QPS；默认E99 GT10保持，最新正式性能E183、离线测量E185不变。

设计收敛为两个候选来源与不补全：重复遗漏目标适合固定ID表；具体ID源覆盖不足时，提出独立全base几何分区/倒排后端，按q及主结果R预测值得补查的区域，在其中重新检索真实base点，原metric精算合并。区域级遗漏标签允许提出训练残差源外ID，但可迁移性和成本优势均待验证。全base收录不是无限预算覆盖承诺。

先验证新来源，再验证R条件化相对同后端q-only的增量，最后数据集级配置选择，逐query选择器后置。初步pilot提案COCO/Deep、K100、L100/200/400；SIFT/GIST/Web/Y/Flickr保留扩展反例，后续正式真实K1/K100。动作允许不补；完整费用对比附近更大L的GT10，不能以相同精算候选量冒充同费用。

历史差异：E174/E175从旧残差候选作种子在同NSG上一跳，E176细条件仍为固定ID表；新候选要求独立来源和区域内query检索。IVF/PQ、候选分类、adaptive probing已有前作，不主张组件本身新颖；实质研究对象是主结果条件化的剩余区域选择及可支付性。新接口、后端和选择器均未实现，也没有新未曝光确认角色或已分配运行预算。

[完整设计](../entry_method_exploration/20261027_adaptive_completion_design_v1/design_zh.md) · [状态](../entry_method_exploration/20261027_adaptive_completion_design_v1/state.json) · [修改前快照](../entry_method_exploration/20261027_adaptive_completion_design_v1/source_before/) · [下一阶段目标](../s-target.md)。旧E174–185科学产物/失败记录与seal保持原件，不恢复旧runner。
