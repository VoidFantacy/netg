# NETG / ACSG 当前研究总结

> 最后核对：2026-09-08。本文件回答当前研究主线、证据边界与阶段决策。实现与复现契约见 [spec.md](spec.md)；当前方案、入口选择流程、阶段gate与接续状态统一从 [s-target.md](s-target.md) 阅读。版本目录中的recommendation保留调研时的推荐论证，不另行维护当前计划。

## 1. 当前方法

### 当前主要方向：改进入口选择方法

2026-09-08论文导向[调研v5](entry_selection_research/20260908_v5/report.md)已完成，状态`RESEARCH_COMPLETE_DESIGN_ONLY`：比较四条候选与既有v4效用树。B“可部署收益驱动的入口发现与路由联合设计”是**论文导向的条件性主候选**，必须发现旧H外入口，并在相同候选母集/路由容量/标签预算下优于coverage-only；A“真实遗憾驱动的多面入口索引”与v4树并列检验表示；C同状态一次入口干预是高风险备选；D策略修改成对标注只定位离线效率支线。没有把它们拼成一个复杂系统，也没有确认任何方案高原创或性能GO。完整机制、近期前作碰撞、成本及最小否决见v5报告与四份专题。

原[调研v4](entry_selection_research/20260908_v4/report.md)的真实效用斜切树保留为共同基线：直接优化原kernel实测收益、多叶可选同hub、query-only单路径、最多10次线性判断；重参照与树分别审计，教师失败不否决成功的树。TAO/成本敏感树已有机制，因此任务适配原创性较弱；全H可选不等于叶动作覆盖全部H，训练改善不是样本外保证。树仍未实现未训练，原[方法](entry_selection_research/20260908_v4/method.md)和[预算草案](entry_selection_research/20260908_v4/minimum_gate.md)保持历史身份。

v5一手审计发现：GATE/LIRA已覆盖学习入口/构造与路由相互指导，Maxout/MUVERA/DFAMS覆盖多面/多原型检索，COAL/BanditEval等覆盖主动成本标注，DARTH/NGFix/SHEAF/CRINN覆盖搜索自适应或查询驱动修图的多个部分。旧probe-reroute已经监督merged Recall/NDC并使用trace/frontier/topology，不能误写成只有独立入口标签；原位共享完整状态与同剩余预算是C尚未测试的差别，不能据省重复工作推断选择可预测。此次仅调研与文档，没有新模型/搜索/环境修改或原始validation/held-out访问，不恢复旧失败分支。

2026-09-08 用户授权的[Fast根因诊断已完成](fast_router_diagnosis/20260908_v1/report.md)：双数据集各512历史pilot，原NSG/raw-IP与20K paired Fast，全H single及C8真实pair/triple，共2,770,770次搜索。输入/画像复算、真实count/plain/repeat和独立统计核查通过，检查项内未发现实现错误。主要可定位缺口是GT1几何标签/画像评分与真实有限预算搜索效用不一致；ANN近似不是主因，近邻迁移未呈现稳定优势，但不能证明理论不可学习。当前计划见[s-target.md](s-target.md)，Fast基线保留。

单入口exact画像路由相对全H单入口oracle仍差WebVid14.16/11.46 pp、Yandex11.02/5.92 pp（L64/128）；直接知道原GT1 basin标签也仍差13.07/10.35及7.75/4.80 pp。exact C8内最佳single仍遗漏3.16–6.66 pp的全H机会，因此短名单内与外均有损失。这里oracle均是同L、当前H、免费事后选择，不是部署收益或全base上界。

此前固定anchor、固定三入口的默认设计现已撤下：含anchor最佳triple比不受限最佳triple低0.84–3.11 pp，四点全族区间均为正；C8最佳single的平均Recall四点均略高于最佳triple（此项描述性，不能宣布单入口部署最优）。最近fit−随机fit的四个主对比全族区间均跨0；跨L A0集合相交率92.19%/96.09%，不能用唯一ID改变夸大困难。v4树及v5静态候选以单入口作为最小动作检验真实效用表示与可预测信号；不自动训练原v2组合模型、不恢复失败分支。[完整32对比](fast_router_diagnosis/20260908_v1/analysis/v2/analysis.md)。

已有WebVid validation 1K、815现有候选、K10/L64诊断中，Fast Top-3 Recall为65.23%，免费穷举选择的单入口oracle为80.24%，graph NDC为923.564→913.376。这支持该历史候选池存在选择空间，不证明当前入口是唯一瓶颈。它使用旧30K Fast与旧评测、排除选择成本，不能视为新paired20K/双数据集/端到端收益；命中并集贪心三入口也不是最佳联合搜索。[原始诊断](oracle_entry_diagnostics/webvid_validation_1k_current_hubs_v1/results.json)。

