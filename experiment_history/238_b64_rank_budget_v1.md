# E238 WebVid 由主搜索分数分配三路 B64 配额

保留原 B32/B64 顺序、同一发布核、图及三路入口。主搜索得到第 100 名负内积后，以一个单调策略选择三路的预定义容量。六个动作的候选集合逐级嵌套。比前一轮，只裁最远路改为允许容易查询缩近路。E231 开发窗 42 个原生真实 Top-K 回放点、129,024 个逐查询标量核验、28 组老动作历史包逐字相同。2,048 条拟合和 1,024 条校准同 E234。Budget40 相对等工作固定 Far40 实际多找回 431 个、少精算 9,218 个。Budget52 相对 Far52 多找回 209、少精算 26,035。数据聚合了七档 L。

3,072 条确认真 K100，105 点、210 个 CPU15 单线程完整批次。Budget40 在八个目标中七个均值更快，六个慢遍仍快。在 74.5% 目标，两者均用 L192，Budget40 1,768.6 对老 B64 1,753.0 QPS，+0.89%，慢遍对快遍 +0.58%。75.5% 处 Budget40 L208 为 1,648.0 QPS，老 B64 L204 为 1,642.8，均值 +0.31%，慢遍对快遍 −1.12%。Budget52 同目标均值 +0.08%，慢遍对快遍 −1.42%。L204 Budget40/Budget52 分别差 161/72 个正确成员达标。该机制具有 WebVid K100 条件收益，75.5% 主目标没有稳定替换依据。

[完整报告](../entry_method_exploration/20261123_b64_rank_budget_v1/report.md) · [协议](../entry_method_exploration/20261123_b64_rank_budget_v1/protocol.md) · [校准](../entry_method_exploration/20261123_b64_rank_budget_v1/models/calibration.json) · [目标比较](../entry_method_exploration/20261123_b64_rank_budget_v1/analysis/targets.csv) · [封存](../entry_method_exploration/20261123_b64_rank_budget_v1/seal.json)
