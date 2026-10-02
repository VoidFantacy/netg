from pathlib import Path
import json,csv,hashlib,shutil,time,re
ROOT=Path('/data/netg/ACSG'); TB=Path(__file__).resolve().parents[1]; R=TB/'stages/e115_score_topology_factorial'
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(16<<20),b''):h.update(b)
    return h.hexdigest()
def ident(p):p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
assert not (R/'complete.json').exists()
c=read(R/'config.locked.json'); a=read(R/'reviews/analysis_complete.json'); gate=read(R/'results/gate.json'); jobs=read(R/'reviews/jobs.json')
assert gate['decision']=='STOP_CROSS_SCORE_TOPOLOGY_CANDIDATE' and a['status']=='PASS'
assert all(j['exit_code']==0 and not Path('/proc',str(j['pid'])).exists() for j in jobs)
checked={}
for rows in [c['source_files'],read(R/'reviews/search_source_freeze.json')['files'],read(R/'reviews/model_identity_gate.json')['files'],a['source_files'],a['outputs']]:
    for x in rows:
        if x['path'] not in checked:assert sha(x['path'])==x['sha256'],x['path'];checked[x['path']]=x['sha256']
for x in c['large_files']:
    s=Path(x['path']).stat();assert s.st_size==x['bytes'] and s.st_mtime_ns==x['mtime_ns']
metrics=list(csv.DictReader((R/'results/metrics.csv').open()));factors=list(csv.DictReader((R/'results/factors.csv').open()))
rows=[]
for ds in c['datasets']:
    for m in ds['methods']:
        r=[next(x for x in metrics if x['dataset']==ds['dataset'] and x['method']==m['name'] and int(x['K'])==k and int(x['L'])==128) for k in [1,100]]
        rows.append(f"| {'Web' if ds['dataset'].startswith('web') else 'Yandex'} | {m['name']} | {100*float(r[0]['recall']):.4f} | {100*float(r[1]['recall']):.4f} | {r[0]['failed']}/{r[1]['failed']} | {float(r[0]['mean_route_ndc']):.3f} | {float(r[0]['mean_graph_ndc']):.3f} |")
