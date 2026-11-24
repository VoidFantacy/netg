# E253 经典 L2 三方法同期比较

在 E252 的 Deep10M、BIGANN-SIFT10M、GIST1M 上增加纯 GT10，三臂重跑同一冻结查询与 L 网格。三臂共用 E211 发布库的原平方 L2 标量主搜索。GT10 直接返回主搜索 Top-K，两条补点臂使用 E252 的相同表和精算路径。真 K1/K100、96 个数据集/K/L 配置、288 点、576 个完整 CPU15 单线程批次，每点两遍取 QPS 均值。

正式总墙钟 1302.84 秒。两遍原生返回逐字一致，历史 E252 的两种补点 192 组也逐字匹配四字段。每点额外核验首 256 条，共 73,728 条配置级查询。计时全部结束后以相同冻结 L2 真值统一评分。

44 个预设达标目标均可比较。纯 GT10 最快 41 个，GT10+B32 最快 0 个，Mixed64 最快 3 个。GIST 的 Recall@1 96% 从纯 GT10 L200、524.2 QPS 到 Mixed64 L160、599.3 QPS（+14.32%）。Recall@100 85% 从纯 GT10 L160、635.1 QPS 到 Mixed64 L144、650.1 QPS（+2.36%）。两处慢遍仍快，优势按网格和门槛解释。SIFT K100 的 99.8% 门槛双方同为 L640，新版只快 0.27%，两遍速度范围交叠。Deep 与 SIFT 的 K100 相同 L 下，Mixed64 相对纯 GT10 最大只提高 0.0094 与 0.0101 个百分点。GIST 同 L 最大提高 K1 0.600 与 K100 0.245 个百分点。

[协议](../entry_method_exploration/20261123_gt10_b32_mixed64_classical_v1/protocol.md) · [三方法报告](../entry_method_exploration/20261123_gt10_b32_mixed64_classical_v1/report.md) · [逐点](../entry_method_exploration/20261123_gt10_b32_mixed64_classical_v1/analysis/points.csv) · [固定目标](../entry_method_exploration/20261123_gt10_b32_mixed64_classical_v1/analysis/targets.csv) · [历史返回核验](../entry_method_exploration/20261123_gt10_b32_mixed64_classical_v1/analysis/historical_parity.csv) · [封存](../entry_method_exploration/20261123_gt10_b32_mixed64_classical_v1/seal.json)
