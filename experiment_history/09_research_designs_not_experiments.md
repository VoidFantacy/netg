# 09｜已完成研究设计与未执行提案

核对日期：2026-09-10。本页用于防止把“调研完成、依赖就绪、写了协议”误认为做过方法实验。以下设计版本保留其原state和交付身份；当时的推荐、预算和未执行命令不覆盖当前[s-target.md](../s-target.md)。本页记录设计版本，原件不变；2026-09-09另行授权执行的C stage1是[E21真实实验](10_c_state_intervention.md)，不能把其结果回写成旧R0已经运行。

2026-09-09 E21停止后，用户曾将A+B列为下一阶段主线；当次仅更新文档与研究优先级，尚无A+B执行。随后另行授权的实现及评测分别记为E22/E23，不能把本页旧设计的未运行身份解释成全项目今天仍未运行。联合R0与C stage1的原state、manifest和交付快照保留当时身份，当前安排见[s-target.md](../s-target.md)。

## 1. 文献复审与入口研究版本

| 版本 | 当时完成了什么 | 当时建议/机制 | 实际未做什么与后续变化 |
|---|---|---|---|
| [research_direction_review/20260908_v1](../research_direction_review/20260908_v1/report.md) | 对P2/P3假设与近期论文作原文/源码审查，保存14篇核心核对和独立审查 | R0–R2成本优先筛查、基线可比性、固定P2表示下搜索过程检查 | 未实施R0–R2；后来被用户指定的入口研究替代，不能把它列为欠跑实验 |
| [入口v1](../entry_selection_research/20260908_v1/direction.md) | 固定研究方向、下一对话提示、保护快照；原state为`DIRECTION_SET_RESEARCH_PENDING` | 调研候选池/排序/少量入口组合 | 原pending是该交付时状态；后续调研已完成，不是仍需从头执行v1 |
| [入口v2](../entry_selection_research/20260908_v2/report.md) | 一手文献/作者实现与本地失败审查、recommendation/minimum_gate/protocol_draft | C8内含anchor的固定三入口与40维联合选择器草案 | 40维模型未实现未训练；anchor/固定3/C8充分假设后来被真实Fast诊断撤下 |
| [范围澄清v3](../entry_selection_research/20260908_v3/clarification.md) | 用户明确离线可重、在线要轻；同步研究边界 | 允许重模型、复杂监督和离线预计算，不强制轻训练或teacher/student | 没有生成新标签/模型/结果；不是一次学习实验 |
| [效用树v4](../entry_selection_research/20260908_v4/report.md) | TAO/成本敏感树、旧NETG/ranker/Atlas一手审计；method/minimum_gate与独立复核 | 全H真实Recall、允许多叶同hub、单路径query树；重参照分别审计 | 没有树训练器/重模型/新72.14M标签或部署点；当前保留为共同基线 |
| [论文方向v5](../entry_selection_research/20260908_v5/report.md) | 四专题、近期前作碰撞、成本与方法审查、保护校验 | A多面、B入口发现与路由共同设计、C同状态干预、D成对标注 | v5原版四条都未实现未运行；没有高原创性或性能GO证明；当时计划先细评B/A/C，后续C stage1执行及A+B主线调整分别见E21和本页接续记录 |
| [B独立R0](../entry_method_exploration/20260909_b_r0_v1/README.md) | 对H外64列、fixed-m、受限tree selector-aware swap作组件碰撞审计和未执行pilot草案 | 当时因组件前作与论文优先级关闭该具体v1 | 未生成候选、标签、模型或搜索结果；关闭不是性能否证，当前只作历史版本 |
| [A独立R0](../entry_method_exploration/20260909_a_r0_v1/README.md) | 对per-hub多facet、regret增删、flat MIPS作组件碰撞审计和未执行协议 | 当时给出“关闭或接受低原创性systems诊断”的二选一 | 用户后来认为该整体原创性标准过严；v1未运行，其组件前作继续作为强对照 |
| [A+B联合R0](../entry_method_exploration/20260909_ab_joint_r0_v1/README.md) | 按方法层原创性重构为fixed `M=|H|`、Fast可恢复的flat slot/action codebook；定义many-to-one映射、受限affine、两类误差分解和2×2 gate | 先在现有H内共同设计可路由分区与入口语义，H外发现后置 | 只完成理论重述；没有protocol lock、实现、标签、训练、搜索、validation或held-out |
| [C独立R0](../entry_method_exploration/20260909_c_r0_v1/README.md) | 补查QING/ANNiE等前作，复核E13–E16和源码；定义完整state、一次force-expand、共同剩余graph-NDC cap与逐支实际成本、state×reuse析因及A+B接口 | 只保留有界的state-machine parity→有限动作oracle→learnability否决路径；不并入A+B主线 | 本R0没有新kernel、checkpoint、标签、模型、搜索、validation或held-out；随后独立stage1执行C0–C2，C1通过/C2实质门停止，见[10](10_c_state_intervention.md)；无方法/联动GO |

