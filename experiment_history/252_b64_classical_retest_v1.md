# E252 新 B64 在三套经典平方 L2 数据上的复测

冻结 Deep10M、BIGANN 前 10M SIFT 和 GIST1M 的底库、图、三入口 GT10 和原 B32。Deep/SIFT 用 soft 画像，GIST 用 hard 画像。两套 10M 各 3,072 条公开查询，GIST 使用全部 1,000 条。每集在原 16,000 条补点拟合之外加入 4,000 条 fit 尾段和 4,192 条 QGT learn 查询，训练与全部公开查询按向量字节排除重叠。从 L176/192/208 实际 K100 遗漏续填有序 B32 前缀到 64。在线保留原生平方 L2，B32 与 Mixed64 共用同一 L2 标量主搜索。

固定真 K1/K100 的 96 个数据集/K/L 配置，二方法 192 点，CPU15 单线程各两遍，共 384 个完整批次。正式总墙钟 856.00 秒。两遍包逐字一致，另有 49,152 条配置级候选与原距离排序核验。图仅展示 Mixed64，B32 同期作为逐点和固定目标对照。

同 L 的 96 个配对中 62 个召回提高，34 个持平。Deep K1 全部持平，Deep 和 SIFT 的 K100 最大增益分别为 0.0039、0.0046 个百分点。同 L 每查询额外精算约 86–96 个候选，所选六场景 QPS 变化中位数为 −3.98% 到 −1.16%。两套 10M 数据的 28 个双边达标目标均由 B32 更快达到。

GIST K100 每档同 L 召回增加 0.009–0.122 个百分点。预设门槛仅两处 Mixed64 更快。K1 的 96% 门槛从 L200 降到 L160，513.8 到 600.8 QPS（+16.94%），同 L160 的 B32 为 95.9%。K100 的 85% 门槛从 L160 降到 L144，627.6 到 665.4 QPS（+6.03%），同 L144 的 B32 为 84.996%。这些速度来自跨过门槛后选择更小实测 L。其余 14 个 GIST 目标均由 B32 更快达到。经典 L2 保留 B32 作为常规补点对照，GIST 两处保留为局部达标证据。

[协议](../entry_method_exploration/20261123_b64_classical_retest_v1/protocol.md) · [实测报告](../entry_method_exploration/20261123_b64_classical_retest_v1/report.md) · [逐点](../entry_method_exploration/20261123_b64_classical_retest_v1/analysis/points.csv) · [两遍](../entry_method_exploration/20261123_b64_classical_retest_v1/analysis/rounds.csv) · [固定目标](../entry_method_exploration/20261123_b64_classical_retest_v1/analysis/targets.csv) · [封存](../entry_method_exploration/20261123_b64_classical_retest_v1/seal.json)
