# E242 WebVid 75.5% 整数档复测

原样冻结 E234 线性门、单阈值，E238 Budget52、Far52、原 B32 和老 B64。复用 E231 公共确认 3,072 条，不拟合任何参数。逐一测试 L198 至 L210，真 K100 78 点、156 个完整 CPU15 单线程批次。所有交叠档的冻结方法与相应原始实验返回逐字段一致。

75.5% 门槛老 B64 L204 为 75.5150% / 1,658.1 QPS。Far52、CutoffGate、Gate 和 Budget52 全部在 L205 可达标。线性 Gate 75.5479% / 1,658.5（+0.02%，慢遍对快遍 −0.06%）。Budget52 75.5374% / 1,661.8（+0.22%，慢遍仍 +0.11%）。固定 Far52 −0.14%，单阈值 +0.10%。此网格的 B32 截于 210，不给同门槛达标点。早期 E234/E238 使用较粗网格的 204→208 比较仍保留历史身份，完整步长核对显示只需加一档 L。

[完整报告](../entry_method_exploration/20261123_b64_dense_target_v1/report.md) · [协议](../entry_method_exploration/20261123_b64_dense_target_v1/protocol.md) · [逐点](../entry_method_exploration/20261123_b64_dense_target_v1/analysis/points.csv) · [历史返包核对](../entry_method_exploration/20261123_b64_dense_target_v1/analysis/historical_parity.csv) · [封存](../entry_method_exploration/20261123_b64_dense_target_v1/seal.json)