当前“工程性较强”的研究问题在于设计缺少统一且经验证的选择原则，模型复杂度本身不构成有效性证据；允许使用重模型检验更复杂的可学习规律。需拆开候选池、短名单/排序和少量入口的实际联合收益，明确监督与成本。GATE/旧NETG已用真实搜索监督，旧静态utility、probe-reroute与Multi-view失败边界保留；“学习入口/图感知/可达性”本身不是新贡献，也不能从历史oracle保证整体提高。

此前基于14篇核心论文的[文献复审](research_direction_review/20260908_v1/report.md)仍支持暂停硬区域、GT集中度/门户代理/静态容量组合；但其“先做P2六点成本筛查，再优先改搜索过程”的R0–R2建议现已被入口方向替代，未运行、不自动排队。强基线、公平成本、split隔离及最终性能门槛继续保留。

此前入口调研按原[调研指令](entry_selection_research/20260908_v1/next_dialogue_prompt.md)完成，其历史状态`RESEARCH_COMPLETE_DESIGN_ONLY`及[20260908_v2](entry_selection_research/20260908_v2/report.md)交付保留。调研比较了搜索效用候选覆盖、独立single utility排序和真实组合选择，当时推荐固定三入口、C8含anchor的21个triple及29个一至三入口诊断；本轮实测已撤下这些默认限制，原调研版本不覆盖当前决策。旧ranker已用真实single Recall/NDC，换模型名不构成新机制。GATE作者release无在线query MLP，Fast相对它的优势不能笼统归因于免去在线神经推理。

[原最小gate草案](entry_selection_research/20260908_v2/minimum_gate.md)及40维组合模型仍未实现未执行，不从本轮诊断自动转入训练。原调研轮只读证据并写文档；本轮另立协议实际运行Fast诊断，两者授权/状态分别记录。旧v1 pending和v2设计状态均是历史交付，原P3 NOPASS、Multi-view成本否决及全部旧产物保持。本轮没有方法源码/环境修改或原始validation/held-out访问。

### 已停止的历史版本：目标邻域驱动的分层搜索

该版本联合设计覆盖全部 base 的目标区域、查询到目标区域占比的层次预测、以及固定总容量下的区域候选保留。原计划先冻结 NSG，先做 P2 机制证伪，再按 gate 构建完整结构和学习模块。夜间授权已按截止完成；已通过 P0/P1/P2机制gate；P3结构与门户完整pilot完成但搜索收益gate为NOPASS，三项有界失败诊断也已完成。版本 `hierarchical_target_search/20260907_v1` 没有有效端到端性能改善证据，真实P2路由退化、oracle同L质量较高但更慢。

依赖已准备：METIS v5.2.1/i64、GKlib、独立基线 Python 环境、kRt/gp-ann MIPS 构建、RoarGraph 和局部 MKL；复用现有 GATE 适配。依赖检查通过不代表方法有效。依赖准备轮没有真实数据实验；本次夜间已完成搜索/计时验收、P2/P3完整pilot及失败诊断，证据另立日志。交接见版本目录 `dependencies/README.md`，`overnight_prompt.md` 为已结束的历史授权原文；该入口调研指令已保留为[历史记录](entry_selection_research/20260908_v1/next_dialogue_prompt.md)，当前优先级统一见[s-target.md](s-target.md)。本方法保持全 CPU。本次方法开发和实验已按北京时间2026-09-08 07:00截止完成停止核验；[实验总结](实验总结.md)已在停止后完成并通过文档复核，没有截止后补跑实验。

P2已运行64个图结构区域、每区2门户，比较统一池、均匀区域池和概率容量区域池。P3已运行16×16区域、每叶3门户共768，oracle全局选4叶区；oracle读取开发pilot真实GT区域占比，仅作诊断，不是可部署路由。P4层次线性预测尚未启动。该历史版本独立于旧 Multi-view、静态 utility ranker 和 probe-reroute。若证据明确指向连接瓶颈，才进入独立辅助图分支。

拟合只用 router_train 后 20K，前 10K 为已有历史使用的开发 pilot；paired Fast 也重建 20K prototype。旧 30K Fast 单列参考。双数据集均须在至少两个相邻工作点达到同 Recall QPS ≥+10%，或同 QPS Recall@10 ≥+1 pp，并有校正区间支持；P6/P7 才确认性能。实现成功和 pilot 通过均不代表项目完成。

