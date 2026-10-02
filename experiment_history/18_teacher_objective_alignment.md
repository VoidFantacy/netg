# 18 教师标签与训练目标对齐（E29）

2026-09-11完成，状态`TEACHER_OBJECTIVE_ALIGNMENT_COMPLETE_NO_STABLE_DUAL_GAIN`。本轮未建立优于原GT10的稳定双数据Recall–QPS优势。 当前建议继续保留WebVid已冻结GT10 soft、Yandex GT10 hard；本轮四格均没有足够证据支持替换。

## 问题与实质对照

延续[E28](17_gt10_shared_transform.md)的集合CE下降但教师入口重合下降现象。新版本[20260911_teacher_objective_alignment_v1](../entry_method_exploration/20260911_teacher_objective_alignment_v1/report.md)固定原GT10 hard、H、共享linear/λ100/80epoch，只做教师与损失的2×2。cost教师为原C8 maxhits/minNDC选优；keep在无额外hits空间时保留原GT10实际HNSW三入口。CE与结构化top3 margin各自作用分开，原cost_ce逐位恢复E28linear100。

在线raw query→一次microHNSW top3→三个真实hub→原NSG，不加query塔或重排。margin上界教师漏选成员错误，不上界NSG Recall损失；多个等效好集合仍被压成一个教师，固定λ下两目标的实际漂移并不相同。

## 执行与冻结

两集fit20k复用224万真实三元组标签，全部独立ID→GT评分，新标注0。两教师命中上界相同，但keep放弃一部分成本改道；新教师不能部署。8份模型在新开发query前全部冻结，无超参/epoch选择。完整fit20k、cal1024、audit1024做真实检索，audit另有L128exact诊断；validation2000×11方法×5L=110正式点，各3次完整warm/plain单线程wall。

## 完整结果

以下同批相对GT10 hard，R为百分点，QPS为同L三轮中位数比；不是等Recall加速。

| 数据集 | L | cost_ce ΔRpp / ΔQPS | keep_ce ΔRpp / ΔQPS | cost_margin ΔRpp / ΔQPS | keep_margin ΔRpp / ΔQPS |
|---|---|---|---|---|---|
| WebVid2.5M | 64 | +0.080 / -0.80% | -0.020 / -0.69% | -0.020 / -0.31% | -0.045 / -0.50% |
| WebVid2.5M | 128 | +0.070 / -0.58% | -0.015 / -0.51% | -0.010 / -0.18% | -0.090 / -0.27% |
| WebVid2.5M | 256 | +0.090 / -0.19% | +0.095 / +0.21% | +0.055 / -0.08% | -0.055 / +0.02% |
| WebVid2.5M | 400 | +0.045 / -0.01% | +0.030 / -0.12% | +0.025 / +0.11% | -0.085 / +0.24% |
| WebVid2.5M | 800 | -0.040 / +0.07% | -0.055 / -0.16% | -0.005 / -0.09% | -0.095 / -0.12% |
| Yandex10M IP | 64 | -0.025 / +1.24% | -0.035 / +0.83% | +0.060 / +1.50% | -0.030 / +1.13% |
| Yandex10M IP | 128 | -0.110 / -0.70% | -0.115 / -0.62% | -0.020 / -0.52% | -0.030 / -0.73% |
| Yandex10M IP | 256 | -0.070 / +0.10% | -0.130 / +0.43% | -0.045 / +0.23% | -0.040 / +0.45% |
| Yandex10M IP | 400 | -0.035 / -0.07% | -0.100 / +0.07% | -0.035 / +0.11% | -0.040 / -0.22% |
| Yandex10M IP | 800 | -0.035 / +0.13% | -0.080 / +0.12% | -0.040 / +0.04% | -0.040 / -1.39% |

预设WebVid75/80/85%、Yandex90/95/98%的Recall–logQPS插值描述，不外推、不计为新增实测点：

| 数据集 | 方法 | 预设点覆盖 | 插值QPS几何均变 |
|---|---|---|---|
| WebVid2.5M | cost_ce | 3 | +0.36% |
| Yandex10M IP | cost_ce | 3 | -1.33% |
| WebVid2.5M | keep_ce | 3 | +0.18% |
| Yandex10M IP | keep_ce | 3 | -2.13% |
| WebVid2.5M | cost_margin | 3 | +0.16% |
| Yandex10M IP | cost_margin | 3 | -0.83% |
| WebVid2.5M | keep_margin | 3 | -0.75% |
| Yandex10M IP | keep_margin | 3 | -1.42% |

## 机制与局限

| 数据集 | 模型 | fit L128 ΔRecall pp | fit Δgraph NDC |
|---|---|---|---|
| WebVid2.5M | cost_ce | +0.049 | +0.20% |
| WebVid2.5M | keep_ce | +0.054 | +0.22% |
| WebVid2.5M | cost_margin | +0.135 | -0.06% |
| WebVid2.5M | keep_margin | +0.124 | +0.01% |
| Yandex10M IP | cost_ce | -0.002 | -0.02% |
| Yandex10M IP | keep_ce | -0.002 | -0.01% |
| Yandex10M IP | cost_margin | -0.007 | +0.00% |
| Yandex10M IP | keep_margin | -0.001 | -0.00% |

两因素的实际Recall主效应和交互、正负query、完整训练及有/无候选命中空间组均保留。margin可以改善教师入口拟合，但实际fit、cal、audit、validation并不因此自动一致提高；原T1保留的是实际HNSW集合，与原画像精确top3存在差异。只读梯度/漂移方向诊断不是因果性能控制。

本轮只有共享linear/固定margin与正则/80轮/一个图和H；无收敛证书、无漂移匹配新搜索控制。所有fit/cal/audit/validation均有历史使用，held-out未读取/hash。E24GT10和E28MLP的历史局部信号不因此抹去。

## 成本与核验

实际原NSG调用2,085,120，修复0，合成0，正常预算收口。训练8次共176.44s(CPU8，含对齐诊断)。正式CPU15/实际线程1/OMP-BLAS-MKL1，无训练并发。170点471200输出独立评分，8条原曲线160000输出与E28回归；fit已知三元组199,159输出与原缓存核对。原base/图/kernel/H/旧模型与结果保持身份。旧GT/QGT/主图从零成本未新测。

## 证据与接续

- [协议](../entry_method_exploration/20260911_teacher_objective_alignment_v1/protocol.md)、[完整报告](../entry_method_exploration/20260911_teacher_objective_alignment_v1/report.md)、[方法推导](../entry_method_exploration/20260911_teacher_objective_alignment_v1/research.md)。
- [主曲线](../entry_method_exploration/20260911_teacher_objective_alignment_v1/figures/recall_qps_main.svg)、[全部曲线](../entry_method_exploration/20260911_teacher_objective_alignment_v1/figures/recall_qps_all.svg)、[因素图](../entry_method_exploration/20260911_teacher_objective_alignment_v1/figures/factor_effects.svg)、[工作簿](../entry_method_exploration/20260911_teacher_objective_alignment_v1/chart_data.xlsx)。
- [原始点](../entry_method_exploration/20260911_teacher_objective_alignment_v1/results/all_points.csv)、[调用账](../entry_method_exploration/20260911_teacher_objective_alignment_v1/logs/evaluation_jobs.json)、[最终审计](../entry_method_exploration/20260911_teacher_objective_alignment_v1/reviews/final_audit.json)。

本版本收口，下一方向见当前[s-target](../s-target.md)，不借本轮余量扩网格。
