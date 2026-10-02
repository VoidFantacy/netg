# ACSG 下一阶段方向与实验接续

2026-09-11。**GT10收益机制分析E27已完成，限定补测已收口。** 状态`GT10_MECHANISM_ANALYSIS_COMPLETE_WITH_BOUNDED_DIAGNOSTICS`。两个原正点在exact3下仍有收益，WebVid小幅速度复现，Yandex原速度幅度未稳定保留；信息与一般平滑仍未完全分离。完整证据见[历史16](experiment_history/16_gt10_mechanism.md)及[E27报告](entry_method_exploration/20260911_gt10_mechanism_v1/report.md)。下一步由用户明确选择一条方法分支及其独立协议；第4节不是自动执行队列。

## 1. 当前结果给下一步的约束

E24的GT10局部正信号保留，E25/E26增强未通过不抵消原收益。E27说明：query相关的多目标分数归属改变画像及实际三入口，少数正负query的净差产生收益；两个已补正点在exact3下仍分别+0.435/+0.310pp，不能主要归于HNSW误差。

WebVid hard新重复五L QPS中位提高0.34%–1.36%，其中L64/800质量也提高，L128/256/400仍有质量交换；Yandex原L128约2.56%速度未在E25/E26稳定保留。后续评价继续看完整实测Recall–QPS，不以NDC、单L或粗网格插值代替端到端。

一个固定打乱控制7/8方向支持保留query–真实目标对应关系，但区间全跨0且ESS/方向不完全匹配。大ESS、填补空hub、画像位移或GT区域覆盖都不是已证明可选好入口的规则。有限L三入口效用仍不能由几何代理直接替代。

## 2. 当前冻结资产与对照

- E24所有画像、E25门控、E26三alpha/端点和E27原始分析/限定补测均封存。原base/raw-IP/NSG、QGT seed20260828、H815/821及三个唯一真实入口保持。
- 后续保留matched GT1 hard、GT10 hard及原cal冻结的GT1/GT10 soft；WebVid原主画像是GT10 soft，Yandex是GT10 hard。Fast30K继续单列其30K/seed100/顺序身份。
- E27 tail_shuffle仅为机制控制，没有被选为部署候选；本轮未生成single/triple训练标签或训练新模型。其一份排列、两个局部exact正点和WebVid重复矩阵都已经执行完，不是可继续追加的预算。
- E27正常181376真实调用、修复0、合成0。E24/E25/E26各自旧预算均已收口；未用修复额度不转为新实验预算。
- fit/cal/audit/validation均有历史使用；本轮两个exact正点也为事后选取的解释对象。held-out未打开，不自动开启。任一新方法必须如实披露这些使用历史。

## 3. 机制分析已经完成：剩余问题与方法选择

### 3.1 已完成交付

已有A–C归属/画像/入口/成本分析、108个历史点重评分，以及独立锁定的shuffle、两个局部exact和WebVid重复计时均完成。交付[完整报告](entry_method_exploration/20260911_gt10_mechanism_v1/report.md)、[全部表](entry_method_exploration/20260911_gt10_mechanism_v1/results/tables.md)、[最终验收](entry_method_exploration/20260911_gt10_mechanism_v1/reviews/final_audit.json)。原第3节的阶段要求与完整启动指令保存在[E27修改前快照](entry_method_exploration/20260911_gt10_mechanism_v1/source_before/s-target.md)，不据旧指令重跑。

### 3.2 尚未解决的具体问题

1. 真实多目标对应与一般支持/平滑分别贡献多少，仍未完全分离；一个shuffle不是完全匹配控制，也不证明任何GT1平滑都不行。现有结果足以保留目标相关分配，不必把它包装为普遍因果定理。
2. 画像几何分数与实际finite-L三入口作用仍有错位。query相同而L变动可正负切换；ESS、角位移和覆盖分层也不稳定，尚没有已验证的简单选择规则。
3. 跨query分布/独立构建以及目标Recall区间的严格实测前沿尚未验证。Yandex原速度幅度不应成为下一实验的确定收益前提；路径/cache等未测项不补写故事。

### 3.3 下一阶段如何选择

建议保留query相关多目标分数归属和每query质量1，围绕剩余的有限L效用代理缺口定义下一问题。若用户选择2A，先按4.1核对旧标签兼容性及与旧赢家centroid的实质区别，再冻结软/硬画像对照与独立协议；本轮尚未证明这类效用可预测或可学习。

