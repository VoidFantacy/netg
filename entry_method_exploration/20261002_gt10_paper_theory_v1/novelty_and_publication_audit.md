# GT10 论文创新与 CCF B 期刊定位审查

2026-10-02，UTC+8。任务状态：**THEORY_PUBLICATION_DESIGN_ONLY_NO_EXPERIMENTS**。本轮只读原论文、官方目录与期刊说明、项目静态文档；没有训练、构图、GT、搜索、计时、向量读取、旧数组统计、模拟或数学程序。下文是论文设计与可证伪边界，不是录用承诺或实验执行许可。

## 1. 选定的研究问题与贡献范围

保留现行 GT10，研究问题具体为：**当查询和 base 的几何不一致时，多 rank target 对真实 hub 的归属怎样形成有效的 inverse-query 入口画像；这种变化在什么有限 beam 条件下影响真实共同 pool 的 GTK 发现，并在什么条件下无法带来 Recall–QPS 收益？**

方法本体已有：真实 hub 集 H；每 query 的十个真实 target 分别分配到 H；十 rank 权重先在 query 内平均，因此每 query 的总权重仍为 1；用这些权重反向累加 query 方向，加当前 unit-hub anchor 后归一化；Micro-HNSW 返回三个真实 ID；同一 raw-IP NSG、L、邻接、扩展和自然停止执行共同 pool 搜索。算法合同见 [本轮算法](algorithm_and_falsifier.md)，历史实现与证据见 [E24 协议](../20260910_gt_topk_profiles_v1/protocol.md)、[现行 spec](../../spec.md)、[E103 原记录](../../experiment_history/96_optimized_five_dataset_retest.md)。

合适的贡献表述是 **target 归属驱动的逆向 query 画像方法及其真实有限搜索机制**。这里的 transport 只表示归属权重把 query 矩传给 hub，并未建立最优传输问题；不要引入 optimal transport 的新颖性或保证。

候选增量有三层，须合在一起审查：

1. **方法差异**：学习“哪些 query 的真实多个 target 归属于这个 hub”，而非直接按 base 聚类选最近入口，或用图路径教师学访问优先级。它仍属于已有的查询感知入口框架。
2. **专门机制**：多个 rank 的归属既有协方差，也有总体偏差；GT1 的 hub 标签可能携带妨碍实际路由的变化因素，后续 rank 可能消除它，也可能引入新偏差。需要在有限 base、真实 IP 排序、三个共同入口及固定图中实现正例和符号反转例，不能只构造任意标签后验。
3. **检索兑现**：population 画像 → 有限样本/anchor 误差 → 第三/第四 hub 间隔 → 实际近似三入口 → query 的高分诱导图可达组件 → GTK 发现与完整工作集合。任何一层缺失，都不能把画像拟合解释为真实质量保证；工作集合也不能直接换算 QPS。

目前有可审阅的条件理论主线，**还没有足以声称“已达到 CCF B 投稿充分条件”的证据**。没有找到完全相同的多 rank 逆向画像和真实三入口构造，属于有限检索结果，不是全领域不存在前作的证明。

## 2. 与最接近前作的精确关系

下面比较的是原文方法合同，而不是用“神经网络/闭式方法”名字划界。各来源的阅读范围和版本列在 §6。

