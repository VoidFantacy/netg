# E174 分析字段与范围

本说明对应冻结 `src/evaluate.py` 输出的 `analysis/final_v1/metrics.json` 及同名三类 CSV；仅记录 schema，不含本轮结果判断。`points`、`comparisons` 和 `mechanisms` 的共同身份为 `role/dataset/K/L/method/n`。正式 `n=4096`，真实搜索 K 为1或100；不从K100返回派生K1。

## points：每个真实方法/预算点

| 字段 | 含义与范围 |
| --- | --- |
| `recall_pct`, `matched_GT_members` | 全4096实际返回相对既有 exact rawIP GT 前K个成员的命中；Recall%=100×命中总数/(nK)，沿用既有GT的tie成员定义。 |
| `qps_rounds`, `qps_median/min/max`, `wall_seconds` | 三轮正常未计数查询的完整 owned wall，包含输出分配/初始化/释放、路由、主搜索和全部附加工作；加载、写盘、GT评分与审计分开。 |
| `graph_ndc_sample_mean`, `route_ndc_sample_mean` | 仅事前固定均匀256 query：前者包含main及R/C/X的真实DC调用，后者为画像路由调用；不是全4096 NDC。 |
| `count_audit_n`, `count_scope`, `stats` | 计数及操作诊断仅覆盖上述256，不得由均值冒充全量实测计数或单项耗时。 |
| `source_complete` | 对应native点收据。全量plain/replay与oracle范围、timed输出不保留等限制以收据及独审为准。 |

`stats.post_dots` 是原R与C的实际fresh scalar调用数；成功阶段保留完整C，非有限早退可能只付前缀。`stats.new_distances` 是新增X调用数。附加scalar费为两者之和。空C/合法域回退可不重评分，padding R不调用DC；不能一概写成每query固定K+24。`graph_ndc` 已包含这两项，不能再次相加。

## comparisons：实际质量和速度差异的权威

| 字段 | 含义与范围 |
| --- | --- |
| `reference`, `reference_L` | 同role/dataset/K下的真实参考点；L相同或跨两个冻结档位。 |
| `recall_delta_pp` | 候选减参考的Recall百分点差。 |
| `rescue_members`, `damage_members` | 全4096实际返回的新增/丢失GT成员数；净命中差=救回−损伤。全部方法的实际救回/损伤以此为权威。 |
| `queries_net_improved/damaged` | 每query净命中差正/负的query数；不同于救回/损伤成员总数。 |
| `paired_qps_ratio_rounds`, `paired_qps_ratio_median`, `paired_qps_change_pct` | 按round index对齐的三轮QPS比、中位数及其百分比变化。same-L为顺序方法匹配；cross-L仅描述性round对齐，不是同时或随机配对。 |
| `all_rounds_faster`, `speed_ranges_separated` | 分别表示三个速度比均>1、候选最慢轮QPS仍大于参考最快轮QPS。后者是报告在协议门上附加的保守条件。 |
| `observed_joint_gain` | 实测Recall净差>0且速度比中位数>1；只是观测标签，不等于确认复现、总体支配或默认替换。 |
| `delta_ci` | 已有2000次paired query bootstrap的描述性区间、固定seed及scope；不建立语义IID或多比较同时保证。 |

## mechanisms：全量区域trace及支持集合诊断

仅区域方法有机制行，共64点。每点源于全4096独立untimed trace；实际C/X到达及评分/合并由native oracle核验，timed packet未保存。候选支持扩展本身不等于最终Recall改善。

| 字段 | 含义与范围 |
| --- | --- |
| `C_total/mean`, `X_total/mean`, `selected_seeds_total/mean` | 全query的实际候选/seed数量总和及均值；每query C≤24、X≤extra_cap、seed≤3。 |
| `queries_with_X`, `extension_aborted` | 有实际X的query数、X非有限中止数；中止保留已付费用及对应表的完整原direct返回，M5分支即原M5。 |
| `X_outside_original_M5_U` | X中位于原冻结M5 posting ID并集U_M5之外的成员出现次数。 |
| `X_outside_original_TRAIN_GT100_U` | X中位于原20K TRAIN GT100 ID并集U_TRAIN之外的成员出现次数。 |
| `new_rescues_vs_M5` | **仅M5REG24/M5REG96/M5FIRST96计算**：相对同L原M5最终新增返回的真实GT成员，且核验来自X。 |
| `new_rescues_outside_original_M5_U`, `new_rescues_outside_original_TRAIN_GT100_U` | **同样仅上述M5区域方法计算**：新增真实救回中位于对应支持集合外的成员出现次数；不是净收益，须同时看comparisons的损伤。 |

**重要：MFREG96/GEOREG96的上述三个`new_rescues...`字段在evaluate中初始化为0而未计算，含义是未计算，不能解释为实际零救回。** `name.startswith('M5')`且非原M5的分支才执行该归因。主报告只使用M5REG96的这些字段，因此范围正确；其他控制的实际Recall、救回/损伤应取`comparisons`，辅助独审`independent_mechanisms.csv`可额外提供控制实际数及U外损伤。

全部U外计数均为**每query incidence之和**，同一个ID跨query可重复计数，不是全局distinct ID数，也不代表本query的新目标或最终救回。U外实际损伤未在evaluate机制字段中单列时，不得补成0。

## 使用边界

112点全量返回、64点全量trace、固定256计数是不同范围。完整wall判定费用，trace解释候选来源，comparisons判定实际质量差异；不能互相替代。图和报告只复用已完成metrics及小收据，不重新生成GT、距离或拟合。现有schema中的观测标签与更严格报告门均不改变GT10默认，也不意味着丢弃原M5。
