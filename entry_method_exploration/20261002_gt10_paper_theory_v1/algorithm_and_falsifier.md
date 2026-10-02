# 保留现行 GT10：完整算法与有限 beam 发现理论

2026-10-02，纯理论草案。没有训练、GT、ANN、向量读取、旧数组统计、合成模拟或数学程序。本文件的选择是**把已有 GT10 写成可审稿的完整方法与理论框架，并补直接连接真实搜索的理论**，而不是给 E04/E118/E164 的真实效用监督换名。此稿不能保证 CCF B 录用；需要独立证明审阅、最接近前作审查和真实机制/完整 Recall–QPS 证据。

## 1. 方法究竟是什么

方法仍是 GT10 的三阶段：真实 target 选实际入口；target 对入口的归属反向聚合 query 画像；便宜的画像小图选三个真实入口，随后运行原 NSG。它不是预测一个虚拟 GT，也不改变底图的距离、邻接、扩展或停止。

输入为固定 base B、raw-IP 底图 G、独立 QGT query、画像拟合 query X_i=unit(q_i)、每个拟合 query 的精确前十 target ID。QGT 与画像拟合输入应有独立角色；GT10 的“10”只是训练 rank 数，正式输出仍为 K=1/100。

1. 用当前 QGT-Cover 球面代表 query 和其真实 GT 候选，选择互异真实 base ID H={h_1,…,h_H}。这里继承现行选择器，不能把下文固定 H 的定理写成整个选择器的最优性。
2. 令 u_h=unit(base[h])。对每个真实 target t，hard 归属 w_h(t)=1[h=argmax_j unit(base[t])·u_j]，ties 沿真实 ID；soft 为同一全 H cosine 的 stable softmax，温度固定为现行配置。每 query 的 a_h(q)=10⁻¹Σ_{j=1}^{10}w_h(t_j(q))，因此 Σ_h a_h(q)=1。
3. 离线形成 m_h=u_h+Σ_i a_h(q_i)X_i，p_h=unit(m_h)。画像保存的是 query 方向，标签来自 target。每画像只绑定一个真实 h。
4. 在 p_h 上建立现行 Micro-HNSW。在线对原 query 检索三个互异真实 ID，按现行真实 ID 顺序送入 mode=2；主图使用原 raw query 与 raw-IP 距离、原 L 和原自然停止。
5. 正式单线程完整 wall 包含画像检索、入口排序、主搜索和输出；所有共享缓存/距离 memo/内核优化也给默认相同机会。

这套算法已有实现与性能记录。算法定义以 [E24 原协议](../20260910_gt_topk_profiles_v1/protocol.md)、[当前 spec](../../spec.md:170) 为准；本稿没有新接口或训练目标。源码 [ACSG.cpp](../../ACSG/ACSG.cpp:1519) 的 mode=2 合法时仅初始化最多三个互异入口，**不随机填满 L**；空入口才 fallback。以下定理必须使用实际初始化 S，而不能偷偷加入 L 个随机点。

候选论文贡献应表述为：**用 target–hub 对应关系学习入口的 inverse-query geometry，并刻画其对固定有限 beam 的发现机制**。闭式归一化、球面均值、小图、两塔、监督更贵或训练更久本身均不是新贡献。GATE 已有固定底图/小图/查询选 hub 架构；最终创新边界由 [前作审查](../20261002_theory_until1600_v1/theory_prior_and_falsifier_audit.md) 与本轮论文审查共同约束。

## 2. 新补的主命题：入口改变可访问的高分组件

### 2.1 固定分数合同

固定一个 query、有限有向图和所有实际初始化 ID S（|S|≤L），该 query 开始时 visited 为空。令 σ(v)=-native_distance(q,v)，越大越好。先假设该 query 下每个 v 有固定有限 σ，所有评分调用路径给相同值；pool 保留分数最高的至多 L 个已发现不同 ID，拒绝等于末位 cutoff 的新项；每次扩展当前最高分未扩展成员，扫描完整原邻接行，visited 在本 query 内永久，无额外距离/扩展 cap，所有 retained pending 成员最终得到扩展。当前自然游标/rewind 可实现这一语义，但 SIMD 不同路径的统一 σ 不自动成立。

