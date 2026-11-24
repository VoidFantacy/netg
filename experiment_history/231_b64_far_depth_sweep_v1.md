# E231 WebVid K100 第三路深度扫描

冻结原 B32、老 B64、三路原 GT10 soft-t1 和 SPAN4。较近两路各 64，较远一路试 40/48/52/56/60。开发用 E230 查询，确认另取与 E230、E229 及原画像拟合精确字节互斥的 3,072 条。两窗合计 176 点、352 批真 K100。CPU15 单线程两遍完整计时，45,056 条额外逐查询原生标量核验。开发各档另保存真实原生 GT10 主状态。公共窗在历史上用过。

开发窗 L196，Far52 的 Recall@100 为 75.5046%，QPS 1,696.7。同期老 B64 75.5586%、1,721.1 QPS，Far52 慢 1.42%。确认窗口的 75.5% 目标由老 B64 L204 达成，Far52 L208 慢 1.34%，最快可比深度 Far60 L204 慢 0.32%。深度 52 能补回开发窗所需质量，确认没有稳定完整吞吐改善。下一阶段检查相同预算下候选质量。

[报告](../entry_method_exploration/20261123_b64_far_depth_sweep_v1/report.md) · [协议](../entry_method_exploration/20261123_b64_far_depth_sweep_v1/protocol.md) · [目标实测](../entry_method_exploration/20261123_b64_far_depth_sweep_v1/analysis/targets.csv) · [封存](../entry_method_exploration/20261123_b64_far_depth_sweep_v1/seal.json)