### Fast v1：已验证基线

Fast v1 是 `QGT-Cover + closed-form GT-basin prototype + Micro-HNSW top-3`：先用独立 5K QGT 查询及 exact top-100 GT 选真实 base hubs，再用独立 30K 查询的 top-1 GT basin 形成每个入口的“查询画像”（prototype），在线选 top-3 入口搜索冻结 NSG。

它依赖 exact train GT，但不依赖 ACO、DPC、逐 hub probe labels、optimizer 或 MLP，也不修改底图。QGT-Cover 是项目内启发式命名，不是严格 set cover。

### 已结束扩展：Multi-view Target-Basin Routing

`Multi-view Target-Basin Routing` 把三个独立初始化的 Fast build 当作三个 prototype views：保留第一 view 的 rank-0 anchor，合并三路 top-8 候选并选两个补充入口，最终仍以 top-3 搜索同一 frozen NSG。

设计假设是多个 QGT 划分能提供互补候选，anchor 能限制主入口漂移。三个 views 合起来只算一个模型；随机 build seed 不是独立 task，也不是 query bootstrap，因此本方法不能称为元学习。该扩展已在正式化 E1b 因路由成本失败，不再是当前待验证方法。

## 2. 已确认结果

### Fast v1

- WebVid held-out：Fast 在已测预算上优于旧 Formal Neural Router。
- Yandex official 10M/IP held-out：Recall 基本等效，主要优势是 Medoid-normalized QPS。
- LAION validation 与 held-out 已完成；但 LAION 与 WebVid public query 源文件相同，只能证明跨 base corpus/scale 迁移，不能算独立第三 query workload。
- 现有 `build_wall_seconds` 只覆盖已有 exact GT 后的入口构建。完整成本必须报告 `T_exact-GT + T_QGT + T_prototype + T_router-index`，不能把秒级数字称为完整训练。

权威结果：`fast_entry_benchmark_results/benchmark_summary.md` 与 `fast_entry_variants/laion10m_acsg_v1_{validation,heldout}_report.md`。

### Three-view：同 L 有收益，但部署成本 NO-GO

旧 `28/29/30` 单组模型在 WebVid/Yandex validation 10K、Recall@10、`L=64/128` 四点均优于 seed-20260828 Fast：

| 数据集 | L | Python reference Recall delta | graph NDC delta | C++ Recall delta |
| --- | ---: | ---: | ---: | ---: |
| WebVid | 64 | `+0.871 pp` | `-2.278%` | `+0.822 pp` |
| WebVid | 128 | `+0.369 pp` | `-1.388%` | `+0.340 pp` |
| Yandex | 64 | `+0.250 pp` | `-1.709%` | `+0.214 pp` |
| Yandex | 128 | `+0.209 pp` | `-0.992%` | `+0.148 pp` |

这证明该历史三view配置在同 L 下有质量潜力，但不证明部署收益。正式化结果如下：

1. 旧 E0 的 16 项检查通过，覆盖路由／搜索 parity、真实 anchor 和 count/timing 接口分离；后续源码审计发现整批计时仍包含 GT 评分，不能将旧 E0 解释为 wall 计时边界已完全合格；
2. E1 dense 在双数据集 train-1K 上仅 routing NDC 就超过 paired Fast L64 总预算；
3. E1b 固定后两路 `M16/efConstruction200/efSearch32` Micro-HNSW，在 train-10K 将 mean routing NDC 从 WebVid `1760.299` 降到 `642.337`、Yandex `1766.112` 降到 `549.376`，anchor mismatch 均为 0；
4. 等 total-NDC 匹配后，WebVid L64/L128 目标的 Recall@10 分别比 Fast 低 `14.697/4.960 pp`，Yandex 低 `4.103/1.463 pp`，四点全 FAIL。

因此总决策为 `NO_GO_ROUTING_COST`。等 NDC 与等 wall 是合取 gate；前者已失败，计时不能逆转结论，故未运行。E2–E4、tail、独立构建和 held-out 均按规则 `NOT_RUN`。证据：`target_basin_formalization/20260907_v1/{gate.json,report.md}`。

## 3. Claim 边界

