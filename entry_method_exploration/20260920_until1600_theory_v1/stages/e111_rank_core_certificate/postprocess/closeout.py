import os,json,time,hashlib,csv,shutil,re,urllib.parse,ast
from pathlib import Path
R=Path(__file__).resolve().parents[1];TB=R.parents[1];ROOT=TB.parents[1]
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(16<<20),b''):h.update(b)
 return h.hexdigest()
def ident(p):p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
assert not (R/'complete.json').exists();gate=read(R/'results/gate.json');assert gate['status']=='STOP_CERTIFICATE_ID_GUARANTEE_TIE_MISMATCH'
assert gate['identity_member_violations']==gate['byte_duplicate_explained_violations']==15
v=read(R/'results/identity_violation_records.json');assert len({(x['dataset'],x['query_index']) for x in v})==1 and all(x['query_index']==3821 and x['K']==1 for x in v)
assert not read(R/'reviews/analysis_lock.json')['no_numeric_certificate_outputs_read_before_this_lock']
cover=list(csv.DictReader((R/'results/certificate_coverage.csv').open()));available=list(csv.DictReader((R/'results/all_H_availability.csv').open()));rescue=list(csv.DictReader((R/'results/guaranteed_rescue_lower_bound.csv').open()));assert len(cover)==162
topology=read(R/'reviews/topology_complete.json');analysis=read(R/'reviews/analysis_complete.json');jobs=read(R/'reviews/jobs.json');assert topology['status']==analysis['status']=='PASS'
docs=['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md']
for n in docs:p=R/'source_before_closeout'/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/n,p)
lines=['# E111：把可达条件落到真实图，保留数值边界与覆盖不足','',
'2026-09-20，排名核心可保留路径的图派生诊断完成，**STOP_CERTIFICATE_ID_GUARANTEE_TIE_MISMATCH**。全部162个既有方法/K/L点核验后，有15条ID包含违例，全部来自同一条Web query的同向量不同ID；原指标、query和违例均保留。即使暂看理想同分规则条件下的信息门，Yandex的可保证恢复量与覆盖也不足，因此本版不训练、不增加核心大小/路径前缀。','',
'## 1. 这次真正推导了什么','',
'固定有限池L，真实前m名节点m≤L且与外部严格分离时，其中任何已发现节点都不会被驱逐，最终会被展开。令r为实际第一个完整展开节点，S为初始入口，则从(S∩B_m)与(N_out(r)∩B_m)出发，在原有向图的B_m诱导子图内可达的目标，得到一个条件Recall下界。它不使用欧氏三角不等式，也不把cosine所属区域直接当搜索效用。完整条件、证明与数值限制见[推导](../../research/retained_target_reachability.md)。','',
'本阶段在原两集各4096曝光query上固定m64/100，通过位集传递闭包和hub出邻居倒排，得到全部815/821原hub的单入口条件目标集合；再结合E107八种入口及E110干预的实际首节点，核验真实K1/K100返回。没有新增NSG/ANN搜索、GT、图或训练；生成了新的图派生诊断标签，不能称零标签。','',
'## 2. 充分条件覆盖多少','',
'下面是尚以GT排名/同分假设为条件的覆盖量，不是可部署Recall，也不是实际搜索oracle上界。','',
'| 数据 | 核心m | 全H至少一个GT1证书的query | 每query平均可证GT1入口数 | 全H最大可证目标数的均值 |','|---|---:|---:|---:|---:|']
for x in available:lines.append(f"| {'WebVid' if x['dataset'].startswith('web') else 'Yandex'} | {x['m']} | {float(x['any_H_GT1_certificate_pct']):.3f}% | {float(x['mean_H_GT1_certificates']):.3f} | {float(x['mean_max_H_certified_count']):.3f} |")
lines += ['', '对当前GT10 exact3，L128证书覆盖其实际GT1命中的Web33.26%、Y12.13%；K100对应28.28%、12.05%。固定单入口NSG的该首行核心证书覆盖为0，但实际Recall很高，直接说明这是保守充分条件，不是必要条件。大部分成功仍可能通过核心外的中间节点到达目标；不能因没有证书判它们无效。','',
'在使用真实GT选择“保留基线或换一个可证单入口”的特权规则下，L128条件推断如下。它不计选择/部署成本，也没有新执行这些oracle动作；不能把它直接写进方法性能表。','',
'| 数据 | K | 对照 | 条件额外命中量对应ΔR pp | 受益query数 |','|---|---:|---|---:|---:|']
for x in rescue:
 if x['baseline'] in ['GT103','DefaultANN']:lines.append(f"| {'WebVid' if x['dataset'].startswith('web') else 'Yandex'} | {x['K']} | {x['baseline']} | {float(x['guaranteed_recall_improvement_lower_bound_pp']):.4f} | {x['guaranteed_rescue_queries']} |")
