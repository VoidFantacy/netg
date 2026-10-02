# 23 冻结HNSW-RL图的性能补测（E34）

2026-09-11完成，状态`COMPLETE_FROZEN_RL_BENCHMARK`。用户在E33开发门停止后明确要求比较QPS、Recall、查询失败率并画图，因此独立授权本次性能补测。E33原协议、训练、开发门和零QPS记录保留，没有重新选择模型或重启训练。

## 方法、输入与计量

冻结E33 cal选定物理图：WebVid seed20260912/step400，Yandex seed20260911/step300；只改Micro-HNSW底层已有边，原画像/ID/上层及NSG不变。对照NSG原固定入口、原Fast30K、GT10-hard；WebVid额外GT10-soft-t1，它才是该RL图的直接起点。Fast30K的训练量与构图seed不同于20K GT10，不能把两者差异全部解释为GT1→GT10。

原历史validation2000/集、L64/128/256/400/800、K10/raw-IP；WebVid25点、Yandex20点。CPU15及进程/OMP/BLAS/MKL均1线程，两集串行；每点一次完整warmup、五轮轮换独立plain整批wall，QPS取中位数并显示min/max。GT、计数、hash、I/O和加载在timer外。复用E33无训练hook的binary，加载冻结图，没有新构建/优化或held-out访问。

失败严格为Recall@10<0.1即零GT10命中，不是运行异常。保存query-ID对齐的结果，统计相对每个基线的挽救、新增失败、仍失败以及Recall/QPS/失败率变化。

## 相对直接起点的完整结果

WebVid起点GT10-soft-t1，Yandex起点GT10-hard；ΔRecall为绝对百分点，ΔQPS为五轮中位数相对变化。

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

相对NSG/Fast/FastGT10-hard的全部35项配对比较，以及原45点、225轮wall，均见报告/CSV。Recall–QPS图保留全部实测点；同Recall分析只在各自非支配曲线共同区间作明确标记的log-QPS插值，无外推/新选点。不能用某个更快点或路由NDC直接推导整条曲线改进。

## 验收、成本和解释边界

90000保存输出独立GT复算，70000旧基线输出的ID/距离bits/入口/hits/mask/路由和NSG NDC回归E30通过。五轮/plain/count/每点16条原kernel结果一致，同方法跨五L图与入口一致，失败挽救−新增=基线失败−RL失败。实际NSG630720，修复0；新增训练/标签/GT生成0。查询进程耗时含加载和验收，不当作QPS；完整既有训练成本见[历史22](22_hnsw_edge_rl.md)。

两组validation有反复历史使用，2000条中一条失败对应0.05pp；bootstrap区间未校正多重比较，五轮计时不是新Recall样本。只测一份预选RL图，没有跨seed性能复现，学习相对随机的归因仍保留E33控制证据。本轮不自动替换默认，也不否定尚未测试的坐标训练/加边/重连。

独立版本前后SHA保护E33完整目录及实际依赖，原大图/向量/模型/标签/结果不改。历史validation本轮已明确授权读取及计时；held-out未读/hash。新增图PNG/SVG/PDF及Excel，最终验收和冻结身份保存。

- [完整报告](../entry_method_exploration/20260911_hnsw_rl_benchmark_v1/report.md)、[协议](../entry_method_exploration/20260911_hnsw_rl_benchmark_v1/protocol.md)、[状态](../entry_method_exploration/20260911_hnsw_rl_benchmark_v1/state.json)、[调用账](../entry_method_exploration/20260911_hnsw_rl_benchmark_v1/logs/jobs.json)。
- [Recall–QPS](../entry_method_exploration/20260911_hnsw_rl_benchmark_v1/figures/recall_qps.svg)、[三指标曲线](../entry_method_exploration/20260911_hnsw_rl_benchmark_v1/figures/metrics_by_search_L.svg)、[相对变化](../entry_method_exploration/20260911_hnsw_rl_benchmark_v1/figures/rl_changes.svg)、[Excel](../entry_method_exploration/20260911_hnsw_rl_benchmark_v1/chart_data.xlsx)。
- [输出验收](../entry_method_exploration/20260911_hnsw_rl_benchmark_v1/reviews/output_verification.json)、[最终验收](../entry_method_exploration/20260911_hnsw_rl_benchmark_v1/reviews/final_audit.json)、[评测控制器](../entry_method_exploration/20260911_hnsw_rl_benchmark_v1/src/run.py)、[独立分析](../entry_method_exploration/20260911_hnsw_rl_benchmark_v1/src/analyze.py)。

本轮预算收口，无排队训练/ANN任务；研究接续见根[s-target](../s-target.md)。
