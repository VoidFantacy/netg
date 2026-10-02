from shared import *
import csv,collections
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
threads();assert read(O/'reviews/verification.json')['status']=='PASS'
points=list(csv.DictReader((O/'results/points.csv').open()));cases=list(csv.DictReader((O/'results/catastrophic_cases.csv').open()));cost=read(O/'results/cost.json')
def p(ds,n,phase):return next(x for x in points if x['dataset']==ds and x['model']==n and x['phase']==phase)
categories=['S only zero','T only zero','Both zero','Neither zero'];counts=[]
for ds in DS:
    rows=[x for x in cases if x['dataset']==ds];cnt=collections.Counter(('Both zero' if x['S_zero']=='True' and x['T_zero']=='True' else 'S only zero' if x['S_zero']=='True' else 'T only zero' if x['T_zero']=='True' else 'Neither zero') for x in rows)
    counts.append([cnt[k] for k in categories])
dump(O/'results/catastrophic_summary.json',dict(datasets=[dict(dataset=ds,counts=dict(zip(categories,v)),selected_condition='baseline fit hits10 and A hits0; endpoint-specific, not predictive stratum') for ds,v in zip(DS,counts)]))
(O/'figures').mkdir(exist_ok=True)
fig,axes=plt.subplots(3,2,figsize=(11.5,10),layout='constrained')
for di,ds in enumerate(DS):
    for j,(name,label,color) in enumerate([('A','Both factors','#64748b'),('S','Score only','#2563eb'),('T','Topology only','#d97706')]):
        pts=[p(ds,name,ph) for ph in ['fit','cal','audit']];x=np.arange(3)+(j-1)*.25
        axes[0,di].bar(x,[float(z['delta_recall_pp']) for z in pts],.25,label=label,color=color)
        axes[1,di].bar(x,[int(z['failure_queries'])-int(p(ds,'C',ph)['failure_queries']) for z,ph in zip(pts,['fit','cal','audit'])],.25,color=color)
    for r in [0,1]:axes[r,di].set(xticks=np.arange(3),xticklabels=['Fit 20K','Historical cal','Historical audit']);axes[r,di].axhline(0,color='#6b7280',lw=.7)
    axes[0,di].set_title(['WebVid','Yandex'][di]);axes[0,di].legend(fontsize=8);axes[0,di].set_ylabel('Recall change (pp)');axes[1,di].set_ylabel('Zero-hit failure count change')
    bars=axes[2,di].bar(categories,counts[di],color=['#2563eb','#d97706','#9333ea','#059669']);axes[2,di].bar_label(bars);axes[2,di].set_ylim(0,max(counts[di])+2);axes[2,di].set_ylabel('Count within A catastrophes');axes[2,di].set_title('C hits=10, A hits=0: fixed-endpoint cases',fontsize=10)
fig.suptitle('E62: fixed score/topology intervention; L128 development, no formal QPS',fontsize=13)
for ext in ['png','svg','pdf']:fig.savefig(O/'figures'/f'factorial_and_failures.{ext}',dpi=170)
plt.close(fig)
table=[]
for ds,dsname in zip(DS,['WebVid','Yandex']):
    for name in ['A','S','T']:
        q=[p(ds,name,ph) for ph in ['fit','cal','audit']]
        table.append(f"| {dsname} | {name} | "+' / '.join(f"{float(z['delta_recall_pp']):+.4f}" for z in q)+' | '+' / '.join(z['net_hits'] for z in q)+' | '+' / '.join(f"{int(z['failure_queries'])-int(p(ds,'C',ph)['failure_queries']):+d}" for z,ph in zip(q,['fit','cal','audit']))+' |')
