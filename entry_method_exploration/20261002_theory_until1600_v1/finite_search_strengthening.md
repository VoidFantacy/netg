# 有限图搜索的局部保留、相对损伤与不可识别边界

2026-10-02下午理论研究，终稿v1（15:37，UTC+8）。本文仅手推证明、解析反例、只读原论文和静态源码；不执行真实或合成搜索、枚举、模拟、旧数组统计、训练、构图、GT或向量评分。上午产物已封存，本文不修改它们。所有结论都是带前件的数学陈述，不是线上GO或已验证性能收益。

**主要加强是局部 ID 保留证书。** 它用已经到达的完整 pool、一个有完整边界信息的局部区域及全 native 路径有效的分数上界，代替未知全库 top-L 集合。该证书允许 ties，也不要求官方 GT 与 native 分数同序。代价是必须已支付搜索前缀、知道完整边界与可靠上界；这些信息及证书核算没有免费来源。它不能给当前未执行的三入口方法一个先验收益保证。

## 1. 合同与记号

固定 q、底图及邻接顺序、主核、实际 K/L、初始化、visited、展开和自然停止。L 指实际容量：生产 E99 为 max(search_L,K)，E166 的工作点满足 L≥K。实际 seed 消费数不超过 min(3,L)，且为合法非空、不同 ID；不能把传入但未消费的入口算入证明。

为方便上界，以下使用**越大越好的 native 存储分数** σ(v)=−candidate.distance。当前主图 E99/E166 经 `storage_distance_computer` 使用 FAISS `NegativeDistanceComputer` 包住 `FlatIPDis`，因此 distance=−IP_native、σ=IP_native；标量解析构造 x=σ 与 q=1 相符。HNSW router 的 callback 才为 distance=1−IP_native，不能把这个 offset 带到 NSG。[主图包装](/data/netg/ACSG/ACSG/ACSG.cpp:35)、[FAISS negate](/data/netg/ACSG/faiss/faiss/impl/DistanceComputer.h:77)、[FlatIPDis](/data/netg/ACSG/faiss/faiss/IndexFlat.cpp:176)、[HNSW callback](/data/netg/ACSG/entry_method_exploration/20260930_theory_until2200_v1/research/target_bank_frozen_curve_v1/src/common/hnswlib/space_ip.h:18)。

每个节点第一次实际评分后，其存储值在这次执行中不再重算或修改。不同执行/评分路径可得不同数值；主证书不假定一个全库共同排序。所有合法分数必须有限，distance 低于 empty sentinel，排除 NaN、overflow、sentinel fallback。

状态只能取实际可达的**完整邻接行边界**：

- 当前 pool P 含 L 个 distinct ID，已满且按实际比较规则排序；P⊆D。
- D 是已经完整评分的 visited ID 集合。visited 在评分/拒收前标记，永久保持；已评分而不在 P 的节点不会重新插入。
- pool 的非 pending 节点已经完整展开其邻接行；剩余 pending 按原规则继续，直到自然终止。
- 原 cursor/rewind 不变量成立：不能用手工 cursor 跳过更靠前的 pending。继续阶段和返回没有新增 tie re-sort。
- 不允许 batch 中间“已标 visited、尚未评分”的假状态，不允许强制无评分标记、额外 cap、早停、visited reset、或此后注入随机补点。

这组前件来自上午已审合同，不将任意手工数组称为合法 state。[E99 初始化与主循环](/data/netg/ACSG/ACSG/ACSG.cpp:1528)、[E99 评分和插入](/data/netg/ACSG/ACSG/ACSG.cpp:1614)、[E166 核](/data/netg/ACSG/entry_method_exploration/20260930_theory_until2200_v1/research/target_bank_frozen_curve_v1/src/kernels.hpp:28)、[pool 比较与插入](/data/netg/ACSG/ACSG/detail/CandidatePool.h:13)。

令 β=min_{u∈P}σ(u)，即当前 **L-th cutoff**。由于 pool 已满，未来只插入能竞争当前 cutoff 的节点，β 只能非降。这个数值单调性只用本次执行的存储值，不用跨 scalar/batch4 的共同节点顺序。ties 的具体处理仍由原代码决定。

## 2. 命题 A：局部 eligible 区域封闭

取一个有限 ID 区域 C，P⊆C。可将最初 D\P 中已经丢弃的节点排除在 C 外。记 P_pending 为初始 P 中的 pending 节点；只需已知 **F=P_pending∪(C\D)** 的完整原邻接行。初始 P 中非 pending 行已经完整展开，此后不会再次展开，故不需要为了此证书重新读取其行。对每条出口边 u→v，u∈F、v∉C，若 v∉D，则具有覆盖此后所有合法 native 评分路径的上界 U_v，且

    U_v ≤ β。

已在 D\P 的出口节点不需上界，因为永久 visited 且不会重入。

**结论：** 此后所有被接受的节点、所有实际展开的节点都在 C 内。C 外可能被评分并拒收，费用并未消失。

**证明。** 初始 pending 都在 P_pending⊆C。之后未来展开只能来自初始 P_pending，或在初始 C\D 中被新接受的节点；初始 D\P 永不重入，P 中已完成的行也永不再次展开。归纳展开的节点 u∈F：指向 C 内的接受不会离开 C；指向 C 外且初始已 visited 的节点跳过；其他 C 外节点首次评分时 σ(v)≤U_v≤β≤当时 cutoff，因此拒收并永久 visited。故任何新 pending 仍在 C。归纳直到自然停止。只看初始 D 足够：之后新标记的 C 外节点均已被拒收，不可能成为新的入口。□

等号依赖当前实际核的 full-pool guard `distance>=worst.distance` 直接拒收（即 σ≤cutoff 拒收），不是通用 beam tie 合同。若接收规则改为允许边界等值入池，须退回严格 U_v<β。未满 pool 不适用任一版本。

这是一个**执行继续过程的局部封闭条件**，并不要求 C 是全图闭子图；出口可存在，只要未来可能展开行的未 visited 出口上界不高于已满 pool 的 L-th cutoff 且实际核拒收等值。不是几何距离更近或 raw-target affinity 更高的条件。

