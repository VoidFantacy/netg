# ACSG 下一阶段实验方向与新对话交接

2026-09-10。状态：`NEXT_EXPERIMENT_DIRECTION_DEFINED_UNRUN`。用户要求详细记录刚才讨论的全部实验方向及优先级，方便新对话执行。**第一优先是固定H的GT-topK软画像；第二优先是真实finite-L效用分组/挑入口；第三为成对拉伸Micro-HNSW的效率支线。** 聚类器替代、rank容量、三入口联合评分和raw-IP范数问题按各自依赖展开，见第4节。本次只完成文档交接；具体运行协议在新对话启动时冻结，没有新聚类、标注、训练、ANN构建或评测。

最近真实实验仍为E23：`EXPLORATORY_SMALL_RECALL_SIGNAL_NO_CLEAR_QPS_GAIN`，相对matched Fast20K有小幅Recall信号，没有明确整体QPS优势。Full固定目标优化更好，但Yandex五L Recall均不及rank8。实测见[summary.md](summary.md)和[E23复盘](experiment_history/12_three_entry_rank_exploration.md)。

## 1. 首轮要回答的问题

当前Fast先用独立5K query聚类，从代表query的GT100中选815/821个互异真实入口；随后将20K画像训练query按GT1到raw hub的cosine硬分组，计算`normalize(unit(hub)+Σ unit(query))`。第二步只看一个目标，可能丢失多目标信息，且画像支持不均衡。

首轮问题是：**不增加在线画像数量、入口数和评分模型复杂度，使用多个GT目标及软归属，能否改善真实三入口NSG搜索的Recall–QPS？** 现有H已有免费oracle空间，先固定H隔离画像归属作用。GT覆盖、静态度数和几何分数不能代替finite-beam真实收益。

依据：[四问题报告](entry_method_exploration/20260910_ood_hubs_clustering_router_research_v1/report.md)、[一手文献](entry_method_exploration/20260910_ood_hubs_clustering_router_research_v1/papers.md)、[既有本地证据](entry_method_exploration/20260910_ood_hubs_clustering_router_research_v1/local_evidence.json)。研究原件的`RESEARCH_COMPLETE_METHOD_UNSELECTED_UNRUN`保留当时身份；本文件记录随后要求的实验接续。

## 2. 优先实验：固定H的GT-topK软画像

### 建议默认范围

以下为新协议的建议范围，尚未执行；启动时核对当前源码和输入，再一次性锁定参数、调用预算与选择规则。

| 项目 | 建议范围 |
|---|---|
| 数据与图 | WebVid2.5M、official Yandex first10M/IP；保持原base、metric、预处理和冻结NSG |
| 真实入口 | QGT seed20260828的H815/821；不重新聚类、不增减或替换真实ID |
| 画像输入 | 与E23 matched Fast相同fit20K，即router_train原始行`[10000,30000)`，仅用fit GT构建 |
| 开发划分 | cal1024为原始行`[0,1024)`，audit1024为`[1024,2048)`；沿用身份，明确属于历史开发数据 |
| GT目标数 | 首轮建议`K_gt∈{1,10}`，与搜索评价的Recall@10分别命名 |
| 在线形式 | 一画像对应一个真实hub；raw query→Micro-HNSW direct3→原`search_new(mode=2)`，三个互异真实入口 |
| 路由对齐 | matched组共用M16/efConstruction200/ef10、seed20260828及真实ID升序消费；一份画像用于全部L |
| 评估范围 | 先开发集L128；冻结后建议沿用每数据集validation前2K、L64/128/256/400/800作探索。披露历史访问，不能称全新盲测；held-out不打开 |

### 画像定义和必要对照

令query的第t个exact raw-IP目标为`g_t(q)`，首轮继续使用当前目标–hub cosine：

`s_t,h = unit(base[g_t(q)]) · unit(raw_hub[h])`。

硬归属将每个GT目标交给一个最高分hub；软归属令`b_t,h = softmax_h(s_t,h / T)`。首轮建议GT名次等权：

`a(q,h) = (1/K_gt) Σ_t b_t,h`

