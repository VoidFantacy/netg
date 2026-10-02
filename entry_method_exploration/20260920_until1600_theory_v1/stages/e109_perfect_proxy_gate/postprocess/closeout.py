import sys,csv,re,shutil,urllib.parse,ast
from pathlib import Path
RUN=Path(__file__).resolve().parents[1];sys.path.insert(0,str(RUN/'src'))
from common import *
assert not (RUN/'complete.json').exists()
protected_check();gate=read(RUN/'results/gate.json');search=read(RUN/'reviews/search_complete.json');analysis=read(RUN/'reviews/analysis_complete.json')
assert gate['status']=='STOP_PROXY_OBJECTIVES_BEFORE_TRAINING' and search['status']==analysis['status']=='PASS'
rows=list(csv.DictReader((RUN/'results/paired.csv').open()));proxy=list(csv.DictReader((RUN/'results/proxy_values.csv').open()));assert len(rows)==16
docs=['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md','experiment_history/104_perfect_proxy_information_gate.md']
for n in docs:
 p=RUN/'source_before_closeout'/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/n,p)
dump(RUN/'reviews/closeout_before.json',[identity(RUN/'source_before_closeout'/n) for n in docs])
lines=['# E109：真实目标代理仍未跨过搜索效用断点','',
'2026-09-20，固定fit信息门完成，**STOP_PROXY_OBJECTIVES_BEFORE_TRAINING**。两种代理在Yandex均有正信号，但WebVid没有相应收益；按预锁跨两集门不训练这两个目标，不追加阈值或数据子集。原GT10默认与生产E99保持。','',
'## 1. 这是学习目标的前置检查','',
'从E24原fit20K固定取floor(i*20000/2048)，两集各2048行；原H、NSG、raw query和GT不变。TargetMean直接使用真实GT10单位目标向量的均值，最大化三个单位hub与该均值的平均内积。Coverage直接使用真实GT10目标的原hub归属质量，最大化三hub质量和；并列按原GT10精确分数及real ID。对照GT10Exact和UnitHubExact，同为全H精确选3入口。','',
'两个代理知道部署时不可得的真实目标信息，但不是实际搜索效用最优动作，也不是Recall上界。fit参与过原画像构造；以下没有未曝光泛化证据。真实K1/K100均用L128，不新增Recall@10；输入覆盖10只是训练目标代理。','',
'## 2. 全部真实检索对照','',
'ΔR单位pp；16项主比较用固定20000次配对bootstrap、99.6875%区间（Bonferroni口径），仅作本fit投入门。','',
'| 数据 | K | 代理 | 控制 | ΔR pp | 校正区间 | 零命中 控制→代理 |','|---|---:|---|---|---:|---|---|']
for x in rows:lines.append(f"| {'WebVid' if x['dataset'].startswith('web') else 'Yandex'} | {x['K']} | {x['method']} | {x['baseline']} | {float(x['delta_recall_pp']):+.4f} | [{float(x['CI_adjusted_low']):+.4f}, {float(x['CI_adjusted_high']):+.4f}] | {x['baseline_failed']}→{x['method_failed']} |")
lines += ['', 'Web目标均值相对GT10的R1/R100为−1.3184/−0.0132pp，覆盖代理为−0.6836/−0.0908pp；Web八项区间均跨0。Yandex两代理对两控制的八项区间均为正，其中目标均值相对GT10为+1.0254/+0.5854pp。保留这个数据集差异，但不据此改变冻结的跨数据训练门。','',
'## 3. 代理更好不保证搜索更好','',
'| 数据 | 方法 | 输入GT10区域覆盖 | 目标均值亲和 |','|---|---|---:|---:|']
for x in proxy:lines.append(f"| {'WebVid' if x['dataset'].startswith('web') else 'Yandex'} | {x['method']} | {float(x['mean_GT10_input_coverage'])*100:.3f}% | {float(x['mean_target_affinity']):.6f} |")
lines += ['', 'Web覆盖代理将平均输入区域覆盖从35.42%提高到68.93%，最终R1却低0.6836pp。Yandex则覆盖从54.69%提高到81.50%，R1/R100提高0.9277/0.4756pp。这是同一个代理到实际有限beam搜索的转化随数据而异的直接证据；不是模型表达力不足的证明，也不能归因于单一机制。','',
'目标均值MSE与覆盖交叉熵均有各自的代理后悔界，但Recall界还需要代理到搜索效用的一致误差项δ。E109不估计全动作族δ，只显示当前两个代理最优动作未给出跨数据收益。停止投入不等于所有近似预测器必不可能改善：有限beam非单调，近似预测产生的不同动作仍可能更好。','',
'预锁门要求每个代理在两集、两K、两控制均值均非负，且每集至少一个共同K对两个控制都≥1pp并且校正区间下端>0。TargetMean仅Yandex通过，Coverage两集门均未通过；Coverage在Yandex对GT10的K1均值0.9277pp低于1pp，不能事后下调门槛。','',
'## 4. 验证、成本和下一步','',
f"真实NSG {search['NSG_calls']:,}次，搜索编排{search['seconds']:.2f}秒，分析{analysis['seconds']:.2f}秒；0新GT/图/梯度训练/正式QPS。CPU15/实际线程1，方法及数据串行。两个smoke与链接E99同输出/距离bits/NDC，全量count/plain一致；全H代理排名、integer质量和10、输入方向/源行/real ID、独立评分、K1首返回与K100及NDC均通过。",'',
'新图表已实际查看，旧输入/模型/图及源码身份保持。后续应研究代理到搜索的断点，或在保留精确动作得分的条件下改善E108发现的小图可检索性；不能把本次停止解释成需要更大网络。16:00限时研究继续，当前无E109待运行搜索。','',
'[协议](protocol.md) · [完整指标](results/metrics.csv) · [配对](results/paired.csv) · [代理量](results/proxy_values.csv) · [门](results/gate.json) · [图](figures/proxy_information_gate.png) · [验收](reviews/completion_audit.json)。']
(RUN/'report.md').write_text('\n'.join(lines)+'\n')
rel='entry_method_exploration/20260920_until1600_theory_v1/stages/e109_perfect_proxy_gate'
summary=f'2026-09-20 **E109完美代理门完成，STOP_PROXY_OBJECTIVES_BEFORE_TRAINING**。两集预锁fit2048行、K1/K100/L128，真实目标均值与区域覆盖对两个exact控制。相对GT10，Web目标均值R1/R100为−1.3184/−0.0132pp、覆盖−0.6836/−0.0908pp；Yandex分别+1.0254/+0.5854pp、+0.9277/+0.4756pp。Web八项校正区间跨0、Y八项为正，跨集训练门均未通过。Web区域覆盖35.42%→68.93%却未提高真实召回，说明代理到有限beam效用的桥接仍缺。66304 NSG、约78秒编排，0新GT/图/训练/QPS；fit特权信息非部署方法、非Recall上界，原默认保持。[报告]({rel}/report.md) · [记录104](experiment_history/104_perfect_proxy_information_gate.md)。'
for n,new in [('summary.md',summary),('spec.md',f'2026-09-20 E109独立[完美代理评估器]({rel}/protocol.md)完成验收：预锁fit2048位置、E27 real-ID整数归属、真实GT10单位目标均值；C++全H精确四路由，原raw query进逐字继承NSG，真实K1/K100/L128。全量count/plain、链接E99 smoke、全H排名/独立评分/K1前缀及NDC通过；分析16项固定校正区间并执行预锁门。源/输入/输出/报告封存，无生产API变化、无新GT/图/训练/QPS，E109无待运行任务。'),('s-experiment.md',f'2026-09-20 **E109完美代理门完成并停止训练投入**：Yandex有正信号、Web无转化，两个代理均未过跨集门。Web区域覆盖大增但Recall不增，明确代理与有限beam效用缺口；66304 NSG，0训练/GT/图/QPS，默认保持。[记录104](experiment_history/104_perfect_proxy_information_gate.md)。')]:
 p=ROOT/n;t=p.read_text();head,old,rest=t.split('\n\n',2);assert 'E109' in old;p.write_text(head+'\n\n'+new+'\n\n'+rest)
