# 固定有限图搜索的响应、交互与保真条件

终稿：2026-10-02 12:30（UTC+8；初稿11:44）。本文件只讨论理论、已曝光历史证据和纯合成数学核验；不构成新方法 GO，不改变暂停状态或默认。

## 结论与待解决缺口

当前最有用的理论强化是两项有条件结论：**全局前 L 安全前沿的多跳发现证书**，以及**有效完整行边界上，以 live pool 身份定义的返回响应等价类**。它们分别回答“哪种路径不会被其他入口挤掉”和“哪些完整状态差异只影响费用、不影响最终返回”。这比入口距离误差、画像 top3 翻转率或全图 hop 更接近冻结主核，但都不是免费线上特征，也不是已测 Recall–QPS 提升。

目标访问候选还必须依次通过四件事：选点支持覆盖、评分/选点保真、主核返回响应保真、完整 wall 净节省。任一层的正信号不能跨层继承。旧165/166显示 target 路由虽能减少一些 graph NDC，却在完整 wall 上更慢；旧桶支持的覆盖率又不足以保证保留原 target 选择。默认仍为 Web `GT10-soft-t1`、Y `GT10-hard`、生产 E99。[当前状态](/data/netg/ACSG/summary.md:3)

## 固定合同及实现核对

固定底图有向邻接行及其顺序、当前 query q、主核、实际 K/L、输入中实际消耗的入口、visited 规则、展开和停止。L指实际pool容量：E99 `max(search_L,K)`，E166协议本来L≥K。令 d_q(v) 越小越好；S 是**实际消耗且去重**的 seed 集合，不是传入但未消耗的入口。研究核最多取前三个，且不足 L 才继续取。当前 L 均远大于3。定理只处理合法非空 S、有限分数、无 tie 的情况；附录单独放宽ties/共同序前提。

| 实现问题 | 当前源码事实 | 对证明的影响 |
|---|---|---|
| 随机 filler | mode2 合法非空入口不补到 L；只有消费入口为空才随机补1点 | 定理排除空入口随机分支；不把 L 个随机点偷偷纳入 S |
| visited 但未入 pool | 未访问的合法邻居先置 visited、实际评分，再根据 cutoff 拒收 | D 必须包含所有 scored 点，不能仅统计 accepted pool |
| stagnation 早停 | `current_stagnation` 只写 trace；循环由 pool pending 扫描终止 | 不存在未展开安全点因 stagnation 被提前截断的例外 |
| 插入/rewind | pool 有序，拒绝劣于已满 cutoff 的点；插入位置不超过当前 k 会 rewind | 与“每次选择当前最优 pending 点”的符号调度一致 |
| batch4 | 先标记至4个未见邻居，再评分全部并依邻接顺序插入；整个行处理完 | 只在完整行边界用 D=已评分集；batch 收集中间不满足该状态定义 |
| scalar/batch4 | seed 用 scalar；四邻居可能用 `distances_batch_4` | 必須另假设所有评分路径产生同一节点严格总序；抽样 parity 不证明全局成立 |

源码依据：[E99入口](/data/netg/ACSG/ACSG/ACSG.cpp:1528)、[E99评分与插入](/data/netg/ACSG/ACSG/ACSG.cpp:1614)、[E99 stagnation/rewind](/data/netg/ACSG/ACSG/ACSG.cpp:1654)、[E166完整核](/data/netg/ACSG/entry_method_exploration/20260930_theory_until2200_v1/research/target_bank_frozen_curve_v1/src/kernels.hpp:28)、[E166 query/visited初始化](/data/netg/ACSG/entry_method_exploration/20260930_theory_until2200_v1/research/target_bank_frozen_curve_v1/src/base_engine.hpp:42)、[pool插入与原tie顺序](/data/netg/ACSG/ACSG/detail/CandidatePool.h:13)。

E166正式表的绝对wall/QPS来自共享span+batch4研究核，Default3指该核上的默认入口策略控制；同时回归验收原E99返回。它不是已部署生产E99的现场绝对速度。生产核未切换；同核候选相对比较和停止结论仍有效，未来换核须各臂重测，不能搬用旧绝对时钟。

**算术范围。**精确 IP 下 d_q(v)=−q·x_v，是路径无关的分数。native 推论至少要求：对同一个 q，任何两节点u≠v及任意评分路径π、κ，混合比较 d_π(u)<d_κ(v) 都由同一个严格总序决定，且分数有限并严格低于empty sentinel。只证明scalar内与batch4内各自排序相同仍不足：例如两个kernel分数整体偏移但内部序相同，混合pool比较可能反转。仅要求 GT 排名与 native 排名一致也不够；同节点在两个动作中经不同评分路径产生逆序，会破坏共同 P_L。若还要求 distance-bit/output-bit 保真，条件必须提升到返回 floatbits 一致。NaN/Inf、sentinel分支、ties、提前cap、partial-row恢复、强制标记而不评分均不在下列简洁证明中。

