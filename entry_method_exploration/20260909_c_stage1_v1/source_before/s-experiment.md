# ACSG 历史实验概览与复盘索引

> 实验记录更新截至2026-09-08，设计索引同步至2026-09-09。`experiment`拼写正确，文件名沿用`s-experiment.md`。本文负责“以前做过什么、结论大概是什么、去哪里详细复盘”，与spec、summary、s-target同在项目根目录。详细记录统一放在[experiment_history/](experiment_history/README.md)，原始产物保留原位置。

**对某个旧实验不确定时，必须进入下表的详细复盘，进一步读原协议、配置、state/gate、结果与后续修正。不能仅凭本概览或记忆判断已经做过、为何失败、是否应该重做。** 当前最近实验结论见[summary.md](summary.md)，下一阶段见[s-target.md](s-target.md)，代码架构合同见[spec.md](spec.md)。

## 1. 已执行的实验与诊断

状态针对具体版本和证据范围。实现验收、诊断信号、依赖准备、方法性能通过分别记录；同L Recall或oracle改善不等于端到端成功。

| ID / 实验家族 | 做过的主要内容 | 当前保留的历史判断 | 详细复盘 |
|---|---|---|---|
| E01 旧NETG/ACO/DPC/Router | 节点权重、hub发现、逐query×hub搜索标签、离线Router；旧Deep/SIFT/Gist/Yandex等报告 | 已使用真实搜索监督；ACO-Max有实现缺陷，旧数据/成本不可直接混入新official-IP协议 | [01 Fast与legacy](experiment_history/01_fast_and_legacy.md) |
| E02 Fast WebVid/Yandex | QGT-Cover＋GT1 basin画像，正式held-out、多seed/timing与逐query对照 | 已有基线结果；WebVid质量收益、Yandex主要归一化QPS收益，完整GT-inclusive构建成本另有缺口 | [01](experiment_history/01_fast_and_legacy.md) |
| E03 LAION迁移 | validation与held-out均完成；修正首轮raw口径后使用unit-IP | 已完成跨base corpus/scale控制；与WebVid共用public query来源，不是独立第三query任务 | [01](experiment_history/01_fast_and_legacy.md) |
| E04 三view早期质量 | 三个build作一个ensemble，固定anchor、三路top8合并 | 同L有小收益，早期阶段GO不是最终方法GO | [02 Multi-view](experiment_history/02_multiview_and_attention.md) |
| E05 Multi-view正式E0/E1/E1b | 路由parity、dense成本、固定后两路Micro-HNSW与等total-NDC对照 | `NO_GO_ROUTING_COST`；E2–E4依gate未跑；旧E0计时证明范围后来收窄 | [02](experiment_history/02_multiview_and_attention.md) |
| E06 confidence attention | 按置信度调整view权重，检验共享alpha | 两数据集偏好相反；当前共享公式NO_GO，不是否定全部attention | [02](experiment_history/02_multiview_and_attention.md) |
| E07 sparse utility ranker | Fast32候选、真实Recall/NDC、soft labels与交互打分 | 局部小正信号未形成跨数据集成本收益，停止该模型路线 | [04 效用与表示](experiment_history/04_utility_and_representation.md) |
| E08 search-aware centroid | WebVid5K全815入口真实标签，按赢家重新聚合画像 | 有局部同L Recall提升，未证同成本/跨数据收益；不能称未用过真实效用监督 | [04](experiment_history/04_utility_and_representation.md) |
| E09 utility residual | signed utility残差修正原prototype | WebVid微弱正收益，缺双数据/完整成本验证；不写成已证跨数据失败或方法GO | [04](experiment_history/04_utility_and_representation.md) |
| E10 residual basin modes | v1多模式与v2 anchored校正两轮 | 分别保留机制/成本/结果边界，未形成稳定改进；不是confidence或Multi-view同一实验 | [04](experiment_history/04_utility_and_representation.md) |
| E11 BTG v1–v4 | raw-topology/BFS转移与多版纠偏、跨数据效用检验 | 静态拓扑扩散路线NO_GO；各版修正与局部正值不丢失 | [04](experiment_history/04_utility_and_representation.md) |
| E12 原existing-hub oracle | 旧WebVid validation1K，全H single及独立命中并集组合代理 | 确认候选内有空间；免费oracle/并集不是部署点或真实最优联合搜索 | [05 Oracle与reroute](experiment_history/05_probe_reroute.md) |
| E13 paid probe失败检测 | 只支付L10，识别可能从改道受益的query | 风险检测有增量信息；早期L10/16/32却只收费L10的版本无效 | [05](experiment_history/05_probe_reroute.md) |
| E14 restart/merged rerouter | 候选32、merged Recall/NDC、trace/frontier/topology选择器 | 替代入口选择失败；不能把已用监督误记为独立single或仅几何标签 | [05](experiment_history/05_probe_reroute.md) |
| E15 finite-beam v1与审计 | GT-free trace的增量信息、成本和收益集中性 | 正式解释为信息增量通过、成本对齐失败；旧“没有增量”判定被纠正 | [06 finite-beam/Atlas](experiment_history/06_finite_beam_and_atlas.md) |
| E16 v2 cost-first distillation/Atlas | 64-query近邻搬运top8真实效用，在线不probe | 四点utility差区间跨0；不能据此否定任意重教师到轻模型蒸馏 | [06](experiment_history/06_finite_beam_and_atlas.md) |
| E17 GATE同图适配 | WebVid原图上的作者方法受限适配；无效HBKM版本另存 | 本地适配未胜Fast，Yandex扩展未跑；不等于论文全方法被证伪 | [03 基线](experiment_history/03_baselines.md) |
| E18 分层P2 | 64区域、门户与统一/均匀/概率候选池、有限oracle | 真实区域保护退化；oracle有质量但更慢，仅机制门槛允许一次P3修订 | [07 层次P2/P3](experiment_history/07_hierarchical_p2_p3.md) |
| E19 分层P3及诊断 | 16×16结构/768门户；门户暴露、seen/unseen、局部尺度、23trace补齐 | P3搜索收益NOPASS；诊断完成，P4–P8未跑；停止不等于长期研究完成 | [07](experiment_history/07_hierarchical_p2_p3.md) |
| E20 Fast根因诊断 | 两数据集各512pilot、全H single/C8 pair-triple、最近fit/随机控制 | 实现检查通过；几何代理缺口、短名单损失，撤下固定anchor/3；未证一般不可学习 | [08 Fast诊断](experiment_history/08_fast_router_diagnosis.md) |

