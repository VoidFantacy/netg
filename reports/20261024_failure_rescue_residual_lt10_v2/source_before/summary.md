# ACSG 当前结论

更新于2026-10-24。**默认保留GT10：WebVid为GT10-soft-t1，Yandex为GT10-hard；共享NSG实现保留E99优化。** 残差补全仍是研究方案，没有替换默认。

最新研究是[E184空间分布与失败修复诊断](entry_method_exploration/20261024_residual_geometry_diagnosis_v1/report_zh.md)；最新正式性能是[E183七集评测](entry_method_exploration/20261017_gt10_residual_comprehensive_v1/analysis/delivery_v2/report_zh.md)。两轮各自已完成，当前没有待恢复的实验队列；长期“可靠Recall–QPS综合改进”目标未因此达成。

## 当前方法和性能判断

GT10用查询画像选择三个真实入口，再执行固定NSG。残差表在主搜索后补算候选并合并，不改变主遍历。E183保留原始L2/raw-IP、真实K1/K100、完整单线程wall，645点/1935批；E184只复算已有56K查询并新增离线几何诊断，没有新ANN、GT、训练或QPS。

- GT10对Deep/SIFT有迁移收益；GIST较弱且有混合结果。
- B32相对自身GT10：WebVid/COCO两K共同Recall区间的既有折线均受益；Flickr交叉，Yandex K100较低；Deep/SIFT K100较低，GIST混合。
- 同L增召回且变慢是补点取舍；不能据此否定完整曲线改善。共同Recall区间的折线描述不等于新增等Recall实测，也不外推未测L。

下面固定L200；Deep/SIFT/Web用soft，其余hard，补全为同家族B32。QPS直接引用E183三轮完整wall中位数，不能与E99/E103等不同核、不同计时批次的绝对速度拼接。

| 数据集 | GT10 Recall@100 / QPS | B32 Recall@100 / QPS | 同L净Recall pp / QPS变化 |
| --- | --- | --- | --- |
| Deep10M | 97.0780% / 1934.02 | 97.0801% / 1867.56 | +0.0021 / -3.44% |
| SIFT10M | 98.1532% / 1617.15 | 98.1557% / 1565.00 | +0.0025 / -3.22% |
| GIST1M | 89.1140% / 611.73 | 89.1800% / 601.90 | +0.0660 / -1.61% |
| WebVid | 72.7033% / 1756.55 | 74.7290% / 1661.32 | +2.0257 / -5.42% |
| Yandex | 88.7724% / 1632.56 | 88.8294% / 1569.01 | +0.0570 / -3.89% |
| COCO | 95.3444% / 2690.89 | 96.7159% / 2522.93 | +1.3715 / -6.24% |
| Flickr30k | 97.2072% / 2569.23 | 97.6352% / 2428.35 | +0.4280 / -5.48% |

## 失败与改进比例

| 数据集 | K1失败率 | K100未满100查询 | 原未满100查询中净改善 | 遗漏成员修复率 |
| --- | --- | --- | --- | --- |
| Deep10M | 0.50% | 55.24% | 0.38% | 0.0719% |
| SIFT10M | 0.08% | 53.91% | 0.46% | 0.1354% |
| GIST1M | 3.00% | 90.50% | 6.74% | 0.6063% |
| WebVid | 19.44% | 99.16% | 60.84% | 7.4210% |
| Yandex | 6.32% | 86.89% | 5.08% | 0.5077% |
| COCO | 1.92% | 85.32% | 73.20% | 29.4591% |
| Flickr30k | 0.28% | 74.74% | 42.07% | 15.3251% |

K1失败为实际K1未命中GT1；K100未满100包括只少一个成员。“原失败中净改善”的分母是原未满100查询，“遗漏成员修复率”的分母是原遗漏成员；两者都不等于整条查询已找齐。COCO完整恢复100/100为1402/8532（16.43%），Web为34/9916（0.34%）。主L200损伤0；全已有B32预算的5个边界损伤事件照常保留。