**如何定义一个先于 suffix 的保守 C。** 数学上可从初始 P_pending 出发，沿初始尚未 visited 且 U_v>β 的出口递归纳入节点，未知上界视作 +∞；附上全 P。每个纳入的新点要有完整行，已 visited 点不用递归，外围出口都有 U_v≤β。所得 guard-closure 是尚余可能被接受区域的上包络，满足 A，且不同于执行后的 B_L。本文没有执行这项遍历/枚举，也没有实现 runner。若上界松或 metadata 缺失，它可扩到全库；这只是明确条件信息的获取问题，不能将“存在一个 C”写成免费特征。

## 3. 命题 B：局部 native ID 保留与相对 Recall 损伤界

在命题 A 的状态和区域中，取当前 v∈P，使用其实际存储值 σ_v。定义不同 ID 的潜在威胁集合

    T_v = {u∈P\{v}: σ(u)≥σ_v}
          ∪ {u∈C\D: U_u≥σ_v}。

其中 U_u 同样须覆盖全部未来合法评分路径。初始 D\P 的节点已永久丢弃，不计威胁；当前其他 pool 节点使用已经固定的实际存储值，无须用松上界替代。所有等值点都计入，避免假定 tie-ID 规则。

如果 |T_v|<K≤L，则 v 最终必在返回的 K 个 ID 内。

**证明。** 此后能够新进入 pool 的节点都在 C\D；只有 U_u≥σ_v 的节点才可能在存储值上不劣于 v。当前其他 pool 中潜在不劣节点也全部计入 T_v。每个 ID 最多插入一次，故整个继续过程中最多 K−1 个不同 ID 可能排在 v 前或与其同分。若 v 被淘汰，需存在 L≥K 个不劣于它的其他 pool ID，与该计数矛盾。因此 v 一直保留，且终局至多 K−1 个其他 ID 可排在其前，必入 top-K。证明既不要求 GT 同序，也不要求跨路径数值相同。□

**相对损伤推论。** 令旧默认同 q 返回 B，|B|=K 且 ID 不同；令 W⊆B∩P，W 中每个成员都通过上述保留证书。新执行最终返回 A，则对任意合法 GT 集合 G_K(q)，包括含 canonical ties 的 GT，均有

    Recall(A)−Recall(B) ≥ −|B\W|/K。

因为 W⊆A，旧命中最多从未保护的 B\W 中损失。这个推论不假定 GT/native 一致排序。若 W=B，则 A=B（两者均 K 个不同 ID），相对 Recall 差为0；不据此声称绝对 Recall=1、输出距离 bits 相同或 wall 相同。

若另有 **已合法获知 GT 成员身份** 的 N⊆G_K\B，且 N 的每个 ID 也在当前 pool 并通过证书，则

    Recall(A)−Recall(B) ≥ (|N|−|B\W|)/K。

这个粗界仍不能证明严格正增益：W 与 N 均在 K 个返回槽中，|N|≤K−|W|=|B\W|，右侧必≤0。把该下界称为“strict改善证书”会漏掉容量约束，本文自审已纠正。

要得到非空的严格改善条件，须再合法知道未保护旧 ID 中的 nonhit 集合 Z⊆(B\W)\G_K。此时

    Recall(A)−Recall(B) ≥ [|N|−(|B\W|−|Z|)]/K。

或若已知旧实际命中数 h_B 及受保护旧命中数 h_W，则下界为 (|N|−(h_B−h_W))/K。K2 的解析非空例为 B={旧GT,旧nongt}，保护旧GT、已知旧nongt身份，同时保护一个新GT，得到 +1/2。保护全部旧正确成员并加入新正确成员可以严格改善；保全部旧返回 IDs 则已占满 K，不能再加新成员。GT/nonhit 身份是额外真值前件，本文没有读取新 GT 建立 N/Z/h；raw target、hub 标签或更大分数不能代替它。

**非空性与费用。** 解析例 K=1、L=3，当前完整 pool 的存储值为 g:10、p:8、t:7，C=P，所有未 visited 出口都有已证 U<7，则 g 无威胁，必保留。若旧 B={g}，即使 g 已是全局真 GT1，该证书也可保其 ID；不同于后文严格逐位 score 提升条件，它不要求存在比 GT1 更高分的点。但这只是手设的非空例，不说明真实 graph 上边界上界可得或频繁成功。

旧 B 的获得、候选前缀、完整 C 邻接读取、上界 metadata 与核算都有成本。没有同 q 缓存时，先运行完整默认取得 B 通常已经付掉主要费用；这是离线 teacher/响应分析条件，不能自动变成更快的线上 gate。保留 Recall 标签的证书不能省略原 suffix 的正式费用测量，也不能改变当前固定自然停止合同。

### 3.1 当前有序 pool 的 ties 加强

当前 `insert_into_pool_live` 只插入新点、memmove 幸存旧点、淘汰尾点；继续阶段及输出都不再按新的 tie-key 重排幸存旧 ID。记 pos_P(v) 为 v 在当前实际有序数组中的位置。可以将命题 B 的威胁集合收紧为

    T_v^ord = {u∈P: pos_P(u)<pos_P(v)}
              ∪ {u∈C\D: U_u≥σ_v}。

若 |T_v^ord|<K，则同样保证 v 最终返回。当前与 v 同分却排在其后的旧 ID 不会跨过 v，故不计；新点仍把所有潜在等值都算威胁，不能推定其插入 tie 位置。证明用“v 尚未删除时，它之前只能是初始 ahead ID 或潜在新威胁 ID”的归纳。其位置始终至多 K≤L，故不可能被删尾淘汰；终局仍在前K。

这是对**已有物理顺序**的保留证书，不要求全局 canonical tie-key，也不表示同 pool ID、不同初始 tie 顺序响应等价。例如 K1/L3、有序 P=(v,p,t) 且三者存储值均0，C=P、所有新出口 U≤0：原核均拒收新点，T_v^ord 为空而保护 v；无序 ≥ 计数会给2而不能认证。这是解析非空例，不是当前数据 ties 频率。

**当前原 helper 的进一步 FIFO 收紧。** 合法有限新分数低于 sentinel、无重复 ID 时，若新点严格优于 best，front 特判插最前；否则 full-pool guard 已排除与 worst 相等/更差，或未满池的最右槽为 sentinel。二分初始 left 值≤新 distance、right 值严格更大，循环将 right 定位到第一个严格更大 distance；backward duplicate 检查只改 left、不改 right。因此新等值节点插在已有等值组之后。依赖这一实际实现，可以将未来项进一步改成

    T_v^FIFO = {u∈P: pos_P(u)<pos_P(v)}
               ∪ {u∈C\D: U_u>σ_v}。

