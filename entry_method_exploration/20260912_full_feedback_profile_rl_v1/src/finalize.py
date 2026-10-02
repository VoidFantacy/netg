from shared import *
import re,ast
threads(8);resources();started=time.monotonic();check(O/'reviews/prequery_freeze.json');check(O/'reviews/protected.json');check(O/'reviews/native_dependencies.json')
assert read(O/'reviews/training_verification.json')['status']=='PASS';r=read(O/'results/summary.json');cost=r['cost'];gate=r['gate'];assert gate['status']=='STOP_FULL_FEEDBACK_BUDGET_EXPANSION'
status='COMPLETE_FULL_FEEDBACK_PROFILE_RL_LOCAL_RL_SIGNAL_AGGREGATE_GATE_STOP'
tab='| 数据集 | 方法/seed | 选中步 | train512 ΔR pp | full train ΔR pp | monitor ΔR pp | 末点monitor ΔR pp | 原E43选中monitor ΔR pp |\n|---|---|---:|---:|---:|---:|---:|---:|\n'
for x in r['models']:
 name='WebVid' if x['dataset']==DS[0] else 'Yandex';tab+=f'| {name} | {x["arm"].upper()}/{str(x["seed"])[-2:]} | {x["selected_step"]} | {x["train_delta_recall_pp"]:+.4f} | {x["full_train_delta_recall_pp"]:+.4f} | {x["monitor_delta_recall_pp"]:+.4f} | {x["last_monitor_delta_recall_pp"]:+.4f} | {x["E43_selected_monitor_delta_recall_pp"]:+.4f} |\n'
