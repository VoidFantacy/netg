import sys,csv,re,shutil,urllib.parse,ast
from pathlib import Path
RUN=Path(__file__).resolve().parents[1];sys.path.insert(0,str(RUN/'src'))
from common import *
assert not (RUN/'complete.json').exists();protected_check()
gate=read(RUN/'results/gate.json');search=read(RUN/'reviews/search_complete.json');analysis=read(RUN/'reviews/analysis_complete.json');assert gate['status']=='STOP_FIRST_EXPANSION_CANDIDATE' and search['status']==analysis['status']=='PASS'
summary=list(csv.DictReader((RUN/'results/primary_summary.csv').open()));pairs=list(csv.DictReader((RUN/'results/paired.csv').open()));metrics=list(csv.DictReader((RUN/'results/metrics.csv').open()));assert len(summary)==4 and len(pairs)==36 and len(metrics)==54
docs=['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md','experiment_history/105_first_expansion_intervention.md']
for n in docs:p=RUN/'source_before_closeout'/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/n,p)
dump(RUN/'reviews/closeout_before.json',[identity(RUN/'source_before_closeout'/n) for n in docs])
lines=['# E110：首展开顺序有作用，但修复尚未超过单入口','',
'2026-09-20，固定三入口首展开干预完成，**STOP_FIRST_EXPANSION_CANDIDATE**。同样三个GT10精确入口，先展开画像top1一次，可以挽回部分原多入口损失；相对简单单入口则未有稳定新增收益。原默认与生产E99保持，不进入该候选ANN/QPS或强制步数/anchor模型调整。','',
'## 1. 从关联到同集合干预','',
'E107既有全4096行重算发现：GT10从1到3入口，Web47.8516%、Y42.4072%会由其他节点先展开；单位hub分别0%/7.3730%。Web原hub约等范数，单位hub精确top1也就是top3中raw-IP最近者，故初始排序保持；GT画像排序无这个恒等关系。这个诊断本身仅是关联，0新NSG/ANN。','',
'本阶段不选失败query，使用原两集各4096已曝光E105开发query、相同H/GT10/NSG/原raw-IP。新内核保留三入口、visited、初始候选池和L，只先展开画像top1一次，随后游标回0继续原循环。完整K1 L64/128/256/400/800，K100 L128/256/400/800；对照原GT10Exact1和GT10Exact3。','',
'它识别的是这一具体首展开干预的反事实效应，不是把原1→3差异唯一归因为初始排序。即使首节点相同，后续候选池竞争也能造成损伤。','',
'## 2. 冻结主汇总与投入门','',
'先对每K的全部L按query平均，再对两个K等权平均；四项主对照使用固定10000次配对bootstrap、98.75%区间。相同query和不同预算高度相关，未当独立重复。','',
'| 数据 | 控制 | 平均ΔR1 pp | 平均ΔR100 pp | 等K平均Δ pp（98.75%区间） | 平均graph NDC比 |','|---|---|---:|---:|---|---:|']
for x in summary:lines.append(f"| {'WebVid' if x['dataset'].startswith('web') else 'Yandex'} | {x['baseline']} | {float(x['K1_mean_delta_pp']):+.4f} | {float(x['K100_mean_delta_pp']):+.4f} | {float(x['equal_K_mean_delta_pp']):+.4f} [{float(x['CI9875_low']):+.4f}, {float(x['CI9875_high']):+.4f}] | {float(x['mean_graph_NDC_ratio']):.6f} |")
lines += ['', '对原三入口，18个K/L均值16正、2零，Yandex主汇总区间为正；Web主区间仍跨0。对单入口，Web等K平均仅+0.0479pp、Y+0.0016pp，两个区间均跨0，Y K100跨L均值−0.0310pp。两集成本门通过，但质量门失败，不能把修复三入口退化当成比简单单入口更好的方法。','',
'门要求两集每K跨L平均对两个控制均非负，等K平均对两个控制均≥0.10pp且区间下端>0，平均graph NDC≤原3入口1.01倍。未降低门槛；完整负点保留。','',
'## 3. L128实际Recall变化与失败','',
'| 数据 | K | 控制 | ΔR pp | 控制零命中→干预 | 新GT成员 / 丢失GT成员 |','|---|---:|---|---:|---|---|']
for x in pairs:
 if x['L']=='128':lines.append(f"| {'WebVid' if x['dataset'].startswith('web') else 'Yandex'} | {x['K']} | {x['baseline']} | {float(x['delta_recall_pp']):+.4f} | {x['baseline_failed']}→{x['method_failed']} | {x['new_GT_members']} / {x['lost_GT_members']} |")
