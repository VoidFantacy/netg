from shared import *
threads(8)
d=read(O/'results/diagnosis.json');jobs=read(O/'logs/jobs.json')
assert read(O/'reviews/attribution_verification.json')['status']=='PASS'
status='COMPLETE_REMOVED_PROFILE_ATTRIBUTION_CONTEXT_DEPENDENT_CREDIT'
rel=str(O.relative_to(R));hist='experiment_history/31_removed_profile_factorial.md'
names=dict(zip(DS,['WebVid','Yandex']))
table='| 数据集 | 配置 | 新增命中G | 损伤L | 净命中 | ΔRecall pp | 受益/受损query |\n|---|---|---:|---:|---:|---:|---:|\n'
labels={'C':'原中心','F':'完整扰动','S':'仅改被移除画像','R':'恢复该行、其余照改'}
for m in d['metrics']:
 table+=f"| {names[m['dataset']]} | {m['cell']} {labels[m['cell']]} | {m['gain_hits']} | {m['loss_hits']} | {m['net_hits']:+d} | {m['delta_recall_pp']:+.4f} | {m['helped_queries']}/{m['harmed_queries']} |\n"
cases='| 数据集/冻结query | C | F | S | R | 命中交互 |\n|---|---:|---:|---:|---:|---:|\n'
for s in d['datasets']:
 for ca in s['cases']:
  cases+=f"| {names[s['dataset']]} {ca['role']} row{ca['row']} | "+' | '.join(str(ca['hits'][cell]) for cell in CELLS)+f" | {ca['interaction']:+d} |\n"
