# E65 今日候选的历史开发集完整wall比较

2026-09-13，`COMPLETE_DEVELOPMENT_WALL_LOCAL_WEB_SIGNAL_NO_REPLACEMENT`。固定E64的best_new：WebVid E62_topology、Yandex E63_zero_mass，与原NSG/Fast30K/GT10-hard同机同批五L五轮，WebVid另匹配soft起点。45方法点、225完整plain wall全部完成。数据是已用于E64选择的router_train[2048:4096]历史开发2048，不能称最终泛化验证；E34最终validation今日未打开，旧cal/aux失败保持。

相对匹配起点，WebVid五L ΔRecall为−0.0391/+0.0244/+0.0781/+0.0635/+0.0195 pp；中位QPS变化+0.616/+0.503/−0.049/+0.118/+0.346%。保留4/5点Recall正值和共同Recall描述性插值+0.570/+0.683/+0.814%的局部曲线信号；五个QPS交叉范围均含零，失败净新增0/2/1/1/1，尚无稳定加速或可替换默认的证据。

Yandex五L ΔRecall为−0.1318/0/+0.0049/−0.0928/−0.0342 pp；中位QPS−0.547/−0.645/+0.273/−0.719/−0.103%，五个交叉范围均含零。共同区间插值−1.067/−0.470/+0.329%，质量混合且多数点负，无双集新前沿。L128净命中不变但零命中减1，仍需与其它L损伤并列。

配对表gain_hits/loss_hits按逐query净命中变化的正部/负部累计；实际GT10成员集合增损另存[member_deltas.csv](../entry_method_exploration/20260913_until2100_v1/stage6_development_wall_v1/results/member_deltas.csv)，35组独立mask核验通过。Web L128两种定义为33/28与50/45，Y为26/26与34/34，净值分别+5/0一致。

## 失败query

WebVid9个源query产生13次zero-hit转换L事件，Yandex5个源query产生11次，合计14独立query/24事件。Yandex row3846在全部五L从10变0，只替换三入口的一个成员；L到800仍未恢复是已测范围，不能外推所有预算失败。row2441在前三个L从0救回到10。WebVid4063在L64/128从10变0，3434在L256/400/800从1变0。图表保留完整70组baseline→new命中、源命名空间、固定入口，事后案例不能当学习到的难query规则。

## 实现与成本

复制E34同SHA无hook evaluator，原评分/图完整字节加载。CPU15实际进程/OMP/BLAS/MKL1，子进程exec前绑核；一次完整warmup和五轮按dataset/repeat/L轮换，每次一个被测方法，无并发训练/标签/独立评分。整批wall含路由/映射/原NSG/output，GT/count/hash/JSON/load/build在外。完整wall与计数、离线操作时间分账；route-only/graph-only未额外单测，以null记录原因。

新增645840 NSG、501760 HNSW；35物理图加载/复制、70 plain/count加载，0新图构建/梯度/GT。两native job操作905.745秒含加载/计数/IO；独立92160集合/mask评分、720原kernelparity、225轮QPS恒等/顺序、五L图/入口、8192行E64 L128原结果bytes恢复均通过。全部native返回后分析，所有图已查看。绘图文字/对比度修正只涉及未封存派生图，0额外查询。

[完整报告](../entry_method_exploration/20260913_until2100_v1/stage6_development_wall_v1/report.md) · [协议](../entry_method_exploration/20260913_until2100_v1/stage6_development_wall_v1/protocol.md) · [45原值](../entry_method_exploration/20260913_until2100_v1/stage6_development_wall_v1/results/points.csv) · [225wall](../entry_method_exploration/20260913_until2100_v1/stage6_development_wall_v1/results/timings.csv) · [配对增损](../entry_method_exploration/20260913_until2100_v1/stage6_development_wall_v1/results/paired.csv) · [失败query汇总](../entry_method_exploration/20260913_until2100_v1/stage6_development_wall_v1/results/failure_query_summary.csv) · [QPS–Recall](../entry_method_exploration/20260913_until2100_v1/stage6_development_wall_v1/figures/recall_qps.svg) · [失败query图](../entry_method_exploration/20260913_until2100_v1/stage6_development_wall_v1/figures/failure_query_cases.svg) · [验收](../entry_method_exploration/20260913_until2100_v1/stage6_development_wall_v1/reviews/verification.json)。