v2/v4/v5最终状态为`RESEARCH_COMPLETE_DESIGN_ONLY`，含义是调研与设计交付完成。真实Fast根因诊断发生在其中，独立记录于[08](08_fast_router_diagnosis.md)，不能因其执行过2.77M搜索就说v2或v4方法已经训练。

## 2. 必须保留的设计纠正

- v2固定anchor与固定三个入口不再是当前默认；原因来自08真实组合诊断，不是单纯偏好变化。旧预算3M/4h属于该草案，不自动成为新方向的通用额度。
- v4不是“重教师成功才准训练树”：query-only重参照与树分别拟合、分别判断，教师失败不能否决成功的树，教师也不是理论上界。树直接优化真实效用，不必复制教师唯一ID。
- v4的全H为815/821个可选动作，不保证深度/最少叶支持约束下最终叶动作覆盖全部H。20K与最少叶32会限制叶数；多叶同hub也会消耗容量。
- v5已将普通主动/低秩Atlas、多原型+MIPS、仅旧H压池等宽泛表述降级；相近前作的存在和限定查新范围均保留，不将“没搜到同名论文”写成首次。
- 2026-09-09的原创性标准更正：组成部件已有不构成整体方法NO-GO。A+B可以把新的ANN问题定义、固定容量约束耦合、专门优化和端到端部署闭环作为方法／系统原创性候选；但仍须明确承认各组件前作，未完成广泛查新和实证前不称“首次”。GATE同样大量复用既有表示与图技术，不能用比外部基线更苛刻的逐组件首次标准评估本项目。
- 本地v4效用树已经允许多叶映射同一hub、按真实finite-L效用更新分区和叶动作，因此A+B不能把“多区域同入口”或“真实效用联合分区/动作”本身称新。当前候选边界限定为fixed-M flat codebook、Fast identity可恢复、显式slot/action factorization、共享受限metric adapter及micro-IP部署。
- A+B第一阶段令`C=H`、`M=|H|`并允许多个slot映射同一真实入口；H外候选只在existing-H exact联合门通过且覆盖损失仍主导后再开启。它不是重启B v1的H外64列/tree-swap pilot，也不是把A v1原协议照搬过来。
- C的旧参考不是只学standalone Recall。05表明旧chooser已有merged Recall/NDC与state特征；其中最终v4只在WebVid运行，Yandex最终扩展未运行。同完整state、同一预登记剩余graph-NDC cap并逐支记录实际成本的原位干预，是R0当时尚未测试的差别；现已由[E21](10_c_state_intervention.md)补齐C1/C2，当前冻结配置按实质门停止。
- C的宽泛“搜索中加入口并继续”也不是新机制：QING 2012已在保留的priority queue、result heap与visited/color历史中按停滞加入新pivot；ANNiE、LAET、DARTH和Ada-ef又覆盖live-state预算／停止控制。当前只保留candidate-specific `continue/force-expand`成对动作值、共同剩余graph-NDC cap与逐支实际成本这一窄组合，定向查新不支持“首次”主张。
- 当前`SearchTrace`只有终态汇总，`retset_buf`会被重置，游标／有效长度位于调用栈，visited也不等于expanded；因此R0要求C新增独立state-machine并先做pause/clone/no-op/resume parity（现由新stage1完成，见10），不能从E13–E16旧产物回放checkpoint或用`RegionalSearch`冒充原kernel。
- A+B的独立single效用`u_L(q,e)`不能充当C的状态条件增量；若两者以后都通过，必须先冻结deployed A+B，在其诱导状态上重新标注，再做`{Fast,AB}×{off,C}`。组合胜出不等于正交互，未证协同就保持模块叙事。
- D是离线效率支线，最终模型不变时不自动加速在线。2nD只覆盖分支成对标注，叶新动作发现最坏仍为nH，不能声称整套标签复杂度必然降为2nD。

