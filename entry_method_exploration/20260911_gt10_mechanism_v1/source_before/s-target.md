# ACSG 下一阶段方向与实验接续

2026-09-10夜间。**用户最新确定：下一步先弄清GT10为什么提高性能，以GT10 hard对GT1 hard为主对照。** 计划状态`GT10_MECHANISM_ANALYSIS_PLANNED_UNRUN`，具体执行顺序见第3节，新对话指令见第6节；本次只更新文档，明日续接分析。E25/E26均已收口，E26保留`SHRINKAGE_DID_NOT_STABILIZE_SELECTIVITY_NO_FORMAL_GO`，不以其负结果否定E24。原[当晚收口安排](entry_method_exploration/20260910_profile_shrinkage_v1/authorization_update.md)继续有效，原protocol保留历史。第4节的方法探索在GT10机制分析之后按证据选择，不是一张自动执行队列。

## 1. 最近结果给出的判断

E24的GT10已有正信号，应先解释它。相对matched GT1 hard，WebVid GT10 hard在L64/800同时提高Recall和QPS，L128/256是小幅Recall下降与速度提高的交换，L400微降；Yandex五L Recall均提高，三个点QPS也提高。WebVid L64为+0.285pp/+3.13%，Yandex L128为+0.335pp/+2.56%，这些速度数值属于E24当轮单次wall。不能把“大部分优于NSG”全部归给GT10，Fast本身的收益要由matched GT1 hard对照扣开。

E25两类门控与E26单路收缩都未建立跨数据集稳定的收益保留/损失减少与端到端改善。E25 WebVid保留较多收益但路由成本抵消小幅质量修复，Yandex减少损伤时失去大多数有效改道。E26两数据集cal冻结α0.75，cal/audit/validation均未达联合目标；validation有效事件保留64.62%/68.92%、全部受损事件净减少14.02%/22.58%，十点九个Recall低于E24，无稳定同L双升。

这两组后续结果回答的是“能否继续增强GT10”，不撤销E24已有提升。75%收益保留/25%损伤减少是E25/E26目标，不作为原GT10有效性的门槛；也不要求全部query或每个L都变好。评价应看目标Recall区间的整体实测前沿、重复稳定性和代价。原始事实见[E24报告](entry_method_exploration/20260910_gt_topk_profiles_v1/report.md)、[E25报告](entry_method_exploration/20260910_selective_profile_gate_v1/report.md)、[E26报告](entry_method_exploration/20260910_profile_shrinkage_v1/report.md)。

## 2. 当前冻结资产与继续时的对照

- E24画像、E25门控和E26三个alpha/两端点均封存；E26两数据集统一冻结alpha0.75不是默认部署推荐。原base/raw-IP/NSG、QGT seed20260828、H815/821和三个唯一真实入口不变。
- E26未训练或生成全H/single/triple新标签；cal[6144,8192)2048/audit[8192,10000)1808不参与E24 fit20K，但具有历史开发使用。历史validation前2000已用于E24/E25/E26；下一方法须披露该历史，不能称新盲测，held-out仍不自动打开。
- E26正常897280真实调用、修复0、合成2268，全部阶段结束；E25正常1089152、E24正常543296均已独立用完并收口。任何旧预算、未使用修复额度或时间授权都不是新队列预算。
- 后续新方法保留matched Fast20K、E24按旧cal冻结的主画像及相关GT10硬/软对照；Fast30K另列30K/seed100/顺序身份。E25/E26可作对应机制参照，不按旧validation重新挑主规则。

## 3. 下一步首要任务：解释GT10的性能收益

**任务目标。** 回答GT10改变了什么、哪些变化真正帮助搜索、Recall和QPS分别为何变化，以及收益在哪些数据/query/L上存在。允许结论是多个因素共同作用或部分速度差未复现，不能预设“GT更多所以必然更好”。先解释已观察到的收益，再由解释决定如何继续改进。

### 3.1 主对照、现有证据与理论起点

