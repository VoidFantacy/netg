# 完整拒收组能否省去评分：仅理论条件

2026-10-02下午解析研究。没有实现、metadata构建、向量读取、搜索、枚举或计时；不改变当前核、默认和停止规则。本页考察一个可能改善时间的具体计算合同，状态为 **HOLD：完整上界及净费用未知**。它不是新的branch-and-bound理论或实验GO。

按用户最新口径，离线训练和事前metadata构建/校验可以增加投入；无需证明训练更快。本页约束的是上线费用与真实Recall–QPS，当前没有开始任何离线计算。

## 1. 先把质量合同缩到逐ID等价

固定原生产搜索、query、底图、入口、L/K、邻接顺序、原生评分调用路径及浮点环境。只考虑当前pool已满L、没有在途评分的原评分组边界。原kernel按邻接中的未visited节点形成组G（batch4或原有末尾partial组），markvisited后评分，再按原顺序执行拒收/插入。记组开始时原pool的最差good-score为β，good-score是主NSG的−native distance。

如果已有合法完整metadata能证明**组内每个ID在原本调用路径下的评分**满足

    σ_native(v) ≤ U_G ≤ β，所有v∈G，

那么该整个组在原程序中均被拒收：原guard为distance≥worst，等值也拒收；第一个点不入pool，后续点仍面对同一个β。可以不计算这个组的dots，仍按原顺序markvisited、保留邻接/cursor/pending和原组边界，继续后面的原调用。组前后pool存储值、顺序、pending及visited状态与原执行相同。

对每个被省去的原组归纳，若其余评分调用使用相同query/base地址、相同参数/算术路径和浮点环境，并且callback的数值不依赖累计计数或其它被省去的副作用，则全部接受/展开与最终返回ID相同。这里不要求GT同native排序，也不要求全库mixed total preorder；保护的是具体原执行的逐ID输出。因此任何合法GT下Recall@1/@100均相同。

上述“相同状态”不包含NDC计数、实际vector loads、cache、wall或未使用的浮点异常标记。若这些副作用能影响后续数值、程序控制或正式输出，必须另外保持其语义，不能用纯callback证明。**满pool前不能这样省**：分数低的bridge仍可能被空槽接纳。

原组可以位于一行内部；状态还须保留active pivot、该行下一邻接位置以及此前组留下的updated/cursor累计值。active pivot即使已被更高分点从pool淘汰，原程序仍要扫描余行；不能因此跳过剩余邻居。

自然耗尽合同中没有基于physical NDC的cap/提前停止；若实际程序按该计数停止，减少请求会改变停止点，须另证或保持原logical计数。若日志/正式输出包含被省去点的真实distance、distance bins或FP异常，也不能声称全部trace相同；本页只保护声明的pool状态、扩展及返回ID/bits，不虚构被省去的distance供memo缓存。

## 2. 必须保持原组，不能随意只省其中一个点

原四点组中只省部分dots、将剩下三点改用scalar核，或者把它们移到下一batch，都可能改变它们的存储bits。一个未省点w在原batch路径为β−ε、在替代scalar路径为β+ε，就会从拒收变接受；随后它是否通往GT又能改变召回。这里仅用抽象合法路径差说明所缺前件，未执行数值反例，不声称实机已出现该差。

因此最简单的充分合同是**原组全部跳过或原组全部照旧评分**。如果要部分跳过，须另证剩点保留原数值/跨路径比较安全；距离更准确本身不能替代逐ID等价。原逻辑按未visited邻居动态分组，静态连续邻接块不自动等于原组。metadata必须完整覆盖当前实际G；不能把缺失成员的局部bound当整个组bound。

U_G还必须覆盖每个成员在原组中的位置、原callback参数和路径，或直接覆盖全部可能原路径的上界；只证某个scalar dot的上界不等于证明原batch4全部成员的存储分数。

省去组内评分后，visited为真但该ID并未实际评分。不能将其放入[局部证书](finite_search_strengthening.md)的“fully-scored D”并套用未知分数rank计数。它拥有的是**已证永远拒收**的上界状态：其U_G≤当前β，而未来满pool cutoff非降，永久visited且不会重入。若后续理论使用D，必须显式扩充为带上界的certified-rejected状态。

## 3. 事前完整上界可长什么样

