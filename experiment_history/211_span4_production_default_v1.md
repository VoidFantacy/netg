# E211 GT10 正式入口 A/B 与默认切换

2026-11-20 完成 E211 并切换默认。标准 Flat raw-IP 的 `ACSG::search_new(mode=2)` 默认走 SPAN4，L2 等其他距离路径走标量。四个真实数据集各3,072条，真实K1/K100各7个L，224点、448个完整CPU15单线程批次。112个新旧配对返回逐字节相同，112/112个配对通过逐点速度筛选。纯GT10完整QPS变化+13.74%至+28.35%，GT10+B32变化+13.16%至+27.94%。

两臂调用同一个正式 `ACSG::search_new` 和相同路由、图及表。候选版在线读取每次展开的邻接跨度并以原 Faiss 计算至多四路距离，按原序进行候选竞争。显式回退调用 `acsg.set_flat_ip_batch4_enabled(false)`，查询开始前设定。

预先固定 4 数据集、2 真 K、7 L、4 臂、2 遍。全部实测输出及 E210 对应输出一致。候选池和 visited 3,584 次配对，B32 独立归并 172,032 次。112/112 点通过逐点速度筛选。通过阈值后把源码的默认值设为 true，另编译发布库及常规 bench 程序。四个 raw-IP 数据集、三个 L2 数据集和 1,200 次共享索引并发都核验了发布路径。

[正式报告](../entry_method_exploration/20261120_span4_production_default_v1/report.md) · [预锁协议](../entry_method_exploration/20261120_span4_production_default_v1/protocol.md) · [产物和来源封存](../entry_method_exploration/20261120_span4_production_default_v1/seal.json) · [前置研究 E210](210_span4_four_dataset_retest_v1.md)
