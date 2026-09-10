# ACSG 下一阶段实验方向与新对话交接

2026-09-10。状态：`NEXT_EXPERIMENT_DIRECTION_DEFINED_UNRUN`。用户在四问题调研后要求把下一步实验方向整理到本文件，方便新对话执行。**优先方向：固定现有真实入口H，比较GT1与GT-topK、硬归属与软归属构建的画像。** 本次只完成文档交接；具体运行协议在新对话启动时冻结，没有新聚类、标注、训练、ANN构建或评测。

最近真实实验仍为E23：`EXPLORATORY_SMALL_RECALL_SIGNAL_NO_CLEAR_QPS_GAIN`，相对matched Fast20K有小幅Recall信号，没有明确整体QPS优势。Full固定目标优化更好，但Yandex五L Recall均不及rank8。实测见[summary.md](summary.md)和[E23复盘](experiment_history/12_three_entry_rank_exploration.md)。

## 1. 首轮要回答的问题

当前Fast先用独立5K query聚类，从代表query的GT100中选815/821个互异真实入口；随后将20K画像训练query按GT1到raw hub的cosine硬分组，计算`normalize(unit(hub)+Σ unit(query))`。第二步只看一个目标，可能丢失多目标信息，且画像支持不均衡。

首轮问题是：**不增加在线画像数量、入口数和评分模型复杂度，使用多个GT目标及软归属，能否改善真实三入口NSG搜索的Recall–QPS？** 现有H已有免费oracle空间，先固定H隔离画像归属作用。GT覆盖、静态度数和几何分数不能代替finite-beam真实收益。

依据：[四问题报告](entry_method_exploration/20260910_ood_hubs_clustering_router_research_v1/report.md)、[一手文献](entry_method_exploration/20260910_ood_hubs_clustering_router_research_v1/papers.md)、[既有本地证据](entry_method_exploration/20260910_ood_hubs_clustering_router_research_v1/local_evidence.json)。研究原件的`RESEARCH_COMPLETE_METHOD_UNSELECTED_UNRUN`保留当时身份；本文件记录随后要求的实验接续。

## 2. 优先实验：固定H的GT-topK软画像

### 建议默认范围

以下为新协议的建议范围，尚未执行；启动时核对当前源码和输入，再一次性锁定参数、调用预算与选择规则。

| 项目 | 建议范围 |
|---|---|
| 数据与图 | WebVid2.5M、official Yandex first10M/IP；保持原base、metric、预处理和冻结NSG |
| 真实入口 | QGT seed20260828的H815/821；不重新聚类、不增减或替换真实ID |
| 画像输入 | 与E23 matched Fast相同fit20K，即router_train原始行`[10000,30000)`，仅用fit GT构建 |
| 开发划分 | cal1024为原始行`[0,1024)`，audit1024为`[1024,2048)`；沿用身份，明确属于历史开发数据 |
| GT目标数 | 首轮建议`K_gt∈{1,10}`，与搜索评价的Recall@10分别命名 |
| 在线形式 | 一画像对应一个真实hub；raw query→Micro-HNSW direct3→原`search_new(mode=2)`，三个互异真实入口 |
| 路由对齐 | matched组共用M16/efConstruction200/ef10、seed20260828及真实ID升序消费；一份画像用于全部L |
| 评估范围 | 先开发集L128；冻结后建议沿用每数据集validation前2K、L64/128/256/400/800作探索。披露历史访问，不能称全新盲测；held-out不打开 |

### 画像定义和必要对照

令query的第t个exact raw-IP目标为`g_t(q)`，首轮继续使用当前目标–hub cosine：

`s_t,h = unit(base[g_t(q)]) · unit(raw_hub[h])`。

硬归属将每个GT目标交给一个最高分hub；软归属令`b_t,h = softmax_h(s_t,h / T)`。首轮建议GT名次等权：

`a(q,h) = (1/K_gt) Σ_t b_t,h`

`p_h = normalize(unit(raw_hub[h]) + Σ_q a(q,h) unit(q))`。

保持每条query总贡献为1、raw-hub prior权重为1，避免增加GT数时同时放大训练总权重。首轮保留cosine只为隔离GT数与软归属；**没有同时解决Yandex目标范数在归一化时被丢失的问题**。

