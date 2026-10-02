# 148 按需QGT完整费用与浮点边界

2026-09-30，记录147的读取诊断落实为真正按需精确标签生成。原query聚类/代表顺序/去重/ravel语义保留；固定2048精确fit、17952教师标签和原画像/小图参数，两集从无标签依赖完整重建。

Web/Y完整wall为114.023/243.072秒，同日全QGT版本190.552/547.282秒，单次降40.16%/55.59%。实际仅815/821 QGT，未回退；总精确5732、NSG35968、事后ANN1024，2画像/图。没有新质量测试或默认替换；质量仍见144。

H/W逐位和物理图语义恢复、512对原生路由一致。但原全标签逐位核验失败：Web短尾批27行分数有浮点差，一行未消费的第69/70名互换。完整集合和已消费前缀一致，独立float64核验2700项、fit标签/距离不变；保留初次失败及audit_v2修正，不能称通用oracle位等价。该省费也适用于默认方法，不能作为混合监督独占收益；无随机交错、缓存未清理，不报严格统计加速。

完整证据：[报告](../entry_method_exploration/20260930_theory_until2200_v1/research/demand_qgt_full_build_v1/report.md)、[协议](../entry_method_exploration/20260930_theory_until2200_v1/research/demand_qgt_full_build_v1/protocol.md)、[成本JSON](../entry_method_exploration/20260930_theory_until2200_v1/research/demand_qgt_full_build_v1/results/cost_summary.json)、[浮点修正](../entry_method_exploration/20260930_theory_until2200_v1/research/demand_qgt_full_build_v1/audit_correction.md)、[核验](../entry_method_exploration/20260930_theory_until2200_v1/research/demand_qgt_full_build_v1/reviews/independent_audit.json)。
