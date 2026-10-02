from pathlib import Path
import json,csv,hashlib,shutil,time,os,re
ROOT=Path('/data/netg/ACSG');TB=Path(__file__).resolve().parents[1];R=TB/'stages/e112_one_hop_hub_design'
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(16<<20),b''):h.update(b)
 return h.hexdigest()
def ident(p):p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
assert not (R/'complete.json').exists()
cfg=read(R/'config.locked.json');gate=read(R/'results/gate.json');numeric=read(R/'reviews/numeric_verification.json');jobs=read(R/'reviews/jobs.json')
assert gate['status']=='STOP_ONE_HOP_H_DESIGN_INFORMATION_GATE' and numeric['status']=='PASS'
verified={}
for name in ['setup_freeze.json','search_source_freeze.json','hub_freeze.json']:
 for x in read(R/'reviews'/name)['files']:assert sha(x['path'])==x['sha256'];verified[x['path']]=x['sha256']
for x in read(R/'reviews/protected_before.json')+numeric['raw_files']:
 assert sha(x['path'])==x['sha256'];verified[x['path']]=x['sha256']
for name in ['analysis_lock.json','analysis_v2_lock.json','analysis_v3_lock.json']:
 x=read(R/'reviews'/name)['source'];assert sha(x['path'])==x['sha256'];verified[x['path']]=x['sha256']
for folder in ['analysis_serialization_failure','analysis_serialization_failure_v2']:
 for x in read(R/'reviews'/folder/'review.json')['files']:
  assert sha(x['snapshot'])==x['sha256']
  if x['path'].endswith('.csv'):assert sha(x['path'])==x['sha256']
for c in cfg['datasets'].values():
 stat=Path(c['index']).stat();assert stat.st_size==c['index_stat']['bytes'] and stat.st_mtime_ns==c['index_stat']['mtime_ns']
for j in jobs:assert j['exit_code']==0 and not Path('/proc',str(j['pid'])).exists()
before=R/'reviews/document_before';before.mkdir();docs=['summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md'];snap=[]
for rel in docs:
 p=ROOT/rel;out=before/rel;out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,out);snap.append(dict(**ident(p),snapshot=str(out)))
dump(R/'reviews/document_before.json',snap)
tables={name:list(csv.DictReader((R/'results'/name).open())) for name in ['certificate_coverage.csv','paired_information.csv','conditional_rescue.csv','selected_H_support.csv']}
coverage=tables['certificate_coverage.csv'];pairs=tables['paired_information.csv']
rows=[]
for ds in cfg['datasets']:
 for method in cfg['methods']:
  a=next(x for x in coverage if x['dataset']==ds and x['role']=='QGT' and x['method']==method);b=next(x for x in coverage if x['dataset']==ds and x['role']=='development' and x['method']==method)
  rows.append('| '+('WebVid' if ds.startswith('web') else 'Yandex')+f" | {method} | {float(a['F_mean_pct']):.4f} | {float(b['F_mean_pct']):.4f} | {float(b['GT1_any_pct']):.4f} | {float(b['GT100_max_pct']):.4f} |")