静态核对 [ACSG.cpp:1483](../../ACSG/ACSG.cpp:1483)、[ACSG.cpp:1616](../../ACSG/ACSG.cpp:1616) 显示初始化和合法新邻居在评分前 set visited，拒收也保持 visited；[ACSG.cpp:1675](../../ACSG/ACSG.cpp:1675) 的 rewind 确保新入池的更优 pending 不被跳过，完整 row 之后才更新游标。`search_new` 本身不清空 vt，caller 必须使用新表或 advance；[IndexACSG.cpp:407](../../ACSG/IndexACSG.cpp:407) 有每 query advance。这里审的是源码合同，不声明对历史 E99 二进制新做了运行 parity。

给定解析阈值 τ，定义 H_τ={v:σ(v)≥τ}，以及从所有 S∩H_τ 出发、沿诱导图 G[H_τ] 可达的 C_τ(S)。不同于“全库高分集合”，C 只包含不用经过低于 τ 的桥便可从初始高分入口到达的节点。

**命题 A（有限 beam 的高分发现）。** 若 |C_τ(S)|≤L，则 C 中每个节点都会在第一个 σ<τ 节点扩展之前被发现并扩展；在此之前所有已发现 C 节点始终留在 pool。允许全库有任意多 σ≥τ 的节点，只要它们在上述诱导图中暂不可达。

证明如下。

1. 在任何低分节点尚未扩展的前缀，所有已发现高分节点属于 C：高分初始化在 C，扩展高分时发现的高分邻居仍在 C。
2. 这个前缀总共最多发现 |C|≤L 个高分 ID。每个新高分 ID 在未满 pool 时插入；满时如果存在低分末位便严格优于它。若 pool 已全是高分，新高分将意味着已发现至少 L+1 个 C 节点，与 |C|≤L 矛盾。因此任何高分都不被拒收或淘汰。等于 τ 的不同节点之间 ties 不损害这个计数论证。
3. 若 C 尚有节点未发现/未扩展，取从高分初始化出发的一条高分路径，路径上第一个尚未扩展的节点已发现并保留；它是 pending 且分数≥τ，所以先于任何低分 pending 节点扩展。有限图与永久 visited 使此过程终止，届时全部 C 已扩展。

第三步排除了“路径存在就一定成功”的漏洞：路径必须位于当前 query 的高分诱导图，并且整个可达高分组件的宽度受 L 控制。更近入口、原图强连通或多加一个入口均不单独满足本命题；增加入口还可能扩大 C 到超过 L。

**推论 A1（完全关闭的搜索工作集合）。** 若 |C_τ(S)|=L，则自然搜索的完整扩展集合恰为 C。C 全发现后占满 pool，全部低分已发现项被淘汰，C 的低分外邻居都不能再入池；没有 pending 低分会扩展。因此，若每个 ID 只算一次固定分数，主图实际评分 ID 集合恰为 S∪N⁺(C)，主图评分数为其基数。这里 N⁺ 只含合法 base ID；完整 physical 邻接扫描槽数为 Σ_{v∈C}r_v，r_v 是原 row 的实际槽数，包含 padding/非法槽和重复 ID。当前定宽图为 graph.K×|C|，不能用去重 out-degree 冒充数组访问量。其中初始低分 S 仍已计费，外邻居即使被拒收也已算分。

这个推论给了**完整工作集合**，而不只是“首次命中更快”。|C|<L 时没有这份关闭条件：低分节点可能继续扩展并发现另一个组件，不能用前缀工作量替代完整 wall。

### 2.2 接到真实 GTK 返回

再令 T_K(q) 为官方真实 GTK，K≤L。假定实际 native 排序把所有 GTK 成员严格排在全部非 GTK 之前；这可由原始精确 IP 的正间隔与覆盖所有实际浮点路径的误差界推得，不能把官方 GT 自动等同 native 分数。

**推论 A2（联合入口召回下界）。** 在命题 A 的前件下，原搜索 Recall@K ≥ |T_K∩C_τ(S)|/K。

