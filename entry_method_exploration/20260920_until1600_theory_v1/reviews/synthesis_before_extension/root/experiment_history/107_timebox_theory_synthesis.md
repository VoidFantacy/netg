# 107｜E107–E111限时理论综合

2026-09-20，13:05:42–16:00的理论→方法→冻结核验研究；阶段结果已完成，最终截止状态以[父状态](../entry_method_exploration/20260920_until1600_theory_v1/state.json)为准。本条是跨阶段综合，不是E112或新正式性能试验。

GT10固定权重方向目标有闭式最优解；当前证据将H自适应入口、画像精确质量、普通小图恢复能力和有限池多入口竞争分开。没有稳定替换原默认。E109完美区域代理未过跨数据门，E110首展开修复未稳定超过单入口，E111保守证书在Yandex覆盖不足。

后续四次冻结内核合成执行表明，相同几何和GT在两张强连通有向图上可出现入口优劣反转；范围限任意有向图，不宣称toy是NSG构图产物，也不否定固定图上的可学习性。图中包含两个合成cycle，不计为数据集索引构建。

E111后数学审查修正：核心与外部严格分离仅保证成员保留，指定GT1 ID返回还需内部第一名无并列或GT一致的并列规则。原文前件与理由保存，冻结阶段报告、GT、Recall及15条违例保持；这些违例都来自同一条query的逐字重复向量。不能用0.024414pp的单query边界解释大部分旧失败。

本限时段2,797,056真实NSG、6次合成kernel调用、4张普通路由小图，0新底层图/GT/梯度训练/held-out/生产或默认变更。E111生成图派生诊断标签；E108有54配置/162轮单线程完整在线wall。含加载搜索进程累计2888.65秒，编译/准备/派生/分析另计，历史输入成本未知部分不置零。

默认仍Web GT10-soft-t1、Yandex GT10-hard及生产E99；E103仍是最新完整五数据集前沿。截止后无自动训练、补网格或部署队列。

[完整报告](../entry_method_exploration/20260920_until1600_theory_v1/report.md) · [成本台账](../entry_method_exploration/20260920_until1600_theory_v1/results/cost_ledger.json) · [图依赖反例](../entry_method_exploration/20260920_until1600_theory_v1/research/graph_dependence_v1/report.md) · [理论修正](../entry_method_exploration/20260920_until1600_theory_v1/reviews/theory_scope_correction.json) · [最终验收](../entry_method_exploration/20260920_until1600_theory_v1/reviews/completion_audit.json)。
