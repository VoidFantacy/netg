from write_report import *

def main():
    t=read(O/'results/analysis_tables.json')
    conclusion=read(O/'results/conclusion.json')
    gate=read(O/'results/performance_gate.json')['methods']
    output=read(O/'reviews/output_verification.json')
    relative='entry_method_exploration/'+O.name
    summary_table=table(['数据集','L']+[cell+' ΔRpp / ΔQPS' for cell in CELLS],[
        [SHORT[ds],L]+[num(next(r for r in t['differences'] if r['dataset']==SHORT[ds] and r['stage']=='validation' and r['L']==L and r['method']==cell)['delta_recall_pp'],3,True)+' / '+num(next(r for r in t['differences'] if r['dataset']==SHORT[ds] and r['stage']=='validation' and r['L']==L and r['method']==cell)['delta_qps_pct'],2,True)+'%' for cell in CELLS]
        for ds in DS for L in [64,128,256,400,800]])
    gate_table=table(['数据集','方法','预设点覆盖','插值QPS几何均变'],[
        [d['dataset'],g['method'],d['covered_targets'],num(d['geometric_mean_qps_change_pct'],2,True)+'%'] for g in gate for d in g['datasets']])
    train=read(O/'models/training_runs.json')
    fit_table=table(['数据集','模型','fit L128 ΔRecall pp','fit Δgraph NDC'],[
        [r['dataset'],r['method'],num(r['delta_recall_pp'],3,True),num(r['delta_graph_ndc_pct'],2,True)+'%']
        for r in t['differences'] if r['stage']=='fit'])
    recommendation=conclusion.get('recommendation','保留原已冻结GT10路线；新四格的局部正负分别保留，不将拟合改善直接写成检索优势。')
    # Archive first, then update index, then current-summary/next-goal documents.
    h=R/'experiment_history/18_teacher_objective_alignment.md'
    assert not h.exists()
    h.write_text('\n\n'.join([
        '# 18 教师标签与训练目标对齐（E29）',
        f"2026-09-11完成，状态`{conclusion['status']}`。{conclusion['verdict']} {recommendation}",
        '## 问题与实质对照',
        f'延续[E28](17_gt10_shared_transform.md)的集合CE下降但教师入口重合下降现象。新版本[{O.name}](../{relative}/report.md)固定原GT10 hard、H、共享linear/λ100/80epoch，只做教师与损失的2×2。cost教师为原C8 maxhits/minNDC选优；keep在无额外hits空间时保留原GT10实际HNSW三入口。CE与结构化top3 margin各自作用分开，原cost_ce逐位恢复E28linear100。',
        '在线raw query→一次microHNSW top3→三个真实hub→原NSG，不加query塔或重排。margin上界教师漏选成员错误，不上界NSG Recall损失；多个等效好集合仍被压成一个教师，固定λ下两目标的实际漂移并不相同。',
        '## 执行与冻结',
        '两集fit20k复用224万真实三元组标签，全部独立ID→GT评分，新标注0。两教师命中上界相同，但keep放弃一部分成本改道；新教师不能部署。8份模型在新开发query前全部冻结，无超参/epoch选择。完整fit20k、cal1024、audit1024做真实检索，audit另有L128exact诊断；validation2000×11方法×5L=110正式点，各3次完整warm/plain单线程wall。',
        '## 完整结果',
        '以下同批相对GT10 hard，R为百分点，QPS为同L三轮中位数比；不是等Recall加速。',summary_table,
        '预设WebVid75/80/85%、Yandex90/95/98%的Recall–logQPS插值描述，不外推、不计为新增实测点：',gate_table,
        '## 机制与局限',fit_table,
        '两因素的实际Recall主效应和交互、正负query、完整训练及有/无候选命中空间组均保留。margin可以改善教师入口拟合，但实际fit、cal、audit、validation并不因此自动一致提高；原T1保留的是实际HNSW集合，与原画像精确top3存在差异。只读梯度/漂移方向诊断不是因果性能控制。',
        '本轮只有共享linear/固定margin与正则/80轮/一个图和H；无收敛证书、无漂移匹配新搜索控制。所有fit/cal/audit/validation均有历史使用，held-out未读取/hash。E24GT10和E28MLP的历史局部信号不因此抹去。',
        '## 成本与核验',
        f"实际原NSG调用{output['physical_calls']:,}，修复0，合成0，正常预算收口。训练8次共{sum(m['training_seconds'] for m in train):.2f}s(CPU8，含对齐诊断)。正式CPU15/实际线程1/OMP-BLAS-MKL1，无训练并发。170点471200输出独立评分，8条原曲线160000输出与E28回归；fit已知三元组{output['fit_native_cache_parity_outputs']:,}输出与原缓存核对。原base/图/kernel/H/旧模型与结果保持身份。旧GT/QGT/主图从零成本未新测。",
        '## 证据与接续',
        f'- [协议](../{relative}/protocol.md)、[完整报告](../{relative}/report.md)、[方法推导](../{relative}/research.md)。\n- [主曲线](../{relative}/figures/recall_qps_main.svg)、[全部曲线](../{relative}/figures/recall_qps_all.svg)、[因素图](../{relative}/figures/factor_effects.svg)、[工作簿](../{relative}/chart_data.xlsx)。\n- [原始点](../{relative}/results/all_points.csv)、[调用账](../{relative}/logs/evaluation_jobs.json)、[最终审计](../{relative}/reviews/final_audit.json)。',
        '本版本收口，下一方向见当前[s-target](../s-target.md)，不借本轮余量扩网格。'
    ])+'\n')
    history_readme=R/'experiment_history/README.md'
    shutil.copy2(history_readme,O/'source_before/history_README.md')
    content=history_readme.read_text()
    marker='## 写入规则'
    assert marker in content
    content=content.replace(marker,'| [18 教师与目标对齐](18_teacher_objective_alignment.md) | E29：教师/损失2×2、完整fit诊断、110点三轮Recall–QPS与因素交互 |\n\n'+marker,1)
    # Keep the new row adjacent to the existing table instead of separated by a blank line.
    content=content.replace('边界 |\n\n| [18','边界 |\n| [18')
    history_readme.write_text(content)
    index=R/'s-experiment.md'
    content=index.read_text()
    marker='| E28 GT10共享入口变换'
    assert marker in content
    row=f"| E29 教师与目标对齐 | 原/保留教师×CE/margin的8次共享linear训练；完整fit、开发及110正式点三轮wall | `{conclusion['status']}`；拟合/实际检索与因素交互分别记录，原模型恢复并保留全部正负 | [18 教师与目标对齐](experiment_history/18_teacher_objective_alignment.md) |\n"
    index.write_text(content.replace(marker,row+marker,1).replace('当前最近完成分析已为E27','当前最近完成实验已为E29').replace('十六份详细卡片','十八份详细卡片'))
    (R/'summary.md').write_text('\n\n'.join([
        '# ACSG 当前实验总结',
        f"> 更新至2026-09-11。E29教师与目标对齐已完成，状态`{conclusion['status']}`。架构见[spec](spec.md)，下一阶段见[s-target](s-target.md)，完整历史见[s-experiment](s-experiment.md)。",
        '## 当前判断',
        '**'+conclusion['verdict']+'** '+recommendation,
        '本轮把教师与损失分开做2×2，固定GT10 hard/sharedlinear/λ100/80epoch。margin不再只依赖集合概率，而直接惩罚漏选教师成员；keep教师在无额外命中空间时保留原实际三入口。完整实际性能必须独立看，不由教师拟合指标升级为方法GO。',
        '## 完整五L结果',
        '下表均相对本批GT10 hard；ΔR是Recall@10百分点，QPS是同L三轮中位数之比。全部正负保留。',summary_table,
        '预设WebVid75/80/85%、Yandex90/95/98%的非支配曲线log-QPS插值，仅概括粗网格相对位置：',gate_table,
        '## 机制上推进了什么',
        '教师T0→T1在WebVid/Yandex分别改10041/10257条query的目标，候选最高Recall保持79.642%/92.929%；keep教师平均图NDC升至1666.10/2890.70，明确放弃了部分成本改道。C8教师逐query用GT选优，不能部署或当作全H/等工作上界。',
        '两集原cost_ce均逐位恢复E28 linear100；8份模型导出/损失独立NumPy核验。margin在WebVid改善了教师入口拟合，但同λ的漂移也明显更小；本轮没有漂移匹配搜索控制，不能把所有差异都解释成对齐机制。Yandex及开发段结果与训练拟合分开保留。',fit_table,
        f'原HNSW实际入口与精确画像top3不总一致；T1保留实际路由，精确训练指标不等同于部署决策。两因素和交互、fit完整有/无headroom分组、梯度与负例见[报告](%s/report.md)。'%relative,
        '## 执行与证据边界',
        f"复用224万逻辑三元组标签，全量重新独立评分，新标签调用0。训练8次{sum(m['training_seconds'] for m in train):.2f}s(CPU8)。全部170点471200个输出独立评分；正式110点各3次warm/plain，原八曲线160000输出回归E28。真实NSG调用{output['physical_calls']:,}，repair0，synthetic0；预算收口。",
        '正式CPU15/实际线程1/OMP-BLAS-MKL1，各方法顺序执行，GT/count/I/O/建图在timer外。原图、base、kernel、H及旧资产只读。fit/cal/audit/validation均有历史使用，held-out未读取/hash；一个图/H、单优化种子，不构成新盲测或论文级结论。三次wall不是Recall样本，bootstrap未校正多重比较；插值不是额外实测等Recall点。',
        'E24GT10和E28MLP局部信号保留；增强未形成稳定双数据优势不抹去原方法已有证据。E28完整旧summary见本轮修改前快照。',
        '## 交付',
        f'- [完整报告](%s/report.md)、[主曲线](%s/figures/recall_qps_main.svg)、[所有方法](%s/figures/recall_qps_all.svg)、[Excel](%s/chart_data.xlsx)。\n- [协议](%s/protocol.md)、[最终审计](%s/reviews/final_audit.json)、[历史18](experiment_history/18_teacher_objective_alignment.md)、[E28原summary快照](%s/source_before/summary.md)。'%(relative,relative,relative,relative,relative,relative,relative)
    ])+'\n')
    spec=R/'spec.md'
    content=spec.read_text()
    content=content.replace('E27既有证据归因及限定shuffle/exact/重复计时工具已实现；原Fast/kernel不变','E29教师/目标2×2训练与评测工具已实现；原Fast/kernel不变')
    start=content.index('## 教师与目标对齐 v1（E29')
    content=content[:start]+f'''## 教师与目标对齐 v1（E29，2026-09-11，已完成）

独立[E29协议]({relative}/protocol.md)固定E28共享linear/λ100/80epoch，2×2分别改变教师和损失。[prepare.py]({relative}/src/prepare.py)核验E28原始三入口标签，导出原cost教师和无额外hits时保留GT10实际HNSW3的keep教师；两教师逐query最高hits相同，新标注0。新M损失给非教师分数加μ=.1后取top3，减去完整教师分数；原C集合CE不变。只对教师漏选成员给结构化hinge上界，不将其视为NSG损失。

[train.py]({relative}/src/train.py)输出8份float32单位W、完整目标轨迹和每10epoch精确对齐。cost_ce在两集逐位恢复E28 linear100；全枚举/有限差分与NumPy导出/最终两损失核验通过。全部模型在开发query前冻结，无cal选择。在线raw query/一份HNSW3/原NSG不变。

[run_evaluation.py]({relative}/src/run_evaluation.py)使用与E28逐位相同的独立复制binary及源码，原build身份记录在bin/evaluate.provenance.json。完整fit20k、cal1024、audit1024及原validation2000：170点471200输出；110正式点各3次warm/plain，GT/count/I/O在timer外，CPU15/实际线程1与资源/调用cap逐job核验。相同模型五L入口/微型图一致，全部count/reference/repeat结果按bit核验；8条旧曲线160000输出回归E28。

[analyze.py]({relative}/src/analyze.py)独立GT重评分、完整fit新入口与兼容标签核对、两个因素的配对差值/交互，以及明确标记的非支配曲线插值。[gradient_diagnostics.py]({relative}/src/gradient_diagnostics.py)仅在全部查询后做fit梯度/几何分析，optimizer step与NSG调用均0。实际NSG调用2085120，repair0，synthetic0；本版本预算收口。全部旧资产/冻结/图表与文档验收见[final_audit]({relative}/reviews/final_audit.json)。方法结论见summary与[历史18](experiment_history/18_teacher_objective_alignment.md)，不由实现通过升级为性能GO。
'''
    spec.write_text(content)
    (R/'s-target.md').write_text(f'''# ACSG 下一阶段方向与实验接续

2026-09-11。E29教师与目标对齐已完成并收口，状态`{conclusion['status']}`。{conclusion['verdict']} {recommendation} 原用户授权的训练、真实Recall–QPS曲线、分析和验收均完成；以下建议未执行，不自动借用本轮剩余额度。

## 1. 首先评估多个等效好集合的监督

E29将“换教师”与“换损失”分开，margin对教师入口的拟合与真实检索效果不总同步。下一步可先只读当前C8完整标签，研究最高命中层级内多个集合的等效程度和成本分布，避免强迫学唯一入口身份。候选外效用未知，不能将其默认为负例或用C8内评价外推全H。完整fit真实检索、因子差值与梯度证据见[报告]({relative}/report.md)。

若启动新的训练，应先锁定集合等效定义、成本取舍和唯一教师控制；保持同H/原NSG/实际三入口，通过新独立协议报告fit与开发真实命中，不凭目标下降扩网络。该方向当前只有建议，没有实施新的多集合损失。

## 2. 漂移匹配控制优先于扩大模型

同λ没有匹配CE/margin的实际变换幅度。可设计仅由fit导出向量确定缩放系数的CE残差对照，以匹配margin漂移，再做独立真实查询比较；这能检查收益是否主要来自更保守的改动。几何投影结果已经单列，但未执行该反事实QPS控制。新画像和新查询必须有独立预算，不能从旧输出模拟速度。

## 3. 优化精度与迁移边界

当前为固定80轮、一个种子、共享linear，无收敛证书。若继续同目标，应先明确优化充分性的可检验标准和固定停止规则，再研究开发段是否跟随；不要把更多epoch或更大MLP自动等同于方法改进。若完整fit真实效用没有进展，不扩大模型/held-out；若仅fit有收益，先定位可迁移监督。

## 4. 资产、数据与重新启动约束

- E29实际NSG调用2,085,120，训练8，新标注0，repair0，预算收口；不转用修复余量。
- E24–E29原图/H/源码/标签/模型/日志与结果保留。架构/API见[spec](spec.md)，历史见[s-experiment](s-experiment.md)。
- fit/cal/audit/validation均有历史使用；held-out未读取/hash。本轮结果不是新盲测或论文充分性结论。
- 只有新的独立同机端到端Recall–QPS支持性能判断，教师空间、精确入口排名、梯度和NDC都不是其替代品。
- 接续先读AGENTS、summary、spec、本文件、历史18和原协议/结果，再建立独立版本。旧runner拒绝覆盖，不能换名重启已收口网格。

本轮完整产物：[报告]({relative}/report.md)、[因素曲线]({relative}/figures/factor_effects.svg)、[Excel]({relative}/chart_data.xlsx)、[验收]({relative}/reviews/final_audit.json)。
''')
    (O/'README.md').write_text(f'''# E29 教师与目标对齐

状态`{conclusion['status']}`。{conclusion['verdict']}

- [完整报告](report.md)、[理论与来源](research.md)、[执行前协议](protocol.md)。
- [主Recall–QPS](figures/recall_qps_main.svg)、[全部基线](figures/recall_qps_all.svg)、[因素与交互](figures/factor_effects.svg)。
- [图表数据工作簿](chart_data.xlsx)、[全部实测点CSV](results/all_points.csv)、[调用账](logs/evaluation_jobs.json)。
- [状态](state.json)、[最终验收](reviews/final_audit.json)、[源入口](src/common.py)。

source_before保存修改前文档快照，旧相对链接属于原根目录语境。旧大型数据/图/标签保持原位置，只读绑定；本版本脚本拒绝覆盖已有输出。
''')
    dump(O/'reviews/documentation_update.json',dict(status='PASS',documents=[identity(p) for p in [R/'summary.md',R/'spec.md',R/'s-target.md',R/'s-experiment.md',h,history_readme,O/'README.md']]))
    print('root and history documents updated',flush=True)

if __name__=='__main__':main()
