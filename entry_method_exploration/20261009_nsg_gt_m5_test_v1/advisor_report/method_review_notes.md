# GT10 与 M5：方法事实核实和导师报告表述边界

审阅者：/root/retest_contract。范围：既有源码、配置、冻结训练表元数据、历史文稿及文末三个一手论文的相应段落；未运行 native、未读取本次 E173 正在产生的质量输出、未读取新测返回数组。本文供报告作者核对方法，不是新的性能结论或新颖性认证。

## 1. 可以向老师明确说明的研究问题

**GT10研究如何把目标侧监督转成查询侧的真实图入口选择；M5研究如何利用同一已付路由状态，以受限输出候选容量补偿有限图搜索的遗漏。**

两者针对检索链的不同环节。GT10改变初始入口分布，仍由原图搜索发现最终目标；M5保留GT10的入口和主图搜索，额外候选在主搜索正常结束后进入最终结果。研究价值应来自目标、路由、有限图响应与完整费用之间可证伪的联系，而不是使用小图、hash表、greedy或heap本身。

可用的学术问题表述是：

> 在固定底图、评分核和主搜索预算下，目标监督是否能形成比原始节点几何更有效的查询入口画像？给定已取得的路由状态与有限预算搜索响应，联合残差候选分配是否能比完整GT频率候选、独立行频率候选和更大搜索预算产生更好的完整Recall–QPS关系？

第一句属于GT10，第二句属于M5；“是否”仍需机制与实际性能证据回答。

## 2. GT10的精确方法事实

设真实base hubs为 h_j，u_j=unit(base[h_j])；拟合查询X_i=unit(q_i)，其精确前十目标ID为t_i1,…,t_i10。

### 2.1 H不是虚拟聚类中心

现行QGT-Cover在独立5K QGT查询上做球面k-means。每簇按查询对该质心的cosine相似度排序，再按代表查询的GT100名次取第一个全局未使用真实base ID；不足时扫描GT补齐，最终真实ID排序。Web H=815，Yandex H=821。它是启发式真实入口选择，不能写成严格最小集合覆盖、全局最优H或由簇质心直接GT1得到H。

### 2.2 GT10归属与画像

对真实目标t，hard归属：
w_j(t)=1[j=argmax_l unit(base[t])·u_l]；
同分按已有真实ID列序。

soft归属：
w_j(t)=exp(c_j(t)/T)/Σ_l exp(c_l(t)/T)，
c_j(t)=unit(base[t])·u_j。
实现使用减最大值的stable softmax。

每个查询对hub的权重为
a_ij=(1/10)Σ_{r=1}^{10}w_j(t_ir)，因此Σ_j a_ij=1。

最终画像为
m_j=u_j+Σ_i a_ij X_i，
p_j=m_j/||m_j||。
这是一份query方向画像，标签由真实target–hub关系得到，不能称为直接复制目标向量或学习新的base embedding。已有实现使用float32单位化/目标打分，GT10权重及画像合力以float64聚合、float32导出。该数值实现与理想公式须区分。

### 2.3 训练/构建和在线

GT10现行画像fit为20K查询，精确GT100容器的前10列参与画像；独立QGT5K负责真实H选择。没有SGD、MLP或图搜索效用标签作为GT10画像训练目标；有精确GT监督、聚类和闭式画像构建。

Web默认GT10-soft-t1；Y默认GT10-hard。t1指三档温度中的中档，不是T=1。现有Web中档T=0.016201138496398926，由同批fit GT1目标对所有单位hub的第一/第二cosine分数差中位数确定，带10^-4下界；三档为T/4、T、4T。Y-hard不依赖温度。

在线原始query进入已有画像Micro-HNSW，efSearch=10、取3个真实hub ID，然后原raw query进入相同NSG、原raw-IP与原L。E173/M5当前原生路由保持实际maxheap-pop次序，不应在报告中写成精确全H top3或自动升序的三个入口。Micro-HNSW是近似检索；构建阶段的query单位化不代表线上额外改变底图metric。

### 2.4 有限的理论结论

固定a与H且m_j非零时，上述p_j解球面线性代理
max_{||p||=1} [u_j·p+Σ_i a_ij X_i·p]。
这是Cauchy–Schwarz给出的闭式最优；不是对H、soft/hard权重、实际HNSW路径、三入口联合图搜索、Recall或QPS的全局最优。

