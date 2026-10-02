from common import *
from analyze import SHORT,NAMES

def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','|'+'|'.join(['---']*len(headers))+'|']+
        ['| '+' | '.join(str(v) for v in row)+' |' for row in rows])

assert read(O/'state.json')['status']=='REPORT_COMPLETE_FINAL_AUDIT_PENDING'
t=read(O/'results/analysis_tables.json');conclusion=read(O/'results/conclusion.json');selection=read(O/'results/method_selection.json')
out=read(O/'reviews/output_verification.json');gate=read(O/'results/development_gate.json');runs=read(O/'models/training_runs.json')
relative=str(O.relative_to(R));hist=R/'experiment_history/19_equivalent_teacher_sets.md'
assert not hist.exists(),'refuse overwriting a historical card'
recommend='；'.join(d['dataset']+'推荐'+NAMES[d['recommended']] for d in selection['decisions'])+'。'
decision_table=table(['数据集','本批插值速度几何均值最高','相对原默认','推荐'],[
    [d['dataset'],NAMES[d['descriptive_fastest']],f"{d['descriptive_fastest_change_pct']:+.2f}%",NAMES[d['recommended']]] for d in selection['decisions']])
matrix=[]
for ds in DS:
    for L in [64,128,256,400,800]:
        row=[SHORT[ds],L]
        for key in ['e29_cost_margin','single','multi','multi_matched']:
            r=next(r for r in t['delta_gt10'] if r['dataset']==SHORT[ds] and r['stage']=='validation' and r['method']==key and r['L']==L)
            row.append(f"{r['delta_recall_pp']:+.3f} / {r['same_L_qps_change_pct']:+.2f}%")
        matrix.append(row)
matrix_table=table(['数据集','L','E29 margin ΔRpp / ΔQPS','single ΔRpp / ΔQPS','multi ΔRpp / ΔQPS','multi matched ΔRpp / ΔQPS'],matrix)
gate_table=table(['数据集','multi fit ΔRpp','同漂移multi−single pp','cal平均ΔRpp','audit平均ΔRpp','推进条件'],[
    [r['dataset'],f"{r['fit_gain_pp']:+.3f}",f"{r['matched_multi_minus_single_pp']:+.3f}",f"{r['dev_mean_gain_pp']['cal']:+.3f}",f"{r['dev_mean_gain_pp']['audit']:+.3f}",
     '通过' if r['passed'] else '未通过'] for r in gate['datasets']])