主对照固定为两数据集的`GT10 hard`与`GT1 hard / matched Fast20K`，覆盖L64/128/256/400/800；WebVid虽原cal选中GT10软，也必须直接分析GT10硬。GT1软/GT10软为辅助消融，NSG/Fast30K为上下文对照，E25/E26用于解释后续改动为何损失原收益。保持原fit20K、H、raw-IP、NSG、入口数、Micro-HNSW参数/seed/入口顺序一致，不把30K/20K或旧不同顺序的差异归给GT数。

从[E24构建源码](entry_method_exploration/20260910_gt_topk_profiles_v1/src/build_profiles.py)核对：若`b(q,j)`是第j个GT目标按cosine归属的真实hub，则`a1(q,h)=1[b(q,1)=h]`，`a10(q,h)=Σ(j=1..10)1[b(q,j)=h]/10`，画像为`normalize(unit(raw_hub)+Σq a(q,h)unit(q))`。GT10 hard对每个GT目标硬归属，但同一query可向多个hub分配分数权重；每query总质量仍为1。它不是训练query增至十倍，也不是增加H或在线入口数。画像累加的是query方向，GT向量只决定权重。GT1原float32恢复和其它画像float64累加差异单列数值控制，不能把舍入变化算作多目标机制。

### 3.2 阶段A：先核清提升的范围与稳定性

从[E24全部原值](entry_method_exploration/20260910_gt_topk_profiles_v1/results/tables.md)、[逐点指标](entry_method_exploration/20260910_gt_topk_profiles_v1/results/metrics.csv)、[配对差](entry_method_exploration/20260910_gt_topk_profiles_v1/results/comparisons.csv)重建两数据集GT10硬对GT1硬的完整五点表、逐query命中变化和实测非支配点。正点、交换点、负点一起解释，不以连线直接推断等Recall加速，不用固定单L优劣代替整条前沿。

核对E25/E26中已经重复测得的A0/A1：Yandex的A1确为GT10硬，可以对相同模型/query的质量做身份回归、对各轮独立QPS差分别检查；WebVid的A1是GT10软，不能将这些重复当作GT10硬重复。相同query/模型的重复计时不增加Recall样本数，跨轮wall不混成同一批比较。先利用已有三次wall、route/graph单测和原始日志；缺少的稳定性证据列入阶段D，避免先整轮重跑。

交付一张“哪个数据集、哪个Recall区间、改善质量还是速度、当前复现到什么程度”的证据表。若某一速度增幅随轮次明显变小，明确报告；仍可继续分析其画像/质量机制，不把一次速度差当作确定因果。

### 3.3 阶段B：从GT归属追到画像与三入口

按下表沿同一原query/hub身份连接已有fit统计、W、入口和真实结果。先分析相关和必要条件，不把支持数、距离或几何覆盖直接写成搜索效用。

| 要回答的问题 | 优先使用的证据 | 怎样避免错误归因 |
|---|---|---|
| 第2–10名GT增加了哪些信息？ | 每rank归属hub、与GT1同hub的比例、每query有效hub数；`a10−a1`的质量转移 | 同hub的十个目标不等于十份新信息；总query质量仍为1 |
| 哪些画像实际改变，是否减少支持不足？ | [支持统计](entry_method_exploration/20260910_gt_topk_profiles_v1/results/profile_support.csv)、每hub mass/ESS/prior比例、W角位移和方向集中度 | ESS增长与平均更平滑是描述，不能直接推出泛化或Recall提高；QGT选H的簇与fit画像basin分开 |
| 新画像把哪些query送去了不同入口？ | GT1/GT10硬的精确top3与HNSW top3、实际三入口集合重合、分数间隔、入口频次/覆盖 | 同三入口在原kernel下应有相同结果；变了多少入口不等于改好了多少 |
| 哪些改道贡献了净命中收益？ | 全部query按增益/持平/受损分组，报告正负幅度、零命中救回/新增失败及跨L变化，再关联支持和入口变化 | 全query保留分母，案例按明确规则选；GT只作离线解释，不进入线上策略 |

画像归属矩阵若未存完整文件，按原fit与构建规则只读重算，并核对manifest中的digest；不运行会覆盖原模型的builder。分组统计尽量先在原开发段提出解释，再检查其它已使用段的一致性，并披露它们都是历史开发/validation数据，不能称新的盲验证。

### 3.4 阶段C：区分“入口更有效”与“计算更便宜”

