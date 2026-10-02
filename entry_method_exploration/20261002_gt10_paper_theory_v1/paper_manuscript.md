# GT10论文主稿：目标邻域画像与有限预算图搜索的对齐

2026-10-02。中文工作稿，目标按用户确认的CCF B类期刊。本文补现行方法的理论与论证结构；不声称新实验、论文已达到接收标准或GT10的所有部件首次提出。完整证明分别见[rank与搜索构造](gt10_theorem_core.md)和[有限pool发现理论](algorithm_and_falsifier.md)，最近前作与期刊定位见[审查稿](novelty_and_publication_audit.md)。

拟题：**Target-Neighborhood Query Profiles for Entry Routing in Budgeted Graph Search**。中文题名：**面向有限预算图搜索的目标邻域查询画像与入口路由**。不另造一个模型名；方法仍称GT10。

## 摘要工作稿

图近邻搜索的入口通常由base几何或学习的入口表示确定。当query与base的分布不同，入口原向量可能不能代表从该入口出发能够服务的查询。我们研究一种目标邻域监督的入口画像方法：首先用代表查询的真实近邻选取实际base入口，再将每条训练查询的前r个真实目标按目标–入口相似度分配到入口，并反向聚合查询方向；在线用这些画像的小图返回三个真实入口，接入原有限容量图搜索。训练目标数r不增加在线入口数或画像维度。

本文的理论重点是目标rank与实际有限搜索的对齐，而非把r个目标当作r个独立样本。我们分开分析rank造成的人口方向漂移、切向协方差、弱合力风险和近似路由误差，并将它们连接到真实共同pool召回。我们给出一个有限raw-IP base的显式构造：同一真实GT、六个入口和相同画像，在两个强连通图上的GT10相对GT1召回增量分别为正和负；该结果表明画像稳定性不足以决定收益符号。进一步，通过查询诱导的高分可达组件给出有限pool发现和完整扩展集合的充分条件。

现有完整单线程曲线说明GT10在部分数据与工作区间有实际收益，也存在持平和退步。论文尚需验证上述理论条件对真实收益的解释力，并补齐与最接近入口路由方法的同条件证据。本文不由代理误差、距离计算数或离线成本推出端到端QPS。

## 1. 问题与可审查的主张

固定base B、底图G、服务指标、原主搜索、容量L及返回数K。主指标为真实Recall@1、Recall@100和完整在线wall对应的QPS。GT10中的10只表示训练目标rank数；K100仍使用真实GT100和L≥100。

研究问题是：**目标邻域中的rank信息，何时能把query分布编译成便宜的真实入口表示，并对同一有限搜索产生有用的入口集合？**

主张不应写成“最近入口更好”“更多目标普遍降低误差”或“原型均值首次用于检索”。候选贡献应集中在两点：目标邻域到query画像的具体监督算子；这一算子经真实三个入口作用于有限pool的正面条件与失效机制。前者与GATE等前作的差异需逐项核实，后者的基础工具须如实注明出处。

## 2. 完整算法

### 2.1 数据角色和入口集合

输入为有限base、已建好的原图、独立QGT查询及其真实GT候选、画像拟合查询及其真实前r个目标。当前实现继承QGT-Cover：对QGT单位query做球面k-means；每簇按query到质心相似度排序，逐query按GT100名次取第一个全局未用的base ID；不足时扫描QGT的GT候选补齐，最后按真实ID排序。它是启发式选择器，不是严格set cover，也不是直接取质心的GT1。

源码：[选择器](../../benches/run/build_fast_entry_variants.py:180)。独立QGT条件只使固定H后的统计分析合法，不给该选择器最优性保证；实际历史数据是否满足IID仍须单独说明。

### 2.2 目标归属与查询画像

记入口单位原向量为u_h，拟合query单位方向为X_i，真实目标为t_j(q_i)。原指标下生成GT，目标–入口归属则使用单位target与u_h的cosine；这两个步骤的metric不同，不能混写。

hard责任为唯一最高cosine入口的指示量，最高分并列沿已排序真实ID；soft责任为全部H入口cosine的stable softmax。每query到入口的质量为

`a_h^(r)(q_i) = (1/r) Σ_(j=1)^r w_h(t_j(q_i))`，且`Σ_h a_h^(r)(q_i)=1`。

画像为

`p_h^(r) = normalize(u_h + Σ_i a_h^(r)(q_i) X_i)`。

这聚合的是query方向，目标提供归属标签；画像绑定实际入口ID，不是新的base目标或虚拟搜索节点。prior系数为1，不用质量均值替代query合力。数学单位化与实际`max(norm,1e−12)`、float32导出须区分；弱norm与舍入另计。

当前soft温度尺度由同批fit GT1最高/次高hub cosine差中位数、下限1e−4决定，三个候选为尺度×1/4、1、4；随后cal选模型、audit只报告。不能把同批选温度当外部固定算子而直接套IID界。固定温度分析与统一温度界见[完整算法理论](algorithm_and_falsifier.md)。

