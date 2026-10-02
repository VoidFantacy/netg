from pathlib import Path
import json,csv,hashlib,time,shutil,re,os
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1';os.sched_setaffinity(0,{15})
ROOT=Path('/data/netg/ACSG');TB=Path(__file__).resolve().parents[1];R=TB/'stages/e113_comparison_support'
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(16<<20),b''):h.update(b)
 return h.hexdigest()
def ident(p):p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
assert not (R/'complete.json').exists();cfg=read(R/'config.locked.json');gate=read(R/'results/gate.json');assert gate['status']=='STOP_EXACT_PAIR_FEATURE_DICTIONARY';verified={}
for name in ['protected_before.json','setup_freeze.json','search_source_freeze.json','input_sources.json']:
 x=read(R/'reviews'/name);files=x if isinstance(x,list) else x['files']
 for a in files:assert sha(a['path'])==a['sha256'],a['path'];verified[a['path']]=a['sha256']
for a in read(R/'reviews/numeric_verification.json')['raw_files']:assert sha(a['path'])==a['sha256'];verified[a['path']]=a['sha256']
lock=read(R/'reviews/analysis_lock.json')['source'];assert sha(lock['path'])==lock['sha256'];verified[lock['path']]=lock['sha256']
for c in cfg['datasets'].values():
 s=Path(c['index']).stat();assert s.st_size==c['index_stat']['bytes'] and s.st_mtime_ns==c['index_stat']['mtime_ns']