|T_v^FIFO|<K 保证 v 返回。未来实际同分节点不会越过已有 v，初始 behind 也不会越过；仍按位置上界归纳。这不是任意 tie 插入器的保证。对尚未发现的节点没有先到优势，下面 Q_j^loc 必须保留 ≥ 威胁计数。

### 3.2 局部 safe-path：保护尚未发现的 ID

命题 B 只保护当前 pool 中的节点。若 C 内还有安全路径，可以再用局部区间证明未来必发现的成员。令 eligible 集合

    E = P ∪ (C\D)。

P 中节点的区间退化为已经固定的实际存储值 ℓ_u=U_u=σ(u)；C\D 中节点使用覆盖全未来评分路径的 [ℓ_u,U_u]。定义

    Q_j^loc = {v∈E: |{u∈E\{v}: U_u≥ℓ_v}|<j}。

命题 A 仍必须成立。此时任何已发现的 Q_L^loc 节点都必接受、永久保留并最终完整展开：若初次发现时 pool 已满，其他 L 个 pool ID 中至少一个严格低于 ℓ_v≤实际 σ(v)，所以新点可入池；此后不劣于它的不同 ID 总数最多 L−1，无法淘汰它。当前 P 中的安全点直接适用同一计数证明。

因此

    Reach_{G[Q_L^loc]}(P∩Q_L^loc) ⊆ D_final，
    Reach_{G[Q_L^loc]}(P∩Q_L^loc) ∩ Q_K^loc ⊆ A。

第二式再用至多 K−1 个潜在不劣 ID 的返回条件。令旧 B 与右侧交得 W，即使 W 当前尚不全在 P，也得到命题 B 的任意 GT 相对损伤界。所有路径都在已知 C 的原邻接中，不能用想象的 hub 邻接或 proxy connectivity 填路径。

**路径证书的解析非空例。** K1/L3，当前 P=(p8,r7,t1)，C 另含 a9,g10；完整原边有 p→a→g、g→p,r、r→t、t→p，其余出口都已 visited 或有 U≤1。使用精确退化区间时 Q_L^loc={p,a,g}，Q_K^loc={g}，从当前 p 安全到达尚未发现的 g，故最终返回 g。若旧 B={g}，它可保护当前不在 P 的旧返回 ID；不需读 GT 证明相对零损。这里 C/区间都是手设条件，不是实际库上的证书成功率。

这是上午 global Q_L/Q_K 的**局部 eligible 适配**：局部边界先证明其他 ID 永不可进入，永久 visited 再排除 D\P，当前存储值可以收紧区间。机制不是新创；实质减少的是待证明 ID 范围，并补上“新入口通过安全路径发现旧返回”的条件，费用/未知前件没有消失。

### 3.3 已证整原组拒收后的visited接口

主定义仍是fully-scored D。另取一种已独立证明原逻辑/返回保真的[整原组省评分](certified_group_elision_theory.md)执行，在完整row边界且无在途，令V=D_phys∪D_cert为永久visited：D_phys实际已评分，D_cert只由sound整原组guard认证拒收，P中每点都有actual storedbits。V\P永久不可重入，继续仍遵循原自然logical展开/停止，不允许任意无依据force-mark。

此接口下命题A/B/Qloc可显式把D替为V：F=P_pending∪(C\V)、eligible E=P∪(C\V)，威胁未来项也只取C\V。这些归纳只用旧废点不能重新插入、当前P分数已知和未来potential eligible，**不需要D_cert的虚构distancebits**。若suffix继续使用sound整原组guard，Q_L^loc新点由于威胁数<L而严格优于某个当前pool点，无法满足其U≤β的全拒条件，仍必实际评分/接受并展开，安全路径推论保留。

这只是已先证保真的优化状态与局部条件的接口推论，不把原kernel的visited=scored语义悄然改写。§4的响应汇合依赖其合法历史/topL(scored)/共同mixed比较合同，不能仅凭这个V接口直接继承，也不恢复未评分值trace或费用。

## 4. 局部响应等价：可放宽全库共同序，但不能放宽成 interval-only

取同 q/图/K/L 的两个合法完整行状态，live pool ID 集合相同 P。各自已满且具有命题 A 的封闭区域 C；对所有两边初始都可能未 visited 的出口，U_v 不高于两边初始 cutoff 的最小值且两边原核拒收等值。要求 **C 内所有混合评分路径间的交叉比较服从同一个严格总序**，而不只是 scalar 内部排名等于 batch4 内部排名。

则上午的 whole-pool 返回类证明可限制在 C 内：两状态继续后最终 pool/返回 ID 相同。独占 pending 节点在另一侧已完整展开；其在 C 内的邻居若不在共同 pool，依据共同严格序与 top-L(scored) 不变量低于 cutoff；C 外新邻居依据边界上界拒收。共同 pending 节点同步接受同一组可竞争 ID。因此删去仅影响拒收费用的展开后，pool 演化耦合。□

该条件比“全库存在共同 strict order”局部，但仍须证明区域内混合路径一致序；global parity 抽样不是该证明。相同 ID 不保证距离 bits；若需要 bits，另要求共同节点评分 bits 相同。两执行的 visited、pending、trace、NDC、cache 与 wall 可不同。只同固定 q，不产生跨 q 可迁移的效用或费用标签。

**ties 的四环反例。** 任意有向图取强连通环

    a → u → b → g → a，σ(a)=σ(b)=0，σ(u)=1，σ(g)=2。

L=2、K=1，两个合法初始化均消费 seeds {a,b}，所有 seeds pending，但等值优先顺序分别为 (a,b)、(b,a)。第一种先展开 a，发现 u 后淘汰尚未展开的 b；u 的邻居 b 已 visited，终局返回 u。第二种先展开 b，发现 g 后淘汰 a；g 的邻居 a 已 visited，终局返回 g。初始 live pool ID 和全部存储分数完全相同，返回却不同，且 GT1=g 唯一，不靠 GT tie 制造质量差。