`p_h = normalize(unit(raw_hub[h]) + Σ_q a(q,h) unit(q))`。

保持每条query总贡献为1、raw-hub prior权重为1，避免增加GT数时同时放大训练总权重。首轮保留cosine只为隔离GT数与软归属；**没有同时解决Yandex目标范数在归一化时被丢失的问题**。

| 画像 | 要隔离的作用 |
|---|---|
| GT1＋硬归属 | 恢复当前matched Fast20K P0，作为实现和改进主基线 |
| GT10＋硬归属 | 多目标投票 |
| GT1＋软归属 | 软分配 |
| GT10＋软归属 | 二者组合 |

温度使用小候选表，建议最多3个值，两种软画像共用同一表。具体值可参考fit目标–hub分数间隔，必须在任何cal搜索前写入protocol/config；只用cal选温度/候选，audit只报告冻结候选。允许Fast作为恢复项，但回退Fast不能冒充新方法提升。不同时增加GT名次权重、top-m截断、多prior、vMF、rank、MLP、拉伸或新的H。

实现要明确稳定softmax、硬归属ties、零向量/无支持回退和累加数值类型。软权重全非零不等于有效支持充分，应记录权重质量、有效样本量或集中程度。按query/GT批次处理，不驻留不必要的高维中间张量。

画像从已有fit exact GT闭式构建，**不需要重跑E22全H single标签或E23三入口训练标签，也不需要梯度训练**。开发与最终评估仍执行真实三入口搜索，其调用与训练标注成本分开。

## 3. 执行阶段、判断与产物

| 阶段 | 工作与产物 | 判断边界 |
|---|---|---|
| P0 身份和协议 | 读交接/源码/历史，创建独立版本，记录输入与源码hash；冻结温度、选择规则、评估范围、线程、计时次数和总调用预算 | 身份、split、GT列宽有疑点先查证，不从旧目录名推断，不覆盖旧artifact |
| P1 构建与恢复 | 先复现GT1硬归属P0，再构建其它对照；记录权重/支持、画像变化和构建时间 | 原P0数值及入口/原kernel输出恢复通过后再评价新方法；差异先修复 |
| P2 开发诊断 | 建议cal L128对预定候选做同画像exact3与HNSW3真实NSG搜索；按固定规则选择，再冻结并报告audit | 分开画像质量和近似检索损失。若所有候选cal均不优于Fast，保存完整失败表并收口，不扩网格追结果 |
| P3 端到端比较 | 冻结后在协议指定的小validation测五L、必要基线及预定消融 | 不按audit/validation换模型或删负点；报告完整Recall–QPS及失败query，小幅单次wall不作稳定加速结论 |

cal建议以HNSW实际三入口总hits为主，graph NDC及较简单配置作并列规则；exact3只解释机制，不事后在两套路由间挑结果。上述P2是小型首轮建议，实质阈值和并列规则须在cal前锁定，不沿用C或其它历史版本的门槛。audit是冻结候选的报告，不用于重新选择；一旦进入P3保留所有预定点。

P3基线至少包括NSG、原Fast30K-3、matched Fast20K-3和冻结新候选；GT10硬/GT1软等消融的展示行与总点数事前固定。原Fast30K保留seed100/heap顺序，另列输入与执行差异，方法改进主归因取matched Fast20K。E23 Full/rank8作历史参考，不为这次闭式画像消融自动重训或增加大基线队列。

正式查询及cal/audit对照统一单线程：`threads=1`、OMP/OpenBLAS/MKL=1并核验实际线程，一次只跑一个方法。QPS取独立整批plain wall，在线入口排序及全部路由工作在timer内；GT评分、NDC计数、hash、写盘在timer外。记录Recall@10、QPS、零命中/挽救/新增失败、route/graph/total NDC；exact GT、画像和微型图构建成本分列。

保存protocol/config、commands、state、逐query输出和检查，最终交付全部原值表、Recall–QPS图、成本账和报告，并同步四份主文档及历史。无新收益就收口该版本，不自动升级为正式性能GO。

## 4. 全部实验方向：优先级、方法、对照与进入条件

