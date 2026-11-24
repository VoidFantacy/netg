# E217 复用 GT10 入口取补点候选

2026-11-21 完成。COCO 和 WebVid 的真 K1/K100，E206/E216 的 dev/cal L184 实际主返回，共 15,906 个状态。fit-only B32、CACHE、BKT4、BKT8 每条实际精算数一致，两条控制的八组回放包与 E216 字节一致。BKT4/BKT8 复用三个 GT10 入口取至多 12/24 个代表，以全维余弦选一条预编表替换尾部。端到端资格 0/4，正式点 0。

BKT8 相对同期 CACHE 每条补点重放省 10.30–11.99 微秒。按实际相同预算枚举桶内代表动作并允许回到 B32，COCO K100 校准窗相对同 L B32-fit 的实际及上限净增为 +199/+994，L192 所需 +412。WebVid K1 校准窗实际 +6、上限 +21、所需 +7；WebVid K100 BKT8 校准窗的上限距 L192 仍少 129 个成员。全维最近代表的选择收益低，原候选空间的上限因场景而异。GT 只参与训练角色结果统计及离线选择上限。

[报告](../entry_method_exploration/20261121_gt10_bucket_residual_v1/report.md) · [协议](../entry_method_exploration/20261121_gt10_bucket_residual_v1/protocol.md) · [资格数据](../entry_method_exploration/20261121_gt10_bucket_residual_v1/analysis/replay.csv) · [状态](../entry_method_exploration/20261121_gt10_bucket_residual_v1/state.json)。