## 3. 预算是草案，不是已经支付或预计耗时

v4及A+B完整方案若都采用每数据集20K fit＋1024校准＋1024审计、两个L、H815/821，则逻辑上为72,141,056次完整标签搜索，其中fit65,440,000次。没有实际运行这批标签；旧512诊断不能作为完整矩阵。搜索4h/拟合8h是旧版本预算上限，不是新A+B已批准预算或估算训练时长。

v5 D的25% fit点为16,360,000次，加完整开发至少23,061,056次，再计采样/训练/对照。B增加64入口列，在20K两L下每数据集每轮增加2.56M调用。A的facet内存/MAC只是算术；C的后缀分支次数不能按完整search估价。这些数字用于方案比较，不是新性能结果。

## 4. 原件与详细复盘入口

- R0–R2：[综合报告](../research_direction_review/20260908_v1/report.md)、[本地假设审计](../research_direction_review/20260908_v1/reviews/local_hypothesis_audit.md)。
- v1：[原对话提示](../entry_selection_research/20260908_v1/next_dialogue_prompt.md)、[原state](../entry_selection_research/20260908_v1/state.json)。
- v2：[推荐](../entry_selection_research/20260908_v2/recommendation.md)、[最小gate](../entry_selection_research/20260908_v2/minimum_gate.md)、[state](../entry_selection_research/20260908_v2/state.json)。
- v3：[范围澄清](../entry_selection_research/20260908_v3/clarification.md)、[state](../entry_selection_research/20260908_v3/state.json)。
- v4：[方法定义](../entry_selection_research/20260908_v4/method.md)、[最小gate](../entry_selection_research/20260908_v4/minimum_gate.md)、[本地失败审计](../entry_selection_research/20260908_v4/reviews/local_failure_audit.md)、[state](../entry_selection_research/20260908_v4/state.json)。
- v5：[B专题](../entry_selection_research/20260908_v5/reviews/joint_entry_design.md)、[A专题](../entry_selection_research/20260908_v5/reviews/utility_representation.md)、[C专题](../entry_selection_research/20260908_v5/reviews/adaptive_intervention.md)、[D专题](../entry_selection_research/20260908_v5/reviews/active_supervision.md)、[方法审查](../entry_selection_research/20260908_v5/reviews/independent_method_review.md)、[成本审查](../entry_selection_research/20260908_v5/reviews/independent_cost_review.md)、[state](../entry_selection_research/20260908_v5/state.json)。
- A/B R0：[B独立评估](../entry_method_exploration/20260909_b_r0_v1/assessment/assessment.md)、[A独立评估](../entry_method_exploration/20260909_a_r0_v1/assessment/assessment.md)、[当前联合理论](../entry_method_exploration/20260909_ab_joint_r0_v1/theory.md)及其[state](../entry_method_exploration/20260909_ab_joint_r0_v1/state.json)。
- C R0：[当前评估](../entry_method_exploration/20260909_c_r0_v1/assessment.md)、[state](../entry_method_exploration/20260909_c_r0_v1/state.json)与其继承的[v5专题](../entry_selection_research/20260908_v5/reviews/adaptive_intervention.md)。

原版本sources和manifest固定当时取得的一手材料，不代表代码被安装或执行。旧delivery_manifest内当时主文档的SHA属于该次交付快照；本次重新分工后根文件SHA会改变，而旧版本文件及清单保持不变。

## 5. 2026-09-10：E23后四问题调研