lines += ['', '冻结信息门要求两集相对GT10 exact3的GT1可保证恢复量均≥1pp，同时证书覆盖当前成功GT1 query至少25%；这里的覆盖明确取当前GT10 exact3证书，未替换为全H存在比例。Web条件数值通过，Y仅7/4096即0.1709pp且覆盖12.13%，不通过。原同分ID零违例门另行失败，两项原因分开报告。','',
'## 3. 同分ID为何使原断言失败','',
'Web query位置3821的GT1为345234，GT2为344262，二者base向量逐字相同；存储GT分数同为0.3253275454，float64独立内积同为0.3253275315。GT13、GT103与DefaultANN在五个K1预算都返回344262，因此出现3方法×5预算=15条ID证书违例；这是1个query，不是15个独立query。其余K1证书和全部K100成员包含检查没有违例。','',
'该事实违反“GT和搜索同分处理一致”的前提，不是一般保留引理的反例。现行Recall按GT ID计算，所以原分数仍保留；没有去掉query、换成向量等价Recall或修写旧GT。本查询最多影响每个Web K1均值1/4096=0.024414pp，不可据此解释此前大部分失败；Yandex信息门仍独立失败。','',
'GT100已有分数中，Web仅1条GT1/GT2同分（即此例），Y为0；m64与第65名同分Web2条、Y3条。m100未保存第101名，外部严格间隔未在本轮重新验证。所有数学保证继续保留排名、同分及完整循环条件；经验包含检查不替代任意浮点输入证明。','',
'第一次分析在首条违例停止并保存源码/锁/日志，随后只扩展为完整违例审计；未重算图标签或改变门。第二次分析沿用了“未读数值”的首轮标记，已保留前件并修正为false：这是第二轮已知首条违例后的审计。数值与来源修正分别记录，不伪称盲分析。','',
'## 4. 成本与研究结论','',
f"图派生编排{topology['seconds']:.2f}秒（含编译/加载/核验），完整第二轮审计{analysis['seconds']:.2f}秒；两个数据集原生图处理{sum(x['seconds'] for x in jobs if x['kind']=='topology'):.2f}秒。独立BFS共{sum(x.get('complete',{}).get('independent_BFS_checks',0) for x in jobs):,}次，全部与位集闭包一致。0新NSG/ANN/GT/图/梯度训练/正式QPS，实际CPU15/线程1，旧E107/E110输出SHA完整恢复。",'',
'这一轮给出了可以核验的桥接条件及其适用范围，同时发现一个真实同分指标边界。当前条件不足以支撑跨数据训练新模型；保留它作为理论工具，不扩大m或把原有失败归咎于网络不够复杂。16:00研究继续转向理论审查与总结。','',
'[协议](protocol.md) · [162点覆盖](results/certificate_coverage.csv) · [全H](results/all_H_availability.csv) · [条件恢复量](results/guaranteed_rescue_lower_bound.csv) · [15条违例](results/identity_violation_records.json) · [图](figures/certificate_coverage.png) · [门](results/gate.json) · [首轮保留](reviews/analysis_failure_response.json) · [来源修正](reviews/analysis_provenance_correction.json) · [验收](reviews/completion_audit.json)。']
(R/'report.md').write_text('\n'.join(lines)+'\n');rel='entry_method_exploration/20260920_until1600_theory_v1/stages/e111_rank_core_certificate'
summary=f'2026-09-20 **E111排名核心证书诊断完成，停止本版监督投入**。从原NSG候选池保留规则推出条件可达下界，m64/100、原H全量标签，162个既有K/L点核验。15条ID违例均来自同1条Web query的相同向量不同GT1 ID，全部保留，原Recall/GT不变；其余K1与全部K100成员检查无违例。L128对GT10 exact3的条件GT1恢复量Web2.5879pp/Y0.1709pp，当前成功覆盖33.26%/12.13%；即使按理想同分假设，Y信息门仍失败。充分条件不是必要条件或实际效用上界，不增m/路径/模型。约26秒图派生，0新NSG/ANN/GT/图/训练/QPS，新增诊断标签；默认保持。[报告]({rel}/report.md) · [记录106](experiment_history/106_rank_core_certificate.md)。'
for n,x in [('summary.md',summary),('spec.md',f'2026-09-20 E111独立[排名核心证书工具]({rel}/protocol.md)完成完整审计：固定m64/100、GT100有向诱导子图位集闭包、hub出邻居倒排和真实首节点/初始核心种子集合；16预定query/集对全部核心节点独立BFS。162旧点做条件成员包含检查，15同query同向量ID违例完整保留；未改搜索/GT/指标。首轮断言与后续全量审计/来源标记修正分别封存。0新NSG/ANN/GT/图/训练/QPS，无生产API变化。'),('s-experiment.md',f'2026-09-20 **E111条件可达证书完成**：162旧点完整审计，15条ID违例同属1个重复向量query；Y条件恢复量/覆盖不足。停止该证书监督投入，保留充分条件和全部违例。0新NSG/ANN/GT/图/训练/QPS，新增图派生标签。[记录106](experiment_history/106_rank_core_certificate.md)。')]:
 p=ROOT/n;head,rest=p.read_text().split('\n\n',1);p.write_text(head+'\n\n'+x+'\n\n'+rest)
