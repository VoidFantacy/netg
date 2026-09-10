# ACSG 当前研究方案：论文导向的入口方法候选

> 2026-09-08。`RESEARCH_COMPLETE_DESIGN_ONLY`。完成四条候选与效用树的论文导向比较；B联合入口发现为条件性主候选，A与树检验表示，C为高风险备选，D为离线效率支线。原创性尚未证实，无新实现、训练、性能GO或待续实验进程。

## 当前证据

本文件统一记录“现在做什么、下一步是什么”；实现与复现契约见[spec.md](spec.md)第18–21节，研究结论见[summary.md](summary.md)。

- 当前[论文方向报告v5](entry_selection_research/20260908_v5/report.md)，四专题[A多面表示](entry_selection_research/20260908_v5/reviews/utility_representation.md)、[B联合入口发现](entry_selection_research/20260908_v5/reviews/joint_entry_design.md)、[C原位干预](entry_selection_research/20260908_v5/reviews/adaptive_intervention.md)、[D成对标注](entry_selection_research/20260908_v5/reviews/active_supervision.md)。
- 共同基线[v4树方法](entry_selection_research/20260908_v4/method.md)与[最小gate草案](entry_selection_research/20260908_v4/minimum_gate.md)仍未实现未运行；其本地失败/图入口/策略树前作审计保留。

- [根因报告](fast_router_diagnosis/20260908_v1/report.md)：六个诊断问题、数值、理论边界与决策。
- [32项完整统计](fast_router_diagnosis/20260908_v1/analysis/v2/analysis.md)、[机器可读结果](fast_router_diagnosis/20260908_v1/analysis/v2/analysis.json)、[执行台账](fast_router_diagnosis/20260908_v1/state.json)。
- [冻结协议](fast_router_diagnosis/20260908_v1/protocol.md)、[复现说明](fast_router_diagnosis/20260908_v1/README.md)、[独立执行审计](fast_router_diagnosis/20260908_v1/reviews/independent_execution_audit.md)、[独立统计复核](fast_router_diagnosis/20260908_v1/reviews/independent_analysis_review.md)。

两数据集同20K paired Fast、原NSG/raw-IP，各512历史pilot，全H单入口及C8全部pair/triple、最近fit/随机fit控制，共2,770,770次搜索。输入、画像逐字节复算、真实执行与独立分析均通过。仅新版本内增加诊断工具/副本/结果，方法源码和历史产物保护；原始validation/held-out未访问。

| 诊断问题 | 实际发现 | 当前判断 |
|---|---|---|
| 是否实现错了 | 图/base/ID/画像一致，count/plain/repeat及真实入口消费通过 | 检查项内没有发现实现错误，不能扩大成整个算法无缺陷证明 |
| HNSW近似是主因吗 | exact3相对Fast3变化WebVid+0.35/+0.63 pp，Yandex−0.45/−0.31 pp | 效果小、方向不一致，不先扫HNSW补主要缺口 |
| 几何标签代表好入口吗 | 即使直接知道GT1 basin，全H最佳single仍高4.80–13.07 pp | 当前监督代理不等于真实搜索效用；单均值、多模态、prior等尚未分别干预 |
| C8够用吗 | 全H最佳single仍比exact C8最佳single高3.16–6.66 pp | 短名单内外均有损失，不能默认完美C8重排足以解决 |
| 固定anchor/三入口合理吗 | anchor限制损失0.84–3.11 pp；四点C8最佳single平均均略高于最佳triple | 撤下两个默认限制；oracle未证明single部署最优 |
| 理论上不可学习吗 | 四个最近fit−随机fit主区间均跨0；跨L A0仍有92.19%/96.09%相交 | 当前简单近邻信号不稳定，既无普遍不可学习证明，也无廉价可预测性GO |

所有表中差值限定当前H、给定L、Recall@10和动作家族。同L不等于同NDC/同wall；oracle使用目标标签、免费选择。32项区间来自历史pilot配对bootstrap近似，不能代替三独立构建或正式held-out。

## 当前研究优先级