Recall侧先比较GT1硬/GT10硬各自的exact3和HNSW3，用已有cal/audit逐query结果判断收益在精确画像排序下是否仍存在，不能用WebVid GT10软的exact结果替代硬画像。精确画像top3仍不是NSG效用oracle；三个入口的互补或竞争必须由真实联合搜索解释，不能把独立single命中并集当作三入口结果。

成本侧分开列route NDC、graph NDC、各自单测wall和独立端到端wall。追问GT10是否减少微型图访问、是否让NSG在更有利的位置启动，或改变扩展/距离计算与内存访问；只存在NDC差时不能直接解释全部QPS差。现有路由只占L128总wall约1%，尤其Yandex GT10硬的L128 graph NDC略增而E24 QPS提高，必须保留计时/路径/缓存原因尚未分离的可能。

优先复用已有结果和trace；若缺少逐扩展路径等证据，列清缺失字段，不声称已经观察到更短路径。需要补trace时只对事先固定的小批代表query和对照，在timer外诊断并验原kernel结果一致；诊断开销不能混入正式QPS。

### 3.5 阶段D：有明确证据缺口再做最小补测

先完成A–C的已有证据分析，再为仍无法区分的解释选择最少对照，并在任何新搜索前冻结独立目录、模型/query/GT/图身份、候选、线程、调用与时间/存储上限。两类可能需要的补测是：一类重复固定GT1/GT10硬曲线，确认速度差和目标Recall区间；另一类隔离真实多目标信息与一般平滑/支持增加，例如保留GT1贡献、按固定规则打乱第2–10名目标与query的对应关系作为诊断。后者须先说明实际保持了哪些支持统计、改变了哪些因素，不能泛称完全匹配控制。这些是候选诊断设计，当前未选定具体数值、未实现或执行。

所有新查询单线程、每次一个方法、独立warm/plain端到端wall；若只重放固定入口测graph或做带trace诊断，应明确属于分项/机制证据，不作为完整在线方法QPS。只在已有数据范围或新协议明确限定的开发样本补测，held-out不自动打开；不以本次计划启动GT数/温度/seed大网格、新H、门控、rank、MLP、C/probe或2A新标签。

### 3.6 最终交付与后续决策

产物至少包含：GT1/GT10硬完整性能与重复性表、GT rank→hub质量转移、画像支持/方向变化、逐query三入口与正负命中连接、路由/主搜索/总wall成本分解，以及每个解释的“证据支持／反证／尚未区分”清单。将可确认的机制用中文讲清楚；无法确认的部分给出缺少哪项证据，不能编成单一原因。

收口时回答“GT10的收益主要来自哪里、在什么条件下保留、哪些简单特征值得沿用”。如果真实多目标信息有独立作用，再考虑如何利用；如果主要来自一般支持/平滑，优先研究更直接的控制；如果速度主要是测量波动，就保留已验证的质量变化并纠正速度幅度。2A、联合评分和微型图效率等只按这轮解释决定是否成为下一实验，不预先把新模型当作结论。原E24/E25/E26均保持完成身份，新分析有独立记录，更新summary/history时不覆写旧报告。

## 4. 机制分析之后保留的方法方向

| 优先级 | 方向 | 进入条件和区别 |
|---|---|---|
| 当前首要，第3节 | GT10收益机制分析 | 先解释已有提升与边界，形成证据链；当前计划已确定、分析未执行 |
| 1，E24已完成收口 | 固定H的GT-topK软画像 | 隔离目标归属；与旧GT1 basin内增加两个mode、多seed多view、single赢家centroid不同 |
| 2，较重备选 | 以真实finite-L作用组织分组或在小GT候选集挑入口 | 若主线显示几何代理仍有缺口，再定协议；度数只作特征，三入口用真实联合搜索。旧centroid/rerouter已有真实效用，须说明新条件作用/可预测分组差别 |
| 3，效率支线 | 固定W，成对拉伸并重建Micro-HNSW | `p′=Ap,q′=A⁻ᵀq`，优先受限正对角A；先验评分一致，再看导航和总wall。不能变换后逐画像归一化；不重建边时保分数变换不会改变理想搜索路径 |