- 可确认：三个旧 view 在同 L 下有小幅 graph-search Recall 收益；固定 HNSW-all 后端能大幅降低 dense routing NDC，并逐 query 保持 anchor。
- 不可确认：总成本收益、tail 改善、跨独立构建稳定性、多视角互补因果或 held-out 泛化；这些阶段未获执行授权。
- 不能把失败解释成 HNSW top-8 完全失真：后两 view 对 scalar-float exact top-8 的集合 recall 为 WebVid `0.9873/0.9883`、Yandex `0.9972/0.9976`。真正瓶颈是剩余 routing NDC 挤占 graph-search 预算。
- GATE 已覆盖“冻结图上的 query-aware entry navigation”。本结果不能包装为新的通用路由范式、tail-risk 优化或元学习。

## 4. 已停止方向

- confidence attention：WebVid/Yandex 需要相反 alpha；当前共享-alpha 公式 train-only no-go。结论只针对该公式，不能外推为所有 attention 或元学习无效。
- static utility ranker、probe-reroute、graph-BFS Basin Transition Graph、residual basin modes：已跨数据集或 validation 失败，不再扫同类参数。
- finite-beam trace：trace 有增量信息，但成本／收益集中性不通过；后续 cost-first distillation 的四点 utility CI 均跨零。不得误写成“trace 没有信息”或数学上不可预测。
- 旧 NETG 已用真实 graph reachability；不能把 reachability 本身写成当前创新。

旧分支的实现、表格和诊断保留在 `aco_router_fast_entry.md`、`finite_beam_reachability_diagnostics/`、`probe_reroute_results/` 和其他对应 `*_diagnostics/`，不在本总结重复展开。

## 5. 当前决策

用户进一步明确成本约束为**离线允许重量模型，在线预测保持轻量**。此前“廉价信息”不应限制离线模型/监督/表示的表达能力。后续先用足够表达能力的模型检验样本外真实搜索效用是否可预测，再验证蒸馏、入口侧预计算或其他方式能否在轻量在线路径保留质量；这些是可选机制，不是已验证的新算法。重教师若使用训练侧GT/轨迹，其优势也不代表只用在线可用输入的学生已经可达。完整在线成本和离线构建成本分别计量，具体模型/资源另立协议。本次仅澄清研究范围，未训练或搜索，见[20260908_v3说明](entry_selection_research/20260908_v3/clarification.md)。

最新研究优先级见[论文导向v5报告](entry_selection_research/20260908_v5/report.md)：B共同设计为条件主候选，A与树比较表示，C先做独立有界诊断，D待有效策略后研究标签效率。该判断建立在[Fast根因诊断](fast_router_diagnosis/20260908_v1/report.md)与近期前作碰撞之上；取消anchor/固定3/C8覆盖预设，不先扫HNSW或重做query近邻记忆。优先级不是高原创性背书，也不自动授权实现。当前无待续搜索或训练任务，见[s-target.md](s-target.md)与[v5台账](entry_selection_research/20260908_v5/state.json)；没有新方法GO、理论不可学习结论或原始评估数据访问。

旧 Multi-view 批次按 gate 终止，E2–E4 不是欠账，不续扫 HNSW。已结束的分层搜索夜间版本曾获恢复授权，并按其冻结旧协议通过 P0/P1/P2；P3固定结构与门户诊断已完成但搜索收益gate未通过；门户暴露、目标泛化、实际局部目标尺度诊断及完整23查询trace均已完成。07:00停止核验通过，[实验总结](实验总结.md)已完成并通过文档复核，P4预测模型不启动。

## 6. 不可破坏边界

- 旧 Multi-view 不再运行 E4；新方法须在新协议中完成相应validation/稳定性验收且方法冻结后才执行held-out，不能复用已关闭P6/P7的自动推进授权。
- 冻结 NSG、base、metric、normalization、query split 与 GT 不变。
- 新 artifact 隔离保存并记录 checksum、seed、代码、线程和成本，不覆盖历史结果。
- 三个 views 是一个 ensemble；三个 timing runs 不是三个独立 Recall 样本。
- 任何实验定义或结论变化都同步更新 `spec.md` 与本文件。

## 7. 证据入口

- 实现与复现：`spec.md`
- 当前方案、入口选择流程与下一步：[s-target.md](s-target.md)；其中链接到完整历史快照
- 当前论文导向调研：[v5报告](entry_selection_research/20260908_v5/report.md)、四份专题/独立复核及state；v4树、v2入口组合与v1原指令/state保留历史交付身份
- Fast：`fast_entry_benchmark_results/benchmark_summary.md`
- Three-view：`target_basin_ensemble_diagnostics/v1/decision.json`
- Multi-view 正式化终局：`target_basin_formalization/20260907_v1/{gate.json,report.md}`
- Confidence no-go：`target_basin_meta_diagnostics/v1/decision.json`
- GATE：`gate_baseline_artifacts/webvid2_5m_frozen_r64_v2/analysis.md`
- 历史诊断：`aco_router_fast_entry.md` 与对应 `*_diagnostics/`

