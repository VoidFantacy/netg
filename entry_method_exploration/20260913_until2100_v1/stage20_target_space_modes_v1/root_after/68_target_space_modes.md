# E79：以GT10目标方向分组的入口画像

新目标分组及固定置换对照已完成双数据集真实查询。两集均未通过预锁质量门，停止本版本；不改选置换对照或扫分组参数。 这不否认E73/E74 Yandex局部正信号，默认未替换。整日21:00目标未完成。

相对旧query方向分组，唯一新增训练信号是已有GT10目标方向；在线仍为一次小HNSW取7slot、去重三真实入口、原NSG/raw-IP。父P与原H815/821保持，GT只在返回后评分。

| 数据 | 候选 / 对照 | 净GT10命中 | ΔRecall pp | 救回 / 新增零命中 | 两半净命中 |
|---|---|---:|---:|---|---|
| WebVid | target10 / baseline10 | -11 | -0.0138 | 33 / 40 | 23 / -34 |
| WebVid | target10 / compact10 | +48 | +0.0604 | 57 / 53 | 39 / 9 |
| WebVid | target10 / permuted10 | +73 | +0.0918 | 54 / 44 | 63 / 10 |
| WebVid | permuted10 / baseline10 | -84 | -0.1056 | 21 / 38 | -40 / -44 |
| WebVid | permuted10 / compact10 | -25 | -0.0314 | 53 / 59 | -24 / -1 |
| Yandex | target10 / baseline10 | +0 | +0.0000 | 32 / 30 | -45 / 45 |
| Yandex | target10 / compact10 | -120 | -0.1509 | 31 / 42 | -84 / -36 |
| Yandex | target10 / permuted10 | +213 | +0.2679 | 47 / 26 | 73 / 140 |
| Yandex | permuted10 / baseline10 | -213 | -0.2679 | 15 / 34 | -118 / -95 |
| Yandex | permuted10 / compact10 | -333 | -0.4188 | 24 / 56 | -157 / -176 |

每dataset的target须同时胜P与compact全量、两半非负且失败不增；对permuted全量/两半非负且失败不增。所有条件在查询前锁定。只看训练分离度、净同LRecall、NDC或置换差异都不是完整性能改善。

旧收益保留与损伤迁移（按相对P的逐query净命中正负部，不是GT成员实际集合变化）：

- WebVid target10：保留旧compact正命中 340/820；丢失 480、新增收益 351；避免旧损失 539、新增/放大损失 362。
- WebVid permuted10：保留旧compact正命中 234/820；丢失 586、新增收益 268；避免旧损失 668、新增/放大损失 375。
- Yandex target10：保留旧compact正命中 248/545；丢失 297、新增收益 166；避免旧损失 267、新增/放大损失 256。
- Yandex permuted10：保留旧compact正命中 102/545；丢失 443、新增收益 77；避免旧损失 307、新增/放大损失 274。

原A SHA/P bytes、完整旧Q分配/支持/聚合/W已恢复；目标行维度头/ID/范数、固定32行独立标量目标参考/集和固定12个hub独立query聚合/变体通过。分区差异按A加权并消除二元标签交换，完整表保存。

- WebVid target10：571个合格双子hub，1957画像；相对旧Q分区加权无标签差异均值 36.06%。
- WebVid permuted10：529个合格双子hub，1873画像；相对旧Q分区加权无标签差异均值 39.79%。
- Yandex target10：709个合格双子hub，2239画像；相对旧Q分区加权无标签差异均值 29.35%。
- Yandex permuted10：709个合格双子hub，2239画像；相对旧Q分区加权无标签差异均值 41.42%。

置换只打乱目标特征行，A/Q/源行固定；它也改变支持、合格数和物理图，因此不是仅有目标身份改变的严格等容量因果控制。新目标均值是否覆盖同hub真正有用目标仍未定因，不从几何结果补故事。

本阶段 129536 NSG / 129280 HNSW、4离线分组训练/2旧分组复现、4真实小图构建、0梯度更新/0新GT/0编译。离线总 88.252s，四新分组/聚合/导出 55.450s，目标构造 2.313s，原Q复现 25.094s，构图 0.754s，四native 110.052s。此操作wall含加载/计数/I/O，不是QPS。继承GT/P成本未重测为unknown。

完整plain/count、256原kernel、P/compact旧返回31808行全字段恢复、全部7slot/图W/labels/合法邻接和集合/mask通过；原始输出与成本见链接。CPU15/进程及数值库1线程，四工具实际terminal0后评分，无并发被测方法。

失败并集 495 条dataset/source-row，其中 292 条失败状态变化；全方法均失败的行也完整保留GT10/各入口/各返回ID，图仅显示每集前24个变化源行。

P-fit20K含旧train/monitor；aux7952与两半是已观察选择训练反馈，cal/audit历史使用。E34最终与held-out本阶段未打开；不能把本结果当独立盲测。磁盘使用独立前瞻6.9GiB下限、64MiB阶段上限，另32MiB晚间/4MiB交接；此前各版本7GiB与旧封存不改。

[完整配对](../entry_method_exploration/20260913_until2100_v1/stage20_target_space_modes_v1/results/paired.csv) · [质量门](../entry_method_exploration/20260913_until2100_v1/stage20_target_space_modes_v1/results/gate.json) · [画像分区](../entry_method_exploration/20260913_until2100_v1/stage20_target_space_modes_v1/results/partition_comparison.csv) · [完整失败query](../entry_method_exploration/20260913_until2100_v1/stage20_target_space_modes_v1/results/failure_queries.csv) · [失败图](../entry_method_exploration/20260913_until2100_v1/stage20_target_space_modes_v1/figures/failure_queries.png) · [质量与成本图](../entry_method_exploration/20260913_until2100_v1/stage20_target_space_modes_v1/figures/target_modes_v2.png) · [成本](../entry_method_exploration/20260913_until2100_v1/stage20_target_space_modes_v1/results/cost.json) · [验收](../entry_method_exploration/20260913_until2100_v1/stage20_target_space_modes_v1/reviews/verification.json)。

本阶段无新增QPS点。最近完整QPS图仍来自独立E74开发批次：[QPS–Recall](../entry_method_exploration/20260913_until2100_v1/stage15_compact_wall_v1/figures/recall_qps.png)、[QPS–失败率](../entry_method_exploration/20260913_until2100_v1/stage15_compact_wall_v1/figures/failure_qps.png)、[按L三指标](../entry_method_exploration/20260913_until2100_v1/stage15_compact_wall_v1/figures/three_metrics_by_L.png)；不得把本次L128结果拼到旧速度曲线。晚间最终对照仍待执行。

元数据更正：原analyze源码继承的stage state将build误记0；实际4图及cost原件正确。现state修正为4，原state/分析源码和[更正记录](../entry_method_exploration/20260913_until2100_v1/stage20_target_space_modes_v1/reviews/build_counter_correction.json)保留，0新增查询。图v2只增加数值标签边距，原图保留。

[前瞻协议](../entry_method_exploration/20260913_until2100_v1/stage20_target_space_modes_v1/protocol.md)。
