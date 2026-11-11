# ACSG 当前结论

更新于2026-10-28。**默认保留E99 GT10：WebVid GT10-soft-t1、Yandex GT10-hard。** 最新完成[E188补全费用与硬预算实验](entry_method_exploration/20261028_completion_cost_budget_v1/report_zh.md)：两集真实K100，正式100点/300完整单线程轮，另100点/300轮校准。预定矩阵已收口，无待恢复队列；可靠Recall–QPS研究目标尚未完成。

**24个硬预算区域点中24个被实测GT10同时覆盖Recall与QPS；速度筛选通过0点、预算召回筛选通过0点。** 工程省费与硬预算的作用应分开看，当前不据此统一替换GT10。完整图表见[六页PDF](entry_method_exploration/20261028_completion_cost_budget_v1/ACSG_补全成本与硬预算实验_20261028.pdf)。

## 本轮实际结果：固定L200

| 数据 | 方法L200 | Recall@100 | 完整QPS | ΔRecall pp | 完整耗时增加 |
| --- | --- | --- | --- | --- | --- |
| COCO | GT10 | 95.3444% | 2095.01 | — | — |
| COCO | B32 | 96.7159% | 1982.96 | +1.3715 | +5.65% |
| COCO | REG-R | 95.5793% | 1588.24 | +0.2349 | +31.91% |
| COCO | OPT-R | 95.5793% | 1621.96 | +0.2349 | +29.17% |
| COCO | BLOCK-R512 | 95.6000% | 1621.20 | +0.2556 | +29.23% |
| COCO | BLOCK-R2048 | 95.5999% | 1621.71 | +0.2555 | +29.18% |
| COCO | BLOCK-R8192 | 95.5999% | 1622.59 | +0.2555 | +29.12% |
| COCO | BLOCK-C2048 | 95.6033% | 1641.15 | +0.2589 | +27.65% |
| Deep10M | GT10 | 97.0780% | 1794.93 | — | — |
| Deep10M | B32 | 97.0801% | 1738.11 | +0.0021 | +3.27% |
| Deep10M | REG-R | 97.5601% | 1088.63 | +0.4821 | +64.88% |
| Deep10M | OPT-R | 97.5601% | 1143.17 | +0.4821 | +57.01% |
| Deep10M | BLOCK-R512 | 97.1616% | 1537.58 | +0.0836 | +16.74% |
| Deep10M | BLOCK-R2048 | 97.3027% | 1443.23 | +0.2247 | +24.37% |
| Deep10M | BLOCK-R8192 | 97.4829% | 1233.72 | +0.4049 | +45.49% |
| Deep10M | BLOCK-C2048 | 97.3010% | 1446.68 | +0.2230 | +24.07% |

QPS是本轮同一二进制的三轮中位数，包含正常分配、GT10路由/主搜、补全、六数组复制和销毁；不拼接旧绝对QPS。完整耗时增幅为QPS_GT10/QPS_method−1，不等于QPS降幅。

## 成本与有效候选

Deep L200：REG-R平均扫码26134.2，BLOCK-R2048降至1962.3；额外平均耗时361.46→135.77μs，Recall增量0.4821→0.2247pp。扫描减少与救回保留必须一起判断，不把访问次数下降当完整性能收益。

OPT-R两集三L全部10K的ID/score/route与原REG-R逐字一致；其速度差是工程实现收益，不自动成为对GT10的改进。分段诊断在校准L200上显示Deep扫描/堆维护较大，COCO粗路由较大。legacy诊断复用扫描临时缓冲，不能当原完整wall的严格拆解；正式QPS不包含阶段计时器。

BLOCK-C2048以预算内实际净救回和费用为目标；相同预算的BLOCK-R2048为对照，所有正负结果均见报告。原REG-R共同96个PQ候选，新块法每区域48，总共96，跨后端不能解释为纯扫码量因果。全库新来源与可靠净收益仍是两个判断。

## 校准角色修正与证据限制

原协议将旧16K B32放入末4K配置选择，但该4K已用于B32表训练，六项原选择均为B32并在Deep呈现强表内收益。正式矩阵前保留[原选择](entry_method_exploration/20261028_completion_cost_budget_v1/selection_freeze.json)，另冻[角色修正](entry_method_exploration/20261028_completion_cost_budget_v1/calibration_role_correction.md)与[修正选择](entry_method_exploration/20261028_completion_cost_budget_v1/corrected_selection_freeze.json)：B32继续作为正式参考，自动校准选择排除它。模型、预算和正式100点均未改。修正六项均选择更大L GT10，正式表现见[校准选择检验](entry_method_exploration/20261028_completion_cost_budget_v1/analysis/selected_validation.csv)。不能用这4K批准旧B32泛化或部署。

新模型前12K fit/后4K cal；旧GT10可能使用过合法fitquery。正式10K不参与本轮选择，但历史曝光，非新盲确认；三轮不是三份独立质量样本。仅COCO raw-IP/Deep squared-L2、真实K100，K1/其他五集未测本新方案，无逐query门控或完整主搜状态复用。

## 失败定义、核验与成本

失败始终是单query Recall@100<10%，即0–9命中。改善、脱离失败、成员救回/损伤、源外救回分别统计；不能用平均Recall提升替代严重失败修复。源为原完整16K训练遗漏并集，稀少尾部不作普遍规律。

全部timed返回/三轮SHA、真实主包补全oracle、逐query硬上限、旧包一致、第二份stdlib集合统计、原metric分数抽检和冻结身份核验已完成。第二实现由同一执行者完成，不称独立人员审查。原E187 689文件封存不变。块后端增加内存，benchmark同时装载两种布局；suite包含内部wall，不能相加；B32计数占位0不是0精算。详细成本与限制见[报告](entry_method_exploration/20261028_completion_cost_budget_v1/report_zh.md)。

## 既有证据与接续

七集两K综合证据仍为[E183](entry_method_exploration/20261017_gt10_residual_comprehensive_v1/analysis/delivery_v2/report_zh.md)；E184/E185为几何关联诊断，不能给流形因果或免费在线净收益准入器。E187旧来源pilot保留历史原件。

[实现合同](spec.md) · [下一门](s-target.md) · [历史索引](s-experiment.md) · [100点](entry_method_exploration/20261028_completion_cost_budget_v1/analysis/points.csv) · [成对救损](entry_method_exploration/20261028_completion_cost_budget_v1/analysis/paired.csv) · [实际预算对照](entry_method_exploration/20261028_completion_cost_budget_v1/analysis/discrete_comparisons.csv) · [核验](entry_method_exploration/20261028_completion_cost_budget_v1/reviews/results_audit.json)。
