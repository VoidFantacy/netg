# 153 方向收益选样未超过简单能量控制

2026-09-30，`STOP_FIXED_ALIGNMENT_TREE_RETAIN_ENERGY_CONTROL_SIGNAL`。有限总体理论补齐直接替换风险中的全局内积／二阶包含概率，并推导同pilot估计方向收益的自包含偏差及条件leave-one-out修正。已有主动选样前作，不称新通用理论。

保持总2048精确预算：共同1024 pilot＋剩余1024；16固定种子、原八维廉价特征、深度2／叶128。主LOO树、未经修正树、EnergyTree、打乱LOO监督和Uniform均在训练侧比较，所有预测与选行先冻后评分。Web仍用旧全GT温度，不冒充从无标签构建。

| 方法 | Web平均chord²比Uniform | Y平均chord²比Uniform |
|---|---:|---:|
| LeaveOneOutTree（预定主） | 0.924464 | 0.790357 |
| SelfIncludedTree | 0.935284 | 0.766705 |
| EnergyTree | 0.931361 | 0.766705 |
| ShuffledLeaveOneOutTree | 0.975799 | 0.994830 |

主候选虽双集均改善随机且过两半检查，但Y不及简单EnergyTree，未过预定完整接续门；停止这一版，不改深度／特征／样本／种子。Energy控制保留局部信号：平均方向误差少6.864%／23.330%，Web13/16、Y16/16更好；Y未经修正树与Energy选择结果相同。它不是本主候选通过，更不是Recall收益。

若后继简单控制，先独立冻结、消除旧温度依赖，保留同温度同预算Uniform与打乱控制；再谈真实构建与路由，不能据新源151损伤query补标或按数据集拼最好选择器。条件无偏的选样收益目标不保证其回归／排序后的真实优势。

分析9.135秒、核验10.333秒，64个Bernoulli子集／60个条件子集、256万次树前向、128条配对内积、40次完整混合贡献复算与14身份通过。160个RAM合力／128棵小树；0新GT/NSG/ANN/部署画像/图/性能，默认保持。

[报告](../entry_method_exploration/20260930_theory_until2200_v1/research/replacement_alignment_v1/report.md) · [理论](../entry_method_exploration/20260930_theory_until2200_v1/research/replacement_alignment_v1/theory.md) · [协议](../entry_method_exploration/20260930_theory_until2200_v1/research/replacement_alignment_v1/protocol.md) · [完整结果](../entry_method_exploration/20260930_theory_until2200_v1/research/replacement_alignment_v1/results/summary.json) · [独立核验](../entry_method_exploration/20260930_theory_until2200_v1/research/replacement_alignment_v1/reviews/independent_audit.json)。