|前作|实质相同点|GT10 可以成立的区别与限制|
|---|---|---|
|[GATE，KDD2025](https://arxiv.org/html/2506.15986v1)|固定底图、少量真实 hub、查询感知 hub 表示、小导航图、实际 hub 作为入口；它已经处理 base/query 失配|GATE 的 HBKM 从 base 选 hub，结构表示与 hop 标签训练 hub 表示；GT10 用 target–hub 归属反向形成 query 画像。只有监督对象及其兑现机制可作主差异，架构和“小图路由”不能报首创|
|[Learning to Route，ICML2019](https://proceedings.mlr.press/v97/baranchuk19a/baranchuk19a.pdf)|图上学习查询相关搜索行为、GT 与最短 hop 教师、学习质量/效率关系|它学 query/node 表示并改变访问优先级与搜索，GT10 只改变真实初始化 ID，原主图打分/扩展固定。GT10 不继承它的教师最优性；“用 GT 训练图搜索”不是新思想|
|[Adaptive Entry Point Selection，arXiv2024](https://arxiv.org/html/2402.04713v1)|查询自适应选真实入口，讨论入口距离和图搜索理论|它用 base k-means medoid 与最近入口；Theorem 4.4 比较 b-monotonic 图下 hop 上界。不能把其结果当自然有限 pool 的 GTK/完整 QPS 定理；GT10 须另证多 target 监督及实际 beam 兑现|
|[RoarGraph，PVLDB2024](https://arxiv.org/html/2408.08933v1)|使用真实 query 的多个近邻 target、跨模态/OOD 几何与 target 分散|它用 query–base 二部图投影和连接修复构造底图；GT10 保持底图，用归属的逆向 query 画像选入口。因此“query 指导/多个 GT/OOD”都不是独有贡献|
|[Adaptive Query-Aware Hybrid Search，EDBT2026](https://openproceedings.org/2026/conf/edbt/paper-253.pdf)|历史 query 与返回 target 的关系用于多个 HNSW 初始入口|它有 query 历史索引、structured filter、Recall 估计和路径选择。GT10 的离线静态画像、固定无过滤 NSG 合同不同，但 query→target-bank→入口复用已有先例|
|[ABS，NeurIPS2025](https://arxiv.org/html/2505.15636v1)|按 query 分数有序扩展，解释经典 beam 的宽度与停止|当前高分组件容量命题是 ordered traversal 的专门适配推论，不能单独作为新 beam 理论。候选增量是把逆向画像、rank 误差、实际三入口与发现/完整工作集合接起来|
|[Graph Based K-NN Search Revisited，TODS2025](https://doi.org/10.1145/3736716)|query-dependent 虚拟图、导航/细化与理论检索保证|其 labeled graph 构造及查询方法不同；本轮只取得官方摘要/概要，未完成全文逐命题排除，不能声称已经排除它的全部理论|
|[PAG，ICML2026](https://arxiv.org/html/2603.06660v1)|投影与 beam 过滤减少检索计算，含容纳被排除点的机制|它改变构图、搜索过滤与调度；不是现行固定原图/原 pool 的 GT10 理论。若以后转过滤分支，应面对该最新先例，不能把 projection、buffer 或阈值过滤直接报新方法|
|[Sort Before You Prune，ICML2025](https://raw.githubusercontent.com/mlresearch/v267/main/assets/gollapudi25a/gollapudi25a.pdf)|已有自然有限容量 BeamSearch 的多近邻最坏情形理论|原文 Theorem1.1、§2–3 使用 metric/(sorted) α-reachable 图，结论是距离近似。当前 fixed arbitrary graph/raw-IP 的发现分析不能继承这些前件；“首次为 k>1/有限 beam 提供理论”已被该作明确覆盖|
|[OPT-SNG，2509.15531v5，2026-05-05](https://arxiv.org/html/2509.15531v5)|图结构和搜索的理论分析，讨论 NSG 等与参数选择|§2.2 Algorithm1 的停止是发现集大小达到 L；§5 的路径分析依赖均匀分布和逐步更近的路径。不是当前容量 L、永久 visited、自然停止的三入口共同 pool 合同，不可直接搬其路径界解释 GT10|
|[RP-Tuning，2602.08097v1，2026-02-08](https://arxiv.org/html/2602.08097v1)|已有容量 beam、metric α-reachability、图质量/检索权衡|§3 对底图重新剪枝并证明 reachability 变化；GT10 固定底图而改变入口。它已表明工程 trade-off 须与实际图性质一起讨论，不能把有度数上界或一般路径假设当新贡献|

**GATE 特别核对。** 论文 §4.2 Definition 4 的固定 hub 跨 query hop 标签，与作者 release 的“每 query 在成功 hub 间用 GT1 发现 hop 取正例”不同。冻结 release `229f18dadb791ddede22597e44d5ceb028b104ba` 的在线实现直接把原 query 送入小图、取 top3；离线学习 hub 向量。不能写成“GATE 每次在线跑神经 query tower，所以 GT10 消除在线神经开销”。本轮方法对照使用原论文，实验重现身份使用已封存的 [作者代码核验](../20261002_theory_until1300_v1/latest_entry_literature.md)。

## 3. 哪些数学工具不是创新

|工具/主张|最近的明确先例与处理方式|
|---|---|
|按监督类别平均 embedding、画像或 prototype|[Prototypical Networks，NIPS2017](https://proceedings.neurips.cc/paper_files/paper/2017/file/cb8da6767461f2812ae4290eac7cbc42-Paper.pdf) §2.2–2.3 已有 class mean 与 Bregman 解释；当前球面线性 proxy 的归一化解是标准 Cauchy–Schwarz 应用|
|一个 query 拥有多个非负、总和为 1 的软标签|[Label Distribution Learning，arXiv2014](https://arxiv.org/html/1408.6027v1) §II、III-A 已有这种监督对象；“soft 多目标分布”本身不足以构成方法创新。GT10 是用 label 权重反向聚合 query，而非相同的正向 LDL 预测器|
|误差小于标签/排序间隔则预测不变|[Label Distribution Learning Machine，ICML2021](https://proceedings.mlr.press/v139/wang21h/wang21h.pdf) §3.2 有分布误差与决策 margin；当前 top3 间隔和 normalization perturbation 属标准稳定性工具。本文自己的条件须使用严格间隔并说明 tie 合同|
|把 target feature 的条件均值当预测目标|[Conditional mean embeddings as regressors，ICML2012](https://icml.cc/2012/papers/898.pdf) §3 将 CME 写为向量值回归；当前 E[a_h(Q)unit(Q)] 是反向交叉矩，不等于 E[ψ(T)｜Q=q]，也不因此获得入口效用最优性|
|多 rank 平均“降低方差”|十 rank 共享同一个 query，不是十倍独立 query。协方差展开、bias–variance 分解、McDiarmid、union bound 是证明工具；主要问题在 rank 总体变化对真实入口与搜索的影响|
|vMF、低秩、教师蒸馏、候选过滤、portfolio|本项目 E168 已区分这些通用工具和真实任务缺口；本轮不把它们换名为方法贡献。尤其有限 hard 标签、固定 soft 温度和连续 vMF 后验不能未经兼容性证明便视为现行 GT10 的生成模型|

上述区分继承 [E168 前作/可证伪审查](../20261002_theory_until1600_v1/theory_prior_and_falsifier_audit.md)，不回改其封存稿。GT10 的画像方向为 E[a_h(Q)unit(Q)]；a_h 是 target 的几何归属，尚未证明它等于固定有限 NSG 中入口的 signed utility。把这点作为假设写掉，会把关键问题删掉。

## 4. 当前主理论的交叉审查与可推翻条件

对 [algorithm_and_falsifier.md](algorithm_and_falsifier.md) 的 A/A1/A2/A3 逐步审阅后，未发现其写明合同内的反例：全行扫描、永久 visited、固定 top-L 保留语义、无额外 cap、所有保留 pending 最终扩展不可省略。A 的归纳先限制已发现高分属于同一可达组件，再用 |Cτ|≤L 防止拒收；这比单纯原图可达性强。|Cτ|=L 才关闭后续低分扩展并得到完整工作集合，|Cτ|<L 不能推出完整成本界。A2 还必须要求 K≤L 与官方 GTK/native 非 GTK 的严格分离。

A3 的 potential/safe 版本处理路径不一致，逻辑上仍是容量归纳；native score 区间必须真的覆盖 scalar/SIMD/FMA 等实际路径。当前没有这些区间的真实证书，不能声称原生鲁棒保证已经满足。Cτ、区间组件、近似路由 score 缺口都是解析变量，没有在线免费 oracle。

这些命题可用于完整方法分析，但重要性不能靠“与 ABS 文字不同”建立。可推翻主张的边界如下：

- 若已有入口方法的目标与当前 a_h→query moment 算子等价，则方法新颖性收缩；后续理论必须独立说明超过已有分析的实质结果。
- 若跨 rank 总体归属主要带来服务方向偏差，或 rank 协方差等于单 rank 方差，则多 target 既不保证方向更准，也不提供十倍样本量。
- 若正例只在单点、任意 rank 标签或事后改图成立，则不足以解释现行 GT10。正面模型应是同一有限 base 实现真实排序、真实 hub 归属、实际三入口和共同 pool；需严格间隔与邻域扰动稳定，并提供收益反转例。
- 若实际入口对应的潜在高分组件大于 L，或画像得分间隔不对应实际 Micro-HNSW 的三个 ID，则条件链对真实收益解释力不足。
- 若对照只有 MSE、NDC、首次 GT1 命中、单入口加和或省略路由成本，则不能支持 Recall@1/@100 综合 QPS。

已独立手审 [gt10_theorem_core.md](gt10_theorem_core.md) §2–5：真实 IP 的前100排序、hard 唯一归属、有限 anchor 的 GT1/Z 与 GT10/Y 三入口、两图只改六 hub 出边、共享 pool 下桥/bait 成功与失败论证，均未发现写明合同内的漏洞。球面连续密度已经明确相对于球面面积测度绝对连续；严格间隔保留的是类别三入口集合，不需要把类内 tie 伪装成全 hub 无 tie。

§5.1 的 soft-t1 扩展也已手审：同一模型的 fit GT1 gap 恒定，按当前 median/floor/t1 规则得到 T=.65/(√4251 H₀)；全 H soft 责任分解为 class 与 member 两因子，实际 rank 矩、三入口跨类间隔和有限 anchor 保持。没有把“任意足够小 T”冒称实际 t1，也没有在随机选 T 条件下擅自假设 query IID。

该构造是**本任务的专门机制构造**，不是一个关于一般均值或 margin 的原创定理。它证明 hard 与明确的 median-t1 soft 合法模型“可以有效”和“效应依赖图”，不能证明自然 NSG 的总体通常满足这些条件，也不能替代 WebVid 当前模型的真实机制证据。完整构造没有原生 wall 结果；它不是 QPS 正例。最终正文应避免 universal superiority、first query-aware entrance、distribution-free Recall/QPS guarantee 等主张。

## 5. CCF B 投稿前仍缺的最低证据

本轮不执行以下工作；这些是论文证据缺口，不是新的实验 GO。

1. **原作排除与独立证明复核**：完成 TODS2025、相关 α-reachable/beam 文献的全文对照；对当前 positive/reversal 构造逐条核真实 rank、hard/soft 归属、三入口、自然 pool 和 native 前件。已有标准结果必须明确引用。
2. **监督因果机制**：固定同一 hub/底图/kernel，区分 GT1 与真实 GT10 的 rank 作用、总 query 质量和 anchor 作用；与保持样本量的无真实 target 关联控制比较。不要把 hub 生成器、训练 query 数、温度选择同时变化的结果当多 rank 作用。
3. **实际路径兑现**：画像变化 → hub score margin → 实际小图返回 ID → joint pool 的 GTK rescue/damage → 全程工作与完整 wall。输出 K=1/100 分开，训练 rank=10 与输出 K 不混用。原生 tie 和近似路由失败必须有明确处理。
4. **真实整体收益与外源确认**：同机单线程、当前默认、共享优化、完整线上路由/排序/搜索/输出成本；曲线与成对不确定性；训练/选择/确认 query 角色分离。历史开发结果可支持可行性，不能替代独立来源确认，更不能用 discrete 近似 Recall 点或插值报严格共同改进。
5. **可迁移性**：覆盖 query/base 失配程度、rank 相关性、稀有 hub 支持和多个常见底图，报告理论失效的 workload。训练时间增加可以接受，但必须体现完整在线 Recall–QPS 的收益。

最小可审稿故事应为：“一种 target 归属驱动的 query-side 入口表示；它针对 GT1 标签变化因素提供多 rank 机制分析，并解释何时会改变固定有限搜索的发现与工作集合；在独立数据、强基线和完整成本下验证有效性及失败边界。”理论框架与历史性能尚不足以填满这句话中的实证部分。

## 6. 本轮原论文阅读记录

只列实际原文阅读范围；已读某节不等于全文审完。网页抓取日期不能代替论文版本日期。

|原文身份|本轮实际阅读范围|
|---|---|
|Jiancheng Ruan, Tingyang Chen, Renchi Yang, Xiangyu Ke, Yunjun Gao；GATE；KDD2025；[arXiv 2506.15986v1，2025-06-19](https://arxiv.org/html/2506.15986v1)，[出版 DOI](https://doi.org/10.1145/3711896.3736930)|§2.1；§4.1 HBKM、§4.2 Graph2Vec/hop 标签、§4.3 hub fusion/小图、§4.4 cost；release 静态核验继承封存报告|
|Dmitry Baranchuk, Dmitry Persiyanov, Anton Sinitsin, Artem Babenko；Learning to Route in Similarity Graphs；[ICML2019 / PMLR97](https://proceedings.mlr.press/v97/baranchuk19a.html)|原 PDF §3.1–3.3；搜索映射、hop teacher、student visited states、原距离最后 rerank|
|Yutaro Oguri, Yusuke Matsui；Theoretical and Empirical Analysis of Adaptive Entry Point Selection for Graph-based ANNS；[2402.04713v1，2024-02-07](https://arxiv.org/html/2402.04713v1)|§3.3；§4.1–4.2/Theorem4.4；Conclusion。仅确认 arXiv 身份，不擅定正式 venue|
|Meng Chen, Kai Zhang, Zhenying He, Yinan Jing, X. Sean Wang；RoarGraph；PVLDB2024；[2408.08933v1，2024-08-16](https://arxiv.org/html/2408.08933v1)|§3；§4.1–4.2.1 与 Algorithm1；query–base 二部关系、投影及连接修复|
|Adeel Aslam, Rizwan Khan, Giovanni Simonini, George Konstantinidis；Adaptive Query-Aware Hybrid Search in Vector Databases；[EDBT2026，doi:10.48786/edbt.2026.42](https://openproceedings.org/2026/conf/edbt/paper-253.pdf)|§2.2–2.3；§3.1；query 历史索引、Recall 估计、多初始入口|
|Yousef Al-Jazzazi, Haya Diwan, Jinrui Gou, Cameron Musco, Christopher Musco, Torsten Suel；Distance Adaptive Beam Search for Provably Accurate Graph-Based NNS；[2505.15636v1，2025-05-21](https://arxiv.org/html/2505.15636v1)，[NeurIPS2025 原出版稿](https://proceedings.neurips.cc/paper_files/paper/2025/file/904fe070f484231aa26dbdb37816cd40-Paper-Conference.pdf)|本轮读 v1 §3.1 Algorithm1、有序视角、§4 及 AppendixB.1 Algorithm3；正式稿阅读沿用 E168，两个版本不混为逐字相同|
|Kejing Lu, Zhenpeng Pan, Jianbin Qin, Yoshiharu Ishikawa, Chuan Xiao；PAG；[2603.06660v1，2026-03-01](https://arxiv.org/html/2603.06660v1)，[ICML2026 / PMLR306](https://proceedings.mlr.press/v306/lu26y.html)|读 v1 §1.2、§3.1–3.4；正式页面作者顺序为 Lu, Pan, Ishikawa, Xiao, Qin，正式 PDF 未成功取得，不冒称审过出版正文|
|Jake Snell, Kevin Swersky, Richard S. Zemel；[Prototypical Networks for Few-shot Learning，NIPS2017 原稿](https://proceedings.neurips.cc/paper_files/paper/2017/file/cb8da6767461f2812ae4290eac7cbc42-Paper.pdf)|§2.2–2.3：class mean、距离 softmax、Bregman 解释|
|Xin Geng, Quan Zhao；[Label Distribution Learning，1408.6027v1，2014-08-26](https://arxiv.org/html/1408.6027v1)|§II、III-A。此 v1 页署两人；[作者官方页面](https://palm.seu.edu.cn/xgeng/LDL/) 列 TKDE2016 发表稿作者 Xin Geng，不能把两版作者表混写；未获取发表稿全文|
|Jing Wang, Xin Geng；[Label Distribution Learning Machine，ICML2021 / PMLR139](https://proceedings.mlr.press/v139/wang21h.html)|原 PDF §1、§3.2 Definition1/Theorem1；间隔端点需结合 tie 规则，不未经核验照搬弱不等号|
|Steffen Grünewälder, Guy Lever, Luca Baldassarre, Sam Patterson, Arthur Gretton, Massimiliano Pontil；[Conditional mean embeddings as regressors，ICML2012](https://icml.cc/2012/papers/898.pdf)|§3.1–3.3；向量值回归与 conditional mean 的关系|
|Jiadong Xie, Jeffrey Xu Yu, Yingfan Liu；[Graph Based K-Nearest Neighbor Search Revisited，TODS50(4), Article14, 2025](https://doi.org/10.1145/3736716)|仅官方摘要/贡献概要，访问正文受限；没有作逐定理全文排除|
|Siddharth Gollapudi, Ravishankar Krishnaswamy, Kirankumar Shiragur, Harsh Wardhan；[Sort Before You Prune，ICML2025 / PMLR267 原出版 PDF](https://raw.githubusercontent.com/mlresearch/v267/main/assets/gollapudi25a/gollapudi25a.pdf)|本轮读22页PDF的第1–5页；Theorem1.1、§2.1 BeamSearch/Prune、§2.2 α-reachability、§3.1 metric/Euclidean局部最优；未称全文证明审完|
|Xinran Ma, Zhaoqi Zhou, Chuan Zhou, Zaijiu Shang, Guoliang Li, Zhiming Ma；[Sparse Neighborhood Graph-Based ANNS Revisited: Theoretical Analysis and Optimization，2509.15531v5，2026-05-05](https://arxiv.org/html/2509.15531v5)|§1、§2.1–2.3 Algorithms1/2、§5 Search Bounds、§6.1；不把 v1 标题/七作者表与 v5 混写，不据 arXiv 未更新的 PVLDB 占位信息确认发表页码|
|Tian Zhang, Ashwin Padaki, Jiaming Liang, Zack Ives, Erik Waingarten；[Prune, Don't Rebuild: Efficiently Tuning α-Reachable Graphs for NNS，2602.08097v1，2026-02-08](https://arxiv.org/html/2602.08097v1)|§1、§2/Algorithms1–2、§3/Theorems3.1–3.2；已读方法与命题，未声称全部证明复核或正式 venue 身份|

检索还命中 α-reachable multi-vector 原文及 HEXA（VLDB2026 官方 program）；本轮未成功获取并审完正文，仅作为尚未关闭的阅读项，不能凭标题/摘要宣告差异。此前 E168 已列的前作不因此被本轮“重新发现”而成为新贡献。TODS2025 曾尝试 DOI/ACM 正文与作者稿检索，未取得可用原正文；二手全文镜像不作为本轮技术证据。

## 7. CCF B 目录与适用期刊

**实际核验的是官方 2026 第七版附件第 33 页（数据库/数据挖掘/内容检索的 B 类），不是把 72 页全目录称为读完。** 官方 [第七版发布页](https://www.ccf.org.cn/Academic_Evaluation/By_category/2026-03-31/870181.shtml) 与 [现行正式 PDF](https://www.ccf.org.cn/ccf/contentcore/resource/download?ID=112CF3BF7E1140ACEB271ADAED12A67ADFABB8FF099E40C2759502A85C8A281F) 为分级依据。本地保留 [ccf_2026_official.pdf](literature/ccf_2026_official.pdf)，SHA256 `271b630b576bf8a4f802e767f5694caded93680e22b3a19bef7902591c45c1d3`。

第 33 页原条目可核摘录（版式压缩不改变名称）：

|序号|简称|正式名称|类|
|---|---|---|---|
|5|DMKD|Data Mining and Knowledge Discovery|B|
|10|IS|Information Systems|B|
|13|KAIS|Knowledge and Information Systems|B|
|14|DSE|Data Science and Engineering|B|

旧的 CCF 分类网页仍把 DSE 放在 C 类，不能覆盖 2026 正式 PDF。CCF B 也不是 JCR 分区或中科院分区。

|期刊|官方 scope 与此稿的适配判断|
|---|---|
|**KAIS，优先候选**|[官方 scope](https://link.springer.com/journal/10115/aims-and-scope) 包括知识/信息系统的理论基础、学习、智能检索与高效基础设施。完整方法、机制理论、可迁移真实证据形成的 GT10 故事较贴合；只展示一个工程入口技巧或手工 toy 不足以支持定位|
|**DSE，适用候选**|[官方 scope](https://link.springer.com/journal/41019/aims-and-scope) 明确数据密集计算的理论、算法分析和高效系统。固定图上 query–target 机制与真实检索成本可相容；应突出理论与系统有效性，不能以其刚升 B 作为容易录用依据|
|**DMKD，有条件候选**|[官方 scope](https://link.springer.com/journal/10618/aims-and-scope) 覆盖发现/学习、搜索与优化、可扩展性及多媒体数据。需让逆向画像和 rank 机制成为一般化的学习/检索问题；仅 NSG 单一实现的入口加速会削弱契合度|
|**IS，级别已确认、scope 待核**|官方 Elsevier/ScienceDirect scope 页面本轮访问返回403，未取得内容；只确认目录 B 条目，不据此声称现稿适配或给投稿优先级|

以上排序是根据当前论文故事和已核 scope 的研究判断，不包含录用概率、周期、费用或投稿行动。现阶段先完善可反驳的 GT10 理论与论文主线，保持生产默认和当前实验状态。