这说明未规范为同一全局 tie-key 的比较器不能仅凭 pool ID 认领汇合。当前源码的 distance-only sort/接收规则没有建立一个全局 canonical-ID tie 顺序；本文不执行编译器 tie 行为试验，也不宣称每种 seed 排列都在当前工作点产生此反例。给原核加新的 tie-key 会改变合同，须另审输出与代价，不能作为本次定理的免费修补。

### 4.1 允许 ties 的有序 pool 返回类

可以在更贴 native 的合同下放宽严格序，但必须使用**相同有序 pool ID 序列**。取上述两个合法状态与局部封闭 C，假设 C 中任意两个不同 ID 的所有混合评分路径比较都服从同一个 total preorder：严格好坏与同分结果都一致。固定每节点 native distancebits 是一个更强、更容易陈述的充分条件；仅两个 kernel 各自内部排名一致或区间重叠不是此前件。

原 full-pool 等值拒收、helper 和输出不重排幸存旧 ID 时，两边继续后得到相同**有序最终 pool/返回 ID**。证明沿用耦合：exclusive pending 节点的每个邻居在另一侧已被评分；若在共同 P 外，则至多与 worst 同类，另一侧 top-L(scored) 不允许其严格更好。此侧按同 mixed preorder 评分后弱劣 cutoff，含等值都拒收。共享 pending 的可接受新 ID 不可能在另一侧已经 visited 且在 P 外，否则同样弱劣 cutoff；两边按相同邻接顺序接受同 ID subsequence，当前有序数组与所有 bool 比较相同，所以插入位置相同。删去无 pool 变化的 exclusive 展开后同步演化。原 cursor/rewind 保证余下 pending 不会被跳过。□

该证明恢复的是有序返回类；不恢复相同存储数值/bits、visited/pending、批次分组、NDC 或 wall。若只假设比较等价而非 nodebits 恒定，same-ID distancebits 仍可不同。上述四环正说明 unordered pool 集合不足。当前 E99/E166 抽样 parity 未证明 native 所有混合路径满足共同 total preorder，故不能据此直接合并真实运行时 state 或费用标签。

## 5. 局部前件与不可识别边界

**pool 未满不能用当前最差点当拒收阈值。** K=1、L=3，当前只有 seed p，σ(p)=10。p→b→g，σ(b)=1、σ(g)=20。即使 U_b=1<10，空槽仍接受 b，b 最终展开并发现 g。命题 A 必须在已满 pool 的真实完整状态使用。

**闭区间须用 L-th cutoff，不能用 K-th。** K=1、L=3，完整 pool 值为10、2、1，存在新边界 bridge b:5→g:20。b 低于当前 K-th 值10，但高于 L-th cutoff1，会入 pool 并通往更高点。对 top-K 低于当前最佳不等于搜索不能接受。

**边界信息须完整且是上界。** 只观察已读取边、一个入口距离或 sampled parity，不排除某个尚未证明的边界点被接受并指向 GT。命题 A 的边界不是“看过的邻居均不优”，而是所有 C 中潜在展开行的全部出口均已知并已证明拒收。要在未读大图上证明这一点，必须有事前可核的结构/metadata 合同。

**混合路径约束不能由各 kernel 内部序推出。** scalar(a,b,c)=(0,1,2)，batch(a,b,c)=(100,101,102) 作为越小越好的 distance，两路径内部排序一样。seed b,c 用 scalar，后发现 a 用 batch，则 a 比当前 cutoff2 差而被拒；不存在可用的共同混合序。真实 rounding 较小也能在足够小 margin 下复制该逻辑，不能以每 kernel 排名一致替代交叉比较条件。

**节点是 distinct ID，不是请求次数或 slot 次数。** repeated target slot、同 ID 重复邻接或缓存命中不会增加 T_v 的基数；初始化若真的允许重复 ID 占位，full-pool/TopL 不变量本身须先修复合同。本证书只处理已去重的合法 current pool。

**row 中间的 visited 不等于已评分。** E166 batch4 先标记最多4个邻居再一起评分/插入。若在该间隙把 visited 当成 D，尚未完成评分的 g:20 被错误当成“已经丢弃、永不重入”，当前 pool v:10,p:8,t:7 会错误通过 K1 的 v 保留证书；随后在途 g 仍要评分/插入并夺走返回。另一类 row 中间状态中，当前 pivot 可能已被后续新点从 P 淘汰，但其原邻接剩余行仍将继续扫描；只令 P⊆C 会漏掉这个 active pivot。完整行边界排除了两种问题。本文不以一个 partial-batch 数组证明状态定理，也不建立尚未实现的运行时导出合同。

**一层信息的不可识别反例。** 这是假定证书只得到当前 pool 及其一层邻接/分数的计算模型，不是声称已知完整 θ 时存在新的 Shannon 信息缺失。两合法实例有同一批节点真分：g20,h15,p10,b9,r8,t7,z6，K1/L3，默认 seeds {h,r,t}，候选 seeds {p,r,t}；g 为同一唯一 GT1。公共边为 p→b、r→p、t→p、z→h、h→g,p、g→r,t,z。唯一未观察的二层边在实例 I 为 b→g，在实例 II 为 b→z。两图均强连通；每实例内默认和候选使用同一固定底图。候选当前完整初始 pool 及所有一层邻接 ID/分数完全相同，默认均返回 g。

实例 I 中 b9 替掉 t7 后展开并发现 g20，候选不损 Recall；实例 II 中 b9 的 z6 低于更新后的 cutoff8 而拒收，候选终局返回 p10、损失GT1。故仅该局部观测不能对所有合法 fixed-graph 实例给出无损结论，必须有完整边界/可接受路径等额外结构前件。一个 completion 反例不证明当前真实 θ 的失败频率，也不禁止读取/核算完整信息；它精确限制了这组廉价观测能推出什么。

## 6. 任意容量的三入口替换反例：发现旧入口仍不足以保响应

下面只手推一个图族，没有运行枚举或搜索。令任意 L≥3、K=1。节点按严格全局好坏秩为：g:0、t:1、p1:2、p2:3、d_i:3+i（i=1,…,L−3）、v:L+1。精确算术下可取整数 IP 分数 σ(r)=L+2−r，q=1、节点标量 x=σ；全程无 tie、无路径误差。任意L的陈述是数学图族；对应当前容量范围的整数可在float32精确表示，但不能声称无界L仍无float32碰撞。本文没有运行native合成核验。

