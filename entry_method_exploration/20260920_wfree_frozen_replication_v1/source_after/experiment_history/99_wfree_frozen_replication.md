# 99｜E105 冻结 WFree 独立复验

2026-09-20，用户“试试”授权后执行，状态 **STOP_WFREE_REPLICATION**。E104的静态WFree在每集512条历史cal上有局部正值，本轮冻结原模型/小图后，用各4096条新源行query和完整单线程Recall–QPS检验其可迁移性。两集的L128质量门与完整wall门均失败，停止本版继续投入；WebVid GT10-soft-t1 / Yandex GT10-hard默认及生产E99保持。E103仍是最新完整五集比较。

## 固定方法与独立输入

候选复用E104已导出的不逐行归一化W及原物理HNSW；GT10复用E97对应默认P/图。固定真实H815/821、M16、efConstruction200、ef10、真实入口ID升序、原raw-IP底库/NSG。两者使用逐字E103/E104 span+batch4。GT10原raw-query路由，WFree保持E104单位化query路由、原query进入NSG，单位化费用纳入在线wall。本轮比较完整冻结流程，不将差异单独归因于W或范数；0重训、0新构图。

在模型/协议冻结后，WebVid从原训练query源245万行起、Yandex从官方learn源200万行起各扫描预锁2万行窗口，选首4096条有效且唯一query。排除所有已登记aco/router/validation/public四分区逐行字节重复；Web跳过91条重复，Yandex为0。Yandex HTTP Range的源header、旧本地prefix、206范围和远端身份核验通过。query在新GT和搜索前封存；没有按GT或效果筛选。

源窗口不是全源随机抽样；字节互斥不证明语义独立，也不证明全部未登记历史曝光均已排除。本轮8192条query现已用于复验，后续不能改名作为未曝光测试。新GT100基于原完整base/raw-IP生成；两base完整SHA与原manifest一致，另16条float64全库top100集合全部一致。大NSG核验使用前后size/mtime、加载合同及输出恢复，没有新做完整图SHA。

## 实际结果

L128相对匹配GT10，Recall变化单位为百分点，失败定义为对应K的零命中query数：

| 数据集 | K | GT10 Recall | WFree Recall | ΔRecall/pp | ΔQPS | 零命中 GT10→WFree | 救回/新增失败 |
|---|---:|---:|---:|---:|---:|---:|---:|
| WebVid | 1 | 75.3174% | 75.2930% | −0.0244 | −5.90% | 1011→1012 | 125/126 |
| WebVid | 100 | 65.5408% | 65.4895% | −0.0513 | −5.76% | 5→5 | 2/2 |
| Yandex | 1 | 90.6250% | 90.6250% | 0.0000 | −3.27% | 384→384 | 63/63 |
| Yandex | 100 | 83.7917% | 83.4541% | −0.3376 | −3.40% | 24→34 | 8/18 |

四项配对bootstrap的98.75%校正区间均跨0，因此没有通过稳定正增益门，也不宣称已证明普遍损伤。Web/Y主图NDC分别增加约4.10%/1.64%；入口集合相同的query仅31/104条，但大范围改入口未转化为净质量收益。Yandex K100两半Recall变化均为负，零命中新损伤18条多于救回8条。

完整测试各K16预算、128方法配置、每点三轮plain。90/95/99%预设门槛按最快实测可达L比较，7个共同可达组合的WFree平均QPS全部更低：Web K1/K100的90%为−1.13%/−0.53%；Yandex K1的90/95/99%为−3.27%/−2.09%/−1.11%，K100的90/95%为−1.80%/−1.43%。其它5组合双方均未达到，不插值或外推。

部分高预算点有局部Recall正值，完整同L范围保留在报告；不能把主门失败描述成所有点质量均差。质量门要求每集两K均值不退化、至少一K增益≥0.5pp且至少一项校正区间下界>0；wall门要求每集至少一共同门槛提升≥3%且三轮同向，其余不低于−3%。两集两门均未通过。

## 验收与成本

历史fit恢复384次NSG，E104返回ID/距离bits/入口/路由及主图NDC一致。正式2,621,440次NSG，共2,621,824次NSG及同量小图路由；warm/plain/count逐位一致，独立集合评分和float64距离抽查通过。384轮完整wall来自同一boot、CPU15、进程及数值库单线程，方法串行；计时包含单位化/路由/映射/NSG/输出，不含加载、GT评分、count及写盘。

新精确GT约5.13分钟，正式搜索子进程含加载/count/I/O合计63.79分钟；搜索峰值RSS约9.92GiB，GT约17.31GiB。0新训练/大小图构建/K10搜索。E104训练/监督与原base/GT10/图为继承成本，不能记作从零成本为零。旧模型/图/源码及所有负结果保留，新源码/输入/结果独立封存，原始生成报告与根文档修改前快照保留。

## 停止与接续边界

E104查询MLP失败后，辅助WFree的局部正信号也未通过这次独立复验。本版按预锁协议停止，不追加seed、epochs、归一化、L网格或失败query子集；没有待恢复runner。此结果不否定全部离线学习、MLP或RL，也不证明CCF B所需的创新贡献。若继续方法研究，须提出有别于已有静态画像调参的实质假设，说明监督如何对应真实三入口联合效用以及为何能跨query保留净收益；先完成只读研究设计，不自动启动新训练/评测。

证据：[完整报告与曲线](../entry_method_exploration/20260920_wfree_frozen_replication_v1/report.md) · [预锁协议](../entry_method_exploration/20260920_wfree_frozen_replication_v1/protocol.md) · [判定](../entry_method_exploration/20260920_wfree_frozen_replication_v1/reviews/decision.json) · [128点指标](../entry_method_exploration/20260920_wfree_frozen_replication_v1/results/metrics.csv) · [384轮wall](../entry_method_exploration/20260920_wfree_frozen_replication_v1/results/wall_rounds.csv) · [失败query](../entry_method_exploration/20260920_wfree_frozen_replication_v1/results/failure_queries.csv) · [数值核验](../entry_method_exploration/20260920_wfree_frozen_replication_v1/reviews/numeric_verification.json) · [成本](../entry_method_exploration/20260920_wfree_frozen_replication_v1/reviews/cost.json)。