GT10十rank共享一个query，不能把它们当十个独立样本并声称方差缩小十倍。rank相关性、GT1与tail目标方向偏差、画像第3/第4得分间隔、小图近似误差和有限图可达性均影响最终行为。

## 3. M5的精确学习目标与部署

### 3.1 它明确基于GT10

每个数据集冻结同一GT10画像/小图/真实H。训练用原GT10实际top3标签J_i和两个真实lower-L主搜索返回R_i,1、R_i,100；令M_i,K=G_i,K\R_i,K。当前构表监督来自原20K discovery/fit，历史已曝光，不是E173公开测试。

原M5构表预算为：Web K1/L800、K100/L1000；Y K1/L100、K100/L200。E173的L200/400/800/1000/1200曲线使用同一冻结表，没有按新L重新训练。因此新曲线考察的是固定表跨搜索预算的行为，不是每个L各自最优的残差表。

### 3.2 联合覆盖目标

选择posting pair集合A⊆{(j,t)}，每行至多b=8个不同真实target ID。原实际容量总上限8H；同一target可复制到不同hub行。一个查询的候选并集C_A(q_i)来自其已选三行，至多24个ID。

离线目标为

F(A)=(1/N)Σ_i[(1/2)|M_i,1∩C_A(q_i)|+(1/200)|M_i,100∩C_A(q_i)|]。

它对两类遗漏的归一化coverage代理使用各1/2权重；不能误读为K1与K100遗漏成员的未归一化等权，也不能写成直接优化最终两个真实Recall指标。更不能用K1增益抵消K100损伤作为线上结论。

源码将每个(query,target)合并为一个token，精确整数权重为

100·1[t=GT1_i且t不在R_i,1] + 1·1[t在GT100_i且t不在R_i,100]。

所以同一GT1若两种请求都遗漏，token权重101；仅K1遗漏为100；仅K100遗漏为1。token由任一实际共选行中的(j,t) pair覆盖一次，多个行覆盖同一token不重复收益。整数目标与F相差正比例200N，不改变greedy序列。

必须单独定义实际收益：令O_i,K(A)为按真实runtime重评分与rank merge得到的最终K个ID，Δ_i,K(A)=(|G_i,K∩O_i,K(A)|−|G_i,K∩R_i,K|)/K。一般不能令F(A)=(1/(2N))Σ_i[Δ_i,1(A)+Δ_i,100(A)]：C_A包含某遗漏target，只说明它被供给，不能保证它在native score、等分规则与其它候选竞争之后进入最终返回；重评分还可能改变原R的排序。该等式只在各K的官方GT与native评分/排序严格一致、所有GTK严格优于non-GTK等充分条件下成立。它还分别依赖K1/K100旧teacher基线，并不是同一L或本次五档L的真实联合效用目标。

### 3.3 实际greedy定义

候选pair只来自训练实际路由行与真实missing target。每步从所有尚可加入的pair中，选择尚未覆盖token整数权重总和最大的pair；每行cap8；平局按(slot,target真实ID)升序；边际不正则停止。实现是lazy-heap精确重算边际，不是每行独立选最频繁8个。每行导出顺序保留全局选择日志的到达顺序，在线按原实际heap-pop labels读三行。

已有独立audit用token-to-edge增量扣减重放全部TRAIN选择和全局tie，算法不同于compiler的lazy incidence recount；其证明范围是已有TRAIN greedy选择恢复，不能扩大为实际QPS、泛化或目标排序定理。

### 3.4 在线和费用

M5先正常执行与GT相同的路由与固定L主搜索，再从三行读最多24个ID，去掉R内与候选之间的重复。目标向量仍从原base取，没有另存一个新向量模型。若候选非空，对R所有有效ID及候选统一用当前原scalar评分对象重评分，按真实raw-IP结果合并到top-K。

incoming只有严格优于当前最差score才替换；等分incoming被拒，不能把它写成按真实ID重新定义全局GT tie。原R成员的arrival priority及候选读取次序用于heap内同分稳定规则。空表/无有效候选直接返回原R。

最多额外K+24次点积，因此K100费用上限不是仅24个点积。查表、冲突fallback、去重、重评分、merge及输出生命周期全部须进入wall；原已付router可共享，但不能免费把主搜索结果与画像距离直接解释成目标score。

