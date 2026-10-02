# ACSG 当前实验总结

> 更新至2026-09-11。E29教师与目标对齐已完成，状态`TEACHER_OBJECTIVE_ALIGNMENT_COMPLETE_NO_STABLE_DUAL_GAIN`。架构见[spec](spec.md)，下一阶段见[s-target](s-target.md)，完整历史见[s-experiment](s-experiment.md)。

## 当前判断

**本轮未建立优于原GT10的稳定双数据Recall–QPS优势。** 当前建议继续保留WebVid已冻结GT10 soft、Yandex GT10 hard；本轮四格均没有足够证据支持替换。

本轮把教师与损失分开做2×2，固定GT10 hard/sharedlinear/λ100/80epoch。margin不再只依赖集合概率，而直接惩罚漏选教师成员；keep教师在无额外命中空间时保留原实际三入口。完整实际性能必须独立看，不由教师拟合指标升级为方法GO。

## 完整五L结果

下表均相对本批GT10 hard；ΔR是Recall@10百分点，QPS是同L三轮中位数之比。全部正负保留。

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

预设WebVid75/80/85%、Yandex90/95/98%的非支配曲线log-QPS插值，仅概括粗网格相对位置：

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

## 机制上推进了什么

教师T0→T1在WebVid/Yandex分别改10041/10257条query的目标，候选最高Recall保持79.642%/92.929%；keep教师平均图NDC升至1666.10/2890.70，明确放弃了部分成本改道。C8教师逐query用GT选优，不能部署或当作全H/等工作上界。

两集原cost_ce均逐位恢复E28 linear100；8份模型导出/损失独立NumPy核验。margin在WebVid改善了教师入口拟合，但同λ的漂移也明显更小；本轮没有漂移匹配搜索控制，不能把所有差异都解释成对齐机制。Yandex及开发段结果与训练拟合分开保留。

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

原HNSW实际入口与精确画像top3不总一致；T1保留实际路由，精确训练指标不等同于部署决策。两因素和交互、fit完整有/无headroom分组、梯度与负例见[报告](entry_method_exploration/20260911_teacher_objective_alignment_v1/report.md)。

## 执行与证据边界

复用224万逻辑三元组标签，全量重新独立评分，新标签调用0。训练8次176.44s(CPU8)。全部170点471200个输出独立评分；正式110点各3次warm/plain，原八曲线160000输出回归E28。真实NSG调用2,085,120，repair0，synthetic0；预算收口。

正式CPU15/实际线程1/OMP-BLAS-MKL1，各方法顺序执行，GT/count/I/O/建图在timer外。原图、base、kernel、H及旧资产只读。fit/cal/audit/validation均有历史使用，held-out未读取/hash；一个图/H、单优化种子，不构成新盲测或论文级结论。三次wall不是Recall样本，bootstrap未校正多重比较；插值不是额外实测等Recall点。

E24GT10和E28MLP局部信号保留；增强未形成稳定双数据优势不抹去原方法已有证据。E28完整旧summary见本轮修改前快照。

## 交付

- [完整报告](entry_method_exploration/20260911_teacher_objective_alignment_v1/report.md)、[主曲线](entry_method_exploration/20260911_teacher_objective_alignment_v1/figures/recall_qps_main.svg)、[所有方法](entry_method_exploration/20260911_teacher_objective_alignment_v1/figures/recall_qps_all.svg)、[Excel](entry_method_exploration/20260911_teacher_objective_alignment_v1/chart_data.xlsx)。
- [协议](entry_method_exploration/20260911_teacher_objective_alignment_v1/protocol.md)、[最终审计](entry_method_exploration/20260911_teacher_objective_alignment_v1/reviews/final_audit.json)、[历史18](experiment_history/18_teacher_objective_alignment.md)、[E28原summary快照](entry_method_exploration/20260911_teacher_objective_alignment_v1/source_before/summary.md)。