core='''完整反馈显著增加了可见质量响应，但仍未形成所有数据集/估计器都稳定增益的结果。WebVid每200步有133–145步见候选命中变化，Yandex74–85步；原E43为13–18/3–7步。两轮训练的状态会分岔，这一频次对比不再是固定状态采样消融；E44已有固定状态的漏反馈证据。

实际确定均值响应仍稀疏：WebVid每200次更新仅12–20次改变全池命中，Yandex仅1–3次。八模型末点完整训练池均为净正值，但WebVid RL第二seed后期monitor退到−0.1660pp，ES两seed选中monitor均0，说明训练机会与新query收益没有稳定转化。不能把非零reward或看见更多候选收益直接当作泛化成功。

RL的局部正值必须单独保留：WebVid选中两seed monitor +0.0781/+0.0098pp，Yandex为0/+0.0781pp；RL这个arm在两集均有正候选。原预锁门要求每个数据集的RL和ES都至少一个seed正增量，因WebVid ES失败而未过，按协议停止本完整反馈版本的预算扩展。这个统一门的失败不能抹掉RL双集信号，也不能反过来改写为统一门通过。Yandex ES第二seed +0.0586pp同样保留；尚无独立开发或Recall–QPS证据。
'''
next_text='''接着执行E48评分/邻接2×2，直接回答原有动作的跨query收益损伤来自共享评分方向还是普通HNSW重建的干扰：固定E44全部20状态/八方向，补齐(Wa,Gc)/(Wc,Ga)，真实路由全池并精确补测变化query，不增加训练epoch或幅度。源码和协议已准备，当前尚未编译或查询。

之后另立“冻结RL候选能否保留双集增量”的独立对照问题，考虑用既有隔离cal/audit和原单线程静态评测器验证完整Recall–QPS。它不复活E47的统一训练门、不重训或按新结果改模型；所有候选/选择规则/预算在查询前另冻，当前无新cal/audit。用户要求大胆假设、小心证明，因此继续验证已有具体信号，不把自设统一门变成放弃所有局部结果的理由。'''
body=f'''# E47 局部画像完整反馈RL/ES

2026-09-12，`{status}`，统一门`{gate['status']}`。八次真实训练完成，RL双集局部信号保留，统一稳定性门停止扩展预算。

{tab}
{core}
## 方法与真实成本

原E43 P/B/H/单行H×16参数、两arm双seed/σ.3/200步/Adam/GT无关hub与ε日程保持；只把奖励query覆盖改为完整4096。候选以及每次确定均值更新都真实build/route4096、仅三入口变化补测原NSG，其他完整返回按同query/原NSG/L/K/metric键复用。全部route NDC更新，当前缓存随均值更新替换；80次缓存换父/no-op/回退及效用恒等预检通过。

冷启动每run实际run4096；monitor1024每20步实际查询，train512从当时完整缓存提取。完整checkpoint保存全W/系数/动量/计数以及train4096+monitor1024返回；选中非零checkpoint规则与E43相同，selected/last输出静态W与普通HNSW。线上仍一次HNSW→三个真实入口→原NSG，没有在线策略模型。

实际228832 NSG=125952固定冷启动/monitor/parity+101961候选补测+919均值补测；HNSW59107328、普通构图14424、optimizer1600。候选逻辑反馈52428800行、均值逻辑6553600行，与真实新增搜索分开。完整预留800000，未释放失败预算；本阶段无失败job。两query进程710.011/550.973s，累计1260.983s（约21.0分钟），CPU15实际进程/OMP/BLAS/MKL1、串行；含加载/路由/构图/评分/写盘/验收，不是线上QPS，也不是与E43的独立重复速度对照。

## 独立核验

重放12800候选与1600确定均值的完整缓存、路由entries/cache hash及所有变化patch，独立集合评分586208返回（含102880新patch、32768冷启动和450560 checkpoint行），核验12800候选W身份、1600四分量梯度/Adam、88全量checkpoint、16导出和1024条三路parity。均值逐step命中变化累加逐query等于最终完整训练池差，源/输入/原E37–E46与native/NSG SHA保持；核验45.448s，无新搜索。

所有新结果都来自历史train/monitor，monitor选择checkpoint，不是盲测/泛化结论。0新GT/cal/audit/validation/held-out/QPS，默认保持WebVid GT10-soft-t1 / Yandex GT10-hard。E43原ES正值和E44分层失败不覆盖。

## 接续

{next_text}

[协议](protocol.md)、[模型表](results/models.csv)、[完整质量](results/quality.csv)、[反馈](results/feedback.csv)、[逐步](results/steps.csv)、[原门](results/method_gate.json)、[成本](results/cost.json)、[独立审计](reviews/training_verification.json)、[图](figures/full_feedback_learning.svg)。
'''
(O/'report.md').write_text(body);(O/'conclusion.md').write_text(core+'\n'+next_text+'\n')
hist=body.replace('# E47 局部画像完整反馈RL/ES','# 36. E47 局部画像完整反馈RL/ES');hist=re.sub(r'\]\(([^)]+)\)',lambda m:'](../entry_method_exploration/20260912_full_feedback_profile_rl_v1/'+m.group(1)+')',hist);(R/'experiment_history/36_full_feedback_profile_rl.md').write_text(hist)
p=R/'s-experiment.md';s=p.read_text();i=s.index('| E46 完整三入口精确反馈复用');s=s[:i]+'| E47 局部画像完整反馈训练 | 同局部表示/σ/步数/两臂双seed，完整4096反馈与逐均值精确缓存 | `COMPLETE_FULL_FEEDBACK_PROFILE_RL_LOCAL_RL_SIGNAL_AGGREGATE_GATE_STOP`；RL双集有选中正值，WebVid ES未过统一门；228832 NSG/1600更新完成 | [36 完整反馈训练](experiment_history/36_full_feedback_profile_rl.md) |\n'+s[i:];s=s.replace('三十五份详细卡片','三十六份详细卡片');p.write_text(s)
p=R/'experiment_history/README.md';s=p.read_text();s+='\n- [36 完整反馈RL/ES](36_full_feedback_profile_rl.md)：E47完成八训练，保留RL双集局部信号；统一门因WebVid ES失败停止预算扩展。\n';p.write_text(s)
(R/'summary.md').write_text(f'''# ACSG 当前结果摘要

2026-09-12，最近完成E47，`{status}`。[报告](entry_method_exploration/20260912_full_feedback_profile_rl_v1/report.md)、[历史36](experiment_history/36_full_feedback_profile_rl.md)、[审计](entry_method_exploration/20260912_full_feedback_profile_rl_v1/reviews/training_verification.json)。用户20:00持续研究目标继续，默认保持WebVid GT10-soft-t1 / Yandex GT10-hard。

{tab}
{core}
实际228832 NSG、59107328 HNSW、14424普通构图、1600更新，累计训练进程1260.983s。精确复用保持完整反馈，0新GT/开发/QPS；完整重放586208集合评分、12800候选W、88 checkpoint、16导出与1024parity通过，E37–E46保护。当前最近完整Recall–QPS仍E37。

{next_text} 详细接续见[s-target](s-target.md)。
''')
(R/'s-target.md').write_text(f'''# ACSG 下一阶段目标与接续

2026-09-12，E47八次训练及独立重放完成，[历史36](experiment_history/36_full_feedback_profile_rl.md)。用户要求大胆假设、小心证明并持续至20:00，总目标继续。

## 保留信号与停止范围

RL选中monitor WebVid +0.0781/+0.0098pp、Yandex0/+0.0781pp，双集有局部正值。E47统一门还要求ES双集正值，WebVid ES均0而失败，停止该版本训练预算扩展；不得把统一门改判通过或因此抹掉RL信号。完整质量反馈已从WebVid每200步13–18/Yandex3–7变为133–145/74–85，但确定均值仅12–20/1–3步改命中；状态随训练分岔，固定采样效应仍引用E44。

{next_text}

## E48预锁因果控制，执行准备中

[独立协议](entry_method_exploration/20260912_score_topology_factorial_v1/protocol.md)固定E44原全部20 context/160动作。C=(Wc,Gc)、A=(Wa,Ga)完整恢复；新增S=(Wa,Gc)、T=(Wc,Ga)。完整验证同H/映射/层级/入口/maxlevel/degree后安装有序邻接，原画像bytes由native逐行核验，不改变原路由/NSG。全池真实route，入口变化新NSG，不变部分按合法键精确复用；未知S/T不填0。

预计500状态、340普通build、320实际+20no-op拓扑安装、2051200 HNSW；每集NSG完整预留30000/总60000，100代表物理图×16query三路parity。逐query四格交互/条件边际、G/L/有限动作收益覆盖和最佳动作损伤分别核验。若S/T某因素在双集均保留≥75%A累计gain且loss≤50%，有限最佳净值不低于A并有正收益，才考虑独立单因素训练；否则保留混合机制，不能事后挑query/幅度救门。

## 冻结RL模型的后继问题

E47统一门衡量两估计器共同受益，不能代替“RL候选能否泛化”的独立问题。后继拟固定所有已选模型并以现有隔离cal/audit作同批原生对照，RL/ES作为真实对照都保留，先验证fit位级一致再按预锁cal规则选seed。若测wall，必须独立单线程五L/五轮实际Recall–QPS，不新增validation/held-out或改模型。这是新问题的固定模型验证，不是重启E47训练；当前尚未执行。

19:35停止训练、19:40停止新查询、20:00收口；所有旧资产和默认保持。E47两dataset handle均已采集exit0，无遗留训练进程。先完成已有E48源码的编译/身份恢复与缺失反事实测量，再按时间推进固定模型验证。
''')
p=R/'spec.md';s=p.read_text().replace('E46精确反馈复用已验收','E47完整反馈训练已验收').replace('## 局部画像完整训练池反馈（E47，训练进行中）','## 局部画像完整训练池反馈（E47，已验收）').replace('当前训练尚未完成，效果/审计状态由summary维护，无新开发/GT/QPS。','八次训练已完成，效果/审计状态由summary维护，无新开发/GT/QPS。');s+='\nE47 [audit_training.py](entry_method_exploration/20260912_full_feedback_profile_rl_v1/src/audit_training.py)独立重放12800候选/1600均值缓存，586208集合评分、全部路由hash/复用键、四梯度分量/Adam/候选画像/88 checkpoint/16导出及1024parity通过；逐query更新命中差与最终状态守恒。实际228832 NSG/59107328 HNSW/14424build/1600更新，逻辑反馈与真实新增调用分账。[summarize.py](entry_method_exploration/20260912_full_feedback_profile_rl_v1/src/summarize.py)保持原统一门及逐arm结果，停止预算扩展不自动否认RL局部正值；后继评分/拓扑installer和冻结模型评测尚未执行。\n';p.write_text(s)
dump(O/'reviews/visual_review.json',dict(status='PASS',files=['figures/full_feedback_learning.png'],method='Viewed rendered learning curves and E43/E47 comparison; selected/last distinctions readable'))
dump(O/'state.json',dict(status=status,gate=gate['status'],NSG_calls=228832,HNSW_calls=59107328,builds=14424,optimizer_updates=1600,campaign_complete=False))
roots=[R/x for x in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md','experiment_history/36_full_feedback_profile_rl.md']];links=0
for p in roots+[O/'report.md',O/'protocol.md']:
 for link in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if '://' in link or link.startswith('#'):continue
  assert (p.parent/link.split('#')[0]).exists(),(p,link);links+=1
for p in files(O/'src'):
 if p.suffix=='.py':ast.parse(p.read_text(),filename=str(p))
jobs=read(O/'logs/jobs.json');assert len(jobs)==8 and all(x['status']=='COMPLETE' for x in jobs);assert sum(x['actual'] for x in jobs)==228832
rec=dict(status='PASS',NSG_calls=228832,HNSW_calls=59107328,builds=14424,optimizer_updates=1600,protected_files=len(read(O/'reviews/protected.json')['files']),local_links=links,
 artifact_bytes=sum(x.stat().st_size for x in files(O)),independent_verification=read(O/'reviews/training_verification.json'),campaign_complete=False,seconds=time.monotonic()-started)
dump(O/'reviews/final_audit.json',rec);dump(O/'reviews/completion_audit.json',dict(status='PASS',stage_complete=True,campaign_complete=False,next='Score/topology factorial, then separate frozen RL candidate verification'))
freeze(O/'reviews/final_artifact_freeze.json',files(O)+roots);print(json.dumps(rec,indent=2),flush=True)