其它分支仍按第4节保留：3A必须先说明约1%量级路由占比下的完整wall目标；聚类替换需要支持/单峰证据；rank比较需要固定目标和标签。每次只进入用户明确指定的一条，选择之前不启动训练、ANN重建、标签、搜索或held-out。原GT10不需要满足E25/E26的75%/25%增强门槛，也不要求每query/L都受益。

## 4. 机制分析之后保留的方法方向（均须单独指定）

| 优先级 | 方向 | 进入条件和区别 |
|---|---|---|
| 第3节已完成 | GT10收益机制分析 | E27归因及限定补测已收口；作为后续选择证据，不重跑 |
| 1，E24已完成收口 | 固定H的GT-topK软画像 | 隔离目标归属；与旧GT1 basin内增加两个mode、多seed多view、single赢家centroid不同 |
| 2，较重备选 | 以真实finite-L作用组织分组或在小GT候选集挑入口 | 若主线显示几何代理仍有缺口，再定协议；度数只作特征，三入口用真实联合搜索。旧centroid/rerouter已有真实效用，须说明新条件作用/可预测分组差别 |
| 3，效率支线 | 固定W，成对拉伸并重建Micro-HNSW | `p′=Ap,q′=A⁻ᵀq`，优先受限正对角A；先验评分一致，再看导航和总wall。不能变换后逐画像归一化；不重建边时保分数变换不会改变理想搜索路径 |

依据第3节已完成的GT10机制分析，由用户确定后续方法分支。原有方向分别改善画像目标、真实入口作用和索引导航，应独立对照后再决定组合；E24的局部收益保留，不能因后续增强未通过便跳过其原因分析。除E24已完成外，下面其它方法分支尚未执行，也不构成一张自动全部跑完的实验队列。

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
| GT10硬优于GT1硬，软分配无额外收益 | 使用E27已确认的分解与未解决项，再决定一个具体方法 | 软分配、复杂聚类器或有监督分组必然更好 |
| 软画像的exact选择有收益，HNSW部署明显损失 | 保留画像，独立研究微型图导航/成对拉伸 | 精确画像top3等于最优真实入口 |
| exact与HNSW都无收益，但现有H效用空间仍大 | 优先真实搜索作用分组/条件三入口评分 | 必须先换新H或重建NSG |
| 现有H的受限候选覆盖不够，而新GT候选有实质作用 | 定义固定H预算的入口替换实验，连同路由学习一起测 | 新候选oracle提升已经可部署 |
| 学习模型fit更优而cal/audit更差 | 在同目标下研究rank/正则及可预测性 | 继续增加rank或MLP一定有效 |
| 画像支持薄弱或单峰假设明显不合适 | 比较一种有支持约束的聚类器或vMF | 离线簇更均衡/似然更高就是Recall–QPS提升 |

优先次序不替代具体证据。每个实际运行版本都先锁自己的参数/预算/停止条件；本节保留全部讨论方向，E24已经结束；后续按用户明确选择进入2A/3A/聚类/rank等独立分支，不默认复跑第一方向。

Micro-HNSW是约800个画像的小图，主搜索仍为NSG。以后若改NSG须新图身份并重建受影响标签/评测。旧E22大矩阵不恢复；C保持`NO_GO_UNCONDITIONAL_HEADROOM_STOP_C`，不自动启动C3/C4、联动、D或效用树。所有旧源码、图、GT、标签、模型、日志和结果保留。

## 5. 新对话应定位的代码与证据

