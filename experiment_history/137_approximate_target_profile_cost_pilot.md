# 137 E125近似目标画像的构建费用试验

2026-09-22，**STOP_APPROX_TARGET_PROFILE_PILOT**。保持原H/20K/GT10公式、温度、prior、小图与主搜索，原NSG medoid固定K100、Web L1250/Y L256生成训练目标，消费前十；QGT5K exact仍保留。是监督获得费用假设，不延续E124服务编译或宣称蒸馏创新。

近似目标单线程完整作业64.591/28.040秒，对应record135八CPU exact20K搜索312.862/1417.293秒；两集成本门通过，但非同线程加速比。画像相对原件中位偏移0.980°/2.082°，两个exact控制逐位恢复。

E105已曝光、与训练query字节互斥的4096query/集，三L三重复，24方法点/72轮CPU15实际单线程完整wall。12点召回均值均未损失超过0.10pp、QPS变化均在−0.2161%至+0.0893%；Web K1/L1000为−0.097656pp，98.75%区间[−0.292969,+0.073242]未过预锁−0.25pp下界。其余主点分别Web K100−0.002686pp、Y K1+0.097656pp、Y K100−0.016357pp，质量区间门通过。停止因未证明风险足够小，不是证明普遍损伤；不追加数据/教师L/阈值补过。

全部默认输出/距离bits/入口/两种NDC恢复E105，warm/plain/count与链接E99一致。独立两候选画像重聚合、98304返回评分、60数组、4区间、192float64距离及219身份通过。初版Engine加载了未调用的Router，另实现不读取画像/图的生成器，64条完整标签及E99恢复；原labels/成本不改，附加128 NSG。

合计532096 NSG、491520 ANN、2候选画像/图、2exact画像控制重建，0新exact GT/新源/K10。主控制器942.966秒，分析1.525秒，独立数值审计4.621秒，依赖审计23.697秒。0执行阶段prepare循环错误及修正版保留。默认Web soft/Y hard、生产E99保持。

证据：[报告](../entry_method_exploration/20260922_until2200_improvement_v1/stages/e125_approximate_target_profiles_v1/report.md)、[预锁协议](../entry_method_exploration/20260922_until2200_improvement_v1/stages/e125_approximate_target_profiles_v1/protocol.md)、[门](../entry_method_exploration/20260922_until2200_improvement_v1/stages/e125_approximate_target_profiles_v1/results/gate.json)、[独立核验](../entry_method_exploration/20260922_until2200_improvement_v1/stages/e125_approximate_target_profiles_v1/reviews/independent_audit.json)。