## 命题一：发现集决定最终 top-K

令 D_t 为截止 t 已完成评分的所有节点，P_t 为 live pool IDs，|P_t|≤L。严格顺序和有限分数下：

\[
 P_t=\operatorname{Top}_{\min(L,|D_t|)}(D_t).
\]

证明：初始化消费≤L个不同入口且排序，成立。每次新点评分后，pool未满则插入；已满且新点劣于最差点则拒收；否则有序插入并淘汰最差点。因此逐次归纳保持 top-L 不变量。visited 去重保证已评分节点不会以第二个新身份插入。完整行边界上，visited=D_t；batch中间允许 visited 暂时先于 D_t，因此不用于后面的状态定理。

终止时输出 `Top_K(D_final)`，不足 K 以空ID补位。若 L≥K 且标签 GTK 与该严格顺序的全局 top-K 完全一致，则：

\[
 R_K(S,q)=\frac{|D_{\rm final}(S,q)\cap GT_K(q)|}{K}.
\]

每个已发现的 GTK 节点前面全图至多 K−1 个更优点，因而不可能被 top-K(D) 截掉；未发现点不会输出。这个发现式是该合同下的精确等式，不是通过入口距离代理推断 Recall。

若 native 全局前K为 N_K、标签为 T_K，令
\(\epsilon_{\rm ord}=|T_K\setminus N_K|/K=|T_K\triangle N_K|/(2K)\)，则
\[
0\le |D\cap T_K|/K-R_{T_K}(\operatorname{Top}_K(D))\le\epsilon_{\rm ord}.
\]
因为已发现的 T_K∩N_K 均会返回，发现但漏返的真GT只可能来自 T_K\N_K。该项目前**未被全量证明为0**，不能用 E99/E166抽样一致性替代。不同query的GTK可变化；命题是对各固定q成立。

## 命题二：全局前L中的路径不会被其他入口挤掉

令 P_L(q) 是该节点严格顺序的**全base全局前L**集合。对实际种子 S 定义
\[
C_L(S,q)=\operatorname{Reach}_{G[P_L(q)]}(S\cap P_L(q)).
\]
这里 Reach 是沿原有有向边、只经过 P_L 内节点的可达闭包。

**安全点引理。**若 v∈P_L 被发现，则 pool 中能严格优于它的节点最多L−1个，故 v永远不会被拒收或淘汰。它的 pending 标记只有完整展开该节点才清除；有限图、每点至多首次插入一次、无额外早停/cap，因此最终必展开。

**闭包证明。**S∩P_L 均已发现并会展开。沿 P_L 内路径归纳：前驱展开会评分后继；后继属于P_L，因安全点引理会被保留并展开。因此 C_L⊆D_final，且全部 C_L 最终展开。GT/native排名一致时
\[
R_K(S,q)\ge |C_L(S,q)\cap GT_K(q)|/K.
\]
若只知 native顺序，保守形式为
\(R_{T_K}\ge |C_L\cap T_K|/K-\epsilon_{\rm ord}\)，也可直接使用已证明属于 T_K∩N_K 的证书成员。

**性质与限制。**C_L(S)=⋃_{s∈S∩P_L}Reach(s)，所以证书覆盖函数是标准集合覆盖的单调次模函数；真实 Recall(S) 仍可非单调。E112已推导 single首行闭邻域下界和标准次模 H 覆盖，本次只是其更强、代价更高的 **rank-safe 多跳闭包**适配，不能认领次模框架首次。[E112历史](/data/netg/ACSG/experiment_history/108_one_hop_hub_design.md:3)、[一跳上限及稀疏支持](/data/netg/ACSG/experiment_history/109_source_support_and_query_branches.md:7)

