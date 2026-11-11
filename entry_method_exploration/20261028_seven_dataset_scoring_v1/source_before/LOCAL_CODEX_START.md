# ACSG 当前接续入口

更新于2026-10-28；工作区`/data/netg/ACSG`，分支`research/state-20261002`，HEAD `96cf05d5410cf51272048cd1f90b4bb194e23c62`。E174–190主要是本地未提交工作，HEAD不能恢复完整产物。E190已完成，无待恢复矩阵。

## 阅读顺序

1. [AGENTS](AGENTS.md)，再读[summary](summary.md)→[spec](spec.md)→[s-target](s-target.md)→[s-experiment](s-experiment.md)。
2. [E190报告](entry_method_exploration/20261028_coco_fixed_candidate_scoring_v1/report_zh.md)、[六页PDF](entry_method_exploration/20261028_coco_fixed_candidate_scoring_v1/ACSG_COCO固定候选排序与完整费用_20261028.pdf)、[实测点](entry_method_exploration/20261028_coco_fixed_candidate_scoring_v1/analysis/points.csv)、[预算比较](entry_method_exploration/20261028_coco_fixed_candidate_scoring_v1/analysis/discrete_comparisons.csv)。
3. [条件决定](entry_method_exploration/20261028_coco_fixed_candidate_scoring_v1/selection.json) · [补充冻结](entry_method_exploration/20261028_coco_fixed_candidate_scoring_v1/dense_control_freeze.json)、[评分/覆盖核验](entry_method_exploration/20261028_coco_fixed_candidate_scoring_v1/reviews/scoring_formal_audit.json)、[质量核验](entry_method_exploration/20261028_coco_fixed_candidate_scoring_v1/reviews/formal_results_audit.json)、[状态](entry_method_exploration/20261028_coco_fixed_candidate_scoring_v1/state.json)。

## 已收敛结论

原网格3个新评分点：2个被GT10覆盖，速度筛选1点通过。 密集GT10补充：唯一阳性L400点速度门0、预算Recall门0。 该固定评分版本尚未形成可支付的Recall–QPS改进，停止本版本，默认E99 GT10保持。

同一候选pool/扫描块逐query一致。COCO L200扫描覆盖18747个遗漏；旧PQ短名单覆盖/救回2131/2131，SQ8为18747/18747。SQ8相对PQ Recall增加1.6616pp。质量机会与完整费用分开，不把扫描覆盖当免费收益。 原矩阵29点/87轮，另冻密集GT10补充9点/27轮；补充同窗口SQ8 L400相对阈值GT528速度-2.02%，预算Recall差-0.0398pp。原矩阵L400阳性筛选保留其原身份，候选/参数未改。预设PQ384两级方案未触发：校准PQ384遗漏覆盖/SQ8-96遗漏覆盖=0.3833，门槛0.75；未试其他宽度。

仅COCO/K100；旧B32只作正式参考，排除含其训练标签的校准。SQ8全base无query/GT拟合。公开test历史曝光，无新盲确认；旧E189 seal保持。

## 可复制接续提示词

```text
请接续/data/netg/ACSG，先只读核分支/HEAD与LOCAL_CODEX_START、AGENTS及四根文档，再读E190报告、selection和核验。
E190固定COCO评分矩阵已完成：正式38点/114完整T1轮，primary校准26点/78轮；默认E99 GT10保持，无待恢复队列。
候选池/扫描块逐query相同；SQ8排序质量与完整费用分开，原PQ384条件结果保留，不按曝光test追加宽度到通过。
旧E189/E190科学seal不改，不自动重跑或扩大范围；按我的当前明确任务继续。
```

本轮修改前根文档见[E190 source_before](entry_method_exploration/20261028_coco_fixed_candidate_scoring_v1/source_before/)，历史根SHA保持当时身份。
