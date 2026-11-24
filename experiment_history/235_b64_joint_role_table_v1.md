# E235 WebVid 三路入口角色联合编表

真 K100，发布 SPAN4、WebVid GT10 soft-t1 与 E231 双查询窗。同样的原有序 B32 行按画像位置区分三种角色，联合迭代真实训练事件在未被另两路覆盖时的增量。限制 64/64/40 时有只用原 B64 ID 的 RankOrder40 以及允许原训练真漏点补进的 RankFill40。RankFill56 对同一名义总预算做均匀三路限额。仅用原 E183 的 16,000 条训练，比较开发和确认 154 点、308 个完整 CPU15 单线程批次。

RankFill40 在训练上覆盖由 104,853 到 139,265 个事件，超过老 B64 的训练覆盖 113,793。确认窗 L196 相对同期 Far40 却少 63 个正确成员，实际精算多 0.12 个/查询。确认达到 75.5% 仍需 L208，QPS 比老 B64 L204 慢 0.93%。RankFill56 为 −1.03%，RankOrder40 为 −1.33%。此固定训练范围的角色细分未复现训练优势。

[完整报告](../entry_method_exploration/20261123_b64_joint_role_table_v1/report.md) · [协议](../entry_method_exploration/20261123_b64_joint_role_table_v1/protocol.md) · [训练可达性](../entry_method_exploration/20261123_b64_joint_role_table_v1/banks/far/training_certificate.json) · [同期逐点](../entry_method_exploration/20261123_b64_joint_role_table_v1/analysis/points.csv) · [封存](../entry_method_exploration/20261123_b64_joint_role_table_v1/seal.json)
