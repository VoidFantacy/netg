# ACSG 当前实验总结

> 更新至2026-09-10。最近完成E24固定H的GT1/GT10×硬/软画像。实现见[spec.md](spec.md)，下一方向见[s-target.md](s-target.md)，历史见[s-experiment.md](s-experiment.md)。

## 当前总体结论

**E24已完成并收口：有低成本的局部Recall–QPS正信号，尚未得到跨数据集、全部预算都稳定更优的统一画像。GT10值得保留，软归属并非普遍更好。** 状态`EXPLORATORY_LOCAL_FRONTIER_SIGNAL_NO_FORMAL_GO`。

cal冻结主候选为WebVid GT10软T=0.0162011385、Yandex GT10硬。两数据集各validation2000、一个QGT构建、L64/128/256/400/800，NSG/原Fast30K-3/matched Fast20K-3/GT10硬/GT1软/GT10软共60点全部完成；每点单线程独立plain wall一次。两主候选各3/5点同时提高Recall和实测QPS，另外点有交换；不存在整条新曲线稳定支配旧Fast的证据。

## 相对matched Fast20K-3的全部主候选点

| 数据集 / cal冻结主候选 | L | ΔRecall pp | ΔQPS % |
|---|---:|---:|---:|
| WebVid / GT10软 | 64 | +0.525 | +3.51 |
| WebVid / GT10软 | 128 | -0.070 | +1.55 |
| WebVid / GT10软 | 256 | +0.115 | +3.58 |
| WebVid / GT10软 | 400 | +0.005 | -0.75 |
| WebVid / GT10软 | 800 | +0.040 | +2.18 |
| Yandex-IP / GT10硬 | 64 | +0.120 | -0.07 |
| Yandex-IP / GT10硬 | 128 | +0.335 | +2.56 |
| Yandex-IP / GT10硬 | 256 | +0.035 | +0.56 |
| Yandex-IP / GT10硬 | 400 | +0.080 | -0.01 |
| Yandex-IP / GT10硬 | 800 | +0.060 | +0.80 |

WebVid L128的cal/audit原先+0.820/+0.586pp，validation却−0.070pp；Yandex cal+0.049pp、audit−0.078pp，validation五点小正值。主候选10项配对Recall差中9项未校正95% query bootstrap区间跨0，Yandex L128下界也仅约+0.010pp；不能据单次wall的小百分比变化宣称稳定加速。

L128实值：WebVid Fast20K 74.260%/1938.54QPS→主候选74.190%/1968.53；Yandex89.720%/1873.77→90.055%/1921.79。零命中分别54→51和38→32，同时仍有12/4个新增失败query。原Fast30K保持独立口径；其Yandex L128为89.830%/1934.67QPS，新主候选并未在两指标同时超过原Fast30K。

## 消融与成本解释

- GT10硬在Yandex五L Recall均小幅正值，在WebVid L128/256/400却下降0.085/0.115/0.110pp。不能把增加GT目标当作统一修复。
- WebVid GT1软L64为+0.740pp，L800为−0.050pp；GT10软相对GT10硬互有高低。validation未用于重新选族或温度。
- WebVid有query支持的画像802→815，GT10软主候选中位ESS16→132.28，但支持变充分没有保证validation L128收益。高T广泛摊薄权重不等于高信息支持。
- audit主候选exact3−HNSW最终Recall为+0.146/−0.020pp；exact画像选择不是实际入口效用oracle。L128 Fast20K路由单测约7.166/4.535μs/query，仅约独立端到端wall的1%；分项wall不相加作为QPS。
- 输入准备/核对22.41s；GT1硬恢复核心合计0.447s，其余七候选/数据集构建阶段合计15.30s。cal/audit/validation搜索子进程70.52/34.26/484.65s，含加载/建图/计数等，不能称查询wall。exact GT/QGT/原NSG从零成本未新测。

## 实际范围与验收

原base、raw-IP、NSG、QGT seed20260828及H815/821固定，三个互异真实ID；matched方法均M16/efConstruction200/ef10、seed20260828、升序消费，原Fast30K保留seed100/heap顺序。GT仅用于fit构建画像和搜索后评分；fit20K、cal/audit各1024，选择和全部画像冻结后才读取历史validation2K。held-out未打开。

GT1硬画像逐位恢复P0，真实搜索恢复通过。每数据集8候选，共16份闭式画像，无single/triple训练标签、Full/rank8训练或其它变量。实际543296次原NSG调用，未使用修复预留，另1500次合成fixture调用。116点169408输出独立GT10评分通过，三基线60000个validation输出与E23逐位相同；各画像五L的HNSW图及query入口一致。所有查询进程实际线程数1、CPU15，63个绑定上游文件及冻结资产检查通过。

## 权威证据与接续

- [E24复盘](experiment_history/13_gt_topk_profiles.md)、[完整报告](entry_method_exploration/20260910_gt_topk_profiles_v1/report.md)、[全部原值](entry_method_exploration/20260910_gt_topk_profiles_v1/results/tables.md)、[Recall–QPS](entry_method_exploration/20260910_gt_topk_profiles_v1/figures/recall_qps.svg)、[差值图](entry_method_exploration/20260910_gt_topk_profiles_v1/figures/deltas.svg)。
- [结果JSON](entry_method_exploration/20260910_gt_topk_profiles_v1/results/summary.json)、[配对CSV](entry_method_exploration/20260910_gt_topk_profiles_v1/results/comparisons.csv)、[成本](entry_method_exploration/20260910_gt_topk_profiles_v1/results/costs.json)、[输出核验](entry_method_exploration/20260910_gt_topk_profiles_v1/reviews/result_verification.json)、[保护审计](entry_method_exploration/20260910_gt_topk_profiles_v1/reviews/immutable_integrity.json)。

一个构建、validation2K、单次wall、历史开发/验证访问及cosine归属的raw-IP范数缺口限制结论。E24已收口，不扩网格、不按validation换主候选；若继续，建议固定H的真实finite-L效用分组2A，保留本轮冻结画像作为对照，待用户明确下一分支。全部其它方案仍保留在s-target，不自动串行执行。

E23保留[真实三入口排序的小Recall信号、无明确整体QPS优势](experiment_history/12_three_entry_rank_exploration.md)历史身份；E22旧大矩阵和C保持停止。所有旧源码、图、GT、标签、模型和结果保留。