**离线可以重，在线预测要轻。** 近期原论文/作者实现核查后，不把“真实效用、重模型、多原型、主动采样、自适应”本身当新贡献。四方向独立评价，不自动拼成一个复杂系统：

| 方向 | 必须验证的新机制 | 当前定位 |
|---|---|---|
| B：入口发现与受限路由共同设计 | 发现旧H外真实入口，按fit内部交叉折上轻路由实际收益接受交换；同C/m/F/标签预算胜coverage-only | 论文导向的条件性主候选，旧H内压池只算v4变体 |
| A：真实遗憾驱动多面入口索引 | 在同总面数下，真实误选冲突增删面优于普通maxout/几何多原型，并保留微索引后的收益 | 表示备选，与树做强对照；非高原创背书 |
| C：同完整搜索状态的一次入口干预 | 同剩余工作预算的continue/inject直接增量可预测，状态复用和预测收益分别归因 | 高风险备选，改变kernel合同；旧chooser失败仍有效 |
| D：策略修改驱动成对标注 | 同策略容量下减少真正必需的query×entry标注，并计全H叶动作发现成本 | 离线效率支线，不单凭省标签宣布在线GO |

现有v4效用树作为共同基线：原NSG/raw-IP、K10、各L单独训练，query-only单路径、多叶可选同hub，主目标真实Recall，NDC仅累计Recall同分次序；最多10次线性分支直接取得真实base ID。重参照与树分别审计，教师不是上界，也不否决质量成功的树。其TAO/成本敏感优化是已有工具，任务适配原创性较弱，但易做可解释的成本对照。

## 下一步证伪顺序（研究建议，未授权执行）

1. 选择单一候选另立执行版本，冻结fit/calibration/audit、动作/模型族、统计与预算。沿用后20K fit、前10K历史开发池的草案时，排除已诊断512不使剩余query成为新鲜测试集；原始validation/held-out保持关闭。
2. 论文优先时，先给B一个有限且含H外节点的候选母集，比较同路由容量下的覆盖损失与实际路由损失。若只提高oracle或不胜coverage-only，否决当前共同设计机制，不追加入口/模型扫参。
3. 快速判断表示时，A与v4树共享合法全H标签，比较精确多面评分、普通maxout与真实regret增删，再支付微索引成本。若只比Fast均值好、但不胜普通监督多原型，降为组件对照，不写高原创叙事。
4. C必须先做独立kernel no-op/count/plain验收，然后一次检查点/有限备选的原位oracle和可预测性门槛；旧方法已用merged效用和state特征，不能以重启改继续推断学习成功。D待有效策略后研究25%fit标注点，叶动作发现/开发/训练总成本均收费。
5. 质量通过后再进入完整纯wall，比较Fast1/Fast3、效用树与强基线；双数据集、相邻工作点、三独立构建、尾部及方法冻结后的held-out10K×3要求保留。

v4全监督成本示例为72,141,056次标签搜索，其中fit65.44M、开发6.701056M。D的25%fit加完整开发至少23.061056M；B每轮新64入口在20K、两L下每数据集增加2.56M；C剩余分支不能按完整调用次数估价。v4的搜索4h/拟合8h是历史草案预算，不是新候选ETA或自动预算。本次没有可直接接续执行的新命令。

## 保留边界

[完整v5报告](entry_selection_research/20260908_v5/report.md)是本轮结论与证据入口；三份交接修改前快照在[v5/source_before](entry_selection_research/20260908_v5/source_before)。v4树、v2固定anchor/三入口/40维设计、诊断及v1指令/state保留历史身份，不覆盖当前优先级。

旧R0–R2、P3 NOPASS、Multi-view成本NO-GO、probe-reroute和夜间state/gate/CLOSED不恢复。A/B/D以冻结原kernel为边界，C只在本轮作为独立搜索过程候选评价，未解除旧分支禁止resumable实现的停止规则。base/图/metric/kernel变化按spec联动重建；仅变入口时旧身份相同的single列可映射复用，新列补测，模型/路由/下游重建，保留旧产物。本次调研完成不等于长期方法目标完成。
