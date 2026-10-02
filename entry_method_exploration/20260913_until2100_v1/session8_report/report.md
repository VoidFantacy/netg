# ACSG 第8串行研究会话报告

E82–E85四阶段完成。没有建立更好方法的完整性能证据；E84在WebVid对compact的局部修复值得保留，完整门仍失败。整日21:00目标尚未完成，E34晚间最终对照待执行。

| 阶段 | 实际结果与停止范围 |
|---|---|
| E82 新目标bank完整排名效用 | 真实补齐3593个缺失三入口键；六门均失败，不能仅凭修近似误差继续扩E79–E81目标bank。Web局部修复和精度分组保留。 |
| E83 同hub补边 | 对compact Web−1命中/失败−1，Y0/0；路由计数增加。固定同hub补边规则停止。 |
| E84 查询排名缺口补边 | 对compact Web+42/失败−4、两半+22/+20；对P仍−17/+7。Y对compact−4/0。固定最高票规则停止，不扩大其wall。 |
| E85 路由前query线性选择 | 后3976接受对P Web−35/+3、Y+24/−3；对compact Web+8/0、Y−57/+5。原收益保留约58%，双集门失败，在线未实现。 |

E84的Web变化包含114正命中和72负命中，GT成员151增/109失；保留旧compact正收益774/820、丢失46，新增32，避免旧损失82、新增损失26。实际三入口集合改变405条，38条改善、24条损伤；Y仅35条入口变化，1条改善/2条损伤。这些是配对query描述，不能当每条新边的因果贡献。E73/E74 Yandex原局部前沿信号保持。

本会话新增 **266,834 NSG / 339,072 HNSW**、8静态图边安装、2图监督训练、4岭回归拟合；0普通HNSW build/新增GT。编译12.744s，E84图监督阶段4.989s，E83/E84查询native操作分别111.127/111.272s，E82 native21.140s。操作wall含加载/count/I/O，存在子阶段包含关系，不是QPS。E83安装计时因准备元数据错误未保存、继承GT/P成本未知；E84短路由进程RSS仅轮询样本，非实际峰值。

**新增QPS点0**。最新完整开发曲线仍为[E74 QPS–Recall、QPS–失败率和按L三指标](../stage15_compact_wall_v1/report.md)，其同批55点/五轮独立wall保持原身份，不能与本会话L128诊断拼成一组曲线。晚间必须冻结候选后同批测原NSG/Fast/GT10匹配起点/实际新方法。

本报告四个真实方法的失败并集 **413** 条、状态变化 **173** 条，全方法均失败 **240** 条。独立集合/mask评分63,616行、共有P/compact全字段回归31,808行；全表含GT10、各方法三入口和返回ID。图按源行固定前24变化例展示；失败严格为零GT10集合命中。E82完整排名诊断的517条失败、E85含训练段的410条缓存失败在各阶段独立报告，不混作一批新在线实验。

[四真实方法完整失败表](failure_queries.csv) · [失败图](failure_queries.png)。

角色：P-fit20K含旧train/monitor；aux7952、旧cal/audit历史已暴露且选择反馈算训练。E84仅raw fit查询提供排名票；E85前3976真实命中差进入拟合，后3976只作本版拟合外接受，非项目未见数据。E25历史结果因避免重启旧机制被复盘，E34最终原始query/GT及held-out未打开。所有新ANN/数值训练串行CPU15和实际进程/数值库1线程，原NSG/base/rawIP固定。

[E82完整报告](../stage23_target_exact_utility_v1/report.md) · [协议](../stage23_target_exact_utility_v1/protocol.md) · [成本](../stage23_target_exact_utility_v1/results/cost.json) · [封存](../stage23_target_exact_utility_v1/reviews/final_artifact_freeze.json)
[E83完整报告](../stage24_sibling_links_v1/report.md) · [协议](../stage24_sibling_links_v1/protocol.md) · [成本](../stage24_sibling_links_v1/results/cost.json) · [封存](../stage24_sibling_links_v1/reviews/final_artifact_freeze.json)
[E84完整报告](../stage25_query_shortcuts_v1/report.md) · [协议](../stage25_query_shortcuts_v1/protocol.md) · [成本](../stage25_query_shortcuts_v1/results/cost.json) · [封存](../stage25_query_shortcuts_v1/reviews/final_artifact_freeze.json)
[E85完整报告](../stage26_query_gate_feasibility_v1/report.md) · [协议](../stage26_query_gate_feasibility_v1/protocol.md) · [成本](../stage26_query_gate_feasibility_v1/results/cost.json) · [封存](../stage26_query_gate_feasibility_v1/reviews/final_artifact_freeze.json)
