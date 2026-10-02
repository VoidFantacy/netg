from shared import *
import re,ast
threads(8);resources();started=time.monotonic();check(O/'reviews/prequery_freeze.json');check(O/'reviews/protected.json');check(O/'reviews/native_dependencies.json')
v=read(O/'reviews/verification.json');assert v['status']=='PASS';gate=read(O/'results/gate.json');cost=read(O/'results/cost.json')
assert cost['NSG_calls']==7525 and gate['qualifying_factors']==[]
status='COMPLETE_SCORE_TOPOLOGY_FACTORIAL_MIXED_MECHANISM'
tab='| 数据集 | 四格因素 | 累计gain/loss/net hits | 最佳静态净值 | 逐query上界 | 未覆盖/自身损伤差额 |\n|---|---|---:|---:|---:|---:|\n'
for ds in gate['datasets']:
 for f,label in [('A','A 评分+邻接'),('S','S 只评分'),('T','T 只邻接')]:
  x=ds[f];tab+=f'| {"WebVid" if ds["dataset"]==DS[0] else "Yandex"} | {label} | {x["gain_hits"]}/{x["loss_hits"]}/{x["net_hits"]:+d} | {x["best_net_hits"]} | {x["oracle_hits"]} | {x["uncovered_oracle_hits"]}/{x["own_loss_gap"]} |\n'