| 优先级 | 方向 | 进入条件和区别 |
|---|---|---|
| 1，当前主线 | 固定H的GT-topK软画像 | 隔离目标归属；与旧GT1 basin内增加两个mode、多seed多view、single赢家centroid不同 |
| 2，较重备选 | 以真实finite-L作用组织分组或在小GT候选集挑入口 | 若主线显示几何代理仍有缺口，再定协议；度数只作特征，三入口用真实联合搜索。旧centroid/rerouter已有真实效用，须说明新条件作用/可预测分组差别 |
| 3，效率支线 | 固定W，成对拉伸并重建Micro-HNSW | `p′=Ap,q′=A⁻ᵀq`，优先受限正对角A；先验评分一致，再看导航和总wall。不能变换后逐画像归一化；不重建边时保分数变换不会改变理想搜索路径 |

这个排序表示研究资源优先级，不要求每个方向都先取得正结果才能思考下一方向。第一方向失败也有信息价值：它可能提示需要真实搜索监督，而不是继续增加GT数。三个方向分别改善画像目标、真实入口作用、索引导航，应独立对照后再决定组合。下面的方案均未执行，也不构成一张自动全部跑完的实验队列。

### 4.1 第二优先：用真实搜索作用分组、挑入口，并考虑连通性

**问题与证据。** GT1答案近不等于作为入口能在有限beam中找到更多答案；现有H内也有明显遗漏效用。E20 L128单入口GT1-basin对全H免费oracle，WebVid为75.605%对85.957%，Yandex为91.758%对96.563%。这是选择空间，不能转成低成本可学习保证。因此先区分“现有H选得不对”和“H里缺好入口”。

**2A：先固定H，研究query应该由哪个入口服务。** 从与当前base/graph/query/H/L身份兼容的已有single结果中取得`R_L(q,h)`及实际graph NDC，作为离线诊断或候选提议；不能把single当三入口联合奖励。可比较GT10软归属与按真实收益接近程度构成的软归属，让一条query支持多个效果接近的入口，避免强迫噪声很大的唯一赢家。Recall和成本先分列；若构成标量效用，尺度与成本系数须在协议中固定，并最终由独立wall验证。

这个分支首先回答：真实效用分组能否被query画像表达、且在cal/audit上保留收益？对照至少包括当前Fast、第一方向冻结画像、旧single赢家硬centroid式参考和新的软/可预测分组。只有免费教师好、在线画像不好，应报告表示/可预测性缺口；不把教师上界作为方法点。旧E08已经做过single赢家重建centroid，不能把简单重聚合再次称新；需要明确软标签、分组约束或条件联合作用的区别。

**2B：如果确需改变真实入口，再做固定预算的GT候选选代表。** 候选可从独立QGT query各簇的GT-topK并集中产生，先保留原代表作为恢复项；由fit代表query在冻结NSG上的有限L搜索效果挑入口，而不是只用代表query的GT1或最高度数。候选池只能用构建/fit信息形成，cal/audit/validation不参与提议。候选规模、代表query数、每簇调用上限和全局H预算在新协议中锁定，不直接扩成整个base搜索。

在“选哪一个节点”的比较里固定query簇和同一套画像构建规则；新旧hub都必须有对应画像，不能给新hub套旧向量。保持相同总H、真实ID唯一性及相同入口数，记录跨簇候选碰撞、稀有簇覆盖、回退和替换率。若允许多个簇共用同一hub，则还需独立定义slot数、去重和补位，那是另一项变化，不能默默混入本轮固定一画像一hub对照。

**连通性怎样进入。** 可以记录入度、出度、邻居方向冗余、指向多个目标区域的边，以及在代表query下能否产生持续的分数改进。静态指标只作候选特征/解释，入口选择的主要证据仍是真实finite-L Recall和已付成本。建议对照“原GT代表 / 静态图特征规则 / 真实搜索作用选代表”，检验图特征有没有独立贡献。没有现成标签的新H列必须新测；不要把单向入度当作向外可达性，也不要重启旧BTG的BFS/PageRank式扩散网格。