search_seconds=sum(j['seconds'] for j in jobs if j['kind'] in ['smoke','main'])
rss=max(j.get('complete',{}).get('maxrss_kib',0) for j in jobs)/1048576
report='''# E115：拆开GT10评分与路由小图

2026-09-20。**STOP_CROSS_SCORE_TOPOLOGY_CANDIDATE**。四格对照支持GT10小图的路由计算优势，但预定混合候选B在两集主质量点均未过门，未启动条件正式wall，不更换默认。评分与小图相互作用，不能从不同版本各取一个正向结果后推断组合必然更好。

## 动机和冻结设计

E108同时更换评分向量与路由小图，无法单独解释其路由NDC差异。本次固定原GT10画像P、单位hub向量U、原GT10完整小图状态GP和E108单位hub小图GU，构成A=(P,GP)、B=(U,GP)、C=(P,GU)、D=(U,GU)。**只有B是事先候选，C仅作机制控制**。E54已经采用模型/图交叉分析，E56/E95也研究过构图，本次是针对GT10的归因补充，不是新图学习算法。

GP/GU包含所有有序分层邻接、层级、入口节点和标签。混合索引仅改向量字节；四份before副本、完整非向量字节hash、所有向量行及real-ID均已核对。raw query、ef=10、3真实入口按ID升序进入同一NSG。两集各4096条E105已曝光开发query；K1的L64/128/256/400/800，K100的L128/256/400/800，全72点。路由缓存跨K/L复用，所以本次没有可报告的端到端QPS。

## 匹配结果

L128；Recall单位%，失败为该K返回与GT完全无交集的query数。K1/K100虽然终止搜索相同，Recall定义不同。下表完整NSG NDC取K1，已验证相同L的K1/K100一致。

| 数据 | 四格 | Recall@1 | Recall@100 | 失败K1/K100 | 路由NDC | NSG NDC |
|---|---|---:|---:|---:|---:|---:|
'''+ '\n'.join(rows)+'''

B−A主差值及预锁98.75%配对区间：Web K1 −0.0977pp [−1.0254,+0.8057]、K100 −0.1482pp [−0.5381,+0.2349]；Yandex K1 −0.2930pp [−0.9521,+0.3662]、K100 −0.3481pp [−0.7979,+0.0752]。Web K1恢复111/损伤115，Yandex52/64，说明动作改变可以带来相互抵消。区间跨0不证明效果恰为零；本次候选没有满足预定改进证据。

按K跨全部L平均，B−A为Web +0.1123/−0.0152pp、Yandex −0.1611/−0.1674pp。两集均不满足“两个主K非负、至少一个≥0.5pp且至少一个校正下界>0、各K跨L均值非负”。停止B，不改选C、某个L或单数据集，也不追加ef/seed/阈值。完整数字见[metrics](results/metrics.csv)、[paired](results/paired.csv)、[gate](results/gate.json)。

## 机制解释与归因边界

固定评分时，GP在两种评分背景、两集都减少路由NDC。例如U评分下，Yandex从215.711降至129.309，Web从165.168降至129.278。固定GP时，P又比U省路由计算。这表明低路由成本来自评分和图状态共同作用，**路由NDC减少不等于完整wall更好，也不等于真实召回提高**。

逐query精确恒等式为D−A=(B−A)+(C−A)+(D−B−C+A)。最后一项是交互项。L128的K1/K100平均交互分别为Web +0.1465/+0.4326pp、Yandex +0.4883/+0.2544pp。所有主B−A区间按冻结四检验口径；其余交互区间仅描述，不据其选择新候选或声明全部点显著。整数命中数恒等式73728行全部通过。

事后只读二进制解析发现：**原GP与GU的层级和初始入口不同**。因此本对照隔离完整小图状态，不能把C−A称为严格同层级的建边因果效应。E108同seed重建GP与GU的层级、入口相同；原GP与重建GP的所有第0层有序邻接完全一致，但上层不同。已有同层级控制的路由NDC仍为Web119.236对165.168、Yandex109.314对215.711，方向相同；它不是本次新增性能测量。

静态第0层平均出度为Web GP9.239/GU13.148、Yandex GP11.029/GU20.593。较稀疏邻接是成本差异的一个可检验解释，但静态出度不能单独分出实际展开次数、新访问节点和重复邻居的贡献。该描述在结果之后生成，不改变原门。[拓扑描述](results/topology_description.json)。

![L128评分与图状态四格](figures/score_topology.png)

[PDF图](figures/score_topology.pdf)使用同一表；图已实际查看，坐标、数值与图例可读。

## 验收、成本与结论

A/D全部返回ID、距离bits、入口、两段NDC恢复E108；四格smoke的计数/普通/链接E99内核完全一致。独立全量评分，预定query的另一实现复算、131072行K1前缀、111681行相同入口一致性均通过。

'''+f'新增295680次真实NSG（294912主诊断+768 smoke）、33024次路由ANN；4份混合索引及4份before副本，0普通构图/底图/新GT/训练/held-out/正式QPS。搜索进程含加载及smoke共{search_seconds:.6f}秒，编译8.527983秒、序列化0.032110秒、分析{a["seconds"]:.6f}秒、静态描述0.040991秒；最大进程RSS {rss:.6f}GiB。成本不是QPS。六个登记native进程均正常结束。\n\n'+'''本次获得机制证据，没有稳定替代GT10的方法。Web GT10-soft-t1、Yandex GT10-hard、生产E99均保持。原始负点、协议和身份记录保留；评分/建边换名及追加参数网格不进入待运行队列。

[冻结协议](protocol.md) · [配置](config.locked.json) · [诊断成本](reviews/diagnostic_complete.json) · [数值核验](reviews/analysis_complete.json) · [完整图状态身份](reviews/model_identity_gate.json)。
'''
(R/'report.md').write_text(report)
dump(R/'reviews/figure_visual_review.json',dict(status='PASS',actual_png_viewed=True,reviewer='root visual inspection before closeout',figures=[ident(R/'figures'/f) for f in ['score_topology.png','score_topology.pdf']],labels_readable=True,source=ident(TB/'research/plot_e115.py')))
hist=ROOT/'experiment_history/113_score_topology_factorial.md'; assert not hist.exists()
hist.write_text('''# 113｜E115 GT10评分与小图交叉机制

2026-09-20，STOP_CROSS_SCORE_TOPOLOGY_CANDIDATE。E108评分/图共同变化，本次预锁P/U×GP/GU四格，只有B=(U,GP)可进质量门，C只作机制控制；复核E54/E56/E95，不声称新方法。

两集各4096曝光query、完整72个真实K1/K100点。B−A在L128的Web K1/K100为−0.0977/−0.1482pp、Yandex−0.2930/−0.3481pp，四个98.75%配对区间均跨0；双集预锁门均失败，不测条件wall、不追加网格、不改选C。默认Web soft/Y hard及生产E99保持。

固定评分，GP均减少路由NDC；Yandex U评分215.711→129.309，Web165.168→129.278。但质量存在评分与图交互，低NDC不能推出完整wall/Recall改善。原GP与GU层级/入口也不同，作用是完整图状态；旧E108同层级重建对照仍支持成本方向。原/重建GP第0层全部边相同；GP静态平均度较低只作解释线索。

混合索引所有非向量字节不变、全行W/ID核验；A/D全部旧结果恢复，smoke三内核一致，独立评分/前缀/同入口/整数分解均通过。295680真实NSG、33024ANN、4混合副本、0普通构图/GT/训练/正式QPS；搜索进程含加载327.357980秒，编译8.528秒，RSS约9.917GiB。完整负点保留。

[完整报告](../entry_method_exploration/20260920_until1900_theory_v1/stages/e115_score_topology_factorial/report.md) · [协议](../entry_method_exploration/20260920_until1900_theory_v1/stages/e115_score_topology_factorial/protocol.md) · [门](../entry_method_exploration/20260920_until1900_theory_v1/stages/e115_score_topology_factorial/results/gate.json)。
''')
docs=['summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md'];before=R/'reviews/closeout_documents_before';before.mkdir()
for rel in docs:
    p=before/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/rel,p)