jobs=read(R/'reviews/jobs.json');assert all(x['exit_code']==0 and not Path('/proc',str(x['pid'])).exists() for x in jobs);calls=sum(x.get('complete',{}).get('NSG_calls',0) for x in jobs);assert calls==32768
seconds=sum(x['seconds'] for x in jobs if x['kind']=='fit_trace');compile_seconds=sum(x['seconds'] for x in jobs if x['kind']=='compile');maxrss=max(x.get('complete',{}).get('maxrss_kib',0) for x in jobs)/1024**2
rows=list(csv.DictReader((R/'results/shared_support.csv').open()));table=[]
for x in rows:table.append('| '+('WebVid' if x['dataset'].startswith('web') else 'Yandex')+f" | {int(x['distinct_graph_node_pairs']):,} | {100*float(x['single_query_pair_fraction']):.4f}% | {x['query_support_max']} | {x['eligible_pairs']} | {float(x['selected_recorded_query_coverage_pct']):.4f}% |")
(R/'report.md').write_text('''# E113：具体搜索比较对缺少跨query共享支持

2026-09-20。**STOP_EXACT_PAIR_FEATURE_DICTIONARY**：Web/Y中97.7842%/99.2891%的不同节点比较对只出现在一条训练query中。预锁32维具体节点差字典未通过支持门；停止该字典，不降低支持阈值、改变维度或转选单集训练。当前默认和生产保持。

## 问题与执行

由同GT1 query分支反例，研究是否能将实际搜索比较`qᵀ(x_i−x_j)`对应的节点差向量作为query特征。这里先检查操作结构是否在不同GT1目标的query间有重复支持；出现次数不是因果重要性、可预测性或收益证据。

仅原E104 fit2048/集、原底图/真实raw-IP/L128。每query保留默认anchor与已测56集合中的一个最大等K teacher；多个teacher按与anchor重合数、真实ID择优，anchor已最优时两动作相同。分别真实调用K1/K100，每个动作先原kernel控制、再仅记录比较的fork；所有返回ID/距离bits/NDC恢复E104原动作，两个K的比较集合也完全相同。无cal/development/held-out载荷访问。

共32768次NSG是同4096条fit query的动作/K/控制重复，不是32768个独立样本。0新ANN/GT/图/梯度或画像训练，无QPS。记录初始化排序、满池拒绝、插入端点/二分/同分扫描；空槽不当作节点、同query两动作不重复增加支持。E104与E107 kernel SHA完全相同，独立fork只加观察。

## 结果

| 数据 | 不同节点对 | 仅单query支持 | 最大query支持 | 达标节点对 | 最多32对覆盖的query |
|---|---:|---:|---:|---:|---:|
'''+ '\n'.join(table)+'''

每个达标对须被至少32条query实际比较，且正/负符号各至少8个不同GT1，向量差非零。选择顺序固定为较小正负GT1支持、总query支持、ID；要求至少32对且覆盖至少半数query，两集同时满足。Web只有10对、覆盖149/2048=7.2754%；Y最大支持只有27条，没有对满足32条要求。两个条件两集均失败。这些门是预锁支持启发式，不能写成普遍的样本复杂度定理。

Web共19,481,998个query/动作/节点对记录，合并同query两动作后14,851,623条；Y相应26,369,480/18,627,565条。每个数字只计一份K的轨迹，另一K逐条相同。全部8192个query/动作行严格排序去重，原输出SHA逐份一致；同query同对没有跨动作相反严格符号。混合/零符号Web532、Y156条保留。Web所选10对的374条严格比较与float64节点差特征符号均一致。

## 能排除什么，不能排除什么

具体节点ID对过于局部，当前字典不具备预定规模和覆盖，不能仅因图分支理论正确就直接训练MLP。不同节点对仍可能共享几何或结构模式；本阶段没有检验这种更抽象的参数共享，也不证明所有图条件特征无效。旧Atlas是query近邻效用平均，旧L10 chooser要支付在线trace；本版只检查离线比较对支持，没有重新运行这些旧模型。

这与E112一起显示一个共同缺口：把理论成立的局部事件直接做成具体ID标签，往往缺少跨query支持。GT10按目标几何区域聚合具有不同的信息共享方式，但区域代理仍未保证真实有限beam收益，不能反向宣称GT10完全最优。

## 成本与保护

'''+f'''两个fit记录进程含加载合计{seconds:.3f}秒，编译{compile_seconds:.3f}秒，最大RSS{maxrss:.3f}GiB，独立分析{read(R/'reviews/analysis_complete.json')['seconds']:.3f}秒；这些都不是线上QPS。执行前发现生成header的相对include依赖，显式链接同一冻结common目录并保存11项依赖身份，0失败编译/搜索，方法源码未因此变更。源码、输入、输出及已有阶段身份验收通过，历史产物保持。

'''+'''[协议](protocol.md) · [配置](config.locked.json) · [全部统计](results/shared_support.csv) · [门](results/gate.json) · [数值核验](reviews/numeric_verification.json) · [执行成本](reviews/jobs.json) · [include依赖](reviews/include_dependency.json) · [完成审计](reviews/completion_audit.json)。
''')
history=ROOT/'experiment_history/110_actual_comparison_support.md';assert not history.exists();history.write_text('''# 110｜E113实际搜索比较对支持

2026-09-20。由同GT1内部搜索分支反例，先检查实际比较节点对是否能形成跨query共享特征。仅E104 fit2048/集，原anchor及相同56标签中的最大等K teacher，真实K1/K100/L128。原kernel控制与记录fork的全部ID/距离bits/NDC均恢复历史动作，K1/K100比较集合一致。

Web/Y分别14,407,197/18,430,741个不同节点对；97.7842%/99.2891%只被一条query比较，最大支持48/27。预锁每对≥32query、两符号各≥8不同GT1，要求32个非零差向量覆盖半数query；Web仅10对覆盖7.2754%，Y0，整体STOP_EXACT_PAIR_FEATURE_DICTIONARY。不改阈值/规模、扩数据或转选单集训练。

32768次NSG为原4096条fit query的重复动作/K/控制核验；0ANN/GT/新图/梯度或画像训练/QPS。记录进程含加载约39.60秒、分析5.660秒。原件/8192行/全部输出SHA核验通过；include相对依赖在首次编译前显式补全，无失败搜索。具体ID对支持不足不等于所有图条件抽象不可共享，也不是GT10最优证明。默认Web soft/Y hard、生产E99保持；整体任务仍至19:00。

[完整报告](../entry_method_exploration/20260920_until1900_theory_v1/stages/e113_comparison_support/report.md) · [原始门](../entry_method_exploration/20260920_until1900_theory_v1/stages/e113_comparison_support/results/gate.json) · [全部统计](../entry_method_exploration/20260920_until1900_theory_v1/stages/e113_comparison_support/results/shared_support.csv)。
''')
docs=['summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md'];before=R/'reviews/closeout_documents_before';before.mkdir()
for rel in docs:p=ROOT/rel;dest=before/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
def prepend(rel,txt,replace=False):
 p=ROOT/rel;h,rest=p.read_text().split('\n\n',1)
 if replace:rest=rest.split('\n\n',1)[1]
 p.write_text(h+'\n\n'+txt+'\n\n'+rest)