### 2.3 小图路由和原主搜索

```text
Offline(B, G, QGT, Qfit, GTfit, r, hard_or_soft):
    H ← current QGT-Cover(QGT, exact GT candidates)
    sort H by real base ID
    U_h ← normalize(B[h])
    determine current soft temperature candidates from fit GT1 gaps, if needed
    for each candidate rule:
        M_h ← U_h for all h
        for each fitting query q_i:
            X_i ← normalize(q_i)
            for each true rank j ≤ r:
                w ← hard or soft assignment of normalize(B[GTfit[i,j]]) to all U
                M_h ← M_h + w_h X_i/r for all h
        P_h ← current normalize(M_h), export float32
        build current Micro-HNSW on P_h with labels = real h
    select model on calibration role, freeze; audit does not select again
    return frozen selected profiles, router, real ID mapping

Online(q, K, L):
    S ← actual three distinct real hub IDs returned by current router
    prepare S in the current canonical seed order
    R ← original graph search(G, raw q, S, K, L, original metric)
    return R
```

路由数学排名可分析为unit(q)·p，但实际系统可以直接用raw q做IP查询；正比例缩放不改变精确排名，却不保证原生归约或近似遍历完全相同。HNSW的1−IP与NSG的负IP也不能直接比较数值。

mode=2有效入口最多初始化三个、无随机填满L；只在空入口时fallback。主图永久visited、整行扫描、有限pool保留、自然rewind和停止不改变。画像、路由图和输出接口均是已有实现。本轮没有改训练目标、温度、入口数、底图或代码。

### 2.4 成本

离线可以承担更多真实目标监督和画像拟合费用；这是允许增加的投入。输出模型为H个d维画像及一个小图，r只增加离线目标归属工作。在线仍需计全部路由、原搜索及输出；同模型规模不意味着实际wall相等。对非零query，完整查询batch的总wall才定义吞吐，不拼接分项计时。

## 3. 理论结果与证明路线

### 3.1 rank平均改变方向，也改变相关噪声

单query向量贡献为`Y_(r,h)=r⁻¹Σ_j w_h(t_j(X))X`。其均值为rank均值的平均，协方差包含全部rank交叉项：`Cov(Y_r)=r⁻²Σ_(j,k)Cov(B_j,B_k)`。十个目标共享同一query、排序与邻域，统计样本数仍为query条数n。

固定非零人口矩μ时，切向投影`P=I−ppᵀ`、`p=unit(μ)`控制单位画像的通常方向误差；`tr(PΣ)/n`与prior的切向项分开，径向方差给弱合力/反向风险。更多训练可以压缩采样误差，却不能消除rank造成的人口方向漂移。完整非渐近界和Cantelli证明见[理论§6](gt10_theorem_core.md)。这些协方差、投影和概率工具是标准工具或本地已有理论，不列为独立原创贡献。

### 3.2 一个真正由raw-IP产生GT的正例与反例

构造五维有限base、12类query、六个真实hub、六个GT1候选和六族各99个后续目标。真实GT1由query的Z分量决定，真实GT2–100由独立Y分量决定；全部目标的hard归属均由实际target–hub cosine唯一确定。

当前hard GT1画像的精确top3是三个Z类hub，GT10画像的精确top3是三个Y类hub。另证明同一模型按现行fit GT1 gap中位数生成的数学soft-t1也有此top3，不需假定温度任意趋零。先验系数1、有限平衡训练样本和所有真实有序GT边界均在构造内处理；不证明真实Web/cal选择或native误差满足前件。

在相同base上只改六个hub的桥边，得到两个强连通、有限度数图。桥服务按Y时，GT1/GT10的Recall@1和Recall@100分别为1/2与1；桥服务按Z时分别为1与1/2。失败证明直接使用整个共享pool：低分桥在扩展前被合法bait链填满容量后淘汰；成功证明使用真实GTK发现后的保留性质。不是三个single响应相加。

因此，**相同GT/rank/profile统计不能识别GT10真实收益的符号**。该结果解释了为何真实GT监督也可能与图服务失配。严格不等式使构造在小扰动邻域和连续query密度下保留；不局限于孤立tie。它针对固定合法H与图，不证明QGT-Cover或NSG构图器必定产生这个H/图，更不是QPS构造。完整定义与证明见[理论§2–5](gt10_theorem_core.md)。

### 3.3 从画像误差到实际共同pool召回

人口top3间隔、样本方向误差和每个实际小图的近似/数值/ID映射事件给入口失配概率ε_r。对固定原搜索的共同pool响应R_K，若相同canonical入口恢复同一初始化与数值合同，实际和人口策略的平均Recall差绝对值≤ε_r。因此GT10相对GT1的真实质量差位于

`[Γ_K−ε_10−ε_1, Γ_K+ε_10+ε_1]`，

