# E216 COCO、WebVid 在线相近查询补点

2026-11-21 完成。E211 SPAN4，原 GT10，基于同一 fit-only B32 的候选替换。VOTE 小 HNSW 取 32 后按完整维重排取 16，并实时投票。CACHE 取 4 后重排取 1，读取预编投票 ID。三路前缀保持，尾部最多换 16 个，实际精算数与同 L 原 fit 表逐查询相同。资格 24 个窗单元同时保留，两个新方法在两数据集、两种 K 的 dev/cal 同 L 均净增，转入正式测量。

正式 COCO、WebVid 各 3,072 条公开查询，真 K1/K100 各 8 档 L，纯 GT10、完整16K B32、fit-only B32、VOTE、CACHE 五臂，160 点、320 个完整 CPU15 单线程批次，两遍。32 个旧控制返回包和 E214 对齐，全部实际 ID 与时长经两实现核验。主网格同 L 相对完整 B32 的 64 个新点均增加召回且降低完整 QPS。COCO K100 的 VOTE L184 能超过完整 B32 L192 召回，QPS 较低；WebVid K1 两个新方法 L184 都超过 L192 召回，QPS 较低。

追加独立计时阶段同窗加密两代表点，59 点、118 批。COCO K100 CACHE L200 为 96.9355% / 1,980.2 QPS，完整 B32 L208 为 96.9899% / 2,034.1 QPS，CACHE 慢 2.65%。WebVid K1 CACHE L192 为 83.4635% / 1,571.0 QPS，最快达标 B32-fit L208 为 83.4961% / 1,545.3 QPS，CACHE 快 1.67%，慢遍对达标控制所有快遍仍快 1.20%。两例保留同样本下的跨 L 取舍，原粗网格的较大表观速度差单列。

VOTE 的补点重放增量 32.77–42.59 微秒/查询，CACHE 为 15.83–18.09，正式 wall 包含这条在线路径。CACHE 模型文件约 30.60/32.67 MiB。局部 WebVid K1 正例可保留为实测候选，整体替换证据不足。

[主报告](../entry_method_exploration/20261121_neighbor_residual_online_v1/report.md) · [加密对照](../entry_method_exploration/20261121_neighbor_residual_online_v1/confirmation_result.md) · [在线协议](../entry_method_exploration/20261121_neighbor_residual_online_v1/protocol.md) · [资格数据](../entry_method_exploration/20261121_neighbor_residual_online_v1/analysis/heldout_quality.csv) · [封存状态](../entry_method_exploration/20261121_neighbor_residual_online_v1/state.json)。
