"""Post-hoc failure-query report from already verified raw results; zero new search."""
from common import *
import csv,collections
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
threads();assert read(O/'reviews/verification.json')['status']=='PASS'
events=list(csv.DictReader((O/'results/failure_cases.csv').open()));groups=collections.defaultdict(list)
for event in events:groups[event['dataset'],int(event['source_row'])].append(event)
records=[];fig,axes=plt.subplots(1,2,figsize=(13,7));Ls=[64,128,256,400,800]
for ax,ds,title in zip(axes,DS,['WebVid','Yandex']):
    ids=sorted(row for dataset,row in groups if dataset==ds);c=read(O/'inputs'/ds/'config.json');source_rows=np.fromfile(c['row_ids'],np.int64);local=[int(np.flatnonzero(source_rows==r)[0]) for r in ids]
    matched='baseline_soft' if ds==DS[0] else 'gt10_hard';before=[];after=[];entries={}
    for L in Ls:
        base=O/'results'/ds/f'{matched}_L{L}';new=O/'results'/ds/f'best_new_L{L}'
        before.append(np.fromfile(base/'hits.u8',np.uint8)[local]);after.append(np.fromfile(new/'hits.u8',np.uint8)[local])
        e0=np.fromfile(base/'entry_ids.i32',np.int32).reshape(-1,3)[local];e1=np.fromfile(new/'entry_ids.i32',np.int32).reshape(-1,3)[local]
        if entries:assert np.array_equal(entries['baseline'],e0) and np.array_equal(entries['new'],e1)
        entries=dict(baseline=e0,new=e1)
    b=np.asarray(before).T.astype(int);h=np.asarray(after).T.astype(int);im=ax.imshow(h-b,cmap='RdYlGn',vmin=-10,vmax=10,aspect='auto')
    ax.set_xticks(range(5),Ls);ax.set_yticks(range(len(ids)),ids);ax.set(title=title+' — baseline hits → new hits',xlabel='Search L',ylabel='router_train source row')
    for i,row in enumerate(ids):
        saved=groups[ds,row];newLs=[int(e['L']) for e in saved if e['kind']=='new_failure'];rescuedLs=[int(e['L']) for e in saved if e['kind']=='rescued']
        assert newLs==[L for j,L in enumerate(Ls) if b[i,j]>0 and h[i,j]==0];assert rescuedLs==[L for j,L in enumerate(Ls) if b[i,j]==0 and h[i,j]>0]
        for j in range(5):ax.text(j,i,f'{b[i,j]}→{h[i,j]}',ha='center',va='center',fontsize=10,color='white' if abs(h[i,j]-b[i,j])>=7 else 'black')
        records.append(dict(dataset=ds,source_namespace=next(x['source_namespace'] for x in read(O/'reviews/input_roles.json')['datasets'] if x['dataset']==ds),source_row=row,
           baseline_hits_by_L=' '.join(map(str,b[i])),new_hits_by_L=' '.join(map(str,h[i])),new_failure_Ls=' '.join(map(str,newLs)),rescued_Ls=' '.join(map(str,rescuedLs)),
           baseline_entries=' '.join(map(str,entries['baseline'][i])),new_entries=' '.join(map(str,entries['new'][i])),changed_entry_members=len(set(entries['new'][i])-set(entries['baseline'][i]))))
fig.suptitle('E65 — all queries with a zero-hit failure transition at any measured L',fontsize=14)
fig.text(.5,.015,'Post-hoc descriptive cohort • Historical development • Repeated L values are not independent queries • Green = more hits',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.04,1,.94))
for ext in ['png','svg','pdf']:fig.savefig(O/'figures'/f'failure_query_cases.{ext}',dpi=180)
with (O/'results/failure_query_summary.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
assert len(events)==24 and len(records)==14
y=next(r for r in records if r['dataset']==DS[1] and r['source_row']==3846);assert y['baseline_hits_by_L']=='10 10 10 10 10' and y['new_hits_by_L']=='0 0 0 0 0'
w=next(r for r in records if r['dataset']==DS[0] and r['source_row']==4063)
section=f'''

## 失败查询的具体表现

按任一L发生zero-hit转换筛出的事后集合为WebVid9条query/13次L事件、Yandex5条query/11次L事件；合计14条query，不能把24次事件当作24个独立样本。[全部query表](results/failure_query_summary.csv)与[逐L命中图](figures/failure_query_cases.svg)保留完整五L的baseline→new命中以及固定三入口。

Yandex source row3846在全部五L都从10命中变为0，原入口`{y['baseline_entries']}`→新入口`{y['new_entries']}`，替换{y['changed_entry_members']}个成员。这个已测query仅扩大L到800仍未恢复；不能由此宣称所有预算必然失败，也不能在未做新干预时把责任唯一归给评分或拓扑。相对地，row2441在L64/128/256从0救回到10，原收益同样保留。

WebVid row4063在L64/128从10变0，入口`{w['baseline_entries']}`→`{w['new_entries']}`；row3434在L256/400/800从1变0。Recall总增益与少量灾难性或边界失败同时存在，正是平均Recall和零命中率必须分别呈现的原因。这里的query选择是事后解释，不生成在线预测规则或调参反馈。
'''
if '--plot-only' not in sys.argv:
    report=(O/'report.md').read_text();assert '## 失败查询的具体表现' not in report;(O/'report.md').write_text(report+section)
dump(O/'reviews/failure_query_verification.json',dict(status='PASS',zero_transition_events=24,unique_queries=14,all_five_L_pairs_checked=70,entry_identity_across_L=True,new_searches=0))
print('FAILURE_QUERY_REPORT_PASS',json.dumps(records,ensure_ascii=False),flush=True)
