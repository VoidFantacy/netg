from shared import *
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
threads(); assert read(O/'reviews/verification.json')['status']=='PASS'
points=list(csv.DictReader((O/'results/points.csv').open()));groups=[];cases=[]
for ds in DS:
    c=read(O/'inputs'/ds/'config.json');rows=np.fromfile(c['row_ids'],np.int64)
    baseline=dict(np.load(O/'results'/ds/'baseline/raw.npz'))
    for name in LABELS[1:]:
        raw=dict(np.load(O/'results'/ds/name/'raw.npz'));b=baseline['hits'].astype(int);h=raw['hits'].astype(int)
        bm=baseline['hitmask'];hm=raw['hitmask'];gain=np.array([int(x).bit_count() for x in hm&(~bm&1023)]);loss=np.array([int(x).bit_count() for x in bm&(~hm&1023)])
        assert np.array_equal(gain-loss,h-b)
        for phase,(lo,hi) in c['roles'].items():
            for k in range(11):
                ix=np.flatnonzero((b[lo:hi]==k))+lo
                groups.append(dict(dataset=ds,model=name,phase=phase,baseline_hits=k,queries=len(ix),members_gained=int(gain[ix].sum()),members_lost=int(loss[ix].sum()),net_hits=int((h[ix]-b[ix]).sum()),
                   rescued=int(((b[ix]==0)&(h[ix]>0)).sum()),new_failures=int(((b[ix]>0)&(h[ix]==0)).sum()),changed_entries=int((raw['entries'][ix]!=baseline['entries'][ix]).any(1).sum())))
            ix=np.flatnonzero(((b[lo:hi]==0)&(h[lo:hi]>0))|((b[lo:hi]>0)&(h[lo:hi]==0)))+lo
            for i in ix:
                cases.append(dict(dataset=ds,model=name,phase=phase,source_namespace=c['namespace'],source_row=int(rows[i]),local_row=int(i),baseline_hits=int(b[i]),new_hits=int(h[i]),
                 member_gain=int(gain[i]),member_loss=int(loss[i]),baseline_entries=' '.join(map(str,baseline['entries'][i])),new_entries=' '.join(map(str,raw['entries'][i])),kind='rescued' if b[i]==0 else 'new_failure'))
        save(O/'results'/ds/(name+'_members.npz'),source_rows=rows,baseline_hits=b,new_hits=h,members_gained=gain,members_lost=loss,baseline_mask=bm,new_mask=hm)