其中Γ_K是人口策略在该固定图、L、K上的实际joint质量差，而不是免费的入口几何oracle。Γ_K的符号必须由图结构或真实响应确定；上一节给出正负均可的实例。K1与K100分别分析。

### 3.4 有限容量搜索何时发现有效区域

对固定query的实际高分排序，考虑从初始高分入口沿高分诱导图可达的组件C_τ。如果`|C_τ|≤L`，其中全部节点在首个低于τ节点扩展前被发现和扩展；若真实GTK与非GTK的native排序严格分离，最终Recall@K至少为`|GTK∩C_τ|/K`。

如果`|C_τ|=L`，完整扩展集合恰为C_τ；首次评分的ID集合为`S∪N⁺(C_τ)`，初始低分ID及被拒邻居仍收费。容量不足、score paths不一致或近tie时要用明确的potential/safe区间版本；无可靠区间不能报原生保证。

这是ordered best-first traversal的适配推论，不能单独作为原创beam理论。其作用是给GT10的入口对齐提供可检验结构条件，并解释为什么强连通、短路径或入口更近不足以保证成功。`|C|<L`只给前缀，不能冒充完整工作量。完整证明见[算法理论§2](algorithm_and_falsifier.md)。

### 3.5 与完整速度条件连接

容量闭合的两个组件给精确GTK覆盖与完整首次评分/槽数。若候选覆盖更好，且评分/扫描节省超过全部路由与pool/cache/输出残余增量的可信上界，才同时得到真实质量与时间改善。已给两个强连通组件的解析例：相同L、相同扫描槽数，较好的组件含GTK且外邻居共享，使首次评分数从2L变成L+1。该例证明结构条件非空，不证明GT10会生成这种入口，也没有原生计时。费用记账是标准恒等式，未知残余前件不能删去。完整推导见[综合收益条件](joint_gain_conditions.md)。

## 4. 与前作的实质区别

GATE已有不改底图、真实hub、query-aware表示和小图入口路由架构，不能把这一总体结构作为本方法独有创新。待核方法差异是QGT真实目标选hub，以及多rank target归属后反向聚合query矩的具体算子；闭式而非两塔本身不足以构成重要创新。[GATE原文](https://arxiv.org/html/2506.15986v1)。

Oguri–Matsui已有自适应入口与路径理论；ABS已有beam/order停止分析；原型与球面均值亦有成熟前作。本稿应主张的是针对实际rank画像、共同pool召回与图服务失配的完整论证，保留标准工具出处。最近前作逐项碰撞与未读正文边界见[审查稿](novelty_and_publication_audit.md)。不得写“首次”“唯一”或“无人研究”。

## 5. 已有实证与它不能证明的事

现有数据仅引用已封存原文字报告，不重算、不合并新的测试来源。

|已测记录|支持什么|不能替代什么|
|---|---|---|
|[E24固定H GT1/GT10](../../experiment_history/13_gt_topk_profiles.md)|同H/在线三入口的局部完整wall收益及明确负点；按cal冻结方法|新盲测、稳定全区间优势、同T纯rank交互估计|
|[E103五集统一内核完整曲线](../../experiment_history/96_optimized_five_dataset_retest.md)|真实Recall@1/@100与完整单线程QPS；GT10在部分集/区间有实际收益|与NSG同Recall显著性、五集全面第一、GT10相对GT1的机制因果|
|[E134方向稳定性](../../experiment_history/134_gt10_profile_direction_stability.md)|同20K两半的方向稳定和真实对应亲和；置换也部分稳定|IID总体结论、稳定导致召回提高、图服务对齐|
|[E166当前最新性能](../../experiment_history/166_target_bank_frozen_curve.md)|近期候选仍有质量/速度取舍，默认保持|本轮新方法成绩、GT10论文新增实验|

E103最快实测R90达标点中，Web K1/K100的soft相对NSG QPS为+24.99%/+0.79%，Y的hard为+9.63%/+6.96%；方法L与实际Recall不同，不称精确同Recall优势。GIST相对NSG基本持平或落后。hard与soft不能逐阈值挑赢家拼成单一部署方法。

这些结果使研究有实证基础，但尚未识别rank方向与finite-pool服务的实际对应关系。新理论证明的是可能性、条件与不可识别性，不是对旧正点追加一个已确认的因果解释。

## 6. CCF B论文当前完成度

算法定义、现有实现、完整历史性能和形式理论主线已经可以组成一个可审阅工作稿。还不能诚实地称“现在就足以接收”：最关键缺口是新理论条件在真实系统的解释力，以及相对最接近方法的可信区别；单靠更多公式不能补齐这两项。

后续在获得实验指令前只继续论文与证明工作。可以增加离线训练投入，仍必须保持实际Recall–QPS评估合同。下一份经授权的最小证据应回答：GT10相对GT1的实际收益是否由rank矩变化、实际top3与共同pool服务联合解释；并与更简单的同监督控制及GATE比较。具体证据清单和否证门见[主报告](report.md)。本文件不授权执行这些测试。