### 本次夜间接续（核对于北京时间 2026-09-08 07:10）

**P3 NOPASS，当前无有效端到端性能改善。** P0/P1/P2和P3新增256叶区实现验收通过；P2真实区域保护在双数据集退化，oracle虽有Recall潜力但更慢，因而仅获一次表示修订进入P3。P3训练结构改善没有传递成预定搜索收益：主对照oracle_probability下λ1_greedy3−λ0_greedy3，WebVid L64/128为−0.866/−0.790 pp，两个普通95%区间均为负；Yandex−0.095/−0.017 pp，区间含0。完整数值、CI及证据见[当前研究判断](hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/current_findings.md)和[P3 gate](hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/gates/P3.json)。

三项诊断已完成：所有8格的实际入口集合均改变，排除“新门户没进入实际route”；WebVid pilot的目标集中度有部分传递（top4区域目标比例M4 +1.808 pp），但Recall损失主要来自fit见过的目标，不能全部归因于unseen；Yandex M4变化−0.004 pp。M4不是Recall上界，seen是base目标ID在fit GT10出现，不是查询重叠。实际邻接审计证实两数据集全部fit目标满足d(u)·9Q<M的严格条件；这说明当前目标量级足以让可行的净GT分散改善移动降低J，但不证明该移动存在、实际被选中或导致检索退化。完整限制与独立复核见当前研究判断。

固定23查询trace全部补齐，460条trace/276配对重放通过；原P2 gate保留决策时16条证据，[完成补充](hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p2/trace_completion_addendum_v1.json)说明后续覆盖。8个门户对照的普通95%区间均含0，不证明等效；五轮计时不是五个独立Recall样本。Fast部分frontier计数未测量，不能把占位零当成实测。

P4–P8、validation性能评测和held-out均未启动，没有辅助图触发证据；机制修订计数仍1，不调λ、不重开本版本P3。当时提出的“目标更集中却丢seen命中”方法审查已由文献复审完成；其R0成本优先建议随后被用户指定的入口选择调研方向替代，当前下一项见第1节及新的调研指令。夜间停止时已无研究进程，watchdog已退出；[最终进程核验](hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/control/final_process_verification_v1.json)通过，[实验总结](实验总结.md)已完成并通过文档复核。到时停止不等于长期研究目标完成。

局部尺度的[纯代数补充](hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p3/objective_lexicographic_addendum_v1.md)进一步证明：固定当前状态、考虑的候选与可行性，当前λ1先按整数GT分散变化ΔS、再按切边变化ΔC比较；全部fit目标满足严格界，unseen对所有候选ΔS恒为0。与stay零同分保持原标签，严格改善移动同分才按叶ID。图仍影响候选和同ΔS比较，容量及更新顺序仍重要；这不证明全局最优或Recall退化原因。

输入访问口径澄清：validation未用于拟合/选择或ANN性能评测，但P0已读取其query/GT做文件头、全SHA、查询逐行指纹去重/跨split重叠及finite检查、GT ID范围/行内重复检查；held-out文件未打开。此前笼统的“validation/held-out未读”由此收窄，既有日志保留，详见[P0访问补充](hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p0/validation_access_scope_addendum_v1.json)。

北京时间2026-09-08 03:02已提前关闭本次新实验入口（`control/CLOSED.json`）：P3负结果及有限诊断完成，当前任务进程为零；截止监控保留至07:00，07:00最终停止核验通过，报告已于07:06在截止后创建。期间等待不计作训练/实验时间。

### 截止后交付核验（北京时间 2026-09-08 07:14）

07:00:00.312截止核验及07:01:24独立全进程身份核验均通过，无活跃任务，无终止信号，无截止中断。34个已启动重任务区间无重叠；源码/CMake/settings保护通过，主动删除文件无。见[最终停止](hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/control/final_process_verification_v1.json)、[最终保护与资源](hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/report_preparation/final_protection_resources_v1.md)和[实验总结](实验总结.md)。报告已完成并通过独立复核；研究结论仍P3 NOPASS，长期目标未完成。

[实验总结](实验总结.md)最终独立复核PASS，0项实质/阻断问题，证据见[报告复核](hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/report_preparation/final_report_independent_review_v1.md)。本次有截止的执行与报告交付已完成；长期研究仍未完成，当前P3 NOPASS及后续gate边界不变。
