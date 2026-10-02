from common import *
import csv,collections
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
threads();assert read(O/'reviews/verification.json')['status']=='PASS'
events=list(csv.DictReader((O/'results/failure_cases.csv').open()));groups=collections.defaultdict(list)
for event in events:groups[event['dataset'],int(event['source_row'])].append(event)
records=[];fig,axes=plt.subplots(1,2,figsize=(13,9));Ls=[64,128,256,400,800];counts=[]
for ax,ds,title in zip(axes,DS,['WebVid','Yandex']):
 ids=sorted(row for dataset,row in groups if dataset==ds);c=read(O/'inputs'/ds/'config.json');source_rows=np.fromfile(c['row_ids'],np.int64);local=[int(np.flatnonzero(source_rows==r)[0]) for r in ids]
 matched='baseline_soft' if ds==DS[0] else 'gt10_hard';before=[];after=[];entries={}
 for L in Ls:
  base=O/'results'/ds/f'{matched}_L{L}';new=O/'results'/ds/f'best_new_L{L}'
  before.append(np.fromfile(base/'hits.u8',np.uint8)[local]);after.append(np.fromfile(new/'hits.u8',np.uint8)[local])
  e0=np.fromfile(base/'entry_ids.i32',np.int32).reshape(-1,3)[local];e1=np.fromfile(new/'entry_ids.i32',np.int32).reshape(-1,3)[local]
  if entries:assert np.array_equal(entries['baseline'],e0) and np.array_equal(entries['new'],e1)
  entries=dict(baseline=e0,new=e1)
 b=np.asarray(before).T.astype(int);h=np.asarray(after).T.astype(int)
 # Select display by maximum absolute hit change, then source row; full CSV below.
 chosen=sorted(range(len(ids)),key=lambda i:(-int(np.max(np.abs(h[i]-b[i]))),ids[i]))[:24];chosen.sort(key=lambda i:ids[i])
 if chosen:
  ax.imshow((h-b)[chosen],cmap='RdYlGn',vmin=-10,vmax=10,aspect='auto');ax.set_yticks(range(len(chosen)),[ids[i] for i in chosen])
  for y,i in enumerate(chosen):
   for j in range(5):ax.text(j,y,f'{b[i,j]}→{h[i,j]}',ha='center',va='center',fontsize=9,color='white' if abs(h[i,j]-b[i,j])>=7 else 'black')
 ax.set_xticks(range(5),Ls);ax.set(title=f'{title} · {len(chosen)} displayed / {len(ids)} total queries',xlabel='Search L',ylabel='router_train source row')
 for i,row in enumerate(ids):
  saved=groups[ds,row];newLs=[int(e['L']) for e in saved if e['kind']=='new_failure'];rescuedLs=[int(e['L']) for e in saved if e['kind']=='rescued']
  assert newLs==[L for j,L in enumerate(Ls) if b[i,j]>0 and h[i,j]==0];assert rescuedLs==[L for j,L in enumerate(Ls) if b[i,j]==0 and h[i,j]>0]
  records.append(dict(dataset=ds,source_namespace=next(x['source_namespace'] for x in read(O/'reviews/input_roles.json')['datasets'] if x['dataset']==ds),source_row=row,baseline_hits_by_L=' '.join(map(str,b[i])),new_hits_by_L=' '.join(map(str,h[i])),new_failure_Ls=' '.join(map(str,newLs)),rescued_Ls=' '.join(map(str,rescuedLs)),baseline_entries=' '.join(map(str,entries['baseline'][i])),new_entries=' '.join(map(str,entries['new'][i])),changed_entry_members=len(set(entries['new'][i])-set(entries['baseline'][i])),displayed=i in chosen))
 counts.append(dict(dataset=ds,unique_queries=len(ids),L_events=sum(len(v) for (dataset,_),v in groups.items() if dataset==ds),displayed=len(chosen)))
fig.suptitle('E74 · GT10 zero-hit transitions: baseline hits → compact multi-profile ef10 hits',fontsize=14)
fig.text(.5,.015,'Post-hoc historical development · max |hit change| then source row for display; all cases in CSV · L events are not independent queries',ha='center',fontsize=9);fig.tight_layout(rect=(0,.04,1,.95))
for ext in ['png','svg','pdf']:fig.savefig(O/'figures'/f'failure_query_cases.{ext}',dpi=180)
plt.close(fig)
with (O/'results/failure_query_summary.csv').open('x',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
dump(O/'reviews/failure_query_verification.json',dict(status='PASS',zero_transition_events=len(events),unique_queries=len(records),all_five_L_pairs_checked=len(records)*5,entry_identity_across_L=True,datasets=counts,new_searches=0));print('FAILURES',json.dumps(counts))
