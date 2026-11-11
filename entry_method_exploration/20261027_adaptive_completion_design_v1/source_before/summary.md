# ACSG 当前结论

更新于2026-10-24。**默认保留GT10：WebVid为GT10-soft-t1，Yandex为GT10-hard；共享NSG实现保留E99优化。** 残差补全仍是研究方案，没有替换默认。

最新研究是[E185流形相关几何探查](entry_method_exploration/20261024_manifold_residual_probe_v1/report_zh.md)，承接[E184空间分布诊断](entry_method_exploration/20261024_residual_geometry_diagnosis_v1/report_zh.md)；最新正式性能是[E183七集评测](entry_method_exploration/20261017_gt10_residual_comprehensive_v1/analysis/delivery_v2/report_zh.md)。上述诊断与性能轮次各自已完成，当前没有待恢复的实验队列；长期“可靠Recall–QPS综合改进”目标未因此达成。

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

## 失败与改进比例：严格Recall@100低于10%

**用户已澄清：失败是单条查询Recall@100低于10%，即命中0–9个GT100成员；恰好10个排除。** 分母是同集/方法/L全部query。此前主表的“未满100”不符合这个问题，旧图表与当时记录保留，但现行解读由[全L修正报告](reports/20261024_failure_rescue_residual_lt10_v2/report_zh.md)取代。

GT10低召回失败率：

| 数据集 | L100 | L128 | L200 | L400 | L800 | L1000 | L1200 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Deep10M | 0.04% | 0.04% | 0.02% | 0.01% | 0.00% | 0.00% | 0.00% |
| SIFT10M | 0.01% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| GIST1M | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| WebVid | 1.92% | 1.33% | 0.53% | 0.20% | 0.03% | 0.01% | 0.00% |
| Yandex | 1.67% | 1.36% | 0.86% | 0.45% | 0.23% | 0.16% | 0.14% |
| COCO | 0.02% | 0.02% | 0.01% | 0.01% | 0.00% | 0.00% | 0.00% |
| Flickr30k | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |

固定L200的三方法与残差增量：

| 数据集 | NSG失败率 | GT10失败率 | B32失败率 | 原低召回中有所改善 | 原低召回中升到≥10% |
| --- | --- | --- | --- | --- | --- |
| Deep10M | 0.00% | 0.02% | 0.02% | 0/2 | 0/2 |
| SIFT10M | 0.00% | 0.00% | 0.00% | —（无原低召回） | —（无原低召回） |
| GIST1M | 0.00% | 0.00% | 0.00% | —（无原低召回） | —（无原低召回） |
| WebVid | 1.42% | 0.53% | 0.46% | 26/53 | 7/53 |
| Yandex | 1.74% | 0.86% | 0.85% | 5/86 | 1/86 |
| COCO | 0.00% | 0.01% | 0.01% | 0/1 | 0/1 |
| Flickr30k | 0.00% | 0.00% | 0.00% | —（无原低召回） | —（无原低召回） |

Web L200改善26/53，但只有7/53（13.21%）脱离低召回，19条改善后仍低于10%；Yandex改善5/86，脱离1/86（1.16%）。达到10%不代表高召回或完整恢复。L200 GT10也新增Deep2条、COCO1条低召回，不能只报救出。

**残差总体收益主要来自原本≥10%的query。** L200 Web补回20257个GT成员，其中75个（0.37%）来自原低召回query；Yandex为8/570（1.40%）；COCO为0/13715。因此“总体Recall增加”不能直接解释为“严重失败已解决”。

成员遗漏修复率与未满100/恢复100统计仍是有效的辅助指标，但不是当前失败率。原E184的跨集/空间关联针对这些广义遗漏结果，不能直接当作低于10%尾部的证据。主L200残差损伤0、其他已有B32预算的边界事件保持原记录；本次只复算147个既有点，无新ANN/GT/训练/计时。

## 残差与空间分布的判断

E185新补3584条固定样本局部PCA和最近训练query对照，另对56K原query增加基线/频次双因素分层。**支持局部几何连续性与遗漏共享有关，不支持单一“越低维越有效”。** COCO最近训练GT100重合42.00%，入口重合数匹配对照18.29%；训练遗漏覆盖10.51% vs 2.61%（是单条最近训练query的覆盖，不是B32最终修复率）。

COCO局部GT100有效秩27.59，高于SIFT19.69/Deep22.86，却有更高残差修复率。原命中段与训练残差频次分层后，高分离度组改善概率差COCO+12.04pp、Web+1.09pp；局部秩差值方向跨集混合。PCA秩不是真实流形维数；粗分层/七集相关不能作因果或新数据净收益准入器。完整[结果与局限](entry_method_exploration/20261024_manifold_residual_probe_v1/report_zh.md)。

