from shared import *
d=read(O/'results/diagnosis.json');v=read(O/'reviews/independent_verification.json');jobs=read(O/'logs/jobs.json')
assert v['status']=='PASS' and all(j['status']=='COMPLETE' for j in jobs)
rel=O.relative_to(R).as_posix();status='COMPLETE_TARGET_REST_FACTORIAL_WEBVID_LOCAL_SIGNAL_YANDEX_TARGET_NULL'
conclusion='WebVid的一个有效单画像改动可以从全局负收益中分离：只改hub42091保留正例1→5，负例保持9，全1024净增4命中且无新增损伤。Yandex的hub9339959单独改动没有命中收益，其余画像块已能重现完整扰动的收益与损伤。当前证据支持按实际干预分配画像责任，不能按最终新增入口直接归因；未建立跨数据集学习方法或泛化优势。'
labels={'C':'原中心','F':'完整扰动','S':'只改目标画像','R':'只改其余画像'}
table='| 数据集 | 配置 | 新增命中G | 损伤L | 净增命中 | ΔRecall pp | 受益/受损query |\n|---|---|---:|---:|---:|---:|---:|\n'
for m in d['metrics']:
 table+=f"| {'WebVid' if m['dataset']==DS[0] else 'Yandex'} | {m['cell']} {labels[m['cell']]} | {m['gain_hits']} | {m['loss_hits']} | {m['net_hits']:+d} | {m['delta_recall_pp']:+.4f} | {m['helped_queries']}/{m['harmed_queries']} |\n"
casetable='| 冻结query（train/source行） | C 原中心 | F 完整扰动 | S 仅目标 | R 仅其余 |\n|---|---:|---:|---:|---:|\n'
for s in d['datasets']:
 for x in s['cases']:
  casetable+=f"| {'WebVid' if s['dataset']==DS[0] else 'Yandex'} {x['role']} {x['row']}/{x['source_row']} | {x['hits']['C']} | {x['hits']['F']} | {x['hits']['S']} | {x['hits']['R']} |\n"