经典MIPS球界已有直接前作：[Ram、Gray，KDD2012，§3.2.1 Theorem3.1](https://rithram.github.io/research/papers/2012/RG_KDD12.pdf)。若事前已证某个有限组/metadata桶中所有实际base向量满足||x_v−c||≤R，则Cauchy–Schwarz给

    qᵀx_v ≤ qᵀc + ||q||R。

本页仅把这个已知实数上界适配到原拒收组。需要再加覆盖**原评分路径**的native误差E_G、中心dot求值误差E_c，以及上界计算自身的向上包络。若有N_q≥||q||，保守形式可写为

    U_G ≥ fl(qᵀc) + E_c + N_q R + E_G，

右边的实际加乘亦须可靠向上包络。R、N_q和各误差不是当前已获取事实；NaN、overflow、FTZ/subnormal等问题须在误差合同内排除或处理。主NSG为−IP distance，不能混入router的1−IP偏移。

更廉价但更松的norm桶界为U_G≥N_q·M_G+E_G，M_G≥max_G||x_v||，同样需要上界计算误差。若G跨多个既有metadata桶，使用所有相关桶的上界最大值才完整；不能只取命中的一个桶。中心dot和桶读取本身收费，四个桶查询也未必比原batch4便宜。

**以当前pivot本身为中心的特定球界通常空。** 理想实数pivot分数≥β，或直接用stored σ(pivot)加非负半径/误差构造时，该上界≥β，无法严格压到β以下。原拒收含等值，因此pivot=β且半径/误差都为0的退化等值仍可成立；先前组收紧cutoff使旧pivot低于新β，也可能令球界非空。这里不声称任意native interval球界都不可能。off-pivot中心或较低norm桶在逻辑上避免上述空性，但必须是事前完整、可校验且在线便宜取得的metadata，不是免费的新信息。

### 3.1 pivot正交残差界不同于pivot中心球界，条件可以非空

令原pivot向量p非零，C=||p||²，Q=||q||²，s=qᵀp。对邻居v事前存a_v=pᵀx_v/C及r_v=||x_v−a_v p||。精确正交分解给

    qᵀx_v = a_v s + q_resᵀx_v,res
            ≤ a_v s + r_v sqrt(Q−s²/C)。

这个分解/残差加速在[FINGER作者预印本v1，§3.2、Appendix A](https://arxiv.org/pdf/2206.11408v1)已有直接前作；本页采用经典Cauchy–Schwarz包络，不采用估计角或平均误差作为逐点安全界。例p=q=e₁、x_v=.8e₁+.6e₂给s=1、r_q=0、上界.8；满pool cutoffβ=.9时可拒收，尽管pivot分数1≥β。这并不与pivot中心球界的空性矛盾，两者不是同一个包络。

实际只能取得native ŝ、事前rounded metadata与范数区间。假设已证s∈I=[s_-,s_+]、a_v∈A=[a_-,a_+]、r_v≤r_+、Q≤Q_+、0<C≤C_+；I须包含原pivot全部误差，不能把ŝ当精确s。令m²=inf_{s∈I}s²，B=Q_+−m²/C_+。完整区间sound时B≥0且r_q≤sqrt(B)。所以可用更松但保守的实数上界

    max{a_-s_-,a_-s_+,a_+s_-,a_+s_+} + r_+ sqrt(B) + E_v。

端点乘积处理负a/s；加乘、m²、除法、抵消、sqrt及上界存储仍须可靠向上/向下包络。若计算得负radicand、分母不能排除0或metadata合同不成立，应停用证书，不能用随意clamp“修复”并继续承诺安全。组上界取全部实际成员/原路径上界的最大值。区间太宽会令拒收条件为空；当前没计算真实区间或覆盖率。

### 3.2 更重离线训练可以选投影，但应学习完整时间对象

另一个不依赖具体pivot的已知正交分解：固定真实正交投影P，事前存Px_v及||x_v−Px_v||，上线取得Pq及||q−Pq||，则

    qᵀx_v ≤ (Pq)ᵀ(Px_v)+||q−Pq||·||x_v−Px_v||。

加入原路径native误差与所有feature/bound误差即可送入整组拒收条件。这允许离线学习更适合真实query/图的子空间，训练成本可增加；但low-rank误差小不自动使更多原组满足U_G≤β，也不自动减少完整wall。事前SVD的float文件不自动表示精确P²=P=Pᵀ；须证orthogonality/残差包络，或使用精确coordinate子空间。这里没有生成或选择P。

精确实数下，如果P'在P上增加一个正交单位方向z，记原残差q_res=az+q₂、x_res=bz+x₂，则

    ab+||q₂||||x₂|| ≤ sqrt(a²+||q₂||²) sqrt(b²+||x₂||²)。

因此嵌套子空间的该实数上界逐点非增，整组可拒收集合在相同原执行状态上可以扩大。这是Cauchy–Schwarz的直接推论，不是新的低秩定理；浮点实现的不同误差包络未必非增，取全部已证上界的min仍为可靠上界。维数更高也增加feature计算、metadata带宽和bound费用，不能从更紧包络推出QPS更高。

离线目标因此应与**上线完整计划时间**关联：真状态的cutoff和原组分布、被省计算的实际费用、必付feature/bound费用及交互代价；仅优化全图residual能量或训练MSE没有这个保证。它们的真实分布与代价未知，不能以理论分解替代新证据。所有新feature/guard须共享给最快默认，再比较质量动作的净收益。

FINGER的graph-neighbor距离近似/过滤已由本地[9月22日后继筛选](../20260922_until2200_improvement_v1/literature/successor_screening.md)记录，并非新发现。其v1以low-rank角估计、分布匹配与平均L1 correction进行近似；这些不是原batch路径逐点绝不误拒合同，本页不能直接继承。本文也不使用其SVD最优命题作证明；任意已认证P的上述包络成立，选择哪一个P在线净好仍未解决。

### 3.3 更多训练不能免费突破所保留metadata的最坏界

若上线评分比较函数仅使用(Px_v,||x_v−Px_v||)、(Pq,||q−Pq||)，没有额外方向/ID条件信息，且正交补空间非空，那么上述实数上界是这组metadata的尖锐最坏界：q_res≠0时，取未知x_res与q_res同方向且具有声明范数，即达到proj-dot＋两残差范数乘积；q_res=0或x_res=0时也等于精确分数。

因而当此上界高于cutoff，仅凭同一组数值或平均残差角训练不能对所有合法completion给出更小的逐点安全上界。可以通过更多方向metadata、完整球/椭球约束、合法support条件或附加在线计算收紧可行集；更重离线训练也可能把这些结构编码进额外特征，但那已增加可见信息/费用合同。本论证约束这组受限metadata，不声称完整已知索引缺Shannon信息，也不证明真实拒收率低。

平均L1误差不是逐点sup界；罕见大误差可以和任意小平均并存，经过search-state选择后条件误差也可能改变。若用随机/分布界而非确定性证书，必须另给选择、全路径事件和最终召回风险合同，不能继续使用本页的逐ID完全等价结论。

### 3.4 概率证书可经首次差异耦合给出风险界，仍不是确定性保真

固定原索引θ、query q和原native程序；其原trace及每次实际callback路径独立于随机metadata R。若对于原trace中每个distinct请求v及其原路径，最终使用的上界满足

    P_R{U_v(R,q)<σ_original-path(v,q)} ≤ δ_v，

且这个δ_v已包含内部多stage、维数/模型选择及所有数值误差风险，那么不用假定事件独立：在第一个错误省组之前，两个执行保持§1的logical pool/visited/pending及后续保留callback bits/path的coupling，physical NDC/cache/wall可以不同；首次错误只能属于原trace中的某个成员。union bound因此给

    P_R{返回与原程序不同} ≤ min(1, Σ_{v∈D_original(q)}δ_v)。

错误之后的轨迹可以自适应改变，不妨碍这个首次差异证明；D_original及原路径本身须与R独立。若同ID会出现多个原路径/请求，则对这些实际原请求的完整事件union，不能用distinct ID误省预算。本地永久visited主核满足distinct，但不同router阶段不能自动合并。

U_v的事件须定义于固定originaltrace对应状态上的**完整guard程序**，包含R-dependent内部选择；不是错误后实际trace中任选一个点的fixed-pair误差率。

两侧Recall∈[0,1]且好事件逐ID相同，故对每个K可得E_R[Recall_new−Recall_original]≥−δ_total；同一好事件同时保护全部评估K。这个risk界不承诺任何给定R一定保真，更不承诺召回严格提高。独立未来query分布可再用塔式平均；按R挑选query、按fit结果选择R或内部多个上界，须把相应selection纳入风险合同，不能条件于一个“被挑中”的seed后继续报原δ。

还可说明固定部署R的population风险：对独立query总体Q，令F(R)=P_Q(新返回不同于原返回)、δ̄=E_Q δ_total(Q)。塔式给E_R F(R)≤δ̄。固定0<η<1、δ̄>0时，非负量的Markov界给P_R{F(R)>δ̄/η}≤η；δ̄=0则F=0几乎处处。同一good-seed事件上，每个由该次完整返回派生的K均有E_Q[(原Recall_K−新Recall_K)_+]≤δ̄/η。不同K若另跑不同配置，须合并其事件预算，不能免费同时保护。

这个两层风险界只在metadata原抽取分布与Q独立的合同中成立；选择过的R仍不自动享该保证。事前有限family若每个生成流程确有δ_i，可各自分配η_i后union，Ση_i控制整个family，再允许fit挑选；训练改变R分布须重证δ_i。这里只手推，没有选择任何δ/η/family、seed或样本，也没有建立实际population或QPS证书。

[ADSampling，Gao、Long 2023作者预印本v1，§3 Lemma3.1–3.3/Theorem3.4、§4 Corollary4.1](https://arxiv.org/pdf/2303.09855v1)已有可靠距离比较、内部stage预算及整个ANN同返回的概率前作，本地9月22日也已记录。这里仅明确原batch、原native与随机metadata的适配前件。不能把一般“被选中的点固定pair失败率δ”直接当history-conditional δ；上述原trace首次差异耦合或真正uniform/conditional合同才可避免选择偏差。

该论文以理想orthogonal变换保欧氏距离；真实float变换后的full dot不自动与原raw核bits相同。若要套本页原输出合同，未省原组仍须保留原callback，概率界还须覆盖true-to-native和bound误差。论文§8给IP逐比较归约：非零q/x下，将raw阈值β换成依赖||q||||x||的单位向量距离阈值；它不是把raw-IP库改成统一cosine/L2排序。零norm、超出可达范围的阈值、strict/equal及native误差均须单独处理。

查询变换、风险检查/metadata访问、fallback原组及cache交互全部线上收费；内部stage更可靠可以更慢。本文没有选δ、随机矩阵、训练seed、query或任何真实风险/速度点，状态仍HOLD。

概率过滤的默认变体也不自动属于“逐ID保真”的默认集合J：它需要单独声明真实质量/随机风险和公平成本合同，保留原默认；不能先让默认损伤，再降低候选的质量门。确定性整组证书与随机risk候选在保证类型上必须分开。

## 4. 一个非空解析状态，以及它没有证明的事情

设合法满pool的good-score为10、9、8，β=8；原接下来的评分组全是已知norm≤7的base，query norm为1且所有原路径误差≤.1，则U_G≤7.1<8，整组确实可拒收。将前提中的norm/error metadata视为事前给定，不读取或构造任何向量。这个例只表明条件不是逻辑矛盾；没有真实组分布、覆盖率、bound紧度或计时结论。

反之，单个pivot到邻居距离小、邻居样本低分、上次运行拒收或GT10亲和低，都不足以证明这个完整原路径上界。当前搜索可能有高分桥，错误省去一次就可能改变后续发现。根本未满pool的低分点也不能跳过。

## 5. 完整费用与共享默认必须一起计算

记具体改造的完整时间为T_elide、原时间T_orig；metadata读取、查询/缓存、bound运算、分支、visited处理、输出和变化后的cache效应全部属于T_elide。形式上

    T_orig − T_elide = 被省原计算的时间 − 全部新增和交互时间，

只是费用分解，不把dot数量换成已知微秒，也不保证右边为正。batch4对多点共享query loads/指令，省四个dot不等于四倍scalar时间；metadata高维dot或多桶读取可能抵消节省。构建成本不是主要优化目标，但它也不能证明在线净收益。

此类逐ID等价优化若同样适用于原默认、memo/handoff及其它候选，必须先形成**共享该机会的最快默认**。候选的门槛是T_candidate,elide<T_best-default,elide且Recall条件满足，而不是只胜未优化旧默认。它本身只保持召回；与某种质量动作组合后的相对完整时间仍未知，不能据此宣称可靠Recall–QPS综合改善。

## 6. 当前研究结论

相较“证明全图搜索结局”，整组拒收合同只需要当前组的完整上界，因而给出一个更具体的计算问题。但完整可得性、原路径数值包络、dynamic groups覆盖、metadata内存/查询费、共享默认净费用都尚未闭合。球/范数bound和branch-and-bound已有直接前作，本地已有同初始化缓存、one-hop、共享原核优化；本页没有完成系统新颖性检索。

这一对象可继续做理论审阅，不能实施或跑实验。本轮没有创建新的metadata、改评分/visited/停止核，亦没有声称真实覆盖率或性能收益。
