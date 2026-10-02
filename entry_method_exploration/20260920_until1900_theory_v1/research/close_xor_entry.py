from pathlib import Path
import json,time,hashlib,re,shutil
TB=Path(__file__).resolve().parents[1];ROOT=Path('/data/netg/ACSG');R=TB/'research/xor_entry_expressivity_v1'
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def ident(p):p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
assert not (R/'complete.json').exists();c=read(R/'config.locked.json');v=read(R/'result.json');jobs=read(R/'jobs.json');assert v['status']=='PASS' and v['synthetic_calls']==8
for x in c['sources']:assert ident(x['path'])==x
for j in jobs:assert j['exit_code']==0 and not Path('/proc',str(j['pid'])).exists()
observations=v['observations'];assert len(observations)==8
for q in [(-1,-1,1),(-1,1,1),(1,-1,1),(1,1,1)]:
    a=[x for x in observations if tuple(x['query'])==q];assert len(a)==2 and sum(x['hit'] for x in a)==1 and all(x['GT1']==14 and x['GT1_margin']==79 for x in a)
text='''# 非线性选择是否必须使用神经网络

2026-09-20，**TWO_ENTRY_XOR_EXPRESSIVITY_VERIFIED**。理论能力例子，0真实NSG/ANN/query或GT载荷读取/训练/正式QPS。固定一张人工强连通图、四个query、同一个唯一GT1；8次原ResearchKernel调用恢复全部预定返回。

## 图搜索确实能产生线性不可分的入口偏好

设q=(x,y,1)，x,y为±1；只有两个可选单入口A/B。图、向量和K=L=1都固定。第一层按x的符号选分支，第二层按y的符号选分支；A的同号支路到目标，B的异号支路到目标，错误支路停在局部点。所有query的目标向量t=(0,0,100)，得分100；其他节点最高分21，严格GT1间隔79。

| x | y | A命中GT1 | B命中GT1 | 最优入口 |
|---:|---:|---:|---:|---|
| −1 | −1 | 1 | 0 | A |
| −1 | +1 | 0 | 1 | B |
| +1 | −1 | 0 | 1 | B |
| +1 | +1 | 1 | 0 | A |

若每个入口只有一个静态线性分数，即使允许偏置，两者之差也只是`a*x+b*y+c`。两个同号点均判A，要求`a+b+c>0`和`−a−b+c>0`，相加得c>0；两个异号点均判B，要求`a−b+c<0`和`−a+b+c<0`，相加得c<0，矛盾。固定并列优先A时，同号可用≥但异号仍须<，相同矛盾；优先B时相反。平衡四点分布的最好线性分类最多3/4，而特权最优为1。

这证明“两固定动作各一个线性评分”并不总能表达有限池图搜索的最优入口。它没有证明当前约800个hub、三入口联合动作和ANN下的WFree不能表示某个真实教师，更没有证明本项目QMLP失败只因容量不足。

## 两种不同的表示都能解这个例子

一种是简单非线性query特征`f(q)=(|x+y|,|x−y|)`，按两维大小选A/B；绝对值可以用4个ReLU单元表达，没有序贯决策或RL需求。

另一种保留原query，用四个线性画像`(1,1,0)、(−1,−1,0)、(1,−1,0)、(−1,1,0)`，前两个映射A、后两个映射B。每个query唯一最高分画像就是其角点，得分2，其余为0或−2；因此同样100%选择最优入口。原始坐标未变，每个真实入口允许两个画像。两种解析选择均在原核验程序逐query检查，没有模型训练或小图ANN。

所以，最优入口区域非线性，只能要求调整受限表示，**不能唯一推出必须使用MLP**。多画像还增加索引规模及真实ID去重成本，query网络增加在线计算；本例没有比较这些成本。项目已有多画像和QMLP版本，本次不重开它们，也不提供论文新颖性声明。XOR不可分本身是基础事实，图构造只把它接到有限池搜索。

## 条件、成本与复查

人工图有15个节点、最大出度2；全部节点出发的BFS确认强连通。它不是NSG构图程序产生的近邻图，L1也不是当前两数据集的性能预算。作用限排除一般图上过强的线性充分性推断。不能从人工成功率推断真实收益、训练难度或泛化。

'''+f"合成调用8次、人工图1张，编译进程{jobs[0]['seconds']:.6f}秒、合成进程{jobs[1]['seconds']:.6f}秒，CPU15/单线程；两个登记进程均正常结束。独立检查四query各恰有一个正确入口、共同GT1与间隔。\n\n"+'''[冻结协议](protocol.md) · [完整图/向量/返回](result.json) · [原内核核验源码](verify.cpp) · [旧线性即可分反例](../query_branch_stability_v1/protocol.md) · [真实E104停止](../../../../experiment_history/98_query_representation_pilot.md)。默认与生产保持，无新训练队列。
'''
(R/'report.md').write_text(text)
dump(R/'completion_audit.json',dict(status='PASS',sources_verified=len(c['sources']),jobs_closed=2,query_action_rows=8,synthetic_calls=8,real_NSG_calls=0,ANN_calls=0,new_training=0,new_dataset_graphs=0,report=ident(R/'report.md'),files=[ident(p) for p in R.rglob('*') if p.is_file()]))
dump(R/'complete.json',dict(status='COMPLETE',completed_unix=time.time(),decision='TWO_ENTRY_XOR_EXPRESSIVITY_VERIFIED',synthetic_calls=8,real_NSG_calls=0,ANN_calls=0,synthetic_graphs=1,report=ident(R/'report.md'),audit=ident(R/'completion_audit.json')))
s=read(TB/'state.json');assert s['synthetic_calls']==4;s['synthetic_calls']=12;s['stage']='Final theory synthesis and audit';dump(TB/'state.json',s)
hist=ROOT/'experiment_history/115_routing_representation_theory.md';assert not hist.exists()
hist.write_text('''# 115｜小图几何解释与入口表示的理论边界

2026-09-20，理论复核，不是新学习候选。承接E115成本分解后，进一步限制“更集中→图更稀疏”和“非线性→必须MLP”的推理。

HNSW原文§3/§4算法4与本地剪枝源码表明，其决定依赖候选与已选邻居的相对距离；最终未满行也未必经完整剪枝。基础共同分量嵌入保持所有距离统一正比例，能使方向任意集中、绝对方差趋近0，却保持逻辑构图/路由比较；需固定层级/顺序/参数及精确算术。36个有理数距离、216个比较符号例子核验，0搜索/图。未降低中心化秩，故不否定所有内在维度解释。

另一个冻结人工强连通15节点raw-IP图，4query×2入口、K=L1，共8次原内核合成调用；同一唯一GT1下，最优入口呈XOR，两入口各单个线性分数无法完全表达。四个线性画像映射两个入口，或简单绝对值query特征都可表达。只证明两固定动作的能力边界，不是当前约800hub/三入口WFree不可能性、真实MLP必要性或新颖性证明。

0新真实NSG/ANN/GT载荷/训练/数据集图/正式QPS；人工图1张，原始8返回及向量边完整保留。旧QMLP/多画像/E95及E115停止保持，默认和生产E99不变。

[小图几何条件](../entry_method_exploration/20260920_until1900_theory_v1/research/routing_geometry_scope.md) · [XOR报告/证明/成本](../entry_method_exploration/20260920_until1900_theory_v1/research/xor_entry_expressivity_v1/report.md)。
''')
docs=['summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md'];before=TB/'reviews/representation_scope_documents_before';before.mkdir()
for rel in docs:p=before/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/rel,p)
def prepend(rel,text):
    p=ROOT/rel;head,rest=p.read_text().split('\n\n',1);p.write_text(head+'\n\n'+text+'\n\n'+rest)
