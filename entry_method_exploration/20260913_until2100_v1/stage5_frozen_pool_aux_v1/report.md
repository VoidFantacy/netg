# E64 今日固定候选的扩大历史开发复核

全部候选仍未过预锁辅助门，双集best_all保持原GT10。WebVid纯拓扑端点有净+38命中、两半均正的局部信号，但失败净增2；Yandex四个真实新端点净命中均负。E63训练池的局部正值没有被抹掉，扩大开发后的收益仍不足支持替换。

每集冻结7个现有模型，在router_train[2048:10000]全部7952行上测L128；前后3976为预锁两半。baseline加E61遗漏、E62评分/拓扑、E63零命中质量及两个sham。没有改画像/图/参数/seed，旧E61–E63 cal门失败不回写；两个sham不参加推荐。

| 数据集 | 模型 | ΔRecall pp | 净hits (两半) | 零命中数 | 救回/新增失败 |
|---|---|---:|---:|---:|---:|
| WebVid | E61_missing | +0.0088 | 7 (24/-17) | 171→177 | 19/25 |
| WebVid | E62_score | -0.0755 | -60 (-56/-4) | 171→180 | 13/22 |
| WebVid | E62_topology | +0.0478 | 38 (31/7) | 171→173 | 11/13 |
| WebVid | E63_zero_mass | -0.0025 | -2 (6/-8) | 171→172 | 5/6 |
| WebVid | E61_sham | +0.0151 | 12 (8/4) | 171→173 | 12/14 |
| WebVid | E63_sham | -0.0239 | -19 (9/-28) | 171→170 | 7/6 |
| Yandex | E61_missing | -0.0931 | -74 (-38/-36) | 156→164 | 7/15 |
| Yandex | E62_score | -0.0981 | -78 (-21/-57) | 156→164 | 7/15 |
| Yandex | E62_topology | -0.0302 | -24 (-30/6) | 156→158 | 4/6 |
| Yandex | E63_zero_mass | -0.0226 | -18 (-23/5) | 156→154 | 8/6 |
| Yandex | E61_sham | -0.0201 | -16 (-18/2) | 156→154 | 12/10 |
| Yandex | E63_sham | -0.0289 | -23 (-11/-12) | 156→158 | 4/6 |

规则要求总净命中正、两半各非负、失败数不增、totalNDC≤+1%。WebVid E62_topology通过前三项中的命中条件，但11救回伴随13新增失败；不能只汇报Recall改善。WebVid E63全池−2命中、两半+6/−8；Yandex E63−18命中、两半−23/+5，虽失败净减2，仍不满足Recall条件。Yandex E61/S分别−74/−78命中，两半均负。

诊断展示best_new按既定排序选为WebVid E62_topology、Yandex E63_zero_mass；这两个身份不表示过门或推荐。后续开发wall协议固定使用它们和全部基线，不依据测速改选；E34最终validation只在晚间最终冻结后比较。

这些7952行与本日P-fit20K、cal/audit2048在同源行身份互斥，但被Fast30K和早期研究使用；不能称全项目未观察。所有本阶段反馈用于辅助选择，属于训练信息。完整原22048行query/GT从原来源逐字恢复，source hash与图/W/mapping均核验。无最终validation/held-out访问。

实际新增222,880 NSG、222,656 HNSW，14物理源图加载/复制、28 plain/count加载，0新小图构建/GT/梯度/QPS。两个完成native job共143.010秒。首次绑核竞态在exec前0查询停止，原111440预留保留；一次修正后总预留334,320，实际调用不含未执行预留。

首次prepare导入名错误0查询、首次taskset启动竞态0查询均保留原log。run_v2在子进程exec前CPU15绑核，native及控制器共同核验实际线程1/CPU15；两dataset串行，全部terminal实际exit之后分析。111328集合/mask、14图全bytes、224原kernelparity、full plain/count以及选择/失败守恒独立核验通过。

[协议](protocol.md) · [规则和选择](results/selection.json) · [42个指标行](results/points.csv) · [失败案例](results/failure_cases.csv) · [成本](results/cost.json) · [验收](reviews/verification.json) · [启动修正](launch_repair_amendment.md) · [图](figures/auxiliary_results.svg)
