# 历史缺口与最强简单反例审查

2026-10-02，理论研究至13:00（UTC+8）。本文件由历史审查代理维护；当前为终稿。读取主文档、历史卡、原协议和源码，不启动训练、构图、GT、ANN/NSG、未曝光query或held-out。主搜索与默认没有变化。

## 一、结论先行

历史不能支持“还没有用过真实搜索奖励或成本敏感监督”“currObj缺完整wall”“只要保留原两个入口就不降召回”等说法。真实联合标签、成本敏感策略、查询侧非线性、自由静态画像、上层状态、动作图正则、特权目标服务及其廉价编译都已实际测试。E36 MLP/RL奖励实际是Recall与总NDC，完整QPS为独立评价；不能将它写成直接QPS训练。E118使用真实graph时间差，E164在四rank动作上使用完整query时间均值与整数召回约束，因此也不能称真实时间监督从未测试。全部模型家族与完整wall标签的组合并未被穷尽，但仅换cost标签或模型不足以构成当前研究缺口。E164关闭了E126的相对rank/目标预算/完整wall缺口，继续加state、trace、深度、阈值属于已停止版本的扩展。

目前仍有两个具体、可推翻的缺口：

1. **目标信息的访问费用**：固定原20K训练GT1库，用现有GT10路由选择倒排桶，再扫描raw目标；这是尚未实现的访问机制。它有E165/166的Web R1局部质量信号作为动机，但标准粗细索引已有前作，且桶覆盖、目标打分代理和完整wall均可能失败。
2. **20K目标访问与联合动作的组合**：原rank1/2与本query直接从固定raw-target bank选出的H外target一起进入同一个原生三入口搜索。E23/E35/E36的真实三入口动作限H；E116是固定槽绑定，但输出同样随query选槽变化，不能称其“不依query”；E165/166的目标库选择只用单入口，P2/P3则改变了搜索过程。这个缺口属于更大候选域、新访问方式和联合动作的组合，不能叫首次query-specific H外点、首次联合学习、首次目标监督或新排序理论。

两项都没有已证可靠Recall–QPS改善，不能因未测试就判为更可能成功。优先保留简单、无学习、固定动作控制；没有足够信息或费用证据时停在设计层。

## 二、已测试边界与不可换名重启的路线

| 家族 | 核验的原机制 | 实际证据边界 | 对新提案的约束 |
|---|---|---|---|
| E25 | 两套固定三入口策略；query范数、画像分数/间隔、ESS、角漂移、入口重合；额外3/6次raw IP及两路路由收费；线性门 | Web局部修复被双路费用抵消，Y放弃多数收益 | 再加入口raw距离、gap、置信度、简单defer没有新信息来源 |
| E23/E28/E30/E32/E35/E36 | 原H内真实联合三入口；多个context、C8全部56组合、等价教师、直接真实收益；E36有76维特征、非加性MLP和三步换点/停止 | 代理/训练改善与开发质量、完整费用分离；E36完整wall下降8%–9% | 不能把“用了联合奖励”“组合是非加性”“RL多步”当作未测缺口 |
| E104/105 | QLinear/QMLP、WFree，同56真实集合监督；WFree冻结后双集各4096新源、128点完整曲线 | QMLP开发门失败；WFree新源救回/损伤接近抵消、共同Recall阈值均更慢 | 更大query塔、自由W、更多epoch/seed不是当前缺口 |
| E116 | 每槽4频率+4几何H外候选；替一槽、原另两入口保持，真实联合标注；最终至多16个固定绑定 | 开发固定版本召回/速度无稳定综合收益 | H外入口和保两入口并非首次；新的差异必须是每query动态目标访问与选择 |
| E117 | 同次实际top3四动作（default3或rank1/2/3单点）；六关系特征、深度2浅树、Recall/Cost/置换同监督 | 实际K1/K100/L128及32点完整wall；未形成可靠增量 | 入口数、raw入口分数及浅树收费已检验，不能靠新阈值声称新方法 |
| E118 | 32共享比较方向、ReLU64、多输出ridge，全H单入口对动态默认的Recall/graph-time差 | 全H oracle有余量，MSE略改善；主GraphCost20点命中完全不变却更慢；140点完整wall | 不能把oracle、全矩阵MSE或方向数量扩展当成新的可用信息 |
| E121 | 上层结束节点z→全H固定真实ID，四折、全局/置换控制 | 有状态相关信号但低于默认；当时费用为graph-only | 不应把全部入口信息称无用；本冻结状态表仍已停止 |
| E122 | query线性效用预测、真实hub响应图函数正则、同谱置换/无图控制 | 结构信号存在，最大化选择误差仍导致外折负净效用 | 标准多任务图平滑不是未测路线，更小MSE不等于更好动作 |
| E123/124 | 真实GT区域→入口服务表；特权外折正值后，用query ridge预测区域并静态编译 | 特权信息有效，廉价学生未取得净收益；更多语义样本改善MSE却不稳定改善动作 | 不把GT预测/语义蒸馏重新命名为新监督；代理校准缺口已实际暴露 |
| E164 | z→query相对rank四动作，在Web1000/1250、Y128/256实际响应和完整wall，同固定/置换/六特征控制 | 四点召回均值负；两K100轻微提速伴质量损失；State四点未超过置换召回 | 原E126缺口已关闭；不再加state/trace/阈值/深度/预算/样本续调 |
| E165/166 | 原20Kquery近邻→其GT1单入口；同容量raw目标HNSW与投回H/置换控制；冻结target曲线 | QueryTarget四点更慢；TargetBank Web R1质量局部正但12同L点均慢；72跨预算无经验支配 | 保留目标侧信号，不归给query配对学习；不加案例数/ef/GT数/预算网格追正 |