原三个入口为 {p1,p2,v}，替换为 {t,p1,p2}，有向边为

- t→v；p1→p2，若 L>3 再连 d1。
- p2→v；d_i→d_{i+1}，最后 d_{L−3}→v。
- v→g；g→p1 与 t。

L=3 时没有 d 节点。所有节点强连通，最大 out-degree2。

**原入口。** p1、p2 和所有 d 均优于 v，至发现 g 前一共只有 L 个 seed/链节点。v 不会被淘汰，所有更优 pending 扩展后 v 最终展开，发现唯一 GT1=g。

**替换入口。** t 先展开并发现 v：L=3 时 v 直接拒收；L>3 时 v 初始可入池。其后 p1/d 链引入 d_i，使已评分集合含 t,p1,p2,v 及 L−3 个 d，共 L+1 个。v 最差，会在自己展开前被淘汰。其他已保留节点都仅指向已经 visited 的 v；g 从未被发现，返回 t。

新 t 不但更接近 GT，还能直接发现被替换的 v；新执行事实上评分了全部旧 seed ID。但这不等于 v 有机会展开，更不等于发现旧返回 ID g。把两入口/多入口效用当单入口命中并集，或用“旧入口仍被覆盖”证明不损 Recall，都被这个有限-capacity 反例排除。

**K100 / 任意 K≥3 的同类扩展。** 对任意 L≥K≥3，令 GT 前K为 g,p1,p2,c3,…,c_{K−1}，严格秩依次0,1,2,3,…,K−1；t 秩K，d_j 秩K+j（j=1,…,L−K），v 秩L+1。入口仍为 {p1,p2,v} 与 {t,p1,p2}。p1 连 p2 及 c3（无 c 时连 d1 或 v），c 链末接 d 链首或 v，d 链末接 v；另有 p2→v、t→v、v→g、g→p1,t。空链自然跳过，最大出度2、仍强连通。

原入口发现并展开 K−1 个共同 GT 和 L−K 个 d，连 v 总计 L 个不同 ID，v 可展开而找回 g；新入口多一个 nongt t，v 在更优的 c/d pending 全部处理前被拒/淘汰，返回前K含共同 K−1 个 GT 与 t，恰损失1/K。t 未必最先展开，但一直存在指向下一更优 c/d 的 pending，v 不会抢先展开。该扩展覆盖实际 K100/L≥100；不声称 L<3 能实际消耗三个入口。

