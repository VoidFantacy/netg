# 路由工作恒等式核验：预定协议

2026-09-20，继E115四格停止之后的机制审查，不是新候选。问题：较低的静态出度是否对应实际搜索中较少的距离计算；不能由静态度直接推出路径变短。

范围锁定E115全部四格、两集各4096条曝光query，原ef10/top3/raw-IP/W/图/ID。只加载路由小图与query，读取E115缓存入口和路由NDC作恢复；不加载大图、GT或训练标签。0真实NSG、0新图/GT/训练/正式QPS。每query原版搜索一次、观察版一次，总ANN65536；不换seed/ef/层级或选query。CPU15，线程1，串行两集；单任务120秒上限，18:50后禁止新搜索。

依据冻结hnswlib源代码，原searchKnn自带metric_hops/metric_distance_computations只记上层（base模板collect_metrics默认false）。观察版逐字提取该函数，只改名并把两个base模板分支的collect_metrics置true；距离函数仍用同一内积计数器。所有逻辑、队列、比较顺序与输出保持。对每query核验原/观察版返回标签、距离bits、总NDC，并恢复E115缓存入口/NDC。

无删除/过滤，初始上层入口与base起点各计算一次，得到精确记账式：

`NDC = 2 + upper_neighbor_scans + base_first_visit_distances`。

`base_neighbor_scans = base_first_visit_distances + base_visited_skips`。

观察版减原版的hops为base展开行数，减scan为base邻接扫描数。此处base_first_visit不表示整个分层搜索全局首次，上层可以重复打分，base另有visited。逐query验证各项非负、整数恒等式、base唯一访问数不超过H−1。

完整32768行保存，不筛选结果。汇总四格全部均值及GP/GU条件差值，分清扫描/距离/展开；它是成本核算，不把均值差分宣称为纯出度的因果贡献，不推出完整wall、Recall或同HNSW构图条件的一般定理。原GP/GU层级差异继续披露。无性能通过门，无后续训练队列；若parity失败，停止并保留错误，不用不一致结果解释机制。
