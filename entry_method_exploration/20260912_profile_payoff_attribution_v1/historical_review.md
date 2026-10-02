# 接续前的旧表示路线复核

本轮完整阅读历史11、17–21，并核对当前spec相应合同及原源码/协议的目标部分，没有运行旧脚本、解码其原评估输入或重做模型。

- E22 [详细11](../../experiment_history/11_ab_fixed_slot_exploration.md)：自由低秩W加可学习mapping已做过，原[src/train.py](../20260909_ab_experiment_v1/src/train.py)使用效用软遗憾；映射与画像作用不能混为共享低秩的因果证据。
- E28 [详细17](../../experiment_history/17_gt10_shared_transform.md)：[原train.py](../20260911_gt10_shared_transform_v1/src/train.py)明确实现独立H×d的free delta及共享linear/MLP，normalize后静态部署。存在free参考不能证明原共享模型容量是失败主因。
- E29 [详细18](../../experiment_history/18_teacher_objective_alignment.md)：教师/目标2×2与原画像保留控制仍是全局拟合；未隔离某个新增hub画像与其余画像。
- E30 [详细19](../../experiment_history/19_equivalent_teacher_sets.md)及[原协议](../20260911_equivalent_teacher_sets_v1/protocol.md)：等价完整集合及平均位移匹配不匹配逐hub方向，更不等于单hub反事实。
- E31 [详细20](../../experiment_history/20_training_effectiveness.md)及[原协议](../20260911_training_effectiveness_v1/protocol.md)：同表示/教师只改优化日程，未验证新增局部自由度。
- E32 [详细21](../../experiment_history/21_direct_reward_policy.md)及[原train.py](../20260911_direct_reward_policy_v1/src/train.py)：已有真实收益与完整动作目标，不能简单以“改为直接reward”换名复跑。

所提2×2只复制既有W的行以定位局部联动，区别于旧全局训练，也不声称新模型族或新性能方法。本轮只读复核；更完整的新训练选择仍须追溯旧协议/实现/结果，不能因个案通过直接扩模型。