冻结表磁盘payload：Web53099 bytes、Y53369 bytes；manifest的payload+4096 scratch预留分别57195/57465 bytes。这不是完整线上进程内存或所有动态分配的最终实测值；runtime另核resident_bytes≤128KiB。两份compile_manifest的16.40/19.31秒只计已有训练返回/GT之后的构表，不是完整训练成本。

## 4. 理论边界与创新性边界

F是标准非负加权coverage，故单调、次模。每行cap是partition matroid；另加pair总容量是其截断，当前8H总容量在每行cap8下冗余。实际lazy heap精确恢复最大可行边际；停止时若存在零边际可行元素，可在证明中零收益补齐而不改变目标值。因此当前训练coverage设定可套用单个matroid最大边际greedy的标准1/2近似；不是简单cardinality约束常见的1−1/e，也不是自创定理或真实Recall保证。报告主文可以仅说“适用标准次模优化理论”，把常数与条件放附录。本方法未实现更强的连续greedy优化。[Golovin–Krause §1–2.1回顾的经典结果](https://arxiv.org/pdf/1101.4450)

覆盖等于实际新增Recall，需要共同native排序/评分且所有真实GTK严格排在non-GTK之前等前件。只有理想覆盖或真实分数弱分离不足以排除等分到达顺序、GT/native排序差异的影响。即使训练覆盖代理最优，也不保证新查询Recall、固定表跨L行为或QPS。

降低L一般节省主图成本，补全试图支付由降L引起的质量债务；同L补全一般增加工作量。是否综合提高，必须比较每个真实完整工作点。不能把低L配置的速度与较高L配置的Recall拼成同一个方法成绩。

本地已存前作审阅指出：
- GATE已经覆盖固定底图、候选/真实hub选择、小索引和query监督入口学习的一部分架构；“用小图选择入口”不能直接申报首创。
- SPANN已有head→posting、共选posting重叠处理、真实候选评分与合并。
- Hyvönen等JMLR2024 multilabel natural classifier已有query区域内GTK频率→候选、聚合和精确评分，比仅SPANN更接近M5的监督posting。
- SIGIR2024 MIPS learnt-IVF已有GT→路由分区监督；GT监督与候选分区组合本身不是新颖性。
- 本地E61已有遗漏目标监督；E14已有结果union；165/166已有目标侧检索。因此M5可申明的差异仅是固定默认已经取得的路由标签、有限beam residual teacher、共享双K联合容量分配、输出侧补全及预算补偿这一明确合同，尚不能从组合推出发表所需创新性。

SPANN、JMLR2024与learnt-IVF的边界来自已有本地原文/源码审阅，本轮没有重新打开这三项外部论文；GATE、Faiss与标准greedy结果本轮另核一手来源，见文末。这里不是完整相关工作核验。正式稿应按原论文/官方代码重新定位贡献，不使用未核对的“首次”“现有工作均未考虑”等排他断言。

## 5. 防止报告偏工程化的证据组织

主文先给出研究问题、目标监督与有限响应的失配、上述两个精确数学对象及可证伪预测，再描述实现。hash表、128KiB、16probe、缓冲释放等只用于说明部署费用可信，应放实现/复现段或附录，不应代替贡献。

最有判别力的机制对照是：
1. GT10 vs GT1/原raw-hub画像：区分十目标聚合与纯几何入口。
2. M5 residual_joint vs allgt_joint：同联合优化器下只改变missing监督，隔离“残差”是否必要。
3. residual_joint vs missing_frequency：同残差监督下只改变共选行联合去重，隔离“联合覆盖”是否必要。
4. M5 vs更大L默认/全局目标频率/同U小目标索引：隔离额外输出候选是否值得支付费用。
5. empty/rescore-only：区分wrapper成本、全R重评分与真实候选补全。

这些是论文证据结构，不是本轮追加实验授权。E173只测NSG/GT/M5三方法五L，能给出公开测试上的完整工作点行为；即使有增益，也不足以单独证明residual teacher或joint greedy优于最接近监督posting控制。已有历史控制结果可如实列为历史证据，但不能冒充本次同轮公开测试。

## 6. 应规避的表述与替代表述

|应规避|可以使用|
|---|---|
|GT10最优入口/全局Recall最优|固定权重的球面线性代理有闭式画像最优解；实际有限搜索效用待实证|
|十目标等于十倍独立样本|十rank平均可能平滑归属，但有同query相关性与rank偏差|
|GT10软温度t1=1|t1是中档median-gap温度；当前Web数值T≈0.0162011|
|M5只是调L/加缓存，所以无研究问题|M5有明确有限响应残差目标和受限联合候选分配问题；是否超过标准监督posting尚待证明|
|M5创新就是hash表/union/次模greedy|这些是已有工具；贡献必须由残差相对完整GT监督的必要性及真实性能联系支撑|
|M5天然无损/coverage就是真实Recall|两者只在GT/native严格排序等条件下等价；实际需独立评分与报告增损|
|greedy有1−1/e保证|当前partition-matroid最大边际greedy适用标准1/2代理近似|
|M5只多24次评分|候选非空时保守RESCORE至多K+24次评分，完整费用另含lookup/dedup/merge|
|构表16/19秒就是完整训练时间|这里只计既有GT与搜索返回后的posting编译；监督与真实搜索费用另列|
|本次公开测试就是未曝光盲测|公开测试历史已曝光，但训练/测试互斥；本次为冻结模型实际复测|
|目前已证明整体优于GT/可以发表CCF B|本次结果与必要机制/前作区分逐项报告；不预设性能或发表充分性|

## 7. 已直接读取的证据

- GT真实H选择：/data/netg/ACSG/benches/run/build_fast_entry_variants.py，choose_unique_gt_hubs。
- GT权重与画像：/data/netg/ACSG/entry_method_exploration/20260910_gt_topk_profiles_v1/src/build_profiles.py，profile_from_weights及candidates分支。
- GT温度：同目录src/initialize.py第97–114行及config.locked.json。
- GT数学与有限beam条件：/data/netg/ACSG/entry_method_exploration/20261002_gt10_paper_theory_v1/algorithm_and_falsifier.md。
- M5实际目标/导出：/root/acsg-e172-storage-v2/campaign/m5/compile_postings.py。
- M5独立greedy审计：/root/acsg-e172-storage-v2/campaign/m5/audit_train_greedy.py。
- M5冻结训练范围与anchor：/root/acsg-e172-storage-v2/campaign/config.locked.json。
- M5表容量及阶段费用：上述m5/models/{webvid2_5m_light_v1,yandex_t2i_official10M_ip_v1}/compile_manifest.json。
- M5在线语义：/root/acsg-e172-storage-v2/campaign/m5/runtime.hpp及runner_v9.cpp；E173src/runtime.hpp只改include，src/native.hpp与原件逐字相同。
- M5理论/前作边界：/data/netg/ACSG/entry_method_exploration/20261002_overnight_algorithm_audit_v1/residual_output_postings_method.md。

未读取E173新质量指标、正在产生的返回packet或当前性能日志。报告作者须在全部实际复测完成后另核数值，不能用本文替代结果审计。

## 8. 本轮额外核实的一手参考及可支持的范围

- [GATE: Empowering Graph-based Approximate Nearest Neighbor Search with Adaptive Awareness Capabilities](https://arxiv.org/html/2506.15986v1)，§4及§4.1：已经在底图上加入自适应高层导航，采用base平衡聚类后选簇中心附近真实hub，再用结构/历史query信息和two-tower学习导航。GT10的QGT真实H选择、目标归属和闭式query画像与它不同；这支持具体机制差异，不能支持“query-aware入口导航首次提出”。其性能数值与GT10没有当前同核同预算复现，不直接引用为性能优劣证据。
- [The Faiss Library](https://arxiv.org/html/2401.08281v1)，§3.4–3.6：明确以速度–准确率Pareto工作点比较搜索配置，也描述shortlist后准确评分的既有refining模式。它支持报告的工作点比较与精确补全并非独有工具；不能据此推出M5的残差posting目标已被原文完整实现，或用候选coverage替代最终Recall。
- [Golovin–Krause, Adaptive Submodular Optimization under Matroid Constraints](https://arxiv.org/pdf/1101.4450)，§1–2.1：回顾经典非自适应最大可行边际greedy在p个matroid约束下的1/(p+1)近似，引用Fisher等旧结果；其论文新贡献是自适应扩展。M5构表属于固定训练coverage的非自适应设定，引用时应明确是经典理论适用，不把自适应定理或经典保证冒充M5原创。
