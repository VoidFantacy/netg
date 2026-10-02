# GT10代理到有限搜索效用：前作与反例审查

日期：2026-10-02；作者角色：history_gap_audit。终稿于15:35（Asia/Shanghai，UTC+8）冻结。依据[下午协议](protocol.md)，本次只手推、读原论文与静态历史文件；没有执行ANN搜索、模拟、枚举、向量评分、训练或新增统计。上午封存件不修改。目标仍是完整Recall@1/@100–QPS，本文没有真实性能结论。用户最新允许离线训练更贵：本文不要求训练省费，要求上线表示/获取/选择/执行完整费用兑现；本次仍不开始训练或metadata计算。

## 1. 先分清三个不同的一阶量

固定底图、核、L、K、动作族A和native算术合同。Q为总体query，z(Q)为单位query，a_h(Q)为GT10到hub h的硬/软权重。现行画像的总体对应量是

\[
v_h=u_h+nE[a_h(Q)z(Q)],\quad p_h=v_h/\|v_h\|.
\]

它最大化给定单位方向的线性亲和目标，不能把这个闭式性质写成有限搜索最优。它是按目标归属加权的**query逆向矩**；它不是E[目标特征|query]，也不是实际入口效用的回归系数。有限先验u_h、各hub的权重质量及归一化还会改变方向或消除幅度。

另两个量是：给廉价在线可见表示X=φ(Q)的条件目标矩μ(X)=E[ψ(T)|X]，以及真实动作条件效用η_a(X)=E[U_a(Q)|X]。U可以先是一个固定scalar目标；若要保持Recall@1/@100并改善wall，则须分别处理质量约束及时间，不能用任意Recall−λNDC把整个目标替换。给定完整Q和确定配置，GT/response本来由Q决定；条件期望的非退化性来自压缩X或环境随机性，不是GT标签在Shannon意义上提供了Q之外的信息。

本地[20260922理论](../20260922_until2200_improvement_v1/theory.md)第1、3–6节已经区分亲和闭式最优、方向/路由/搜索两座桥、条件服务偏差、osc遗憾及完整wall。今日的增量是把中间桥的可识别条件展开，不声称上述原则新颖。

## 2. 目标ID不定义query不变的有限响应核

root给出的六节点解析例经独立手推成立。raw-IP二维，q₁=(1,0)、q₂=(0,1)，节点为

| 节点 | 向量 | q₁分数 | q₂分数 |
| --- | --- | --- | --- |
| t | (10,10) | 10 | 10 |
| d | (9,9) | 9 | 9 |
| b | (8,3) | 8 | 3 |
| e | (7,8) | 7 | 8 |
| h | (2,2) | 2 | 2 |
| c | (1,1) | 1 | 1 |

图为h→{b,d}，b→t，d→e，e→c，c→h，t→h。它强连通；两query各自全库分数严格，GT1都是t。完整行、pending最佳优先、最佳L候选池、自然停止，单种子h，L=2：

- q₁：h之后池为{d,b}；展开d时e=7被拒，b仍pending，随后b发现t，返回命中。
- q₂：h之后池为{d,b}；展开d时e=8挤掉b=3，b尚未展开；e发现c=1被拒，自然停止，漏t。

因此把r_h(t)定义成“入口h对目标t的真实有限搜索命中”并要求它不随query变，是一个额外结构假设，不能从相同GT1推出。目标亲和、目标归属或全图可达均未控制非GT桥/bait的排名。在q₂保持其他条件改L=3，b可以保留并最终发现t；预算不变性同样没有免费获得。这个手推例没有声称native真实样本中出现率，也没有新运行。

任意固定L≥2也可解析延伸：保留h→{b,d₁}、b→t，使用长度L的bait链d₁→…→d_L→c→h、t→h。q₁让d₁高于b，而后续bait低于b；q₂让全部L个bait高于b而低于t。q₁会先展开b，q₂的bait始终领先并在展开b前将其淘汰。给各节点二维坐标分别指定两query分数即可。该延伸只用于反驳无条件跨预算命题，不构成Recall@100或native频率证据。

### 2.1 更强的决策反例：同目标特征要求相反的唯一最优动作

六节点例说明一个动作的响应变化；下例进一步让最优入口相反，排除“响应不同但仍有共同最优动作”的空隙。保留t,h,d,b,e,c的上述向量，增加j=(2.1,2.2)、d′=(9.1,9.2)、b′=(3.1,8.1)、e′=(8.2,7.2)。有向边改为

    h→{d,b}, d→e, b→t, e→c;
    j→{d′,b′}, d′→e′, b′→t, e′→c;
    c→{h,j}, t→c.

全图强连通，两个query的全库分数都严格、唯一GT1仍为t；单入口动作族{h,j}、L2/K1、完整自然搜索。h的两query响应仍为(1,0)。j在q₁中先展开d′9.1，e′8.2淘汰b′3.1，随后c1被拒，漏t；在q₂中d′9.2的e′7.2低于b′8.1而被拒，b′随后发现t10。因此j响应为(0,1)，q₁唯一最优为h、q₂唯一最优为j。

任意仅由这个相同target ID t或固定归属w(t)计算的表示均相同，无法同时恢复两个唯一最优动作；将两query赋正概率，随机化target-only策略也有严格正质量regret。**这是对该表示的决策不足，不是全query student不可学习、query之外缺Shannon信息、当前GT10全部失败或QPS结论。** 全q当然能区分两点，且此处没有计算/训练该student。所有数值与搜索步骤仅手推，未运行。

甚至可以让完整有序GT10相同：将t替换为十个节点t_r=(10−0.01(r−1),10−0.01(r−1))，r=1,…,10；b/b′均连t₁，目标链t_r→t_{r+1}，t₁₀→c。所有目标在两query下均高于其他节点9.2，所以有序GT10及其任意固定hard/soft归属平均完全相同；GT1=t₁仍唯一，h/j的R1响应仍相反，图强连通及严格序保持。正确分支发现t₁已足以R1命中，不声称L2能展开整条目标链或Recall10为1；错误分支仍在目标链外被截断。这里只按公式指定有限节点，未生成图文件或运行搜索。

## 3. 条件目标一阶矩何时足够：一个精确而受限的判据

先额外假设有限响应真能写成固定target响应矩阵W：T∈{1,…,m}，E[U_a|T=t,X]=W_at，因而η_a(X)=Σ_t W_at P(T=t|X)。这是对条件平均的充分性要求，不是仅定义W_at=E[U_a|T=t]便能成立。它不是一般有限图事实；当X能区分§2的两query时，固定target版本直接失败。

设Ψ的第t列是固定特征ψ(t)∈R^d；选默认a₀，D_a=W_a−W_a₀。对**所有**target分布p∈Δ_m，μ=Ψp能识别每个相对效用D_ap，当且仅当

