"""Generalized failure-case report; the copied E65-specific helper is not executed."""
from common import *
import csv,collections
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
threads();assert read(O/'reviews/verification.json')['status']=='PASS'
events=list(csv.DictReader((O/'results/failure_cases.csv').open()));groups=collections.defaultdict(list)
for event in events:groups[event['dataset'],int(event['source_row'])].append(event)
records=[];plot_data={};counts={};Ls=[64,128,256,400,800]
for ds in DS:
    ids=sorted(row for dataset,row in groups if dataset==ds);c=read(O/'inputs'/ds/'config.json');source_rows=np.fromfile(c['row_ids'],np.int64)
    local=[int(np.flatnonzero(source_rows==r)[0]) for r in ids];matched='baseline_soft' if ds==DS[0] else 'gt10_hard';before=[];after=[];entries={}
    for L in Ls:
        base=O/'results'/ds/f'{matched}_L{L}';new=O/'results'/ds/f'best_new_L{L}'
        before.append(np.fromfile(base/'hits.u8',np.uint8)[local]);after.append(np.fromfile(new/'hits.u8',np.uint8)[local])
        e0=np.fromfile(base/'entry_ids.i32',np.int32).reshape(-1,3)[local];e1=np.fromfile(new/'entry_ids.i32',np.int32).reshape(-1,3)[local]
        if entries:assert np.array_equal(entries['baseline'],e0) and np.array_equal(entries['new'],e1)
        entries=dict(baseline=e0,new=e1)
    b=np.asarray(before).T.astype(int);h=np.asarray(after).T.astype(int)
    for i,row in enumerate(ids):
        saved=groups[ds,row];newLs=[int(e['L']) for e in saved if e['kind']=='new_failure'];rescuedLs=[int(e['L']) for e in saved if e['kind']=='rescued']
        assert newLs==[L for j,L in enumerate(Ls) if b[i,j]>0 and h[i,j]==0];assert rescuedLs==[L for j,L in enumerate(Ls) if b[i,j]==0 and h[i,j]>0]
        records.append(dict(dataset=ds,source_namespace=next(x['source_namespace'] for x in read(O/'reviews/input_roles.json')['datasets'] if x['dataset']==ds),source_row=row,
            baseline_hits_by_L=' '.join(map(str,b[i])),new_hits_by_L=' '.join(map(str,h[i])),new_failure_Ls=' '.join(map(str,newLs)),rescued_Ls=' '.join(map(str,rescuedLs)),
            baseline_entries=' '.join(map(str,entries['baseline'][i])),new_entries=' '.join(map(str,entries['new'][i])),changed_entry_members=len(set(entries['new'][i])-set(entries['baseline'][i]))))
    harmed=sorted([i for i in range(len(ids)) if np.any((b[i]>0)&(h[i]==0))],key=lambda i:(int((h[i]-b[i]).min()),ids[i]))[:12]
    rescued=sorted([i for i in range(len(ids)) if np.any((b[i]==0)&(h[i]>0))],key=lambda i:(-int((h[i]-b[i]).max()),ids[i]))[:12]
    selected=list(dict.fromkeys(harmed+rescued));plot_data[ds]=(ids,b,h,selected)
    counts[ds]=dict(unique_queries=len(ids),events=sum(len(groups[ds,r]) for r in ids),shown=len(selected),all_five_L_pairs=5*len(ids))
fig,axes=plt.subplots(1,2,figsize=(13,10),layout='constrained')
for ax,ds,title in zip(axes,DS,['WebVid','Yandex']):
    ids,b,h,selected=plot_data[ds]
    if not selected:ax.text(.5,.5,'No zero-hit transitions',ha='center');continue
    diff=(h-b)[selected];ax.imshow(diff,cmap='RdYlGn',vmin=-10,vmax=10,aspect='auto')
    ax.set_xticks(range(5),Ls);ax.set_yticks(range(len(selected)),[ids[i] for i in selected]);ax.set(title=f"{title}: {counts[ds]['unique_queries']} total queries, {len(selected)} shown",xlabel='Search L',ylabel='router_train source row')
    for y,i in enumerate(selected):
        for x in range(5):ax.text(x,y,f'{b[i,x]}→{h[i,x]}',ha='center',va='center',fontsize=8,color='white' if abs(diff[y,x])>=7 else 'black')
fig.suptitle('E67: baseline hits → multimode hits\nUp to 12 largest-loss and 12 largest-gain failure-transition queries per dataset\nHistorical development; post-hoc display, no model selection',fontsize=12)
for ext in ['png','svg','pdf']:fig.savefig(O/'figures'/f'failure_query_cases.{ext}',dpi=180)
plt.close(fig)
with (O/'results/failure_query_summary.csv').open('x',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
section='\n\n## 失败查询\n\n'
for ds in DS:
    a=counts[ds];section+=f"{ds}有{a['unique_queries']}条独立query、{a['events']}次跨L的零命中转换事件。全表保存{a['all_five_L_pairs']}组五L命中和固定三入口；重复L不是独立样本。图按最大损失/收益分别至多12条的固定展示规则选{a['shown']}条，全部query仍在CSV。\n\n"
section+='[全部失败query与入口](results/failure_query_summary.csv) · [代表失败/救回图](figures/failure_query_cases.svg)。这些事后案例仅用于解释，不产生在线规则或最终选型反馈。\n'
report=(O/'report.md').read_text();assert '## 失败查询' not in report;(O/'report.md').write_text(report+section)
dump(O/'reviews/failure_query_verification.json',dict(status='PASS',zero_transition_events=len(events),unique_queries=len(records),datasets=counts,
    all_five_L_pairs_checked=5*len(records),entry_identity_across_L=True,new_searches=0,display_rule='up to 12 largest losses plus 12 largest gains per dataset; unique source rows'))
print('FAILURE_QUERY_PASS',counts,flush=True)