history=f'''# 19 等效三入口集合教师（E30）

2026-09-11结果完成，状态`{conclusion['status']}`。{recommend} “本次数值最快”与达到预设替换条件的推荐分别记录，不能将计时波动中的微小领先称为稳定胜出。

## 问题与实质变化

延续[E29](18_teacher_objective_alignment.md)的教师拟合/实际检索缺口。原C8中最高hits且最低graph NDC的教师经常不唯一；新G保留全部严格并列三元组。single只接受原T0，multi接受G；二者使用相同56组合竞争域、共享linear、固定λ100/τ.05/μ.1、Adam.003、80轮最后epoch。损失max(F+.1×非接受)减max接受F只约束已标注C8域，未知组合不当作已知负例。

两集4次训练后，multi均稍有更大位移。仅由fit模型将multi沿normalize(P+t(W−P))缩到single的均方位移，形成multi_matched；single_matched是single同字节alias。整体位移匹配不匹配逐hub方向或实际入口。在线仍一份HNSW3→真实hub→原NSG，无新增在线网络或组合重排。

## 执行与比较

标签224万逻辑条全量ID→GT复核，新标签0。完整fit20k L128、cal/audit1024 L64/128及audit exact3；原validation2k、12方法×5L×两集120正式点，各5次单线程独立warm/plain。所有新画像在开发前冻结，开发门失败不触发重新调参；按用户要求保留最终完整曲线。

{decision_table}

上表在预设WebVid75/80/85%、Yandex90/95/98%的实测非支配曲线上作Recall–logQPS插值，不外推，不是新增精确等Recall测量。原默认为WebVid GT10 soft/Yandex GT10 hard；替换要求覆盖三点，其中至少两点中位+3%且五轮比值均>1，其他点无≥3%退化。

## 完整五L结果

以下相对同批GT10 hard，同L两项变化不等于等Recall加速。全部正负和各轮计时在原报告/表中。

{matrix_table}

## 开发与停止位置

{gate_table}

推进状态`{gate['status']}`。预设fit各≥+0.20pp、成本增幅≤1%、共同位移下multi胜single及两开发split平均收益均正。该门控制进一步研究扩展，不代替最终QPS；最终曲线按用户要求完成。等效数量、共同G接受率、实际HNSW接受、完整fit有/无空间组、分数梯度改变比例分别保存；代理或梯度不是性能因果证明。

关键机制：T0原本就在G内按锚点分数择优，因此初始化时两目标选中的最高分好组合完全相同。有真实命中空间组仅1.04%/0.65%的query改变分数梯度，没有空间组则为15.06%/12.11%；最终multi分数下前者为6.40%/3.42%。这些初末检查及很小的实际单/多差值，削弱“唯一教师身份是当前主要瓶颈”的判断，但不证明整条优化轨迹或QPS因果。多教师与漂移匹配相对推荐方法的三目标插值QPS几何均变分别为WebVid−1.38%/−1.40%、Yandex−0.79%/−0.83%。

## 成本、保护与边界

4次训练共{sum(r['training_seconds'] for r in runs):.2f}s(CPU8，含训练诊断)。原NSG调用{NORMAL_CAP:,}，repair0/synthetic0；180点491200个query输出独立评分，9条原曲线180000输出逐位回归E29。原库/图/kernel不变，新评测源码只将3轮合同改为5轮。正式CPU15/实际进程与OMP线程1，无训练或重分析并发。

只有历史fit/cal/audit/validation、一个H/图、一个优化seed和固定80轮；没有收敛证书、fresh blind confirmation或held-out读取/hash。G的相同命中数/NDC不要求相同GT成员，也不保证相同wall。E24 GT10/E28 MLP历史局部信号保留，本次增强边界不反推原方法无效。

## 原始证据

- [协议](../{relative}/protocol.md)、[完整报告](../{relative}/report.md)、[方法研究](../{relative}/research.md)。
- [主Recall–QPS](../{relative}/figures/recall_qps_main.svg)、[全部曲线](../{relative}/figures/recall_qps_all.svg)、[漂移控制](../{relative}/figures/drift_control.svg)、[Excel](../{relative}/chart_data.xlsx)。
- [选择判定](../{relative}/results/method_selection.json)、[开发门](../{relative}/results/development_gate.json)、[原始点](../{relative}/results/all_points.csv)、[调用账](../{relative}/logs/evaluation_jobs.json)、[最终验收](../{relative}/reviews/final_audit.json)。

本版本预算收口；接续见当前[s-target](../s-target.md)，不重启旧runner。
'''
hist.write_text(history)
p=R/'s-experiment.md';s=p.read_text();anchor='|---|---|---|---|\n';assert anchor in s
s=s.replace(anchor,anchor+f'| E30 等效三入口教师 | 严格并列G、单/多教师4次训练与漂移控制；完整fit/开发、120正式点五轮wall | `{conclusion["status"]}`；描述性最快与推荐分开，原方法及全部正负保留 | [19 等效教师](experiment_history/19_equivalent_teacher_sets.md) |\n',1)
s=s.replace('当前最近完成实验已为E29','当前最近完成实验已为E30').replace('十八份详细卡片','十九份详细卡片');p.write_text(s)
p=R/'experiment_history/README.md';s=p.read_text();anchor='\n## 写入规则\n';assert anchor in s
s=s.replace(anchor,'| [19 等效三入口教师](19_equivalent_teacher_sets.md) | E30：严格并列集合、单/多教师与漂移控制、120点五轮Recall–QPS及推荐选择 |\n'+anchor,1);p.write_text(s)
summary=f'''# ACSG 当前实验总结

> 更新至2026-09-11。E30等效集合教师已完成真实评测与分析，状态`{conclusion['status']}`。架构见[spec](spec.md)，接续见[s-target](s-target.md)，历史见[s-experiment](s-experiment.md)。

## 当前选择

{recommend}

{decision_table}

描述性最快按三共同Recall参照的插值速度几何均值排序；推荐另要求至少两个目标中位≥+3%、五轮比值均>1、无约定退化且覆盖三个参照。插值不是新增实测等Recall点；未满足替换门就保留默认，不将细小数值排序写成稳定胜出。

## 实际方法与完整五L

固定GT10 hard锚点、共享linear/λ100/80epoch。G保留C8最高hits且最低graph NDC的全部严格并列三元组；single接受原T0，multi接受G，两者同已知竞争域/损失/预算。multi_matched只由fit模型缩到single均方位移，single_matched同字节alias。在线一份HNSW3/原NSG不变。

{matrix_table}

以上相对同批GT10 hard，ΔR为百分点、ΔQPS为同L比值，不等于等Recall加速。完整12方法、五轮raw wall及区间见[报告]({relative}/report.md)。

## 推进边界与机制

{gate_table}

开发门状态`{gate['status']}`。G常常不唯一，但不代表其身份约束是主要训练瓶颈；候选内接受率、全H精确top3、实际HNSW入口和NSG收益分别保存。只读分数梯度差异用于解释约束范围，不替代性能归因。漂移只匹配全H均方位移，不匹配方向、逐hub幅度或入口变化。

T0已在G内按锚点分数择优，初始化时两目标选中的最高分好组合完全相同。有真实命中空间组仅1.04%/0.65%的query改变分数梯度；最终multi分数下为6.40%/3.42%。等效答案很多与实际关键约束改变很多并不等价。多教师/漂移匹配相对推荐方法的三目标插值QPS几何均变为WebVid−1.38%/−1.40%、Yandex−0.79%/−0.83%；均未达到预设替换条件。

## 计量与证据

两集4次训练，2个漂移控制画像，新训练标签0；224万逻辑标签全量复核。原NSG实际{NORMAL_CAP:,}次，repair/synthetic均0。全部180点491200个输出独立评分，正式120点各五轮单线程wall，9条旧曲线180000输出逐位回归E29。

CPU15/实际线程1/OMP-BLAS-MKL1，计数/GT/I/O/建图在timer外，不与训练或重分析并发。历史fit/cal/audit/validation重复使用；一个H/图/训练seed，无优化收敛证书，held-out不读取/hash。原GT10和E28 MLP的历史局部信号保留。

## 交付

- [完整报告]({relative}/report.md)、[主图]({relative}/figures/recall_qps_main.svg)、[全部曲线]({relative}/figures/recall_qps_all.svg)、[Excel]({relative}/chart_data.xlsx)。
- [协议]({relative}/protocol.md)、[择优]({relative}/results/method_selection.json)、[开发门]({relative}/results/development_gate.json)、[最终验收]({relative}/reviews/final_audit.json)、[历史19](experiment_history/19_equivalent_teacher_sets.md)。
- E29完整旧summary保存在[修改前快照]({relative}/source_before/summary.md)。
''';(R/'summary.md').write_text(summary)
spec=R/'spec.md';s=spec.read_text();s=s.replace('（E29教师/目标2×2训练与评测工具已实现；原Fast/kernel不变）','（E30等效教师/漂移控制/五轮评测工具已实现；原Fast/kernel不变）')
s=s.replace('## 等效三入口集合监督 v1（E30，2026-09-11，执行中）','## 等效三入口集合监督 v1（E30，2026-09-11，已完成评测）')
s=s.replace('当前真实检索与最终验收待执行，不能由实现或训练通过宣称方法收益。',
    f'实际180点491200个输出已独立GT评分，120正式点各五轮wall，9条旧曲线180000输出回归E29；五L同模型入口与微型图一致。全部{NORMAL_CAP:,}原NSG调用，repair/synthetic0，预算收口。择优按冻结的共同Recall参照及五轮速度条件执行，原始wall/插值/描述性最快与推荐身份分别存储。完整验收见[final_audit]({relative}/reviews/final_audit.json)，方法结论见summary/[历史19](experiment_history/19_equivalent_teacher_sets.md)，不由实现通过升级为性能GO。')