**三入口联合评分是本方向的条件分支。** E23已观察同一query对a/b的偏好随另两个入口改变，但没有量化为全部差距。如果single服务分组仍不能改善实际三入口，可在固定小候选池上比较：独立分数取top3，与直接评分整个集合`F(q,{e1,e2,e3})`。一个可研究的有限模型是单项分数加两两交互，再与能表达整组上下文的模型区分；两两模型不保证表达全部三阶作用。组内顺序应置换不变，评分标签必须来自三个互异真实入口启动同一次原kernel。

这里不能把C8自动当成充分候选，也不能把三个single命中并集当真实联合收益。先固定候选池及其覆盖诊断，再比较同池上的选择器；池外质量损失与池内排序损失分别报告。任何在线候选提议、集合枚举/评分、query网络和去重都收费。共享hub端MLP若最终仍导出固定W，依旧是静态单项评分，不会自动变成整组三入口模型。

**进入与收口。** 只有在具体分支、标签复用身份和成本账清楚后才锁协议。新H只提高免费oracle、收益只在fit出现，或真实三入口的额外路由成本吃掉质量收益，都不足以继续扩大预算。若独立exact选择也没有改善，应先审查目标/候选；不能靠换HNSW掩盖问题。产物包括候选来源、旧新H映射、逐query/入口或三元组真实结果、分组支持、可预测性与覆盖分解、在线成本和完整Recall–QPS。

### 4.2 第三优先：针对OOD调整Micro-HNSW的几何与导航

**问题与证据。** 先固定画像W和真实hub映射，研究同一评分函数能否用更少时间检索。query–base的OOD差异不能直接套到query–画像；query均值画像仍可能收缩/偏移，须从fit统计核对。E23 audit中Fast20K的精确画像top3相对HNSW，最终Recall仅提高0.283/0.078pp；Yandex Full反而低0.098pp，所以当前没有“微型图是主要质量瓶颈”的结论。路由NDC不是wall占比，要先测实际成本。

**3A：优先保分数的成对变换。** 首轮事先指定一份W，建议先用matched Fast20K，避免同时选择画像模型和变换。对可逆A，定义`p′=Ap,q′=A⁻ᵀq`，保持`q′ᵀp′=qᵀp`，而画像之间的内积变为`p_iᵀAᵀAp_j`。需要重建Micro-HNSW才可能改变边和访问路径；只在原邻接上做保分数变换，理想算术下query比较次序不变。变换仅作用于路由，NSG仍读取原raw query。

最小版本使用正对角A，单query代价O(d)。可用fit raw query未中心化二阶矩初始化`A_ii∝sqrt(mean(q_i²)+ε)`，做总体尺度规范化并限制条件数。应保留A=I恢复项，在fit上确定初始化及小范围强度/尺度限制候选，再按cal选择；这些数值须预先锁定。该初始化不是最优性结论，对角缩放也未解决跨维相关；全矩阵二阶矩平方根/白化相关形式O(d²)，只有成本证据支持时再考虑。

不得变换后再把每个画像单位化，不得随意给query减均值，否则保分数关系会改变。统一缩放、正交旋转或把图画得更开，在精确算术和固定随机/ties下没有这里所需的建图比较改变机制。两侧同乘各向异性A则得到新分数`qᵀAᵀAp`，属于改评分/度量的另一分支，不能称无损拉伸。

| 必要对照 | 目的 |
|---|---|
| 原W＋原micro-HNSW | 当前路由成本和质量基线 |
| A=I＋相同构建配置重新建图 | 恢复与随机/建图身份对照 |
| 成对A变换＋重建micro-HNSW | 检验几何改变能否改善导航 |
| 原W/变换W的exact top3 | 检查数学分数、排序及真实ID一致；对小margin/ties单独审查浮点差异 |

首轮固定M、efConstruction、ef和随机seed，避免把更大搜索宽度的收益归给拉伸。随后若单独研究ef–质量曲线，事先冻结相同ef候选表，并在相同画像检索质量/最终Recall下比较真实wall。记录query变换耗时、画像搜索wall、路由/总NDC、ANN对exact的集合覆盖、最终NSG Recall和完整QPS；减少NDC却总wall更慢仍未通过效率目标。

