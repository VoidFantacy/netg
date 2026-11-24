# E244 WebVid 新 B64 同等访问复用验证

E243 的 Mixed64、E238 的 Budget40 与原 B64 各测原路径和同一种 E233 visited 复用，原 B32 保留。固定 SPAN4 主链、图、底库、raw-IP 路由和原生合并。验证源为 WebVid seed validation 物理行 4096–7167，3,072 条与 E237 已测窗、E243 训练及公共测试精确字节互斥。16 个 L、真 K100、112 点、224 个 CPU15 单线程完整计时批次。每个 L 三对访问复用返回位级一致，共 48 对。另逐个被跳过的 ID 核原生距离和标量合并。

75.5% 门槛，老 B64 / Visited64 的 L200 为 75.5124%，1,685.7 / 1,688.9 QPS。Mixed64 / VisitedMixed64 的 L196 为 75.5811%，1,719.6 / 1,721.0 QPS。两者都使用同等访问复用时，新表完整 QPS +1.90%，慢遍对快遍 +1.52%。都用原流程时 +2.01%，慢遍对快遍 +1.78%。这是 E243 扩样本和多预算候选表在第三个不同查询窗的正结果。Budget40 对同等 Visited64 该门槛 −2.80%。同等复用在别的目标有接近持平与负点，严格按实际目标报告。

[完整报告](../entry_method_exploration/20261123_b64_equal_fastpath_v1/report.md) · [协议](../entry_method_exploration/20261123_b64_equal_fastpath_v1/protocol.md) · [逐点](../entry_method_exploration/20261123_b64_equal_fastpath_v1/analysis/points.csv) · [逐对等价](../entry_method_exploration/20261123_b64_equal_fastpath_v1/analysis/historical_parity.csv) · [封存](../entry_method_exploration/20261123_b64_equal_fastpath_v1/seal.json)
