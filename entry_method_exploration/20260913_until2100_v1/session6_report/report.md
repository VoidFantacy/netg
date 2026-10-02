# 第6串行研究会话报告：E75–E78

本会话完成一组层级、支持、方向与范数控制，未找到稳定整体改善；整日21:00目标未完成。E75/E77/E78主候选各自预锁门均失败，未追加其完整wall；E76只做旧返回诊断。E73/E74的Yandex局部正信号保留。

| 主候选相对compact，aux7952 L128 | Web净命中 / 失败净新增 | Y净命中 / 失败净新增 |
|---|---|---|
| E75保留原层级 | −59 / +2 | −22 / +3 |
| E77半收缩A | +58 / 0 | −80 / +6 |
| E78质量范数 | 0 / 0 | −44 / +3 |

E77的Web修复伴随大量旧收益丢失，Y主要评分方向损伤；E78保留更多旧收益，仍无净改善。低ESS不是共同损伤原因，恢复层级不恢复邻接。完整机制、控制、双半门和代价见各报告，不能把同LRecall或NDC当QPS。

本表失败严格为零GT10命中。以下统计来自五个已测主配置P/compact/E75/E77 A/E78 mass的全部7952源行；不是挑选最终集或新的查询。完整CSV含所有“任一配置失败”的query，包括五个配置都失败的行，并保留GT10、三入口及每个返回ID；图只显示按源行升序前24个失败状态变化query。

| 数据 | 任一配置失败query | 失败状态变化query | 五配置全失败query |
|---|---:|---:|---:|
| WebVid | 251 | 140 | 111 |
| Yandex | 203 | 97 | 106 |

| 数据 / 候选对compact | 救回 / 新增失败 |
|---|---|
| WebVid / E75_preserved | 8 / 10 |
| WebVid / E77_shrink | 38 / 38 |
| WebVid / E78_mass | 2 / 2 |
| Yandex / E75_preserved | 5 / 8 |
| Yandex / E77_shrink | 22 / 28 |
| Yandex / E78_mass | 1 / 4 |

[完整失败query CSV](failure_queries.csv) · [失败图](failure_queries.png) · [统计/派生验收](failure_summary.json)。

本会话实际388608 NSG/387840 HNSW，4真实build/8向量安装；合成另4图/512HNSW。12个native均终止返回0、CPU15及实际线程/数值库均1；native总331.602秒包含load/count/I/O，不是纯在线QPS。E75成功重编译5.527秒，首次失败编译时长未知；E77向量安装独立耗时未知，未将未知记零。没有新GT/梯度/正式QPS，E76另重评分143616旧返回，本报告派生独立重评分79520旧返回不计新ANN。继承E66画像训练30.286秒及历史GT成本不记零。

最新完整QPS图仍来自E74：55点275轮独立完整wall，Yandex保留局部Recall/失败改善，五轮QPS范围跨零，约1.9%～3.0%只是描述性插值；Web损伤保留。它是历史开发批次，不能与新L128诊断拼成曲线或称晚间最终验证。

[E74 QPS–Recall](../stage15_compact_wall_v1/figures/recall_qps.png) · [QPS–失败率](../stage15_compact_wall_v1/figures/failure_qps.png) · [按L三指标](../stage15_compact_wall_v1/figures/three_metrics_by_L.png) · [E74完整报告](../stage15_compact_wall_v1/report.md)。

[E75报告](../stage16_preserved_levels_v1/report.md) · [E76诊断](../stage17_child_support_diagnosis_v1/report.md) · [E77四格](../stage18_child_shrink_factorial_v1/report.md) · [E78质量权重](../stage19_child_mass_norm_v1/report.md)。

P-fit20K包含旧train/monitor，aux7952和两半/旧cal/audit都历史暴露，所有选型反馈计训练。E34历史validation今天最终对照尚未运行，不回流训练/选型；held-out未打开。下一方向及空间预算是未运行设计，见[接续设计](../next_stage_design_session6.md)；[安全交接](../handoff.md)由监督器接续，整日目标未完成。