**3B：query感知的微型图边，后置备选。** 若保分数缩放不足，可借鉴RoarGraph/OOD-DiskANN的query–目标关系构图：从fit query对画像的需求建立候选连接，再作有界剪枝、方向多样性和连通检查。此时必须先定义需求是“高分画像”还是“高真实效用入口”，两者不是同一个标签。保持W、H、边预算/搜索配置可比，分别测试几何建边和query感知建边；不要把论文重建base图的整套加速数当成本地小图预期。

**3C：重建NSG主图是更大范围的独立研究。** 如果目标转为大图OOD导航，需要重新审查RoarGraph/RobustVamana同机适配、完整图构建/存储成本和同等比较，不再属于“只改入口层”。图身份改变使原入口效用标签失效；若base/metric没变，exact GT本身可以保持有效，但所有搜索结果必须重测。当前不安排该分支自动执行。

**进入与收口。** 评分保持、身份与输出parity先验收，再评价效率。成对变换破坏排序，先排查归一化/中心化/数值实现，不能视为方法提高。若只有ANN代理召回提高而端到端没有改善，或变换成本超过节省，应收口该版本。产物包括A及条件数、fit统计身份、前后评分误差、图/入口差异、路由wall和端到端曲线。

### 4.3 聚类器怎么换：先确定分组目标，再比较算法

此项是第一/第二方向的配套选择，不是凭OOD标签直接替换k-means。当前聚的是query，球面k-means有合理性；5K分约800簇平均仅约6条，复杂模型需要最小支持或参数共享。最初QGT簇与后续20K画像basin必须分别统计，不能把后者计数当成前者的簇大小。

| 备选 | 具体要试什么 | 必要控制和风险 |
|---|---|---|
| 受约束的球面k-means / 层次球面聚类 | 先形成支持较充分的粗簇，再细分；观察最小支持、失衡和query重构 | 控制总簇/画像预算；硬均衡可能切开真实语义，不能只看簇大小更整齐 |
| vMF混合模型 | 对方向数据做软成员概率，容许不同集中程度；小样本簇可共享或正则化集中参数 | 与球面k-means用同一输入及输出预算；控制自由度，检查成分塌缩、有效支持及稳定性 |
| query–GT目标关系驱动的分组 | 依据query的GT-topK落入哪些粗目标区域，或哪些入口真实有效来分组；再学习query到分组的路由 | 纯GT ID重合可能太稀疏，旧128对近query的Yandex GT10平均交集仅0.250；粗目标区域和监督代价也要记录 |

建议先单独比较原球面k-means与一个最相关备选，不同时替换聚类器、GT目标、真实入口和在线路由。若仅变分组，H和下游画像规则保持固定，明确簇如何映射到H；若映射/真实H也随之改变，应作为独立因素记录，不能把全部变化归于聚类器。始终核对唯一真实ID、画像数及三入口去重语义。

离线指标记录簇大小、空簇、有效支持、目标区域覆盖、GT名次/目标范数分布及稳定性；它们用于解释，最终仍看真实搜索和成本。vMF似然、silhouette或query重构变好不单独构成GO。LIRA提供query目标分布监督的相关思路；Neural LSH的base图平衡分区原假设不能直接推广为OOD保证；SOAR提示冗余要具互补性，而不是多加随机view。

### 4.4 rank容量比较：目标稳定后，保留Full作参考

**问题。** rank8只是预设残差容量，尚未与rank4/16/32比较；Full训练目标更低，但Yandex最终五L不如rank8。选中Full残差的前8奇异方向能量为WebVid90.25%、Yandex63.27%，它是Frobenius能量，不是最优rank或最终Recall标准。

建议在明确的一份目标上比较`r∈{4,8,16,32}`与Full，保留相同P0、H、fit/cal/audit、真实标签、损失、λ候选和求解预算规则。若沿用E23，则两因子均学习，并由同一fit初始梯度的嵌套奇异方向初始化，避免为不同rank偷偷使用不同教师/验证信息；Z=0、同一P0恢复项保持一致。若研究新目标，就另立版本，不能把E23的最优λ/rank当成已经在新目标上选择过。

