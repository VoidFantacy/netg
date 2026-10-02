# E70 固定小图搜索宽度控制

2026-09-13，第4串行会话。P/duplicate3P/mode3P各ef10/30，原图/W/真实H/NSG/raw-IP固定，无训练/构图。历史aux7952/L128，固定3976两半；全部反馈计训练/开发，不是最终validation。

| 数据 | 比较 | 净命中 | ΔRecall pp | 救回/新增失败 | 两半净命中 | 路由/总NDC变化% |
|---|---|---:|---:|---|---|---|
| WebVid | mode3P30−baseline10 | +6 | +0.0075 | 43/48 | [-16, 22] | +87.32/+5.26 |
| WebVid | mode3P30−baseline30 | -100 | -0.1258 | 38/48 | [-70, -30] | +1.16/+0.22 |
| WebVid | mode3P30−mode3P10 | +112 | +0.1408 | 23/15 | [22, 90] | +79.58/+4.96 |
| WebVid | baseline30−baseline10 | +106 | +0.1333 | 13/8 | [54, 52] | +85.17/+5.03 |
| Yandex | mode3P30−baseline10 | +77 | +0.0968 | 38/31 | [8, 69] | +111.69/+3.93 |
| Yandex | mode3P30−baseline30 | +89 | +0.1119 | 33/26 | [28, 61] | +18.68/+1.16 |
| Yandex | mode3P30−mode3P10 | +28 | +0.0352 | 11/8 | [22, 6] | +75.91/+3.01 |
| Yandex | baseline30−baseline10 | -12 | -0.0151 | 8/8 | [-20, 8] | +78.37/+2.73 |

预锁的后继完整wall质量门：WebVid未通过, Yandex通过。原E66失败状态保持，不将更多计算或更高完整画像排名一致率称性能改进。

完整画像前三一致率（ef10→30）：
- WebVid baseline: 86.38% → 97.08%。
- WebVid duplicate3P: 59.09% → 81.10%。
- WebVid mode3P: 77.73% → 93.00%。
- Yandex baseline: 93.61% → 99.52%。
- Yandex duplicate3P: 72.75% → 91.55%。
- Yandex mode3P: 86.38% → 98.06%。

E69精确P与精确mode的不同结果仍是解释参照，本阶段没有重新计算完整评分；近似路径与NSG效用不是单调关系。ef30是physical node宽度，不是10个不同hub或等工作量。新增路由费用必须在后继独立完整wall收费。

实际194304 NSG/193920 HNSW/0build；24源图plain加载、24count加载，未复制小图。原生四job 150.859s、编译13.947s；操作与count均不是QPS。完整96960返回独立集合/mask核验；47712主批及768预检ef10恢复、1536预检/主批一致、63616完整slot去重距离与384原kernel对照。

CPU15，进程/OMP/OpenBLAS/MKL/NUMEXPR/BLIS线程1，native全部实际退出后分析；五字段/slot/原kernel/图SHA/加载字节/调用预算均检查。source_diff只包含允许10/30的参数和reference_graph直接加载；原评测/计时循环逐字E66，所有输出aligned。E34最终与held-out未使用，失败严格GT10零命中。

[完整配对](results/paired.csv) · [原值/完整成本](results/points.csv) · [失败案例](results/failures.csv) · [排名一致率](results/ranking.csv) · [图](figures/width_control.png) · [门](results/gate.json) · [协议](protocol.md) · [验收](reviews/verification.json)。