用户询问聚类代表是否直接GT1/需连通性、OOD聚类替代、rank8是否最优，以及HNSW能否拉伸。独立版本[20260910_ood_hubs_clustering_router_research_v1](../entry_method_exploration/20260910_ood_hubs_clustering_router_research_v1/README.md)完成当前源码、manifest、E20原诊断/E23结果与一手论文核对；状态`RESEARCH_COMPLETE_METHOD_UNSELECTED_UNRUN`。

源码澄清：QGT先对5K query作球面聚类，再从靠近质心的成员query的GT100中取第一个全局未用真实节点，不是直接求质心GT1；20K/30K画像阶段另用GT1到raw hub的cosine硬归属及query向量之和。E23在线索引的是学习后的画像，主图仍为冻结NSG。

本次重新提取旧汇总：E20 L128单入口GT1-basin对全H免费oracle，WebVid为75.605%对85.957%，Yandex为91.758%对96.563%；仅说明现有H内有遗漏效用。E23 audit1024的Fast20K精确画像top3比HNSW最终Recall仅高0.283/0.078pp，Yandex Full反而低0.098pp；精确画像分数不是实际入口效用oracle，诊断QPS为null。rank8只与Full比较过，尚无rank4/16/32选择证据。

建议保留H先定义GT-topK软画像；较重备选为真实有限L效用分组/挑代表；效率支线为对画像和query施加互逆转置变换，保持分数后重建微型图。变换与query感知构图有LeanVec-Sphering/RoarGraph等相关前作，迁移到本项目未执行，也未作首次性或性能GO结论。vMF/平衡聚类只作实现候选，静态度数不替代finite-beam作用；原BTG/centroid/rerouter历史不被改名忽略。

证据：[完整报告](../entry_method_exploration/20260910_ood_hubs_clustering_router_research_v1/report.md)、[14项阅读记录及访问限制](../entry_method_exploration/20260910_ood_hubs_clustering_router_research_v1/papers.md)、[旧结果提取与hash](../entry_method_exploration/20260910_ood_hubs_clustering_router_research_v1/local_evidence.json)。没有新聚类、标签、训练、索引或评测；E23仍为最近真实实验，后续方法与协议尚未选定。

### 后续文档交接：固定H的GT-topK软画像优先

用户在上述调研交付后指示“同步文档，把下一步的实验方向写到s-target，方便我启动新对话进行实验”。本次已在[s-target.md](../s-target.md)集中写明优先方向、GT1/GT10×硬/软归属的小型消融建议、fit/cal/audit身份、matched Fast对照、单线程端到端计时、分阶段产物与停止边界，以及可复制的新对话启动指令。新的接续状态为`NEXT_EXPERIMENT_DIRECTION_DEFINED_UNRUN`；协议数值与调用预算在新对话启动时冻结。

方向2真实finite-L效用分组/挑入口、方向3保分数拉伸微型图，以及目标稳定后的rank容量比较仍是后续备选，不自动形成串行实验队列。首轮闭式画像不需要重跑E22 single或E23联合训练标签；已有准备器会生成组合，不能整段重跑冒充轻量输入准备。

仅修改当前交接和索引，spec已实现合同、四问题研究原件及E23原结果保留；本次没有新的训练、ANN或查询实验。更新前文档快照与检查存于[_maintenance/20260910_gt_topk_handoff](./_maintenance/20260910_gt_topk_handoff/README.md)。

用户接着要求“下一步的实验方向可以写详细一点，刚刚我们讨论的分完优先级都写上去”。因此再次扩充s-target第4节，保留上述优先主线，同时详细记录2A现有H真实效用分组、2B固定预算GT候选挑入口、连通特征对照及条件三入口整组评分；3A保分数成对拉伸、3B查询感知微型图边、3C独立NSG主图研究；另列球面/vMF/目标关系聚类、rank4/8/16/32与Full、Yandex范数归属消融。每项明确问题证据、方法候选、必要对照、成本/标签依赖、进入和收口依据，并增加按结果选下一方向的表格及分支启动指令。首轮默认仍是固定H的GT-topK软画像，不将所有方向自动串行运行。

此次详细化没有改变已实现架构或实验结果，也没有锁定或启动这些分支的运行协议；新文档快照和检查见[_maintenance/20260910_prioritized_experiment_handoff](./_maintenance/20260910_prioritized_experiment_handoff/README.md)。