for file,records in [('cohorts',groups),('failure_cases',cases)]:
    with (O/'results'/f'{file}.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
def p(ds,n,phase):return next(x for x in points if x['dataset']==ds and x['model']==n and x['phase']==phase)
fig,axes=plt.subplots(2,3,figsize=(14,7.4));phases=['fit','cal','audit'];x=np.arange(3)
for row,(ds,label) in enumerate(zip(DS,['WebVid','Yandex'])):
    for name,color,offset in [('zero_mass2','#087e8b',-.19),('sham_mass2','#e68a2e',.19)]:
        vals=[p(ds,name,s) for s in phases]
        for col,key in [(0,'delta_recall_pp'),(1,'failure_queries'),(2,'total_NDC_change_pct')]:
            y=[float(a[key])-(float(p(ds,'baseline',s)[key]) if col==1 else 0) for a,s in zip(vals,phases)]
            bars=axes[row,col].bar(x+offset,y,.36,label=name,color=color)
            axes[row,col].bar_label(bars,fmt='%+.3f' if col!=1 else '%+.0f',fontsize=8,padding=3)
    for col,title in enumerate(['Recall change (pp)','Zero-hit failure count change','Total NDC change (%)']):
        ax=axes[row,col];ax.axhline(0,color='#667085',lw=.8);ax.set_xticks(x,phases);ax.set_title(label+' — '+title);ax.grid(axis='y',alpha=.18);ax.margins(y=.3)
axes[0,0].legend(fontsize=8)
fig.suptitle('E63: fixed 2x zero-hit query mass; same total mass and GT10 attribution',fontsize=14)
fig.text(.5,.015,'Historical fit/cal/audit • L128 • CPU15 / 1 thread • Development diagnostics; no QPS measurement',ha='center',fontsize=10)
fig.tight_layout(rect=(0,.04,1,.95));(O/'figures').mkdir(exist_ok=True)
for ext in ['png','svg','pdf']:fig.savefig(O/'figures'/f'development_metrics.{ext}',dpi=180)
cost=read(O/'results/cost.json');build=read(O/'results/build.json');verify=read(O/'reviews/profile_verification.json');selection=read(O/'results/selection.json')
table=[]
for ds,label in zip(DS,['WebVid','Yandex']):
    for phase in phases:
        a=p(ds,'zero_mass2',phase);b=p(ds,'baseline',phase);s=p(ds,'sham_mass2',phase)
        table.append(f"| {label} | {phase} | {float(a['delta_recall_pp']):+.4f} | {a['gain_hits']}/{a['loss_hits']} | {b['failure_queries']}→{a['failure_queries']} | {a['rescued']}/{a['new_failures']} | {float(s['delta_recall_pp']):+.4f} |")
lines=['# E63 零命中query质量重权', '', '固定2倍质量的真实/随机query对照已完成；开发门结果：'+', '.join(x['dataset']+'='+x['selected'] for x in selection['datasets'])+'。这只是历史开发集判断，无正式QPS，原默认不替换。', '',
'保持原GT10 hard/soft成员归属，原P的348/311条零命中fit query质量加倍，总质量归一回20000、raw prior保持1。另以固定seed随机选同数量query作sham。没有调强度或选择随机seed，sham不参与推荐。在线仍一份普通Micro-HNSW top3→三个真实入口→原NSG，H815/821、raw-IP、base、GT、大图均未改。', '',
'E09是top32单入口signed advantage/hardness残差，本轮是完整GT10正权聚合，机制不同但不作新颖性声称。E09 WebVid微弱正值保留。P-fit包含旧train/monitor，cal/audit均历史与今日暴露；Fast30K也使用全router_train。不称盲测，E34最终validation未参与训练/选型。', '',
'| 数据集 | 分组 | zero ΔRecall pp | 增益/损伤hits | 零命中数 | 救回/新增失败 | sham ΔRecall pp |','|---|---|---:|---:|---:|---:|---:|']+table+['',
'cal只按净命中>0、零命中数不增、mean totalNDC≤+1%选择，先冻结selection再汇总audit；audit不回选。失败严格是返回top10与exact GT10交集为空。完整11组GT成员周转与逐query净值分开，极端原命中组的单向变化受上下界影响，不是可预测收益证明。', '',
f"新增{cost['NSG_calls']:,} NSG、{cost['HNSW_calls']:,} HNSW、6小图；原生操作{cost['native_phase_seconds']:.3f}秒含加载，画像assignment/聚合{build['seconds']:.3f}秒、独立画像验收{verify['seconds']:.3f}秒，身份核验与准备另计。44096历史基线返回生成成本不当零。0新GT/梯度更新/正式QPS，缓存比例和NDC均不能换算性能。", '',
'原A0 SHA与P bytes恢复，六画像独立逐rank聚合、40000 zero-hit身份/随机集合重放、总质量/先验恒等通过。132288返回集合/mask、六物理图全字节、44096原路由恢复与384三路parity通过。全部native在CPU15实际线程1串行退出，分析在两job完成后执行。', '',
'[协议](protocol.md) · [指标](results/points.csv) · [选择](results/selection.json) · [11组](results/cohorts.csv) · [失败案例](results/failure_cases.csv) · [成本](results/cost.json) · [验收](reviews/verification.json) · [画像验收](reviews/profile_verification.json) · [图](figures/development_metrics.svg)']
(O/'report.md').write_text('\n'.join(lines)+'\n');print('E63_REPORT_READY',len(cases),'failure transitions')