\[
D_a\in\mathrm{rowspan}\begin{bmatrix}\mathbf1^\top\\\Psi\end{bmatrix}\quad\forall a.
\]

充分性：写D_a=b_a1ᵀ+β_aᵀΨ，便有η_a−η_a₀=b_a+β_aᵀμ。必要性：若某D_a不在该行空间，线性代数给z∈kerΨ∩1⊥且D_az≠0。取内部p₀并让ε充分小，p₀±εz均为概率分布，μ相同，相对效用不同。因此此量不能由μ唯一恢复。

这说明的是**全部相对效用值**的充分性，不能擅自称任意Bayes动作的必要条件：某个相对效用虽然变化，最优动作仍可能恰好不变。对于动作选择，只需所有同μ纤维有共同最优动作，这是更弱、而且需针对实际utility验证的条件。本文未证明原GT10特征满足其中任一条件。

最小决策反例：T∈{−1,0,+1}，ψ(T)=T；默认效用0，候选效用T²−1/2。p₁全放在0，p₂各1/2放在±1，二者μ=0；p₁应默认，p₂应候选。将两动作同时平移/缩放即可得到[0,1]有界效用，不改变排序。一阶均值没有辨别所需二阶量。它不是GT10真实分布的模型，而是说明缺少loss/response特征对齐时，低维均值不普遍校准。

低秩W可允许某个低维分解，但不证明选定的raw目标方向、GT hub标签或画像刚好覆盖其行空间；分解坐标若靠真实response求得，还须在线廉价计算且可迁移。矩阵秩低也不自动证明任何模型、任何decoder或任何convex surrogate的最小校准维度。这个局部行空间判据应与一般calibration dimension严格区分。

具体地，在固定W并允许任意target特征和带intercept的线性decoder时，令Π=I−11ᵀ/m，恢复全部相对utility的最小特征维数为rank(DΠ)。必要性来自DΠ的行空间必须包含在ΨΠ行空间中；充分性是取DΠ行空间的一组基为Ψ。默认差分消除动作公共效用，Π再消除target常数方向。这个精确维数只针对上述线性恢复合同和**全部simplex分布**；若只允许一个真实可实现GT集合/条件分布子族，必要维数可能更小，不能将任意p的下界直接套在旧样本。它不等于一般convex calibration dimension，不证明给定GT向量或画像满足覆盖，更不证明旧query×action response矩阵低秩时，上线query可廉价推得潜因子。