| 画像 | 要隔离的作用 |
|---|---|
| GT1＋硬归属 | 恢复当前matched Fast20K P0，作为实现和改进主基线 |
| GT10＋硬归属 | 多目标投票 |
| GT1＋软归属 | 软分配 |
| GT10＋软归属 | 二者组合 |

温度使用小候选表，建议最多3个值，两种软画像共用同一表。具体值可参考fit目标–hub分数间隔，必须在任何cal搜索前写入protocol/config；只用cal选温度/候选，audit只报告冻结候选。允许Fast作为恢复项，但回退Fast不能冒充新方法提升。不同时增加GT名次权重、top-m截断、多prior、vMF、rank、MLP、拉伸或新的H。

实现要明确稳定softmax、硬归属ties、零向量/无支持回退和累加数值类型。软权重全非零不等于有效支持充分，应记录权重质量、有效样本量或集中程度。按query/GT批次处理，不驻留不必要的高维中间张量。

画像从已有fit exact GT闭式构建，**不需要重跑E22全H single标签或E23三入口训练标签，也不需要梯度训练**。开发与最终评估仍执行真实三入口搜索，其调用与训练标注成本分开。

## 3. 执行阶段、判断与产物

| 阶段 | 工作与产物 | 判断边界 |
|---|---|---|
| P0 身份和协议 | 读交接/源码/历史，创建独立版本，记录输入与源码hash；冻结温度、选择规则、评估范围、线程、计时次数和总调用预算 | 身份、split、GT列宽有疑点先查证，不从旧目录名推断，不覆盖旧artifact |
| P1 构建与恢复 | 先复现GT1硬归属P0，再构建其它对照；记录权重/支持、画像变化和构建时间 | 原P0数值及入口/原kernel输出恢复通过后再评价新方法；差异先修复 |
| P2 开发诊断 | 建议cal L128对预定候选做同画像exact3与HNSW3真实NSG搜索；按固定规则选择，再冻结并报告audit | 分开画像质量和近似检索损失。若所有候选cal均不优于Fast，保存完整失败表并收口，不扩网格追结果 |
| P3 端到端比较 | 冻结后在协议指定的小validation测五L、必要基线及预定消融 | 不按audit/validation换模型或删负点；报告完整Recall–QPS及失败query，小幅单次wall不作稳定加速结论 |

cal建议以HNSW实际三入口总hits为主，graph NDC及较简单配置作并列规则；exact3只解释机制，不事后在两套路由间挑结果。上述P2是小型首轮建议，实质阈值和并列规则须在cal前锁定，不沿用C或其它历史版本的门槛。audit是冻结候选的报告，不用于重新选择；一旦进入P3保留所有预定点。

P3基线至少包括NSG、原Fast30K-3、matched Fast20K-3和冻结新候选；GT10硬/GT1软等消融的展示行与总点数事前固定。原Fast30K保留seed100/heap顺序，另列输入与执行差异，方法改进主归因取matched Fast20K。E23 Full/rank8作历史参考，不为这次闭式画像消融自动重训或增加大基线队列。

正式查询及cal/audit对照统一单线程：`threads=1`、OMP/OpenBLAS/MKL=1并核验实际线程，一次只跑一个方法。QPS取独立整批plain wall，在线入口排序及全部路由工作在timer内；GT评分、NDC计数、hash、写盘在timer外。记录Recall@10、QPS、零命中/挽救/新增失败、route/graph/total NDC；exact GT、画像和微型图构建成本分列。

保存protocol/config、commands、state、逐query输出和检查，最终交付全部原值表、Recall–QPS图、成本账和报告，并同步四份主文档及历史。无新收益就收口该版本，不自动升级为正式性能GO。

## 4. 后续方向与暂不混入的变量

| 优先级 | 方向 | 进入条件和区别 |
|---|---|---|
| 1，当前主线 | 固定H的GT-topK软画像 | 隔离目标归属；与旧GT1 basin内增加两个mode、多seed多view、single赢家centroid不同 |
| 2，较重备选 | 以真实finite-L作用组织分组或在小GT候选集挑入口 | 若主线显示几何代理仍有缺口，再定协议；度数只作特征，三入口用真实联合搜索。旧centroid/rerouter已有真实效用，须说明新条件作用/可预测分组差别 |
| 3，效率支线 | 固定W，成对拉伸并重建Micro-HNSW | `p′=Ap,q′=A⁻ᵀq`，优先受限正对角A；先验评分一致，再看导航和总wall。不能变换后逐画像归一化；不重建边时保分数变换不会改变理想搜索路径 |

