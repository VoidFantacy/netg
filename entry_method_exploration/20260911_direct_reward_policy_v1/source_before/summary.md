# ACSG 当前实验总结

> 更新至2026-09-11。E31有界训练有效性检查完成，状态`TRAINING_EFFECTIVENESS_COMPLETE_OPTIMIZATION_IMPROVED_CACHE_GATE_FAILED`。架构见[spec](spec.md)，下一步见[s-target](s-target.md)，历史见[s-experiment](s-experiment.md)。

## 当前判断

原E30的80步配置还有优化余地；保持同一模型、教师和λ100，使用固定小步长/衰减训练1200步后，两集目标继续下降。WebVid缓存实际命中有所提高，Yandex仍无有效收益，未达到预设双集缓存门。本次收口这一固定监督/共享画像优化支线，保留WebVid局部信号和原GT10成果。

当前默认仍为WebVid2.5M **GT10 soft**、Yandex10M IP **GT10 hard**，依据[E30完整Recall–QPS与择优](entry_method_exploration/20260911_training_effectiveness_v1/../20260911_equivalent_teacher_sets_v1/report.md)。E31没有新HNSW/NSG查询或QPS，训练耗时不用于性能排名。

## 实际优化与缓存结果

| 数据集 | 教师 | 原80步总目标 | 新选中总目标 | 变化 | 选中步 | 末100步最佳目标再降 |
|---|---|---|---|---|---|---|
| WebVid2.5M | single | 0.533651 | 0.516364 | -3.239% | 1200 | 0.001263% |
| WebVid2.5M | multi | 0.526664 | 0.508577 | -3.434% | 1200 | 0.001306% |
| Yandex10M IP | single | 0.930740 | 0.928057 | -0.288% | 1199 | 0.000043% |
| Yandex10M IP | multi | 0.925134 | 0.922398 | -0.296% | 1197 | 0.000026% |

| 数据集 | 画像 | 缓存Recall@10 | 相对锚点pp | 相对原同教师pp | 图NDC变化 |
|---|---|---|---|---|---|
| WebVid2.5M | single | 75.3820% | +0.1945 | +0.0940 | -0.1426% |
| WebVid2.5M | multi | 75.3990% | +0.2115 | +0.0910 | -0.1407% |
| Yandex10M IP | single | 90.1775% | -0.0040 | -0.0055 | -0.0241% |
| Yandex10M IP | multi | 90.1775% | -0.0040 | -0.0025 | -0.0288% |

缓存指标是float32画像从每query已测的56组三入口中选最大分数，再查原真实L128/K10标签。参考anchor也在相同C8域选择，不是原实际HNSW入口；图NDC不是端到端wall。

WebVid multi相对原80步再增0.0910pp，训练query配对bootstrap95%区间[+0.0455,+0.1340]；相对anchor增0.2115pp。Yandex multi相对原80步−0.0025pp，区间[−0.0185,+0.0110]；相对anchor−0.0040pp，应解读为未观察到提升而非稳定退化。

## 停止位置与结论限制

[缓存门](entry_method_exploration/20260911_training_effectiveness_v1/results/cache_gate.json)为`STOP_CACHE_UTILITY_GATE`。两种教师均未满足同一种cell在两集各≥+0.20pp且成本≤+1%的条件；WebVid multi的全H未知14个query另使最坏净界仅+0.1610pp，Yandex全H已知覆盖100%仍无收益。即使放宽WebVid保守界，Yandex也会使双集门失败，因此按预定条件没有进入真实开发/validation补测。

不能把当前缺少双集收益全归因于原80步优化不足；也不能从这一固定教师/共享linear/λ100/seed推断所有学习画像无效。末100步目标变化小没有提供全局收敛证书，离散选择仍可能波动；所选checkpoint仅按fit目标决定，未按效用改选。fit有历史使用，缓存区间不是泛化或新盲测；held-out未读取/hash。E24 GT10和E28 MLP的历史局部信号保留。

## 计量与交付

两集single/multi共4次训练、4800更新，训练阶段302.73s(CPU8)，低于600s合计上限。复用224万逻辑真实标签，新标签0；新NSG调用/HNSW查询/QPS点均0。枚举/有限差分、旧4个模型恢复、新4个选中与最后点共8份数值核验通过。原资产保护与表格/文档验收见[最终审计](entry_method_exploration/20260911_training_effectiveness_v1/reviews/final_audit.json)。

- [完整报告](entry_method_exploration/20260911_training_effectiveness_v1/report.md)、[优化与效用图](entry_method_exploration/20260911_training_effectiveness_v1/figures/optimization_and_utility.svg)、[缓存实际收益图](entry_method_exploration/20260911_training_effectiveness_v1/figures/cache_utility.svg)、[Excel](entry_method_exploration/20260911_training_effectiveness_v1/chart_data.xlsx)。
- [协议](entry_method_exploration/20260911_training_effectiveness_v1/protocol.md)、[checkpoint诊断](entry_method_exploration/20260911_training_effectiveness_v1/reviews/checkpoint_diagnostics.json)、[历史20](experiment_history/20_training_effectiveness.md)。
- E30完整旧summary保存在[修改前快照](entry_method_exploration/20260911_training_effectiveness_v1/source_before/summary.md)，原全部12方法五L五轮曲线和结果保持原位。