link='[记录115](experiment_history/115_routing_representation_theory.md)'
prepend('summary.md','2026-09-20 **表示能力与几何解释边界补充完成**：人工图8次原内核调用验证同GT1的最优入口可呈XOR，两入口单线性分数不足；简单非线性与四线性画像均可解决，未证明真实数据必须MLP。另给保距离顺序的集中化反例，集中度本身不能解释图更稀疏。0新增真实搜索/训练，原停止与默认保持。'+link+'。')
prepend('spec.md','2026-09-20独立XOR合成核验器复用冻结ResearchKernel：固定15节点3维raw-IP强连通图、4query×2单入口、K=L1；8返回及严格共同GT1、四画像/非线性解析决策一致。只作人工能力边界，不接入生产或真实评测；另有有理数几何恒等式检查，0ANN/数据集图/训练。'+link+'。')
prepend('s-experiment.md','2026-09-20理论边界补充：共同分量集中化保持逻辑距离比较；人工图8次kernel核验XOR入口偏好，多画像和简单非线性均能表达。非真实改进/新模型，默认保持。'+link+'。')
p=ROOT/'experiment_history/README.md';p.write_text(p.read_text().replace('|---|---|\n','|---|---|\n| [115 路由表示理论边界](115_routing_representation_theory.md) | 集中化保序反例、两入口XOR、多画像与非线性替代表达 |\n',1))
p=ROOT/'s-target.md';t=p.read_text();t=t.replace('当前只做理论综合、成本与身份审查至19:00','表示能力/XOR及小图几何条件审查也已完成，未产生新模型；当前只做理论综合、成本与身份审查至19:00',1);p.write_text(t)
files=[hist,R/'report.md',R/'complete.json',TB/'research/routing_geometry_scope.md',TB/'reviews/routing_geometry_exact_arithmetic.json'];links=0
for p in files+[ROOT/x for x in docs]:
    if p.suffix!='.md':continue
    for dest in re.findall(r'\]\(([^)]+)\)',p.read_text()):
        if '://' in dest or dest.startswith('#'):continue
        assert (p.parent/dest.split('#')[0]).resolve().exists(),(p,dest);links+=1
dump(TB/'reviews/representation_scope_complete.json',dict(status='PASS',created_unix=time.time(),files=[ident(p) for p in files],documents=[ident(ROOT/x) for x in docs],local_links=links,synthetic_calls=8,real_NSG_calls=0,ANN_calls=0,default_changed=False,overall_goal_complete=False))
print(json.dumps(dict(status='COMPLETE',synthetic_calls=8,compile_seconds=jobs[0]['seconds'],synthetic_seconds=jobs[1]['seconds'],links=links,report=ident(R/'report.md')),indent=2))
