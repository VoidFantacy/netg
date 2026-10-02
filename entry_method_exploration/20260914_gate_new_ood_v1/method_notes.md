# E96 方法解释与结果边界

- NSG、GT10、GATE使用同一数据集的同一原生NSG底图及原`search_new`，分别注入固定单入口、画像HNSW3入口、GATE HNSW3入口。NSG含既有构建期连接性处理。全量HNSW为独立完整base索引。
- 我们的方法是GT10：真实QGT hub选择 → fit20K的GT10归属权重累计单位query形成单位画像 → 画像Micro-HNSW M16/efC200/ef10/top3，映射真实ID并升序。Web复用soft-t1，Y复用hard；LAION仅在cal1024、L128按冻结规则在hard/soft-t1二选一，测试前冻结。不是直接对约800个原始数据点做路由。
- GATE为明确的CPU/IP适配，512个两层32×16 HBKM真实hub、固定5近+5远/最多5hop与1000节点的release10子图和拓扑Graph2Vec，原NSG L64/K1首次发现路径hop标签；返回GT1才有效。作者release每query最小hop为正、尾部hop为负并按规则过滤；训练fit10K、监控1024，Adam/余弦triplet/max200/patience20。网络按release FF2048，纠正batch/sequence维度。每batch同hub共享前向是CPU优化，也共享了dropout样本；这一点与逐triplet独立dropout并不逐位等价。没有query神经塔。线上只加载静态单位embedding，通过归一化query+IP实现cosine路由，M256/efC256/ef10/seed100/top3按堆弹出顺序映射入口，全部路由成本计入wall。不能冒称论文逐位复现。
- 旧本地GATE标签把扩展节点数作为hop。E96独立observer修正为首次发现路径长度并与当前原kernel做返回位一致性校验；旧模型与旧结果保留历史身份，不复用作本轮训练结果。
- 完整HNSW M32/efC200/seed20260828，离线最多16线程并行插入，保存实际有序拓扑，构建RNG互斥修正不改搜索函数。完整向量从base逐位恢复，未量化，未采样base。恢复/序列化在计时外，运行时完整索引在内存中。
- 图和模型各固定构建/训练一次，三次指每个查询性能点的完整wall重复。L与HNSW efSearch不是同工作量，结论依据实测Recall–QPS曲线；同L失败配对仅解释该预算下的查询变化。计时三次也不是三个独立训练seed。
- Web与LAION公开测试query同源；public测试已有项目历史曝光，不称三套全新盲测分布。最终测试不参与本轮checkpoint/画像选择。GATE和GT10训练量及离线成本不同，报告实际量，不把继承的GT/NSG/画像成本写成零。
- 失败查询指top10与GT top10零交集。另给真实第1邻居不在返回top10中的比例。Recall的query bootstrap和失败率Wilson区间仅作查询样本的不确定性描述；QPS阴影是三次实测极值范围。
- 环境重启造成的在途离线工作成本可能未完整捕获；已提交阶段、标签分片、训练历史和恢复点的成本与结果分别保留。正式点按完整L块提交；中断L块归档后重测，记录boot_id。当前默认不会因准备或一项监控指标被替换。

来源：[GATE release](https://github.com/jacksondca/gate/tree/229f18dadb791ddede22597e44d5ceb028b104ba)、[GATE论文](https://arxiv.org/abs/2506.15986)、本目录protocol/参数修正/config、源码和各dataset manifest。
