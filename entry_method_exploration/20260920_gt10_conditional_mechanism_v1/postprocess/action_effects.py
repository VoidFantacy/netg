"""Descriptive analysis of all already-run comparisons; no new search or selection."""
import sys,csv
from pathlib import Path
RUN=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(RUN/'src'))
from common import *
assert read(RUN/'reviews/analysis_complete.json')['status']=='PASS'
assert not (RUN/'results/action_effects.csv').exists()
dump(RUN/'reviews/action_effects_source_lock.json',dict(source=identity(Path(__file__)),created_unix=time.time(),posthoc=True,new_search=0,changes_primary_gate=False))
hits=np.load(RUN/'results/aligned_hits.npz');records=[]
for ds,c in LOCK['datasets'].items():
    n=LOCK['evaluation_n']
    for family in c['families']:
        title=family.title();original=title+'OriginalExact';p=RUN/'results'/ds
        original_entries=np.fromfile(p/original/'entries.i32','<i4').reshape(n,3)
        for name in ['GT1Exact',title+'GroupMeanExact']+[title+f'Perm{j}Exact' for j in range(4)]:
            entries=np.fromfile(p/name/'entries.i32','<i4').reshape(n,3)
            changed=np.any(entries!=original_entries,axis=1)
            for K in LOCK['K']:
                old_hits=hits[ds+'__'+original+'__K'+str(K)].astype('int64');new_hits=hits[ds+'__'+name+'__K'+str(K)].astype('int64')
                delta=new_hits-old_hits
                old_ids=np.fromfile(p/original/f'k{K}.ids.i32','<i4').reshape(n,K);new_ids=np.fromfile(p/name/f'k{K}.ids.i32','<i4').reshape(n,K)
                old_dist=np.fromfile(p/original/f'k{K}.distances.f32','<u4').reshape(n,K);new_dist=np.fromfile(p/name/f'k{K}.distances.f32','<u4').reshape(n,K)
                changed_output=np.any(old_ids!=new_ids,axis=1)|np.any(old_dist!=new_dist,axis=1)
                assert not np.any((changed_output|(delta!=0))&~changed)
                ndc0=np.fromfile(p/original/f'k{K}.ndc.u64','<u8').astype('int64');ndc1=np.fromfile(p/name/f'k{K}.ndc.u64','<u8').astype('int64')
                gained=int(delta[delta>0].sum());lost=int(-delta[delta<0].sum());assert gained-lost==delta.sum()
                records.append(dict(dataset=ds,family=family,baseline=original,method=name,K=K,L=128,n=n,changed_entry_queries=int(changed.sum()),changed_entry_pct=float(changed.mean()*100),changed_output_queries=int(changed_output.sum()),higher_recall_queries=int((delta>0).sum()),lower_recall_queries=int((delta<0).sum()),equal_recall_queries=int((delta==0).sum()),gained_target_hits=gained,lost_target_hits=lost,net_target_hits=gained-lost,delta_recall_pp=float(delta.mean()/K*100),baseline_failed=int((old_hits==0).sum()),method_failed=int((new_hits==0).sum()),delta_graph_ndc_pct=float((ndc1.mean()/ndc0.mean()-1)*100),graph_ndc_difference_mean=float((ndc1-ndc0).mean()),posthoc=True,formal_QPS=False))
with (RUN/'results/action_effects.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=records[0]);w.writeheader();w.writerows(records)
dump(RUN/'reviews/action_effects_complete.json',dict(status='PASS',comparisons=len(records),new_search=0,posthoc=True,changes_primary_gate=False,source=identity(Path(__file__))))
for r in records:
    if 'GroupMean' in r['method'] or r['method']=='GT1Exact':print(json.dumps(r,ensure_ascii=False))