prepend('s-experiment.md','2026-09-20 **E113实际比较对支持完成并停止**：Web/Y约97.8%/99.3%节点对只出现在1条fit query；固定字典Web10对覆盖7.2754%、Y0，未过共享支持门。32768重复NSG核验、0ANN/GT/图/模型/QPS，全部历史输出恢复，默认保持。[记录110](experiment_history/110_actual_comparison_support.md)。')
p=ROOT/'experiment_history/README.md';s=p.read_text().replace('|---|---|\n','|---|---|\n| [110 实际比较对支持](110_actual_comparison_support.md) | E113：原输出恢复；具体节点对缺少跨query支持，停止32维字典，0训练 |\n',1);p.write_text(s)
prepend('summary.md','2026-09-20 **E113比较对字典停止，STOP_EXACT_PAIR_FEATURE_DICTIONARY**。真实fit轨迹中Web/Y约97.8%/99.3%的具体节点比较对只出现于一条query；预锁字典Web仅10对覆盖7.2754%、Y0，未过共享支持门。32768次重复NSG核验约39.6秒记录进程，原E104动作的ID/距离bits/NDC及K1/K100比较集合完全恢复；0新ANN/GT/图/梯度或画像训练/QPS。此结论限具体节点对字典，不否定更抽象的图条件共享；原默认与生产E99保持，继续理论归纳与前作排除。[报告](entry_method_exploration/20260920_until1900_theory_v1/stages/e113_comparison_support/report.md) · [记录110](experiment_history/110_actual_comparison_support.md)。',True)
prepend('spec.md','2026-09-20 E113独立[比较记录fork](entry_method_exploration/20260920_until1900_theory_v1/stages/e113_comparison_support/src/trace_kernel.hpp)完成验收：保留原排序/拒绝/插入语义、记录真实ID比较对/符号/类型；8192个query/动作行严格去重，K1/K100比较集合和历史ID/距离bits/NDC完全一致。include依赖执行前固定，原件SHA验收通过；信息门停止，无新模型或生产API变化。[契约与报告](entry_method_exploration/20260920_until1900_theory_v1/stages/e113_comparison_support/report.md)。',True)
p=ROOT/'s-target.md';s=p.read_text().replace('E113比较对支持诊断已冻结，先完整parity/支持门，无新模型队列；','E113完整parity通过、比较对字典共享支持门失败并停止；后继只审查更抽象的共享机制与既有损失/构图前作，无新模型队列；');p.write_text(s)
links=0
for p in [R/'report.md',history]+[ROOT/x for x in docs]:
 for dest in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if '://' in dest or dest.startswith('#'):continue
  target=(p.parent/dest.split('#')[0]).resolve()
  if target==R/'reviews/completion_audit.json':continue
  assert target.exists(),(p,dest);links+=1
dump(R/'reviews/cost_ledger.json',dict(NSG_calls=calls,ANN_calls=0,new_GT=0,new_graphs=0,new_gradient_or_profile_training=0,fit_trace_process_seconds=seconds,compile_seconds=compile_seconds,analysis_seconds=read(R/'reviews/analysis_complete.json')['seconds'],max_rss_gib=maxrss,source_query_count=4096,distinct_query_action_count=8192,formal_QPS=False))
dump(R/'reviews/document_after.json',[ident(ROOT/x) for x in docs]+[ident(history)])
dump(R/'reviews/completion_audit.json',dict(status='PASS',verified_source_input_raw_files=len(verified),native_jobs_closed=len(jobs),analysis_tool_exit_code=0,local_links_checked=links,report=ident(R/'report.md'),all_historical_output_SHA_equal=True,all_queries_retained=True,default_changed=False,overall_goal_complete=False))
dump(R/'state.json',dict(status='COMPLETE',decision=gate['status'],completed_NSG_calls=calls,pending=[],default_changed=False));dump(R/'complete.json',dict(status='COMPLETE',decision=gate['status'],completed_unix=time.time(),NSG_calls=calls,ANN_calls=0,report=ident(R/'report.md'),audit=ident(R/'reviews/completion_audit.json')))
state=read(TB/'state.json');assert state['completed_NSG_calls']==32768;state.update(stage='E113 closed; theoretical synthesis and prior-work exclusions',active_stage_reserved_NSG_calls=0);dump(TB/'state.json',state);print(json.dumps(read(R/'reviews/completion_audit.json'),indent=2))
