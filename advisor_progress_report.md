# 给师父和师兄的近期方法进展与改进方向讨论稿

## 1. 这阶段的结论

当前方法是 **QGT-Cover + closed-form GT-basin prototype**：用历史查询构造候选入口和入口
原型向量（prototype），再通过小型索引为新查询选择入口，最后搜索冻结 NSG。它替代了原来的
`ACO → DPC → label generation → Neural Router` 流程，在 WebVid、Yandex 和 LAION 上已验证
有效且更轻量。

当前首要问题不是继续补工程实验，而是将候选构造、入口表示和在线路由统一到一个明确的目标与
核心机制下，使方法具有更清楚的论文层次。

## 2. 当前 Fast 方法的核心流程

### 2.1 输入与实验边界

底层是已经构建好的冻结 NSG。方法只学习或构造入口层，不增删、重连 NSG 的边。训练数据被
物理划分为两部分，避免同一批查询同时决定候选和候选表示：

- `QGT-train`：5K 独立训练查询及其 exact top-100 GT，用于构造候选入口；
- `prototype-train`：30K 另一组独立训练查询及其 top-1 GT，用于构造入口 prototype；
- validation/held-out：只用于按冻结协议评估，不参与入口构造。

这里的 QGT 是项目内定义的 **Query Ground-Truth**。QGT-Cover 也是项目内的启发式名称，
不能写成已有的标准算法或严格 set cover，因为当前版本没有覆盖率或近似最优保证。

### 2.2 第一层：QGT-Cover 候选入口

目标是从数百万或千万 base nodes 中选出约八百个真实节点作为可用入口，同时让这些入口覆盖
历史 OOD 查询分布，而不是只围绕 base 分布的中心。

具体过程是：

1. 对 5K 个归一化 QGT-train 查询做 spherical k-means，得到若干查询簇；
2. 每个查询簇都有一批成员查询及其 exact top-100 base GT；
3. 从这些真实 GT 节点中，为每个簇选一个尚未被其他簇占用的代表节点；
4. 最终得到一组去重后的真实 base IDs，作为 QGT hubs。

这一步相比 base-side k-means 的关键变化是：候选位置由历史查询及其真实目标区域决定，因此更
贴近 cross-modal/OOD query 实际要访问的区域。选出的又是真实 base node，可以直接作为冻结
NSG 的搜索入口，不需要往底图加入虚拟点。

它目前的局限也很明确：spherical k-means 只优化查询几何紧致性，GT node 去重也只是工程规则，
两者都没有直接优化“从该节点进入冻结图后能获得多少 Recall、花费多少 NDC、是否改善 tail”。

### 2.3 第二层：构造入口原型向量（prototype）

原始 hub 向量只说明入口节点本身位于哪里，不一定能表示“什么查询适合从这里开始搜索”。因此
第二层用独立的 30K prototype-train 查询，为每个 hub 构造 query-side 表示。

具体过程是：

1. 取每个训练查询的 top-1 GT base vector；
2. 按 raw hub 空间，将该 GT vector 分配给最近的 QGT hub，形成一个经验 GT basin；
3. 聚合落入同一 basin 的训练查询，对归一化 query 求均值；
4. 将 query 均值与该 hub 的原始向量先验做闭式融合并归一化，得到该 hub 的 prototype。

prototype 可以理解为每个入口的一张“查询画像”。它不是入口节点自身的复制向量，而是把过去
真实目标落在该入口负责区域的查询聚合起来，用一个向量概括“什么样的查询适合从这个入口开始
搜索”。新查询与某个 prototype 越相似，就表示它越像该入口过去服务过的查询。整个构造过程
只是求均值、融合入口自身的向量先验并归一化，没有反向传播、epoch 或神经网络训练。

这一步比直接使用 raw hub 更接近 query distribution，但仍然主要是几何表示：它没有直接观察
同一 query 从不同 entry 出发时的真实搜索效用，所以 prototype 相似度不等价于 entry utility。

### 2.4 第三层：在线路由与冻结图搜索

在线阶段只做两步：

1. 在约八百个 prototypes 上建立很小的 Micro-HNSW，新查询先检索 top-3 prototypes；
2. 将它们映射回三个真实 hub IDs，并以这三个入口搜索原来的冻结 NSG。

