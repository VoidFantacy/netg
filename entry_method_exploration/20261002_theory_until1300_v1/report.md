# ACSG理论与Recall–QPS方法研究

研究日期：2026-10-02，截止13:00（Asia/Shanghai，UTC+8）。本轮已于13:00结束理论研究，现为封存终稿。本轮按用户授权阅读原论文、核对历史/源码、推导条件与反例，分析已曝光旧数组，没有新真实ANN/NSG/GT、训练、构图、未曝光query或正式性能。

**当前没有新的可靠Recall–QPS替代。理论的实质进展是把入口几何到有限搜索的缺口缩小为“哪些桥展开、从哪里进入安全前沿”，并给出返回等价和浮点充分条件。方法上优先保留原路由内距离复用这一可隔离的成本问题；它有明确前作，尚缺真实重复trace与完整费用。三桶粗筛受到新的只读覆盖反证，动态raw-target联合动作仍缺访问与联合响应，全部保持HOLD。**

## 1. 当前基线及性能边界

默认仍为WebVid GT10-soft-t1、Yandex GT10-hard，生产E99。最新真实性能记录166，旧9月30日runner与22:00安排未恢复。166的两集各4096历史E105开发query、36配置/108完整wall轮次已核验：12个TargetBank同预算点均更慢，72个预定跨预算比较无经验支配。

下表是E166冻结span+batch4研究核上的默认入口策略与TargetBank控制，共用同核并验收原E99输出；这些绝对QPS不是已部署生产E99的现场计时。生产核没有切换。

| 各自最快实测R90点 | 默认Recall / QPS | TargetBank Recall / QPS |
|---|---:|---:|
| Web R1/L1000 | 90.454102% / 417.190 | 90.991211% / 413.177 |
| Web R100/L1250 | 90.581543% / 334.895 | 90.576416% / 333.291 |
| Y R1/L128 | 90.625000% / 2364.615 | 90.625000% / 2283.658 |
| Y R100/L256 | 91.044434% / 1289.884 | 90.885010% / 1264.985 |

Web R1有局部质量信号而速度降低；其他格未形成稳定质量优势。旧query与网格不能证明全预算或新来源效果。E164已经实际关闭旧E126的state/rank/目标预算/完整wall缺口，E165/166目标访问是已执行对照；不能再据旧记忆把这些写成“未实现”。详见[当前summary](../../summary.md)、[历史碰撞审查](history_gap_audit.md)。

## 2. 理论完善：从几何代理到发现机制

### 2.1 有条件的精确机制式

在固定有向图、同query、路径无关严格评分顺序、L≥K、合法实际seed及自然完整展开下，pool始终保留已评分集D的前L，该顺序的全局前K只要被发现就会返回。**另须假定评价GT_K与该全局前K一致**，才能写RecallK等于发现了多少GTK，而不是入口分数有多高；真实标签/native排序不一致时用明确误差项或保守交集下界。

令P_L为全base全局前L；其中节点一旦发现不会被淘汰，最终必展开。初始seed在P_L中的多跳可达GTK得到安全下界。进一步令E_out为实际展开且不在P_L内的节点，定义后验边界

\[
B_L=(S\cup N^+(E_{out}))\cap P_L.
\]

则

\[
D\cap P_L=Reach_{G[P_L]}(B_L),\qquad
Recall_K=\frac{|GTK\cap Reach_{G[P_L]}(B_L)|}{K}.
\]

这补足了通常原hub位于前L之外的情形：它们经桥节点进入安全区域。新增更近target可能抢先展开诱饵，淘汰尚未展开的桥，改变E_out与B_L；所以真实Recall随seed集合仍非单调。固定P_L上的初始seed安全覆盖下界C_L(S)是单调次模；后验B_L依赖实际展开，不能将它的覆盖或真实联合Recall误认成次模。

