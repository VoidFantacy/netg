# 第6独立串行会话安全交接

2026-09-13 15:04:57 +0800，E75–E78已完成并封存，**整日21:00用户目标未完成**。本会话在15:21:01安全边界前返回，由监督器接续下一唯一写入/实验会话；不启动并行CLI或子代理。全部12个真实native及构图/合成/分析工具已终止，返回0；当前无遗留实验、训练或分析进程。

## 结果与失败查询

[E75–E78综合报告](session6_report/report.md) · [完整失败query CSV](session6_report/failure_queries.csv) · [失败图](session6_report/failure_queries.png)。五主配置任一零GT10命中的独立(dataset,source row)共454条：Web251/Y203；其中失败状态变化140/97、五配置全失败111/106。全表保留GT10、三入口和返回ID，图每集按源行选前24个变化行；0新ANN的缓存派生，不能当新样本或性能点。

| aux7952 L128主候选相对compact | Web净GT10命中 / 失败净新增 | Y净命中 / 失败净新增 |
|---|---|---|
| E75原slot随机层级恢复 | −59 / +2 | −22 / +3 |
| E77子方向半收缩A | +58 / 0 | −80 / +6 |
| E78固定图质量范数 | 0 / 0 | −44 / +3 |

三者各自预锁门双集未通过，停止对应版本，**无E75/E77/E78新wall**；不扫层级/alpha/指数，不自动选择S/T/uniform。E75恢复层级不恢复邻接；E76低ESS并非共同损伤原因。E77全干预修复部分旧损失，也抹去Web39.63%/Y43.67%的旧正命中，评分/拓扑/交互分列；E78大多保留旧收益仍不能改进。失败不等于没有局部空间，下一机制须实质区别。

[E75报告](stage16_preserved_levels_v1/report.md) · [E76诊断](stage17_child_support_diagnosis_v1/report.md) · [E77四格](stage18_child_shrink_factorial_v1/report.md) · [E78质量权重](stage19_child_mass_norm_v1/report.md)。四份原协议/source/input/result/seal及历史[64](../../experiment_history/64_preserved_compact_levels.md)、[65](../../experiment_history/65_child_profile_support.md)、[66](../../experiment_history/66_child_shrink_factorial.md)、[67](../../experiment_history/67_child_mass_norm.md)保持，原图/GT/脏源/日志不清理。

E73/E74 compact的Y局部信号仍保留：E74五L对P命中+99/+59/+38/+1/+15、失败−10/−7/−4/−1/0，五轮QPS范围均跨零，约1.9%～3.0%只是描述性共同Recall插值；Web L128−23/失败+6。默认未替换，尚无稳定整体改善。最新完整性能图来自同一E74开发批次，不能把本轮L128结果拼接进去。

[E74 QPS–Recall](stage15_compact_wall_v1/figures/recall_qps.png) · [QPS–失败率](stage15_compact_wall_v1/figures/failure_qps.png) · [按L三指标](stage15_compact_wall_v1/figures/three_metrics_by_L.png) · [E74完整报告](stage15_compact_wall_v1/report.md)。晚间最终对照尚未运行。

## 成本、资源与核验

本会话388608 NSG/387840 HNSW、4真实小图build/8坐标安装；合成另4图/512HNSW/0NSG。12native总331.602060556秒含load/count/I/O，不能作QPS；新增正式QPS点0。E75成功重编译5.526952531秒，首次失败编译时长未知，因此总编译为null；[独立更正](reviews/e75_compile_cost_scope_session6.json)保留原E75seal。E77独立安装时长未知，E78四安装0.124121362秒；画像构造与图build各成本原件保存。0新GT/梯度，但所有辅助选择反馈计训练；继承E66画像训练30.286秒和历史GT/标签成本未重测，不记零。

今天累计4705364 NSG/5116896 HNSW/352真实build，开发220点/1100wall分属E65/E67/E71/E74独立批次，最终validation点仍0。E75/E77/E78共193920集合/mask、95424旧P/C全字段回归、768原kernel验收；E76重评分143616旧返回，本综合报告另79520旧集合行，全部都是缓存统计而非追加ANN。

CPU15/实际进程和OMP/OpenBLAS/MKL/NUMEXPR/BLIS1线程、方法/数据集全串行。plain/count与原kernel/图W/slots/labels/映射/独立集合验收全部通过。E78阶段19790相同三入口行只计mass对P/C，监督54717另含uniform配对；E77阶段14448只计A对P/C，监督46978另含S/T，口径均正确，不需重跑。

预交接检查6894项身份通过，当前free 7.0553 GiB。四新阶段逻辑105,189,985 bytes（含引用symlink目标），去重inode分配103,616,512 bytes；不能把逻辑字节直接作额外磁盘消耗。7GiB下限之外至少32MiB专留晚间，当前研究余量在交接开销前约24.66 MiB。下一阶段必须现场累计预算，不沿用旧64/128MiB限额、不清理旧文件。

监督截至14:59已完成E75–E78所有source/raw/seal/图和inventory_v6、下一设计源码/最终输出预算核验；本会话综合报告和session seal刚生成，可后续只读复核，不等待批准、不重跑已通过项。

## 角色和接续

P-fit20K包含旧4096train/1024monitor；aux7952是router_train[2048:10000]，固定两半与旧cal/audit均历史暴露，任何选型/动作反馈算训练。E34历史validation2000今天尚未打开，只作晚间冻结后最终对照，不回流训练/选型；held-out不自动打开，元数据余行不能证明全项目未观察。

[inventory_v6](candidate_inventory_v6.json)保留旧32配置，新增6主候选配置和6机制控制，共44。S/T/uniform仍不选入best_new；其他失败新方法只能按独立冻结的最终协议展示，不能绕过原增强wall门。E74展示best_new=compact不是全局最终选择。原NSG/base/rawIP/GT和815/821真实H固定，Micro-HNSW只索引这些入口的画像，不是10M底图。

在项目根目录执行：

```bash
env PYTHONDONTWRITEBYTECODE=1 .venv_cpu/bin/python entry_method_exploration/20260913_until2100_v1/src/resume_inspect_v6.py
```

再读[下一阶段设计](next_stage_design_session6.md)及[监督备注](/data/acsg_sessions/20260913_until2100_v1/supervisor_notes.md)。stage1–19全部完成，不重跑旧runner。下一方向是按已有GT10目标向量拆同hub训练组，再聚合原query画像；**尚未实现/训练/构图/查询**。先独立0ANN可行性协议、A/P及旧query分组复现、RAM流式目标与完整磁盘预算，不能把目标分离度当NSG效用。监督只读确认历史E10/E66组内实际仍按query方向拆，这条源代码上的变化成立，但不称文献创新。

若空间不足容纳一组完整新实验，则先准备最终协议/配置/图表，不开半组实验。最终基础Web5方法/Y4方法、五L五轮共45点/225wall/630720NSG；两集各加独立配置是55点/275wall/770880NSG（N=2000），32MiB预留仍需包含输入引用、raw、图、派生和封存的完整manifest预算。选择best_all/best_new先冻结后读E34；规定NSG/Fast/GT10匹配起点/实际新方法同批完整在线wall，GT/count/hash/JSON/build/load在外。

20:00停止新训练，20:40停止新增query，21:00交付完整QPS–Recall/失败率/按L三指标和失败查询报告。新阶段source_before和独立版本/前瞻门，完成后历史→索引→summary、next同步s-target、接口/计量同步spec。现授权足够串行实施，不重复问批准；禁止删除、外发、发布、推送或改Codex配置。本次完成仅是会话安全交接。
