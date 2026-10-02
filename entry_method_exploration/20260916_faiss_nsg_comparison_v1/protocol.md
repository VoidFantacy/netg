# E101：原生 Faiss NSG 与项目搜索的同图比较

用户要求“比较一下，看看哪里值得优化”。在E100源码与结构诊断之后，新增同图原生库基线、最小多入口适配及预定实现控制，回答库替换是否更好、哪项开销值得继续投入。E99生产实现、模型和旧结果保持；修改前备份为dba6986eb9baa645e9ad1231f9d112bb06550c5d，main/index不变。

固定WebVid原2505000×512 IP base、项目冻结NSG图、原GT10-soft-t1路由器和完整10K public query/GT。原生Faiss IndexNSG包装直接借用同一storage和邻接内存，不训练、不构图、不修拓扑。Faiss的初始邻居+随机填满L语义保留，不要求与项目返回相同；它与项目图构建后的结果组合，命名为“Faiss-native on frozen project graph”，不能称重新构建的原生Faiss整套索引。

锁定四点：K1/L96、K100/L100、K1/L800、K100/L1250；仅Recall@1/100。十个版本：Faiss-native、NSG-current、GT10-current、GT10-minimal、GT10-core、GT10-span、GT10-prefetch-filter、GT10-batch4、GT10-span-batch4、完整HNSW。

- current实际链接E99优化库；NSG是固定单入口，GT10使用原三入口。
- minimal沿用Faiss候选排序/插入和遍历机制，只适配最多三入口、未满候选池与结果不足；不启用E99预取/有效前缀复制，不含项目trace/历史模式。
- core为同一独立小内核恢复E99预取与有效前缀复制，作为后面三个优化控制的匹配基线；另与current比较简化代码的影响。它不是原生库，不能冒称stock Faiss。
- span在core上使用每行最后有效邻接位置，保留内部空洞和有效边顺序；辅助信息一次在加载后产生、单独记录耗时和内存。
- prefetch-filter在core上仅过滤已经visited的向量预取，visited预取保持。
- batch4在core上按原邻接顺序聚合最多四个新邻居，调用Faiss distances_batch_4后依原顺序插入；聚合时预取各向量首cache line。span-batch4只组合预定的两项，不按结果选择组合。

每点每版本warmup一次、plain三次、count一次，共2000000次真实查询、120轮plain，上限2100000。另设合成图边界/等距/visited轮回差分回归；不按公开结果追加预算/方法/种子。实验版本若数值或NDC不一致，停止该候选的速度解读并保留失败；不修改算法来迎合公开结果。

plain包括真实路由、距离计算、图遍历和结果输出转换，GT/磁盘/加载外置。原生Faiss调用IndexNSG.search(完整batch)，内部线程锁为1；返回int64和IP符号转换到共同输出格式的成本也计入。它的count轮调用同一库NSG.search和真实距离包装，并核验与公开API返回一致；count不作QPS。其它控制须在每轮对齐E99全部ID、距离bits、入口，count逐query route/graph NDC一致；合成测试还核对距离调用顺序。所有返回按同一严格GT ID评分。

同机CPU15，进程及OMP/BLAS/MKL线程1，方法串行；每点按固定轮换顺序、第二次反转，避免一种方法总在最前。RSS上限64GiB，新增盘上限512MiB，不并发训练/构图/编译/其它性能测试。源码/配置/库及数据身份在启动前冻结并在结束核验；统计中保留三次范围，不把微小差异称稳定胜出。

交付四点Recall–QPS图、对照加速图、逐轮和逐query原始结果、有效工作与成本、原生库语义边界、有优先级的优化结论。四个点只能回答本轮范围；不声称完整前沿、五集速度或已部署。若建议正式落地，仍需共享NSG四方法公平更新和其它四集回归；本轮不自动重训或覆盖生产。
