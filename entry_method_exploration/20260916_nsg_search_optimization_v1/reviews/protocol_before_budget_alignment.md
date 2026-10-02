# E99 NSG搜索实现优化

用户授权优化现有实现，选择先重点验证WebVid Recall@1/100、其他四集一致性回归，并要求修改前Git备份。备份已完成：2739b09a67f3ca0b6f145d43690d36345df3182c，branch backup/pre-nsg-optimization-20260916_103846；6115文件逐字节回读一致，main与原暂存区不变。E97/E98原产物、底库/图/模型/GT和旧静态库保持只读。

实现固定两个改动：1) search_on_graph_new每query从当前DistanceComputer（可解包NegativeDistanceComputer）提取FlatCodes存储地址，下一邻居lookahead=1预取visited与code首缓存线；无法取得存储的自定义DistanceComputer仅预取visited。不使用全局raw-base指针，不修改Faiss距离运算或ACSG对象布局/API。2) 保持原候选插入位置和等距规则，仅减少未满池的无效尾部复制；遇到非有限/FLT_MAX距离退出该query的压缩复制，以保留旧行为。

先做原kernel与新kernel的合成完整路径回归：IP/L2、重复/等距向量、单节点/不连通/自环/重复邻居/无效邻居、1/3/重复/空入口、三入口模式、K1/100、局部/复用候选缓冲、visited轮回与trace输出；核对返回bits、距离调用顺序和trace字段。另枚举有限候选池与E98短池控制的等距反例。生产代码通过后固定，不依测试query选择参数。

性能仅WebVid完整10000公开query、原五方法，所有NSG方法共享同一优化；预先固定K1/L100与800，K100/L100与1250。旧/新kernel在同一进程相同已加载图/模型中按轮次交替，warmup+3轮plain，完整包含路由与搜索；HNSW在同进程作不变参考。每点独立count核对E97的ID/距离bits/入口与逐query route/graph NDC。旧kernel编译为独立命名空间且使用同一内存中的图和storage，避免进程/加载差异。

Yandex、Deep、SIFT、GIST在原全部公开测试query、四种NSG入口方法、K1/100与L100/1250上各一次count一致性回归，直接对齐E97；不声明其新QPS。无LAION、无Recall@10、无新训练/图/GT/超参数网格。严格CPU15/进程和库线程1，方法串行；编译与后处理不与查询计时并发。

搜索调用上限2600000（Web 4点×9方法版本×5遍×10000=1800000，其余四集31000 query×16组合=496000；小型合成测试普通与ASan/UBSan各一轮，另计且合计<=20000次）。RSS<64GiB，新磁盘<1GiB。最终交付可独立链接的优化库/评测程序、源码diff、全量一致性与Web实测、图、Git恢复点和四份根文档；不把诊断时E98的+13.15%直接当成正式实现收益。

计数包装器在E99显式暴露被包装FlatCodes的只读codes/stride，仍用同一个原距离函数计分，使其余四集的count回归也实际经过向量预取分支；计数运行不当作QPS。