## 残差与空间分布的判断

**空间结构与主搜失败有关，静态残差收益另受遗漏目标重现、路由覆盖和容量保留约束。** 不能概括为多模态天然有效、越小越有效或越聚集越有效。

- Deep/SIFT超过99%的测试遗漏不在当前训练残差源里。固定源即使全取且不计费用，额外Recall上限仅0.0195/0.0140pp；保持当前路由源则为0.0086/0.0062pp。扩大当前表无法补源外目标。
- GIST的10886个遗漏→训练源4242→路由源1117→B32救回66，路由和保留损失明显，不能沿用单一“源外”解释。Yandex训练源覆盖仅7.528%，来源和选择都受限。
- 跨七集，训练残差目标重复倍率与成员修复率Spearmanρ=0.964，原遗漏成员率ρ=0.214。七集规模、metric、特征、图、训练和容量密度未配平；源覆盖还与救回有结构包含关系，相关不是因果证明。
- 数据集内几何分离与遗漏数多数负相关。按原遗漏量粗分层后，Web/COCO高分离组改善概率高8.17/11.50pp，高训练残差频次组高44.69/19.61pp；几何仍有条件关联，粗分层不构成因果调整。GT几何特征尚不能作为免费在线门控。
- E182同源规模对照已显示：固定H的小库优势在密度控制后不再单调；H还改变路由和每hub训练密度，不能归结为纯规模规律。

## 核验、成本与限制

E184成功诊断170.346秒、stdlib set/Counter第二实现4.368秒；56K逐条整数、9项跨集秩相关和14项条件差值核验通过，每集8条query验证8192背景样本的距离矩公式。由同一执行者完成不同实现，不称独立人员审查；首类型错误失败日志保留，失败wall未记录。

E183正式suite18267.58秒（约5.07h），包含内部正式wall、预热和保存核验；不能与1935内部wall再相加。独审407.80秒，历史完整冷启动成本未知。完整费用见[E183账本](entry_method_exploration/20261017_gt10_residual_comprehensive_v1/analysis/cost_ledger.json)与[E184收据](entry_method_exploration/20261024_residual_geometry_diagnosis_v1/analysis/receipt.json)。

单图/单画像、已曝光公共查询、GIST仅1K、8192背景样本、描述性相关及未独立重算的旧bootstrap/插值限制保留。没有新增盲确认、因果干预、默认替换或可靠性能结论。

## 证据与文档入口

[六页图表PDF：失败率、救回率与残差作用](reports/20261024_failure_rescue_residual_v1/ACSG_失败率_救回率与残差作用_20261024.pdf)覆盖三方法失败、不同分母的救回/完整修复、遗漏分区、收益/费用及完整K100曲线；只重排E183/E184既有结果，无新增实验。

[E184详细报告](entry_method_exploration/20261024_residual_geometry_diagnosis_v1/report_zh.md) · [逐集CSV](entry_method_exploration/20261024_residual_geometry_diagnosis_v1/analysis/dataset_summary.csv) · [56K查询CSV](entry_method_exploration/20261024_residual_geometry_diagnosis_v1/analysis/query_metrics.csv) · [覆盖链](entry_method_exploration/20261024_residual_geometry_diagnosis_v1/analysis/coverage_chain.csv) · [第二实现核验](entry_method_exploration/20261024_residual_geometry_diagnosis_v1/analysis/integer_audit.json) · [E183全部645点](entry_method_exploration/20261017_gt10_residual_comprehensive_v1/analysis/final_v1/points.csv) · [E183独审](entry_method_exploration/20261017_gt10_residual_comprehensive_v1/reviews/independent_results_audit.json)。

实现与数据合同见[spec](spec.md)，后续研究问题见[s-target](s-target.md)，历史见[s-experiment](s-experiment.md)。清理前历次“当前/运行中/截止安排”的完整正文已[归档](experiment_history/_maintenance/20261024_current_state_cleanup_v1/archive/summary.md)，仅保留历史身份，不作为当前队列。