更直接的低秩前作是[Ramaswamy–Agarwal–Tewari, NIPS2013 §3 Theorem3](https://proceedings.neurips.cc/paper_files/paper/2013/file/a5cdd4aa0048b187f7182f1b9ce7a6a7-Paper.pdf)：固定loss factorization ℓ(y,a)=α_yᵀβ_a+c时，用least-squares学条件E[α_Y|X]，按β_a解码即为calibrated surrogate；正文手证包含近似minimizer，不仅在真均值处排序正确。本文行空间/默认差分是对固定target feature、全部相对utility值恢复合同的线性代数适配，不能以“低秩＋平方回归＋decoder”作为新通用方法。真实ANN还须证明可用的target/response factorization、query表示可识别潜因子、联合action与线上解码费用，不能从有限loss矩阵因子存在性继承这些前件。

### 3.1 一个rank2而一维convex校准的直接前作例

Y/actions={−1,0,1}，损失ℓ(a,y)=|a−y|，默认a₀=0。相对损失两行为D_−=[−1,1,1]、D_+=[1,1,−1]；centered行分别[−4/3,2/3,2/3]和[2/3,2/3,−4/3]，手见线性独立，rank(DΠ)=2。换utility=−loss仅改符号，不改秩。

但scalar s∈R上的convex surrogate |s−y|与nearest-label decoder已校准。对任何条件分布p，Φ_p(s)=E_p|s−Y|的median最优区间包含至少一个label，因此Φ*=min_aℓ_p(a)。在相邻labels之间Φ是两端label risk的线性插值；nearest label对应插值权重λ≥1/2，其另一端风险≥Φ*，故

\[
\ell_p(\operatorname{decode}s)-\ell_p^*\le2[\Phi_p(s)-\Phi_p^*].
\]

区间外clip到端label只会减小Φ，同一界成立。这个界覆盖p=1/2产生的flat median区间、decoder midpoint ties及所有近似minimizer，不止exact median。零维固定预测不能同时对δ_−1、δ_+1最优，所以convex calibration dimension恰为1；它只需选对动作，不需恢复两条全部相对风险数值。

这是[Ramaswamy–Agarwal2016](https://www.jmlr.org/papers/volume17/14-316/14-316.pdf)的直接ordinal前作：Example2定义absolute ordinal loss，Example8给一维absolute surrogate并证明校准，§4.3明确CCdim(L_ord)=1且affine dimension上界不紧。上面的三label插值手证只是补全本地易读边界，不作新定理。

## 4. 一阶query画像到utility系数还差哪些假设

对固定廉价单位表示z，假设真实相对utility确实仿射：Δ_a(Q)=b_a+β_aᵀz(Q)。若E[z]=0，Σ=E[zzᵀ]可逆，则

\[
E[Δ_a z]=Σβ_a,
\quad β_a=Σ^{-1}E[Δ_a z].
\]

所以signed utility一阶矩在已知协方差、正确线性函数类下可以估计系数；单位方向归一化不是这一步。若Σ各向同性，只省掉共同协方差变换，仍需保留各动作系数幅度与intercept。若signed labels改为GT正权重a_h，等式中Δ_a被替换，必须另外证明它们识别同一β。

解析幅度反例：二维unit circle总体的Σ=I/2、均值0；设U_A(z)=1/2+(1/4)(2,0)·z，U_B(z)=1/2+(1/4)(0,1)·z，二者均在[0,1]。这里U可读作廉价z下的条件质量均值；不是已指定有限图上逐query整数Recall函数。两utility-weighted一阶矩的方向分别为e₁、e₂。在z=(0.6,0.8)，条件质量U_A=0.8>U_B=0.7；只用单位画像点积却得到0.6<0.8。即使正确signed moment且各向同性，消除幅度也可反转动作。没有进行采样或模拟。

若直接假设η_a(X)=b(X)+λ(X) zᵀp_a、λ(X)>0且对a公共，dot排序当然正确；这是**rank-affine充分条件**，有审查价值，却几乎直接要求目标排序一致。真正机制论证应给出更原始的joint distribution/响应结构推出它，或说明有界action-dependent残差，不能把该假设本身当解释。

一个确切但很强的生成充分例是：latent Z为basin，z|Z=h服从vMF(p_h,κ)，各basin先验相同、κ共同；a_h(Q)是真实后验；无偏的总体weighted moment方向恢复p_h；且动作响应W_ah=c_h+γ1[a=h]，γ>0共同。此时posterior排序等于dot排序，期望utility排序等于posterior排序。一旦κ/先验不同，需κ_h zᵀp_h+logπ_h+logC_d(κ_h)；一旦W不是上述共同diagonal benefit，需要用W解码posterior而非选最大basin概率。GT10人为硬/软权重尚未被证明是真实vMF posterior，raw prior也未被证明collinear于总体mean。本例仅是充分模型，不是本地已成立理论。

而且对现行hard画像，上述精确责任前件有直接结构冲突：finite κ_h与π_h>0使vMF密度在整个sphere严格正，posterior每个h严格正；GT10-hard在H>10时每query最多10个非零hub权重，因此不能等于这样的posterior。这个正面模型必须称不同assignment的toy充分模型，不能解释为现行hard已具可成立的精确生成前件。现行finite-bank soft也不能仅当作“精确后验待证”：§4.3将证明连续非退化vMF下的更强finite-image冲突。可保留近似责任或直接moment条件，但须另给残差。零支持/截断密度可允许稀疏posterior，support/normalizer须重新推导；κ→∞在unique最大时通常只给单类onehot，不自动得到GT10多hub责任。方向先验u_h也不等于latent类prior π_h；两种prior不可混用。

### 4.1 更强的GT10算子反例：响应理想仍可错排序

root的第二个解析例经独立审阅，核心成立。它只固定画像算子和合法H，不声称整个QGT hub生成器必产该H。单位query A=(1,0)权重49、B=(0.1,√0.99)权重1、C=(−0.1,√0.99)权重50；H_good=e₁、H_bad=C。真实targets为±M_j e₁，M_j≥20互异；A/B的GT10均正类，C均负类，每query十个目标的hard归属完全在相应hub，故query权重和仍为1。原先验各一个raw hub给

\[
p_{good}=\operatorname{unit}((50.1,\sqrt{0.99})),\quad p_{bad}=C.
\]

B的两分数为6/√2511≈0.1197和0.98，因此GT10闭式代理选bad。可行同unit-linear族p'_good=e₁、p'_bad=−e₁却对三个query均选对类。将上述query权重共同乘r并令r增大，good方向趋于unit((49.1,√0.99))，B仍错，因此不是靠有限raw先验才制造的现象。

K=L=1的四环核心good→targetPlus→bad→targetMinus→good说明完美类响应：正确类入口发现global GT1，错误类的异类target比seed差而被拒。B的正target分数≥2，超过bad=0.98，故正确类确实命中。四节点是压缩核心示意；要满足同一库的真实GT10目标数，须使用下一段完整GT链而不是只有两个target。此时**query-invariant target类响应核可以成立，proxy仍错**，与§2揭示的响应分解断点是两种不同反证。

扩展至L≥K时必须明确低分wrong GThead在pool未满时可能先被接受，不能把L1拒绝直接搬过去。每类至少max(10,K)个target，GT链按M_j降序，head取M_max；每hub接本类GT链head及至少L个distinct bait的链，GT链尾跨到异类hub，完整图强连通。bait为α_j u_h，α_j∈(0.1,0.9)。在wrong类query下，所有bait都高于异类GThead，优先展开并在head展开前填池淘汰它，尾回已visited同hub；正确GT链的前K个节点是global前K，L≥K保障逐个保留/展开，K<10时不声称剩余GT链节点也属于global前K。α避跨节点ties。三入口扩展还须L≥max(K,3)，给实际joint图且所有跨类出口均经低分head，不能以三个single响应相加代替证明。root正文负责完整构造，本文只记录独立审阅的成立前件。

这个例证明：在同一受限unit-profile函数族内，GT10方向亲和代理的总体/重复权重极限最优可以不是真实质量风险最优。不能把它扩大为所有非参数surrogate的Fisher不一致、所有GT10真实数据负效用，或可靠QPS命题。

### 4.2 非vMF的cap充分例：有内容但限制很强

独立手审root的新cap命题：若hub h的所有正权query和方向prior都在中心μ_h、半径ρ_h<π/2的球面cap，正合力v_h非零。沿μ_h投影至少cosρ_h乘总权重，垂直范数至多sinρ_h乘总权重，因此p_h也在同cap。给真实类h的query到μ_h角距≤r_h，画像误差angle(p_h,μ_h)≤ε_h，任意其他j中心距δ_hj；own距≤r_h+ε_h，other距≥δ_hj−r_h−ε_j。故

\[
δ_{hj}>2r_h+ε_h+ε_j
\]

足以让h点积严格胜j。以r_h=ε_h=ρ_h、ε_j=ρ_j代入得δ_hj>3ρ_h+ρ_j；保证两方向取max，共同ρ需要δ>4ρ。这是标准球面triangle/positive cone论证，未涉及搜索、成本或新方法。

若说人口ε=0，必须是a_h重加权后的类query分布绕μ_h旋转对称且均值非零，或权重自身保留这种对称性；未加权query总体对称不足以推出E[a_h z]平行μ_h。有限prior、样本偏差仍需独立ε。

hard支持也有限制：要求每条正a_h样本在cap_h且上述caps强分离，就排除了同一query同时给不同hub正权；否则该query落在两个互不相交caps。这一精确充分例可以在GT10所有目标同hub的一类责任模型成立，故不是vMF式全support冲突的空前提；但不能解释一般多hub GT10-hard责任。即使标签/排序全部正确，仍须声明目标类与实际finite response的桥及完整费用。E134方向稳定性不曾证明所有query被小cap覆盖，不能拿稳定mean替代cap前件。

### 4.3 fixed-target归属的有限值限制：soft也不能精确等于非平凡vMF后验

静态实现[旧E106 prepare.py:54](../20260920_gt10_conditional_mechanism_v1/src/prepare.py:54)独立确认hard逐GT rank加0.1，soft用unit(target)对固定raw H打分、manifest全局温度，归一化后各rank加1/10；query只在后续query加权聚合进入。数学上固定有限目标库、H和全局温度时，w_h(t)固定，因此a_h(q)=Σ_{t∈GT10(q)}w_h(t)/10只取有限多个向量值。此语义不证明同ID在不同BLAS路径字节相同。

对d≥2的标准连续球面vMF混合，π_h>0，natural parameter ξ_h=κ_h μ_h。后验比满足

\[
\log\frac{ρ_h(x)}{ρ_j(x)}=b_{hj}+(ξ_h-ξ_j)^\top x.
\]

若某对ξ_h−ξ_j≠0，任一该线性函数的level set在球面测度为0；vMF混合有连续正密度，有限个level的概率仍为0。a只取有限值，a_h/a_j的正值集合也有限；ρ全正排除a含0的情况。所以P(a(X)=ρ(X))=0。这不需证明GT开cell；root的另一证明也成立：exact-IP有限GTK区域内a常数，连续posterior若a.e.等于a，必在球面开patch常数，其linear log-ratio迫使所有ξ相同。

退化例外是所有ξ_h相同，posterior全局等于类prior π；还需a全局也等于该常数，单凭μ相同不够。d=1的sphere只有两个离散点，不适用level零测度论证。有限观察点上的插值、实际FP离散输入或量化posterior、query-dependent归属/温度须另论；本段不拿理想连续论证替代native检查。

因此将当前hard/soft权重**精确**等同非平凡vMF总体后验，比“方向一阶矩对齐”强得多，并不能成立于此标准连续模型；加一个近似责任残差或改成直接moment/cap条件仍是可能数学路径，但尚无残差小/真实response或完整QPS证据。它不否定经验GT10有效，也不把这条有限值与连续后验的基本事实声称为原创统计定理。

这里不能缩写为“a不是任何posterior”：给定q随机选一个GT10成员，再按固定w分配hub，即可构造辅助Z使P(Z=h|q)=a_h(q)，只是它的class-conditional density一般不是该解析vMF族。finite-image反证也没有提供有用的近似误差下界；有限库足够细、分布集中或natural parameters相近时误差可能很小，一阶方向矩甚至可以在a≠ρ时精确对齐。

### 4.4 与hard语义兼容的非空正例：moment可对齐而posterior不同

root补出的正例经独立手推成立。d≥2，Q的unit方向X有密度f(x)=C_d(κ)cosh(κx₁)，κ>0，即等先验vMF(±e₁,κ)混合。目标库各有n≥max(10,K)个±M_j e₁、M_j>1互异，H raw方向±e₁。每条x₁≠0 query的GT10均同sign类，hard全部归相应hub，故a_+=1[x₁>0]、a_−=1[x₁<0]。

保持e₁轴的横向反射不改变f或a_+，所以E[a_+X]的横向分量全0，纵向c_+=E[X₁1[X₁>0]]>0；中心反演给E[a_−X]=−c_+e₁。因此人口GT10方向±e₁，aligned有限prior不偏unit(E[v])方向。有限sample的实际合力仍可有横向误差，不能从此断言每份样本画像精确。

这里latent vMF component Z与服务标签Y=signX₁不同；ρ_+=logistic(2κx₁)处处正，a_+是hard指示，二者不等却不妨碍moment方向对齐。正确hub的GT链按M降序，前K全局最高；wrong GT头低于wrong seed与全部私有bait，至少L个bait先展开/填池淘汰它。L≥K、自然完整继续、解析共同严格序下，correct响应1、wrong0，x₁=0零测。此真实响应桥由显式图族提供，不由latent后验推得。

正例只固定H/hard画像算子和人口分布；没有证明QGT选H器、真实数据、有限fit、native近零ties/underflow或完整wall满足相同前件。它避免了“只能给空正面假设”的问题，也说明§4.3只否定exact posterior等同而没有否定方向亲和可用；不是新的vMF检索方法。

一个更强、也经手审核对的版本能严格改善raw-H的理想Recall：将density改为c cosh(κx₁)1[|x₁|≥η]，0<η<sinθ、0<θ<π/2；raw H为±v，v=(cosθ,sinθ,0,…)，目标仍±M_j e₁且M_minη>1。target→raw-H hard唯一归属仍为sign x₁，转轴对称仍给weighted population moments ±b e₁。选择x₁=x∈(η,sinθ)、x₂=−√(1−x²)，则vᵀx=cosθ·x−sinθ√(1−x²)<0，附近球面开patch密度正。因此raw-H按sign(vᵀx)有严格正概率选错类，人口GT10按sign(x₁)全对；η≥sinθ则没有这种positive-measure错区，等号只有零测tie边界。

若iid fit使两画像chord误差||p_+−e₁||、||p_-+e₁||均≤ε<η，理想score gap≥2η减去两误差仍正，故整个支持域选对。LLN及非零moment只给a.s. eventually或概率趋1，不给事先固定n无损保证；这里raw anchor ±v并不aligned于±e₁，但其固定prior/n渐近消失。截断density的归一化和方向均值不是未截断vMF的A_d公式。same GT链/bait桥在M_minη>1下成立；native FP、实际H来源、有限fit和完整wall仍未知。已测raw-H对照E108是直接本地前作，这个toy不授权重跑它。

同一正例也可满足现行**soft数学归属算子**，而不是只有hard：每个target先按现行合同unit normalization，故±M_j e₁变为±e₁；仅有两个raw hubs ±v、等softmax基准权重（无另加不等class-prior π项；若写w_h∝π_h exp(score_h/T)，则本例π_+=π_-=1/2并抵消）、固定全局温度T>0。正target对+hub的softmax权重α=logistic(2 cosθ/T)>1/2，负target权重为1−α。GTK10同sign类，故a_+(x)=(1−α)+(2α−1)1[x₁>0]。总体中央对称给E[X]=0，于是

    E[a_+^soft(X)X]=(2α−1)b e₁，
    E[a_-^soft(X)X]=−(2α−1)b e₁。

任意固定finite T的非零人口方向仍为±e₁，截断margin与真实GT链响应桥沿用；这个full-positive soft责任无需等于vMF posterior。有限先验/样本偏差须相对缩小后的moment质量(2α−1)b计入，不能从hard样本规模继承方向保证；T→∞使moment为0的极限不可使用归一化/LLN非零结论。本段只解释固定两hub算子的一个非空模型，不证明实际Web默认H、温度、query分布、有限fit、近似路由或成本，未算新向量或生成画像。

## 5. signed相对utility、校准与迁移

真实动作条件均值已知且用精确argmax时，均值就是Bayes决策；平方损失对完整utility向量的非参数总体回归可以识别这个均值。把目标换成语义标签、GT affinity、区域平均或winner ID后，平方损失校准到的是替代目标，不能自动修正response偏差。比较损失/损失加权属标准cost-sensitive reduction，不是换名后的新监督。

winner-only最小反例：廉价可见X相同，默认K100命中均为50；候选比默认胜的概率均0.6。世界A候选增量为+0.10(0.6)、−0.01(0.4)，期望+0.056，应选候选；世界B为+0.01(0.6)、−0.10(0.4)，期望−0.034，应默认。对应候选命中60/49与51/40，都为合法K100整数计数，winner分布一样而期望质量符号不同。这只是手设响应分布，未构造/运行对应真实图。若限定Recall@1单独0/1、并提供成对默认/candidate命中标签，其增量幅度是固定的，此反例不适用；真实多K质量与wall没有这个通用固定幅度前提。

代理g与真实u同量纲时，近似选择ĝ满足ε_route-max，标准bound是

\[
u(a^*)-u(\hat a)\le\operatorname{osc}_a(u-g)+\operatorname{osc}_a(g-\hat g)+\epsilon_{route}.
\]

这已在本地20260922理论出现。它不允许以cosine分数当作Recall单位，不证明各项因果占比，也不保证只改善第二项就改善总utility。默认列不可省。若分别控制Recall@1/@100/时间，应分别给残差/约束，最终仍检验完整wall；本文没有残差大小的新证据。

迁移至少涉及四个彼此独立的前件：监督动作与上线动作完全一致；底图、L/K、seed集合及search kernel的response合同一致；廉价在线表示支持同一条件均值/排序而非GT教师才可计算的表示；fit与评估分布及完整费用可迁移。跨L、single→joint、H内→动态H外、更改访问后suffix/cache都不能只靠相同target标签继承。无限数据/非参数校准不能绕过表示限制或未收费的访问成本。

还应单列top3组合层：即使single效用预测完全精确，选最高三个single也不普遍最大化joint效用。理想无beam竞争的coverage模型中，target类x/y概率0.6/0.4；h₁、h₂、h₃均只覆盖x，h₄只覆盖y。前三single均0.6而第四0.4，选前三joint命中0.6，选{h₁,h₂,h₄}却为1。这个手推例连有限池干扰都不需要；重复覆盖足以阻止从single排序继承joint最优。实际有限beam再增加非单调性。single rank-affine条件用于三入口时，须另有modular utility/互斥覆盖等原始结构，或直接joint action响应decoder。它是标准coverage问题和本地E28/30/32/36的历史碰撞，不是新组合监督。

### 5.1 固定核不等于压缩表示下条件响应可迁移

固定实际U_a(Q)只保证同一完整query的响应合同不变。若线上只使用X=φ(Q)，fit/test在同一X纤维内部的query混合可改变η_a(X)=E[U_a|X]。用§2.1的两个真实有限响应解析点，让X仅由相同target特征决定；fit对q₁/q₂给概率0.9/0.1，test给0.1/0.9。两边X分布完全相同，密度比为1，但(h,j)的条件质量均值从(0.9,0.1)变为(0.1,0.9)，Bayes入口反转。故相同图/GT规则/主核、相同X支持或target标签不能单独证明student排序可迁移。全q表示可区分这两点，这不是对其不可学习的论断。

一个有效但尚未建立的迁移合同是：两分布具有相同η_a(X)，test对fit绝对连续，且r(X)=dP_test/dP_fit≤C<∞。对固定策略π的非负条件quality regret g_π(X)=max_aη_a(X)−η_π(X)，直接换测度给

    E_test[g_π] ≤ C E_fit[g_π].

若采用精确argmax â的条件均值估计，pointwise regret≤2 max_a|â_a−η_a|，再由Cauchy–Schwarz得到

    E_test[regret] ≤ 2 sqrt(C E_fit[Σ_a(â_a−η_a)²]).

该式针对同一有限动作族、真实响应均值、相同表示合同及质量单位；不替代代理到response的桥，也不证明完整wall或模型有限样本MSE。仅给X密度比而不保证共同η不能套用；无覆盖的test区域更不能靠fit低损失保证。

这是标准covariate-shift/importance-weighting前作的条件边界。[Sugiyama、Krauledat、Müller 2007](https://www.jmlr.org/papers/volume8/sugiyama07a/sugiyama07a.pdf) §2.1明确不变的条件输出分布和已知有限密度比；§3 Lemma1的IWCV换测度证明依赖这些前件。本文只读该原文相应部分，不实施密度比估计、IWCV或重新划分数据。相对默认列消除公共难度也不会消除表示纤维内这种条件响应改变。

### 5.2 冻结policy类的signed残差矩还需独立的换测度条件

[同事稿§5.1](decision_information_theory.md)给出较弱的选择校准合同：在一个固定总体P、冻结策略族Π及预测器下，同时控制b_π^P=E_P[U_π−Û_π]；若sup_π|b_π^P|≤ε，则同P中预测最优策略的类内regret≤2ε。该结论通过手审，但不能因X密度比有界就直接迁移这类**signed平均矩**。

解析反例：F两组，candidate的条件K100质量为0.9/0.1，default恒0.49；预测分别为0.5/0.49，Π仅有两个constant动作。P两组各半，则全部Π价值残差为0，预测唯一选candidate。Q两组概率变为0.1/0.9，输入密度比为0.2/1.8且η_a(F)没有变；candidate真实均值0.18，低于default0.49，预测策略的类内regret为0.31。固定原生动作/条件响应、fit policy校准及bounded ratio三个前件同时存在，却未保证target policy校准；正负残差的P取消被换测度破坏。这与§5.1中压缩X内η改变、X边际完全相同的反例是两种独立断点。数字仅手算，不构造搜索或验证数据。

精确分解可明确两层负责对象。固定动作条件均值η_a^P(F)、η_a^Q(F)，预测Û_a(F)，mask M_πa；设Q_F≪P_F、ρ(F)=dQ_F/dP_F。则

    b_π^Q
      = E_P[ρ(F) Σ_a M_πa(F)(η_a^P(F)−Û_a(F))]
        + E_Q[Σ_a M_πa(F)(η_a^Q(F)−η_a^P(F))].

若全部Π的第一项绝对值≤ε_weight、第二项绝对值≤ε_shift，target价值预测误差≤ε_weight+ε_shift，target proxy优化误差ζ再给类内regret≤2(ε_weight+ε_shift)+ζ。共同F条件均值只令第二项为0，不自动控制第一项；若P有完整conditional校准或E_P绝对残差控制，则可以另用ρ≤C推界。只知signed矩上界不能写成Cε。相对默认计划可用真实paired Δ_π替换U_π，公共action残差可在默认差中消去，但action-dependent shift仍存在。

这里是标准importance weighting、条件期望与2ε比较的合同展开。第一项需要importance-weighted masks ρ M_πa（合法ratio已知或带估计误差），第二项需要target条件响应证据；二者并未从GT affinity、低秩或旧训练矩获得。若完整计划费用依赖策略/获取/cache，须对每个冻结T_π直接写同类换测度式，不把它错拆成一个免费动作时间表。

这组条件可以指导**未来**确认合同：先固定预测器/Π/完整调用与默认J，再在未参与选型且来自目标workload的合法确认资料上验证对应真实paired质量和完整time，或取得适用的同时总体误差证书。同P训练矩为0、类内2ε和density ratio存在性都不等于确认。选择已用过确认资料时须负责整个被选策略族/多K/多域/共享默认的同时偏差；wall另需适合实际尾部与相关性的统计合同。本文没有访问/计算确认数据，不得据此恢复实验或给GO。

## 6. 原论文对照：直接前作，不作原创命名

| 原论文与实读定位 | 对本问题的直接作用 | 本地不能继承的内容 |
| --- | --- | --- |
| [Ramaswamy、Agarwal、Tewari 2013](https://proceedings.neurips.cc/paper_files/paper/2013/file/a5cdd4aa0048b187f7182f1b9ce7a6a7-Paper.pdf)，§2–3 Theorem3及正文证明 | low-rank loss factorization、条件mean least-squares与线性loss decoder直接给校准；比笼统“双塔/低秩”更直接的前作 | 条件loss/响应因子不是当前GT10 feature；存在低维loss不能继承cheap online embedding、动作解码或QPS，也不提供所有value恢复的必要维 |
| [Ciliberto、Rudi、Rosasco 2016](https://proceedings.neurips.cc/paper/2016/file/88a839f2f6f1427879fc33ee4acf4f66-Paper.pdf)，§3 Assumption 1、Lemma 1、Theorem 2 | loss可线性嵌入时，学习条件feature均值，再用对应loss decoder，有一致性/比较不等式；是“均值何时够”直接前作 | GT10 weighted query centroid没有提供该loss embedding、条件mean estimator及正确decoder；有限样本/限制类另需证明 |
| [Ramaswamy、Agarwal 2016](https://www.jmlr.org/papers/volume17/14-316/14-316.pdf)，Example2/8、§4.1–4.3 | 一般有限loss matrix的convex calibration dimension及一维ordinal校准；由loss几何约束预测空间而非凭模型名称推校准 | 本文行空间判据只针对给定target feature恢复全部utility差，不能等同该论文一般最小校准维度；§3.1已给rank2/校准维1反例 |
| [Osokin、Bach、Lacoste-Julien 2017](https://proceedings.neurips.cc/paper/2017/file/38db3aed920cf82ab059bfccbd02be6a-Paper.pdf)，§3 | calibration须同时指明task loss、surrogate及允许score subspace；统计与优化规模也重要 | 非参数pointwise校准不证明静态unit-profile函数类能表达有限搜索utility，也不提供在线费用 |
| [Liu、Grigas 2021](https://proceedings.neurips.cc/paper_files/paper/2021/file/b943325cc7b7422d2871b345bf9b067f-Paper.pdf)，§2–4 | predict-then-optimize decision loss和surrogate的风险传递，有明确分布/可行域前件 | SPO+特定连续/对称/密度、可行域条件未在native确定性response上建立；不能称直接替换损失即保证；本地20260922已引用 |
| [Chang等 2015 LOLS](https://proceedings.mlr.press/v37/changb15.pdf)，§2 Algorithm 1、§3 Theorems 1–4 | 以实际rollout后的终局相对cost构造cost-sensitive labels；state/action coverage与roll-in/out不匹配可破坏低代理regret | 不是从目标ID生成response；不保证有限ANN全局最优。固定底图主核的入口决策是单次action reduction，不能把改主搜索policy直接移入范围 |
| [Banerjee等 2005](https://www.jmlr.org/papers/volume6/banerjee05a/banerjee05a.pdf)，§2.2、§3 | vMF mean方向为normalized resultant，mixture posterior含先验和κ；是原型的标准生成解释 | centroid方向充分需要生成/response条件，不能由闭式形式反推数据遵循这些条件；本地20260922已引用 |
| [Baranchuk等 2019](https://proceedings.mlr.press/v97/baranchuk19a/baranchuk19a.pdf)，§3.1–3.5 | graph-global表示、query/vertex双映射、基于BFS teacher的learned-trajectory监督，直接碰撞“学习graph response/双塔”名称 | 它替换主图展开评分，使用distance-call预算及原距离重排；BFS最短hop teacher不是固定native有限beam入口utility。既有方法结果不能迁移到不改主核/停止的合同 |
| [Sugiyama等 2007](https://www.jmlr.org/papers/volume8/sugiyama07a/sugiyama07a.pdf)，§2.1、§3 Lemma1 | 固定条件输出分布与输入密度比下，importance-weighted risk/CV可迁移；是训练到上线分布的直接前作 | 相同原图、kernel或压缩X边际不保证η_a(X)不变；本轮没有估计密度比、测量shift或重新验证student |
| [Ram、Gray 2012](https://rithram.github.io/research/papers/2012/RG_KDD12.pdf)，§3.2/§3.2.1 Theorem3.1 | exact MIPS ball branch-and-bound，qᵀc+||q||r为整ball分数上界，是off-pivot组界/拒收的直接前作 | exact球界不是当前native多路径上界；已知完整bucket、metadata精度、guard及访问费用仍需证明；不继承树遍历/构图替换 |
| [ABS 2025原文v1](https://arxiv.org/html/2505.15636v1)，§3.1–3.2、§4 Claim2 | ordered traversal与stopping解耦、greedy到wide beam的前缀机制及标准beam失败是直接前作 | 与本地多seed/full-row/FIFO仍需独立条件适配；metric/navigability准确性定理不能直接用于raw-IP固定图。Eq1–2 literal≤计数含x自身的offbyone约定不清，仅沿用§3.2机制定位，不claim原pseudo逐行精确对应 |
| [FINGER arXiv2206.11408v1（2022）](https://arxiv.org/pdf/2206.11408v1)，§3.1–3.3、Appendix A/B/C/G | 已知graph-neighbor拒收计算、pivot平行/正交分解、low-rank角近似、分布匹配及实际近似筛选，是当前计算理论的直接前作 | mean L1 correction不是原路径逐点native上界；候选接受后精算不撤销此前误拒。v1为5作者预印本，不与WWW2023六作者版本混记；SVD optimal命题不用于本地证书 |

以上均读原论文对应内容，未使用二手综述替代。论文摘要、定理条件与本地应用分别叙述，不把通用统计决策定理写为ACSG创新。

### 6.1 原文身份与阅读范围复核（15:20）

以下姓名/年份/题名按原PDF首页及官方原文metadata核对；URL沿上表，各节为本轮真正读过的范围，不声称全文实读。

| 年份/版本 | 原文完整题名 | 全部作者 | 阅读范围 |
| --- | --- | --- | --- |
| NIPS 2013 | Convex Calibrated Surrogates for Low-Rank Loss Matrices with Applications to Subset Ranking Losses | Harish G. Ramaswamy; Shivani Agarwal; Ambuj Tewari | §2–3 Theorem3及正文证明 |
| NIPS 2016 | A Consistent Regularization Approach for Structured Prediction | Carlo Ciliberto; Alessandro Rudi; Lorenzo Rosasco | §3 Assumption1、Lemma1、Theorem2 |
| JMLR 2016 | Convex Calibration Dimension for Multiclass Loss Matrices | Harish G. Ramaswamy; Shivani Agarwal | Example2/8、§4.1–4.3 |
| NIPS 2017 | On Structured Prediction Theory with Calibrated Convex Surrogate Losses | Anton Osokin; Francis Bach; Simon Lacoste-Julien | §3 |
| NeurIPS 2021 | Risk Bounds and Calibration for a Smart Predict-then-Optimize Method | Heyuan Liu; Paul Grigas | §2–4 |
| ICML 2015 | Learning to Search Better than Your Teacher | Kai-Wei Chang; Akshay Krishnamurthy; Alekh Agarwal; Hal Daumé III; John Langford | §2 Algorithm1、§3 Theorems1–4 |
| JMLR 2005 | Clustering on the Unit Hypersphere using von Mises-Fisher Distributions | Arindam Banerjee; Inderjit S. Dhillon; Joydeep Ghosh; Suvrit Sra | §2.1–2.2、§3 Eq3.4–3.7 |
| ICML 2019 | Learning to Route in Similarity Graphs | Dmitry Baranchuk; Dmitry Persiyanov; Anton Sinitsin; Artem Babenko | §3.1–3.5 |
| JMLR 2007 | Covariate Shift Adaptation by Importance Weighted Cross Validation | Masashi Sugiyama; Matthias Krauledat; Klaus-Robert Müller | §2.1、§3 Lemma1 |
| KDD 2012 | Maximum Inner-Product Search Using Cone Trees | Parikshit Ram; Alexander G. Gray | §3.2/§3.2.1 Theorem3.1 |
| arXiv2505.15636v1, 2025-05-21 | Distance Adaptive Beam Search for Provably Accurate Graph-Based Nearest Neighbor Search | Yousef Al-Jazzazi; Haya Diwan; Jinrui Gou; Cameron Musco; Christopher Musco; Torsten Suel | §3.1–3.2、§4 Claim2 |
| arXiv2206.11408v1, 2022-06-22 | FINGER: Fast Inference for Graph-based Approximate Nearest Neighbor Search | Patrick H. Chen; Wei-cheng Chang; Hsiang-fu Yu; Inderjit S. Dhillon; Cho-jui Hsieh | §3.1–3.3、Appendix A/B/C/G |

FINGER的[官方v1摘要身份](https://arxiv.org/abs/2206.11408v1)列五作者；PDF首页第三作者拼作“Hsian-fu”，本表用官方metadata的Hsiang-fu。官方摘要的Chang/Yu/Hsieh使用姓在前格式，本表仅统一姓名顺序。WWW2023六作者版本须按该版本另记，不能把其作者列表/年份套在本次实读v1上。其余论文年份按上列实际版本，不从本地引用简称补猜姓名。

## 7. 本地历史碰撞：哪些“新方向”已有实做

| 方向 | 已有直接证据 | 结论边界 |
| --- | --- | --- |
| 真实winner query centroid | [E04 §3](../../experiment_history/04_utility_and_representation.md)、build_search_aware_prototypes.py | 有search-aware标签的闭式centroid早已做过；Recall/NDC局部结果无可靠完整QPS替换 |
| signed utility原型 | [E04 §4](../../experiment_history/04_utility_and_representation.md)、[原构建实现](../../benches/run/build_utility_residual_prototypes.py) | 10K/top32/L64&128，连续Recall−0.05相对NDC，中心化advantage×hardness，normalize(old+0.25 residual)；Web旧验证有小正，缺Y/fullwall，不能写全负也不能当新方向 |
| basin response/transition matrix | [E04 §6 BTG](../../experiment_history/04_utility_and_representation.md) | 图BFS basin transition/diffusion已做；图可达/传播矩阵尚不是query-dependent有限beam utility核 |
| GT条件一阶画像分解/降噪 | [E106机制报告](../20260920_gt10_conditional_mechanism_v1/research.md)、[历史卡](../../experiment_history/101_gt10_conditional_mechanism.md) | 已有B共享组均值+D组内crossmoment、保ESS置换及GroupMean；D方向信号/画像稳定性不自动是Recall因果贡献 |
| query可见utility/student | E25、E36、E104/105、E117/118、E119 | 已有rescue/damage、joint response、linear/MLP/strong model/比较方向；新名字不构成新信息或action。E36 reward为Recall+NDC，不能称QPS训练 |
| 目标区域服务＋低秩/线性编译 | E121–124，[20260922理论](../20260922_until2200_improvement_v1/theory.md) | router state、动作几何ridge、privileged region表及student都已检验；完美教师区域不自动给student可迁移排序，AS双阶段仍仿射 |
| graph-neighbor低维距离过滤 | [9月22日后继筛选:7](../20260922_until2200_improvement_v1/literature/successor_screening.md:7) | 已明列FINGER WWW2023/ADSampling及概率近似非bit parity；本次native-safe整原组合同不是首次提出投影/拒收省dot，不由更贵离线训练继承性能 |

历史STOP约束具体版本，不能推出函数类/方向不可能。但下一提案须指出新结构前件、新监督信息或不同动作空间；仅把旧centroid改称response kernel、把ridge改称低秩双塔、再调loss/温度都没有补缺口。

## 8. 当前可审查缺口及反证门

1. **response分解缺口**：拟把GT10 proxy解释成真实utility，先说明query-dependent桥/淘汰如何进入分解或残差；§2反例必须被假设明确排除，不能用相同target亲和跳过。
2. **表示/decoder缺口**：即使query-invariant W成立，需给选定ψ的loss行空间对齐或更弱决策充分性。§3同mean反例和§4幅度反例为最强廉价解析控制。不能先声称低秩、后把正确utility坐标当作免费输入。
3. **监督迁移缺口**：若用实际response学结构，最简单同监督baseline包括带intercept/amplitude的直接signed回归、默认列、既有signed residual；joint动作不能由single相加。这里只定义理论比较对象，没有训练授权。
4. **性能缺口**：本轮没有新trace/计时/频率；纸面低维、校准或证书没有证明完整QPS。不能从这些命题给默认替换GO。

当前判断：可完善解释和失败边界；没有足够前件把GT10闭式亲和证明升级为有限搜索Recall–QPS保证，也没有据此成立的新实验/实现GO。

## 9. 独立交审记录（15:35终稿）

以下只手推与静态读同事稿件，未运行数学检查、枚举或统计。

- [GT10桥](surrogate_to_search_theory.md)：反例、cap、finite-image与截断对称正例成立于各自声明的前件；补正四环只是核心、GT链降序/firstK安全、3seed实际消费需L≥max(K,3)、hard与finite-vMF后验支持冲突、有限sample必须另计δ_h。soft正例是直接moment对齐，不以posterior等同获得。
- [信息/费用](decision_information_theory.md) §6.1–7：完整付费fallback分解、固定费用模型的凸可行集/dual、跨K/数据约束及最强固定默认门通过；共同费用、可执行动作、条件响应、suffix状态与控制版本均须固定。C̄≥0只在同prefix强制默认控制也纳入所比J的前件下成立，不是所有未实现计划的事实。
- [局部搜索](finite_search_strengthening.md)：full-pool/whole-row/永久visited条件下，局部封闭、威胁计数、safe paths和任意GT损伤界通过；有序pool共同preorder耦合、helper FIFO ties精化及只查未来可展开行的guard-closure亦通过。上界/完整边界/已付前缀和旧返回仍有获取费用，实际native mixed序与成功频率尚未证。
- **实质修正：仅保护任意旧ID加新GT不够推出strict提升。** 原下界ΔRecall≥(|N|−|B\W|)/K本身正确，但新旧返回均sizeK且W、N不交，故|N|≤K−|W|=|B\W|，这个下界永不严格正。latest agent自审指出该容量限制，本审阅先前漏掉此步，现已复核并通知root。若另有合法已知nonhit Z⊆B\W，可改为Δ≥(|N|−(|B\W|−|Z|))/K；或已知旧总hits h_B、保护的旧hits h_W，可用(|N|−(h_B−h_W))/K。解析K2例B={oldGT,nongt}、W={oldGT}、Z={nongt}、N={newGT}给+1/2。没有读取新GT或据此建立本地证书。
- 容量与入口要分开：同有序初始化、实际seedcount≤小L、无random padding/cap/早停、永久visited、完整行评分且真正best-pending时，小L的expanded rows可成为大L执行前缀。严格统一mixed序是一个充分前件；原helper FIFO与同地址/同路径纯callback还可用共同prefix的storedbits构造arrival-key证明，不需全库mixed序。独立suffix后Recall仍需GTK/native分离或全局同序；prefix只给发现/请求包含，不能单独给质量或wall。这个条件结论不授权增加L，也不与三入口替换非单调反例矛盾。
- off-pivot整原评分组全拒收条件：在满pool β下，若全部组员的原路径native分数有可靠U_G≤β，且仍原样markvisited、保动态unvisited分组/后续callback路径与控制逻辑，则可跳整组dot并耦合ordered输出。部分组跳dot会改变scalar/batch路径，未获parity。没有计算bits的visited点不能称有known stored bits或写入精确memo；也不能直接纳入要求所有D已评分的旧状态合同。主核若按NDC cap/早停则控制改变，不能套用本结论。Ram/Gray球界是原始前作；本地E99已共享batch4等优化，此类guard必须共享给合法默认控制及候选并包含完整metadata/guard费用，未知节省不归给新入口信息。
- [整组拒收稿](certified_group_elision_theory.md) §3.1–3.2的区间与nested projection通过：C≤C_+使s²/C≥inf_I s²/C_+，故Q_+−inf_I s²/C_+为query residual squared-norm上界；a/s端点max处理任意符号。新增正交方向的ab+||q₂||||x₂||≤sqrt(a²+||q₂||²)sqrt(b²+||x₂||²)对负ab也成立，实数界非增而native误差/费用未必非增。group边界还必须保原active row pivot/下一邻接位置：pivot即使已离pool，也要扫描完原剩余行。
- 在仅给精确projection及残差范数的metadata合同中，Cauchy–Schwarz upper是尖锐的：非零q_res下令未给orientation的x_res与它同向即可达到。若bound高于cutoff，更多训练或平均残差角不能在这个受限信息模型中变出更小的逐点安全界；需更多orientation或真正额外support约束。固定真实base本可读取，不等于此cheapmetadata已支持该推论；这不是实际机会频率结论或新Cauchy–Schwarz机制。
- FINGER v1 uncentered top-SVD optimal性不继承：手设D_res的两个向量(M,1,0)、(M,−1,0)，M>1，皆正交于pivot e₃。rank1 uncentered top方向e₁丢掉全部pair差，而e₂保留pair差，故不能保证原pair-distance目标最优。若另限定orthoprojector并改用未再平方的平均lost squared-norm，centered covariance描述该另一个目标；若是squared error则涉及四阶，不能声称centered PCA是一般修复。这个反例不否定论文已测性能，也不影响任意已认证正交P的安全包络。
- 15:10复审[命题ledger](proof_ledger.md)及proxy soft正例：ledger每行目前保留了相应严格前件，未把旧GT10/signed训练、classic centroid/vMF、decision calibration或FINGER过滤写成新机制。soft公式需固定两hub、equal softmax prior、unit target和全局finite温度；弱moment的sample/anchor扰动界均已单列，仍无当前分布或费用事实。
- capacity与完整原组拒收若结合，仅在两个容量的共同expanded前缀拥有完全相同原动态group、bound结果和启用规则时，β_small≥β_big给“big可省则small也可省”，所以small实际评分的原组big也实际评分。skip仍markvisited并保持后续数值环境/分组；无callback counter、FP flags或NDC cap副作用，才保物理请求比较。它只给request数、不推出wall。
- 候选mixed匹配的手审：将当前topK与旧B作bijection，每对为已证终局保留的sameID，或在**统一**native绝对误差ε下具有stored-score严格2ε余量。stored值固定、永久visited与FIFO尾淘汰使既有ID的rank只能变差，因此最终保留的sameID不会曾离topK；新ID进入topK时不低于交换tail的stored值，可把严格margin标签传下去。末端distinct匹配把旧GT标签映到同ID或true更高的GT，因而hitcount非降。per-ID不同ε不能直接沿该过程传统一余量；旧B、误差证书、匹配和保留证书均需获取，没有免费实现/性能结论。
- [整组拒收稿](certified_group_elision_theory.md) §3.4的随机风险适配通过：原trace/path与R独立、每原请求的完整guard事件覆盖内部选择/multiple stages及数值风险时，首次错误省组必有原成员native分数超过所用U。对这些原事件union（无需独立）给P(不同返回)≤Σδ及各K期望召回损伤≤δ_total。重复callback路径应按请求union；R后选query/fit后挑R不能继承原δ；概率变体不得称确定性保真或加入无质量变化的默认J。
- 局部证书与拒收优化的**有限范围接口**也通过：先独立证明整原组优化保原logical执行与输出，再在其合法whole-row满pool状态使用永久visited V=D_phys∪D_cert、P actual bits；V\P不可重入，未来接受来自C\V。因此A/F、威胁计数及E/Qloc可另段用V替D，而不需要已cert-reject旧废点的bits。Q_L未来点按威胁计数必strict高于某pool点，sound U≤β不能把它误省为rejected，安全路径发现仍成立。原D=fully-scored语义及一般response等价的历史topL(scored)/virtualtrace前件保持；任意force/no-score mark不构成该合法状态，也不继承汇合证书。

15:35终审已复读report、manifest、ledger；本人负责P01–10/P19与M02 v1的metadata/范围相符，19个下午独立工作与3个上午沿用工作的计数没有将版本重复列成独立论文。ABS正式版新URL在本人web工具不可读取，不追加其正式版实读claim，相关读页由实际读取的同事负责。report若写“严格改善另需旧hit/nonhit真值”，应限于任意ID保护的粗界（或承认更强true-score/GT证书），不是任何严格改进证明的普遍必要条件；已向root提出。除此以外，当前交审未发现新增实质错误。

本文到此冻结；此处任何“通过”均指解析论证，无真实性能核验。默认/暂停/后继实验门均不由本文改变。