### 原协议和源码核对入口

- E25：[详细卡](../../experiment_history/14_selective_profile_gate.md)、[原协议](../20260910_selective_profile_gate_v1/protocol.md)、`src/gate_policy.hpp`。实际使用query范数、gap、ESS及raw-entry重评分，不能记成只看几何且没收费用。
- E23：[详细卡](../../experiment_history/12_three_entry_rank_exploration.md)、[原协议](../20260910_three_entry_rank_v1/protocol.md)。所有候选始终是原H真实hub；前三context确实保留top3中任意两点。
- E35：[详细卡](../../experiment_history/24_hnsw_selection_diagnosis.md)、[原协议](../20260911_hnsw_selection_probe_v1/protocol.md)。56组合来自同一次GT10 top8，且top8属于原H。
- E36：[详细卡](../../experiment_history/25_query_swap_policy.md)、[原协议](../20260911_query_swap_policy_v1/protocol.md)、`src/runner_v2.cpp`。一次top8、全部56特征/MLP的费用，即使早停也已支付。
- E104/105：[表示卡](../../experiment_history/98_query_representation_pilot.md)、[新源复验卡](../../experiment_history/99_wfree_frozen_replication.md)及所引协议/decision。原停止状态与独立query角色保留。
- E116：[详细卡](../../experiment_history/117_entry_id_pilot.md)、[原协议](../20260920_entry_id_pilot_v1/protocol.md)。每query通过固定槽的绑定确定新ID；不是扫描target桶后动态选raw目标。
- E117：[详细卡](../../experiment_history/119_entry_set_pilot.md)、[原协议](../20260920_entry_set_pilot_v1/protocol.md)。协议明确“不追加两入口、C8或其它节点”。
- E118：[详细卡](../../experiment_history/121_comparison_direction_pilot.md)、[方法](../20260921_comparison_direction_pilot_v1/method.md)、[最终判断](../20260921_comparison_direction_pilot_v1/decision.md)。全H最大化与完整公共特征费用均已讨论。
- E121–124：[状态](../../experiment_history/128_router_state_table.md)、[动作正则](../../experiment_history/129_action_coupled_ridge.md)、[特权服务](../../experiment_history/131_target_service_privileged_gate.md)、[静态编译](../../experiment_history/132_semantic_service_linear_compile.md)、[误差分解](../../experiment_history/133_privileged_surrogate_decision_geometry.md)及所引原协议/理论。
- E164–166：[状态rank](../../experiment_history/164_router_rank_pareto_online.md)、[query→target](../../experiment_history/165_query_target_transfer_online.md)、[冻结曲线](../../experiment_history/166_target_bank_frozen_curve.md)及所引协议。E165 `src/experiment.cpp` 的 `once` 分支为TargetBank/QueryTarget各填单个有效ID；`base_engine.hpp` 当前wrapper只接受1或3个有效ID，底层冻结kernel可处理≤3。若将来增加Default2对照，应单独验收wrapper与原kernel消费，不能假设现评测器已有两入口能力。

