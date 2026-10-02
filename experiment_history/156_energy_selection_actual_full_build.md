# 156 固定r0 Energy完整构建

2026-09-30，主完整费用与同预算打乱监督控制均完成并通过身份核验。Energy从无目标标签输入开始，包含全20K单线程教师、pilot1024、特征／树、第二次base载入和追加1024 GT、画像／小图与输出。

| 数据集 | Energy完整wall(s) | 默认完整wall(s) | 单次描述性节省 | Shuffled增量wall(s) |
|---|---:|---:|---:|---:|
| WebVid | 131.133096 | 336.051409 | 60.978% | 29.662551 |
| Yandex | 259.136797 | 1519.753871 | 82.949% | 89.983748 |

四个选样器的特征、树、全部预测／选行恢复155固定r0，四份V/W与冻结模拟真值重建逐位相同；原生plain/count及独立新图／分数核验通过。Web旧尾批4条距离舍入bits不同（最大8.94e−8）、ID不变，另4条float64全库top100顺序核验通过，原失败及修正版均保留。GT7780、NSG40064、ANN2048，4W/4图/4树、2QGT聚类。单次缓存条件比较，控制增量不冒充独立完整成本。

费用和身份门通过，下一步先冻结四模型与新来源再测真实K1/K100。本记录0新线上性能、默认不变。主动蒸馏已有pilot后选样框架；新颖性和搜索收益尚未证明。

证据：[报告](../entry_method_exploration/20260930_theory_until2200_v1/research/energy_full_build_v1/report.md)、[协议](../entry_method_exploration/20260930_theory_until2200_v1/research/energy_full_build_v1/protocol.md)、[费用](../entry_method_exploration/20260930_theory_until2200_v1/research/energy_full_build_v1/results/cost_summary.json)、[审计](../entry_method_exploration/20260930_theory_until2200_v1/research/energy_full_build_v1/reviews/independent_audit.json)。
