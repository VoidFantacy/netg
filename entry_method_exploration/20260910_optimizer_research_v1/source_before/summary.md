# ACSG 当前实验总结

> 更新至2026-09-09。当前结果为用户指定的五点探索；实现见[spec.md](spec.md)，接续边界见[s-target.md](s-target.md)，历史见[s-experiment.md](s-experiment.md)。

## 当前结论

**A+B五点探索已完成，当前冻结候选没有显示出相对Fast的整体改进。** 两个数据集各2000条validation、一个QGT构建、单线程、L64/128/256/400/800，只比较NSG、Fast30K direct3和A+B。每点一次完整预热和一次独立端到端wall，全部30点完成。原过重的大矩阵和后续队列已按用户要求取消，不自动恢复。

同一数据集五点固定同一份入口选择模型，逐query入口完全相同。模型输入只有query；L是后续图搜索的候选池大小。所用模型的训练标签曾在L128下测得，这描述监督来源，不限制模型推理适用的L，也不意味着要为每个L单独训练。

## 相对Fast的三项指标

每点N=2000；失败数为Fast→A+B。失败严格Recall@10<0.1（GT10零命中）。QPS百分比来自单次独立plain wall，较小差异不能解释为稳定收益。

| 数据集 | L | ΔRecall pp | ΔQPS | 失败数 |
|---|---:|---:|---:|---:|
| WebVid | 64 | -0.325 | -14.77% | 114→135 |
| WebVid | 128 | -0.540 | -8.29% | 54→70 |
| WebVid | 256 | +0.180 | -5.33% | 24→22 |
| WebVid | 400 | +0.175 | -5.14% | 10→9 |
| WebVid | 800 | +0.130 | -1.32% | 4→3 |
| Yandex-IP | 64 | -1.450 | -17.94% | 49→80 |
| Yandex-IP | 128 | -0.775 | -11.90% | 37→53 |
| Yandex-IP | 256 | -0.215 | -9.70% | 24→29 |
| Yandex-IP | 400 | +0.105 | -7.71% | 18→19 |
| Yandex-IP | 800 | +0.135 | -4.59% | 6→4 |

相对NSG，WebVid五点Recall增加0.950–2.835pp、少5–60条失败query；Yandex增加0.255–0.570pp、少6–17条失败query。QPS变化分别为−2.74%至+1.37%、−6.36%至−1.00%，因此质量提升不能单独视为整体性能优势。全部原值、失败率及挽救/新增失败数量见[三基线报告](entry_method_exploration/20260909_ab_experiment_v1/exploration_5point_v1/report.md)。

## 实际执行和解释边界

- 此前已经完成169,857,792次正式入口效用标签调用及12个dataset×seed×训练标签L的模型拟合。五点探索复用冻结模型，无新增训练。三seed标签共享真实hub并集计算，但各模型仅使用本构建H。
- 最初16线程计时不符合用户要求，已停止且不进入主表；服务器中断、恢复及后续过重单线程矩阵都保留原输出。旧大矩阵只有12个cal/audit调用和首个WebVid构建的完整validation调用完成，未形成完整held-out结果。
- 本轮两个数据集过程wall约80.07/85.09秒（含加载、构建、校验、预热）；表中QPS单独取计时区间。16query/点原kernel ID/距离bits/NDC一致，2000query/点warm/timed一致，独立GT复核60000个输出，实际线程为1。
- 所选模型fit Recall约增加3pp，而cal分别下降0.332/0.391pp；允许Fast1回退时两个cal都选原初始化。主表报告新候选，没有将回退视为新方法收益。残差权重变化很小，主要变化在入口映射，提示训练增益未泛化；这不是新消融或一般不可学习证明。
- 本轮仅validation2K、单构建、单次wall，不做正式统计显著性、跨构建稳定性或未测L的等Recall插值结论。C维持E21停止状态，未做A+B联动。

## 权威证据

- [E22详细复盘](experiment_history/11_ab_fixed_slot_exploration.md)、[最终探索报告](entry_method_exploration/20260909_ab_experiment_v1/exploration_5point_v1/report.md)、[实际命令](entry_method_exploration/20260909_ab_experiment_v1/exploration_5point_v1/commands.md)。
- [原值CSV](entry_method_exploration/20260909_ab_experiment_v1/exploration_5point_v1/results/metrics.csv)、[相对变化CSV](entry_method_exploration/20260909_ab_experiment_v1/exploration_5point_v1/results/comparisons.csv)、[完整JSON](entry_method_exploration/20260909_ab_experiment_v1/exploration_5point_v1/results/summary.json)。
- [正确性与入口一致性](entry_method_exploration/20260909_ab_experiment_v1/exploration_5point_v1/reviews/final_verification.json)、[输入/模型身份](entry_method_exploration/20260909_ab_experiment_v1/exploration_5point_v1/inputs/manifest.json)、[探索判定](entry_method_exploration/20260909_ab_experiment_v1/exploration_5point_v1/results/decision.json)。