lines += ['', '真实K100新增与丢失成员按GT ID逐一计算，不用净改善query数冒充成员增损。单点图使用95%描述性区间，投入结论依主汇总门。所有首节点保持组的输出/距离bits/NDC均完全不变，效应来自预定义首节点改变组；没有按效果选择这些组。','',
'## 4. 验证与成本','',
f"真实NSG {search['NSG_calls']:,}次、54方法点，搜索编排{search['seconds']:.2f}秒，分析{analysis['seconds']:.2f}秒。0新GT/图/梯度训练/K10/正式QPS。CPU15/实际线程1，数据/方法串行，完整count/plain一致；两个原控制smoke对链接E99，全量控制恢复E107。实际首展开ID逐query验证，干预与控制同三入口、原首节点保持时no-op、同L K1/K100前缀及NDC均通过。",'',
'第一次编译因旧KernelCall成员指针类型遗漏新增int参数失败，耗时2.02秒，0搜索；前件源/锁/日志/状态保留后只修正签名，方法/门不变。正常运行另有一次成功编译，失败与成功成本分列。该独立内核未进入生产；NDC不是QPS，缓存精确路由亦不是部署性能。','',
'当前研究转向能与实际候选池保留规则连接的可检验充分条件，先量化适用范围，不因强制首节点有局部修复而堆叠更强模型。16:00限时研究继续，E110没有待运行任务。','',
'[协议](protocol.md) · [完整指标](results/metrics.csv) · [36配对](results/paired.csv) · [主汇总](results/primary_summary.csv) · [固定两组](results/first_order_groups.csv) · [图](figures/first_expansion_effect.png) · [门](results/gate.json) · [编译修正](reviews/compile_signature_correction.json) · [验收](reviews/completion_audit.json)。']
(RUN/'report.md').write_text('\n'.join(lines)+'\n');rel='entry_method_exploration/20260920_until1600_theory_v1/stages/e110_first_expansion_intervention'
new=f'2026-09-20 **E110首展开干预完成，STOP_FIRST_EXPANSION_CANDIDATE**。固定同GT10三入口、只让画像top1先展开，18个K/L均值相对原3入口16正/2零；等K主汇总Web+0.1065pp区间跨0，Y+0.1552pp的98.75%区间[+0.0095,+0.3178]。但相对单入口仅+0.0479/+0.0016pp、区间均跨0，Y K100均值为负，两集质量门失败。L128相对3入口R1/R100：Web+0.2197/+0.1096pp，Y+0.3662/+0.1377pp；零命中1008→999、4→2、386→371、24→23。首排序是实际影响因素，不能把修复多入口退化当稳定新方法。442880 NSG/54点、约488秒，0新GT/图/训练/QPS；完整parity与身份验收通过，默认保持。[报告]({rel}/report.md) · [记录105](experiment_history/105_first_expansion_intervention.md)。'
for n,text in [('summary.md',new),('spec.md',f'2026-09-20 E110独立[首展开干预评估器]({rel}/protocol.md)完成验收：编译期ForcePrimary与actual-first记录、保持初始三入口/visited/池，先展开primary一次后游标回0。全54点count/plain、全部原控制E107恢复、控制smoke链接E99、同首节点no-op、K1前缀/NDC及独立评分通过；首次成员指针别名编译修正前件保留。源码/结果/门/报告封存，无生产API变更，0正式QPS，E110无待运行任务。'),('s-experiment.md',f'2026-09-20 **E110首展开干预完成并停止候选**：同三入口先展开画像top1，修复部分原三入口退化，Y主效应区间正；对简单单入口未建稳定收益。442880 NSG/54点、0新GT/图/训练/QPS，默认保持。[记录105](experiment_history/105_first_expansion_intervention.md)。')]:
 p=ROOT/n;head,old,rest=p.read_text().split('\n\n',2);assert 'E110' in old;p.write_text(head+'\n\n'+text+'\n\n'+rest)
