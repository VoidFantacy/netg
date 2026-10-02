# 158 Energy画像分数到实际搜索的连接诊断

2026-09-30，沿157固定四模型／两批／六方法对只读分析，0新搜索、GT、模型或性能。Energy相对Default的query分数平方差比Uniform低13.291%／27.999%；该几何变化已在新query体现，但157没有稳定召回改善。

| Energy相对Uniform，每集8192条 | Web | Yandex |
|---|---:|---:|
| 精确top3改变 | 428 | 619 |
| 实际top3改变 | 648 | 772 |
| 精确同、实际变 | 297 | 203 |
| 精确变、实际同 | 77 | 50 |
| 最终R1返回改变 | 11 | 24 |
| 最终R100有序返回改变 | 57 | 75 |

相同入口者主返回／距离bits／主NDC全部相同；不同入口者也多数保持最终返回。Web R100在“精确同、实际变”组净−63成员，另一实际改变组+52；Y两组+160／−129。它们是固定模型的观察性事件分解，不能解释成小图拓扑干预的因果效应，不据此调图或继续训练。

按实际float32 W转float64评分，只单位化query；二阶矩而非中心化协方差，最大恒等式误差1.53e−16。所有浮点边界与证书、全部三种控制都保存。R100真实成员救回／损伤与每query净变化分开，有序输出与集合变化分开。

分析7.627秒、另一套实现核验4.596秒；1024标量top3、1536证书、576组单元、131072返回和197身份通过。原145计数用语另附后补，120单元复算；旧净Recall与封存不变。157停止本版Energy调参、保留费用候选的边界保持，下一步只做共享精确标注四格检查。

[完整报告](../entry_method_exploration/20260930_theory_until2200_v1/research/energy_routing_bridge_v1/report.md) · [全部结果](../entry_method_exploration/20260930_theory_until2200_v1/research/energy_routing_bridge_v1/results/summary.json) · [独立核验](../entry_method_exploration/20260930_theory_until2200_v1/research/energy_routing_bridge_v1/reviews/independent_audit.json) · [145用语后补](../entry_method_exploration/20260930_theory_until2200_v1/research/routing_member_count_clarification_v1/report.md)。