理由：这些真实成员在高分前缀都被发现；至多 K 个 GTK 且 K≤L，严格优于非 GTK，故之后也不会被 pool 淘汰。该下界直接针对共同 pool 的完整 S，不把三个单入口 Recall 相加，也不假设单入口效用可分。

如果仅有 native 的弱分离而非严格分离，跨 GTK/non-GTK 的等分到达规则仍可能损伤官方成员，须另给共同 total-order/输出类证明；本稿不省去 ties。

### 2.3 原生区间版本

若无法统一 scalar/batch4 的 σ，但对每个 v 已有覆盖所有合法计算路径、编译优化、舍入和 FP 环境的可靠区间 [ℓ_v,U_v]，则定义 potential 高分图 P_τ={v:U_v≥τ}，C⁺_τ=Reach_{G[P_τ]}(S∩P_τ)；safe 高分图 F_τ={v:ℓ_v≥τ}，D_τ=Reach_{G[F_τ]}(S∩F_τ)。

**命题 A3（路径不一致时的保守发现）。** 若 |C⁺_τ|≤L，则 D 中全部节点在首次实际 σ<τ 节点扩展前已被发现并扩展。

实际高分初始化必在 potential seeds 内；任何仅由实际高分扩展发现的实际高分节点必位于 C⁺。因此高分数量仍≤L，safe 路径上的每节点在实际路径下均≥τ，A 的“第一个 unfinished safe 节点”论证适用。这里不要求全部 gray 节点扩展，不把 C⁺ 当实际工作集合；C⁺ 可能很松。

若另外 D=C⁺ 且 |D|=L，则每个 potential 节点都是 safe 可达；完整扩展集合同样恰为 D。A2 用 T_K∩D 代替 T_K∩C，并仍单独要求 GTK/non-GTK 的原生排序分离。

没有可靠区间时，A3 只是解析条件。不能用 float64 静态 scores 或一个 γ_d 模型冒充对实际 SIMD/FMA/associative-math 归约路径的完整证明。

## 3. 与 GT10 训练连接：rank 平均的偏差与方差

不能把十个 GT 当十个独立 query。固定 H/温度，令 X 为随机拟合 query 的单位向量，对每个 rank j 定义 Y_{j,h}=w_h(t_j(X))X。现行 GT10 的单 query 贡献为 Ȳ_h=10⁻¹Σ_jY_{j,h}；不同 j 共享同一 X、GT 排序和目标邻域。

记 μ_{j,h}=EY_{j,h}，μ̄_h=10⁻¹Σ_jμ_{j,h}。其方差（向量平方范数）精确为

v̄_h=E||Ȳ_h−μ̄_h||²
    =10⁻²Σ_{j,k}E⟨Y_{j,h}−μ_{j,h},Y_{k,h}−μ_{k,h}⟩。

十目标平均的总体方向未必等于 GT1；rank bias 是 B_h=||μ̄_h−μ_{1,h}||。不同 rank 更相关时，方差改善小；rank 均值不同可引入真实偏差。

**命题 B（不依赖 rank 独立性的平滑充分条件）。** 若所有 rank 的 μ_{j,h} 相同且 E||Y_{j,h}−μ_h||²=v_h，则

v̄_h=[v_h+9c̄_h]/10≤v_h，

其中 c̄_h 是 90 个有序不同 rank 对的内积协方差平均；上界由 Cauchy–Schwarz 得到 c̄_h≤v_h。只有 c̄_h<v_h 才严格改善，若十个归属每 query 完全相同则等号成立。此式没有独立假设；1/10 只在 c̄_h=0 时成立。

一般 rank 均值不同时，sample 平均恢复 μ̄ 而非 μ_1。相对任一指定服务方向矩 b_h，误差分解为总体失配 ||μ̄_h−b_h|| 加有限 query 样本误差；不能把减小方差解释为更接近服务边界。

### 3.1 有限 query 样本与固定 anchor

