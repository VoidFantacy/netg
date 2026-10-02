from common import *
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
threads();assert read(O/'reviews/verification.json')['status']=='PASS'
points=list(csv.DictReader((O/'results/points.csv').open()));paired=list(csv.DictReader((O/'results/paired.csv').open()));interp=list(csv.DictReader((O/'results/frontier_interpolation.csv').open()));cost=read(O/'results/cost.json')
selection=read(O/'results/frozen_selection.json')['datasets'];(O/'figures').mkdir(exist_ok=True)
colors={'nsg':'#697386','fast30k':'#1673b8','gt10_hard':'#e39125','baseline_soft':'#30946e','best_new':'#ac3c85','duplicate3P':'#627fbe'}
base_labels={'nsg':'NSG','fast30k':'Fast30K (GT1)','gt10_hard':'FastGT10-hard','baseline_soft':'GT10-soft (matched)','duplicate3P':'Duplicate3P control'}
def pp(ds,name):return sorted([p for p in points if p['dataset']==ds and p['model']==name],key=lambda x:int(x['L']))
def names(ds):return ['nsg','fast30k','gt10_hard']+(['baseline_soft'] if ds==DS[0] else [])+['duplicate3P','best_new']
def label(ds,name):return base_labels.get(name,'New: '+selection[ds]['best_new'])
def export(fig,name):
    for ext in ['png','svg','pdf']:fig.savefig(O/'figures'/f'{name}.{ext}',dpi=180)
    plt.close(fig)
foot='Historical development 2,048 queries already used for selection • CPU15 / 1 thread • Five full batch walls • Not final validation'
for key,xlabel,file in [('recall_pct','Recall@10 (%)','recall_qps'),('failure_rate_pct','GT10 zero-hit failure rate (%)','failure_qps')]:
    fig,axes=plt.subplots(1,2,figsize=(13,5.5))
    for ax,ds,title in zip(axes,DS,['WebVid','Yandex']):
        for name in names(ds):
            ps=pp(ds,name);x=[float(p[key]) for p in ps];q=np.array([float(p['QPS']) for p in ps]);low=np.array([float(p['QPS_min']) for p in ps]);high=np.array([float(p['QPS_max']) for p in ps])
            ax.plot(x,q,'o-',label=label(ds,name),color=colors[name],markersize=4,lw=1.4);ax.fill_between(x,low,high,color=colors[name],alpha=.13)
        ax.set(title=title,xlabel=xlabel,ylabel='QPS (median; shade = five-run range)');ax.set_yscale('log');ax.grid(alpha=.2);ax.legend(fontsize=8)
    fig.suptitle('E67 — '+('Recall–QPS' if key=='recall_pct' else 'Failure rate–QPS'),fontsize=15);fig.text(.5,.014,foot,ha='center',fontsize=9);fig.tight_layout(rect=(0,.05,1,.94));export(fig,file)
fig,axes=plt.subplots(2,3,figsize=(14,8))
for row,(ds,title) in enumerate(zip(DS,['WebVid','Yandex'])):
    for name in names(ds):
        ps=pp(ds,name);x=np.arange(5)
        for col,(key,ylabel) in enumerate([('recall_pct','Recall@10 (%)'),('QPS','QPS (median)'),('failure_rate_pct','Zero-hit failures (%)')]):
            ax=axes[row,col];ax.plot(x,[float(p[key]) for p in ps],'o-',color=colors[name],label=label(ds,name),markersize=4,lw=1.3);ax.set_xticks(x,[64,128,256,400,800]);ax.set(xlabel='Search L',ylabel=ylabel,title=title+' — '+ylabel);ax.grid(alpha=.2)
            if col==1:ax.set_yscale('log')
    axes[row,0].legend(fontsize=8)
fig.suptitle('E67 — all three measured metrics by L',fontsize=15);fig.text(.5,.01,foot,ha='center',fontsize=9);fig.tight_layout(rect=(0,.04,1,.94));export(fig,'three_metrics_by_L')
fig,axes=plt.subplots(2,2,figsize=(12,7))
for row,(ds,title) in enumerate(zip(DS,['WebVid','Yandex'])):
    comparator='baseline_soft' if ds==DS[0] else 'gt10_hard'
    vals=sorted([p for p in paired if p['dataset']==ds and p['comparator']==comparator],key=lambda p:int(p['L']));x=np.arange(5)
    recall=np.array([float(p['delta_recall_pp']) for p in vals]);qps=np.array([float(p['QPS_change_pct']) for p in vals])
    axes[row,0].plot(x,recall,'o-',color='#ac3c85');axes[row,0].fill_between(x,[float(p['descriptive_query_bootstrap_low_pp']) for p in vals],[float(p['descriptive_query_bootstrap_high_pp']) for p in vals],color='#ac3c85',alpha=.12)
    axes[row,1].plot(x,qps,'o-',color='#ac3c85');axes[row,1].fill_between(x,[float(p['all_range_low_pct']) for p in vals],[float(p['all_range_high_pct']) for p in vals],color='#ac3c85',alpha=.12)
    for col,yl in enumerate(['Recall change (pp)','QPS change (%)']):
        ax=axes[row,col];ax.axhline(0,color='gray',lw=.8);ax.set_xticks(x,[64,128,256,400,800]);ax.set(title=title+' new vs matched GT10',xlabel='Search L',ylabel=yl);ax.grid(alpha=.2)
