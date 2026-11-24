# E233 WebVid B64 跳过主搜已打分候选

保留原 B32 前缀。Visited64 保留老 B64 供给，跳过原主搜索已打分且未进原 Top-K 的候选。OnePass64 同候选去重控制。真实 K100，次序、底库、主图、GT10 路由、原生精算合并固定。

开发和确认各 3,072 条。确认物理行从 3073 至 9222 按冻结清单选择，与开发、E229 诊断及原画像拟合窗精确字节隔离。132 点、264 批 CPU15 单线程两遍完整计时。结果均从真实返回评分。

## L196 打开第三路尾部

| 窗口 | 配置 | 实际 Recall@100 | 完整 QPS | 平均精算数 |
|---|---|---:|---:|---:|
| development | B32 | 74.8662% | 1,753.0 | 93.46 |
| development | B64-old | 75.5586% | 1,706.9 | 187.29 |
| development | Far52 | 75.5046% | 1,711.8 | 175.55 |
| development | OnePass64 | 75.5586% | 1,706.3 | 187.29 |
| development | Visited64 | 75.5586% | 1,703.1 | 180.35 |
| development | Visited52 | 75.5046% | 1,710.3 | 168.95 |
| confirmation | B32 | 74.2972% | 1,773.0 | 93.05 |
| confirmation | B64-old | 75.0208% | 1,723.3 | 186.22 |
| confirmation | Far52 | 74.9684% | 1,730.7 | 174.57 |
| confirmation | OnePass64 | 75.0208% | 1,723.6 | 186.22 |
| confirmation | Visited64 | 75.0208% | 1,720.5 | 179.61 |
| confirmation | Visited52 | 74.9684% | 1,732.8 | 168.29 |

## 75.5% 召回目标

各法使用有限网格的最快实测达标点。慢遍对快遍只描述速度波动。

| 窗口 | 配置 | L | 实际召回 | 完整 QPS | 比老 B64 | 慢遍比老 B64 快遍 |
|---|---|---:|---:|---:|---:|---:|
| development | B32 | 212 | 75.8727% | 1,642.0 | -3.80% | -4.06% |
| development | B64-old | 196 | 75.5586% | 1,706.9 | — | — |
| development | Far52 | 196 | 75.5046% | 1,711.8 | +0.28% | +0.18% |
| development | OnePass64 | 196 | 75.5586% | 1,706.3 | -0.03% | -0.21% |
| development | Visited64 | 196 | 75.5586% | 1,703.1 | -0.22% | -0.57% |
| development | Visited52 | 196 | 75.5046% | 1,710.3 | +0.20% | -0.32% |
| confirmation | B32 | 224 | 76.0280% | 1,576.6 | -5.23% | -5.35% |
| confirmation | B64-old | 204 | 75.5150% | 1,663.6 | — | — |
| confirmation | Far52 | 208 | 75.6885% | 1,644.1 | -1.17% | -1.18% |
| confirmation | OnePass64 | 204 | 75.5150% | 1,664.6 | +0.06% | -0.02% |
| confirmation | Visited64 | 204 | 75.5150% | 1,670.8 | +0.43% | +0.38% |
| confirmation | Visited52 | 208 | 75.6885% | 1,643.5 | -1.21% | -1.45% |

## 验证

33,792 次额外原生标量 Top-K 全排序核对，两遍包位级一致。逐个核跳过 ID 的原生距离。各法同档路由和画像分数一致。

![B32、老 B64、新 B64 Visited64](analysis/recall_qps.png)

[协议](protocol.md) · [逐点结果](analysis/points.csv) · [目标比较](analysis/targets.csv) · [同 L 救损](analysis/same_L.csv) · [原始两遍](analysis/rounds.csv) · [封存](seal.json)
