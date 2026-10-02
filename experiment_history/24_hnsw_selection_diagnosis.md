# 24 当前GT10的HNSW选点最小验证（E35）

2026-09-11，状态`COMPLETE_HNSW_SELECTION_DIAGNOSIS`。用户进一步澄清主要怀疑“HNSW没挑中已有候选里的好点”，因此将验证限定为当前H内的访问、画像排序、实际单入口与联合三入口效用。此前E34删边RL相对GT10起点没有稳定性能增量；本轮没有追加RL训练。

## 数据与实现

双集各128个E20预定pilot，来自train前10K、与当前20K画像拟合行不重叠，但已有历史诊断使用。WebVid原GT10-soft-t1、Yandex原GT10-hard，H815/821、原HNSW/NSG/raw IP固定，L128/K10、三入口真实ID升序。E20全H单入口缓存核对原query/GT/H/NSG后复用，96次预定native回归通过；旧16线程标签仅用于质量，当前CPU15、进程/OMP/BLAS/MKL均单线程。

原HNSW距离函数旁记录内部被评分点，上/底层合并，768组k1/k3/k8对照plain/count、256现有Policy以及top8前三项一致。原C++不读GT；每query实际执行原ANN3、exact3、ef40_3及当前单张GT10的ANN8内全部56组三入口，输出后独立评分。C8与E28/E32的两路并集C8不同，未套用其联合标签。

## 结果与解释

两图均只有1个有向强连通分量，起点可达全部815/821点，最大最短有向跳数7/5。只看单入口效用有差别的92/65个query，最终三入口含任一最优点29/27个、已评分最优点但最终全未选38/34个、完全没评分到最优点25/4个。最优集合包含全部并列最高命中点；“已评分”不等于“扩展”，单入口最优不保证联合有益。

| 真正三入口搜索 | WebVid R@10 | Yandex-IP R@10 |
|---|---:|---:|
| 原ANN ef10 | 75.546875% | 90.234375% |
| exact全画像top3 | 75.703125% | 90.312500% |
| ANN ef40 | 75.703125% | 90.312500% |
| C8全部真实三元组事后oracle | 79.218750% | 93.046875% |

exact相对ANN只有+.15625/+.078125pp，C8 oracle有+3.671875/+2.812500pp。提高ef40使总NDC1774.53/2984.70升至1913.44/3094.16，无wall，不能推QPS。ANN1到全H单入口oracle差的78.36%/94.81%在已评分集合内即可见，这是免费oracle算术分解，不是学习收益。C8三入口oracle仍在59/34个query低于全H单入口，覆盖问题不能全部排除；三入口也不保证支配单入口。

当前证据优先指向收益相关的选择/组合目标，未支持简单归因断图或只缺更多删边训练轮数。用户的“哪些点适合选入”更直接对应每query保留集合，全局hub更换没有验证。下一步应先以一次HNSW的廉价候选做相同成本控制，再决定是否结合实际图交换/导航画像移动。E28共享画像、E32完整56动作精确收益的已做边界保留，不能改名当新方法。

## 成本、修正与验收

实际新NSG15200（15104联合+96回归），HNSW3072，旧209408单入口返回全部重新GT评分。两集查询进程6.22/13.03s、峰值约5.42/9.93GiB，包含load/trace/I/O，非QPS。没有新训练、GT、validation/held-out访问或QPS；诊断预算收口。

首版prepare误用当前20K fit索引旧pilot行，KeyError后在0查询停止；有效prepare_v2改为核验原train源行、SHA及fit不重叠，旧源码/部分输入保留。协议所称距离bits校验实际为C++堆元素浮点值相等，未独立导出两份堆距离bytes作memcmp；报告明确此精度边界。

- [完整报告](../entry_method_exploration/20260911_hnsw_selection_probe_v1/report.md)、[协议](../entry_method_exploration/20260911_hnsw_selection_probe_v1/protocol.md)、[状态](../entry_method_exploration/20260911_hnsw_selection_probe_v1/state.json)、[准备修正](../entry_method_exploration/20260911_hnsw_selection_probe_v1/reviews/initial_preflight_correction.json)。
- [诊断图](../entry_method_exploration/20260911_hnsw_selection_probe_v1/figures/selection_diagnosis.svg)、[逐query CSV](../entry_method_exploration/20260911_hnsw_selection_probe_v1/results/query_diagnostics.csv)、[全部质量](../entry_method_exploration/20260911_hnsw_selection_probe_v1/results/quality.csv)、[详细分解](../entry_method_exploration/20260911_hnsw_selection_probe_v1/results/diagnosis.json)。
- [结果核验](../entry_method_exploration/20260911_hnsw_selection_probe_v1/reviews/result_verification.json)、[调用](../entry_method_exploration/20260911_hnsw_selection_probe_v1/reviews/jobs.json)、[最终验收](../entry_method_exploration/20260911_hnsw_selection_probe_v1/reviews/final_audit.json)。

旧E20/E33/E34及实际源/图/模型/GT/标签不改；根文档修改前快照在source_before。后续未实施方案与停止规则见[s-target](../s-target.md)。