这不是新免费特征：P_L需全局排名，B_L是运行后量。ICML2020[Prokhorenkova/Shekhovtsov §4.4](https://proceedings.mlr.press/v119/prokhorenkova20a/prokhorenkova20a.pdf)已有近邻诱导子图连通与beam保障；本次是对任意有向图、多入口、部分命中及当前实现条件的适配和精确分解，没有证明独立原创性。证明、边界和反例见[search_effect_theory.md](search_effect_theory.md)。

### 2.2 返回等价比完整执行等价更粗

同query下，两个合法可达的完整邻接行边界状态若live pool IDs相同，在上述严格评分/自然停止条件下继续执行会返回相同ID集合。pending/visited差异可能只增加被拒绝节点的重评分，NDC和wall仍可不同。partial-row、强制恢复、cap、ties或路径间排序变化不直接满足该证明。

这个等价类允许理论上共享返回标签，不能删掉原实现的visited/pending、合并费用或把同query结果外推到另一个query。初始pool相同通常只是同三入口，E46完整响应缓存已有；不同入口轨迹后来汇合同pool才是额外可能性，目前无汇合率/省监督费用证据。状态商空间/多教师/direct-reward都有前作，仅换损失或模型名称不是新方法。

另一个差分结论是：两动作在共同trace比较符号区域内保持相同返回集合，则它们的Recall差为0，即使GT随query变化也成立。返回不同的两动作，只需跟踪输出对称差支持上的GT变化；单动作返回稳定并不保证绝对Recall稳定。路径响应区域已有[SPD，ICAPS2025](https://ojs.aaai.org/index.php/ICAPS/article/download/36113/38267/40186)直接前作。

补充[预冻结的旧输出诊断](response_equivalence_protocol.md)覆盖双集6点三方法全部36个方法对单元，114输入身份保持，没有新评分/搜索/GT。四旧中心Default3与TargetBank同返回K-ID集合的query数为Web R1 3998、R100 3532，Y R1 3893、R100 3420（各4096）；其中graph NDC不同有2887/2334/3876/3405条。same hits却不同返回集合另有20/52/27/89条。它支持返回类比hits类严格、返回不决定访问工作量；没有测各query wall，也不能称合法中间pool汇合率或可部署标签迁移。完整结果见[response_class_check.json](response_class_check.json)，独立代理另用struct/zipfile/Counter/set/Fraction复核147456行方法对、828字段：[独立审查PASS](response_class_independent_audit.json)。

### 2.3 native浮点不能被数学等值替代

旧K100数组还存在同返回集合但顺序不同的情况：Default3–TargetBank的Web L1250有20条，Y L256有3条；全部36方法对单元累计164条pair-query。这没有读取距离，不能归因于某种tie或kernel错误，却说明旧集合一致不能证明共同严格总序或位级输出一致。

原seed/scalar与neighbor/batch4归约不同。理论中的共同严格序要覆盖混合比较，不能只凭两个kernel各自内部排序相同或若干输出parity就全局断言成立。

更保守的充分条件是对每节点的所有评分路径给有效区间[l_v,U_v]。把所有可能不劣于v的点计为威胁，若威胁少于L，v发现后就安全保留/展开；若少于K，v发现后必返回K。以安全L集合内路径、真实GT和安全K集合交集得到Recall下界，可容许ties/舍入差。真实全base区间尚未建立，证书可能为空且费用高，所以仍是条件理论。

合成核验覆盖344064个有限pool机器案例、677440个合法完整行状态、211921组差分集合及57344个含ties的区间机器案例；[数学结果](search_effect_math_check.json)通过。它们是整数/有理数符号模型，没有native搜索，也没有证明真实数据满足所有条件。历史审稿与另一调度实现用于查遗漏，不替代数学证明或性能确认。

## 3. 新只读反证：三桶便宜访问不自动保旧收益

协议先固定原20K target→hub归属与E166实际Default3选桶，再读旧slot/命中/NDC；没有query/base向量、新分数或新选择。

| 只读指标 | Web | Y |
|---|---:|---:|
| 三桶物理slot均值 / 最大 | 107.330 / 544 | 86.837 / 182 |
| 去重target数均值 | 82.121 | 85.385 |
| 原GT10+去重扫描请求均值 | 194.380 | 192.399 |
| 原TargetBank请求均值 | 234.444 | 304.942 |
| 旧近似TargetBank选择slot覆盖 | 33.765% | 45.728% |

Web K1/L1000旧50次救回中，10次选点覆盖、40次在桶外；旧28次损伤中，覆盖3次、桶外25次。扫描请求看似更少，仍要支付GT10、布局/选择/去重等费用，不能推QPS。覆盖也不能推新Recall：原参考近似HNSW未必全bank最优，桶内raw精排即使覆盖旧点也可能换到更高分却搜索更差的target。

结果减弱“粗筛保留原局部行为”的论据，没有宣判新方法必败。维持三桶固定版HOLD，不加桶/ef/target数追正。主计算与struct/Counter/set/Fraction独立实现核验全部8192行、12点并保持95输入身份：[只读报告](bucket_feasibility.md)、[独立核验](bucket_independent_audit.json)。第二实现由同一代理完成，不能称独立人员验证。

## 4. 最具体的成本问题：同query原生距离memo

保留原20K物理slot、层级/邻接、visited、heap/tie、ef10及原入口生成/映射流程；仅在一次query内缓存同评分对象首次原distance bits。不同slot映射到相同raw目标，只有byte/kernel/参数/FP环境一致且原callback跨槽返回bits已证相同（包括地址相关算术路径）才可复用，图节点仍各自参与队列。完整回调返回bit一致即可按事件归纳恢复路由/实际入口/主图输出；不免费复用旧入口，不跨profile、raw-target、raw-base或scalar/batch4共用值。

缓存有明确作者先例：[FISHDBC](https://arxiv.org/html/1910.07283v1)及其2018固定提交距离缓存实现，见[访问论文笔记](access_literature.md)。这是尚未发现本项目已执行过的具体工程成本控制，不是新搜索信息或论文原创算法。静态重复率21.055%/1.645%不能替代真实query命中率；E35旧画像trace已有约8.3%/8.5%重复，说明默认也应获得相同优化，不能外推当前目标库比例。

令旧完整耗时差D=T_target−T_default，各冻结版本的净节省含全部新增费用与缓存相互作用。基础四控制比较需S_target−S_default>D；完整方案还含原版/UpperHandoff/memo默认，不能因任一优化拖慢默认降低门槛。令J包含全部这些固定默认控制（原版净节省为0），最终条件为

\[
\boxed{S_{target}>D+\max_{j\in J}S_{default,j}.}
\]

E166 Web R1/L1000的旧D约23.282μs/query，候选需相对更快默认多节省足够时间，才可将旧局部质量信号移向更快一侧。旧时钟差不作为未来严格阈值；所有冻结控制须同批完整重测。[完整成本证明与g门](full_cost_conditions.md)已独立复算，也检验了劣化默认制造假成功的反例。

源码还确定无删除/过滤的非空HNSW每query至少有一次上层终点在base重新评分；直接传原curdist bits是比全请求dense lookup更简单的共享控制，仍未计时。[接口/生命周期审查](memo_interface_note.md)给出该控制及跨slot/address/epoch前件。

**优先级一仍是HOLD：缺真实重复trace、原生bit级保真与匹配完整wall。** 它保留旧正负质量，不能单独解决Y/K100损伤或新来源确认。未来最小窗口/控制已写具体，今天未编译、接入或运行缓存。

## 5. 其他候选与原论文碰撞

| 方向 | 已有前作 / 本地碰撞 | 本轮保留的具体问题 |
|---|---|---|
| GATE直接入口 | KDD2025 hub/图与query监督画像；本地E96/E97/E103已适配与完整wall | 不把图感知/query-aware router或更贵hop标签当新缺口；[原文/release边界](latest_entry_literature.md) |
| 学习粗路由 | Vecchiato SIGIR2024线性GT分区路由；Chiu Learning to Index含簇大小代价；本地query表示/状态/门已测 | 新候选域/真实有限搜索响应和可付访问费用，不能只换更大query塔 |
| 精确/提前拒绝 | FastMKS、FEXIPRO、MAXIMUS、Tribase、Panorama | 全bank精确最优与原近似队列保真须分开；native界、原ef阈值、元数据及query计算成本仍未知 |
| 条件计算 | Bolukbasi ICML2017计策略自身费用；E25/E164已做成本敏感选择 | 新访问动作前的信息是否足以辨识救回/损伤，常数/置换/同监督简单控制必须保留 |
| 动态target联合三入口 | E23/35/36真实组合；E116槽绑定H外ID随query变化；E165/166只测target单入口 | 固定20K raw-target bank直接按query访问t，再与原rank1/2联合，需真联合响应与访问前件 |

[访问原论文逐项笔记](access_literature.md)记录所读方法/定理/作者代码及直接链接。[历史缺口审查](history_gap_audit.md)沿原协议/源码限定新意，不把固定槽绑定误记为完全静态动作。

自适应入口的hop上界、IP-to-L2保排序、PEOs单次概率测试，都不能自动迁移为当前完整Recall–QPS保证。IP规约会引入近似score界的加性项；导航图/原停止/有限概率参数还须各自满足。相应证明、原章节及合成核验见[metric_transfer_limits.md](metric_transfer_limits.md)。补读2025年的[Query-scaled/PSP与MAG](latest_mips_literature.md)进一步区分top1对齐与beam所有比较保序；后者需未知margin阈值。PSP改图/入口/AET，MAG改图并先L2后IP，均不能继承冻结主核的保证。20篇原论文的实读章节均已记录，未称全篇/穷尽前作审查。

## 6. 截止交付与下一边界

各候选已形成可审查的输入、动作、成本、简单控制、第一反证门和结束门：[candidate_gates.md](candidate_gates.md)。[交叉审阅记录](review_notes.md)列出职责、证据强度与已修正的实质问题。没有预先训练新模型的必要；先解决原始访问成本与真实联合效用，不能以RL/MLP/双塔名字代替缺口。

本轮交付包括原论文/历史审查、条件证明/反例、纯合成数学检查、只读桶诊断与独立复核、完整成本门及最小后继方案。[封存检查工具](closeout_checks.py)与[封存预检](closeout_preflight.json)核对157个冻结输入、事前五文档快照、各脚本/结果身份、20篇原论文记录与本地链接；仅核对身份/语法/合同，没有运行真实性能。性能主目标未完成。本轮已于13:00结束理论研究并封存，自动推进停止；所有候选仍HOLD，后续真实实验需用户明确授权。默认与生产源保持，旧停止门/全部历史产物不回改。
