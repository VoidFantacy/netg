# E235 WebVid 三路角色联合编表

保留原 B32 前缀。在不改 B32 前缀的条件下，离线对三路分别分配互补尾部候选。RankOrder 保持原候选支持，RankFill 可选训练内的新 ID。真实 K100，次序、底库、主图、GT10 路由、原生精算合并固定。

开发和确认各 3,072 条。确认物理行从 3073 至 9222 按冻结清单选择，与开发、E229 诊断及原画像拟合窗精确字节隔离。154 点、308 批 CPU15 单线程两遍完整计时。结果均从真实返回评分。

## L196 打开第三路尾部

| 窗口 | 配置 | 实际 Recall@100 | 完整 QPS | 平均精算数 |
|---|---|---:|---:|---:|
| development | B32 | 74.8662% | 1,753.3 | 93.46 |
| development | B64-old | 75.5586% | 1,702.2 | 187.29 |
| development | Far40 | 75.4417% | 1,720.6 | 163.79 |
| development | Far52 | 75.5046% | 1,714.7 | 175.55 |
| development | RankOrder40 | 75.4417% | 1,708.8 | 163.78 |
| development | RankFill40 | 75.4176% | 1,719.3 | 163.83 |
| development | RankFill56 | 75.3841% | 1,713.8 | 163.92 |
| confirmation | B32 | 74.2972% | 1,735.7 | 93.05 |
| confirmation | B64-old | 75.0208% | 1,686.6 | 186.22 |
| confirmation | Far40 | 74.8978% | 1,683.2 | 162.98 |
| confirmation | Far52 | 74.9684% | 1,694.7 | 174.57 |
| confirmation | RankOrder40 | 74.8984% | 1,728.4 | 163.00 |
| confirmation | RankFill40 | 74.8773% | 1,720.2 | 163.10 |
| confirmation | RankFill56 | 74.8568% | 1,694.8 | 163.07 |

## 75.5% 召回目标

各法使用有限网格的最快实测达标点。慢遍对快遍只描述速度波动。

| 窗口 | 配置 | L | 实际召回 | 完整 QPS | 比老 B64 | 慢遍比老 B64 快遍 |
|---|---|---:|---:|---:|---:|---:|
| development | B32 | 208 | 75.6410% | 1,670.9 | -1.84% | -2.12% |
| development | B64-old | 196 | 75.5586% | 1,702.2 | — | — |
| development | Far40 | 204 | 75.9671% | 1,658.6 | -2.56% | -2.79% |
| development | Far52 | 196 | 75.5046% | 1,714.7 | +0.74% | +0.52% |
| development | RankOrder40 | 204 | 75.9661% | 1,659.2 | -2.53% | -2.86% |
| development | RankFill40 | 200 | 75.6924% | 1,672.9 | -1.72% | -3.03% |
| development | RankFill56 | 200 | 75.6595% | 1,675.4 | -1.57% | -2.64% |
| confirmation | B32 | 224 | 76.0280% | 1,582.4 | -5.23% | -5.35% |
| confirmation | B64-old | 204 | 75.5150% | 1,669.7 | — | — |
| confirmation | Far40 | 208 | 75.6195% | 1,657.3 | -0.74% | -0.78% |
| confirmation | Far52 | 208 | 75.6885% | 1,648.9 | -1.24% | -1.25% |
| confirmation | RankOrder40 | 208 | 75.6188% | 1,647.4 | -1.33% | -1.87% |
| confirmation | RankFill40 | 208 | 75.5993% | 1,654.2 | -0.93% | -0.96% |
| confirmation | RankFill56 | 208 | 75.5785% | 1,652.5 | -1.03% | -1.26% |

## 验证

39,424 次额外原生标量 Top-K 全排序核对，两遍包位级一致。三路角色表只用 E183 训练遗漏。各法同档路由和画像分数一致。

![B32、老 B64、新 B64 RankFill40](analysis/recall_qps.png)

[协议](protocol.md) · [逐点结果](analysis/points.csv) · [目标比较](analysis/targets.csv) · [同 L 救损](analysis/same_L.csv) · [原始两遍](analysis/rounds.csv) · [封存](seal.json)