这个设计将在线路由限制在很小的索引中，避免对全部 hubs 运行复杂模型。Fast 的“快”主要来自
入口层构造和路由都很轻，而不是底层图搜索被替换。

需要特别说明成本口径：现有分钟级数字表示 **exact train GT 已经存在之后** 的入口层构建，
不能称为完整训练时间。论文中应报告：

`T_exact-GT + T_QGT-clustering + T_prototype + T_Micro-HNSW`，并区分冷/热页缓存。

### 2.5 相对原方法究竟改进了什么

| 环节 | 原方法 | 当前 Fast v1 | 实际意义 |
| --- | --- | --- | --- |
| 候选入口 | ACO、DPC 等多阶段生成 | QGT-Cover 直接选真实 GT nodes | 流程更短，入口与 query distribution 对齐 |
| 监督生成 | 对 query×entry 做 probe 并生成标签 | 两组独立 query 的 exact GT | 去掉大规模逐入口 label 流程，但仍有 GT 成本 |
| 入口表示 | Neural Router/learned representation | query 均值与 hub prior 的闭式 prototype | 无 optimizer/MLP，构建稳定且轻量 |
| 在线决策 | 神经路由器选择入口 | Micro-HNSW prototype top-3 | 容易部署到已有冻结索引 |
| 底图 | 冻结 NSG | 冻结 NSG | 改善可归因于入口层，不依赖改图 |

## 3. 目前研究方向

### 3.1 旧 NETG 已经使用 graph reachability

旧 NETG 并不是纯几何方法。它对每个真实训练查询，从所有候选 hubs 分别运行一次冻结图搜索，
检查能否找到该查询的 top-1 GT，并选择成功到达 GT 且 NDC 最小的 hub 作为训练标签。因此它的
监督已经同时包含 query 信息和真实 graph reachability。

这一步成本很高。以 WebVid 为例，30K 个训练查询和约 815 个 hubs 对应约 2445 万次
query–hub probe；仅标签生成约 46 分钟，ACO、DPC、标签生成和 Neural Router 四个阶段合计约
108 分钟，而且还不包含 exact train GT 的准备成本。更重要的是，大量 probe 的结果最后只被
压缩成一个 `best_hub_id` 和一个 `min_ndc`，其他入口的 Recall、成本和不同预算下的表现都没有
保留下来。

当前 Fast 为了降低成本，去掉了逐 query×hub probe 和 Neural Router，改用 prototype 几何
相似度选择入口。现在考虑的是：**如何在不恢复旧 NETG 全量穷举成本的前提下，把真实图搜索
效用重新加入当前 Fast。** 具体应使用少量有信息的候选入口构造稀疏、连续的 query–entry
utility，而不是重新生成单一 best-hub hard label。因此这里不是第一次引入 graph reachability，
而是研究如何更低成本、更完整地利用旧 NETG 已经证明有价值的搜索监督。

### 3.2 当前方向：低成本 Search-Utility Atlas

当前方向是保留 Fast 的低成本候选入口和 prototype 路由，同时用少量真实 query–entry 图搜索，
重新引入旧 NETG 中有效但昂贵的 graph reachability。对查询 `q`、入口 `e` 和搜索预算 `L`，
记录与最终检索目标一致的连续效用：

`u(q,e;L) = Recall gain - λ · NDC increase`

具体流程是：

1. 用当前 Fast 的 prototype 相似度，为每个训练查询召回少量候选入口，而不是遍历全部 hubs；
2. 只对这些候选运行真实冻结图搜索，保存各入口在不同预算下的 Recall 和 NDC，形成稀疏的
   query–entry search-utility atlas；
3. 根据这张稀疏图谱构造轻量的 utility estimator，使新查询在不执行在线 probe 的情况下，能够
   预测不同入口的真实搜索收益；
4. 在线在固定预算内选择预测 utility 最高的入口，再搜索原冻结图。

这样既保留了当前 Fast 的低构建和部署成本，也重新利用了旧 NETG 的真实图搜索监督；区别在于
不再做 `30K × 全部 hubs` 的穷举，也不再把结果压缩成单一 hard label。此前尝试用静态 basin
转移近似 graph reachability 的 BTG v1 已经验证失败，不再作为当前方法继续扩展。现在最核心的
问题是：少量候选上的稀疏 utility，是否足以预测新查询的入口搜索效用。