fig.suptitle('E67 — paired changes; bands: query bootstrap / timing ranges',fontsize=15);fig.text(.5,.01,foot,ha='center',fontsize=9);fig.tight_layout(rect=(0,.04,1,.94));export(fig,'paired_deltas')
table=[];differences=[]
for ds,title in zip(DS,['WebVid','Yandex']):
    comparator='baseline_soft' if ds==DS[0] else 'gt10_hard'
    for p in points:
        if p['dataset']==ds:
            table.append(f"| {title} | {label(ds,p['model'])} | {p['L']} | {float(p['recall_pct']):.4f} | {float(p['QPS']):.2f} [{float(p['QPS_min']):.2f}, {float(p['QPS_max']):.2f}] | {float(p['failure_rate_pct']):.4f} ({p['failure_count']}) |")
    a=[p for p in paired if p['dataset']==ds and p['comparator']==comparator];dr='/'.join(f"{float(p['delta_recall_pp']):+.4f}" for p in a);speed='/'.join(f"{float(p['QPS_change_pct']):+.3f}%" for p in a);netfail='/'.join(f"{int(p['new_failures'])-int(p['rescued']):+d}" for p in a)
    range_cross=sum(float(p['all_range_low_pct'])<=0<=float(p['all_range_high_pct']) for p in a)
    ip=[p for p in interp if p['dataset']==ds];ir='/'.join(f"{float(p['change_pct']):+.3f}%" for p in ip)
    differences.append(f"{title}：相对匹配起点，按L64/128/256/400/800的ΔRecall为{dr} pp；QPS中位变化{speed}，{range_cross}/5点的五轮交叉范围含零方向；失败净新增{netfail}条。共同Recall区间三个内部点的描述性log-QPS插值变化为{ir}，它们不是实测同Recall点。")
report=['# E67 多画像方法的完整开发QPS–Recall与失败汇报','',
'55个方法点、275轮单线程完整wall已完成。新方法固定E66 mode3P，同容量duplicate3P为控制；两集E66开发门失败保持，所有局部正负只支持历史开发范围，整日最终目标未完成。','',
'E66中WebVid fit/aux均净负；Yandex fit+164、aux+49且失败减少，但两半−14/+63。这里不按新曲线换模型、ef、seed或阈值。source[2048:4096]开发2048已用于E66辅助训练/选择，不能作为最终泛化集。','']+differences+['',
'同批包含NSG、原Fast30K/GT1、GT10-hard20K和WebVid匹配GT10-soft。新方法与duplicate均为同一3H微型图检索7slot，按距离/slot去重3真实入口，原NSG/base/raw-IP/GT/H不变；真实入口815/821与画像节点2445/2463分账。保留原P并不保证原路由不变。','',
'| 数据集 | 方法 | L | Recall@10 % | QPS中位数 [五轮范围] | 零命中率 %（条数） |','|---|---|---:|---:|---:|---:|']+table+['',
'失败严格zero GT10，hits1不失败。paired表的gain_hits/loss_hits为逐query净命中变化正负部；实际GT10成员找回/丢失另在member_deltas.csv，两者净值相同但不混用。重复wall不是独立Recall样本；query bootstrap、五轮范围和共同Recall插值仅作描述，不由小中位差或同LRecall给性能GO。','',
f"实际新增{cost['NSG_calls']:,} NSG、{cost['HNSW_calls']:,} HNSW，45物理源图加载/复制、90 plain/count加载；0新构图/画像/GT/梯度。native操作{cost['native_job_seconds']:.3f}s含加载/计数/I/O，纯wall单独保存。route-only/graph-only未额外测量，null+原因。",'',
'完整计时包含raw-query路由、去重/映射、原NSG、预分配输出，GT/count/hash/JSON/build/load在外。CPU15实际进程/OMP/BLAS/MKL1，单个被测方法串行，一次完整预热、五轮按dataset/repeat/L轮换。所有工具terminal退出后才分析。112640集合/mask、880原kernelparity、45图bytes、五L相同slot/真实入口和275轮QPS恒等通过；全部71680原基线输出恢复E65，12288个L128新/duplicate/匹配起点输出恢复E66。','',
'原E66开发门保持，本阶段完整wall不变更模型或选型。E34最终validation及held-out未打开；晚间20:00停训练、20:40停新增查询、21:00交付仍待接续。', '',
'[协议](protocol.md) · [全部点](results/points.csv) · [275轮wall](results/timings.csv) · [配对](results/paired.csv) · [GT成员增损](results/member_deltas.csv) · [失败query](results/failure_cases.csv) · [验收](reviews/verification.json) · [成本](results/cost.json)', '',
'[QPS–Recall](figures/recall_qps.svg) · [QPS–失败率](figures/failure_qps.svg) · [按L三指标](figures/three_metrics_by_L.svg) · [配对差值](figures/paired_deltas.svg)；同名PNG/PDF均保存。']
(O/'report.md').write_text('\n'.join(report)+'\n');print('E67_REPORT_READY')