text='''# E62：遗漏画像的评分／邻接固定四格

2026-09-13，`COMPLETE_MISSING_FACTORIAL_NO_CAL_GO`。S/T双集cal均失败，固定选择均C；没有新的推荐或正式QPS结论。E61已有audit微弱正值及本轮WebVid T的fit微弱正值分别保留，不能扩写为稳健改进。

## 固定干预与数据

C=(P,G0)，A=(Wmissing,Gmissing)，S=(Wmissing,G0)，T=(P,Gmissing)。Wmissing为E61固定lambda0.5真实遗漏成员画像；全层有序邻接取同一已冻结端点，安装后实际图中的所有评分向量、真实ID、节点层级和邻接逐字核验。H815/821、三个真实入口、原NSG/base/raw-IP/GT/L128不变。S/T须加载保存的物理图，不能对其评分W普通重建来代替该图。

这沿用E48/E54已实现的干预接口，研究对象换成E61全fit闭式画像；没有重启旧局部RL runner或增加训练。每集22048行，前20K为历史P-fit，后1024/1024为历史cal/audit，全部已使用。C/A全量路由恢复E61；S/T只对完整有序三入口改变行新增NSG，其余复用C。未读取E34最终评估数据，所有本轮反馈仅有开发身份。

## 同L实测及固定选择

下表每组三数依次fit / cal / audit。失败定义为返回top10与exact GT10交集为空；hits=1不算失败。

| 数据集 | 状态 | ΔRecall pp | 净命中 | 零命中数变化 |
|---|---|---|---|---|
'''+ '\n'.join(table)+f'''

cal选择预锁S/T净命中>0、失败数不增加、平均totalNDC≤C×1.01；四个S/T均净命中负。WebVid S的失败数持平，其余三个增加。全部NDC门通过，仍没有候选通过完整门。WebVid T在fit仅+14命中（+0.007 pp）而cal−18、audit−3；Yandex T在三个组均负。audit A的正值依赖因素组合，不能用它选择S/T或重挑lambda。

## 34个灾难性案例的条件责任

只看E61 A将原全命中变为零命中的14条WebVid、20条Yandex，实际S/T命中均为0或10，逐条namespace/source row、三入口和四格hits均已存档。

- WebVid：只S仍零6条，只T仍零4条，两者各自都零1条，S/T各自均恢复10而组合A才零3条。
- Yandex：只S仍零11条，只T仍零7条，两者各自都零1条，只有组合A零1条。

因此评分和拓扑分别都能在部分案例独立致损，且存在组合才发生及两个单独因素都足以发生的病例。不能把全部损伤归给图，或声称冻结评分便可消除损伤。因素交互I=hA−hS−hT+hC的fit总和WebVid−1、Yandex+54；总和小不代表逐query可加，WebVid357、Yandex83条fit交互非零。正交互只指相对两单因子相加的差，不代表绝对获益。

完整11个baseline hits组均独立计算找回/丢失GT成员、净收益与失败转换。原极端组的增损方向受上下界影响，不把这些事后分组当作可预测的困难query策略。此四格不含sham构图，因而没有“真实遗漏身份导致拓扑收益”的归因结论。

## 成本与验收

新增 {cost['NSG_calls']:,} NSG、{cost['HNSW_calls']:,} HNSW、8次小图构建、4次拓扑安装；C/A复用E61的88192行，S/T复用70698行，新增交叉状态实际NSG17494，parity另1536。原生阶段含加载合计{cost['native_phase_seconds']:.3f}s，属于本轮实际操作耗时，绝非QPS；分项build/install/route/NSG/cache/score/I/O在cost.json。Yandex曾与一次提前启动的只读分析短暂重叠，该分析因未完成标记退出，加入完成门后独立重跑；原日志和[调度说明](reviews/execution_note.md)保留。不能把这段wall称为严格独占机器性能时间。

176384返回集合与GT10 mask独立重评分、176384完整缓存行、88192 C/A路由逐位恢复、8物理图全画像/拓扑、512行三路parity和34关键案例通过。实际native均CPU15/threads1，双集顺序启动，全部已退出。0新GT、0梯度更新、0正式QPS。

停止E61强度扫描和单纯去除某一个因素的扩展。后续可考虑保持原GT10成员归属、直接增加原零命中query训练质量的固定难度对照，但它未实现/未运行，须与旧E09难度残差区别并设置随机query身份控制、总质量和raw-prior一致；本轮结果不保证它成功。今日最终比较应包含当天实际新候选，即使best_all仍为原P，也须独立冻结best_new诚实展示失败及曲线，不能只画baseline对自身。当前整日目标未完成。

[协议](protocol.md)、[数据角色](reviews/input_audit.json)、[四格指标](results/points.csv)、[11组得失](results/fit_cal_audit_hit_cohorts.csv)、[34关键案例](results/catastrophic_cases.csv)、[因素交互](results/interactions.csv)、[固定cal选择](results/selection.json)、[成本](results/cost.json)、[验收](reviews/verification.json)、[图](figures/factorial_and_failures.svg)。
'''
(O/'report.md').write_text(text)
print('E62_REPORT_READY',counts,flush=True)