pairrows=['| '+('WebVid' if x['dataset'].startswith('web') else 'Yandex')+f" | GraphH − {x['control']} | {float(x['mean_F_delta_pp']):+.4f} | [{float(x['CI_lower_pp']):+.4f}, {float(x['CI_upper_pp']):+.4f}] |" for x in pairs]
label_seconds=sum(j['seconds'] for j in jobs if j['kind']!='compile');compile_seconds=sum(j['seconds'] for j in jobs if j['kind']=='compile');maxrss=max(j.get('complete',{}).get('maxrss_kib',0) for j in jobs)/1024**2
report='''# E112：首行覆盖入口设计的理论信息门

2026-09-20。**STOP_ONE_HOP_H_DESIGN_INFORMATION_GATE**：WebVid通过预锁信息门，Yandex三个条件全部失败，按跨数据集协议停止本版H设计，不训练画像或执行真实搜索。Web GT10-soft-t1、Yandex GT10-hard及生产E99保持；这不是新部署Recall/QPS结果。

## 推导与唯一干预

单入口h首先完整展开闭出邻域D(h)={h}∪N_out(h)。在L≥K、GT与搜索距离及并列语义一致的条件下，D(h)中的GT_K成员会保留到最终返回。因此c_K=|GT_K∩D(h)|/K是条件下界。指定GT1 ID另需严格第一名或一致并列规则；这里用原DC检查GT1/GT2，非严格query只将K1证书置0，全部query及原GT/Recall保留。GT100外部排名/浮点一致性仍是前提，未新增GT101验证。

用等K分数c=(c_1+c_100)/2定义F(H)=平均_q max_h c(q,h)。它是标准单调次模目标；精确最大边际贪心有1−1/e近似保证。这个保证只约束QGT训练目标，不保证开发覆盖、真实搜索或可部署路由。候选遍历全部真实base节点，在与原QGT-Cover相同的QGT5K、相同H815/821、同一底层NSG下选择GraphH。OriginalH与同QGT的GT1频率FrequencyH是固定控制。

[完整推导及前作](research.md) · [冻结协议](protocol.md) · [配置](config.locked.json)。E111固定旧H的排名核心证书已停止；本版改变H、只用首行邻居，没有扩大m/路径网格。H在本runner读取开发载荷前冻结；开发4096/集此前已曝光，不是新盲测或held-out。

## 实际覆盖及门槛

数值均为百分数，F是知道GT后在H中选择的条件覆盖。GT1_any与GT100_max分别取各自最优入口，二者均值不必等于同一入口的F。

| 数据 | H选择 | QGT F | 开发F | 开发GT1存在覆盖 | 开发GT100最大覆盖 |
|---|---|---:|---:|---:|---:|
'''+ '\n'.join(rows)+'''

| 数据 | 开发配对对比 | F变化pp | 98.75% bootstrap区间 |
|---|---|---:|---:|
'''+ '\n'.join(pairrows)+'''

Web GraphH在默认L128的1011条K1失败query中有96条条件可恢复，占全4096条的2.3438pp；旧H51条、频率H75条。Yandex默认384条失败中GraphH与旧H均0条，频率H1条。这里假定免费知道何时保留默认、何时改用证书入口，属于特权条件恢复量，不是执行过的Recall增益。

预锁门要求两集F相对旧H≥2pp、四个对比区间下界均>0、对默认失败的条件恢复量≥1pp。Web全过，Y全不过，因此整体停止。不能依据Web局部信号改为单数据集继续，或降低Y门槛。

## 这次解释了什么

GraphH的训练收益主要来自真实出边，不能简单归因于把热门GT1放进H：Web的开发非自节点GT1覆盖16.5771%，自节点2.4658%；Y相应1.0010%与0.0488%。GraphH与旧H重叠仅38/815、20/821，QGT至少两个query提供GT1证书，但每hub中位数只有2条。Y训练F17.6002%下降到开发0.8004%，连很保守的实际目标覆盖也难延续。

这支持“精确目标ID的首行覆盖在当前Y数据/样本/容量下信息不足”，不证明整个图无可迁移结构，也不证明所有H选择失败。稀疏支持、选择偏差、目标分布变化可能共同作用；本阶段未分离各自因果份额。GT10仍可通过多行搜索获得很高Recall，不能把小的局部下界误作真实效用上界。后继回到数据分布、有限beam动作稳定性和学习目标的理论审查，不扩本版H/m/跳数/seed/预测器。

## 核验、成本与修正

'''+f'''全部稀疏行顺序/范围及整数分数组合核验；{numeric['greedy_prefix_checks']}步贪心前缀回放和全局边际上界检查；独立预定64条query/角色/集×所有H，共{numeric['independent_membership_checks']}组成员核验。QGT稀疏/稠密分数逐元素相等。0新NSG、ANN、GT、底层图、路由图或梯度/画像训练；有新图派生标签和离线H优化。四个标签进程含加载合计{label_seconds:.3f}秒，编译{compile_seconds:.3f}秒，最大RSS{maxrss:.3f}GiB；不当作QPS。

分析两次因NumPy布尔值JSON序列化失败；初次修正遗漏另一条件，第二次补齐。原源码、日志、四张CSV与两次修正记录均保留；第三版仅转为Python bool，全部CSV SHA相同，门槛/样本/数值未改。首次读取新质量结果发生在最终分析完成后，失败时只查看traceback与源码。最终独立分析耗时{read(R/'reviews/analysis_complete.json')['seconds']:.3f}秒；失败分析日志时间单列，不隐去。图已目视检查。

'''+'''[覆盖表](results/certificate_coverage.csv) · [配对区间](results/paired_information.csv) · [条件恢复](results/conditional_rescue.csv) · [支持量](results/selected_H_support.csv) · [门](results/gate.json) · [图](figures/conditional_coverage.png) · [数值核验](reviews/numeric_verification.json) · [执行成本](reviews/jobs.json) · [第一次分析失败](reviews/analysis_serialization_failure/review.json) · [第二次分析失败](reviews/analysis_serialization_failure_v2/review.json) · [完成审计](reviews/completion_audit.json)。
'''
(R/'report.md').write_text(report)
history=ROOT/'experiment_history/108_one_hop_hub_design.md';assert not history.exists()
history.write_text('''# 108｜E112首行覆盖入口设计

2026-09-20。由单入口首行发现的条件Recall下界推导固定H容量的次模覆盖目标；同原独立QGT5K、H815/821、原底层NSG，比较全base贪心GraphH、原H及GT1频率H。先冻结两集H，再由runner读取完整曝光开发4096/集；不是新盲测。

开发F相对旧H：Web+4.0505pp，98.75%区间[+3.3158,+4.8103]；Y+0.1404pp，区间[−0.0996,+0.3916]。相对频率H：Web+2.2653pp区间正，Y+0.1829pp区间跨0。默认L128失败的条件GT1恢复量Web96/4096=2.3438pp，Y0。Web通过全部信息条件，Y全部失败，整体STOP_ONE_HOP_H_DESIGN_INFORMATION_GATE；不选单集继续、不扩H/跳数/seed/模型。

F是特权条件下界，贪心近似保证仅是标准次模结论，不是新理论、泛化保证或实测Recall。GT1严格性与GT100外部排名条件明确，未改GT/Recall或删query。GraphH中位GT1支持仅2条/入口，Y训练F17.6002%→开发0.8004%；支持稀疏/局部覆盖迁移不足，不等于所有图学习无效。

0新NSG/ANN/GT/图/梯度及画像训练；有新标签与H离线优化。四标签进程49.734秒、编译8.679秒、最大RSS10.169GiB。两次分析布尔序列化错误及修正完整保留，最终CSV逐字相同；独立成员及贪心/来源核验通过，图已检查。原Web soft/Y hard及生产E99保持，整体研究目标仍持续至19:00。

[完整报告](../entry_method_exploration/20260920_until1900_theory_v1/stages/e112_one_hop_hub_design/report.md) · [冻结协议](../entry_method_exploration/20260920_until1900_theory_v1/stages/e112_one_hop_hub_design/protocol.md) · [原始门](../entry_method_exploration/20260920_until1900_theory_v1/stages/e112_one_hop_hub_design/results/gate.json)。
''')
def prepend(rel,prefix,replace=False):
 p=ROOT/rel;s=p.read_text();head,rest=s.split('\n\n',1)
 if replace:rest=rest.split('\n\n',1)[1]
 p.write_text(head+'\n\n'+prefix+'\n\n'+rest)