**空间结构与主搜遗漏量有关，静态残差收益另受遗漏目标重现、路由覆盖和容量保留约束。** 这一广义遗漏关联不自动适用于本次严格低于10%的稀少尾部。 不能概括为多模态天然有效、越小越有效或越聚集越有效。

- Deep/SIFT超过99%的测试遗漏不在当前训练残差源里。固定源即使全取且不计费用，额外Recall上限仅0.0195/0.0140pp；保持当前路由源则为0.0086/0.0062pp。扩大当前表无法补源外目标。
- GIST的10886个遗漏→训练源4242→路由源1117→B32救回66，路由和保留损失明显，不能沿用单一“源外”解释。Yandex训练源覆盖仅7.528%，来源和选择都受限。
- 跨七集，训练残差目标重复倍率与成员修复率Spearmanρ=0.964，原遗漏成员率ρ=0.214。七集规模、metric、特征、图、训练和容量密度未配平；源覆盖还与救回有结构包含关系，相关不是因果证明。
- 数据集内几何分离与遗漏数多数负相关。按原遗漏量粗分层后，Web/COCO高分离组改善概率高8.17/11.50pp，高训练残差频次组高44.69/19.61pp；几何仍有条件关联，粗分层不构成因果调整。GT几何特征尚不能作为免费在线门控。
- E182同源规模对照已显示：固定H的小库优势在密度控制后不再单调；H还改变路由和每hub训练密度，不能归结为纯规模规律。

## 核验、成本与限制

E185成功诊断123.540秒，另有单例匹配失败日志（失败wall未知）；第二份stdlib集合/秩/分层核验通过，仍无新ANN/GT/训练/QPS。E184成功诊断170.346秒、stdlib set/Counter第二实现4.368秒；56K逐条整数、9项跨集秩相关和14项条件差值核验通过，每集8条query验证8192背景样本的距离矩公式。由同一执行者完成不同实现，不称独立人员审查；首类型错误失败日志保留，失败wall未记录。

E183正式suite18267.58秒（约5.07h），包含内部正式wall、预热和保存核验；不能与1935内部wall再相加。独审407.80秒，历史完整冷启动成本未知。完整费用见[E183账本](entry_method_exploration/20261017_gt10_residual_comprehensive_v1/analysis/cost_ledger.json)与[E184收据](entry_method_exploration/20261024_residual_geometry_diagnosis_v1/analysis/receipt.json)。

单图/单画像、已曝光公共查询、GIST仅1K、8192背景样本、描述性相关及未独立重算的旧bootstrap/插值限制保留。没有新增盲确认、因果干预、默认替换或可靠性能结论。

## 证据与文档入口

[五页全L修正版PDF：Recall低于10%的查询比例](reports/20261024_failure_rescue_residual_lt10_v2/ACSG_低于10%召回的查询比例_全L修正版_20261024.pdf)覆盖严格失败口径、三方法全L曲线、低召回改善与脱离、残差收益来源以及更大L的同队列比较。147点原始返回已重算并经第二份stdlib实现核验；旧六页版未满100口径保留历史身份。

[E184详细报告](entry_method_exploration/20261024_residual_geometry_diagnosis_v1/report_zh.md) · [逐集CSV](entry_method_exploration/20261024_residual_geometry_diagnosis_v1/analysis/dataset_summary.csv) · [56K查询CSV](entry_method_exploration/20261024_residual_geometry_diagnosis_v1/analysis/query_metrics.csv) · [覆盖链](entry_method_exploration/20261024_residual_geometry_diagnosis_v1/analysis/coverage_chain.csv) · [第二实现核验](entry_method_exploration/20261024_residual_geometry_diagnosis_v1/analysis/integer_audit.json) · [E183全部645点](entry_method_exploration/20261017_gt10_residual_comprehensive_v1/analysis/final_v1/points.csv) · [E183独审](entry_method_exploration/20261017_gt10_residual_comprehensive_v1/reviews/independent_results_audit.json)。

实现与数据合同见[spec](spec.md)，后续研究问题见[s-target](s-target.md)，历史见[s-experiment](s-experiment.md)。清理前历次“当前/运行中/截止安排”的完整正文已[归档](experiment_history/_maintenance/20261024_current_state_cleanup_v1/archive/summary.md)，仅保留历史身份，不作为当前队列。
