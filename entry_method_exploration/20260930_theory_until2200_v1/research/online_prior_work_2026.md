# 在线入口信息：2026年前作补查

2026-09-30 18:30。只读文献与历史核对，不启动新模型或搜索。当前状态/rank实验的源、协议、模型和选择规则均不受本页影响。

## 与查询结果复用直接重合的工作

[CatapultDB，arXiv:2603.02164v1](https://arxiv.org/html/2603.02164v1)的§3、Algorithm 2将随机超平面哈希桶中的历史最佳返回ID与medoid合成入口，再执行原搜索并更新LRU桶。它是附加入口层，不应仅因文中称shortcut edges就误判为必须改底图。典型参数为8位、每桶40个ID。作者报告的最高2.51倍吞吐属于其工作负载与DiskANN实验，不是本地结果，也不能搬作GT10的预期收益。这里已阅读正文机制、性质和工作负载说明；按作者主页暂列预印本，不自行升级发表状态。

**本项目的分析**：§3.2“Competitive recall”将可导航性、保留medoid与不损召回联系起来，缺少对当前有限候选池执行的对应证明。项目145的原生反例已说明加入口会改变池竞争和展开次序；保留原入口不能当逐查询非降证书。这一限制不推翻该论文的实测收益，但其文字论证不能用来免除我们对损伤的测量。现有证据无需为此重复跑合成反例。

[Adaptive Query-Aware Hybrid Search，EDBT 2026](https://openproceedings.org/2026/conf/edbt/paper-253.pdf)的§2–3用按属性组织的BST检索历史查询，并将历史返回用于入口；还包含召回预测和过滤查询的高阶遍历。Algorithm 1明确使用实际召回更新状态，§3.3区分了训练与推理特征。已核对这些机制段落，现已补读§4实验与消融；作者报告每次搜索40线程。§4.2.3也报告BST随历史增大可比原层间贪心遍历更慢。仍不能据此断言完整wall包含生成实际召回标签的费用。它使“用历史查询找入口”成为明确前作重合项。

[Rethinking Multiple-Query Optimization for Approximate Nearest Neighbor Search](https://openreview.net/pdf?id=rZyQVls8TD)检索可见摘要及§3.1采用查询MST，子查询从父查询实际ANN结果开始。完整PDF未成功获取；检索页仍标under review，作者CV标preprint，发表状态未确认。它改变批处理依赖和查询顺序；我们的逐查询入口实验不能省略排序、建树与结果复用成本后直接引用其收益。

## 容易误当成新入口方法的邻近工作

[AlayaLaser，arXiv:2602.23342v1](https://arxiv.org/html/2602.23342v1)的§4.1已经用base聚类候选及在线顺序距离扫描选择入口；主系统还改变量化布局、beam与I/O执行，§3.2明确把OOD处理留给后继。该系统的全局吞吐结果不能归因于入口单项，也不能外推为当前raw-IP、固定主核的单线程收益。已阅读机制、设置与适用范围，未复现作者系统。

## 内部历史核对与仍未回答的问题

记录01的Fast将训练查询按GT目标映射到固定H，再压缩成画像；记录124/125的TargetKNN则用相近查询投票选择七个既有策略。记录73是在画像小图上依据训练查询排名缺口加边。它们都不是“检索一条独立训练query，直接把它的GT目标ID作为新入口”的相同实现；但区别本身不代表新颖性、信息更强或性能更好。必须继续检查原源码与数据角色，不能仅凭概览宣布从未做过。

直接查询—目标对应需要回答：解除固定H或画像均值的压缩后，传递来的目标能否在目标L下改善真实搜索，且足以支付检索查询实例的完整费用。[165静态迁移验证](query_target_transfer_v1/report.md)现已完成：Web相对配对置换有局部质量信息，主候选仍未形成相对默认的综合收益；目标侧控制的Web R1取舍单独保留。源、图和统计均保持冻结身份。训练库与评价查询按来源及内容去重，评价GT不参与路由。

## 作者源码补查（2026-09-30 18:58）

固定检查[commit e6dfc9a](https://github.com/AdeelAslamSoton/QueryAwareIndexing/tree/e6dfc9a34698e036f11b9baf2a73b6ba0f4c9909)，未编译或运行作者实验。点查询driver先加载GT与distance/selectivity，过滤位图准备也在batch计时前；timer包含search中的GT集合比对与回归更新，但不含GT生成。当前driver使用1线程、ef560、预测分数常数0；search中召回加分被注释，并将返回目标向量放入BST。因此当前HEAD像消融版本，不能视作论文40线程主配置或用它断言论文结果错误。这里确认的是代码/论文口径不能不加核对地拼接。

来源：[driver](https://github.com/AdeelAslamSoton/QueryAwareIndexing/blob/e6dfc9a34698e036f11b9baf2a73b6ba0f4c9909/hnswlib/examples/cpp/example_query_aware_point.cpp#L350)、[search及GT更新](https://github.com/AdeelAslamSoton/QueryAwareIndexing/blob/e6dfc9a34698e036f11b9baf2a73b6ba0f4c9909/hnswlib/query_aware_hnsw/query_aware_hnswlib.h#L194)。对本项目的要求是训练标签与评价角色明确、评价GT只作后验评分、报告完整路由wall；不因外部论文声称便宜而省略这些项。

## 收敛定理能否补上入口到QPS的缺环

[Fast-Convergent Proximity Graphs，camera-ready v5](https://arxiv.org/html/2510.05975v5)的§3.1–3.3已核对HTML与PDF。其性质依赖度量三角不等式、全数据候选剪枝、特定新图及query到NN的距离条件；准确形式是“直接连到NN，或下一步按α收缩”。v2缺少前一分支的文字已在v5修正，应引用最新版（PDF Lemma 2与HTML Lemma 4编号不同）。局部候选的实用α-CNG另作经验评估，不能直接继承全候选定理。

这给当前推导的启发是明确列出连接条件，而非引用一个log复杂度当作现有NSG费用界：本项目使用raw-IP比较，没有证明所需的度量/全候选剪枝合同；即便另外做保持query排序的L2嵌入，也不能因此使既有NSG自动满足新图性质。K100有限pool还要处理多个候选。即使另行假设某条路径有收缩，也只能得到步数上界，不能将两个上界相减证明实际节省或完整wall收益。

19:26补读§4–5：实用图采用局部候选和degree cap；§4.4明确在test queries上选τ，§5.1的效率主指标为NDC和hops。其“speedup”不能直接转写为完整QPS倍数。本项目不照搬该调参口径，未运行或修改底图。

## 费用预测与主搜索控制的邻近前作

[ANNiE，PVLDB 19(11)，2026](https://www.vldb.org/pvldb/vol19/p3820-wang.pdf)的§4.1–4.6/Algorithm 5已核对。它先执行主图homing，再从近邻诱导子图提取聚类系数与多跳可达性，GBDT预测达到目标Recall的NDC；ANNiE-S改变搜索队列/停止条件。正文将分位数保证建立在期望损失全局最优等假设上，并明确有限模型与分布变化会使测试保证偏离；不能把实际训练一次直接称分布无关的逐query保证。

对本项目的含义：带真实搜索预算的图结构费用预测已有直接前作；把164的状态表加深或改为GBDT不构成新信息。ANNiE的局部信息来自已经付费的主搜索，不能拿来当入口选择前的免费输入。本文报告的特征计算费用与NDC减少也不是我们的完整QPS结果。其主搜索改动超出当前入口固定比较合同，本日不实现或运行；仅用来约束新颖性和“便宜信息”的定义。

## 从好入口开始仍须付出邻域搜索费用

[Dynamic Exploration Graph，arXiv:2307.10479v2 §6.7](https://arxiv.org/html/2307.10479v2#S6.SS7)已用索引内query本身作为入口，比较检索其邻域的Recall与QPS；图/搜索算法不变，查询角色和入口变化。该任务与普通未索引query的算法排序不同。这里已读§2.2、§4.1及§6.7，未复现其底图构建。

它支持区分“进入目标附近”和“收集足够近邻”这两个问题，不能推出我们K100瓶颈的具体占比。本文用K1000、索引内query和不同图，其数值不能与本地raw-IP K1/K100拼接。改变查询角色以获得完美入口只是诊断，不是免费的线上策略；本轮不据此新增oracle搜索。
