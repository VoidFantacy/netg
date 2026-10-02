from pathlib import Path
import json,hashlib,shutil,time,re
ROOT=Path('/data/netg/ACSG');TB=Path(__file__).resolve().parents[1]
def ident(p):p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
hist=ROOT/'experiment_history/114_router_work_and_theory_scope.md';assert not hist.exists()
hist.write_text('''# 114｜路由工作量、净收益与理论归属

2026-09-20。E115质量门停止之后，只核对小图成本发生在哪里；没有新候选。

固定四格原参数，全部8192曝光query，原/观察版各一次，共65536 ANN、0NSG/GT读取或生成/训练/新图/正式QPS。观察版仅将hnswlib base模板的collect_metrics打开，32768对返回标签、距离bits、总NDC一致并恢复E115。原计数器只含上层，差分得到base扫描/展开；依源码恒等式派生首次访问与visited跳过，另从CSV验证覆盖和均值。

固定U评分，GU→GP在Yandex的base展开11.546→12.735，base邻边扫描241.854→160.630，NDC215.711→129.309；Web相同方向。省距离不是展开更少，主要是处理更少邻边/新节点；路径、层级和静态度仍共同作用，不能直接据此继续删边。编译5.070秒，路由进程0.565秒，RSS23.031MiB，两个进程已结束。

只读解释补充：E105的三入口改变比例97%以上，但K1救回/损伤125/126与63/63，且完整QPS下降；尚缺能预测净收益的机制。配对区间跨0不证明真值恰为0，不自动追加query或调参。

一手文献补充：NGFix的Escape Hardness与E111排名核心可达保证直接相关，不得称首次提出新理论；本地范围限固定原图/kernel/GT的条件和覆盖核验。SHEAF的返回差界不保证正确，论文两浅探针预测相关性不是本地完整QPS。任意有向图上容量1仍可展开n节点的基础反例说明，池容量本身不推出工作量仅随L增长；没有声称该例由NSG构图产生。

默认Web soft/Yandex hard及生产E99保持。未重开E111/E112/E113/E115停止版本。19:00综合报告继续收尾。

[路由报告与原始证据](../entry_method_exploration/20260920_until1900_theory_v1/research/router_work_identity_v1/report.md) · [净收益解释](../entry_method_exploration/20260920_until1900_theory_v1/research/net_gain_and_uncertainty.md) · [前作与范围](../entry_method_exploration/20260920_until1900_theory_v1/research/certificate_prior_work_addendum.md)。
''')
docs=['summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md'];before=TB/'reviews/routing_review_documents_before';before.mkdir()
for rel in docs:
    p=before/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/rel,p)
def prepend(rel,text,replace=False):
    p=ROOT/rel;head,rest=p.read_text().split('\n\n',1)
    if replace:rest=rest.split('\n\n',1)[1]
    p.write_text(head+'\n\n'+text+'\n\n'+rest)
link='[记录114](experiment_history/114_router_work_and_theory_scope.md)'
prepend('summary.md','2026-09-20 **小图工作分解与理论范围审查完成**：65536次轻量ANN、0新NSG，全部32768对原/观察版输出bits及NDC一致。固定U评分，GT10小图base展开略多，却扫描更少邻边；Yandex NDC215.71→129.31，不能解释成路径更短或据此继续删边。E115质量停止保持。E105入口广泛变化但救回/损伤相抵；E111排名核心保证与NGFix有直接前作关系，收窄原创性表述。默认与生产E99保持，综合报告收尾。'+link+'。')
prepend('spec.md','2026-09-20独立路由工作观察器已验收：逐字提取hnswlib searchKnn，仅打开base collect_metrics，原版计数器只含上层；逐query核验标签/距离bits/NDC及E115恢复，再由源码恒等式分解base首次距离与visited跳过。0NSG/GT访问/新图/训练，65536路由调用仅作诊断，未改生产API。'+link+'。')
prepend('s-target.md','2026-09-20 E115及后继路由工作归因已全部完成：B质量门停止；小图成本来自评分/完整图状态及访问邻接，尚无可部署质量速度改进。当前只做理论综合、成本与身份审查至19:00，无训练/参数网格/新性能候选队列；18:50后不启动搜索。后继需说明跨query净收益信息，不能把排名可达前作或更强网络名称当作新贡献。'+link+'。',True)
prepend('s-experiment.md','2026-09-20路由工作及理论范围补充完成：65536 ANN、0NSG；GT10小图省NDC主要表现为扫描更少邻边，非展开更少。保留E115停止、E105净增损口径，补充NGFix直接前作与稳定性/工作量条件。'+link+'。')
p=ROOT/'experiment_history/README.md';p.write_text(p.read_text().replace('|---|---|\n','|---|---|\n| [114 路由工作与理论范围](114_router_work_and_theory_scope.md) | 精确工作分解、净增损、NGFix/SHEAF前作条件 |\n',1))
files=[TB/'research/net_gain_and_uncertainty.md',TB/'research/certificate_prior_work_addendum.md',TB/'research/router_work_identity_v1/report.md',TB/'research/router_work_identity_v1/complete.json',hist]
links=0
for p in files+[ROOT/x for x in docs]:
    if p.suffix!='.md':continue
    for dest in re.findall(r'\]\(([^)]+)\)',p.read_text()):
        if '://' in dest or dest.startswith('#'):continue
        assert (p.parent/dest.split('#')[0]).resolve().exists(),(p,dest);links+=1
dump(TB/'reviews/routing_review_complete.json',dict(status='PASS',created_unix=time.time(),files=[ident(p) for p in files],documents=[ident(ROOT/x) for x in docs],local_links_checked=links,NSG_calls=0,ANN_calls=65536,default_changed=False,overall_goal_complete=False))
print('Routing review documents and links PASS:',links)