spec.write_text(s)
target=f'''# ACSG 下一阶段方向与实验接续

2026-09-11。E30等效集合教师的训练、漂移控制、真实Recall–QPS及择优已完成，状态`{conclusion['status']}`。{recommend} 本轮用户要求的依次执行及最终图表交付已经实现，原版本预算收口。

## 1. 当前可采用的结果

{decision_table}

推荐与描述性最快分开；共同Recall插值不等于新增精确等Recall点，也不是新盲测。全部12方法曲线及五轮原值见[报告]({relative}/report.md)、[图]({relative}/figures/recall_qps_all.svg)、[Excel]({relative}/chart_data.xlsx)。

## 2. 本轮之后的研究判断

开发门为`{gate['status']}`。G不唯一已被证实，但单/多集合、位移控制、完整fit及开发不能自动串成性能因果证明。若继续研究，应先解释剩余错误发生在已知C8排序、全H画像打分、近似路由还是实际NSG效用；现有[训练/部署分析]({relative}/report.md)和[完整fit分组]({relative}/results/fit_groups.csv)优先复用，不重复相同网格或直接增加模型容量。

如果目标转为确认当前默认的可靠性，应先建立独立复现协议、明确新的query/图或重复条件与成本；不要将本轮已经反复使用的validation称为新验证。任何新画像、优化、HNSW参数或新query均是独立版本，不能从已有输出推算其QPS。当前没有启动后续训练或新的held-out测试。

## 3. 已完成步骤与停止位置

- 严格并列G、single/multi同竞争域控制：4次训练已完成；新标签0，复用224万逻辑三元组。
- 两集multi均缩到single均方位移，系数仅来自fit，single_matched同字节alias；全部实际画像均完成真实检索。
- 完整fit、cal/audit及exact诊断完成；开发门各条件、正负query和几何/分数梯度限制保留。
- 正式两集12方法×5L×五次单线程wall完成，选出描述性最快及有证据支持的推荐。正常调用{NORMAL_CAP:,}，修复0，不借余量扩网格。

## 4. 接续与保护

先读AGENTS、summary、spec、本文件、[历史19](experiment_history/19_equivalent_teacher_sets.md)，再沿[协议]({relative}/protocol.md)、[状态]({relative}/state.json)、[选择判定]({relative}/results/method_selection.json)、[验收]({relative}/reviews/final_audit.json)核对原件。E24–E30图/H/源码/GT/标签/模型/日志与结果保留，旧runner拒绝覆盖。

正式测试继续CPU15/实际线程1，一次一个方法；训练/标签/重分析不与计时并发。fit/cal/audit/validation都有历史使用，held-out未读取/hash。新任务须先说明它与已经完成的教师身份对照有何实质区别，并锁定预算、比较与停止条件。
''';(R/'s-target.md').write_text(target)
(O/'README.md').write_text(f'''# E30 等效三入口集合监督

{recommend}

两集4次训练、2个漂移控制、完整fit/开发和120正式点五轮单线程wall已完成。状态`{conclusion['status']}`，原NSG调用{NORMAL_CAP:,}，新训练标签0。

- [完整报告](report.md)、[主Recall–QPS](figures/recall_qps_main.svg)、[全部方法](figures/recall_qps_all.svg)、[Excel数据](chart_data.xlsx)。
- [协议](protocol.md)、[方法研究](research.md)、[选择判定](results/method_selection.json)、[开发门](results/development_gate.json)、[最终验收](reviews/final_audit.json)。

所有结果为历史query上的本地探索；描述性最快和可靠推荐分别记录。新执行使用独立版本，不覆盖当前模型、标签和原始输出。
''')
files=[R/n for n in ['summary.md','spec.md','s-target.md','s-experiment.md']]+[hist,R/'experiment_history/README.md',O/'README.md']
dump(O/'reviews/document_update.json',dict(status='PASS',files=[identity(p) for p in files],history_before_summary=True))
print('DOCUMENTS_UPDATED',flush=True)
