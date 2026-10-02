# E33 HNSW edge reinforcement learning

状态：`HNSW_EDGE_RL_COMPLETE_WEBVID_SIGNAL_NO_DUAL_GAIN`，已完成并停止在双集开发门。训练直接改变小HNSW底层有向边，导出静态图；没有重排C8或修改原NSG。WebVid局部信号保留，Yandex失败，无新validation/QPS。

- [完整报告](report.md)、[协议](protocol.md)、[结构预检修正](structural_preflight_repair.md)、[方法依据](literature/method_basis.md)。
- [训练图](figures/training_and_static_graphs.svg)、[开发与成本图](figures/development_and_cost.svg)、[图结构](figures/graph_structure.svg)、[Excel](chart_data.xlsx)。
- [开发门](results/development_gate.json)、[cal选择](results/cal_selection.json)、[完整成本](results/costs.json)、[状态](state.json)、[最终验收](reviews/final_audit.json)。
- 有效训练入口：[train_v2.py](src/train_v2.py)、[native_v2.py](src/native_v2.py)、[environment_v2.cpp](src/environment_v2.cpp)；原版本与首个结构预检停止原件保留。
- 实际模型：`models/<dataset>/<seed>/selected/graph.hnsw`；训练图已冻结，`random_graph.hnsw`逐节点出度匹配。线上[评测器](src/evaluate.cpp)编译原hnswlib，没有训练hook。

原模型、原源码/大图、旧标签和结果没有覆盖。本轮预算已收口；重跑或新方向使用独立版本。旧validation只stat保护，未hash/解码；held-out未读/hash。