## 2. 准备与设计：不能计作方法实验

| 记录 | 已完成 | 尚未执行/不能声称 | 详细入口 |
|---|---|---|---|
| 比较依赖准备 | METIS/GKlib、独立Python、gp-ann/MIPS、RoarGraph、局部MKL与smoke | 依赖就绪不是RoarGraph/kRt/LIRA等正式同机结果 | [03 基线与环境](experiment_history/03_baselines.md) |
| 文献复审R0–R2 | 原文/代码/本地假设复核与筛查建议 | R0–R2未执行且已被后续方向替代 | [09 设计记录](experiment_history/09_research_designs_not_experiments.md) |
| 入口v1/v2 | 指令、相关工作、C8固定anchor三入口/40维草案 | 未训练该模型；相关默认限制被E20撤下 | [09](experiment_history/09_research_designs_not_experiments.md) |
| v3离线重/在线轻 | 澄清训练与推理成本边界 | 没有新标签/模型/实验 | [09](experiment_history/09_research_designs_not_experiments.md) |
| v4效用树 | 原生搜索收益/多叶同hub的树设计与gate | 尚未实现训练器、未生成完整20K×H标签、无性能GO | [09](experiment_history/09_research_designs_not_experiments.md) |
| v5四方向 | 近期前作、机制/成本/风险与独立复核 | A/B/C/D均未实施；A+B及C后来分别完成更细R0，仍无方法实验 | [09](experiment_history/09_research_designs_not_experiments.md) |
| A/B独立R0与联合理论 | A、B分别完成组件碰撞审计和未执行协议；随后按用户意见改用方法层原创性标准，形成fixed-M、Fast可恢复的flat slot/action联合理论 | 两个独立R0均未运行并作为历史保留；A+B联合版只完成理论重述，未实现、未训练、未搜索 | [09](experiment_history/09_research_designs_not_experiments.md) |
| C独立R0 | 补查QING/ANNiE等最近前作，核对E13–E16与当前kernel，冻结同状态有限动作、state×reuse析因和A+B条件接口 | 只允许未来另批有界oracle/learnability kill-screen；未实现状态机、未生成标签、未训练、未搜索，也未形成A+B联动GO | [09](experiment_history/09_research_designs_not_experiments.md) |

## 3. 容易误读的版本与证据

- finite-beam v1以`v1_audit`纠正后的状态为正式解释；原decision保留但不单独作为最终判断。
- Fast诊断正式引用`analysis/v2`和`costs_v2.json`；v1保留其统计/事件计时修正过程。
- P2原gate是在16条trace时作出的，后续按原名单补齐23条；两件事分别记录，不能覆写当时gate或说trace仍欠7条。
- 分层夜间P0读取validation字节作完整性检查，未作方法性能评测；Fast根因诊断未打开原始validation/held-out。不同分支使用历史必须逐条查，不能说全项目从未用过validation。
- 原`实验总结.md`是分层夜间报告，原`总结.md`是早期NETG评审记录，`aco_router_fast_entry.md`是Fast转向复盘；都保留原名与内容，通过01/07追溯，不与当前`summary.md`抢职责。
- 旧文件中的待执行/GO/当前计划和spec章节号属于当时版本；当前目标以`s-target.md`为准。历史失败只约束已测试机制与设置，不能扩为数学不可能，也不能换名绕过证据。

## 4. 后续维护

新增实验或停止阶段时，先在`experiment_history/`新增或扩充对应详细卡片，保存协议/输入身份、实际配置/命令、主要结果、成本/未知项、停止理由及原证据索引，再在本表登记。必要的更正保留前后版本；概览不抹平局部正信号、未执行部分或数据口径差异。

当前根四文件、九份详细卡片和原证据形成“概览→复盘→原件”链。目录说明与卡片要求见[README](experiment_history/README.md)；本次文档整理的旧版本、保护与审查保存在[_maintenance](experiment_history/_maintenance/20260908_document_reorganization/)。
