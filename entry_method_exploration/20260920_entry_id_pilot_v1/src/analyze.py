from workflow import *
import csv
def analyze():
 metrics=[];paired=[];allhits={};rng=np.random.default_rng(20260920)
 for ds in LOCK['datasets']:
  inp=RUN/'inputs'/ds/'audit';cfg=read(inp/'config.json');gt=np.fromfile(inp/'gt.i64',np.int64).reshape(cfg['n'],100);p=RUN/'results'/ds/'audit';n=cfg['n'];dh={}
  for K in [1,100]:
   truth=gt[:,:K];baseline=None
   for model in cfg['models']:
    name=model['name'];f=p/f'{name}_K{K}_L128';done=read(f/'complete.json');ids=np.fromfile(f/'ids.i32',np.int32).reshape(n,K);entries=np.fromfile(f/'entry_ids.i32',np.int32).reshape(n,3);hits=np.array([np.isin(x,y).sum() for x,y in zip(ids,truth)]);r=hits/K
    assert np.all(entries[:,0]<entries[:,1]) and np.all(entries[:,1]<entries[:,2]);assert all(len(np.unique(x))==K for x in ids)
    sec=np.array(done['seconds']);row=dict(dataset=ds,method=name,K=K,L=128,n=n,recall_pct=100*float(r.mean()),qps=float(n/sec.mean()),seconds=sec.tolist(),qps_rounds=(n/sec).tolist(),zero_hit_queries=int((hits==0).sum()),graph_ndc=float(np.fromfile(f/'graph_ndc.u64',np.uint64).mean()),route_ndc=float(np.fromfile(f/'route_ndc.u64',np.uint64).mean()),edited_slots=len(model['edits']))
    metrics.append(row);dh[name,K]=(r,hits,entries,row)
    if name=='GT10':baseline=(r,hits,entries,row);continue
    br,bh,be,bm=baseline;diff=r-br;means=[]
    for _ in range(100):means.extend(diff[rng.integers(0,n,size=(100,n))].mean(1).tolist())
    lo,hi=np.quantile(means,[.00625,.99375]);rec=dict(dataset=ds,method=name,K=K,L=128,delta_recall_pp=100*float(diff.mean()),CI98_75_pp=[100*float(lo),100*float(hi)],delta_qps_pct=100*(row['qps']/bm['qps']-1),rescued_zero=int(((bh==0)&(hits>0)).sum()),new_zero=int(((bh>0)&(hits==0)).sum()),improved_queries=int((diff>0).sum()),harmed_queries=int((diff<0).sum()),entry_changed_queries=int(np.any(entries!=be,axis=1).sum()))
    paired.append(rec)
  # Actual K1 and K100 calls share trajectory at equal L, but were timed independently.
  for model in cfg['models']:
   name=model['name'];a=p/f'{name}_K1_L128';b=p/f'{name}_K100_L128';i1=np.fromfile(a/'ids.i32',np.int32);i100=np.fromfile(b/'ids.i32',np.int32).reshape(n,100)
   assert np.array_equal(i1,i100[:,0]);assert np.array_equal(np.fromfile(a/'graph_ndc.u64',np.uint64),np.fromfile(b/'graph_ndc.u64',np.uint64));assert np.array_equal(dh[name,1][2],dh[name,100][2])
  allhits[ds]={f'{name}_K{k}':h.tolist() for (name,k),(r,h,e,m) in dh.items()}
 primary=[x for x in paired if x['method']=='Cost'];quality_nonnegative=all(x['delta_recall_pp']>=0 for x in primary);positive_per_ds=all(any(x['CI98_75_pp'][0]>0 for x in primary if x['dataset']==ds) for ds in LOCK['datasets']);speed=all(x['delta_qps_pct']>=0 for x in primary);passed=quality_nonnegative and positive_per_ds and speed
 gate=dict(status='PASS_L128_CONDITIONAL_PROCEED' if passed else 'STOP_ENTRY_ID_PILOT',quality_nonnegative=quality_nonnegative,positive_CI_in_each_dataset=positive_per_ds,all_mean_qps_nondecreasing=speed,primary_method='Cost',default_changed=False,new_formal_frontier_claim=False,pending_full_curve=passed)
 dump(RUN/'results/metrics.json',metrics);dump(RUN/'results/paired.json',paired);dump(RUN/'results/hits.json',allhits);dump(RUN/'results/gate.json',gate)
 for name,rows in [('metrics',metrics),('paired',paired)]:
  with (RUN/'results'/f'{name}.csv').open('w') as f:
   w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 print(json.dumps(dict(gate=gate,paired=paired),ensure_ascii=False),flush=True)
if __name__=='__main__':analyze()
