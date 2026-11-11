# 失败率、救回率与残差作用：严格低于10%的全L修正版

[打开五页PDF](ACSG_低于10%召回的查询比例_全L修正版_20261024.pdf) · [中文详细解释](report_zh.md)

用户澄清失败是**单条查询Recall@100低于10%**，不是未满100，也不是少于90。命中0–9个计入，恰好10个排除。此版替代20261024六页v1的失败/救回口径；旧PDF与封存文件保持原件。

| 页 | 内容 |
| --- | --- |
| 1 | 严格定义与七数据集GT10全L失败率 |
| 2 | 七数据集NSG / GT10 / GT10+B32的失败率曲线 |
| 3 | 原低召回query中“有所改善”与“升到至少10%”的全L热图 |
| 4 | 残差补回成员来自低召回query还是其他query，以及完整QPS费用 |
| 5 | 原L200低召回队列：残差与增大L比较；GT10救出和新增低召回 |

仅复算E183保存的真实GT与查询返回。147点、7集、7个已测L，固定原家族/同家族B32；56K唯一query、1,176,000次query-point评测。没有新ANN、GT、训练、计时或默认替换。L的连线不外推；几何与“成员遗漏量”的旧关联不能替代严格低召回尾部证据。

数据在[failure_by_L.csv](failure_by_L.csv)、[paired_rescue_by_L.csv](paired_rescue_by_L.csv)、[low_query_rows.csv](low_query_rows.csv)、[hit_distributions.csv](hit_distributions.csv)、[cross_L_query_transitions.csv](cross_L_query_transitions.csv)。原query顺序的逐query命中数保存在per_query_hits.npz。

analyze.py使用NumPy GT成员匹配，audit_counts.py另用stdlib set/array复算全部147点、98组配对并逐query核对NPZ，属于同执行者不同实现。来源身份见inputs_manifest.json，核验见integer_audit.json；原始实验与上一版报告不回写。source_before保存修正前七份现行文档。

build_report.py输出可缩放矢量PDF与逐页PNG/SVG；render_review.py渲染实际PDF。中文字形已视觉检查；Type3字体的中文Unicode抽取有限。最终交付与保护核验见delivery_validation.json。