这是一般 beam 非单调性的机制式解析例，不是实际 NSG 构图输出、损伤频率或对候选三入口方法的实验否定。[ICML2020 §4.4](https://proceedings.mlr.press/v119/prokhorenkova20a/prokhorenkova20a.pdf) 已有最近 m 点诱导连通且进入该区域时的 beam 保证；[ABS Claim2](https://arxiv.org/html/2505.15636v1) 已给标准 beam 失败结构。本文的价值是指出“已发现旧 seed”不足以替代“旧返回 ID 保留”的当前合同前件，不能认领 beam 失败为新机制。

### 6.1 更好的 entry 与相同完整邻接仍不足

严格分数取 g20,p10,t9,u8,b7,v1，L3/K1，原 seeds {p,u,v}、新 seeds {p,u,t}。边为 p→b→g，u→p、v→p、t→p、g→u,v,t，全图强连通。替代点 t 更好，且 **N(t)=N(v)={p}** 完全相同。

原 p 的 b7 高于初始 cutoff1，入池淘汰 v1；u8 先空展开，b7 再展开找到 g20。新初始 cutoff8，p 的 b7 直接拒收，t/u 只回已 visited 的 p，终局返回 p10。原 v 在发现 g 前事实上已经淘汰，损伤不来自 v 的独有邻接，而是 t 提高共同 pool cutoff，压掉**保留入口 p 的桥**。

因此“score 更高＋完整出邻接包含/相同”这个常见局部支配直觉也不能保证联合入口无损。必须限制不同入口支路的 capacity 竞争，或证明旧返回 ID 的发现/保留；只审被替换点的一行不够。

### 6.2 相同入口下增大容量：正面前缀定理与直接前作

与增添/替换入口不同，固定同 q/G/邻接、同实际有序 seeds S，令 L2≥L1≥max(K,|S|)。维持原 complete-row best-pending、永久 visited、自然耗尽、同初始化 tie 顺序以及所有不同 ID 的共同 mixed total preorder。原 helper 是 FIFO tie 插入、满 pool 等值 cutoff 拒收。则小容量的 expanded row 序列是大容量执行的前缀；沿该前缀评分请求 ID 序列相同，大容量的请求数至少与小容量相同。

**证明。** 在共同已经评分的 D 上，pool 是按（节点共同preorder，首次发现/初始化tie优先顺序）的稳定 top-L。该有序 key 使 P_L1⊆P_L2，且大 pool 独有点排在所有小 pool 点之后。只要小 pool 尚有 pending，大 pool 的独有 pending 就不能抢先；两个执行选同一个最前 pending、扫同一完整邻接，visited 集合相同，因而评分请求与首次到达顺序相同。归纳到小 pool 不再有 pending 时，小搜索结束，大搜索可以继续。源 cursor 用最早接受位置 rewind，不会跳过最前 pending。[E99 rewind](/data/netg/ACSG/ACSG/ACSG.cpp:1663)、[E166 cursor](/data/netg/ACSG/entry_method_exploration/20260930_theory_until2200_v1/research/target_bank_frozen_curve_v1/src/kernels.hpp:84)。□

**prefix 本身还可去掉全库 mixed preorder。** 改为假设同纯 callback 在相同 q/base 地址、相同完整算术路径与 FP 环境下返回相同 bits（或已另证跨地址/alignment一致），同初始化数组/tie顺序。沿共同展开前缀，所有合法未 visited 邻居先评分再决定接收，拒收不改变 visited 标记；因此两个执行的 row、unvisited subsequence 与 batch4 分组相同，产生相同新存储值。用这些**已经实际计算的共同 σ 值**及稳定 arrival key 维护 top-L，仍有有序嵌套，归纳得到共同前缀。这个证明不需要对尚未发现节点建立所有 mixed 路径排名。

同字节但地址/alignment改变不自动证明同 reduction；callback 依赖隐藏状态、动态 rounding、评分剪枝/缓存状态不一致时也不能套此弱化。当前 FAISS FlatIPDis 返回只依赖 q、base、dimension 与固定 fvec kernel，其计数器不参与数值，但本文没有执行两个L来核验实机。大容量在小容量停止后的新评分没有任何跨路径保真保证，所以独立的 Recall 前件仍不能删。

如果原 tie 合同不是上述 FIFO，保留**共同严格序**版本即可；不能只凭 tie 分数相同外推前缀。这里假定两容量消费完全相同 seeds，不允许不同 random padding、seed 截断或提前停止。逻辑评分请求前缀不推导 wall 前缀代价相同：pool 插入、分支、cache 和向量布局费用都可能不同。

**更弱的 Recall 前件。** Recall@K 推论另假定小执行终局至少有K个distinct合法返回ID，大执行由共有评分前缀也至少具有同样多；不能把不连通/稀疏图的empty sentinel当返回成员。前缀命题本身不需这个输出基数条件。不必要求 GTK 内部顺序或 native 的 GT tie-key 对齐；只要每个被评分 GTK 的存储值都不低于任一被评分 nongt（全混合路径的二分类 weak separation 是更强充分条件），Recall@K 就非降。小搜索停止时两个虚拟 top-K 相同；其后新 GTK 进入 top-K，淘汰 GTK 净0、淘汰 nongt 净+1。新 nongt 不会严格高于当前 GTK；同分时后到 FIFO 在它们后面，无法把当前最末 GTK 挤掉，因此也不降低 hitcount。对每次新点评分归纳。新高分 GTK 可以替掉旧 GTK，所以只保证命中**数目**非降，不保证旧正确 ID 全部保留。

Exact IP 下官方 GTK 若确为真全库 top-K，含任意合法 canonical tie，二分类 weak separation 自动满足；native mixed order/GT mismatch 时此前件没有被抽样 parity 证明。增加 L 已改变预算且会增加或持平逻辑评分请求，不能因此声称完整 Recall–QPS 改善，也不授权加 L 实验。

**直接前作。** ABS §3.1 Algorithm1 已将 beam 表为共同 ordered traversal＋停止规则，§3.2 明确 greedy 的展开是更宽 beam 的前缀，并比较质量/距离计算。上述任意 L1/L2、多seed、当前 cursor、FIFO/ties 与GTK弱分离是这个已知机制在本地核的条件适配，不是新容量单调机制。[预印本 §3.1–3.2](https://arxiv.org/html/2505.15636v1)、[官方NeurIPS2025原文 §3.1–3.2](https://proceedings.neurips.cc/paper_files/paper/2025/file/904fe070f484231aa26dbdb37816cd40-Paper-Conference.pdf)。

引用限于其 ordered-traversal 与 qualitative prefix 机制，不将本文 L 直接等同 ABS 的 b 或继承逐行实现合同。其 Eq.(1)/(2) 按字面将正在弹出的 x 也计入 D 中 d(j)≤d(x) 的计数，b=k=1 时会涉及 self-exclusion/strict-tie 的 off-by-one 约定；原文未在这些式子里完整展开该约定。本文容量结论由上面的本地完整行/FIFO/cursor 归纳独立成立，不用该式补前件，也没有运行 ABS 作对照。

### 6.3 同机会整组拒收不能仅凭dot数让大容量更省

另假定两容量都共享[整原组拒收](certified_group_elision_theory.md)优化，在共同原展开前缀上，每个实际动态组的bound输入、U_G结果、启用规则及原callback路径都相同；跳过原组仍标记全部visited且不影响后续FP/计数控制。两边一致应用“满pool且U_G≤β才整组省评分”。

两pool均满时，β_small≥β_big，故big能省某组则small也能省；small已满、big未满时big不能省；big已满、small未满不可能出现在相同已评分D下。两边均未满时都不能按此合同省。于是共有前缀中任何small实际评分的原组，big也实际评分；big后缀另有非负请求，**big物理dot请求数≥small**。此处用原执行的虚拟已评分D说明capacity前缀，实际省组节点是certified-rejected而非已知distancebits的physical D。

不允许bound按L改变precision/选择、partial regroup、计数cap、callback隐藏状态或不同默认启用策略后仍套该结论。它不推出wall单调：bound费用、cache与pool管理不同。它只排除“同机会拒收加L，单靠减少dot数已证明更快”的推理；没有测试任一L。

## 7. score 支配：可计算关系条件，但 native 版本通常很空

在一次执行中，按实际存储数值排序的 pool 前 K 值逐位非降。这是不断维护已评分存储值 top-L 的数值不变量，不需要跨执行共同序。令候选当前前K值为 a_i，旧默认返回 B 的存储值为 b_j。

额外假设合法 GT 是同一真分数 g(v) 的全库 top-K（含声明的 canonical tie），且旧与新执行全部评分路径满足已证 |σ(v)−g(v)|≤ε。对候选槽 i、旧返回槽 j 若

    a_i−ε > b_j+ε，

则新终局槽 i 对应节点的真分数严格高于旧 B_j。选择不同 i、不同 j 的 m 对注入匹配，任何匹配到旧 GT 成员的终局节点也必为 GT 成员，故新 Recall 相对旧最多损失 (K−m)/K。m=K 时质量非降。

**不能把严格 > 改为 ≥。** ε=.1，旧 canonical GT1 的真分10、存储9.9，新非 GT canonical-tie ID 真分也10、存储10.1，gap=2ε 正好端点，却从命中变未命中。若要弱比较，需另有 GT tie 安全合同。本文没有该合同。

**完美默认的空证书。** 若旧 B 已含真全局 GT1，任何真实节点都不能严格高于它，完整严格匹配必失败。K=1 时这条件只能作用于旧未命中情形，非降本来为平凡下界0；不能宣传为普遍有用的 R1 安全策略。部分匹配可给损伤预算，但也可能为0。相同 GT ID 当前已发现不自动解决未来：native 误差较高的非 GT 点仍可将它挤出，除非命题 B 或另一个有效 retention 条件保护它。

在 exact arithmetic 或已证一致 canonical 全序下，“所有旧返回 B 均被新执行发现”可以推出最终 top-K 不劣于旧 B；这要求发现**返回 ID**而非 seed，且 GT 同该全序。上节反例不满足此前件，因为 g 未发现。native mismatches 时需重新用数值区间/ID保留，不能从旧样本 bit parity 外推。

一个理论上的主图IP ε来源是在无overflow、无underflow的标准round-to-nearest模型中，γ_r∑|q_i x_i|≤γ_r||q||2 M；M为已证base范数上界，r覆盖所有实际reduction/FMA路径且ru<1。允许gradual underflow时必须另加对应绝对下溢项，FTZ/DAZ及输入/输出转换也须独立覆盖；纯γ_r相对误差式不能处理所有subnormal情况。只写公式并未证明当前scalar/batch4满足它。主图的negate在有限可表示值上只是符号转换，不能误添router的1偏移。若另分析HNSW distance=1−IP，就应选真距离1−exactIP（或真好分exactIP−1），并给最后subtraction的舍入项，不能直接对σ与rawIP套同一个ε。该界可能太松而全部匹配为空。**本文未读取新向量计算M，未改核、未做误差实验。**

静态源码的fvec内积带`FAISS_PRAGMA_IMPRECISE`，宏的相应GCC分支允许associative-math/no-signed-zeros；源代码for-loop写法不能直接证明最终编译的reduction树或当前ε。[内积源码](/data/netg/ACSG/faiss/faiss/utils/distances_simd.cpp:195)、[编译宏](/data/netg/ACSG/faiss/faiss/impl/platform_macros.h:163)。这不影响同地址、同实际路径、同FP纯callback的条件prefix证明，但必须阻止用源码标量累加次序当作已验证全路径数值证书。

[Ogita–Rump–Oishi, *Accurate Sum and Dot Product*, SIAM JSC2005](https://www.tuhh.de/ti3/paper/rump/OgRuOi05.pdf) §2 的 IEEE 舍入/underflow 模型、γ_n 与求和界、§3 FMA 定义是直接前作。其 compensated Dot2/DotK 是改变算术的算法，不是当前 fixed native 核免费可继承的 bound 或新方法。

### 7.1 ID与严格分数混合匹配：只保护self匹配ID

一个更弱的关系证书可以组合原ID保留与数值单调性。令当前实际topK的不同ID为 C_1,…,C_K，旧默认不同返回ID为 B_1,…,B_K。将旧B与当前C作一一匹配，每对满足以下之一：

1. same ID，C_i=B_j，且已另证该ID最终仍在topK（仅这些self匹配成员W需要命题B/FIFO等retention）。
2. σ(C_i)−ε>σ_old(B_j)+ε。

要求旧B、当前C及所有未来可能进入topK的节点原路径都有同一个已证误差ε，即|σ−g|≤ε；GTK为该真分g的全库topK。若命题A已封闭C_region，只需对其中eligible ID及旧B取得共同ε，不必读取全库P_L。不能用每节点不同ε、平均误差或抽样margin直接替代这项统一前件。

**结论：最终GT命中数不低于旧B，无需保留全部当前C ID。** 给每个当前topK ID附其匹配的旧B标签。继续插入时，虚拟topK若变化，只有尾ID被新ID替代，新存储分数不低于被替者。被self匹配且已证最终返回的ID不会中途掉出topK再回来：它的存储分数固定，未来同分点按FIFO后到，尾淘汰不会删除仍存ID的前方节点，永久visited也不允许重插；其排名只能变差。故被替标签一定是strict类型。将该B_j标签交给新ID，σ_new≥σ_old-current维持同一strict误差margin，再次替换时继续传递。终局仍有K个distinct标签；每个旧GT标签对应same ID或真分严格更好的GTK，给出注入命中保护。□

不同ε时σ_new≥σ_current不足以证明σ_new−ε_new≥σ_current−ε_current，这正是不能直接传标签的缺口。只说当前槽值非降、只保护若干旧IDs而未给distinct完整匹配，也不能排除两个保护理由指向同一最终ID。

**非空且不用全C retention的解析例。** K2/L3，节点分数w10,y6,x5,t4,z3,r2,h−1，边为w→t,h；t→w；h→x,r,z；x→y；y,r,z→w，全图强连通。旧默认seeds {w,t,r}，满pool使h−1拒收，返回B={w,t}。候选seeds {w,x,z}，展开w后t4淘汰z3、h−1拒收，完整状态P=(w10,x5,t4)、pending x/t；局部区域P∪{y6}封闭。w通过native ID保留，当前x5相对旧t4有strict margin（例如统一ε=.1）。混合匹配是w↔w的self与t↔x的strict。随后x展开发现y6，最终返回{w,y}，当前x确实离开topK，故不需要全C retention。该例采用手设真/存储分数和合法完整行，没有执行图搜索，也没有获取真实ε或GT。

完美R1默认的self-retention条件非空，但等同已有ID保护推论；完美topK情况下也不能凭strict标签凭空增加K个真命中。这是两个现有条件的组合加强，不是新方法或已有收益。旧B、当前候选前缀、retention、统一ε、匹配及完整在线费用仍未知/须支付。

## 8. 信息可得性、费用与研究边界

局部证书真正减少的是**所需证明范围**：不用全库 P_L 或全库 GT/native 排序，改为当前 C 的完整出口上界和有限威胁 ID 计数。它没有消除已执行前缀、未知完整 C、未知上界及旧 B 的信息需求。若连这组局部前件都不能便宜证明，不能用入口更近、GT10 affinity、更少路由访问或训练 accuracy 补上。

用户允许提高离线训练、metadata构建与校验投入；不要求训练成本下降。可以用较重离线过程学习、构造或认证局部上界，但学习均值/误差小不能替代逐点全路径可靠上界。线上读取这些信息、核算边界/威胁集合、必付前缀与访问仍计入完整 wall；与共享相同机会的最快默认相比，Recall 与QPS综合净改善才是门槛。本轮没有开始这些离线构建或计算。

条件norm界为 σ_native(v)≤||q||||x_v||+ε_v；可取该右式的可靠向上包络作为U_v，需已有可靠 norm metadata。它可能在低 norm 出口与正 cutoff 下非空。若以 active pivot p 的**当前存储分数**构造通常的球界 U_ball=σ(p)+||q||||x_v−x_p||+非负误差，则只要 σ(p)仍≥当前 cutoff，该构造不可能给U_ball<cutoff；零半径/零误差且 pivot 正好为 cutoff 的退化等值可按原核等值拒收使用U_ball≤cutoff。这是该特定球包络的空性，不能限制其他更紧上界。邻接行处理中 cutoff 会收紧，旧 pivot 后续可低于新 cutoff，该球界才可能开始有用；不能将展开时条件外推到整行。[上午静态审计](../20261002_theory_until1300_v1/access_literature.md:154) 是边界分析，没有新性能验证。

这个空性不适用于 pivot 正交残差包络。精确单位方向 u=p/||p||，写 c=q·u、r=||q−cu||、α=u·x_v、τ=||x_v−αu||，则 exact IP≤cα+rτ。q=p=e₁、x_v=.8e₁+.6e₂ 时上界.8可低于 cutoff .9，虽 pivot 分数1仍在pool。signed coefficient、范数/投影metadata、原 native 误差及bound计算自身都须区间包络；这里没有取得真实区间。FINGER v1 §3.2 与 Appendix A 已用邻居投影/残差角度作图搜索评分近似，其 sampled average-L1 correction不提供本文要求的 deterministic full-path upper bound。[原论文](https://arxiv.org/pdf/2206.11408v1)。本地上午已记录该正交分解，非本稿新发明。

对当前原核更直接的时间候选是已证明全拒收的**整个原动态batch组**省dot：[独立理论页](certified_group_elision_theory.md)。它维持原 visited、分组和未来存储值，所省节点只是 certified-rejected，未实际评分；不能将这些ID未经修改放入本文的 fully-scored D。部分节点省去并重新分组会改变scalar/batch4数值路径，不能自动继承输出保真。该页已经交叉手审，尚无metadata或费用测量。

若计划利用证书避免执行完整 suffix，那已改变停止合同，需要另获实验授权、建立同原返回/成本控制；本文只证明原自然继续执行的响应。等价缓存、已知返回标签复用或局部 score 匹配也不提供真实 suffix wall，费用标签不能按 Recall 标签合并。共享默认若得到同类优化，仍必须一并计入完整成本对照。

可独立审阅的结论包括：A 的局部封闭、B/ordered/FIFO 的native ID保留及任意GT损伤界、Q^loc安全路径、ordered-pool局部返回等价、同入口容量前缀/额外Recall条件、同机会省组的物理请求边界，以及ID/strict-score混合匹配。核心条件命题与解析例已获独立手审，目前没有挂起的数学证明缺口；实质容量修正是“新GT粗界不能strict正”，详见§3及[交审记录](review_notes.md)。

仍未闭合的是**真实性能前件**：真实合法完整state导出/重用、事前完整C/边界metadata、全native路径数值interval/统一ε、旧B或truth标签合法可得性、证书覆盖率、原group一致启用、共享默认以及完整wall费用。它们不是“待运行一个数学证明”；本轮不获授权验证这些前件或构建metadata。未证明新三入口优于原默认或可靠Recall–QPS综合改进，系统新颖性检索也未完成。当前保持THEORY/HOLD；不修改默认、不开始实验。

## 9. 本次原文阅读与非原创边界

| 原始材料 | 实读位置 | 本文使用与边界 |
|---|---|---|
| Liudmila Prokhorenkova, Alexander Shekhovtsov, *Graph-based Nearest Neighbor Search: From Practice to Theory*, ICML2020，[PDF](https://proceedings.mlr.press/v119/prokhorenkova20a/prokhorenkova20a.pdf) | 上午已实读 §4.4，下午沿用封存结论 | 最近 m 点诱导子图、beam容量和进入条件是安全前沿直接前作；本稿不认领诱导子图机制首次 |
| Yousef Al-Jazzazi, Haya Diwan, Jinrui Gou, Cameron Musco, Christopher Musco, Torsten Suel, *Distance Adaptive Beam Search for Provably Accurate Graph-Based Nearest Neighbor Search*, NeurIPS2025，[预印本](https://arxiv.org/html/2505.15636v1)、[官方PDF](https://proceedings.neurips.cc/paper_files/paper/2025/file/904fe070f484231aa26dbdb37816cd40-Paper-Conference.pdf) | 上午已实读 §3–4/Claim2；下午复读v1及官方 §3.1–3.2/Algorithm1 | ordered traversal/prefix、standard beam失败、不同停止/准入规则是前作；不等同本地L与其b，不继承改变核后的保证 |
| Yannick Bosch, Sabine Storandt, *Instance-based Approximation Guarantees for Graph-based Nearest Neighbor Search*, ICAPS2025，[PDF](https://ojs.aaai.org/index.php/ICAPS/article/download/36113/38267/40186) | 上午已实读 Definition3–6、Theorem1，下午复核原页 | greedy 路径/Voronoi 响应区域是直接前作；有限beam返回类适配不是程序分区概念首次 |
| Takeshi Ogita, Siegfried M. Rump, Shin’ichi Oishi, *Accurate Sum and Dot Product*, SIAM JSC26(6):1955–1988,2005，[作者 PDF](https://www.tuhh.de/ti3/paper/rump/OgRuOi05.pdf) | 下午实读 §1.2–§2，§3 FMA 定义 | 经典数值误差模型；不得当作当前 CPU/FP/kernel 已验证或主核可免费更换 |
| Patrick H. Chen, Wei-cheng Chang, Hsiang-fu Yu, Inderjit S. Dhillon, Cho-jui Hsieh, *FINGER: Fast Inference for Graph-based Approximate Nearest Neighbor Search*, arXiv2206.11408v1，[原文](https://arxiv.org/pdf/2206.11408v1) | 下午实读 §3.1–3.3/Algorithm1–3，Appendix A（IP） | 图邻居拒收省计算、投影/残差估角已有直接前作；平均L1 correction不是逐点全路径upper，本文不使用其SVD最优命题 |

本地[E112](/data/netg/ACSG/experiment_history/108_one_hop_hub_design.md:3)已有one-hop条件覆盖及标准次模目标，[E46](/data/netg/ACSG/experiment_history/35_exact_feedback_cache.md:5)已有同query/原图/L/K/metric/kernel身份与相同真实三入口的完整响应缓存；该缓存仍真实执行路由并计费。上午定理已有global P_L/Q_L/Q_K与whole-pool返回类。本稿只是明确局部拒收边界＋永久visited使全局威胁缩成C\D，并把native ID保留转为任意GT的相对损伤界；新颖性没有完成系统检索，不称新论文定理首次。