## 三、缺口A：固定目标库的低费用访问

设固定训练GT1多重slot集合T、原H中的离线归属h(t)，原实际GT10三入口G(q)。候选为

\[
T_c(q)=\{t\in T:h(t)\in G(q)\},\qquad
t_c(q)=\arg\max_{t\in T_c(q)}q^\top x_t.
\]

动作保持原单入口NSG；空桶回退、raw-IP、重复slot、tie和连续布局需事前冻结。被选桶距离数为M(q)，平均数是`Σ_h |T_h| Pr[h∈G(q)]`，不是`3×20K/H`。原[未执行设计](../20260930_theory_until2200_v1/research/target_bank_coarse_access_design.md)已核对。静态桶分布不能证明在线平均费用。

本轮主代理的[旧ID数组只读诊断](bucket_feasibility.json)和[独立实现核验](bucket_independent_audit.json)现已完成，没有打开query/base向量或生成新分数。4096旧query实际路由选桶后，Web/Y的unique候选均值为82.121/85.385，物理slot均值107.330/86.837；还须支付原GT10路由112.259/107.014次距离请求。按unique扫描相加仅为194.380/192.399次请求，对原TargetBank234.444/304.942看似减少，但两种内核、访问局部性、扫描组织和额外控制不同，这些计数不构成wall预测。

更强的质量反证是原TargetBank所选slot只被粗桶覆盖33.765%/45.728%。Web K1/L1000原target相对Default3救回50、损伤28，其中桶内仅10/3（净7），桶外40/25（净15）；因此不能继承原target的大部分正信号。旧slot覆盖既不是新桶内argmax恢复率，也不是新入口Recall：即使旧slot在桶内，精确raw-IP仍可能选择另一节点；桶外的query也可能从另一target救回。此诊断只减弱“便宜访问大致保原行为”的论据，未测新方法，缺口A维持HOLD。Web有2条空候选query，回退费用和动作也必须写入未来协议。

**可推翻预测**：相对20K TargetBank小图，GT10选桶能保留足够有用target，同时使完整`原路由+桶访问+raw扫描+映射+原搜索+输出`更快，并在预声明工作区间形成相对默认的实测前沿改善。

**最强简单反例**：目标单入口的实测局部信号可能来自全目标小图选择的特定节点；粗筛漏掉该节点、精确IP改选另一个更近却更差的入口，都会消失。全target几何最优不是真实搜索效用最优。Web的GT10 coarse images与target raw空间不同；Yandex的原raw-IP目标范数还使角度归属不等于MIPS覆盖。即便M小，内存访问/扫描/额外完整路由仍可能抵消主搜索少量节省。

**最低控制**：Default3、完整原路由后rank1、固定20K TargetBank1、CoarseTarget1；若声称语义分桶是原因，还需同桶数/匹配扫描量的普通目标几何粗筛或固定置换桶。普通索引控制有同预算优势时，收益应归控制。免费读取历史TargetBank入口并检查其是否在桶内只可作为覆盖诊断，不能作为新在线方法/QPS。

**应分开的三层**：候选访问覆盖；raw-IP代理对真实单入口效用的排序；完整wall。任何一层通过不自动补齐后一层。标准IVF粗筛和表内扫描已有成熟前作，本版本差异是对有限监督目标库的访问与固定NSG初始化配合，尚无论文原创性结论。

## 四、缺口B：动态目标与原两入口的真实联合动作

设原query相对rank为h1/h2/h3，目标访问输出t(q)。冻结两种不同作用：TargetSingle使用{t}；MixedTarget使用canonical的{h1,h2,t}。重复时应按预定规则回退到原Default3，避免把1/2/3入口数变化偷偷混进主方法。

这是本query直接从固定20K raw-target bank选择t的动作；不是E23/E36的H内第三点，不是E116对画像槽的常数绑定。E116虽绑定固定，实际H外输出仍依query选槽而变化，部分query也已有保两入口的同形动作；因此差异必须明确为**直接target访问的候选域/选择机制加固定rank1/2联合**，不能只靠“动态H外”命名。需要明确不增加在线GT、不根据评价反馈更新目标库或固定规则。