p=ROOT/'s-target.md';head,old,rest=p.read_text().split('\n\n',2);assert '当前E110' in old;p.write_text(head+'\n\n'+f'E110已完成并[停止候选]({rel}/report.md)：首展开干预修复部分三入口退化，但对单入口质量门失败，不进入ANN/QPS或anchor/强制步数调参。当前继续推导有限池保留规则下的目标可达充分条件并检验覆盖，尚未训练新目标。保分数同图等价性已排除在线逆变换重复。15:50停止新搜索、16:00交付的活动目标保持。'+'\n\n'+rest)
p=ROOT/'experiment_history/README.md';t=p.read_text().replace('E110执行中：同三入口强制画像top1先展开，检验初始排序机制','E110完成：首排序干预修复部分三入口损失，但未超过单入口，停止候选');p.write_text(t)
history=ROOT/'experiment_history/105_first_expansion_intervention.md';history.write_text('# 105｜E110 固定三入口首展开干预\n\n'+'\n'.join(lines[2:-1])+'\n\n[完整报告](../'+rel+'/report.md) · [协议](../'+rel+'/protocol.md) · [验收](../'+rel+'/reviews/completion_audit.json)。\n')
freeze=read(RUN/'reviews/search_source_freeze.json')['files'];raw=read(RUN/'reviews/numeric_verification.json')['raw_files']
for r in freeze+raw+read(RUN/'reviews/build_source_lock.json')['libraries']+read(RUN/'reviews/setup_freeze.json')['files']:assert sha(r['path'])==r['sha256'],r['path']
r=read(RUN/'reviews/analysis_lock.json')['source'];assert sha(r['path'])==r['sha256']
for p in (RUN/'source_before').rglob('*'):
 if p.is_file():assert sha(p)==sha(RUN.parent/'e109_perfect_proxy_gate/source_after'/p.relative_to(RUN/'source_before'))
jobs=read(RUN/'reviews/jobs.json');assert len(jobs)==5 and all(j['exit_code']==0 for j in jobs) and all(a['finished_unix']<=b['started_unix'] for a,b in zip(jobs,jobs[1:]));assert sum(j['reserved_calls'] for j in jobs)==442880
for j in jobs:
 p=Path('/proc')/str(j['pid'])/'cmdline';assert not p.exists() or str(RUN).encode() not in p.read_bytes()
figs=[identity(RUN/'figures'/('first_expansion_effect.'+ext)) for ext in ['png','pdf']];dump(RUN/'reviews/visual_inspection.json',dict(status='PASS',figures=figs,method='PNG viewed and checked against full pairs; PDF from same figure.'))
links=[]
for p in [ROOT/n for n in docs]+[RUN/'report.md',RUN/'protocol.md']:
 for link in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',p.read_text()):
  t=link.strip().strip('<>')
  if urllib.parse.urlsplit(t).scheme or t.startswith('#'):continue
  q=(p.parent/urllib.parse.unquote(t.split('#')[0])).resolve();assert q.exists() or q==RUN/'reviews/completion_audit.json',(str(p),link);links.append(dict(source=str(p),target=str(q)))
for p in list((RUN/'src').glob('*.py'))+list((RUN/'postprocess').glob('*.py')):ast.parse(p.read_text())
new_bytes=sum(p.stat().st_size for p in RUN.rglob('*') if p.is_file());assert new_bytes<LOCK['max_new_bytes']
state=dict(status='COMPLETE_FIRST_EXPANSION_INTERVENTION_STOP_CANDIDATE',completed_unix=time.time(),pending=[],default_changed=False,timebox_continues=True);dump(RUN/'state.json',state)
after=RUN/'source_after';after.mkdir()
for n in docs:p=after/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/n,p)
dump(RUN/'reviews/document_checks.json',dict(status='PASS',documents=[identity(ROOT/n) for n in docs],links=links))
audit=dict(status='PASS_STAGE_COMPLETE',state=state,NSG_calls=442880,points=54,pairs=36,primary_summaries=4,protected_SHA_files=len(read(RUN/'reviews/protected_before.json')),NSG_stat_checks=2,frozen_files=len(freeze),raw_files=len(raw),new_GT=0,new_graphs=0,new_training=0,new_QPS=False,search_seconds=search['seconds'],failed_compile_seconds=read(RUN/'reviews/compile_signature_correction.json')['failed_compile_seconds'],max_rss_gib=max(j.get('complete',{}).get('maxrss_kib',0) for j in jobs)/1024**2,new_bytes=new_bytes,local_links=len(links),report=identity(RUN/'report.md'),source=identity(Path(__file__)))
dump(RUN/'reviews/completion_audit.json',audit);assert all(Path(x['target']).exists() for x in links);dump(RUN/'complete.json',dict(status='COMPLETE',audit=identity(RUN/'reviews/completion_audit.json'),report=identity(RUN/'report.md')))
parent=read(TB/'state.json');assert parent['completed_NSG_calls']==2354176;parent.update(stage='E110 complete; derive candidate-retention reachability conditions',completed_stages=['E107','E108','E109','E110'],completed_NSG_calls=2797056,active_stage_reserved_NSG_calls=0,pending=['theory coverage diagnosis','16:00 closeout']);dump(TB/'state.json',parent);print(json.dumps(audit,indent=2))