p=ROOT/'s-target.md';head,old,rest=p.read_text().split('\n\n',2);assert old.startswith('E110已完成');p.write_text(head+'\n\n'+f'E111[条件可达证书]({rel}/report.md)完成：同分ID前提不匹配，且Yandex有效覆盖/条件恢复量未过门，停止本版监督，不增加m/路径前缀/新hub或训练。E110/E109候选均已按门停止。当前16:00目标余下用于理论条件/前作审查、证据整合与截止验收；不因剩余时间重启参数网格。15:50禁止新搜索，16:00按已完成结果交付。'+'\n\n'+rest)
p=ROOT/'experiment_history/README.md';t=p.read_text();needle='| [105 首展开干预]';idx=t.index(needle);t=t[:idx]+'| [106 排名核心证书](106_rank_core_certificate.md) | E111完成：条件可达下界及162点审计；同分ID边界/Y覆盖门失败，0新搜索 |\n'+t[idx:];p.write_text(t)
history=ROOT/'experiment_history/106_rank_core_certificate.md';hist='\n'.join(lines[2:-1]).replace('[推导](../../research/retained_target_reachability.md)','[推导](../entry_method_exploration/20260920_until1600_theory_v1/research/retained_target_reachability.md)');history.write_text('# 106｜E111 排名核心可达证书\n\n'+hist+'\n\n[完整报告](../'+rel+'/report.md) · [协议](../'+rel+'/protocol.md) · [验收](../'+rel+'/reviews/completion_audit.json)。\n');docs.append('experiment_history/106_rank_core_certificate.md')
protected=read(R/'reviews/protected_before.json');freeze=read(R/'reviews/source_freeze.json')['files'];raw=read(R/'reviews/numeric_verification.json')['raw_files']
for x in protected+freeze+raw+[read(R/'reviews/binary_freeze.json'),read(R/'reviews/analysis_lock.json')['source']]:assert sha(x['path'])==x['sha256'],x['path']
assert len(jobs)==3 and all(x['exit_code']==0 for x in jobs) and all(a['finished_unix']<=b['started_unix'] for a,b in zip(jobs,jobs[1:]))
for j in jobs:
 p=Path('/proc')/str(j['pid'])/'cmdline';assert not p.exists() or str(R).encode() not in p.read_bytes()