**可推翻预测**：target带来原H没有的短路径，保留h1/h2对部分query的进入路径，使MixedTarget的真实联合救回−损伤比TargetSingle更好，且完整主搜索节省能支付target访问。在当前目标预算/同输入上，必须超过Default3并战胜Default2、TargetSingle；只战胜TargetSingle可能只是修复它放弃原入口的损伤。

**最低控制**：Default3、Default2={h1,h2}、TargetSingle={t}、MixedTarget={h1,h2,t}。如果主张新增收益来自query-specific H外target，还应比较{h1,h2,h(t)}或同桶/同访问费用的置换target；两控制各自付出真实费用，不用单入口缓存拼接联合反馈。

**最强简单反例**：加入较近target可能抢先展开高分诱饵，将原两入口中的桥节点从有限pool淘汰。替掉rank3也可能删除真正有用路径。保留两入口不产生质量证书；将原入口钉住/强制先展开则改变主搜索，超出这一假设的合同。

**历史直接排查**：

| 可能撞车的历史项 | 为何不等同 | 已有重叠必须承认 |
|---|---|---|
| E23 | 所有第三候选是固定H成员 | 保两入口、第三点真实联合监督已经做过 |
| E35/E36 | 原GT10 top8⊂H；56真组合与非加性MLP | “联合不是可加”及真实组合reward已经做过 |
| E116 | 每画像槽至多一个固定H外绑定；最多16槽编辑 | H外点+原另两点的真实联合标注已经做过 |
| E165/166 | 动态目标全部以单入口传入原搜索 | raw目标库及局部Web R1信号已经做过 |
| P2/P3 | 原Fast首入口+NSG shared seed+8/12固定区域门户；消费全seed并调用RegionalSearch | 目标区域、真实门户和多种入口并存已有研究；不能宣称首次粗细或多seed |

P2源码`benches/bench_hierarchical_eval.cpp:198–265`、P3源码`benches/bench_hierarchical_eval_p3.cpp:281–349`可见：`needs_model`分支保单Fast anchor、设置shared seed并追加固定门户；非Fast方法调用`rg::search`。RegionalSearch有独立global-topK及队列/调度，不能用其失败结论直接判本固定E99三入口失败，但也不能把共享组件当原创。原P2/P3协议及[详细卡](../../experiment_history/07_hierarchical_p2_p3.md)已重读。

## 五、同三入口反例：保留两入口仍可丢GT

以下为解析构造，没有执行新搜索。它扩展记录145已有原生1→1+1反例，用于审查MixedTarget的质量保障；不是新ANN证据或新失败定理。

取q=1、raw-IP、K=1、任意L≥3，令唯一GT节点g的分数为10。强连通图是单向环：

`v0(1) → v1(2) → g(10) → a(−2) → b(−3) → t(9) → d1(9.1) → … → dL(9.9) → z(−100) → v0`。

诱饵分数严格递增。原三入口S={v0,a,b}：最高初始点v0展开v1，再发现g，故最终命中唯一GT。更高IP新目标t替换b，保留原两点：S'={v0,a,t}。t先展开，递增诱饵不断抢先；在发现足够多诱饵后，v0和a被有限L候选池淘汰，且尚未展开。最后桥z分数低，被拒绝，g始终未发现。于是R1(S)=1、R1(S')=0；S2={v0,a}也成功，但S2∪{t}失败。

从入池后的不可淘汰角度看，全库top-L由g及最高的L−1个诱饵组成；老桥v0/v1/a/b/z和target t都在top-L之外。这个反例与“已发现的全库top-L节点最终被扩展”的条件证书相容，只说明其支持条件不可省略。强连通、入口IP更高、入口数同为3、保留两入口，都无法代替该条件。

本轮安全前沿证明由另一代理维护；审稿强调：固定每节点分数总序、有限且严格且低于empty sentinel的分数、GT与该总序一致、K≤L、有效seed数≤min(3,L)、无额外cap和原自然展开，是从全库top-L诱导子图可达覆盖推出Recall下界的条件。固定P_L上的初始seed覆盖`C_L(S)=Reach(S∩P_L)`可单调次模，实际有限pool Recall仍非单调。本反例的安全覆盖下界为0，故不矛盾。原[记录112](../../experiment_history/108_one_hop_hub_design.md)已有一跳条件GT覆盖与次模选择设计，不能将覆盖框架本身认领首次发现。

