# 146：冻结低标签候选的完整构建费用

2026-09-30已完成并核验。记录144候选从无标签输入重建，Web/Y完整wall190.552/547.282秒；生成新QGT5K+2048精确目标、其余17952近似目标，重新选H/温度/画像/图，逐位恢复原预定H/W及物理图语义。缓存OS未清空；构建输入没有旧GT、近似标签、旧温度或W。

其中QGT5K搜索84.457/356.921秒，2048精确搜索33.279/144.059秒，近似教师完整作业57.516/26.251秒；所有加载/输出计入整集wall，父子阶段不重复相加。精确CPU0–7池8/驻留15线程；教师CPU15实际1线程。历史默认核心403.997/1780.232秒提供成本背景，日期/缓存/I/O范围不同，不称同期严格加速。

新14096 exact GT、35968 NSG（含64核验）、1024路由审计ANN、2QGT聚类/2W/2图。全部标签对应行、H/W、两图层边/向量及512对训练路由核验通过；旧输入保持。默认不变，0新线上性能或新源确认。此结果补齐候选构建费，不改变记录144质量与不确定性。

下一步按需生成QGT实际消费行，保留代表顺序/去重/回退，先保证H不变再实测。记录147仅依赖诊断，不按访问比例报wall。

证据：[报告](../entry_method_exploration/20260930_theory_until2200_v1/research/hybrid_full_build_cost_v1/report.md) · [费用](../entry_method_exploration/20260930_theory_until2200_v1/research/hybrid_full_build_cost_v1/results/cost_summary.json) · [审计](../entry_method_exploration/20260930_theory_until2200_v1/research/hybrid_full_build_cost_v1/reviews/independent_audit.json)。
