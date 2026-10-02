from pathlib import Path
import json,csv,hashlib,time,shutil,re
TB=Path(__file__).resolve().parents[1];ROOT=Path('/data/netg/ACSG');R=TB/'research/router_work_identity_v1'
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def ident(p):p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
assert not (R/'complete.json').exists();c=read(R/'config.locked.json');done=read(R/'results/complete.json');jobs=read(R/'jobs.json');summary=read(R/'results/summary.json')
assert done['status']=='PASS' and done['ANN_calls']==65536
for x in c['source_files']:assert ident(x['path'])==x,x['path']
for j in jobs:assert j['exit_code']==0 and not Path('/proc',str(j['pid'])).exists()
groups={};keys=['ndc','upper_expansions','upper_neighbor_scans','base_expansions','base_neighbor_scans','base_first_visit_distances','base_visited_skips'];count=0
for x in csv.DictReader((R/'results/queries.csv').open()):
    v={k:int(x[k]) for k in keys};assert v['ndc']==2+v['upper_neighbor_scans']+v['base_first_visit_distances'];assert v['base_neighbor_scans']==v['base_first_visit_distances']+v['base_visited_skips'];key=(x['dataset'],x['method']);g=groups.setdefault(key,dict(ids=set(),sums={k:0 for k in keys}));assert int(x['query']) not in g['ids'];g['ids'].add(int(x['query']))
    for k in keys:g['sums'][k]+=v[k]
    count+=1
assert count==32768
for x in summary:
    g=groups[(x['dataset'],x['method'])];assert g['ids']==set(range(4096))
    for k in keys:assert x[k]==g['sums'][k]/4096
table='\n'.join(f"| {'Web' if x['dataset'].startswith('web') else 'Yandex'} | {x['method']} | {x['ndc']:.3f} | {x['upper_neighbor_scans']:.3f} | {x['base_expansions']:.3f} | {x['base_neighbor_scans']:.3f} | {x['base_first_visit_distances']:.3f} | {x['base_visited_skips']:.3f} |" for x in summary)
text='''# 小图为什么省计算：实际路由工作分解

2026-09-20，**ROUTER_WORK_IDENTITY_VERIFIED**。这是E115之后的机制诊断，未产生新候选。原四格、全部8192条曝光query，原ef10/top3/raw-IP保持；0真实NSG、0GT读取或生成、0训练/图/正式QPS。

## 记账原理与验收

原hnswlib的hops和distance_computations计数器只在上层自动累加；base模板默认不收集。因此直接把原计数器当作全程距离数会错误。观察版逐字提取searchKnn，只改函数名和base模板的collect_metrics=true，所有队列/比较/距离逻辑未改。

原版与观察版分别调用一次，共65536次ANN。32768对输出标签、距离bits与总NDC全部一致，并逐query恢复E115三入口和路由NDC。观察版计数器减原版给出base展开行数和邻接扫描数。源码保证无删除/过滤时上层初始入口、base初始入口各打分一次，上层每条扫描邻边都打分，base只对尚未visited邻居打分。因此：

`总NDC = 2 + 上层邻边扫描 + base首次访问距离`；

`base邻边扫描 = base首次访问距离 + base visited跳过`。

base首次访问距离和visited跳过是据上述源码恒等式由计数器相减得到的量，不是第三个独立探针。base的“首次”仅限base visited表，不是分层全局首次。全部行核验非负、唯一访问上限及整数关系；Python从CSV另行核对完整query覆盖和所有均值。

## 全部四格均值

A=(P,GP)、B=(U,GP)、C=(P,GU)、D=(U,GU)。P为GT10画像，U为单位hub；GP/GU是E115的完整图状态，含原先不同的高层节点与初始入口。

| 数据 | 四格 | 总NDC | 上层扫描 | base展开 | base扫描 | base首次距离 | base跳过 |
|---|---|---:|---:|---:|---:|---:|---:|
'''+table+'''

固定U评分，GU→GP的base展开数反而增加：Web12.202→13.321，Yandex11.546→12.735；但base邻边扫描减少，Web190.766→157.578，Yandex241.854→160.630。路由NDC分别少35.891和86.403，其中base新访问距离少30.608和73.880，上层邻边打分少5.282和12.523。**这直接反驳“距离数少就是展开更少”的解释**；低成本主要落在减少每次展开所覆盖的邻边/新节点上。

固定P评分，base展开数量接近，Web11.697/11.717、Yandex11.170/11.324；GP的base邻边扫描及首次距离仍明显较少。结合E115的静态度，支持“访问到的邻接较稀疏”这一工作量解释。但路径和所访问节点也随图变化，不能把所有差值归给单一静态平均度，不能凭此要求进一步删边。原GP/GU的层级差异仍在；旧同层级重建控制的方向见E115。

## 与方法决策的关系

本分解回答成本发生在哪里，没有回答怎样保持更多正确入口。E115预定B仍未过召回门，故不测其条件wall、不调ef/稀疏度或新建图。NDC还忽略内存访问、队列和路由/NSG以外工作，不能转成QPS。它也没有为任何新模型提供泛化保证。

'''+f"编译进程{jobs[0]['seconds']:.6f}秒，全部路由进程{jobs[1]['seconds']:.6f}秒（native核心{done['seconds']:.6f}秒，含各图加载/校验/CSV输出），RSS {done['maxrss_kib']/1024:.3f}MiB；这些是诊断成本。两个登记进程已结束。默认和生产保持。\n\n"+'''[冻结协议](protocol.md) · [逐query工作量](results/queries.csv) · [完整汇总](results/summary.json) · [源码](evaluate.cpp) · [E115质量结论](../../stages/e115_score_topology_factorial/report.md)。
'''
(R/'report.md').write_text(text)
audit=dict(status='PASS',created_unix=time.time(),source_files_verified=len(c['source_files']),native_parity_rows=32768,csv_rows_checked=count,jobs_closed=2,NSG_calls=0,ANN_calls=65536,GT_read=False,new_training=0,new_graphs=0,formal_QPS=False,report=ident(R/'report.md'),files=[ident(p) for p in R.rglob('*') if p.is_file()])
dump(R/'completion_audit.json',audit)
dump(R/'complete.json',dict(status='COMPLETE',completed_unix=time.time(),decision='ROUTER_WORK_IDENTITY_VERIFIED',NSG_calls=0,ANN_calls=65536,report=ident(R/'report.md'),audit=ident(R/'completion_audit.json')))
state=read(TB/'state.json');state.update(stage='Theory synthesis and final audit',completed_ANN_calls=98560,pending=['19:00 closeout']);dump(TB/'state.json',state)
print(json.dumps({k:v for k,v in audit.items() if k!='files'},indent=2))
