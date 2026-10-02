from common import *

con=read(O/'results/conclusion.json');assert con['cache_gate']=='STOP_CACHE_UTILITY_GATE'
tt=read(O/'results/report_tables.json');rel=O.relative_to(R).as_posix();prefix='../'+rel

history=f'''# 20 有界训练有效性检查（E31）

2026-09-11完成，状态`TRAINING_EFFECTIVENESS_COMPLETE_OPTIMIZATION_IMPROVED_CACHE_GATE_FAILED`。用户同意一次CPU训练合计10分钟内的优化检查；同一模型、教师、正则和数据固定，若缓存实际收益不达标则停止。结果是优化目标进一步下降，WebVid局部收益增大，Yandex没有有效提升，预设双集缓存门失败。

## 疑点、控制和实现

[E30](19_equivalent_teacher_sets.md)使用Adam.003/80步最后点，初始目标大幅上冲，末段仍下降；这不足以认定bug，也未排除优化余地。E31逐字复制set_loss、triple_scores、归一化共享A、加载与诊断核心，复用最高hits且最低graph NDC的并列G和唯一T0。模型W=normalize(P+AP)、λ100、τ.05、margin.1、A=0、CPU8/float64/fullfit20k/seed20260911不变。

只采用一套预锁优化日程：前20步3e-5→3e-4，至200步保持，之后余弦衰减至1200步3e-6。checkpoint只由fit总目标最低决定，保留最后点作只读敏感性诊断。两集single/multi共4次，从初始化重新训练；不改变老师、模型容量或正则，不按缓存效用挑有利迭代。90个枚举/有限差分及共享A梯度测试通过，旧4个模型独立恢复，新4个选中/最后点共8份NumPy目标与导出核验通过。

## 实际优化和效用

{tt['model_table']}

末段变化小不等于全局收敛，单/多教师目标绝对值不能直接排名。Yandex单教师1199/1200目标仅差约1e-8，离散C8选择仍改变109个query，缓存Recall差0.0100pp；只读检查不更改选点规则。新方案没有出现原第1步的大幅上冲。

{tt['utility_table']}

表中统一float32画像，在已测56个C8完整三元组中选最大分数，再查原真实L128/K10标签。基准为同C8域anchor选择，不是原实际HNSW入口。WebVid multi相对原80步增加0.0910pp（fit配对bootstrap95%区间+0.0455至+0.1340），来自净增182个命中，其中headroom组171；Yandex为−0.0025pp（−0.0185至+0.0110），无有效提升，不是稳定退化证据。

## 阶段门与边界

协议要求同一种cell双集缓存Recall≥anchor+0.20pp、胜原同cell、graph NDC≤+1%，全H已知覆盖≥99.5%且新下界−anchor上界≥+0.20pp。WebVid multi在C8有+0.2115pp，但全H有14个未知query，保守净界+0.1610pp；Yandex全部精确top3已知，依然−0.0040pp。即使忽略WebVid保守界，Yandex也会使双集门失败。状态`STOP_CACHE_UTILITY_GATE`，未进入新fit/cal/audit实际HNSW→NSG或validation/QPS。

已测query上的缓存标签不是新端到端性能；未知组合只是上下界计算，不作为零效用标签。全部query有历史使用，一个H/图/seed/固定λ；无全局最优证书、独立盲测或held-out读取/hash。该结论收口当前固定教师/共享linear/λ100优化支线，不反推所有共享画像不可能有效，也不抹掉GT10既有正信号。

## 成本、结论与证据

4次训练4800更新，训练阶段302.73秒，低于600秒合计上限。新标签0、复用224万逻辑标签；新HNSW查询/原NSG调用/新QPS点均0。E30及原保护链9098个旧文件保持身份，根文档前版本另存source_before。默认保留WebVid GT10 soft/Yandex GT10 hard，依据E30既有完整同批曲线。

后续优先明确原GT10的独立复现与公平基线问题、输入身份和预算；本轮不自动追加训练或held-out。当前下一步见[s-target](../s-target.md)。

- [完整报告]({prefix}/report.md)、[预锁协议]({prefix}/protocol.md)、[缓存门]({prefix}/results/cache_gate.json)、[状态]({prefix}/state.json)。
- [优化与效用图]({prefix}/figures/optimization_and_utility.svg)、[缓存收益图]({prefix}/figures/cache_utility.svg)、[Excel]({prefix}/chart_data.xlsx)。
- [模型恢复/梯度检查]({prefix}/reviews/preflight.json)、[独立模型与缓存核验]({prefix}/reviews/model_and_cache_verification.json)、[停机敏感性]({prefix}/reviews/checkpoint_diagnostics.json)、[最终验收]({prefix}/reviews/final_audit.json)。
'''
hp=R/'experiment_history/20_training_effectiveness.md';assert not hp.exists();hp.write_text(history)
p=R/'s-experiment.md';s=p.read_text();anchor='|---|---|---|---|\n';assert anchor in s
s=s.replace(anchor,anchor+'| E31 有界训练有效性检查 | 同E30教师/模型/λ100，固定优化日程4次×1200步，302.73s；旧/新模型独立恢复、缓存真实标签与全H界 | `TRAINING_EFFECTIVENESS_COMPLETE_OPTIMIZATION_IMPROVED_CACHE_GATE_FAILED`；WebVid有进一步局部收益，Yandex未提升，双集缓存门失败；新NSG/QPS为0 | [20 训练有效性](experiment_history/20_training_effectiveness.md) |\n',1);p.write_text(s)
p=R/'experiment_history/README.md';s=p.read_text();anchor='\n\n## 写入规则';assert anchor in s
s=s.replace(anchor,'\n| [20 训练有效性检查](20_training_effectiveness.md) | E31同目标优化、缓存真实命中与未知界、双集门停止、无新QPS |'+anchor,1);p.write_text(s)
summary=f'''# ACSG 当前实验总结

> 更新至2026-09-11。E31有界训练有效性检查完成，状态`TRAINING_EFFECTIVENESS_COMPLETE_OPTIMIZATION_IMPROVED_CACHE_GATE_FAILED`。架构见[spec](spec.md)，下一步见[s-target](s-target.md)，历史见[s-experiment](s-experiment.md)。

## 当前判断

原E30的80步配置还有优化余地；保持同一模型、教师和λ100，使用固定小步长/衰减训练1200步后，两集目标继续下降。WebVid缓存实际命中有所提高，Yandex仍无有效收益，未达到预设双集缓存门。本次收口这一固定监督/共享画像优化支线，保留WebVid局部信号和原GT10成果。

当前默认仍为WebVid2.5M **GT10 soft**、Yandex10M IP **GT10 hard**，依据[E30完整Recall–QPS与择优]({rel}/../20260911_equivalent_teacher_sets_v1/report.md)。E31没有新HNSW/NSG查询或QPS，训练耗时不用于性能排名。

## 实际优化与缓存结果

{tt['model_table']}

{tt['utility_table']}

缓存指标是float32画像从每query已测的56组三入口中选最大分数，再查原真实L128/K10标签。参考anchor也在相同C8域选择，不是原实际HNSW入口；图NDC不是端到端wall。

WebVid multi相对原80步再增0.0910pp，训练query配对bootstrap95%区间[+0.0455,+0.1340]；相对anchor增0.2115pp。Yandex multi相对原80步−0.0025pp，区间[−0.0185,+0.0110]；相对anchor−0.0040pp，应解读为未观察到提升而非稳定退化。

## 停止位置与结论限制

[缓存门]({rel}/results/cache_gate.json)为`STOP_CACHE_UTILITY_GATE`。两种教师均未满足同一种cell在两集各≥+0.20pp且成本≤+1%的条件；WebVid multi的全H未知14个query另使最坏净界仅+0.1610pp，Yandex全H已知覆盖100%仍无收益。即使放宽WebVid保守界，Yandex也会使双集门失败，因此按预定条件没有进入真实开发/validation补测。

不能把当前缺少双集收益全归因于原80步优化不足；也不能从这一固定教师/共享linear/λ100/seed推断所有学习画像无效。末100步目标变化小没有提供全局收敛证书，离散选择仍可能波动；所选checkpoint仅按fit目标决定，未按效用改选。fit有历史使用，缓存区间不是泛化或新盲测；held-out未读取/hash。E24 GT10和E28 MLP的历史局部信号保留。

## 计量与交付

两集single/multi共4次训练、4800更新，训练阶段302.73s(CPU8)，低于600s合计上限。复用224万逻辑真实标签，新标签0；新NSG调用/HNSW查询/QPS点均0。枚举/有限差分、旧4个模型恢复、新4个选中与最后点共8份数值核验通过。原资产保护与表格/文档验收见[最终审计]({rel}/reviews/final_audit.json)。

- [完整报告]({rel}/report.md)、[优化与效用图]({rel}/figures/optimization_and_utility.svg)、[缓存实际收益图]({rel}/figures/cache_utility.svg)、[Excel]({rel}/chart_data.xlsx)。
- [协议]({rel}/protocol.md)、[checkpoint诊断]({rel}/reviews/checkpoint_diagnostics.json)、[历史20](experiment_history/20_training_effectiveness.md)。
- E30完整旧summary保存在[修改前快照]({rel}/source_before/summary.md)，原全部12方法五L五轮曲线和结果保持原位。
'''
(R/'summary.md').write_text(summary)
target=f'''# ACSG 下一阶段方向与实验接续

2026-09-11。E31训练有效性检查已完成，状态`TRAINING_EFFECTIVENESS_COMPLETE_OPTIMIZATION_IMPROVED_CACHE_GATE_FAILED`。本轮授权的有界验证结束：4次训练合计302.73s，新标签/NSG/QPS均0。[结果报告]({rel}/report.md)、[缓存门]({rel}/results/cache_gate.json)、[历史20](experiment_history/20_training_effectiveness.md)。

## 当前采用和研究收口

默认仍为WebVid GT10 soft、Yandex GT10 hard，以[E30同批曲线]({rel}/../20260911_equivalent_teacher_sets_v1/report.md)为依据。原GT10/E28 MLP局部结果保留。

E31确认原80步有优化余地，额外优化使WebVid缓存Recall相对原multi再增0.0910pp，Yandex没有有效提升。单/多教师都未通过双集缓存门，未继续真实开发或validation。当前固定教师、共享linear、λ100的优化支线收口；没有因为剩余训练预算而追加日程、正则网格或容量。

## 下一阶段优先问题：GT10独立复现与公平比较

优先确认原方法的可复现价值。先复用现有协议和原始曲线，明确当前默认在不同Recall区间、相同线程、相同图/metric/入口数下的证据；将数值领先、局部前沿和稳定提升分开。新的实验要回答一个明确的复现问题，不能将反复使用的历史validation重新称为盲测。

下一份执行协议至少明确：比较的原方法和基线身份；固定图上不同query或独立seed中的哪一项变化；fit/选择/评估拆分；完整单线程端到端wall与Recall的记录；查询/构建/GT依赖和预算；预设共同Recall目标、重复轮次与停止条件。优先采用现有可部署画像和原kernel，训练新画像不是复现默认的先决条件。

这只是接续优先级，下一阶段的复现、基线构建、标签生成、训练或held-out测试均尚未执行。需在下一任务中确定具体实验范围与资源，不从E31或E30剩余预算自行扩大。

## 重新讨论画像学习的证据门槛

若将来提出新目标或新结构，先说明它与E28–E31已完成方案的实质区别、机制预期和最小对照。保留低成本缓存检查的原则；仅当现有教师/候选域能够覆盖所提问题时才复用标签，未知组合不可当零收益负例。任何同L Recall、缓存效用、NDC或训练目标下降都不替代同机独立端到端Recall–QPS前沿证据。

E31的负结果只覆盖当前固定教师/共享linear/λ100/seed和有界日程；没有全局最优证明。WebVid局部缓存改善值得完整保留，但不足以绕过双集推进条件或自动替换部署默认。

## 接续阅读与启动要求

完整读AGENTS→summary→spec→本文件→s-experiment，然后由[历史20](experiment_history/20_training_effectiveness.md)和[历史19](experiment_history/19_equivalent_teacher_sets.md)进入原protocol/state/gate/模型与结果。原E24–E31源码、图、H、GT、labels、模型、日志和报告保留，旧runner拒绝覆盖。

可用接续指令：先核对E31为何停止及WebVid局部正信号，再沿E30完整曲线定位当前默认的适用Recall区间；据现有证据设计最小独立复现协议，列出需要新增的query/seed/GT/构建成本和停止条件。此指令本身不启动训练、ANN或held-out。

所有正式性能继续CPU15/实际进程与OMP线程1，OMP/BLAS/MKL1，一次一个方法，不与训练或重分析并发；计数、GT评分、建图、I/O和hash在plain wall之外。
'''
(R/'s-target.md').write_text(target)
p=R/'spec.md';s=p.read_text();anchor='## 训练有效性检查 v1（E31，2026-09-11，执行中）';assert anchor in s
s=s[:s.index(anchor)]+f'''## 训练有效性检查 v1（E31，2026-09-11，已完成缓存验收）

独立[协议]({rel}/protocol.md)与[训练实现]({rel}/src/train.py)逐字保留E30数学核心、teacher masks和输入，只变Adam日程/1200步上限/fit总目标最小checkpoint规则。两集single/multi各一次，4次4800更新共302.73s，外层进程600s硬限与内层共享deadline同时控制；末点和选中点分别导出A.f64/W.f32。

[preflight]({rel}/src/preflight.py)复核E30旧资产链和原4个A/W目标；原枚举/有限差分与共享归一化A累积梯度测试复用并重新运行。[analyze]({rel}/src/analyze.py)独立NumPy复算4份新模型的选中/最后点，共8个目标/导出，统一float32画像对已测C8组合评分，保存query级slot/hits/NDC、条件已知效用及完整fit的未知组合上下界。G由原hits/NDC重建核验。未知组合不作为零效用标签；仅数学下界允许未知贡献为0。

[checkpoint诊断]({rel}/src/diagnose_checkpoints.py)只读比较选中/最后点的浮点位移和离散入口/缓存命中敏感性，optimizer/NSG调用0，不更改选点。[缓存门]({rel}/results/cache_gate.json)按预锁的双集效用/成本/未知覆盖规则失败，因而本版本没有新HNSW查询、NSG调用或QPS点；未实现或执行新的性能评测器。新增API/产物只涉及离线训练、缓存分析和PNG/SVG/CSV/XLSX报告，不改变线上Policy/kernel/metric。

训练输入和模型各有冻结manifest，全部旧资产/表格/图与文档验收见[final_audit]({rel}/reviews/final_audit.json)。方法结论见summary和[历史20](experiment_history/20_training_effectiveness.md)，实现验收不升级为性能GO。本版本预算收口。
''';p.write_text(s)
(O/'README.md').write_text('''# E31 有界训练有效性检查

已完成，状态`TRAINING_EFFECTIVENESS_COMPLETE_OPTIMIZATION_IMPROVED_CACHE_GATE_FAILED`。固定E30目标、教师和模型，4次×1200步训练302.73s；WebVid缓存有进一步局部收益，Yandex未改善，双集门失败。新NSG/HNSW/QPS均0。

入口：[完整报告](report.md)、[执行前协议](protocol.md)、[缓存门](results/cache_gate.json)、[优化与效用图](figures/optimization_and_utility.svg)、[Excel](chart_data.xlsx)、[最终验收](reviews/final_audit.json)。

全部旧产物保护，原执行目录拒绝覆盖；后续见[根s-target](../../s-target.md)。本次训练耗时不是QPS；原推荐由E30完整性能证据决定。
''')
docs=[hp,R/'s-experiment.md',R/'experiment_history/README.md',R/'summary.md',R/'s-target.md',R/'spec.md',O/'README.md']
dump(O/'reviews/document_update.json',dict(status='PASS',order='history20 then s-experiment/history index then summary/spec/target',files=[identity(x) for x in docs]))
dump(O/'state.json',dict(status='REPORT_AND_DOCS_COMPLETE_AUDIT_PENDING',real_search_calls=0,new_labels=0,heldout_access=False))
print('DOCS_COMPLETE',flush=True)
