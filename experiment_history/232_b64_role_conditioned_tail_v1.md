# E232 WebVid 最远入口专用尾表

沿 E231 的发布 SPAN4、真 K100、原 GT10 soft-t1、候选表和两个查询窗。最远一路按既有画像距离确定。保留全部原 B32 有序前缀和另外两路的原 64，最远一路按 E183 冻结训练真漏点中前两路无覆盖的贡献重排 64 或允许纳入原 B64 之外的训练 ID。最远原顺序、重排和重编各有 40/52 两档。192 点、384 个 CPU15 单线程完整批次。

复用 E231 开发窗实际原生主返回的 56 点回放中，28 个原动作与历史包精确相同。L196 的 52 个上限，重排净增 9 个真实正确成员，重编少 53 个。确认窗同 L 重排少 14 个，重编少 43 个。确认窗 75.5% 目标下，重排 40、重编 40 分别 1,651.9、1,649.9 QPS，两个都低于同期固定 Far40 的 1,654.1 QPS。确认网格不含 L204，老 B64 同期最快达标点为 L208，与 E231 含 L204 的更密比较不能混作同一前沿。开发窗小收益未随查询窗复现，第三路重编保持实验结论。

[完整报告](../entry_method_exploration/20261123_b64_role_conditioned_tail_v1/report.md) · [协议](../entry_method_exploration/20261123_b64_role_conditioned_tail_v1/protocol.md) · [回放逐点](../entry_method_exploration/20261123_b64_role_conditioned_tail_v1/analysis/replay.csv) · [同期逐点](../entry_method_exploration/20261123_b64_role_conditioned_tail_v1/analysis/points.csv) · [封存](../entry_method_exploration/20261123_b64_role_conditioned_tail_v1/seal.json)