先完成第3节GT10机制分析，再依据结果调整后续方法优先级。原有方向分别改善画像目标、真实入口作用和索引导航，应独立对照后再决定组合；E24的局部收益保留，不能因后续增强未通过便跳过其原因分析。除E24已完成外，下面其它方法分支尚未执行，也不构成一张自动全部跑完的实验队列。

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
| GT10硬优于GT1硬，软分配无额外收益 | 先按第3节区分真实多目标信息、支持/平滑和路由/主搜索成本，再决定方法 | 软分配、复杂聚类器或有监督分组必然更好 |
| 软画像的exact选择有收益，HNSW部署明显损失 | 保留画像，独立研究微型图导航/成对拉伸 | 精确画像top3等于最优真实入口 |
| exact与HNSW都无收益，但现有H效用空间仍大 | 优先真实搜索作用分组/条件三入口评分 | 必须先换新H或重建NSG |
| 现有H的受限候选覆盖不够，而新GT候选有实质作用 | 定义固定H预算的入口替换实验，连同路由学习一起测 | 新候选oracle提升已经可部署 |
| 学习模型fit更优而cal/audit更差 | 在同目标下研究rank/正则及可预测性 | 继续增加rank或MLP一定有效 |
| 画像支持薄弱或单峰假设明显不合适 | 比较一种有支持约束的聚类器或vMF | 离线簇更均衡/似然更高就是Recall–QPS提升 |

优先次序不替代具体证据。每个实际运行版本都先锁自己的参数/预算/停止条件；本节保留全部讨论方向，E24已经结束；后续按用户明确选择进入2A/3A/聚类/rank等独立分支，不默认复跑第一方向。

Micro-HNSW是约800个画像的小图，主搜索仍为NSG。以后若改NSG须新图身份并重建受影响标签/评测。旧E22大矩阵不恢复；C保持`NO_GO_UNCONDITIONAL_HEADROOM_STOP_C`，不自动启动C3/C4、联动、D或效用树。所有旧源码、图、GT、标签、模型、日志和结果保留。

## 5. 新对话应定位的代码与证据

- 阅读顺序：[AGENTS.md](AGENTS.md)→[summary.md](summary.md)→[spec.md](spec.md)→本文件→[s-experiment.md](s-experiment.md)。
- 下一首要任务为第3节GT10收益机制分析：[E24构建源码](entry_method_exploration/20260910_gt_topk_profiles_v1/src/build_profiles.py)、[支持统计](entry_method_exploration/20260910_gt_topk_profiles_v1/results/profile_support.csv)、[近似/精确对照](entry_method_exploration/20260910_gt_topk_profiles_v1/results/ann_diagnostics.csv)、[原始全部指标](entry_method_exploration/20260910_gt_topk_profiles_v1/results/metrics.csv)；先以两数据集GT10硬对GT1硬连接已有证据。
- 最近完成E26：[报告](entry_method_exploration/20260910_profile_shrinkage_v1/report.md)、[协议](entry_method_exploration/20260910_profile_shrinkage_v1/protocol.md)、[固定选择](entry_method_exploration/20260910_profile_shrinkage_v1/models/frozen_before_audit.json)、[历史15](experiment_history/15_profile_shrinkage.md)、[用户收口更新](entry_method_exploration/20260910_profile_shrinkage_v1/authorization_update.md)。
- 已完成E25：[协议](entry_method_exploration/20260910_selective_profile_gate_v1/protocol.md)、[固定选择](entry_method_exploration/20260910_selective_profile_gate_v1/models/frozen_before_audit.json)、[完整报告](entry_method_exploration/20260910_selective_profile_gate_v1/report.md)、[历史14](experiment_history/14_selective_profile_gate.md)。
- 已完成第一方向：[E24完整报告](entry_method_exploration/20260910_gt_topk_profiles_v1/report.md)、[协议与预算](entry_method_exploration/20260910_gt_topk_profiles_v1/protocol.md)、[冻结选择](entry_method_exploration/20260910_gt_topk_profiles_v1/models/frozen_before_validation.json)；全部消融及负点保留。
- 当前研究：[四问题报告](entry_method_exploration/20260910_ood_hubs_clustering_router_research_v1/report.md)；代理/入口/微型图差距见[E20历史08](experiment_history/08_fast_router_diagnosis.md)及其原始分析。
- 历史边界：[效用与表示04](experiment_history/04_utility_and_representation.md)、[reroute05](experiment_history/05_probe_reroute.md)、[E23历史12](experiment_history/12_three_entry_rank_exploration.md)。有疑问沿卡片到原始证据，不必重做整轮文献调研。
- 原画像实现：[builder](benches/run/build_fast_entry_variants.py)的`choose_unique_gt_hubs`与`build_gt_basin_prototypes`；新方法放独立版本。
- 输入身份：[E23 prepare_fit.py](entry_method_exploration/20260910_three_entry_rank_v1/src/prepare_fit.py)和其`inputs/<dataset>/<split>/config.json`。GT实际保留100列，读取时核对形状、字节数与row_ids；旧准备器还会读取single标签并生成组合，不能整段照跑来准备本次闭式画像。
- 单线程评测：[E23 protocol](entry_method_exploration/20260910_three_entry_rank_v1/protocol.md)、[evaluate.cpp](entry_method_exploration/20260910_three_entry_rank_v1/src/evaluate.cpp)、[最终验收](entry_method_exploration/20260910_three_entry_rank_v1/reviews/final_audit.json)。复用需绑定新版本的源码/可执行文件/输出身份，不覆盖E23。