finding='''WebVid被移除画像1627796是指定完整扰动中损伤的必要组成，但单改不足以致损；Yandex被移除画像8309868单改足以致损，但其余画像块也能独立致损，恢复该行不能修复。画像责任依赖当前其它画像背景，决定后续离线RL采用真实局部动作配对ΔJ，不能按最终入口身份静态分摊全局回报。'''
mechanism='''WebVid负例row3282的C/F/S/R命中为9/0/9/9，目标单独边际0、在其余改动背景下边际−9。S仍移除了1627796，却换成1427523；它的完整返回ID/距离bits/graph NDC与C相同。F换成42091并丢9命中；R恢复原三入口并救回。损伤取决于联合改道，不能把“移除旧入口”本身等同损伤，也不能把责任独占给新增画像42091。

Yandex负例row3962为10/0/0/0；S和R都到达与F相同的坏三入口。目标单独边际−10、已有其余改动时边际0，表现为重复致损，零条件边际不代表该目标一直无害。其余块内部尚未逐hub定位，不能声称找到唯一坏画像。

本次2048条命中交互I=F−S−R+C只有两条非零：WebVid row3282为−9，Yandex row3962为+10。后者是损伤重叠造成的非加和，不是正收益。E41此前全部0针对不同的“新增画像/其余”切分，不能外推到所有分块；原结果无需覆盖或回写。两集C/F/S/R的拓扑SHA均不同，评分变化和普通HNSW重建邻接变化没有独立隔离，不宣称具体访问因果或共享表示数学不可兼容。'''
pool='''WebVid仅目标S在全1024损失1命中（row2279的5→4），没有收益；R相对F救回row2279的1个和原负例的9个，保留全部22个原增益，损伤52→42，仍净−20，不能当新默认。Yandex S净−10，R/F逐query命中完全相同，均20收益/23损失。两原正例的收益都保留在R。所有Δ以各自C为基准：WebVid为E37已选中心，Yandex为初始化；不是与当前默认的独立比较。'''
wall=sum(j['wall_seconds'] for j in jobs);loadtime=sum(j['load_seconds'] for j in jobs);buildtime=sum(j['native']['build_seconds'] for j in jobs)
cost=f'''实际8192正常NSG+384三路parity=8576，低于10000硬限；8448 HNSW、8普通构图、0optimizer/新GT。两个查询进程串行CPU15，配置/实际/OMP/BLAS/MKL线程均1。合计wall {wall:.3f}s，其中加载{loadtime:.3f}s、构图{buildtime:.3f}s；峰值RSS约{jobs[0]['peak_RSS_KiB']/2**20:.3f}/{jobs[1]['peak_RSS_KiB']/2**20:.3f}GiB。该wall包含加载、计数、IO及验收，不是QPS。两job均终态完成，无重试/修复查询、无排队任务。'''
validation='''8192返回独立集合评分、4096旧E39输出逐位恢复、4096与E41 C/F回归、128query三路parity、八W逐行来源、2048交互和hits/U/J三个信用口径复核通过。所有质量、零命中、入口变化、三项NDC及损伤明细已复核。旧E37–E41整目录与实际native/NSG依赖前后SHA保持，根文档前件独立保存；无新的原validation/held-out读取或hash，旧目录已有隔离开发产物的保护字节读取单列。'''
reward='''后续奖励选择为当前背景下的真实局部动作ΔJ：同批GT无关训练query，比较改动前后命中，减原anchor分母下0.1×总NDC变化、0.1×零命中事件变化，再减原画像漂移正则差。完整批次的收益与损伤均收费；不能只看最后选中该hub的query。S−C与F−R分别对应两个实际背景，不混用、不永久给hub贴好坏标签。两背景平均信用已保存并核验守恒，只作记账，不作为唯一因果分配或旧共享X策略的采样奖励。新局部动作参数化与训练均未实施。'''
report=f'''# E42 被移除入口画像的责任诊断

2026-09-12，状态`{status}`。用户要求先定位损伤责任、再决定RL奖励分配；指定控制已执行，奖励设计已形成。

{finding}

## 控制与输入

冻结E40同负例中唯一被移除hub：WebVid selected/action3/hub1627796（内部slot543），Yandex zero/action0/hub8309868（slot686）。保留E39每集原1024行和E40原正负例，不使用新结果换目标。C全中心、F全原扰动、S仅目标行取F、R仅目标行保持C。每行直接复制原单位float32 W，未插值/采样/训练，S/R不保证共享参数可达。

普通HNSW M16/efConstruction200/seed20260828/efSearch10，H815/821、真实ID/插入顺序、top3 ID升序和原NSG raw-IP L128 K10不变。[协议](protocol.md)、[配置](config.locked.json)、[行构造](reviews/construction.json)。

## 实测责任

{cases}

{mechanism}

## 全查询池收益与损伤

{table}

{pool}

![全池收益与损伤](figures/whole_pool.png)

![冻结案例](figures/frozen_cases.png)

## RL奖励决策

{reward}

完整公式、两块交互记账与未实施训练边界见[奖励决策](reward_decision.md)。本次训练案例事后选取；只支持这两组静态干预的条件作用，不构成可学习性、泛化或Recall–QPS优势。

## 实际成本、验收与交付

{cost}

{validation}

最近实际训练/完整QPS仍为E37，默认保持WebVid GT10-soft-t1 / Yandex GT10-hard。E41 WebVid单画像42091的+4无损局部正值保留；本次其它画像的损伤不能抹掉它，也不能据其启动全H自由画像训练。

[全池CSV](results/metrics.csv)、[逐query](results/queries.csv)、[案例入口](results/cases.csv)、[信用CSV](results/credit.csv)、[信用JSON](results/credit.json)、[原始汇总](results/diagnosis.json)、[运行账](logs/jobs.json)、[独立评分](reviews/independent_verification.json)、[责任核验](reviews/attribution_verification.json)、[完成审计](reviews/completion_audit.json)、[最终验收](reviews/final_audit.json)。重现入口为src/prepare.py→src/run.py（逐集）→analyze/verify/credit/plot/verify_attribution；已完成目录拒绝覆盖，不应直接重启runner。
'''
assert not (O/'report.md').exists();(O/'report.md').write_text(report)
(O/'conclusion.md').write_text(finding+'\n\n'+cases+'\n'+pool+'\n\n'+reward+'\n')
# Write the detailed history first, then index, then current summary/contract/next target.
history=f'''# 31. E42 被移除入口画像责任与条件奖励

2026-09-12，`{status}`。[报告](../{rel}/report.md)、[协议](../{rel}/protocol.md)、[配置](../{rel}/config.locked.json)、[验收](../{rel}/reviews/final_audit.json)。

## 问题、控制与结果

E41按新增入口切分未定位损伤，用户本次明确要求继续被移除画像控制。目标来自原固定负例三入口唯一差集：WebVid1627796/Yandex8309868，每集原1024训练query、同C/F与原W字节。普通HNSW重建与原NSG不变，S仅目标行改动、R恢复目标行而其它取F；无新优化。

{finding}

{cases}

{mechanism}

{table}

{pool}

## 决策、成本与证据边界

{reward}

{cost}

{validation}

案例沿用历史GT选择，局部反事实不是泛化/默认替换证据。当前默认与E37开发门保持；E41的WebVid+4无损信号保留。两块内部没有全H责任分解，不因不满足“既充分又必要”而无限追加控制。当前诊断和奖励口径决策收口，新局部训练器及预算匹配非RL对照只有设计，详见[奖励决策](../{rel}/reward_decision.md)和[s-target](../s-target.md)。

[全池](../{rel}/results/metrics.csv)、[逐query](../{rel}/results/queries.csv)、[案例](../{rel}/results/cases.csv)、[信用](../{rel}/results/credit.csv)、[原始JSON](../{rel}/results/diagnosis.json)、[原始调用](../{rel}/logs/jobs.json)、[独立归因](../{rel}/reviews/attribution_verification.json)。源码/输入/配置在query前冻结；初始shell的python别名不存在，未创建文件或搜索，随即使用项目.venv_cpu。实际两个native job无失败或重试。
'''
assert not (R/hist).exists();(R/hist).write_text(history)
index=(R/'s-experiment.md').read_text();marker='|---|---|---|---|\n'
entry=f'| E42 被移除画像责任控制 | 固定新目标1627796/8309868，双集八格与全2048条件信用 | `{status}`；WebVid必要不充分/Yandex充分不必要，明确背景依赖；8576 NSG、0更新 | [31 被移除画像](experiment_history/31_removed_profile_factorial.md) |\n'
assert marker in index;index=index.replace(marker,marker+entry,1).replace('最近完成记录已为E41控制','最近完成记录已为E42责任控制').replace('三十份详细卡片','三十一份详细卡片');(R/'s-experiment.md').write_text(index)
index=(R/'experiment_history/README.md').read_text();marker='\n## 写入规则';assert marker in index
index=index.replace('\n\n## 写入规则','\n## 写入规则');index=index.replace(marker,'\n| [31 被移除画像责任](31_removed_profile_factorial.md) | E42：WebVid联合致损/Yandex重复致损、条件边际与RL奖励决策、8576 NSG/0训练 |\n'+marker);(R/'experiment_history/README.md').write_text(index)
summary=f'''# ACSG 当前结果摘要

2026-09-12，最近完成E42被移除画像责任控制，`{status}`。[报告]({rel}/report.md)、[历史31]({hist})、[验收]({rel}/reviews/final_audit.json)。诊断与奖励口径决策已完成，尚未训练新策略。默认保持WebVid GT10-soft-t1 / Yandex GT10-hard。

## 当前判断

{finding}

{cases}

{mechanism}

## 完整1024训练query/集

{table}

{pool}

## 奖励决策与实际边界

{reward}

{cost}

{validation}

当前结论是两块条件责任，尚未分解其余块内部逐hub或评分/邻接机制。历史训练案例不构成泛化或正式性能GO；E41 WebVid42091单改+4无损信号、E40局部机会和正负抵消、E39批次不稳与E37开发门均保留。最近实际训练及完整QPS仍为E37。新局部训练只保留设计，[奖励决策]({rel}/reward_decision.md)、[下一阶段](s-target.md)，无排队任务。
'''
(R/'summary.md').write_text(summary)
spec=(R/'spec.md').read_text().replace('E41画像2×2控制已验收','E42被移除画像责任控制已验收')
spec+=f'''

## 被移除画像责任与两块条件信用（E42，2026-09-12）

[协议]({rel}/protocol.md)与[prepare.py]({rel}/src/prepare.py)以E40原负例C/F真实入口差集的唯一被移除hub为目标，冻结WebVid1627796/slot543、Yandex8309868/slot686及E39原1024行。C/F/S/R逐行复制字节合同同E41；S/R作为独立干预，不保证原共享X参数可达。保护E37–E41与实际native/NSG依赖，根文档变更前件另存。

[run.py]({rel}/src/run.py)复制E41已验收查询流程，仍导入原E37 native，无新增kernel/API。每集完整预留4288、硬限10000、CPU15/实际线程1，四图正常1024+前16三路parity；实际8576 NSG/8448 HNSW/8构图。C/F全量回归E39及E41，完整raw/W/序列化图保存。

[analyze.py]({rel}/src/analyze.py)新增固定负例目标单独损伤S−C、完整背景下F−R与分别的充分/必要条件，全池G/L/零命中/NDC/U/原漂移保留。[credit.py]({rel}/src/credit.py)保存逐query hits/U/J两个条件边际、交互及两个背景平均信用，逐条满足两块信用和=F−C；平均数仅是明确均分交互的记账约定，不是新训练奖励执行器。

[verify.py]({rel}/src/verify.py)独立评分8192返回、回归4096旧输出、128parity、八W及2048交互；[verify_attribution.py]({rel}/src/verify_attribution.py)进一步核验案例真实入口/充分必要条件、全部损伤/零命中/三NDC、4096 E41回归和2048三种信用口径。改变目标行、背景、query、参数/图/metric/kernel须新身份与真实反馈；只有派生分析变化可复用当前raw。没有新增训练/GT/QPS或原validation/held-out访问。

后续状态条件局部ΔJ仅为[设计]({rel}/reward_decision.md)，不能登记为已实现策略API。实际结果见[summary](summary.md)/[历史31]({hist})。
'''
(R/'spec.md').write_text(spec)
target=f'''# ACSG 下一阶段目标与接续

2026-09-12，E42被移除画像八格及条件信用已完成，`{status}`。[报告]({rel}/report.md)、[历史31]({hist})。当前用户目标“定位责任，再决定奖励”已落实为实测条件归因与奖励设计；新训练尚未实施。

## 已确定与尚未确定

WebVid目标1627796：负例C/F/S/R=9/0/9/9，完整背景中必要、单改不充分；Yandex8309868：10/0/0/0，单改充分、完整背景中不必要。两条交互−9/+10；其余2046条0。E41新增画像的零交互只适用于原切分。实际入口变化不能直接当画像责任，画像责任也不能解释成它与所有query存在固定不可兼容关系。

WebVid R保留22收益、损伤52→42但仍净−20；Yandex R仍净−3。E41单改42091的+4无损仅一条历史query正信号保留。不选择上述诊断模型部署，不扫描全H寻找唯一坏hub；其余块内部和评分/邻接访问机制未分离，两个训练案例不足以推断泛化。

## 第一优先：固定背景的离线局部动作ΔJ，只有设计

主线仍为离线训练入口画像/普通小图，线上raw query→普通HNSW→原NSG。采用[奖励决策]({rel}/reward_decision.md)：一次明确局部改动，相同GT无关训练批次配对测量前后J，完整收益/损伤/总NDC/失败事件和原漂移收费；S−C与F−R按实际背景使用。停止按最终入口静态分摊整体reward，不用两背景平均信用冒充唯一真实责任。

先冻结一次只改一个画像的局部系数参数化、候选方向/hub选择方式、固定原P/B/H和普通构图合同。它与E37共享X整图动作有实质区别，必须验证导出与真实查询身份，不仅改奖励字段。动作和batch选择不能用本次负例GT结果；已有1024诊断行不作独立开发。训练/monitor源行及历史使用需明确。

唯一对照采用相同局部动作族、相同query/构图/真实NSG预算的非RL黑箱优化；保留no-op/原中心。先锁正常/失败调用和资源预算、更新日程、monitor选择规则与停止门，不同时扩大表示、query batch、方向数和σ。当前没有新预算或训练job被悄然启动。

进入训练前必须具体说明参数化可达性、背景身份缓存键、配对奖励精确恢复J差和未观测动作处理；若无法满足这些，停止设计推进。实际训练若只改善历史fit、monitor不稳定或预算匹配控制无增量，就停止该修订，不靠追加epoch/σ或扫全H救场。开发通过后才设计独立同机单线程完整Recall–QPS；局部ΔJ/NDC不作为QPS。

## 第二、第三优先及停止边界

第二优先是评分与普通重建邻接的独立机制控制，仅当后续局部动作收益有重复信号且访问原因会改变动作设计时再立协议；当前SHA差异不能识别路径因果。第三优先是表示容量/多画像讨论，仅在预算匹配的局部策略仍出现稳定跨query冲突时重新评估。不得仅凭本次两条交互重开E22/E28–E32失败版本或新网格。

## 已交付与接续指令

E41、E42指定八格均已完成，不重跑；E42原始W/图/返回、收益损伤/条件信用、图表和独立核验已保存。当前默认仍WebVid GT10-soft-t1 / Yandex GT10-hard；最近实际训练/完整QPS为E37，开发门保持。新训练设计不表示已授权或已执行，无队列。

> 在/data/netg/ACSG完整阅读AGENTS.md、summary.md、spec.md、s-target.md、s-experiment.md，再由历史31进入E42原协议、配置、负例真实入口/输出和三种信用核验。目标责任已经测出背景依赖：WebVid必要不充分，Yandex充分不必要，不重跑两个既有目标或把+10交互写成正收益。继续时先把局部画像动作参数化、GT无关候选/批次、原J配对奖励与预算匹配非RL对照做成唯一具体训练协议；只实施新明确授权的部分，保留历史门和默认。
'''
(R/'s-target.md').write_text(target)
dump(O/'reviews/visual_review.json',dict(status='PASS',review='Both PNGs opened and visually inspected; labels and values readable, no clipping; PNG/SVG/PDF exported.',figures=['whole_pool','frozen_cases']))
dump(O/'reviews/document_sync.json',dict(status='WRITTEN_PENDING_FINAL_AUDIT',files=['summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md',hist],reward_decision='DESIGNED_NOT_TRAINED'))
print('Report, reward decision, history31 and four root documents synchronized')