core='''已有动作的收益损伤不能统一归因于共享画像评分，也不能统一归因于HNSW重建。WebVid只邻接保留143 gain但带152 loss；只评分61/69，二者都有跨query冲突。Yandex只评分49/78，占主要质量响应；只邻接15/16，主要在目标hub原入口补集。固定拓扑没有清掉Yandex损伤，固定评分也没有保住其主要收益。两因素均未过预锁的双集“保留≥75%gain、loss≤50%、最佳静态净值不减”接续门，因此不直接启动单因素训练或扫幅度。

动作逐query完整响应分类更具体：WebVid80动作中32全质量空、6评分独立充分且邻接空、22邻接独立充分且评分空、1只有联合才有响应、19混合；9动作有非零交互，交互绝对命中差合计44。Yandex分别62空、8评分充分、4邻接充分、6混合；5动作非零交互，绝对差18。这里“充分”只指该动作固定背景下完整命中向量恢复，不是机制唯一归因；交互不能独占计给任何一方。

用户问的两种瓶颈都有，但数据集不同。原A的有限动作集，WebVid九个有响应状态合计oracle63、最佳静态35，差28分成未覆盖24和最佳动作自身损伤4；23/80动作同时增益和损伤，真实冲突存在，但有限方向覆盖不足更占这个差额。Yandex仅3/10状态有质量机会，而原A的oracle与最佳静态都26，存在无损动作完整取得本批观察到的收益；因此这批状态的主要证据是机会稀疏，并非必须牺牲其他query。不能由八个有限方向外推整个表示空间小，也不能把不同状态的最佳动作拼作一份可部署模型。
'''
next_text='''下一问题转向E47已冻结RL候选的独立静态评测：RL在两集monitor有局部正值，保留该信号；原E47整体门因WebVid ES失败仍保持STOP，不扩训练预算。固定两arm双seed选中模型，先fit逐位恢复，再用既有隔离cal选seed、audit验证，并实测单线程五L/五轮完整Recall–QPS。当前E49尚未查询；所有选择规则/预算另冻，不用新开发结果调整画像。19:40停止新查询，20:00完成研究收口。'''
body=f'''# E48 画像评分与HNSW邻接的四格因果控制

2026-09-12，`{status}`，接续门`{gate['status']}`。原E44全部20状态/160原动作，完整train4096，无优化更新。

{tab}
以上是各状态/动作诊断总和，不是Recall收益或一份模型。

{core}
## 实际控制与计量

C=(Wc,Gc)、A=(Wa,Ga)逐位恢复旧端点；S=(Wa,Gc)、T=(Wc,Ga)为补测物理干预。安装器先完整验证同H/ID/层级/入口/maxlevel/合法有序邻接及容量，才修改邻接；native逐行memcmp画像bytes，状态全拓扑SHA对应冻结来源。20同拓扑no-op与8非法拓扑无副作用拒绝通过。S/T不要求是普通builder单独可生成的图，只作机制控制。

全500状态真实route4096；相同query和完整有序三入口键精确复用对应C的NSG返回，变化者全部新NSG，当次route NDC保留。实际NSG7525=2725变化query+4800三路parity，其中原C/A补测1333、S/T补测1392；旧C种子81920历史成本分账。HNSW2051200，340普通构图、320干预+20no-op安装。WebVid/Yandex进程28.588/30.432s，累计59.021s，CPU15实际单线程串行；这包含控制构造等工作，不是线上QPS。

独立集合评分2048000行，737280端点逐位复现、全部缓存键/patch身份、655360逐query交互与四条件边际、500画像/拓扑身份和100代表物理图×16query三路parity通过。0optimizer/新GT/开发/validation/held-out/QPS；源和E37–E47旧资产SHA保持。默认保持WebVid GT10-soft-t1 / Yandex GT10-hard。

## 接续

{next_text}

[协议](protocol.md)、[动作表](results/actions.csv)、[状态上界](results/contexts.csv)、[完整分析](results/analysis.json)、[接续门](results/gate.json)、[成本](results/cost.json)、[独立核验](reviews/verification.json)、[图](figures/factorial_mechanism.svg)。
'''
(O/'report.md').write_text(body);(O/'conclusion.md').write_text(core+'\n'+next_text+'\n')
hist=body.replace('# E48 画像评分与HNSW邻接的四格因果控制','# 37. E48 评分与邻接四格控制');hist=re.sub(r'\]\(([^)]+)\)',lambda m:'](../entry_method_exploration/20260912_score_topology_factorial_v1/'+m.group(1)+')',hist);(R/'experiment_history/37_score_topology_factorial.md').write_text(hist)
p=R/'s-experiment.md';s=p.read_text();i=s.index('| E47 局部画像完整反馈训练');s=s[:i]+'| E48 评分/邻接四格 | 原E44全部20状态/160动作补齐评分独变与拓扑独变 | `COMPLETE_SCORE_TOPOLOGY_FACTORIAL_MIXED_MECHANISM`；WebVid邻接响应更多，Yandex评分更多，两因素均未过单独训练接续门；7525 NSG | [37 四格因果控制](experiment_history/37_score_topology_factorial.md) |\n'+s[i:];p.write_text(s.replace('三十六份详细卡片','三十七份详细卡片'))
p=R/'experiment_history/README.md';p.write_text(p.read_text()+'\n- [37 评分/邻接四格](37_score_topology_factorial.md)：E48完成500状态，区分两集不同机制，保留有限静态机会与冲突。\n')
(R/'summary.md').write_text(f'''# ACSG 当前结果摘要

2026-09-12，最近完成E48，`{status}`。[报告](entry_method_exploration/20260912_score_topology_factorial_v1/report.md)、[历史37](experiment_history/37_score_topology_factorial.md)。

{tab}
{core}
实际7525 NSG/2051200 HNSW/340普通构图/340拓扑安装，500状态，0更新；独立2048000集合评分及655360交互通过。默认保持WebVid GT10-soft-t1 / Yandex GT10-hard，最近完整Recall–QPS仍E37。

E47完整反馈训练已完成，RL双集monitor正候选保留，统一门因WebVid ES失败停止扩展。接着固定模型独立评测，详见[s-target](s-target.md)。用户20:00持续研究目标尚未结束。
''')
(R/'s-target.md').write_text(f'''# ACSG 下一阶段目标与接续

2026-09-12，E48完成并核验，[历史37](experiment_history/37_score_topology_factorial.md)。用户要求大胆假设、小心证明，持续至20:00。

## 当前结论决定的优先级

{core}
## 下一明确问题：冻结RL候选是否保留开发增量

{next_text}

E49拟使用E37原静态无计数wall评测器与全部E47 selected画像/普通HNSW。cal/audit沿用已经隔离的各1024历史开发query，原train/monitor source row IDs逐项排除。每arm按cal平均原U最大、较低total NDC、较小seed选择；选择后冻结再开audit。全部两seed的cal/audit质量保留，不能只报获胜者。fit parity10点、cal10、audit10、frontier50点/250wall，固定NSG/Fast30K/当前GT10/所选RL/所选ES五方法、L64/128/256/400/800。预算预计423680新增NSG、硬限500000，0新训练/GT/validation/held-out；协议准备中，尚未查询。

以配对gain/loss、置信区间和真实同机Recall–QPS共同判断。原E37开发门作为可比门：RL每集cal≥+0.1pp、audit>0，且两split total NDC≤+1%；门失败不抹掉局部正值，门通过也不自动成为部署或正式GO。若无泛化证据，不继续堆轮数；把“稀疏机会、有限方向覆盖、均值更新跨离散边界困难”作为下一方法问题，需独立协议而非改判旧门。

19:35停止训练、19:40停止新查询、20:00收口。E48两query进程均exit0并采集，无遗留查询进程。
''')
p=R/'spec.md';s=p.read_text();s+='''
## 画像评分/邻接四格（E48，已实现并验收）

[factorial_environment.cpp](entry_method_exploration/20260912_score_topology_factorial_v1/src/factorial_environment.cpp)包含已验E46精确反馈wrapper与原E37环境，增加`e48_install`两阶段拓扑验证/安装、`e48_installations`计数及`e48_verify_vectors`实际图画像全bytes校验。H/ID/层级/入口/maxlevel不变，完整有序邻接独立可换；预检失败不得部分写图。S=(Wa,Gc)/T=(Wc,Ga)只作因果控制，不能冒充普通builder输出。

[run.py](entry_method_exploration/20260912_score_topology_factorial_v1/src/run.py)固定E44所有状态/动作，真实全池route和合法三入口缓存；`raw.npz/topology.npz/patch.npz/identity.json`保留每状态，首末context物理图及三路parity。500状态/340build/340安装，7525 NSG/2051200 HNSW；独立[verify.py](entry_method_exploration/20260912_score_topology_factorial_v1/src/verify.py)全2048000集合评分、737280端点位恢复、655360交互及1600三路parity通过。原NSG/metric/GT/线上路由不变，结果由summary维护。冻结模型E49评测仍在准备中。
''';p.write_text(s)
dump(O/'reviews/visual_review.json',dict(status='PASS',file='figures/factorial_mechanism.png',method='Rendered chart viewed; gained/lost hits and finite-action oracle decomposition legible'))
dump(O/'state.json',dict(status=status,gate=gate['status'],NSG_calls=7525,optimizer_updates=0,campaign_complete=False))
roots=[R/x for x in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md','experiment_history/37_score_topology_factorial.md']];links=0
for p in roots+[O/'report.md',O/'protocol.md']:
 for link in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if '://' in link or link.startswith('#'):continue
  assert (p.parent/link.split('#')[0]).exists(),(p,link);links+=1
for p in files(O/'src'):
 if p.suffix=='.py':ast.parse(p.read_text(),filename=str(p))
dump(O/'reviews/final_audit.json',dict(status='PASS',protected_files=len(read(O/'reviews/protected.json')['files']),local_links=links,artifact_bytes=sum(p.stat().st_size for p in files(O)),verification=v,cost=cost,seconds=time.monotonic()-started))
freeze(O/'reviews/final_artifact_freeze.json',files(O)+roots)
print('E48 FINAL AUDIT PASS',flush=True)