## 6. 明日新对话启动指令

本轮第一方向已结束，不再使用旧的“启动第一方向”指令重跑；原指令和全部建议范围保存在[E24修改前s-target](entry_method_exploration/20260910_gt_topk_profiles_v1/source_before/s-target.md)及[锁定协议](entry_method_exploration/20260910_gt_topk_profiles_v1/protocol.md)。

下一次从已确定的GT10收益机制分析开始：

```text
工作目录 /data/netg/ACSG。
完整阅读AGENTS.md、summary.md、spec.md、s-target.md、s-experiment.md，
沿历史13进入E24原协议、构建代码、manifest、逐query结果和成本，再读E25/E26相关对照。
按s-target第3节先弄清GT10为什么提高性能，不先发明新方法。
主对照是两数据集GT10 hard与matched GT1 hard，GT1/GT10 soft作辅助消融。
先复核已有五L的Recall/QPS与重复性，区分GT10对Fast的增益与Fast对NSG的增益。
沿GT目标归属、画像支持/方向、实际三入口、NSG命中/工作量和纯wall追溯；
Recall和QPS分开解释，支持/平滑、真实多目标信息和近似路由因素分开检验。
全部正负query/L点保留，历史validation的使用如实披露，不当新盲测。
先用已有数据完成归因；缺证据才冻结独立小协议和硬预算做最小补测，保留旧资产。
正式查询单线程、每次一个方法、纯端到端wall；trace/count在timer外，分项不冒充总QPS。
不以75%/25%增强门槛否定原GT10，不要求所有query/L都受益；不自动开held-out或新模型大网格。
最终交付有证据支持的收益解释、成立条件、未解决项及由此推出的下一步，同步对应文档。
```

以上是当前接续指令，本次尚未执行分析。完成机制分析后，若证据支持再选择下列方法分支：

| 要启动的方向 | 任务说明 |
|---|---|
| 真实效用分组2A | 按4.1固定H，先核对旧single/triple标签兼容性及与旧赢家centroid的区别，保留GT1硬/GT10硬和原冻结软画像对照，再定独立协议。 |
| 微型HNSW拉伸 | 按4.2的3A固定matched Fast20K W，比较受限正对角成对变换；先恢复评分/身份，再重建Micro-HNSW并测完整wall，不改NSG。 |
| 聚类替代 | 按4.3先定位支持/单峰问题，固定目标和输出预算，只选一种相关聚类备选；不同时改变H、画像和路由。 |
| rank容量 | 按4.4先明确同一目标，核对兼容标签后比较rank4/8/16/32与Full；cal联合选rank/λ，不扩大其它变量。 |

每次只执行明确指定的分支及其锁定协议；第一方向的局部正信号或结束都不会自动开启这些队列。