p=ROOT/'s-target.md';t=p.read_text();a=t.index('当前接续为[E109');b=t.index('\n\n',a);t=t[:a]+f'E109已完成[完美代理信息门]({rel}/report.md)，两个目标均未通过冻结的跨数据训练门，因此不训练TargetMean/Coverage预测器，不降低1pp门槛或选Yandex子集续跑。当前接续先研究代理到有限beam效用的断点，以及能否保留精确动作得分而改善E108小图可检索性；尚未锁定下一变换/搜索。E106及既有失败版本不重启，15:50起只收尾，16:00按实际完成状态交付。以下旧“无待运行任务”按各历史版本解释。'+t[b:];p.write_text(t)
history=ROOT/'experiment_history/104_perfect_proxy_information_gate.md'
history.write_text('# 104｜E109 完美目标代理信息门\n\n'+summary.replace(f']({rel}/',f'](../{rel}/').replace(' · [记录104](experiment_history/104_perfect_proxy_information_gate.md)。','。')+'\n\n'+ '\n'.join(lines[5:-1])+'\n\n[完整报告](../'+rel+'/report.md) · [协议](../'+rel+'/protocol.md) · [验收](../'+rel+'/reviews/completion_audit.json)。\n')
freeze=read(RUN/'reviews/search_source_freeze.json')['files'];raw=read(RUN/'reviews/numeric_verification.json')['raw_files'];before=read(RUN/'reviews/execution_started.json')['source_before']
for r in freeze+raw+before+read(RUN/'reviews/pre_fit_lock.json')['files']+read(RUN/'reviews/build_source_lock.json')['libraries']:assert sha(r['path'])==r['sha256'],r['path']
r=read(RUN/'reviews/analysis_lock.json')['source'];assert sha(r['path'])==r['sha256']
jobs=read(RUN/'reviews/jobs.json');assert len(jobs)==6 and all(x['exit_code']==0 for x in jobs) and all(a['finished_unix']<=b['started_unix'] for a,b in zip(jobs,jobs[1:]))
assert sum(j['reserved_calls'] for j in jobs)==66304
for j in jobs:
 p=Path('/proc')/str(j['pid'])/'cmdline';assert not p.exists() or str(RUN).encode() not in p.read_bytes()
