# 局部动作支持与查询间损伤：目前能判断到哪里

**局部机会存在，但支持稀疏、查询间取舍和迁移问题要按动作分别判断。现有证据不能证明共享画像空间没有更好解。**

今天 E60 固定旧的小幅画像动作，每集 40 个背景、120 个动作。Web 有 108/120 个动作在辅助 cal 上完全不改变命中，Yandex 为 114/120；迁移 audit 分别为 93/120、120/120。Web 的 9 个辅助净正动作又都不满足原 train-J 条件，最终双集支持均 0/40。这说明这组动作的有效反馈稀疏、支持条件没有交集；不能把所有失败都解释为正负收益抵消，也不能把全部不动称为风险控制成功。[原协议](../stage1_support_v1/protocol.md)、[完整动作表](../stage1_support_v1/results/actions.csv)、[详细复盘](../../../experiment_history/49_fixed_action_support.md)。

E89 改为较大的局部父画像恢复：一次将同一真实 hub 的两行子画像恢复为父画像。在 fit20K 中，Web 31/32、Yandex 26/32 个动作同时帮助一些 query、伤害另一些 query。筛选后，单项净收益之和为 297/125，实际同时安装后只有 224/114；合并不能用旧单项结果直接相加。此时确有查询间取舍和动作间相互影响，但这是不同动作与训练池，不能把这些比例当作所有 RL 动作的普遍冲突率，或最终失败案例的逐画像因果解释。[原协议](../stage30_local_parent_restore_v1/protocol.md)、[实际训练器](../stage30_local_parent_restore_v1/src/train.py)、[已验训练增损](../stage30_local_parent_restore_v1/supplement_training_v1/derivation.json)、[详细复盘](../../../experiment_history/78_local_parent_restore.md)。

最终 E94 的 Web 组合在 compact 上保留了五档质量修复，却仍未超过原 GT10-soft P；Yandex compact 的收益集中在低 L，高 L 有损伤。因此当前瓶颈是如何保留有效改道、减少新损伤并迁移到评估查询，尚未得到更好的稳定 QPS–Recall 前沿。既不能据此断言共享表示不可学，也没有证据支持只扩大 RL 模型或训练预算就能解决。[冻结最终对照](../stage35_final_comparison_v1/report.md)。

后续研究线索仅作交接：优先解释有效动作的支持范围、完整并图交互和既有收益的丢失；新的动作设计须另定数据角色、真实反馈预算和控制。已观察的最终坏例不回流选择或调参。本段只引用既有封存证据，0 新训练、ANN、GT、构图或 QPS；没有执行新的方向。
