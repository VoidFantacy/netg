# E184：残差与空间分布、失败比例及改进比例的离线诊断

2026-10-24，用户要求回顾项目并研究这些因素的关联。范围已完成；最新正式性能仍为E183，默认保留E99 GT10。本轮不重开旧队列，不新增ANN、GT、训练、图、模型或QPS测量。

## 范围与问题

复用E183实际计时返回，固定简版家族（Deep/SIFT/Web为soft，其余hard）、B32、L200、真实K1/K100。七集共56,000条query；重新统计Top1失败、Top100未满100/少于90、逐query净改善、完整修复与成员救损。全已有K100/L与hard/soft B32结果仅做敏感性分析，不按新反馈换赢家。

新几何统计使用全部原query/GT100目标向量和每集seed20261024均匀无放回8192个base样本；原L2/raw-IP不变。检查背景距离标准化分离z、邻域方向集中、相对跨度/范数及样本中心化协方差有效秩。z不是论文原始relative contrast，有效秩不是内在维数；GT特征仅事后诊断，未部署在线预测。

## 主要发现

主L200 K100：原未满100查询中得到净改善的比例为Deep0.38%、SIFT0.46%、GIST6.74%、Web60.84%、Yandex5.08%、COCO73.20%、Flickr42.07%；成员遗漏修复率分别0.0719/0.1354/0.6063/7.4210/0.5077/29.4591/15.3251%。改善一条query不等于找齐100个成员，完整修复另列。

Deep/SIFT的测试遗漏仅0.667%/0.758%位于当前训练残差源内；固定源不计费用的乐观Recall额外上限为0.0195/0.0140pp，当前路由源上限为0.0086/0.0062pp。扩大当前表不能补源外目标。GIST为10886遗漏→源4242→路由1117→B32救回66；路由和保留损失更突出。Web/COCO/Flickr有更多重复支持，Yandex源内仅7.528%；不能单归因多模态、库规模或“空间平坦”。

跨七集，成员修复率与训练残差重复倍率的Spearmanρ=0.964，留一集0.943..1.000；与原成员遗漏率ρ=0.214，留一−0.143..0.543。训练GT重复倍率ρ=0.929。源覆盖与修复率ρ=0.964，但有结构包含关系，不是独立因果证据。七集规模/metric/图/特征/容量密度没有配平，不能从这些相关推出普遍规律。

各集内背景分离z与GT10遗漏数多数负相关（Deep−0.477/SIFT−0.274/Web−0.452/Y−0.684/COCO−0.592/Flickr−0.537，GIST−0.072）。与残差是否改善的无条件相关较弱；按原遗漏量粗分层后，Web/COCO高z半组改善概率仍高8.17/11.50pp，高训练残差频次半组高44.69/19.61pp。几何难度和遗漏复用性需分开分析；分层仍非因果调整，层内混杂和不同支持查询数保留。

## 成本、核验和限制

成功诊断170.346秒，stdlib set/Counter第二实现4.368秒；均为离线成本，不是QPS。首尝试布尔常量判断类型错误已保留失败日志，精确失败wall未知；修正后同协议重算，没有性能重测。主统计与E183已审CSV对齐；第二实现逐query复核全部56K的K1/K100、训练源频次和分区，不导入主analyzer或NumPy。它由同一执行者编写，不冒称独立人员审计。每集8条query直接验证8192背景样本均值/方差代数；小输入SHA和大base stat前后保持，整库SHA继承E183。

同L净Recall增加仍支付1.61%..6.24%完整QPS费用（引用E183）；不能以此否定Web/COCO既有同Recall曲线受益，也不能用本轮几何统计宣称新增可靠Recall–QPS改善。单图/模型、已曝光测试、GIST仅1K、单背景样本、固定L跨集难度不同、描述性相关/未作泛化校准等限制保留。

## 判断与后续边界

更符合证据的机制假说是：局部几何影响主搜难度，遗漏目标是否重现及其路由集中程度影响静态表可复用性，有限容量决定机会保留。该假说未经随机干预证明。后续优先区分源外主导与路由/容量主导；若做新方法，应固定合法来源、同源简单频次控制和未参与选择的查询角色，验证几何有无额外解释力，并测全部线上费用。当前仅记录建议，没有训练/门控/补测队列；本次诊断目标已完成，长期可靠Recall–QPS项目目标没有因此达成。

## 2026-10-24 六页图表PDF交付

按用户要求新增[失败率、救回率与残差作用PDF](../reports/20261024_failure_rescue_residual_v1/ACSG_失败率_救回率与残差作用_20261024.pdf)：三方法失败率、不同基准的K1救回、K100查询改善/完整恢复/成员补回、残差流程与遗漏分区、完整QPS费用、147点K100曲线及空间关联。仅重排E183/E184数据，无新ANN/GT/训练/计时。图表数据、来源身份、实际PDF渲染与交付检查见[报告目录](../reports/20261024_failure_rescue_residual_v1/README.md)；原E184科学文件和旧交付manifest未改。

[完整中文报告](../entry_method_exploration/20261024_residual_geometry_diagnosis_v1/report_zh.md) · [冻结范围](../entry_method_exploration/20261024_residual_geometry_diagnosis_v1/protocol.md) · [逐集统计](../entry_method_exploration/20261024_residual_geometry_diagnosis_v1/analysis/dataset_summary.csv) · [56K查询](../entry_method_exploration/20261024_residual_geometry_diagnosis_v1/analysis/query_metrics.csv) · [覆盖链](../entry_method_exploration/20261024_residual_geometry_diagnosis_v1/analysis/coverage_chain.csv) · [几何关联](../entry_method_exploration/20261024_residual_geometry_diagnosis_v1/analysis/within_dataset_spearman.csv) · [遗漏量分层](../entry_method_exploration/20261024_residual_geometry_diagnosis_v1/analysis/baseline_stratified_associations.csv) · [第二实现核验](../entry_method_exploration/20261024_residual_geometry_diagnosis_v1/analysis/integer_audit.json) · [成功成本](../entry_method_exploration/20261024_residual_geometry_diagnosis_v1/analysis/receipt.json)。