联合选择rank和λ只用cal，audit只评估冻结模型；记录优化残差、目标、实际训练成本、模型有效rank、query加权分数差/top3变化以及最终Recall–QPS。不用训练损失最低或SVD能量最高直接选模型。Full用于分清优化不足与容量/泛化差异，不是实际搜索上界。

目前各rank均折叠为同尺寸W部署，因此rank影响离线容量，在线维数/画像数并不随r缩小；画像变化仍可能改变HNSW访问成本。若改为在线低维因子检索，需要同时保留P0分数，另算query投影和候选检索开销，不能把“rank8”偷换成“仅8维ANN”。

标签复用先检查数值依赖：同一query/图/入口集合/L的真实结果可保持有效，但旧候选组合来自旧提议器，覆盖偏差须披露；P0、温度或目标变化后的缓存分数/派生训练项不能无条件复用。若增加rank只改善fit或单点Recall、没有开发与端到端收益，不扩大rank/seed网格。

### 4.5 Yandex raw-IP范数问题：作为独立归属消融

当前exact GT来自raw IP，而GT向量与hub先单位化再分basin，因此目标/hub范数信息在归属时被丢掉。仅归一化同一query不改变其IP排序，但归一化目标/hub会改变归属；两件事不能混为一谈。

先从fit记录目标/hub范数、cosine归属变化、画像有效支持及其与真实入口作用的关系。若有明确不匹配证据，再固定K_gt、软归属温度规则和H，单独比较角度归属与一个明确的范数感知规则。直接把target–hub cosine换成raw dot也只是另一个代理，可能偏向大范数hub，不能宣称自动恢复了query→base的正确相关性。

只在路由归属中改变代理时，主图raw-IP和GT不改；若要修改base/query预处理或正式metric，则按spec重建不兼容GT/图/标签，不能继续混用当前结果。首轮GT1/GT10×硬/软不混入这个变量，防止同时改变过多因素。

### 4.6 从结果决定下一方向，避免只按序号堆实验

| 观察 | 更有针对性的下一步 | 不能据此推断 |
|---|---|---|
| GT10硬优于GT1硬，软分配无额外收益 | 保留多目标信息，检查支持/范数或有监督分组 | 软分配、复杂聚类器必然更好 |
| 软画像的exact选择有收益，HNSW部署明显损失 | 保留画像，独立研究微型图导航/成对拉伸 | 精确画像top3等于最优真实入口 |
| exact与HNSW都无收益，但现有H效用空间仍大 | 优先真实搜索作用分组/条件三入口评分 | 必须先换新H或重建NSG |
| 现有H的受限候选覆盖不够，而新GT候选有实质作用 | 定义固定H预算的入口替换实验，连同路由学习一起测 | 新候选oracle提升已经可部署 |
| 学习模型fit更优而cal/audit更差 | 在同目标下研究rank/正则及可预测性 | 继续增加rank或MLP一定有效 |
| 画像支持薄弱或单峰假设明显不合适 | 比较一种有支持约束的聚类器或vMF | 离线簇更均衡/似然更高就是Recall–QPS提升 |

优先次序不替代具体证据。每个实际运行版本都先锁自己的参数/预算/停止条件；本节保留全部讨论方向，默认新对话启动仍先执行第2–3节主线。

Micro-HNSW是约800个画像的小图，主搜索仍为NSG。以后若改NSG须新图身份并重建受影响标签/评测。旧E22大矩阵不恢复；C保持`NO_GO_UNCONDITIONAL_HEADROOM_STOP_C`，不自动启动C3/C4、联动、D或效用树。所有旧源码、图、GT、标签、模型、日志和结果保留。

## 5. 新对话应定位的代码与证据

