# 限时理论研究工作记录

2026-09-20 13:05:42–16:00（北京时间）。E107–E111及综合推导均已完成；当前仅证据审查与截止验收，没有在运行的搜索或训练。最终时间边界以[父状态](../state.json)为准。

[综合报告](../report.md)将GT10的闭式方向目标、H自适应入口收益、画像的小图可检索性、多入口首展开竞争与实际Recall分开。没有稳定新方法替换，原Web soft/Y hard及生产E99保持。

| 阶段 | 当前结果 |
|---|---|
| [E107](../stages/e107_initialization_factorial/report.md) | 初始化因素144点完成；单位H入口已有明显收益，多入口无一般单调保证 |
| [E108](../stages/e108_unit_hub_online/report.md) | 三控制54点/162轮完整wall；UnitHub无跨数据替换 |
| [E109](../stages/e109_perfect_proxy_gate/report.md) | fit完美代理未过跨数据门，不训练 |
| [E110](../stages/e110_first_expansion_intervention/report.md) | 同三入口首展开干预有机制信号，未稳定超过单入口，停止候选 |
| [E111](../stages/e111_rank_core_certificate/report.md) | 条件证书覆盖不足；同query重复向量ID边界完整保留，停止监督 |

新增[图依赖合成反例](graph_dependence_v1/report.md)4次原kernel调用通过，不读取真实数据；原E107的2次另保留。核心保留与指定GT1返回所需同分条件已[分层修正](retained_target_reachability.md)，原文和冻结E111原件均保留。

理论入口：[学习目标与搜索合同](learning_objective_and_search_contract.md)、[概率解释](probabilistic_profile_interpretation.md)、[目标几何](target_geometry_derivation.md)、[区域后验](coverage_posterior_derivation.md)、[保分数导航等价性](score_preserving_navigation_equivalence.md)、[文献条件](literature_scope.md)。这些基础推导未声称论文首次性，尚未形成新的可部署方法。

累计2,797,056真实NSG、6合成调用、4普通路由小图；0新GT/底层图/梯度训练/held-out/生产变更，E111有图派生标签。4M/2GiB上限、15:50禁止新搜索、16:00交付保持。不因剩余时间扩m/路径/seed/ef或更换网络继续试。