def prepend(rel,text,replace=False):
    p=ROOT/rel;head,rest=p.read_text().split('\n\n',1)
    if replace:rest=rest.split('\n\n',1)[1]
    p.write_text(head+'\n\n'+text+'\n\n'+rest)
link='[记录113](experiment_history/113_score_topology_factorial.md)'
prepend('summary.md','2026-09-20 **E115评分/图交叉完成并停止候选B**：72点中主L128的B−A两集K1/K100均负，校正区间跨0，双集门失败，不进入条件wall。固定评分后GT10完整小图状态减少路由NDC，但不保证Recall或总wall。原GP/GU层级与初始入口不同，旧同层级控制另列。295680真实NSG、33024ANN、4混合副本、0普通构图/GT/训练；默认与生产E99保持。'+link+'。',True)
prepend('spec.md','2026-09-20 E115独立交叉评估器完成：冻结P/U与完整GP/GU，仅替换四份副本向量字节；所有非向量字节、全W/real-ID、原结果恢复、smoke三内核及独立评分通过。路由缓存跨K/L，只作72点质量/成本诊断，不计QPS。事后只读解析层级/邻接；没有生产API变化。'+link+'。',True)
prepend('s-target.md','2026-09-20 E115完整评分/图状态机制矩阵已完成，预定B质量门失败，不进入条件正式wall、不改选C或参数网格。后继只核对小图实际路由工作分解并收束理论：完整图状态效应不能直接归因于出度，评分/图交互也不能推出稳定替换。18:50停止新搜索、19:00收尾，原默认保持。'+link+'。',True)
prepend('s-experiment.md','2026-09-20 E115评分/小图四格归因完成：GT10图状态省路由NDC，但混合候选B双集质量门失败，0新正式QPS。完整状态含层级/入口，原图/评分作用不可简单相加。'+link+'。')
p=ROOT/'experiment_history/README.md';p.write_text(p.read_text().replace('|---|---|\n','|---|---|\n| [113 评分与小图交叉](113_score_topology_factorial.md) | E115：四格归因与交互，混合候选门失败，完整图状态边界 |\n',1))
links=0
for p in [R/'report.md',R/'protocol.md',hist]+[ROOT/x for x in docs]:
    for dest in re.findall(r'\]\(([^)]+)\)',p.read_text()):
        if '://' in dest or dest.startswith('#'):continue
        assert (p.parent/dest.split('#')[0]).resolve().exists(),(str(p),dest);links+=1
dump(R/'reviews/documents_after.json',[ident(ROOT/x) for x in docs]+[ident(hist)])
dump(R/'reviews/closeout_identity.json',[dict(path=p,sha256=h) for p,h in checked.items()])
dump(R/'reviews/completion_audit.json',dict(status='PASS',files_verified=len(checked),jobs_closed=len(jobs),local_links_checked=links,large_input_stats_unchanged=True,search_process_seconds=search_seconds,maxrss_GiB=rss,report=ident(R/'report.md'),NSG_calls=295680,ANN_calls=33024,formal_QPS=False,default_changed=False))
dump(R/'state.json',dict(status='COMPLETE',decision=gate['decision'],pending=[],conditional_wall='NOT_LAUNCHED_QUALITY_GATE_FAILED'))
dump(R/'complete.json',dict(status='COMPLETE',completed_unix=time.time(),decision=gate['decision'],NSG_calls=295680,ANN_calls=33024,ordinary_graph_builds=0,hybrid_router_copies=4,new_GT=0,new_training=0,formal_QPS=False,report=ident(R/'report.md'),audit=ident(R/'reviews/completion_audit.json')))
s=read(TB/'state.json');assert s['completed_NSG_calls']==32768;s.update(stage='E115 closed; routing work and final synthesis',completed_NSG_calls=328448,active_stage_reserved_NSG_calls=0,pending=['routing work attribution','19:00 closeout']);dump(TB/'state.json',s)
print(json.dumps(read(R/'reviews/completion_audit.json'),indent=2))