cost=f"实际8192次正常NSG+384次parity=8576，低于10000硬限；HNSW8448次、普通构图8次、optimizer更新0、新GT0。两个查询进程串行CPU15/实际线程1，合计{sum(j['wall_seconds'] for j in jobs):.3f}s，其中索引加载{sum(j['load_seconds'] for j in jobs):.3f}s、构建{sum(j['native']['build_seconds'] for j in jobs):.3f}s；含计数/写盘/验收，不能当QPS。峰值RSS约{jobs[0]['peak_RSS_KiB']/1024/1024:.3f}/{jobs[1]['peak_RSS_KiB']/1024/1024:.3f}GiB。"
next_plan='''## 接续：验证负例中被移除画像的责任，尚未执行

当前2×2已经完成，不重跑、不追加本次标签或训练。停止把Yandex的9339959当作已识别有效画像；WebVid42091保留为单query的局部正信号，不据此启动全H自由画像训练。

唯一最小后续是把同一固定负例里被移除的画像作为新目标：WebVid row3282原移除hub1627796，Yandex row3962原移除hub8309868。两者来自原冻结三入口差集，均唯一，不按新结果挑hub。这检验坏改道是否来自原入口画像被压低，而不是新增入口自身变好；仍可能包含普通小图重建效应。

沿用各自原C/F、同1024名单和W行字节，再做C/F/S/R：S只改该被移除画像，R改其余但保留它。若S能复现原负例损伤而R消除它，支持该画像改动在这个背景下既能产生损伤、又是完整扰动中该损伤的必要组成；两条件分别报告。若不成立，不据此遍历全H或扩大网格。完整1024的G/L与新增损伤继续收费，不只看负例。

建议仍双集四格8192正常+384parity=8576、总硬限10000、8构图、0optimizer/新GT/新validation/held-out，无QPS。此为新版本待冻结方案，当前没有这些新目标的反事实结果或排队任务。保留原C/F回归、CPU15单线程、输入/输出SHA、失败完整预留合同。

确认责任之后才讨论按入口构造小动作、用真实反事实奖励进行信用分配；不能直接把全局reward分给所有最终入口。E22/E28–E32自由表示/目标实验仍须作为约束，原有局部收益不能替代独立开发和完整Recall–QPS。当前没有新训练授权被推断或任务排队。
'''
(O/'next_control.md').write_text(next_plan)
report=f'''# E41 目标入口画像与其余画像2×2控制

2026-09-12，状态`{status}`。用户要求的八格控制全部实际完成。[协议](protocol.md)、[锁定配置](config.locked.json)、[完整结果](results/diagnosis.json)、[独立核验](reviews/independent_verification.json)、[完成审计](reviews/completion_audit.json)、[最终验收](reviews/final_audit.json)。

## 当前结论

{conclusion}

两集全部2048条query的命中交互I=F−S−R+C均为0；当前观测是两个画像块命中效果相加，不能写成已发现非线性耦合。总NDC/原U有小非零交互，不能将命中相加扩展为所有搜索工作和浮点奖励也严格相加。

## 干预、来源与四格

C全部画像取E39对应中心，F全部取E40冻结原动作；S只把目标hub一行换成F，R只将F目标行换回C。WebVid selected/action3，目标42091（内部slot17），Yandex zero/action0，目标9339959（slot771）。S实际各只改1行，R分别改814/820行；所有行都逐字复制既有单位float32 W，未训练或插值，S/R不冒称原共享RL可达checkpoint。

案例/正负行从E40原attribution_cases直接冻结，未按新结果更换；WebVid来自E37已选μ140，Yandex来自μ0，两个中心身份不同，不能并为同一训练阶段。全部query为E39原1024训练行，原4096输入/GT/源行不改，有历史使用，非独立泛化测试。

每格普通HNSW M16/efConstruction200/seed20260828/ef10、原真实ID/顺序、direct3升序→原NSG L128/K10，raw-IP/embedded base不变。改画像会自然改变普通重建的邻接，所以本控制识别整个画像块干预（评分与小图均可能改变），未隔离HNSW访问路径或独立图效应。

## 全1024收益与损伤

{table}

表中以该集固定中心C为参照；WebVid C是E37已选模型，不能把S的+0.0391pp称为对当前默认GT10的独立改进。S只帮助一条已选过的训练query，没有新损伤，是局部机制信号。F原本增加22命中、损失52；S仅保留其中4个增益，R保留另18个且产生全部52个损伤。其余收益没有被抹去，不能称S保留了F全部收益。

Yandex S全池命中与C相同，R全池命中与F相同；R/F入口也完全相同，但route NDC不同。S仍改变一条query入口而没有改变命中，不能写成画像/搜索完全不动。Yandex目标单行的原改善未保留，预设局部案例条件未过；WebVid同时完整保留指定改善并消除指定损伤，局部条件通过。两件事不构成双集方法GO。

## 冻结案例与反事实

{casetable}

WebVid正例row707只有目标画像块带来+4：S=C+4，F=R+4；负例row3282只有其余画像块带来−9：R=C−9，F=S−9。R中hub42091画像仍是中心值，但它依然进入坏三入口并使9→0；仅凭该入口出现把损伤归给其画像更新，会归错责任。

Yandex两条案例中，目标画像保持中心值的R已经重现0→8和10→0；S两条都维持C。因此E40“新增同hub有正负”的关联，不能证明该hub画像改动导致这些收益或损伤。本结论不表示这个真实入口自身没有NSG作用，而是该画像行的这次改动对本设置的命中效应为零。

每query I=0的强度限于当前两个固定块、现有幅度、单次确定重建和这2048训练query。它并不证明所有方向都可加，也不证明全部共享表示足够/不足。完整query/入口/因素主效应见[逐query表](results/queries.csv)，四格案例入口/计数见[案例表](results/cases.csv)。

## 成本、核验和保护

{cost}

主分析CPU8/线程1约{d['analysis_seconds']:.3f}s，独立复核约{v['seconds']:.3f}s；不含协议/源码编写、保护hash、绘图和人工阅读。WebVid S相对C graph NDC +0.00397%、total +0.00466%；Yandex S graph0%、total约+0.000099%，这些不是wall/QPS改进。

八份W行来源/单位范数独立验证；C/F四个图的W/拓扑/物理图SHA恢复E39，4096条正常输出按ID/距离bits/入口/两NDC逐位回归。每格16query做count/serialized plain/original kernel三路，128条parity原始输出另与正常结果逐位一致。全部8192返回独立集合评分，2048交互及四条冻结案例、八个全池G/L/奖励重算通过。

E37–E40整目录前后SHA保持，原大NSG和native依赖SHA核验；没有新GT/optimizer/validation/held-out原始读取或hash，保护读取包括旧隔离开发产物，未沿旧manifest递归访问原评估集。原画像/模型/大图/默认保持，根文档修改前件独立保存。全部物理W/小图在models，原始aligned返回在results，调用/线程/时间与进程状态在logs/jobs.json。

[全池图](figures/whole_pool.svg)、[冻结案例图](figures/frozen_cases.svg)。本版本8格预算收口，无新训练/评测排队。

{next_plan}

## 实际命令

原目录一次性冻结、拒绝覆盖。准备、两集查询、后评分/核验/绘图串行，日志保留；重跑须建立新版本，不能直接覆盖当前产物：

```bash
env PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 taskset -c 8 timeout 1800 .venv_cpu/bin/python {rel}/src/prepare.py
env PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 taskset -c 15 timeout 1800 .venv_cpu/bin/python {rel}/src/run.py webvid2_5m_light_v1
env PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 taskset -c 15 timeout 1800 .venv_cpu/bin/python {rel}/src/run.py yandex_t2i_official10M_ip_v1
```

分析/独立复核/绘图为src/analyze.py、src/verify.py、src/plot.py，使用相同单线程环境、CPU8，均不增加NSG或训练。
'''
(O/'report.md').write_text(report);(O/'conclusion.md').write_text(conclusion+'\n\n'+table+'\n'+casetable)
card=f'''# 30. E41 目标画像与其余画像的2×2隔离

2026-09-12，状态`{status}`。[报告](../{rel}/report.md)、[协议](../{rel}/protocol.md)、[锁定配置](../{rel}/config.locked.json)、[完成审计](../{rel}/reviews/completion_audit.json)、[验收](../{rel}/reviews/final_audit.json)。用户明确要求执行E40的未运行控制；本次八格全部完成，没有新训练。

## 设计、输入与结果

固定E40两案例：WebVid selected/action3/hub42091，Yandex zero/action0/hub9339959；各用E39原1024训练query。C=全中心，F=全原扰动，S=只改目标行，R=只改其余行。逐字复制既有单位W，S/R未必为原共享参数可达像。原H/ID/顺序、普通HNSW M16/efC200/seed20260828/ef10及原NSG raw-IP/L128/K10保持，0optimizer。

{conclusion}

{table}

## 案例与解释

{casetable}

WebVid S只帮助row707一条query，无新损伤；F的22个增益中只保留4个，其余18个在R中，全部52个损伤也在R中。该正点必须保留，但相对E37已选中心、且案例/训练数据有历史GT使用，不是独立泛化或默认替换证据。Yandex R已经重现F全部命中/入口，目标行不是本次命中差的必要来源；S自身仍有一条入口变化但没有命中变化。

两集2048条query的命中I=F−S−R+C逐条为0，未观察到命中层非线性交互；NDC/U并非严格无交互。坏路径出现某hub不等于该hub画像更新造成损伤，R中该hub画像保持中心也可能进入坏路径。两个因素同时包含画像评分与普通小图重建的影响，不隔离访问/图机制，不证明任意共享表示硬冲突。

## 执行与保护

{cost}

8192完整返回独立GT集合评分、4096旧输出逐位恢复、128query三路parity、八W行构造与2048交互独立复算通过。原E37–E40整目录/大NSG/native依赖SHA保持，根文档前件保存；没有新原validation/held-out访问/hash，保护旧隔离开发产物的字节读取单列。全部模型/图/返回原件保留，无新QPS/默认更换。

## 接续边界

当前hub42091/9339959的2×2已完成；停止重训/调σ来救Yandex目标无效分支，不把WebVid单query正值升级全H训练。下一最小设计为原同负例中唯一被移除画像（WebVid1627796/Yandex8309868）的责任隔离，尚未构图/查询；同四格预计8576/硬限10000、0optimizer，无排队任务，详见[s-target](../s-target.md)。旧局部信号及E37开发门保持。

[全池表](../{rel}/results/metrics.csv)、[逐query](../{rel}/results/queries.csv)、[案例](../{rel}/results/cases.csv)、[原始JSON](../{rel}/results/diagnosis.json)、[图](../{rel}/figures/whole_pool.svg)。
'''
(R/'experiment_history/30_profile_factorial.md').write_text(card)
p=R/'s-experiment.md';text=p.read_text();assert '| E41 ' not in text
text=text.replace('| E40 ',f'| E41 目标/其余画像2×2 | 双集C/F/S/R八格普通HNSW→NSG，原案例和全1024、逐query交互 | `{status}`；WebVid仅目标+4无损，Yandex目标命中无效；8576 NSG、0更新，默认保持 | [30 画像隔离](experiment_history/30_profile_factorial.md) |\n| E40 ',1)
text=text.replace('最近完成记录已为E40诊断','最近完成记录已为E41控制').replace('二十九份详细卡片','三十份详细卡片');p.write_text(text)
p=R/'experiment_history/README.md';text=p.read_text();line='| [29 画像收益与损伤](29_profile_payoff_attribution.md) | E40：已有动作有限上界/静态最佳差距、覆盖与损伤分解、入口变化及query偏好，0新搜索 |'
assert line in text;p.write_text(text.replace(line,line+'\n| [30 目标/其余画像隔离](30_profile_factorial.md) | E41：固定八格真实控制、WebVid局部单画像+4无损/Yandex目标零命中效应、0训练 |'))
(R/'summary.md').write_text(f'''# ACSG 当前结果摘要

2026-09-12。最近完成E41目标画像/其余画像2×2控制，状态`{status}`。[报告]({rel}/report.md)、[历史30](experiment_history/30_profile_factorial.md)、[验收]({rel}/reviews/final_audit.json)。八格控制全部实际完成，最近训练/完整QPS评测仍为E37，默认保持WebVid GT10-soft-t1 / Yandex GT10-hard。

## 当前判断

{conclusion}

{table}

所有Δ相对该数据集固定中心C，WebVid中心为E37已选模型、Yandex中心为初始化；不是对当前默认的独立性能比较。WebVid S只帮助一条历史选中训练query，保留F的4/22命中增益，不能称保留全部收益。Yandex S质量无变化，R与F全量命中/入口一致。该Yandex目标行的新增关联不能当作有效更新责任。

WebVid指定正例C/F/S/R命中为1/5/5/1，负例9/0/9/0；Yandex为0/8/0/8和10/0/10/0。全2048条命中交互F−S−R+C逐条0，当前是不同块收益损伤相加，未见命中层非线性交互；NDC/U仍有细小非零交互。画像与重建小图没有单独隔离，不宣称HNSW访问原因或共享表示数学不可兼容。

## 实际执行与边界

{cost}

8192输出独立集合评分、4096旧输出逐位回归、128query三路parity、八W行来源与2048交互复核通过。E37–E40和原native/大图保持SHA，根文档前件保存；无新原validation/held-out访问/hash，0新训练/GT，未更换默认或运行QPS。

E40原收益分散/正负抵消、E39批次方向不稳与E37开发门停止均保留；E24 GT10、E36及此次WebVid单画像局部正信号不互相覆盖。当前证据支持先识别真正改动责任，再设计局部动作的离线奖励，不能把全局回报按最终被选入口分摊。

下一步为同一负例中唯一被移除画像的责任隔离，WebVid1627796/Yandex8309868；这项新目标控制尚未执行，旧42091/9339959控制不要重跑。建议仍8576 NSG/硬限10000、0optimizer，详见[s-target](s-target.md)。无排队任务。
''')
(R/'s-target.md').write_text(f'''# ACSG 下一阶段目标与接续

2026-09-12。E41原目标画像/其余画像2×2全部完成，状态`{status}`。[结果](summary.md)、[历史30](experiment_history/30_profile_factorial.md)、[报告]({rel}/report.md)。用户此次执行目标已完成，不将后续控制混作未完当前工作。

## 当前证据与主目标

主目标继续为离线训练静态入口画像/小图，在线普通HNSW→原NSG。E41表明至少一个局部有效画像改动可以从全局负回报中分离：WebVid hub42091单改+4命中且无损，原完整动作−30；Yandex hub9339959单改命中无效，其余画像已重现原正负。全2048条query命中交互逐条0，当前证据指向全局动作混合了不同责任的收益/损伤，尚未证明表示容量缺陷或非线性冲突。

两个案例使用历史GT选定，WebVid只有一条query正值，不能据此扩成全H训练或默认替换。原目标行无效的Yandex分支停止，不追加epoch/σ救场。训练/QPS/开发仍以E37原结果为界。

{next_plan}

## 后续训练与图机制边界

责任控制只生成有来源的真实反事实，不构成新learner。若被移除画像诊断有信号，先固定少量局部动作的选择/回报口径及预算匹配非RL控制，再提交唯一训练修订；不同时改表示、query batch、方向数或σ。旧E22自由低秩/mapping、E28 free/linear/MLP、E29–E32目标经验保持，不能换名重启。

画像改变会改分数也会改普通重建邻接。若进一步要识别图访问作用，必须评分固定/图改变的独立对照，不能从最终三入口或NDC推导访问因果。所有候选默认替换仍须冻结模型、同机单线程完整Recall–QPS，局部fit正值不能替代。

## 接续状态与启动指令

E41两个原目标的八格已经真实执行并验收；未来被移除画像控制只有设计，无反事实画像/图/返回、无训练或评测排队。E37–E40原件、默认和开发门保持。

> 在/data/netg/ACSG完整阅读AGENTS.md、summary.md、spec.md、s-target.md、s-experiment.md，再由历史30进入E41协议、八格raw结果、全2048交互与独立验收。不要重跑已完成的hub42091/9339959控制。审查原同负例中唯一被移除画像1627796/8309868的责任隔离，新版本冻结同C/F、原1024名单、四格行字节、预算8576/硬限10000及单线程parity。只执行新明确授权的诊断，不自动重训、扫全H或读新的validation/held-out。
''')
p=R/'spec.md';text=p.read_text().replace('E40既有动作归因已验收；E37部署及原Fast/NSG kernel不变','E41画像2×2控制已验收；E37部署及原Fast/NSG kernel不变')
text=text.replace('目标hub/其余画像2×2目前仅为s-target设计，未生成反事实W/图或标签。','E40原目标hub/其余画像2×2提案保持当时未执行身份，继任E41已实现，见下节。')
text+=f'''

## 目标画像/其余画像2×2反事实控制（E41，2026-09-12）

[协议]({rel}/protocol.md)及[prepare.py]({rel}/src/prepare.py)直接冻结E40原案例与E39行名单，构造C/F/S/R四格：每行只复制中心或原扰动W字节，S只改目标行、R只改其余行。画像H/真实ID/顺序不变，S/R作为独立干预，不声称原共享参数可达。保存四格W和行级身份，无optimizer/插值/新采样。

[run.py]({rel}/src/run.py)复用E37原native二进制，CPU15/线程1，每集完整预留及native cap4288、全局硬限10000、失败不释放/不自动重试、拒绝覆盖。每格普通build/save→run1024→前16query三路verify；C/F全部返回及W/拓扑/物理小图SHA恢复E39，S/R是真实新搜索。实际双集8576 NSG/8448 HNSW/8build、0optimizer，完整raw返回与parity输出保存。

[analyze.py]({rel}/src/analyze.py)输出以C为参照的全池G/L/net、零命中事件、NDC、原anchor分母U/漂移奖励，以及逐query target/rest主效应和I=F−S−R+C；冻结案例局部条件与全池结果分开，不按新结果择优或部署。[verify.py]({rel}/src/verify.py)独立验证8192集合评分、4096旧输出回归、128parity行、八W构造和2048交互。E37–E40目录及原native/NSG依赖前后SHA保持，根文档前件保留；GT只在返回后评分，无新原validation/held-out访问。改变目标行、幅度、query或kernel须新版本/真实反馈，不能复用未测S/R标签。当前结论见[summary](summary.md)/[历史30](experiment_history/30_profile_factorial.md)。
''';p.write_text(text)
print('E41 report, history30, indices and root documentation synchronized.')
