# 114｜路由工作量、净收益与理论归属

2026-09-20。E115质量门停止之后，只核对小图成本发生在哪里；没有新候选。

固定四格原参数，全部8192曝光query，原/观察版各一次，共65536 ANN、0NSG/GT读取或生成/训练/新图/正式QPS。观察版仅将hnswlib base模板的collect_metrics打开，32768对返回标签、距离bits、总NDC一致并恢复E115。原计数器只含上层，差分得到base扫描/展开；依源码恒等式派生首次访问与visited跳过，另从CSV验证覆盖和均值。

固定U评分，GU→GP在Yandex的base展开11.546→12.735，base邻边扫描241.854→160.630，NDC215.711→129.309；Web相同方向。省距离不是展开更少，主要是处理更少邻边/新节点；路径、层级和静态度仍共同作用，不能直接据此继续删边。编译5.070秒，路由进程0.565秒，RSS23.031MiB，两个进程已结束。

只读解释补充：E105的三入口改变比例97%以上，但K1救回/损伤125/126与63/63，且完整QPS下降；尚缺能预测净收益的机制。配对区间跨0不证明真值恰为0，不自动追加query或调参。

一手文献补充：NGFix的Escape Hardness与E111排名核心可达保证直接相关，不得称首次提出新理论；本地范围限固定原图/kernel/GT的条件和覆盖核验。SHEAF的返回差界不保证正确，论文两浅探针预测相关性不是本地完整QPS。任意有向图上容量1仍可展开n节点的基础反例说明，池容量本身不推出工作量仅随L增长；没有声称该例由NSG构图产生。

默认Web soft/Yandex hard及生产E99保持。未重开E111/E112/E113/E115停止版本。19:00综合报告继续收尾。

[路由报告与原始证据](../entry_method_exploration/20260920_until1900_theory_v1/research/router_work_identity_v1/report.md) · [净收益解释](../entry_method_exploration/20260920_until1900_theory_v1/research/net_gain_and_uncertainty.md) · [前作与范围](../entry_method_exploration/20260920_until1900_theory_v1/research/certificate_prior_work_addendum.md)。
