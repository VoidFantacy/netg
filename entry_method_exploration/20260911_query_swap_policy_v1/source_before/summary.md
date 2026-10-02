# ACSG 当前实验总结

2026-09-11。最近完成E35，状态`COMPLETE_HNSW_SELECTION_DIAGNOSIS`。[报告](entry_method_exploration/20260911_hnsw_selection_probe_v1/report.md)、[历史24](experiment_history/24_hnsw_selection_diagnosis.md)、[状态](entry_method_exploration/20260911_hnsw_selection_probe_v1/state.json)。用户澄清主要怀疑HNSW未挑中已有好点，本轮完成最小实际验证，没有新训练或QPS。

## 当前结论

两张GT10原HNSW底层有向图均强连通、起点可达全部815/821点。已评分的有用点未入最终三入口，是这批样本上的主要机制线索；静态断图不是本次观测到的原因。覆盖问题仍存在，不能把全部空间都归为末端排序。

| 验证项 | WebVid | Yandex-IP |
|---|---:|---:|
| 单入口效用有差别的query | 92/128 | 65/128 |
| 其中已评分最优点、最终三入口全未选 | 38 | 34 |
| 其中未评分到任何最优点 | 25 | 4 |
| exact画像top3相对原ANN3 ΔRecall | +0.15625pp | +0.078125pp |
| 当前C8真实三入口oracle相对原ANN3 | +3.671875pp | +2.812500pp |

最优点包含全部并列最高单入口命中点；已评分不是已扩展，单入口最优不能代替真实三入口收益。C8 oracle实际跑完56个组合后用GT挑选，不是学习成果或可部署增益。提高ef40只得到与exact相同的小Recall增量，并增加总NDC；没有新wall，不能换算QPS。[图](entry_method_exploration/20260911_hnsw_selection_probe_v1/figures/selection_diagnosis.svg)、[全部质量/失败率](entry_method_exploration/20260911_hnsw_selection_probe_v1/results/quality.csv)、[逐query](entry_method_exploration/20260911_hnsw_selection_probe_v1/results/query_diagnostics.csv)。

## 执行、核验与边界

各128个预定E20训练pilot，与当前20K画像fit不重叠，但以前做过诊断。当前WebVid GT10-soft-t1/Yandex GT10-hard，原H/ID/画像/HNSW/NSG/raw IP固定、L128/K10；CPU15与进程/OMP/BLAS/MKL1。当前C8为单张GT10 top8，与E28/E32的两路union C8不同。

旧全H单入口209408返回独立GT复核、96个预定native单入口回归通过。当前15104联合输出复算，768组原路由plain/count、256现有Policy与top8前缀通过；新NSG总15200/HNSW3072。首次pilot/fit行检查在0查询停止，修正为核验原train源行；原版本保留。距离parity实际为浮点值相等，不夸大成独立堆距离byte比对。[验收](entry_method_exploration/20260911_hnsw_selection_probe_v1/reviews/final_audit.json)。

两集查询进程6.22/13.03s含load/trace/I/O，非QPS。没有新RL、GT生成、validation/held-out访问。旧源/图/标签/模型/历史原件保护，预算收口。

## 与上一轮及下一步的关系

[E34性能补测](entry_method_exploration/20260911_hnsw_rl_benchmark_v1/report.md)仍是当前RL实际性能依据：删边RL相对直接GT10起点没有稳定增量，不能把相对NSG的全部提高归因RL。原GT10与E28局部信号、E32精确收益fit信号、E33单集删边开发信号分别保留，默认未换。

下一步优先一次HNSW现有候选的查询相关保留/组合，在相同候选成本下比较原top3、简单控制和学习；再验证局部图交换能否补充访问空间。不能据强连通/更多epoch直接推导成功，也不能把已有共享画像/精确56动作目标改名RL。[s-target](s-target.md)记录详细未实施设计。