rank8未证最优；目标/画像稳定后再考虑`{4,8,16,32}+Full`容量比较。vMF或最小支持层次球面聚类也是后续分组备选，不与首轮混合。E23整组三入口评分/条件偏好问题仍保留，GT-topK画像没有证明已解决它。

Micro-HNSW是约800个画像的小图，主搜索仍为NSG。以后若改NSG须新图身份并重建受影响标签/评测。旧E22大矩阵不恢复；C保持`NO_GO_UNCONDITIONAL_HEADROOM_STOP_C`，不自动启动C3/C4、联动、D或效用树。所有旧源码、图、GT、标签、模型、日志和结果保留。

## 5. 新对话应定位的代码与证据

- 阅读顺序：[AGENTS.md](AGENTS.md)→[summary.md](summary.md)→[spec.md](spec.md)→本文件→[s-experiment.md](s-experiment.md)。
- 当前研究：[四问题报告](entry_method_exploration/20260910_ood_hubs_clustering_router_research_v1/report.md)；代理/入口/微型图差距见[E20历史08](experiment_history/08_fast_router_diagnosis.md)及其原始分析。
- 历史边界：[效用与表示04](experiment_history/04_utility_and_representation.md)、[reroute05](experiment_history/05_probe_reroute.md)、[E23历史12](experiment_history/12_three_entry_rank_exploration.md)。有疑问沿卡片到原始证据，不必重做整轮文献调研。
- 原画像实现：[builder](benches/run/build_fast_entry_variants.py)的`choose_unique_gt_hubs`与`build_gt_basin_prototypes`；新方法放独立版本。
- 输入身份：[E23 prepare_fit.py](entry_method_exploration/20260910_three_entry_rank_v1/src/prepare_fit.py)和其`inputs/<dataset>/<split>/config.json`。GT实际保留100列，读取时核对形状、字节数与row_ids；旧准备器还会读取single标签并生成组合，不能整段照跑来准备本次闭式画像。
- 单线程评测：[E23 protocol](entry_method_exploration/20260910_three_entry_rank_v1/protocol.md)、[evaluate.cpp](entry_method_exploration/20260910_three_entry_rank_v1/src/evaluate.cpp)、[最终验收](entry_method_exploration/20260910_three_entry_rank_v1/reviews/final_audit.json)。复用需绑定新版本的源码/可执行文件/输出身份，不覆盖E23。

## 6. 可复制的新对话启动指令

```text
工作目录 /data/netg/ACSG。
请完整阅读 AGENTS.md、summary.md、spec.md、s-target.md、s-experiment.md，
再读 s-target 指向的四问题调研及相关历史原始证据，不要只依据摘要或目录名判断。

请推进 s-target 第一方向：固定现有H，比较GT1/GT10 × 硬/软归属画像。
以文档建议范围为起点，先核对输入和实现、冻结独立小型protocol及调用预算，
然后完成画像恢复检查、开发选择和协议内的小型单线程Recall–QPS比较。
常规实现与小网格细节自行按证据确定并写入协议；完成一阶段后继续协议内下一阶段。
发现身份/parity错误先修复；达到固定停止条件则保留结果、报告并收口。

保持原base、raw-IP、NSG、QGT seed20260828、H815/821和三个互异真实入口。
以matched Fast20K为改进主对照；GT只在fit构建画像，cal选参数，audit只报告，
冻结后评估协议规定的小validation；披露历史使用，不打开held-out。
无需重跑全H single或三入口训练标签，不先训练Full/rank8。
正式查询单线程、单方法独立plain wall，全部路由成本计入端到端QPS。
不要同时引入新H、vMF、rank sweep、MLP或HNSW拉伸，不恢复旧大实验/C。
保留所有旧源码、图、GT、标签、模型和结果，新实验放独立目录。
交付完整结果/对照、Recall–QPS图、成本与局限，同步四份主文档及历史。
```

以上指令供用户在新对话启动实验；本次文档交接未执行它。方向2/3和rank比较不是自动串行队列。
