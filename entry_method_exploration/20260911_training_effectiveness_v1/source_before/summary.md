# ACSG 当前实验总结

> 更新至2026-09-11。E30等效集合教师已完成真实评测与分析，状态`EQUIVALENT_TEACHER_SETS_COMPLETE_NO_RELIABLE_REPLACEMENT`。架构见[spec](spec.md)，接续见[s-target](s-target.md)，历史见[s-experiment](s-experiment.md)。

## 当前选择

WebVid2.5M推荐GT10 soft；Yandex10M IP推荐GT10 hard。

| 数据集 | 本批插值速度几何均值最高 | 相对原默认 | 推荐 |
|---|---|---|---|
| WebVid2.5M | GT10 soft | +0.00% | GT10 soft |
| Yandex10M IP | GT10 hard | +0.00% | GT10 hard |

描述性最快按三共同Recall参照的插值速度几何均值排序；推荐另要求至少两个目标中位≥+3%、五轮比值均>1、无约定退化且覆盖三个参照。插值不是新增实测等Recall点；未满足替换门就保留默认，不将细小数值排序写成稳定胜出。

## 实际方法与完整五L

固定GT10 hard锚点、共享linear/λ100/80epoch。G保留C8最高hits且最低graph NDC的全部严格并列三元组；single接受原T0，multi接受G，两者同已知竞争域/损失/预算。multi_matched只由fit模型缩到single均方位移，single_matched同字节alias。在线一份HNSW3/原NSG不变。

| 数据集 | L | E29 margin ΔRpp / ΔQPS | single ΔRpp / ΔQPS | multi ΔRpp / ΔQPS | multi matched ΔRpp / ΔQPS |
|---|---|---|---|---|---|
| WebVid2.5M | 64 | -0.020 / -0.05% | -0.025 / -0.02% | -0.035 / +0.04% | -0.030 / -0.02% |
| WebVid2.5M | 128 | -0.010 / +0.08% | -0.080 / +0.03% | -0.080 / +0.16% | -0.070 / +0.11% |
| WebVid2.5M | 256 | +0.055 / -0.08% | -0.040 / -0.07% | -0.045 / +0.02% | -0.045 / -0.09% |
| WebVid2.5M | 400 | +0.025 / -0.02% | +0.010 / -0.09% | +0.005 / -0.07% | +0.005 / -0.05% |
| WebVid2.5M | 800 | -0.005 / -0.02% | -0.040 / -0.01% | -0.045 / -0.02% | -0.045 / +0.04% |
| Yandex10M IP | 64 | +0.060 / -0.05% | +0.060 / -0.09% | +0.040 / +0.02% | +0.040 / -0.00% |
| Yandex10M IP | 128 | -0.020 / +0.09% | -0.020 / +0.04% | -0.025 / +0.13% | -0.025 / +0.05% |
| Yandex10M IP | 256 | -0.045 / +0.04% | -0.045 / -0.03% | -0.055 / +0.05% | -0.055 / -0.21% |
| Yandex10M IP | 400 | -0.035 / -0.07% | -0.035 / -0.05% | -0.045 / +0.00% | -0.045 / +0.03% |
| Yandex10M IP | 800 | -0.040 / -0.01% | -0.040 / -0.01% | -0.040 / -0.06% | -0.040 / -0.00% |

以上相对同批GT10 hard，ΔR为百分点、ΔQPS为同L比值，不等于等Recall加速。完整12方法、五轮raw wall及区间见[报告](entry_method_exploration/20260911_equivalent_teacher_sets_v1/report.md)。

## 推进边界与机制

| 数据集 | multi fit ΔRpp | 同漂移multi−single pp | cal平均ΔRpp | audit平均ΔRpp | 推进条件 |
|---|---|---|---|---|---|
| webvid2_5m_light_v1 | +0.123 | +0.010 | +0.063 | -0.186 | 未通过 |
| yandex_t2i_official10M_ip_v1 | -0.009 | +0.004 | -0.078 | +0.034 | 未通过 |

开发门状态`STOP_FURTHER_MODEL_EXPANSION`。G常常不唯一，但不代表其身份约束是主要训练瓶颈；候选内接受率、全H精确top3、实际HNSW入口和NSG收益分别保存。只读分数梯度差异用于解释约束范围，不替代性能归因。漂移只匹配全H均方位移，不匹配方向、逐hub幅度或入口变化。

T0已在G内按锚点分数择优，初始化时两目标选中的最高分好组合完全相同。有真实命中空间组仅1.04%/0.65%的query改变分数梯度；最终multi分数下为6.40%/3.42%。等效答案很多与实际关键约束改变很多并不等价。多教师/漂移匹配相对推荐方法的三目标插值QPS几何均变为WebVid−1.38%/−1.40%、Yandex−0.79%/−0.83%；均未达到预设替换条件。

## 计量与证据

两集4次训练，2个漂移控制画像，新训练标签0；224万逻辑标签全量复核。原NSG实际3,177,280次，repair/synthetic均0。全部180点491200个输出独立评分，正式120点各五轮单线程wall，9条旧曲线180000输出逐位回归E29。

CPU15/实际线程1/OMP-BLAS-MKL1，计数/GT/I/O/建图在timer外，不与训练或重分析并发。历史fit/cal/audit/validation重复使用；一个H/图/训练seed，无优化收敛证书，held-out不读取/hash。原GT10和E28 MLP的历史局部信号保留。

## 交付

- [完整报告](entry_method_exploration/20260911_equivalent_teacher_sets_v1/report.md)、[主图](entry_method_exploration/20260911_equivalent_teacher_sets_v1/figures/recall_qps_main.svg)、[全部曲线](entry_method_exploration/20260911_equivalent_teacher_sets_v1/figures/recall_qps_all.svg)、[Excel](entry_method_exploration/20260911_equivalent_teacher_sets_v1/chart_data.xlsx)。
- [协议](entry_method_exploration/20260911_equivalent_teacher_sets_v1/protocol.md)、[择优](entry_method_exploration/20260911_equivalent_teacher_sets_v1/results/method_selection.json)、[开发门](entry_method_exploration/20260911_equivalent_teacher_sets_v1/results/development_gate.json)、[最终验收](entry_method_exploration/20260911_equivalent_teacher_sets_v1/reviews/final_audit.json)、[历史19](experiment_history/19_equivalent_teacher_sets.md)。
- E29完整旧summary保存在[修改前快照](entry_method_exploration/20260911_equivalent_teacher_sets_v1/source_before/summary.md)。