figs=[identity(RUN/'figures'/('proxy_information_gate.'+x)) for x in ['png','pdf']]
dump(RUN/'reviews/visual_inspection.json',dict(status='PASS',figures=figs,method='PNG viewed and checked against all sixteen paired rows; PDF exported from same figure.'))
links=[]
for p in [ROOT/n for n in docs]+[RUN/'report.md',RUN/'protocol.md']:
 for link in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',p.read_text()):
  target=link.strip().strip('<>')
  if urllib.parse.urlsplit(target).scheme or target.startswith('#'):continue
  q=(p.parent/urllib.parse.unquote(target.split('#')[0])).resolve();assert q.exists() or q==RUN/'reviews/completion_audit.json',(str(p),link);links.append(dict(source=str(p),target=str(q)))
for p in list((RUN/'src').glob('*.py'))+list((RUN/'postprocess').glob('*.py')):ast.parse(p.read_text())
new_bytes=sum(p.stat().st_size for p in RUN.rglob('*') if p.is_file());assert new_bytes<LOCK['max_new_bytes'] and shutil.disk_usage(RUN).free>4*1024**3
state=dict(status='COMPLETE_PERFECT_PROXY_GATE_NO_TRAINING',decision=gate['status'],completed_unix=time.time(),pending=[],default_changed=False,heldout_access=False,timebox_continues=True);dump(RUN/'state.json',state)
after=RUN/'source_after';after.mkdir()
for n in docs:p=after/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/n,p)
dump(RUN/'reviews/document_checks.json',dict(status='PASS',documents=[identity(ROOT/n) for n in docs],links=links))
audit=dict(status='PASS_STAGE_COMPLETE',state=state,protected_SHA_files=len(read(RUN/'reviews/protected_before.json')),NSG_stat_checks=2,frozen_files=len(freeze),raw_files=len(raw),NSG_calls=66304,points=16,primary_contrasts=16,new_GT=0,new_training=0,new_graphs=0,new_formal_QPS=False,threads=1,search_seconds=search['seconds'],max_rss_gib=max(j.get('complete',{}).get('maxrss_kib',0) for j in jobs)/1024**2,new_bytes=new_bytes,local_links=len(links),report=identity(RUN/'report.md'),source=identity(Path(__file__)))
dump(RUN/'reviews/completion_audit.json',audit);assert all(Path(x['target']).exists() for x in links);dump(RUN/'complete.json',dict(status='COMPLETE',audit=identity(RUN/'reviews/completion_audit.json'),report=identity(RUN/'report.md')))
parent=read(TB/'state.json');assert parent['completed_NSG_calls']==2287872;parent.update(stage='E109 complete; investigate proxy-search bridge and score-preserving indexability',completed_stages=['E107','E108','E109'],completed_NSG_calls=2354176,active_stage_reserved_NSG_calls=0,pending=['evidence-derived mechanism research','16:00 closeout']);dump(TB/'state.json',parent)
print(json.dumps(audit,ensure_ascii=False,indent=2))