- 阅读顺序：[AGENTS.md](AGENTS.md)→[summary.md](summary.md)→[spec.md](spec.md)→本文件→[s-experiment.md](s-experiment.md)。
- 当前研究：[四问题报告](entry_method_exploration/20260910_ood_hubs_clustering_router_research_v1/report.md)；代理/入口/微型图差距见[E20历史08](experiment_history/08_fast_router_diagnosis.md)及其原始分析。
- 历史边界：[效用与表示04](experiment_history/04_utility_and_representation.md)、[reroute05](experiment_history/05_probe_reroute.md)、[E23历史12](experiment_history/12_three_entry_rank_exploration.md)。有疑问沿卡片到原始证据，不必重做整轮文献调研。
- 原画像实现：[builder](benches/run/build_fast_entry_variants.py)的`choose_unique_gt_hubs`与`build_gt_basin_prototypes`；新方法放独立版本。
- 输入身份：[E23 prepare_fit.py](entry_method_exploration/20260910_three_entry_rank_v1/src/prepare_fit.py)和其`inputs/<dataset>/<split>/config.json`。GT实际保留100列，读取时核对形状、字节数与row_ids；旧准备器还会读取single标签并生成组合，不能整段照跑来准备本次闭式画像。
- 单线程评测：[E23 protocol](entry_method_exploration/20260910_three_entry_rank_v1/protocol.md)、[evaluate.cpp](entry_method_exploration/20260910_three_entry_rank_v1/src/evaluate.cpp)、[最终验收](entry_method_exploration/20260910_three_entry_rank_v1/reviews/final_audit.json)。复用需绑定新版本的源码/可执行文件/输出身份，不覆盖E23。

## 6. 可复制的新对话启动指令

```text
工作目录 /data/netg/ACSG。
请完整阅读 AGENTS.md、summary.md、spec.md、s-target.md、s-experiment.md，
再读 s-target 指向的四问题调研及相关历史原始证据，不要只依据摘要或目录名判断。

请推进 s-target 第一方向：固定现有H，比较GT1/GT10 × 硬/软归属画像。
以文档建议范围为起点，先核对输入和实现、冻结独立小型protocol及调用预算，
然后完成画像恢复检查、开发选择和协议内的小型单线程Recall–QPS比较。
常规实现与小网格细节自行按证据确定并写入协议；完成一阶段后继续协议内下一阶段。
发现身份/parity错误先修复；达到固定停止条件则保留结果、报告并收口。

保持原base、raw-IP、NSG、QGT seed20260828、H815/821和三个互异真实入口。
以matched Fast20K为改进主对照；GT只在fit构建画像，cal选参数，audit只报告，
冻结后评估协议规定的小validation；披露历史使用，不打开held-out。
无需重跑全H single或三入口训练标签，不先训练Full/rank8。
正式查询单线程、单方法独立plain wall，全部路由成本计入端到端QPS。
不要同时引入新H、vMF、rank sweep、MLP或HNSW拉伸，不恢复旧大实验/C。
保留所有旧源码、图、GT、标签、模型和结果，新实验放独立目录。
交付完整结果/对照、Recall–QPS图、成本与局限，同步四份主文档及历史。
```

以上指令供用户在新对话启动第一方向；本次文档交接未执行它。用户以后如要指定其它方向，可以保留阅读/保护/计时要求，只替换任务段：

| 要启动的方向 | 可替换的任务说明 |
|---|---|
| 真实效用分组 | “推进s-target 4.1的2A：先固定H比较GT几何归属与真实finite-L效用分组，核对旧标签兼容性，保留旧centroid对照；不要默认进入2B新H。” |
| 微型HNSW拉伸 | “推进s-target 4.2的3A：固定matched Fast20K W，研究正对角成对变换与重建Micro-HNSW；先验评分恢复，再测完整wall，不改NSG。” |
| 聚类替代 | “按s-target 4.3先定位支持/单峰问题，固定目标与输出预算，选择一种最相关聚类备选作小对照；不要同时改变H、画像和路由。” |
| rank容量 | “按s-target 4.4，在事先明确的同一目标上比较rank4/8/16/32与Full；若沿用E23目标则核对标签后复用，cal联合选rank/λ，不扩大其它变量。” |

每次只推进用户指定的分支及其锁定协议。方向2/3、聚类和rank不是自动串行队列；全部方案保留在本文件，便于下一对话按结果和用户选择接续。
