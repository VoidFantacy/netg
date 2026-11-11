# ACSG 当前结论

更新于2026-10-28。**默认保留E99 GT10：WebVid GT10-soft-t1、Yandex GT10-hard。** 最新完成[E190固定候选排序实验](entry_method_exploration/20261028_coco_fixed_candidate_scoring_v1/report_zh.md)：COCO真实K100，正式38点/114完整T1轮，primary校准26点/78轮。固定矩阵收口，无待恢复队列；可靠Recall–QPS综合目标尚未完成。

**原网格3个新评分点：2个被GT10覆盖，速度筛选1点通过。 密集GT10补充：唯一阳性L400点速度门0、预算Recall门0。** 该固定评分版本尚未形成可支付的Recall–QPS改进，停止本版本，默认E99 GT10保持。

## 本轮实际结果：固定L200

| 方法 L200 | Recall@100 | 完整QPS |
| --- | --- | --- |
| GT10 | 95.3444% | 2313.27 |
| B32 | 96.7159% | 2168.62 |
| REUSE-BLOCK | 95.5575% | 1813.32 |
| SQ8-96 | 97.2191% | 1530.95 |

QPS为本轮同一二进制三轮中位数，包含正常Batch分配/初始化、GT10路由主搜、全部补全、六数组复制和销毁；不拼接E189绝对速度。

## 得到的机制证据

同一候选pool/扫描块逐query一致。COCO L200扫描覆盖18747个遗漏；旧PQ短名单覆盖/救回2131/2131，SQ8为18747/18747。SQ8相对PQ Recall增加1.6616pp。质量机会与完整费用分开，不把扫描覆盖当免费收益。

SQ8使用全部原base的逐维minmax编码，不读query/GT训练；码额外57.75MiB，另有trained及运行时ID→位置映射，旧辅助后端负担仍在。原矩阵29点/87轮，另冻密集GT10补充9点/27轮；补充同窗口SQ8 L400相对阈值GT528速度-2.02%，预算Recall差-0.0398pp。原矩阵L400阳性筛选保留其原身份，候选/参数未改。预设PQ384两级方案未触发：校准PQ384遗漏覆盖/SQ8-96遗漏覆盖=0.3833，门槛0.75；未试其他宽度。

## 角色、核验与限制

原块表只用前12K fit，后4K按预设条件决定是否进入固定384两级方案；旧16K B32含校准标签，完全排除选择，仅正式参考。公共10K历史曝光，无新盲确认。GT10历史训练/数据角色仍沿原身份。

实际timed包三轮bits/SHA、全量实际主包补全oracle、逐query2048扫码/96原metric精算上限、第二份stdlib整数统计和预算比较通过；SQ8编码另一实现全base逐字一致，扫描pool/块顺序全query一致，原metric评分与短名单另抽核。不同实现同一执行者，非独立人员复现。旧E189的1570件seal保持。

仅COCO/K100、一图/画像；不替代K1、Deep或其余五集。SQ8结果只约束本轮具体库/编码/实现，不能推广为所有量化评分路线的性能结论。

七集两K综合证据仍为[E183](entry_method_exploration/20261017_gt10_residual_comprehensive_v1/analysis/delivery_v2/report_zh.md)，E184/E185为离线诊断；E187–189费用/覆盖结论沿[历史索引](s-experiment.md)读取。

[六页PDF](entry_method_exploration/20261028_coco_fixed_candidate_scoring_v1/ACSG_COCO固定候选排序与完整费用_20261028.pdf) · [原29点](entry_method_exploration/20261028_coco_fixed_candidate_scoring_v1/analysis/points.csv) · [补充9点](entry_method_exploration/20261028_coco_fixed_candidate_scoring_v1/dense_control_analysis/points.csv) · [预算比较](entry_method_exploration/20261028_coco_fixed_candidate_scoring_v1/analysis/discrete_comparisons.csv) · [实现](spec.md) · [下一门](s-target.md)。