prepend('s-experiment.md','2026-09-20 **E112首行覆盖H信息门完成并停止**：同QGT/H预算，Web开发覆盖相对旧H+4.0505pp、频率H+2.2653pp，区间均正；Y仅+0.1404/+0.1829pp、区间跨0，默认失败条件恢复为0。0新搜索/图/GT/画像训练，有图派生标签与离线H选择；默认保持。[记录108](experiment_history/108_one_hop_hub_design.md)。')
p=ROOT/'experiment_history/README.md';s=p.read_text();needle='|---|---|\n';assert needle in s;s=s.replace(needle,needle+'| [108 首行覆盖H设计](108_one_hop_hub_design.md) | E112：标准次模目标的信息门；Web局部通过、Y覆盖/恢复不足，0新搜索，停止本版 |\n',1);p.write_text(s)
prepend('summary.md','2026-09-20 **E112首行覆盖H设计完成，STOP_ONE_HOP_H_DESIGN_INFORMATION_GATE**。同QGT5K/H815或821/原底图，GraphH开发覆盖F相对旧H为Web+4.0505pp（98.75%区间[+3.3158,+4.8103]）、Y+0.1404pp（[−0.0996,+0.3916]）；相对频率控制Web区间正、Y跨0。默认L128失败的条件恢复Web2.3438pp、Y0，跨集门失败。F为特权条件下界，未执行新Recall/QPS；0新NSG/ANN/GT/图/梯度或画像训练，有图标签与离线H优化，约49.7秒标签进程。两个序列化错误及机械修正保留、CSV一致、数值/身份/图验收通过。停止本版H/跳数/seed/模型扩展，原默认与生产E99保持，整体研究继续至19:00。[报告](entry_method_exploration/20260920_until1900_theory_v1/stages/e112_one_hop_hub_design/report.md) · [记录108](experiment_history/108_one_hop_hub_design.md)。',True)
prepend('spec.md','2026-09-20 E112独立[首行覆盖工具](entry_method_exploration/20260920_until1900_theory_v1/stages/e112_one_hop_hub_design/src/design.cpp)已执行验收：QGT100倒排、全base闭邻域稀疏整数分数、lazy最大边际贪心、原H与频率H控制；原DC检查GT1/GT2，独立成员核验与贪心回放通过。三版分析及两次布尔序列化修正保留，CSV一致。标签不是搜索/GT/画像训练，0新NSG或图；信息门停止，生产API、原指标、底图和默认保持。[报告/契约](entry_method_exploration/20260920_until1900_theory_v1/stages/e112_one_hop_hub_design/report.md)。',True)
p=ROOT/'s-target.md';s=p.read_text();s=s.replace('当前先审查更充分的图条件及其与既有BTG/Atlas/效用画像的区别，未启动新模型或搜索。','E112首行覆盖H信息门已完成并停止：Web通过、Y开发覆盖与失败恢复不足，0新搜索/画像训练。后继审查局部标签支持、分布迁移与有限beam动作稳定性；不扩本版H/跳数/seed或转选单集训练。');s=s.replace('E111当前m64/100证书均按门停止','E111当前m64/100证书及E112首行H设计均按门停止');p.write_text(s)
dump(R/'reviews/visual_inspection.json',dict(status='PASS',figure=ident(R/'figures/conditional_coverage.png'),labels_readable=True,no_clipping=True,scope='Conditional coverage rather than deployed Recall'))
dump(R/'reviews/cost_ledger.json',dict(NSG_calls=0,ANN_calls=0,new_GT=0,new_graphs=0,gradient_or_profile_training=0,new_graph_derived_labels=True,new_offline_H_optimization=True,label_process_seconds_including_load=label_seconds,compile_seconds=compile_seconds,max_rss_gib=maxrss,analysis_success_seconds=read(R/'reviews/analysis_complete.json')['seconds'],analysis_failures=[dict(version=v,elapsed_file_clock_seconds=(R/'logs'/log).stat().st_mtime-read(R/'reviews'/lock)['created_unix'],exact_process_wall_available=False) for v,log,lock in [(1,'analysis.log','analysis_lock.json'),(2,'analysis_v2.log','analysis_v2_lock.json')]]))
dump(R/'reviews/document_after.json',[ident(ROOT/rel) for rel in docs]+[ident(history)])
links=0
for p in [R/'report.md',history]+[ROOT/d for d in docs]:
 for dest in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if '://' in dest or dest.startswith('#'):continue
  target=(p.parent/dest.split('#')[0]).resolve()
  if target==R/'reviews/completion_audit.json':continue
  assert target.exists(),(p,dest);links+=1
dump(R/'reviews/completion_audit.json',dict(status='PASS',verified_files=len(verified),all_source_and_raw_identities_retained=True,all_5_owned_jobs_closed=True,all_analysis_versions_closed=True,serialization_repair_CSV_identity=True,all_queries_retained=True,local_links_checked=links,report=ident(R/'report.md'),default_changed=False,overall_goal_complete=False))
dump(R/'state.json',dict(status='COMPLETE',decision=gate['status'],pending=[],default_changed=False))
dump(R/'complete.json',dict(status='COMPLETE',decision=gate['status'],completed_unix=time.time(),NSG_calls=0,ANN_calls=0,report=ident(R/'report.md'),audit=ident(R/'reviews/completion_audit.json')))
dump(TB/'state.json',dict(status='ACTIVE_THEORY_RESEARCH',stage='E112 closed; reassess support and finite-beam stability',deadline_unix=1789902000,completed_NSG_calls=0,synthetic_calls=0,active_stage_reserved_NSG_calls=0,pending=['theory/method decision','19:00 closeout']))
print(json.dumps(read(R/'reviews/completion_audit.json'),ensure_ascii=False,indent=2))