更直接的外部前作是 Prokhorenkova与Shekhovtsov（ICML2020）§4.4（PDF第6页/印刷7808）：已到m-neighborhood、beam≥m、最近m诱导子图连通，则能遍历找到m最近点。**安全诱导子图思想已有**。本地结论只是任意固定有向图、多seed、部分GT下界及当前数值/停止合同的具体推广和核验；未证明其足以成为独立新颖理论贡献。[原PMLR论文](https://proceedings.mlr.press/v119/prokhorenkova20a/prokhorenkova20a.pdf)

P_L 是特权全局信息。计算它通常需要已知真实全局排名或额外访问，不是能免费在线获得的 bound；用既有 GT100 当 P_L 的保守子集仅在 L≥100且 native顺序一致时成立，且可能覆盖很弱。本轮没有读真实底图求 reachability，也没有为此计算新分数/GT。历史已有GT前缀只说明有可能定义更保守的证书，不说明可实现净费用。

这解释了三入口风险边界：保留 default1/default2 只保护它们在 P_L 内的安全路径；被替换掉的 default3，或者途经 P_L 外节点的有用路径，并未获得保护。把 target 本身变得更近也可能先淘汰这类桥节点。不能从“保留两个原入口”推导“至少保留原 Recall”。

### 从安全下界到完整机制等式：外部入口如何进入安全前沿

通常原hub/GT10入口并不在P_L中，初始C_L可能为空。这不表示入口无用。令 E_out 为**本次实际已展开、且在全局前L外**的节点集合，并定义本次边界源
\[
B_L=(S\cup N^+(E_{\rm out}))\cap P_L.
\]
则更完整的等式为
\[
D_{\rm final}\cap P_L=\operatorname{Reach}_{G[P_L]}(B_L).
\]

证明右到左：B_L的safe种子已评分；E_out各完整邻接行已评分，所以其safe邻居均已发现。安全点引理保证所有这些点与P_L内可达后继最终展开。证明左到右：每个被发现safe点来自seed，或来自已展开邻居；若前驱outside即属于B_L，若前驱inside则沿首次发现来源递归。发现时间严格向前且有限，最终到达safe seed或outside-expanded的safe邻居。故safe发现集恰为此闭包。

当L≥K且GT/native序一致，GT_K⊆P_L，因此
\[
R_K(S,q)=|GT_K\cap\operatorname{Reach}(B_L(S,q))|/K.
\]
同q两个动作的Recall差，就是两个后验safe闭包上的GT rescue减damage。若能证明旧闭包被新闭包包含，才得到非下降保证；若后验B保持或增加则充分成立。**E_out/B均是执行后量**，不提供免费线上安全门。实际入口非单调性可以精确定位为：竞争性扩展/淘汰改变outside展开集，继而改变首次进入safe前沿的边界源B，而不是safe前沿内部节点被驱逐。该身份也不是新创造的访问算法或实测频率结论。

## 命题三：完整行边界的 pool 身份可以定义返回响应等价类

取同 q、同图/邻接顺序、同 K/L 下两个**有效、可达的完整行边界状态**。要求上面的路径无关严格顺序、top-L(scored)不变量、visited=已评分节点、pool内非pending节点已完整展开其邻接行、同一固定nearest-pending调度、无额外cap/早停/随机补点。两状态若具有相同 live pool ID 集合 P，则继续运行主核后具有相同最终 pool/返回ID；它们的 pending、visited、NDC及wall可以不同。

**证明的耦合。**按两个状态 pending 并集里的最优点推进。

1. 若 v只在状态A pending，则B的共同pool中v已完整展开，所以 N(v)⊆D_B。若pool已满，N(v)\P 都劣于当前共同cutoff；若pool未满，D_B=P，从而无这类外邻居。A补展开v只会评分并拒绝已在B评分的劣点，不改变P，清除其pending；cutoff以后只会收紧。
2. 若 v在两方都pending，则共同展开。visited差异仅可能位于P外、劣于cutoff的已评分节点，任何会被接受的新点不可能已visited却不在P。因此两方按照相同邻接順序接受相同节点，发生相同pool变化及相同保留/淘汰pending变化；额外被拒评分可以不同。
3. 每次耦合至少消去一个pending或首次发现新点；有限节点及去重使过程终止，最终P相同。

这里“相同pool”**不表示 visited/pending 物理状态相同**，不保证trace相同，更不保证NDC/wall相同。它是返回ID的商空间结论。若输出距离bit也须一致，需进一步要求两状态同节点评分bit相同。历史 C1/C0 的完整状态合同用于恢复trace、成本和真实继续执行，不能用此定理删掉实现中的visited/pending或跳过计费。

该命题排除一个常见伪反例：声称visited含有全局更优GT、该GT又不在相同pool，却仍声称pool=top-L(scored)。这种状态本来不可达。真正合法的成本差异例是：节点2已评分而因劣于节点1被淘汰，与节点2尚未评分两个状态有相同pool={1}；展开1时是否需要重评分2影响NDC，但都返回1。合成核验保留了这个例子。

**理论用途。**若两个入口动作产生相同有效pool，它们可作为**固定同q**的同一返回响应标签类；动作身份不必被强迫唯一匹配。这不是跨q可迁移标签，也不是对所有新动作保持reward/transition的MDP bisimulation。但观察到相同pool通常已付出主核前缀成本；尚没有廉价可迁移特征能预测该类。它比“同hits/NDC”更强，比“完整trace相同”更粗。不能把未知新动作并入已知等价类，也不能把返回类与成本类合并。

initial pool相同在当前mode2通常就是同一实际seed集合，朴素完整响应缓存已由E46实现；该定理的额外情形是**不同入口轨迹在完整行边界汇合**。当前没有所需汇合trace或汇合率，更没有据此节省主核/teacher费用的证据。[E46完整seed响应复用](/data/netg/ACSG/experiment_history/35_exact_feedback_cache.md:5)

更一般的状态商空间/继续子问题思路也不是新概念：BQ-NCO（NeurIPS2023）§3用bisimulation映射压缩具有递归性质的组合优化状态，其映射保持action–reward轨迹。这里仅证明冻结自动继续执行的最终返回集合相同，费用及动作可行性并未保持，故不能由此宣称已得到RL充分状态或可迁移策略。[BQ-NCO原官方论文](https://papers.nips.cc/paper_files/paper/2023/file/f445ba15f0f05c26e1d24f908ea78d60-Paper-Conference.pdf)

## 命题四：比较符号区域与双动作差分，不要求GTK稳定

精确IP、固定入口动作下，主核的分支由已执行距离比较决定。冻结q0的一条有限trace τ，并列出每次真实比较 i,j 的严格符号，即 \(q\cdot(x_i-x_j)\) 的正负。保留这些符号的query区域是线性半空间交；按分支归纳，区内运行同trace、同返回ID与同评分调用计数。只需实际走过的比较，不需穷举所有全base节点对。

对query扰动δ及任意范数，充分安全半径是
\[
\rho_\tau=\min_{(i,j)\in\tau}\frac{|q_0\cdot(x_i-x_j)|}{\|x_i-x_j\|_*},\qquad \|\delta\|<\rho_\tau.
\]
Sentinel有限性/边界要另纳条件；native float32舍入函数不是该线性形式，实际floatbit保真需要误差界或逐分支验证，不能直接套精确IP半径。若希望保持完整路由+主核响应，还须包括上层router及其模型变换后的比较；此命题默认入口动作已固定。

**碰撞核对。**Bosch与Storandt（ICAPS2025）Definition5的Search-Path Diagram已按返回节点划分query空间；Theorem1用greedy路径局部Voronoi单元的交与路径间并描述该响应区域。其定义对任意d成立，实际精确构建主要在2D，高维用离散搜索。当前有限beam、IP、多个入口及visited/pending的程序比较适配不能认领“路径区域证书”为原创；对当前合同的价值是给出比画像入口误差更强的响应条件，以及下面的**双动作相对Recall零差**，而非已证明新颖论文。[原论文PDF](https://ojs.aaai.org/index.php/ICAPS/article/download/36113/38267/40186)

设同一个query q下两个动作的返回K-ID集合为 A(q)、B(q)，真GT为 T(q)。一般有
\[
\Delta R(q)=\frac{|(A\setminus B)\cap T|-|(B\setminus A)\cap T|}{K}.
\]
若两动作在q0返回相同K-ID集合，并且q'在两条trace的共同保真区域内，则A(q')=B(q')，所以 **ΔR(q')=0，无须GT稳定**。共同返回可以同时变得更好或更差；零差是两动作之间的比较结论。

若共同区域内A、B各自固定但不同，T与T'变化，则
\[
|\Delta R(T')-\Delta R(T)|\le\frac{|(A\triangle B)\cap(T\triangle T')|}{K}.
\]
只需限制与两个输出差异有关的GT变化；要求整个GTK固定通常过强。反之，单一动作同返回ID不保证其 Recall 恒定，因为GT可能跨边界。相同NDC更不保证wall恒定。

当A/B是满K个不同真实ID的集合时，\(|\Delta R|\le |A\triangle B|/(2K)\)。而A=B当且仅当对**所有可能K-ID真GT集合**两动作Recall相同：充分性直接；必要性取T=A，若A≠B则A为满召回而B少于满召回。这解释为什么完整返回响应等价比历史某个GTK上的hits并列更强；它仍不提供跨query迁移，因为A/B本身可能随query改变。

## 反例与费用：为何入口距离、hop、加法代理都不足

**须区分哪种顺序。**在共同严格路径无关分数、完整邻接行、无额外cap且所有seed都被消费的条件下，仅重排初始seed顺序不会改变初始化pool；仅排列某行的同一有效邻居集合也不会改变该行结束的pool/pending及后续展开ID/NDC。证明按行归纳：该行完成后pool是原D加这一行未见点的top-L，flags只由是否已展开及是否最终保留决定，和行内顺序无关。这不保证实际评分请求的顺序、全部trace字段（如first-entry distance）或wall相同；native batch grouping/ties可打破前提。故真正的动作交互来自选择/替换了哪些seed、哪个点先展开并挤掉桥，而不能把只给相同三入口换排序当作新的信息来源。

纯符号强连通6环，节点ID即严格rank：`0→1→2→3→5→4→0`，L=2、GT1=0。seed4能返回0；更近seed1停在1；共同seed{1,4}中1先展开引入2，4被挤掉，仍返回1。图/GT/主核均固定。更近入口与增加入口均可能降低Recall。该现象已有145与ABS先例，合成例不是NSG构图产物，只是独立数学核验，不能推断真实发生频率、真实图违反哪些导航条件或不可学习性。

因此新增动态 H 外target和default1/default2组成三入口，需要完整 **联合动作** 监督或响应证书；single action有效、三条single收益之和有效、保留两点、路径更短均不充分。E30已使用等效三元组集合；E32已做完整56动作精确期望Recall；E36已做非加性集合势函数和多步换点。把新目标叫set loss、RL或VOI不会自动提供新缺口。[E30](/data/netg/ACSG/experiment_history/19_equivalent_teacher_sets.md:7)、[E32](/data/netg/ACSG/experiment_history/21_direct_reward_policy.md:7)、[E36](/data/netg/ACSG/experiment_history/25_query_swap_policy.md:7)

E36曾 graph/route总NDC近似不变而完整QPS下降约8%–9%，已证明当前成本口径不能简化为距离调用数量。166 target的路由加重也未被graph节省抵消。因此响应标签至少要分开：返回集合/Recall、图展开及评分、完整wall；同返回响应类内部可以有更贵的执行。[E36 wall](/data/netg/ACSG/experiment_history/25_query_swap_policy.md:26)、[166历史](/data/netg/ACSG/experiment_history/166_target_bank_frozen_curve.md:3)

## 旧终局响应的全点只读核算

先写独立冻结[协议](/data/netg/ACSG/entry_method_exploration/20261002_theory_until1300_v1/response_equivalence_protocol.md)，再打开E166已曝光返回ID、hits和NDC；12:10完成两集全部6点、3方法全3pairs共36单元，全部正负保留。[可复核脚本](/data/netg/ACSG/entry_method_exploration/20261002_theory_until1300_v1/response_class_check.py)、[完整统计](/data/netg/ACSG/entry_method_exploration/20261002_theory_until1300_v1/response_class_check.json)、[114输入身份前后核验](/data/netg/ACSG/entry_method_exploration/20261002_theory_until1300_v1/response_class_input_identity.json)。未打开query/base/GT字节，没有新分数或搜索，未复制raw返回。

以下列出Default3–TargetBank1全部12点，每点n=4096；另两pairs的全部逐点统计保留在JSON，不按结果删取。

| 数据 / K/L | 相同K-ID集合行数 | 同hits但K-ID集合不同 | 同K-ID集合中graph NDC不同 |
|---|---:|---:|---:|
| Web 1/800 | 3971 | 26 | 2959 |
| Web 1/1000 | 3998 | 20 | 2887 |
| Web 1/1250 | 4011 | 17 | 2809 |
| Web 100/1120 | 3485 | 61 | 2339 |
| Web 100/1250 | 3532 | 52 | 2334 |
| Web 100/1400 | 3577 | 41 | 2314 |
| Y 1/96 | 3842 | 36 | 3832 |
| Y 1/128 | 3893 | 27 | 3876 |
| Y 1/160 | 3939 | 18 | 3925 |
| Y 100/200 | 3208 | 139 | 3196 |
| Y 100/256 | 3420 | 89 | 3405 |
| Y 100/320 | 3573 | 57 | 3552 |

所有same-return-set行的旧hits完全相同；old-hit差均落入成员替换数给出的对称差上界。终局返回相同而graph/total NDC不同的情况广泛存在，实证支持“返回标签与费用标签必须分开”。**这里没有live pool或prefix trace，因此不是pool身份相同率，也不是轨迹中途汇合率**；不能据此兑现命题三的额外缓存/标签节省。没有逐query完整wall，不能把同NDC当同wall。same hits更弱的并列也不能直接当返回响应类或其他GT下的并列。

另一个必要边界是**同集合未必同有序ID数组**：Default3–TargetBank1的K100，Web各L有20条、Y各L有3条同集合却次序不同；例如Web L1250同集合3532条而有序数组相同3512条，Y L256分别3420/3417条。严格共同总序下同集合排序唯一，因此旧数组至少不能支持无条件共同严格序或位级输出保真的外推。本轮未读距离值，不能区分exact ties、native归约差或其他路径原因；条件定理继续保留其前件。

历史审查代理另用纯stdlib的struct/set/Fraction实现独立重算：36pair-point、147456pair-query、828统计字段全部对齐，114输入hash前后不变。[独立核验结果](/data/netg/ACSG/entry_method_exploration/20261002_theory_until1300_v1/response_class_independent_audit.json)。这是另一代理的统计实现核验，不是新的性能或确认数据。

## 访问候选必须走完的保真链

| 层次 | 能证明的内容 | 仍未证明的内容 |
|---|---|---|
| 选点支持覆盖 | 原target slot/ID位于本次受限访问集合M(q) | 受限访问实际选中相同ID；联合搜索收益 |
| 分数保真 | 同query、同vectorbits、同评分kernel产生相同scorebits/顺序 | 扩大或换候选后argmax身份相同；原ANN选择是全局raw最优 |
| 返回响应保真 | 同实际入口，或合法pool等价，或双方trace符号保持 | 证书便宜、可迁移、方法实际有正Recall增量 |
| 完整费用 | 对matched q计入路由、cache/lookup、选择器及主核wall | NDC节省自动变QPS；历史性能可转移到新执行路径 |

本轮只读旧已曝光桶核算给出：Web/Y旧targetslot覆盖分别33.7646%/45.7275%，Web主R1旧50次救回中40次桶外。它们是支持保留的明显风险，不是新方法测得Recall损失；来自旧选择的局部信号无法完整继承。[只读核算](/data/netg/ACSG/entry_method_exploration/20261002_theory_until1300_v1/bucket_feasibility.json)

“GT10粗筛桶＋raw精排”若覆盖旧原ANN的target，raw精排仍可能选择更高raw分但响应更差的节点，因为原ANN target并非已证明全targetbank的raw全局最优。需要同时证明候选身份保留或主核响应保留；单有raw分数精确不够。

**同query距离memo的保真条件。**把重复target ID、跨层同slot评分复用，只有在函数纯、同query生命周期、同存储vectorbits、同评分kernel/模式、完全同返回floatbits、无隐含counter/RNG状态影响时，才能按调用序列归纳证明每个旧调用返回原bit，进而保留router轨迹和输出。若scalar/batch4不同bit，缓存键必须包含评分kernel身份，或先证明跨路径bit一致。缓存命中要维护需要的审计调用计数；lookup/epoch/reset成本计入wall，并共享同样的Default3 memo控制。这属于等价执行优化，未提供新信息或新论文理论；理论允许保Recall求速度，却不保证实际净节省。

共享优化Default3也不能成为被拖慢的弱对照：若D=T_target−T_default、S_target/S_default为memo净完整耗时节省，候选须同时胜原默认与memo默认，故 \(S_{target}>D+\max(S_{default},0)\)。若只用 \(S_{target}-S_{default}>D\) 且默认memo变慢，会制造比较假成功；完整费用/最低增益门见[成本条件](/data/netg/ACSG/entry_method_exploration/20261002_theory_until1300_v1/full_cost_conditions.md)。

本地源码进一步确认HNSW upper/base使用同一个构造时选定callback和dimension参数，可在**该HNSW callback内部**按query/key复用完整distancebits；不能将“统一callback”误写为必为scalar，也不把HNSW值借给NSG scalar/batch4。底层visited仍按物理slot，memo只省dot，保留visited/heap/tie动作，并分开logical requests、physical dots、cache hits。[初始/上层调用](/data/netg/ACSG/entry_method_exploration/20260930_theory_until2200_v1/research/query_target_transfer_v1/src/common/hnswlib/hnswalg.h:1281)、[底层neighbor callback](/data/netg/ACSG/entry_method_exploration/20260930_theory_until2200_v1/research/query_target_transfer_v1/src/common/hnswlib/hnswalg.h:390)、[构造时IP callback选择](/data/netg/ACSG/entry_method_exploration/20260930_theory_until2200_v1/research/query_target_transfer_v1/src/common/hnswlib/space_ip.h:348)。

## 原始论文与当前合同的关系

| 原始论文 | 实读内容 | 能借用 / 不能跨用 |
|---|---|---|
| Bosch & Storandt, ICAPS2025, Instance-based Approximation Guarantees | Definition5/6，Theorem1，SPD构建与高维离散条件 | 返回区域/局部比较分区已有；有限beam/IP/双动作差分需另适配，不宣称新原创 |
| Prokhorenkova & Shekhovtsov, ICML2020, Graph-based NN Search: From Practice to Theory | §4.4 beam≥m、进入最近m邻域、其诱导子图连通，则找到全部m点 | safe前沿机制已在原文；任意有向图/多seed部分下界与native合同是本地适配，不认领新诱导图证书 |
| Al-Jazzazi等，NeurIPS2025, Distance Adaptive Beam Search | §3队列/已发现集，beam排序与停止分离，§4导航图近似保证、标准beam反例 | top-L已发现集表示是既有不变量；ABS修改停止规则且依赖metric/navigation，不能用于当前冻结IP停止的保证 |
| Baranchuk等，ICML2019, Learning to Route in Similarity Graphs | §3.1–3.3学习query/node映射、GT-hop oracle、learner-state模仿 | 图感知双塔/行动监督/多专家已有；它修改底层评分和调度，假设足够budget到达GT，不能证明固定kernel的入口动作收益 |
| Drakulic等，NeurIPS2023, BQ-NCO | §3.1–3.2继续子问题、bisimulation映射与action–reward序列 | 状态商空间/多轨迹对称类已有；本地pool结论只保持固定继续执行的终局输出，不保持成本reward或任意注入动作 |

链接：[SPD原PDF](https://ojs.aaai.org/index.php/ICAPS/article/download/36113/38267/40186)、[ICML2020原PDF](https://proceedings.mlr.press/v119/prokhorenkova20a/prokhorenkova20a.pdf)、[ABS官方NeurIPS](https://proceedings.neurips.cc/paper_files/paper/2025/hash/904fe070f484231aa26dbdb37816cd40-Abstract-Conference.html)、[ABS作者全文](https://arxiv.org/html/2505.15636v1)、[Learning to Route官方PMLR](https://proceedings.mlr.press/v97/baranchuk19a.html)、[Learning to Route原PDF](https://proceedings.mlr.press/v97/baranchuk19a/baranchuk19a.pdf)。未使用二手综述作为论证依据。

145已证明画像扰动→入口margin→实际路由→搜索输出的分层上界；163已扩展软权重transport→画像/入口翻转→Recall绝对变化。这些是稳定性或误差界，不提供收益符号、有效多入口交互或wall保证。本次条件的进展在主核内部：rank-safe path限制可被挤占的桥、valid pool商空间分开返回与费用、双动作差分可以避免要求全GT稳定。[145理论](/data/netg/ACSG/entry_method_exploration/20260930_theory_until2200_v1/research/routing_bridge_v1/theory.md)、[163条件](/data/netg/ACSG/entry_method_exploration/20260930_theory_until2200_v1/research/soft_mass_transport_v1/pipeline_conditions.md)

## 纯合成核验及证据边界

[独立符号核验脚本](/data/netg/ACSG/entry_method_exploration/20261002_theory_until1300_v1/search_effect_math_check.py)、[结果](/data/netg/ACSG/entry_method_exploration/20261002_theory_until1300_v1/search_effect_math_check.json)。全部整数节点/严格符号rank及有理数比较；未调用native代码，未读任何真实vector/query/graph/GT。

- 4节点所有4096个无自环有向图，两种邻接顺序、L及≤3种子组合，共344064机器案例；cursor版与独立pending-set版输出/发现/展开序列一致；top-L不变量、安全闭包发现及必展开、outside展开边界源闭包的精确等式成立。相同行逆序仍保持返回、发现集、展开ID序列/NDC；未断言评分调用顺序/所有trace/wall相同。
- 677440条实际可达完整行边界状态记录，按共同pool分组：397867次pending不同、98340次visited不同，仍同最终返回；没有把任意人为不可达state用于命题三。
- 6元素宇宙、K=1/2/3、211921组A/B/T/T'，差分支持集等式与变化界成立。
- 有理数 L∞ 扰动361点保持实际比较符号；强连通加入口伤害及同返回不同评分成本反例均成立。

有限穷举用于查实现模型遗漏，不能替代数学证明，也不能证明当前float32全局总序或真实数据上的证书覆盖率/费用。历史agent已审阅命题二/三归纳条件，未发现漏洞；这不是性能独立验证。上述脚本总新真实ANN/NSG/GT调用均0。

## 尚可继续的候选与停止边界

1. **响应保真memo执行。**先证明旧调用bit级复用及同Default控制，再评完整wall；最具体，但已有cache/execution prior，不产生新的Recall信号。当前仅理论审查，未改代码/跑性能。
2. **固定20K raw-target bank按query访问t(q)，再与default rank1/rank2联合。**E116槽绑定的H外输出也随query选槽变化，并已含部分同形的保两入口动作；不能把“动态H外”本身当新缺口。具体未覆盖的是166同一20K rawBank直接访问/选择机制加原rank1/2的联合。必须保留联合响应和damage定义，不能用single加法。rank-safe证书可解释何时安全，但其全局P_L信息昂贵且未知。没有合格响应监督及成本证据前HOLD。
3. **返回响应类监督。**比唯一target-ID教师宽松，比hits/NDC并列类严格；旧标签可知的相同返回可合并，未知新组合不可标负/标等价。历史多教师/direct reward/set policy已充分碰撞，仅改损失命名不足，需一个新的可迁移响应特征/便宜证书才能形成方法贡献。

本轮不会执行以上实验。13:00前交付理论/阅读/候选审查，仍缺任何可靠 Recall–QPS 综合改善的实测替代；原默认、历史停止门及held-out封存继续有效。

## 附录：不假定scalar/batch4共同严格序的保守区间证书

设同一个固定query下，每个节点v的**每一次、每一种允许评分路径**（包括后来进入pool的stored score）都属于已证明有效的区间 \([\ell_v,U_v]\)，各区间有限且低于empty sentinel。允许ties和路径间舍入变化，但仍要求完整行处理、每节点首次评分、保留L个当前最小stored score及无额外cap/早停。定义
\[
Q_j=\{v:|\{u\ne v:\ell_u\le U_v\}|<j\}.
\]
\(\ell_u\le U_v\) 将所有**可能不劣于v**的点及ties都算作威胁，故这是保守条件。

**区间安全引理。**v∈Q_L若被发现，则必进入pool并永不被淘汰。否则拒收/淘汰需要L个不同节点的stored score不大于v本次分数；每个这样的u满足\(\ell_u\le d(u)\le d(v)\le U_v\)，与Q_L只允许至多L−1个威胁矛盾。因此仍会被完整展开；\(\operatorname{Reach}_{G[Q_L]}(S\cap Q_L)\) 全部被发现。

**Q_K返回引理。**v∈Q_K若被发现，则最终返回K一定包含v：最多K−1个节点在任何评分路径上可能不劣于它。这一步需要Q_K，**仅真GT成员在Q_L被发现不足以保返回K**。因而对任意真实标签T_K、L≥K：
\[
R_{T_K}\ge\frac{|\operatorname{Reach}_{G[Q_L]}(S\cap Q_L)\cap T_K\cap Q_K|}{K}.
\]

这允许用严格全路径数值区间证明个别点安全，不需假设所有全库节点之间序完全一致。它没有使命题三的pool response等价成立：两个状态可能存储不同版本分数，interval alone不能同步后续接受比较。本文原P_L/B_L身份及完整Recall等式也未从这些宽区间直接继承。

可以重新定义后验边界 \(B_Q=(S\cup N^+(E_{\rm exp}\setminus Q_L))\cap Q_L\)，则同一首次发现来源归纳给出 \(D\cap Q_L=\operatorname{Reach}_{G[Q_L]}(B_Q)\)。这只描述保守safe集合内的发现机制；真GT的返回下界仍须再交Q_K。B_Q仍是后验量。

在区间退化为路径无关严格分数时，Q_j=全局前j，回到前面的证书。在实际native上，可靠的全base区间可能需要额外原始计算/数值误差分析、成本很高，Q_j也可能为空；本轮没有生成任何真实区间、额外向量评分或native浮点核验。该附录是对数值风险的充分条件，不是可上线门或原创算法声明。

纯符号附录核验使用3节点全部64有向图、7种固定区间、每点全部端点评分选择和实际≤3入口，共57344机器案例（包含ties），Q_L安全展开、Q_K返回、真标签证书及重新定义的Q_L后验边界闭包等式均成立；结果同[数学核验JSON](/data/netg/ACSG/entry_method_exploration/20261002_theory_until1300_v1/search_effect_math_check.json)。核验没有宣称interval alone保pool响应等价。
