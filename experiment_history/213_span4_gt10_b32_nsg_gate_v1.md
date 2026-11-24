# E213 四集 GT10+B32、NSG 与 GATE 同期比较

2026-11-21 完成。COCO、Flickr30k、WebVid、Yandex first10M 各使用 E212 的公开前 3,072 条。真实 K1/K100 各 7 档 L，CPU15 实际单线程，每点两遍端到端 wall。GT10+B32、固定单入口 NSG、E200 GATE 三条链路的主图搜索均使用 E211 SPAN4，共 168 点、336 批。另加同模型 GATE 标量对照 56 点、112 批。

GATE 先在小 HNSW 上用单位 query 选三个入口，再用原始 query 调共同 raw-IP 主图。四集独立探针观察到 GATE 主搜索的原生 Faiss batch4 调用，标量对照调用数为零。正式 GATE 新旧后端返回 56/56 组逐字节一致，完整 QPS 各点提升 11.97%–27.96%，各点 SPAN4 慢遍快于标量快遍。

三条 SPAN4 链路同 L 时，GT10+B32 相比 NSG 的平均召回更高 52/56 点、召回与 QPS 同时提高 28/56 点。相比 GATE 为 54/56 和 39/56 点。21 个至少一种链路达标的预定召回配置中，最高平均 QPS 的分布为 GT10+B32 14、NSG 6、GATE 1。GATE 最快的一格为 COCO Recall@100 目标 99%，相对 NSG 约高 0.16%，两遍范围重叠。WebVid Recall@100 目标 90% 在当前网格由 GT10+B32 达到，L960 为 90.221% / 374.6 QPS。

两套实现由实际返回和测试 GT 复算全部 224 点及 448 批，另核对 112 个 E212 返回包和 52 个 E200 GATE 返回前缀。门槛是在各方法已测 L 中选择最快达标点，结果对应固定公共窗口与 E211 构建。

[报告](../entry_method_exploration/20261121_span4_gt10_b32_nsg_gate_v1/report.md) · [预锁协议](../entry_method_exploration/20261121_span4_gt10_b32_nsg_gate_v1/protocol.md) · [门槛表](../entry_method_exploration/20261121_span4_gt10_b32_nsg_gate_v1/analysis/recall_thresholds.csv) · [独立复算](../entry_method_exploration/20261121_span4_gt10_b32_nsg_gate_v1/reviews/independent_audit.json) · [状态](../entry_method_exploration/20261121_span4_gt10_b32_nsg_gate_v1/state.json)。