- 阅读顺序：[AGENTS.md](AGENTS.md)→[summary.md](summary.md)→[spec.md](spec.md)→本文件→[s-experiment.md](s-experiment.md)。
- E27已完成：[机制报告](entry_method_exploration/20260911_gt10_mechanism_v1/report.md)、[历史16](experiment_history/16_gt10_mechanism.md)、[补测协议](entry_method_exploration/20260911_gt10_mechanism_v1/supplement/protocol.md)。原E24来源继续保留：[E24构建源码](entry_method_exploration/20260910_gt_topk_profiles_v1/src/build_profiles.py)、[支持统计](entry_method_exploration/20260910_gt_topk_profiles_v1/results/profile_support.csv)、[近似/精确对照](entry_method_exploration/20260910_gt_topk_profiles_v1/results/ann_diagnostics.csv)、[原始全部指标](entry_method_exploration/20260910_gt_topk_profiles_v1/results/metrics.csv)；E27已按两数据集GT10硬对GT1硬完成连接。
- 已完成E26：[报告](entry_method_exploration/20260910_profile_shrinkage_v1/report.md)、[协议](entry_method_exploration/20260910_profile_shrinkage_v1/protocol.md)、[固定选择](entry_method_exploration/20260910_profile_shrinkage_v1/models/frozen_before_audit.json)、[历史15](experiment_history/15_profile_shrinkage.md)、[用户收口更新](entry_method_exploration/20260910_profile_shrinkage_v1/authorization_update.md)。
- 已完成E25：[协议](entry_method_exploration/20260910_selective_profile_gate_v1/protocol.md)、[固定选择](entry_method_exploration/20260910_selective_profile_gate_v1/models/frozen_before_audit.json)、[完整报告](entry_method_exploration/20260910_selective_profile_gate_v1/report.md)、[历史14](experiment_history/14_selective_profile_gate.md)。
- 已完成第一方向：[E24完整报告](entry_method_exploration/20260910_gt_topk_profiles_v1/report.md)、[协议与预算](entry_method_exploration/20260910_gt_topk_profiles_v1/protocol.md)、[冻结选择](entry_method_exploration/20260910_gt_topk_profiles_v1/models/frozen_before_validation.json)；全部消融及负点保留。
- 当前研究：[四问题报告](entry_method_exploration/20260910_ood_hubs_clustering_router_research_v1/report.md)；代理/入口/微型图差距见[E20历史08](experiment_history/08_fast_router_diagnosis.md)及其原始分析。
- 历史边界：[效用与表示04](experiment_history/04_utility_and_representation.md)、[reroute05](experiment_history/05_probe_reroute.md)、[E23历史12](experiment_history/12_three_entry_rank_exploration.md)。有疑问沿卡片到原始证据，不必重做整轮文献调研。
- 原画像实现：[builder](benches/run/build_fast_entry_variants.py)的`choose_unique_gt_hubs`与`build_gt_basin_prototypes`；新方法放独立版本。
- 输入身份：[E23 prepare_fit.py](entry_method_exploration/20260910_three_entry_rank_v1/src/prepare_fit.py)和其`inputs/<dataset>/<split>/config.json`。GT实际保留100列，读取时核对形状、字节数与row_ids；旧准备器还会读取single标签并生成组合，不能整段照跑来准备本次闭式画像。
- 单线程评测：[E23 protocol](entry_method_exploration/20260910_three_entry_rank_v1/protocol.md)、[evaluate.cpp](entry_method_exploration/20260910_three_entry_rank_v1/src/evaluate.cpp)、[最终验收](entry_method_exploration/20260910_three_entry_rank_v1/reviews/final_audit.json)。复用需绑定新版本的源码/可执行文件/输出身份，不覆盖E23。

## 6. 下一次对话启动指令

GT10机制分析及限定补测已经完成；不再复制旧“启动第一方向”或“开始GT10机制分析”指令重跑。原接续完整版本保存在[E27修改前s-target](entry_method_exploration/20260911_gt10_mechanism_v1/source_before/s-target.md)。

```text
工作目录 /data/netg/ACSG。
完整阅读AGENTS.md、summary.md、spec.md、s-target.md、s-experiment.md，
沿历史16读E27完整机制报告、既有A–C证据、补测协议、原始结果与成本；
需要核查原GT10时再沿历史13，E25/E26沿历史14/15。
E27已收口：两个局部正点在exact3下保留，WebVid小幅速度复现，
Yandex原速度幅度未稳定保留；信息与一般平滑尚未完全分离。
先核对本次用户明确指定的下一分支；若未指定，仅复盘和讨论选择，不启动实验。
若指定2A/3A/聚类/rank之一，按第4节完成兼容性和差异核查，
冻结独立协议、候选、输入身份、硬预算及停止条件后，仅执行该分支。
保留matched GT1 hard、GT10 hard及原冻结soft对照，区分Fast与NSG的既有增益。
所有正式查询单线程、每次一个方法、独立纯端到端wall；trace/count在timer外。
历史validation使用如实披露，不当新盲测；held-out和新模型大网格不自动开启。
保留旧资产，不挪用E24–E27旧预算；结果同步对应文档。
```

| 可指定的分支 | 启动前必须明确 |
|---|---|
| 真实效用分组2A | 固定H，核对旧single/triple标签兼容性及与旧赢家centroid的区别；保留硬/软画像对照，再定协议 |
| 微型HNSW拉伸3A | 固定matched Fast20K W，受限正对角成对变换；先评分/身份恢复，再建图测完整wall，不改NSG |
| 聚类替代 | 先确认支持/单峰问题，固定目标和输出预算，只选一种备选；不同时改变H、画像和路由 |
| rank容量 | 先固定同一目标与兼容标签，比较rank4/8/16/32与Full；cal联合选rank/λ，不扩大其它变量 |

这些是保留选项，尚未被本轮选择或执行；GT10机制分析完成不会自动开启任何分支。