还需分开数学模型与当前浮点实现：`faiss/faiss/IndexFlat.cpp`分别调用`fvec_inner_product`及`fvec_inner_product_batch_4`；`distances_simd.cpp`是不同编译归约路径，有限输出parity不能证明任意节点分数永远与调用分组无关。严格实数总序的条件定理成立；要声称原生核无条件继承，应额外证明/核验路径一致或足够的排序间隔。共同总序还必须覆盖**混合路径之间的比较**：仅scalar内部和batch内部各自排名相同不够。例如两条评分路径分别给a/b/c距离0/1/2和100/101/102，各自同序，但b/c作为scalar种子时，新a的batch距离100可被cutoff2拒绝；此为条件审查的解析反例，并非实际Faiss数值观测。本轮不重算全库分数或GT。

进一步前作碰撞：[Prokhorenkova与Shekhovtsov，ICML2020原文](https://proceedings.mlr.press/v119/prokhorenkova20a/prokhorenkova20a.pdf) §4.4及图1已用最近m节点诱导子图连通性解释beam≥m且进入该区域后能发现全部m近邻。本轮任意有向图、多seed部分GT可达覆盖和浮点前件是这一安全区域思路的具体推广/适配，不能声称首次发现近邻诱导子图证书。该文随机单位球模型的复杂度结论不适用于这里的冻结raw-IP图。P_L本身也不由当前免费路由输出提供；当前只知近入口不能判定路径中每个桥的全库rank≤L，故这一条件证书尚不是可上线门控信息。

另一代理的[搜索响应稿](search_effect_theory.md)进一步用实际outside展开集合E_out定义后验边界源`B=(S∪N(E_out))∩P_L`，证明safe发现集等于`Reach_{G[P_L]}(B)`。上述环反例也直接解释它：原动作会展开outside桥v1并把g作为safe边界源；mixed先追诱饵，v1没有发现，g不进入新B，safe子图中的诱饵分支到不了g。真正损失来自outside桥未展开，不是已发现safe节点被新target淘汰。初始C_L覆盖的次模性质不继承给随真实执行变化的B(S)及其覆盖。该解析解释未运行新native实验，后验B也不是免费决策特征。

对同稿pool响应商空间的交叉审稿：在同q/图/L、合法完整行边界、固定严格评分序及无cap条件下，相同live pool身份确实能推出相同最终返回ID，但pending/visited和实际cost可不同。此处只压缩**同q返回响应**，不是跨query可迁移教师；换q会改变排名、GTK与后继路径。初始pool相同通常就是同三入口，E46已覆盖这个朴素缓存。不同入口轨迹在后续边界汇合才提供额外共享标签空间，目前没有汇合率或成本证据。C1完整state仍是精确恢复原执行/trace的必要实现合同；不应删掉visited/pending或把响应类中的不同cost合并。

已另实读Bosch/Storandt的[SPD官方原文](https://ojs.aaai.org/index.php/ICAPS/article/download/36113/38267/40186) Definition3–6/Theorem1：greedy单入口的返回区域由局部Voronoi约束沿路径取交、跨路径取并，作者给精确2D与高维离散实现。因此搜索比较区域与返回响应分区不是首次理论思想；有限beam/IP的程序比较适配及native误差前件需另证。主稿的双动作差分恒等式则正确：同q两返回集合相同时ΔRecall必为0，无须GT稳定；这不保证两动作绝对Recall或wall稳定。

主代理后来授权本代理复核旧终局返回数组；[独立脚本](response_class_independent_audit.py)/[结果](response_class_independent_audit.json)采用struct/zipfile/Counter/set/Fraction，未导入主NumPy实现。CPU0、实际进程1线程，36个pair-point、147456个query-pair、828个统计字段全部对齐；重算逐query Δhits并验证其绝对值不超过单侧输出成员替换数，主114输入SHA/bytes与本次控制身份均前后不变。Web K1/L1000 Default3–TargetBank1的3998/4096行同返回集合，其中3991行总NDC不同，另20行hits相同但集合不同；Y K100/L256对应3420行同集合，其中3416行总NDC不同，另89行hits相同但集合不同。这直接证实终局响应比hits并列更细、比执行费用更粗；没有live pool中间trace，故不证明入口轨迹汇合、可省监督费用、跨query迁移或wall等价。未打开GT/query/base向量或执行新评分/搜索。

同一旧诊断亦有有序/集合身份差异：全部36个pair-point累计136092行同集合、135928行同有序返回，差为164个pair-query；这是跨方法对/预算单元累计，不能称164个独立query。K100的Default3–TargetBank1在Web三个L各有20行、Y三个L各有3行返回集合相同但排列不同；例如Web L1250为3512行有序相同、3532行集合相同，Y L256为3417/3420。这给“无条件共同native严格序”的外推一个具体风险观察。未读取返回distance，无法区分同距、归约路径、tie处理等原因，不归因为kernel错误；同集合也不自动证明排列或distance bits保真。

[记录145](../../experiment_history/145_profile_routing_search_bridge.md)的原`toy.cpp`与`results/toy.json`已核：同原span+batch4，L2/L128，negative-IP和squared-L2共12次实际合成调用，单远入口命中而近入口及远+近入口失败。本轮只读取旧代码和旧结果。

前作边界：已阅读Al-Jazzazi等[Distance Adaptive Beam Search](https://arxiv.org/html/2505.15636v1) §2、§4、Claim 2。作者在可导航metric图上给出更强的有限beam反例，正保证则改停止规则。本项目的raw-IP、冻结图与固定停止不满足其前提；把IP排序转成欧氏排序也不会自动证明原图具有导航性质。此解析构造只为本次入口合同排除不成立的保障，不认领首次理论发现。

## 六、额外工程缺口：同query重复距离的trace保真复用

这不是新的入口信息或联合动作。固定E165/166全部20K物理slot、W/raw向量、层级、有序邻接、入口、ef、slot tie与原NSG动作；同query中若一个实际raw目标重复被距离回调访问，可以缓存第一次的**同一原生浮点结果**并在后续访问返回它。图节点仍按原slot参与队列，不删除slot、不重新排序、不改变逻辑访问。条件满足时可按每次回调归纳恢复原路由slot和完整NSG输出；目标是输出保真下减少重复算术，未证明费用下降。

核查E35/E46/E72/E73/E99–102详细卡/协议和有关源码，以及E165/166路由源码，在此范围**未发现相同trace保真distance memo已执行**。具体差异：

- E35 `src/probe.cpp::observed_ip`把每次上/底层事件记入数组后，直接调用原`fn`；它观察重复，未复用距离。
- E46只按完整query/三入口/图/核/L/K身份复用离线NSG全部响应；路由每次真实执行。这是跨动作反馈缓存。
- C1/C2 `state_machine.hpp`保存的是retset距离、visited/expanded等；`evaluate`要求未visited再调用dc，`inject`对已visited入口直接no-op，没有通用全query距离memo。普通主NSG已在距离前visited去重，故本次空间主要在HNSW上/底层重访以及不同target slot的同raw目标，而不是重复计算一个主图节点。
- E72按真实hub引用数计宽，改变保留/返回规则；E73删除同hub字节重复slot并重构图，近似拓扑及入口改变。这些不保证原trace。
- E99–102改变预取、候选复制、有效邻接span和batch4；原协议保留完整距离调用，并公平给全部共享NSG方法。E100较少NDC却更慢的反证仍适用。
- E165 `CaseRoute::counting`在plain直接接原Space距离；`common/evaluate.cpp::counted`每回调加1后调用原函数，没有距离memo。E166沿同机制。

**最强简单控制与反例**：Default3也要获得同query、同物理slot的通用memo优化，再与TargetBank memo作完整wall比较。不同profile空间、raw目标空间和主图raw-base不能仅因ID相同就共享距离。映射到同raw目标ID的不同slot只有向量bytes/距离路径一致时才能共用值，队列仍保留各slot；普通同slot上/底层重复是另一个可分开的来源。缓存lookup、清零/epoch、载入/分支及额外内存可超过省掉的点积；重复数少或热cache下点积便宜就可能变慢。独立报告逻辑distance请求、unique物理slot、unique真实目标、实际完整IP调用，不能把逻辑trace计数变化混写成搜索减少。

原版Default3同样保留。主代理的[完整成本恒等式](full_cost_conditions.md)用D=T_A−T_B、S_A/S_B分别表示两方法的净memo节省；`S_A−S_B>D`只保证TargetMemo胜DefaultMemo。如果默认memo反而变慢（S_B<0），这一控制可能降低门槛；同时胜原版和memo版默认的严格条件为`S_A>D+max(S_B,0)`。这只是成本恒等式，没有新计时，不能利用一个被cache拖慢的默认宣称可靠方法收益。

当前E166只存总路由NDC与最终slot，没有每query完整重复访问trace；旧E35 trace是另一画像bank，不能外推target重复比例。静态20K中Web15789/Y19671个unique目标只说明可重复空间，不说明实际轨迹命中。先停在HOLD，既不从静态去重率预测QPS，也不把memo称论文创新。上述结论仅为核查范围未发现同一已执行实验，不是全面首次性证明。

本轮额外只读E35原`results/<dataset>/trace_events.json`，按每行`len(events)−len(set(events))`计数，没有新分数或搜索：旧ef10/k8、每集128query，Web逻辑回调/unique物理slot均值112.820/103.414，重复9.406（总回调8.337%）；Y106.891/97.766，重复9.125（8.537%）。两集各128行均有重复。这证明旧画像路由的通用memo控制不是空对照，但数据角色、bank与本次target不同，不能将这些比例作为E166或真实wall收益。

## 七、研究进入条件与停止边界

对主代理[度量/概率迁移笔记](metric_transfer_limits.md)亦完成交叉审稿，并实读[Neyshabur/Srebro原文](https://proceedings.mlr.press/v37/neyshabur15.pdf) §4.2/5.3、[自适应入口原文](https://arxiv.org/html/2402.04713v1) Theorem4.4及[PEOs原文](https://arxiv.org/html/2402.11354v2)的RoutingTest/Theorem6.3与MIPS附录。IP补坐标仅保精确排序，近似distance因子转回score有加性项；一般不保数据点间几何或原图导航，等范数特殊情形应另算。入口hop上界之间的比较不推出实际hop大小关系。PEOs局部误拒界若额外对同一参考trace成立，且所有非误拒转移都耦合保决策，union bound才给输出偏离概率p；无需独立，但需局部界/条件化前件。于是固定query的期望Recall损失至多p；p可能为1，无单次质量或QPS保证。上述为条件审查推导，不把论文直接保证写成当前项目保证。

这次授权是理论/论文研究。本文件不授权或启动任何性能试验。若以后另有实验授权，应在反馈前冻结目标库/访问方式、动作、query角色、真实K/L、完整成本、最低实际收益、可靠性及结束边界；原164–166协议和历史结果不回改。

缺口A的旧数组访问覆盖与M(q)已查，覆盖不足，不能借此授权执行；缺口B没有已对齐的MixedTarget真实联合响应，single标签不能补齐，而且其廉价动态访问前件尚未支持。只有访问行为和完整费用有希望时，才值得在新授权下生成一份固定最小动作的真实联合反馈与完整wall。无需先训练新评分器；简单固定控制已足以反驳两项假设。trace保真memo另需真实重复访问及公平默认优化控制，现无trace不能性能GO。双集/双K正负全部保留，明确单集适用边界；出现质量取舍不叫可靠综合改善。

没有证据支持继续深树、更多共享方向、更大MLP/RL/双塔、更多target/ef/GT数/seed。理论可在现有信息的支持范围和成本上取得进展；不能为了满足截止前“有方法”而制造成功候选。

## 八、本轮审查身份

- 直接读取AGENTS.md、完整summary.md/spec.md/s-target.md/s-experiment.md，沿详细卡进入上述原协议/源码/旧结果。
- 0新训练、构图、GT、真实ANN/NSG、新query、held-out；不读取大底图或运行旧runner。
- 最初仅新增本文件；后经主代理明确授权，另新增独立只读复核脚本/小JSON `response_class_independent_audit.py/json`。本代理没有改动根文件、历史封存或其他代理文件；独立复核JSON及其脚本已冻结。
- 使用记忆仅作历史索引定位；当前结论均由现场原件重新核对。记忆注册表`MEMORY.md:50–84`用于定位E126旧边界及E164–166最新状态，未把其旧HOLD当作现状。
