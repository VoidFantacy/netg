from pathlib import Path
import json,shutil,hashlib,time
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
O=Path(__file__).resolve().parents[1];C=O.parent;R=C.parents[1];a=json.loads((O/'results/summary.json').read_text());rs=a['records']
fig,axs=plt.subplots(1,2,figsize=(11,4),constrained_layout=True)
for ax,r,title in zip(axs,rs,['WebVid','Yandex']):
 keys=['measured_support_events','fixed_set_eligible','actual_target_selected','actual_changed_triple','actual_support_gain_events'];labels=['Measured support','Fixed-set top-3','Actual target hub','Actual triple change','Positive NSG effect'];v=[r[k] for k in keys]
 ax.barh(labels,v,color=['#64748b','#8b5cf6','#0891b2','#d97706','#16a34a']);ax.invert_yaxis();ax.set_xlim(0,max(v)*1.2);ax.set_title(title+' | fit20K, event counts');ax.set_xlabel('Events (one query per measured proposal here)')
 for i,x in enumerate(v):ax.text(x+max(v)*.015,i,str(x),va='center')
fig.suptitle('E88: fixed-return-set ranking reference and actual single-edge response',fontsize=13)
fig.savefig(O/'figures/proposal_response.png',dpi=160);plt.close(fig)
text='''# E88 已测提议目标为何很少改变入口

仅复用冻结fit20K响应，新增ANN/训练/构图/GT/QPS均0。P完整策略更好，并不保证其独有hub在compact画像下排得足够高。

| 数据 | 已测边支持事件 | 固定集插入后目标hub可进前三 | 实际目标hub进前三 | 实际三入口变化 | NSG命中改善 |
|---|---:|---:|---:|---:|---:|
| Web | 167 | 19 | 19 | 20 | 17 |
| Y | 19 | 0 | 0 | 0 | 0 |

Web全1542提议事件中1375未对应被测候选；Y409中390未测，完整表这些实际响应留空。上述167/19恰为不同query，仅代表53/9被测边各自的支持query。Web67个目标本来就在七slot中，实际加边后94个目标返回；Y10个原本就在七slot中，仍全部落在三入口之外。对这组Y支持query，仅增加边不足以弥补目标画像的排序劣势。

排名用float64 query·W，在原七slot与目标的固定并集上排序、按真实hub去重；全部事件按另一lexsort顺序核验，目标与第三hub分差无近界事件。此参照不模拟HNSW路径；目标未返回不等于没访问，首返回source也不等于关键扩展节点。19和19汇总相等不自行证明逐事件因果等价；不能断言其它候选/打分/入口规则均无效。

Web所有独立边在各自支持query合计净+65命中、其余query净+55；支持外24个query-边收益事件和11个损伤事件。这里是独立干预的事件和，不能当合并图+120；E87实际选择16边后合并仅+94。Y两部分均0。完整SCORED行集合/mask评分通过。

下一步优先冻结晚间最终候选/矩阵。若另开实质研究，可先只用已暴露fit检查更好hub的画像竞争性，再设计新离线画像/打分目标；必须保留完整入口实际NSG反馈与冻结接受门，不能放宽E87旧support阈值试阳性。

[完整事件](results/events.csv) · [完整每边响应](results/edges.csv) · [汇总/成本](results/summary.json) · [协议](protocol.md) · [分析源码](src/analyze.py)

![排名与实际响应](figures/proposal_response.png)

fit含历史train/monitor，诊断用于下一方向设计亦属训练反馈；没有读aux响应、E34最终或held-out。首版语法错误发生在执行前，原稿保留；修正版一次成功，无实验重跑。操作wall不作查询性能。
'''.replace('SCORED',str(a['independently_scored_rows']))
(O/'report.md').write_text(text)
base='../entry_method_exploration/20260913_until2100_v1/stage29_proposal_rank_diagnosis_v1/'
htext=text
for prefix in ['results/','src/','figures/','protocol.md']:htext=htext.replace('('+prefix,'('+base+prefix)
(R/'experiment_history/77_proposal_rank_diagnosis.md').write_text(htext)
p=R/'experiment_history/README.md';p.write_text(p.read_text()+'\n[77 E88提议排名](77_proposal_rank_diagnosis.md)：0新ANN；167/19支持事件中19/0目标可进前三。\n')
p=R/'s-experiment.md';p.write_text(p.read_text().replace('| E87 真实策略收益提议目标','| E88 提议排名与实际响应诊断 | 冻结fit七slot/目标排名及实际边响应 | `COMPLETE_CACHED_PROPOSAL_RANK_DIAGNOSIS`；167/19支持事件中19/0目标可进前三，0新ANN/QPS | [77 排名诊断](experiment_history/77_proposal_rank_diagnosis.md) |\n| E87 真实策略收益提议目标',1).replace('当前最近完成记录为E87真实策略收益提议边','当前最近完成记录为E88提议排名与实际响应诊断'))
p=R/'summary.md';p.write_text(p.read_text()+'\nE88缓存诊断（0新ANN/训练）：被测边的Web167/Y19支持事件，固定原七slot插入目标后19/0个目标hub可进前三，实际亦19/0，NSG改善事件17/0。Y10个目标已在七slot仍无前三资格；这组边仅增加可达性不足。仅固定返回集排名参照，不是反事实搜索或普遍无效证明。见[历史77](experiment_history/77_proposal_rank_diagnosis.md)。\n')
p=R/'s-target.md';s=p.read_text();start=s.index('2. E87已完成');end=s.index('3. 优先保证',start);s=s[:start]+'2. E87停止，E88缓存诊断完成：Web167/Y19个被测边支持query中，目标固定集前三资格19/0，实际选中19/0，改善17/0。Y该组目标缺画像打分资格，继续扩边缺少证据。若开新研究，先从冻结fit检查P更好hub的画像竞争性，再前瞻定义新离线画像/打分目标；保留完整三入口真实NSG信用和冻结接受门。不从返回集推断路径、不直接放宽旧support/接受阈值。\n'+s[end:];p.write_text(s)
(O/'root_after').mkdir()
for f in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md']:shutil.copy2(R/f,O/'root_after'/f)
files=[]
for p in sorted(O.rglob('*')):
 if p.is_file():
  s=p.stat();files.append(dict(path=str(p),bytes=s.st_size,mtime_ns=s.st_mtime_ns,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
(O/'reviews/final_artifact_freeze.json').write_text(json.dumps(dict(epoch=time.time(),files=files),indent=2)+'\n')
assert sum(p.stat().st_size for p in O.rglob('*') if p.is_file())<8*2**20
print('E88_REPORT_SEALED',a['independently_scored_rows'])
