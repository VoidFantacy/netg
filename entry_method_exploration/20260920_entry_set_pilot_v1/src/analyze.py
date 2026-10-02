from common import *
import csv

def interval_integer(d,denom,rng):
 values,counts=np.unique(d,return_counts=True);bs=rng.multinomial(len(d),counts/len(d),size=LOCK['bootstrap_reps'])@values
 return (100*np.quantile(bs/(len(d)*denom),[.00625,.99375])).tolist()
def writecsv(path,rows):
 with path.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def analyze(stage='accept'):
 started=time.time();metrics=[];paired=[];aggregate=[];allhits={};verification=[];rng=np.random.default_rng(LOCK['bootstrap_seed'])
 for ds,c in LOCK['datasets'].items():
  inp=RUN/'inputs'/ds/'accept';gt=np.fromfile(inp/'gt.i64',np.int64).reshape(LOCK['accept_n'],100);n=len(gt);doc=read(RUN/'models'/ds/'models.json');fixed=doc['fixed_best_method'];p=RUN/'results'/ds/stage;cfg=read(p/'config.json');hits={};by={}
  X=np.fromfile(p/'features.f64',np.float64).reshape(n,6);rank=np.fromfile(p/'ranked_entries.i32',np.int32).reshape(n,3)
  for point in cfg['points']:
   K,L=point['K'],point['L']
   for m in cfg['methods']:
    name=m['name'];f=p/f'{name}_K{K}_L{L}';done=read(f/'complete.json');I=np.fromfile(f/'ids.i32',np.int32).reshape(n,K);E=np.fromfile(f/'entry_ids.i32',np.int32).reshape(n,3);A=np.fromfile(f/'actions.i32',np.int32);h=np.array([np.isin(row,truth[:K]).sum() for row,truth in zip(I,gt)],np.int16)
    assert all(len(set(row))==K for row in I);assert all(sum(e>=0)==1 or (e[0]<e[1]<e[2]) for e in E)
    pred=predict(m['tree'],X) if 'tree' in m else np.full(n,m['action'],np.int32);assert np.array_equal(pred,A)
    expect=np.sort(rank,axis=1);single=A>0;expect[single]=np.column_stack((rank[np.flatnonzero(single),A[single]-1],np.full((int(single.sum()),2),-1)))
    assert np.array_equal(expect,E)
    sec=np.array(done['seconds']);row=dict(dataset=ds,method=name,K=K,L=L,n=n,recall_pct=float(h.mean()/K*100),zero_hit_queries=int((h==0).sum()),qps=float(n/sec.mean()),qps_mean_rounds=float((n/sec).mean()),qps_rounds=(n/sec).tolist(),seconds=sec.tolist(),graph_ndc=float(np.fromfile(f/'graph_ndc.u64',np.uint64).mean()),route_ndc=float(np.fromfile(f/'route_ndc.u64',np.uint64).mean()),feature_ndc=float(np.fromfile(f/'feature_ndc.u64',np.uint64).mean()),actions=np.bincount(A,minlength=4).tolist())
    metrics.append(row);by[name,K,L]=row;hits[name,K,L]=h
   for name in [m['name'] for m in cfg['methods'] if m['name']!='GT10']:
    for ref in dict.fromkeys(['GT10',fixed]):
     h,b=hits[name,K,L],hits[ref,K,L];delta=h.astype(np.int64)-b;rec=dict(dataset=ds,method=name,reference=ref,K=K,L=L,delta_recall_pp=float(delta.mean()/K*100),CI98_75_pp=interval_integer(delta,K,rng),delta_qps_pct=100*(by[name,K,L]['qps']/by[ref,K,L]['qps']-1),rescued_zero=int(((b==0)&(h>0)).sum()),new_zero=int(((b>0)&(h==0)).sum()),improved_queries=int((delta>0).sum()),harmed_queries=int((delta<0).sum()),net_hits=int(delta.sum()))
     paired.append(rec)
  if stage=='accept':
   # All selected policies must be exactly their full action's output, with no result union.
   for K in [1,100]:
    cols=[];dist=[];work=[]
    for name in ['GT10','Single1','Single2','Single3']:
     f=p/f'{name}_K{K}_L128';cols.append(np.fromfile(f/'ids.i32',np.int32).reshape(n,K));dist.append(np.fromfile(f/'distances.f32',np.float32).reshape(n,K));work.append(np.fromfile(f/'graph_ndc.u64',np.uint64))
    for m in cfg['methods']:
     f=p/f'{m["name"]}_K{K}_L128';A=np.fromfile(f/'actions.i32',np.int32);I=np.fromfile(f/'ids.i32',np.int32).reshape(n,K);D=np.fromfile(f/'distances.f32',np.float32).reshape(n,K);N=np.fromfile(f/'graph_ndc.u64',np.uint64)
     for a in range(4):
      ix=A==a;assert np.array_equal(I[ix],cols[a][ix]) and D[ix].tobytes()==dist[a][ix].tobytes() and np.array_equal(N[ix],work[a][ix])
   # Recover E116's entire matching default subset only after models froze.
   old=Path(c['E116_labels']);meta=np.fromfile(old/'meta.i32',np.int32).reshape(-1,4);bi=np.flatnonzero(meta[:,1]==-1)[5904:10000];oldI=np.memmap(old/'ids.i32',np.int32,mode='r',shape=(len(meta),100))[bi];oldD=np.memmap(old/'distances.f32',np.float32,mode='r',shape=(len(meta),100))[bi];oldE=np.memmap(old/'entries.i32',np.int32,mode='r',shape=(len(meta),3))[bi];oldN=np.fromfile(old/'ndc.u64',np.uint64)[bi]
   for K in [1,100]:
    f=p/f'GT10_K{K}_L128';assert np.array_equal(np.fromfile(f/'ids.i32',np.int32).reshape(n,K),oldI[:,:K]);assert np.fromfile(f/'distances.f32',np.float32).reshape(n,K).tobytes()==oldD[:,:K].tobytes();assert np.array_equal(np.fromfile(f/'entry_ids.i32',np.int32).reshape(n,3),oldE);assert np.array_equal(np.fromfile(f/'graph_ndc.u64',np.uint64),oldN)
   for ref in dict.fromkeys(['GT10',fixed,'ShuffledTree']):
    delta=(hits['CostTree',1,128]-hits[ref,1,128]).astype(np.int64)*100+hits['CostTree',100,128]-hits[ref,100,128]
    aggregate.append(dict(dataset=ds,method='CostTree',reference=ref,equalK_delta_pp=float(delta.mean()/200*100),CI98_75_pp=interval_integer(delta,200,rng)))
  # Same-L actual K1/K100 parity for every method actually run at both K.
  for name,K,L in list(hits):
   if K!=1 or (name,100,L) not in hits:continue
   a=p/f'{name}_K1_L{L}';b=p/f'{name}_K100_L{L}';assert np.array_equal(np.fromfile(a/'ids.i32',np.int32),np.fromfile(b/'ids.i32',np.int32).reshape(n,100)[:,0]);assert np.fromfile(a/'distances.f32',np.float32).tobytes()==np.fromfile(b/'distances.f32',np.float32).reshape(n,100)[:,0].tobytes()
   for fn in ['entry_ids.i32','graph_ndc.u64','route_ndc.u64','actions.i32']:assert (a/fn).read_bytes()==(b/fn).read_bytes()
  allhits[ds]={f'{name}_K{k}_L{l}':h.tolist() for (name,k,l),h in hits.items()};verification.append(dict(dataset=ds,python_cpp_actions=True,full_action_returns=stage=='accept',actual_K1_K100_parity=True,E116_baseline_restored=stage=='accept'))
 out=RUN/'results' if stage=='accept' else RUN/'results'/stage;out.mkdir(parents=True,exist_ok=True)
 dump(out/'metrics.json',metrics);dump(out/'paired.json',paired);dump(out/'aggregate.json',aggregate);dump(out/'hits.json',allhits);writecsv(out/'metrics.csv',metrics);writecsv(out/'paired.csv',paired)
 if stage=='accept':
  primary=[r for r in paired if r['method']=='CostTree'];positive=[r for r in aggregate if r['reference']!='ShuffledTree'];control=[r for r in aggregate if r['reference']=='ShuffledTree']
  criteria=dict(recall_means_nondecreasing_vs_both=all(r['delta_recall_pp']>=0 for r in primary),positive_equalK_CI_vs_both_each_dataset=all(r['CI98_75_pp'][0]>0 for r in positive),qps_nondecreasing_vs_both=all(r['delta_qps_pct']>=0 for r in primary),not_below_shuffled_quality=all(r['equalK_delta_pp']>=0 for r in control))
  passed=all(criteria.values());dump(out/'gate.json',dict(status='PASS_CONDITIONAL_FULL_CURVE' if passed else 'STOP_ENTRY_SET_PILOT',criteria=criteria,default_changed=False,full_curve_required=passed,primary_method='CostTree'))
 dump(RUN/'reviews'/f'{stage}_analysis_verified.json',dict(status='PASS',verification=verification,seconds=time.time()-started,points=len(metrics),wall_rounds=sum(len(r['seconds']) for r in metrics)))
 print('ANALYZED',stage,len(metrics),json.dumps(read(RUN/'results/gate.json')),flush=True)
if __name__=='__main__':analyze(sys.argv[1] if len(sys.argv)>1 else 'accept')