for p in (R/'source_before').rglob('*'):
 if p.is_file():assert sha(p)==sha(R.parent/'e110_first_expansion_intervention/source_after'/p.relative_to(R/'source_before'))
figures=[ident(R/'figures'/('certificate_coverage.'+x)) for x in ['png','pdf']];dump(R/'reviews/visual_inspection.json',dict(status='PASS',figures=figures,method='PNG viewed against coverage table; conditional and ID mismatch scope shown; PDF from same figure.'))
links=[]
for p in [ROOT/n for n in docs]+[R/'report.md',R/'protocol.md',TB/'research/retained_target_reachability.md']:
 for link in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',p.read_text()):
  t=link.strip().strip('<>')
  if urllib.parse.urlsplit(t).scheme or t.startswith('#'):continue
  q=(p.parent/urllib.parse.unquote(t.split('#')[0])).resolve();assert q.exists() or q==R/'reviews/completion_audit.json',(str(p),link);links.append(dict(source=str(p),target=str(q)))
for p in list((R/'src').glob('*.py'))+list((R/'postprocess').glob('*.py')):ast.parse(p.read_text())
new_bytes=sum(p.stat().st_size for p in R.rglob('*') if p.is_file());assert new_bytes<read(R/'config.locked.json')['max_new_bytes']
state=dict(status='COMPLETE_RANK_CORE_AUDIT_STOP_SUPERVISION',decision=gate['status'],completed_unix=time.time(),pending=[],default_changed=False,timebox_continues=True);dump(R/'state.json',state)
after=R/'source_after';after.mkdir()
for n in docs:p=after/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/n,p)
dump(R/'reviews/document_checks.json',dict(status='PASS',documents=[ident(ROOT/n) for n in docs],links=links))
audit=dict(status='PASS_STAGE_COMPLETE_WITH_RECORDED_CONDITION_FAILURE',state=state,protected_SHA_files=len(protected),frozen_files=len(freeze),raw_files=len(raw),NSG_stat_checks=2,NSG_calls=0,ANN_calls=0,new_GT=0,new_graphs=0,new_training=0,new_QPS=False,new_graph_derived_labels=True,points_checked=162,ID_member_violations=15,distinct_violation_queries=1,all_violations_byte_duplicate_explained=True,topology_seconds=topology['seconds'],full_audit_seconds=analysis['seconds'],independent_BFS_checks=sum(x.get('complete',{}).get('independent_BFS_checks',0) for x in jobs),max_rss_gib=max(x.get('complete',{}).get('maxrss_kib',0) for x in jobs)/1024**2,new_bytes=new_bytes,local_links=len(links),report=ident(R/'report.md'),source=ident(Path(__file__)))
dump(R/'reviews/completion_audit.json',audit);assert all(Path(x['target']).exists() for x in links);dump(R/'complete.json',dict(status='COMPLETE',audit=ident(R/'reviews/completion_audit.json'),report=ident(R/'report.md')))
parent=read(TB/'state.json');assert parent['completed_NSG_calls']==2797056;parent.update(stage='E111 complete; theoretical scope and final evidence synthesis',completed_stages=['E107','E108','E109','E110','E111'],active_stage_reserved_NSG_calls=0,pending=['theoretical scope review','timebox synthesis','16:00 closeout']);dump(TB/'state.json',parent);print(json.dumps(audit,indent=2))