以下只给合法的 IID query 数学合同，不说真实训练行已有 IID 证明。H、归属规则与 soft 温度须在这 N 个独立 query 之外冻结，或者有另外的合法 uniform/selection 论证；尤其现行 soft 温度曾由同批 fit GT1 margin 得到，不能只把它条件化为常数便继承 IID concentration。hard 没有温度依赖；外部独立 H 的条件化与同批温度选择不是一回事。满足这些前件时，Ȳ_h∈unit ball；样本贡献均值 \hat μ_h=N⁻¹Σ_iȲ_{i,h}。有

E||\hat μ_h−μ̄_h||≤√(v̄_h/N)。

对任意 δ∈(0,1)，同时所有 H 个 hub 的均值误差以概率至少 1−δ 不超过

ε_h=√(v̄_h/N)+√(2 log(H/δ)/N)。

证明：独立样本的交叉中心项期望为 0，给均方 v̄/N；Jensen 给第一式；改变一个样本最多改变 norm-error 2/N，bounded-differences 的尾部为 exp(−Nt²/2)，再对 H union bound。这个概率工具属于 [McDiarmid 1989](https://www.cambridge.org/core/books/abs/surveys-in-combinatorics-1989/on-the-method-of-bounded-differences/AABA597B562BDA7D89C6077E302694FB)；推导可直接通过 Doob 条件差范围≤2/N、逐步 Hoeffding mgf≤exp(λ²/(2N))、λ=Nt 得到。这里只使用标准工具，不声称原创 concentration。

v̄_h≤1 给不用未知方差的更松界。使用 v̄_h 时它是理论真实总体量，未给数据自估方差证书。大量弱 moment 情形下，worst-case confidence 项可能超过 ρ_h，方向界便无法使用；“已有有限样本定理”不等于“本数据 N 已达其条件”。

若 ρ_h=||μ̄_h||>0 且 ε_h+1/N<ρ_h，则 current anchor 画像 p_h=unit(\hat μ_h+u_h/N) 对人口方向 p_h^*=μ̄_h/ρ_h 满足

||p_h−p_h^*||≤2(ε_h+1/N)/ρ_h。

固定 prior 1 的贡献随 N 减小；更多训练可以减小样本项，却不能消除总体 rank bias、soft 混合失配或联合搜索响应失配。弱人口矩/稀有支持会放大方向误差，不能仅用 ESS 报告质量。

### 3.2 不改算法的同批 soft 温度选择保证

同批温度选择并不要求强制改 split；可用标准 uniform argument。先在读取这 N 个 query 前声明紧区间 [T_a,T_b]，T_a>0，归属分数 c_h(t)∈[−1,1]，H 与目标库固定。现行数学归属 w_h(t,T) 对 T 有

∂_T w_h=w_h(Σ_jw_jc_j−c_h)/T²，|∂_T w_h|≤2/T_a²。

因此 Ȳ_h(T) 及其总体均值各是 2/T_a²-Lipschitz，中心差 \hat μ_h(T)−μ̄_h(T) 是 4/T_a²-Lipschitz。取覆盖该区间、每 T 距离某网格点≤Δ 的预定 M 点网格，在每个固定网格点应用上一节、对 H×M union bound，得到概率至少 1−δ 的同时界

sup_{h,T∈[T_a,T_b]}||\hat μ_h(T)−μ̄_h(T)||
 ≤1/√N+√(2log(HM/δ)/N)+4Δ/T_a²。

该同一事件覆盖全部 T，所以任意使用同批 query/GT 的随机所选 \hat T∈[T_a,T_b] 都合法，无须条件化 \hat T 后假设 query 仍独立。画像方向和下游 margin 再使用 μ̄_h(\hat T)、ρ_h(\hat T) 的随机人口参考；确认 query 须独立于训练。

原 E24 的数学中温度为 max(GT1 cosine margin 中位数,10⁻⁴)，可在解析 unit-vector 合同中取固定 [10⁻⁴,2]；倍率族 {1/4,1,4} 整体可取 [2.5×10⁻⁵,8]。静态原 initialize.py 的 106 行 floor 与倍率定义已由 root 核对。float32 normalize/score 的范围与下溢另需 outward 数值界，不能以理想 [−1,1] 覆盖所有实际实现。超出先验区间事件、H 同批选择依赖、GT 教师随机变化等也须另处理。

此网格只是证明对象，不执行温度枚举，也没有在线网格成本。小 T_a 的 Lipschitz 常数会使界很松；不能把这项合法 uniform 保证写成现有数据的非空数值保证或新增方法创新。

## 4. 从画像到真实三入口，再到有限搜索

给一个**完整、条件可定位的链条**，不再声称 proxy-optimal 就是 Recall-optimal。

1. 人口当前算子的得分为 s_h^*(q)=unit(q)·p_h^*，人口 top3 的唯一集合为 S^*(q)。这是当前 GT10 的 population routing，不是事后 full-H 最优效用动作。
2. 对训练事件中的 η=max_h||p_h−p_h^*||，population 第三/第四分数间隔 γ(q)>2η，使 sample exact top3 与 S^* 相同。
3. 实际 Micro-HNSW 的 sample set-score 缺口定义为 ξ(q)=max_{|A|=3}Σ_{h∈A}unit(q)·p_h−Σ_{h∈S_ANN}unit(q)·p_h≥0。若 ξ(q)<γ(q)−2η，则实际 S_ANN 也等于 S^*：任何错集合相对 sample 最优至少损失 γ−2η。tie、float32 serialized profile 和实际 distance-path 差异应在 η/ξ 内另有可靠边界，不能拿 float64 exact rank 替代原生。
4. 若该人口三入口在某 τ 下满足命题 A 或 A3 的宽度前件，真实 GTK 的 safe coverage 为 κ_K(q)=|T_K∩C|/K（或 |T_K∩D|/K），便有 actual Recall@K≥κ_K(q)。K1/K100 各使用自身 GT、排序前件与 L，不混成 K10。

固定已训练模型和任一事前定义 query 总体，令 F 为实际路由未恢复 S^* 的事件；把图宽度/GT 前件不成立的 query 设 κ=0。于是

E Recall@K ≥ E κ_K(Q)−P(F)。

这是一份可区分源头的 lower bound：总体 GT10 方向造成的人口入口、sample/anchor 误差、小图实际检索、native 数值与有限图高分发现各有单独前件。若与 baseline 比较，右侧只有在超过 baseline 的真实平均 Recall 后才给质量提高；没有这样的事实时不声称收益。

这里只证明 target 对应的 query 矩可怎样作用于搜索。尚未证明真实 GT10 的目标–hub cosine 归属会使 S^* 含高分组件的有效入口，也未证明多个 hub 的归属互不重叠；相关条件只能通过独立机制证据检验。把 target 标签改成 full-H signed utility 会进入 E04/E118 前作，不能作为这里的新方法。

## 5. 条件确实非空，但完整 QPS 仍须实测

可以手工定义一个合法图：τ 高分区域 C 恰有 L 个节点并包含全部 GTK，图内从某个真实 hub 可达；图外有任意多高分节点，但与 C 的通道都经过低于 τ 的桥。把有效 hub 作为初始入口，A1/A2 给完整扩展 C 与 Recall=1；从图外低分入口开始未必满足同一条件，也可能先被其他区域填满。图可以强连通，高分诱导组件仍分离。这个解析存在例不执行、不代表真实 NSG 分布，也不要求改变原搜索。

现行 GT10 的 hard/finite-T soft 正面矩模型已在 [168 推导 §4.3–4.4](../20261002_theory_until1600_v1/surrogate_to_search_theory.md) 给出；不能直接把其固定两个 hub/单入口结果包装为真实数百 hub、top3、现行 H 生成器的保证。此处是兼容的图机制补强，真实 moment–component 对齐仍需证据。

A1 的 unique scored ID/邻接扫描集合不是完整 wall 定理。CPU 的 cache、pool 插入、预取、SIMD group、路由与输出仍收费；使用正确结构集合也不能把 NDC 比例换算 QPS。可接受的质量/速度结论必须来自同机单线程 complete-wall 的当前 default 对照。训练增加可以改进 ε，增加 query supervision/metadata 不提供免费的线上获取信息。

## 6. 哪些是论文贡献，哪些不是

|对象|适合的论文地位|还不能声称什么|
|---|---|---|
|target→hub→query 反向画像，真实 hub 与原主图分离|现行方法主贡献候选；需对 GATE 等精确划界|新架构未有前作、任意 OOD 上占优|
|查询诱导高分可达组件的容量发现命题及区间版|ABS 已有 ordered traversal 的针对当前 pool/原生路径的适配推论；主理论链的搜索部分|单独以该 lemma 充当新的 beam 理论、所有图/beam 的普适新定理|
|rank bias–covariance–population moment–anchor 链|解释 GT10 相对 GT1 的条件与负例|十倍独立样本、已证明 GT10 普遍更稳/更准|
|joint component coverage、population rank margin、actual ANN gap|连接算法各层并指出缺口|top3 单入口效用可加、画像 score 最优即 Recall 最优|
|闭式归一化与样本 concentration|标准工具的应用，证明透明|球面均值、McDiarmid、normalization perturbation 的原创|
|完整 Recall–QPS 原证据、固定 default 与分源确认|论文实证核心|训练便宜/拟合好/NDC下降即可综合提高|

最接近理论需比 [ABS NeurIPS2025](https://proceedings.neurips.cc/paper_files/paper/2025/file/904fe070f484231aa26dbdb37816cd40-Paper-Conference.pdf)、[Sort Before You Prune ICML2025](https://raw.githubusercontent.com/mlresearch/v267/main/assets/gollapudi25a/gollapudi25a.pdf)、[α-Reachable Graphs 多向量原文](https://openreview.net/pdf?id=v8jSxLHEE9)。ABS 的 ordered best-first traversal 与 beam width 停止关系已直接覆盖 A 的基础思想；未见完全相同的显式 Cτ statement 不足以证明创新。**A 应写成适配推论，候选贡献是 inverse-query transport/rank 误差经 query-induced 发现与完整工作集合兑现的完整方法分析。** 该候选仍待论文级前作排除。其 arbitrary score、本地组件、原自然 pool、实际三个初始化的合同不同于修改停止的 ABS 或重新构造 α-reachable 图，但合同不同也不自动构成重要新结果。

[Graph Based K-Nearest Neighbor Search Revisited，TODS2025](https://doi.org/10.1145/3736716) 也有 query-dependent virtual graph、导航与 refine 保证；本轮只获取官方摘要/概要，没有核完整正文，因此不声明排除其所有理论。对照须完整读正文之后再定 novelty claim。Cτ、potential/safe component 和 ξ 都是理论分析对象，未提供在线免费的获取算法或 oracle。

## 7. 可直接否证论文主张的最小问题

这是后续研究问题，不是已经启动的任务。

1. **方法区分失败**：GATE 或其他 query-aware entrance 原作已包含相同 target→hub→query 合力或等价训练目标，则不能据此报方法新颖性；应收缩到此前未有的机制/理论，或另找真实差异。
2. **rank 平滑不成立**：matched GT1/GT10 的 rank 均值失配或 covariance 不满足 B；必须报告 rank bias 和协方差，而不能用 query 数×10。
3. **有效入口不对应 safe component**：真实 S^* 无更多 GTK 的 safe-path coverage，或 potential component 常超过 L；则主图定理对真实收益解释力不足。不能先看失败 query 再调 τ 直到证书通过并称预测。
4. **native 前件失败**：没有覆盖实际 path 的 score 区间，或 GTK/non-GTK 近 tie 足以跨界；区间版不能报实际保真。
5. **小图吸收/混淆**：实际近似路由未保持 population ranking，或者换入口大量被底图吸收；方向改善不等于 Recall 改善。保留已有 E145/E158 类负证据。
6. **完整成本失败**：新增路由/表示费用抵消主搜索工作节省；或公平共享优化后的默认更快。即使理论 Recall 下界很好，也不能报可靠 Recall–QPS 综合提高。
7. **泛化失败**：新来源的 moment、rank相关性、top3间隔、native/path 与组件分布变化；不得用旧开发统计声明分布外保证。

主论文建议保留现行 GT10，不先强行改算法。待理论条件与真实效应解释力成立，才考虑由证据直接指向的一项最小修改；此阶段没有新模型、训练参数或执行 GO。
