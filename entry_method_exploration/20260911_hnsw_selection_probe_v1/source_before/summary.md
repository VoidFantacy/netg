# ACSG 当前实验总结

2026-09-11。最近完成E34，状态`COMPLETE_FROZEN_RL_BENCHMARK`。[完整报告](entry_method_exploration/20260911_hnsw_rl_benchmark_v1/report.md)、[历史23](experiment_history/23_hnsw_rl_benchmark.md)、[状态](entry_method_exploration/20260911_hnsw_rl_benchmark_v1/state.json)。

## 本轮完成

用户另行要求比较QPS、Recall及失败率，已对E33冻结RL图和NSG、原Fast30K、FastGT10-hard重新同机测量；WebVid另列RL起点GT10-soft-t1。双集各历史validation2000、五L，共45方法点、225轮独立整批wall，CPU15/实际进程与数值库均1线程。没有新训练或seed/checkpoint选择；E33开发停止及原零QPS记录保留。

失败严格为Recall@10<0.1（零命中），与程序异常分开。QPS取五轮中位数并保留min/max；原始query路由、映射、NSG、输出均计时，GT/count/I/O/load/hash在timer外。

## RL相对其直接起点

WebVid为GT10-soft-t1，Yandex为GT10-hard；不能把RL相对NSG或Fast的全部差异归因强化学习。下表保留全部五L正负点。

| 数据集 | L | ΔRecall pp | ΔQPS % | 原图→RL失败数 |
|---|---:|---:|---:|---:|
| WebVid | 64 | -0.220 | -0.07 | 104→109 |
| WebVid | 128 | +0.035 | -0.22 | 51→49 |
| WebVid | 256 | -0.085 | +0.04 | 21→23 |
| WebVid | 400 | -0.080 | +0.00 | 9→11 |
| WebVid | 800 | -0.040 | -0.01 | 3→4 |
| Yandex-IP | 64 | -0.140 | +0.25 | 44→45 |
| Yandex-IP | 128 | -0.040 | -0.02 | 32→31 |
| Yandex-IP | 256 | -0.025 | -0.02 | 23→22 |
| Yandex-IP | 400 | +0.010 | -0.04 | 18→17 |
| Yandex-IP | 800 | -0.050 | +0.02 | 6→7 |

WebVid相对其直接起点，五L的Recall变化为-0.220～+0.035pp，QPS变化-0.22%～+0.04%；1/5点Recall上升，2/5点QPS上升。同Recall三个描述性插值位置的QPS变化为-0.91%～-0.29%。 Yandex-IP相对其直接起点，五L的Recall变化为-0.140～+0.010pp，QPS变化-0.04%～+0.25%；1/5点Recall上升，2/5点QPS上升。同Recall三个描述性插值位置的QPS变化为-0.63%～-0.38%。

所有基线的原45点、35项配对挽救/新增失败和同Recall描述性插值见报告。历史validation反复使用、每集仅2000、单份预选RL图；小速度差及未校正bootstrap不足以自动建立稳定替换结论。当前默认仍为WebVid原GT10-soft-t1/Yandex原GT10-hard；E33相对随机未建立稳定增量的边界保留。

## 图表与验收

[Recall–QPS](entry_method_exploration/20260911_hnsw_rl_benchmark_v1/figures/recall_qps.svg) · [QPS/Recall/失败率随L](entry_method_exploration/20260911_hnsw_rl_benchmark_v1/figures/metrics_by_search_L.svg) · [RL相对各基线变化](entry_method_exploration/20260911_hnsw_rl_benchmark_v1/figures/rl_changes.svg) · [Excel](entry_method_exploration/20260911_hnsw_rl_benchmark_v1/chart_data.xlsx)。PNG/PDF、原值CSV及aligned结果齐备。

全部90000输出独立GT复算、70000旧基线输出逐位回归E30；五轮/plain/count/原kernel、五L图/入口一致与失败配对恒等式通过。实际NSG630720，修复0；新训练/GT生成0，旧E33完整目录及实际依赖SHA保护。held-out未读/hash。[最终验收](entry_method_exploration/20260911_hnsw_rl_benchmark_v1/reviews/final_audit.json)。

E33已完成真实轨迹REINFORCE边训练（4×600步、307200新反馈）；开发WebVid局部信号/Yandex失败，与本次新增性能数据分别保留。[E33报告](entry_method_exploration/20260911_hnsw_edge_rl_v1/report.md)、[历史22](experiment_history/22_hnsw_edge_rl.md)。预算均已收口，无排队任务，下一阶段见[s-target](s-target.md)。
