"""Post-measurement read-only diagnosis; no fitting, selection, or new search."""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[key]='1'
import json, time, hashlib
from pathlib import Path
import numpy as np

os.sched_setaffinity(0,{15})
run=Path(__file__).resolve().parents[1]
read=lambda p:json.loads(p.read_text())
lock=read(run/'config.locked.json')
start=time.time(); records=[]
for ds,c in lock['datasets'].items():
    tr=read(run/'models'/ds/'training_report.json'); H=tr['H']; n=tr['n']
    labs=run/'results'/ds/'labels'; done=read(labs/'complete.json')
    rs=[[],[]]; ts=[]
    for block in sorted(done['blocks'],key=lambda x:x['start']):
        b=labs/f"block_{block['start']}"; nb=block['n']
        for ki,name in enumerate(('hits1.u8','hits100.u8')):
            rs[ki].append(np.fromfile(b/name,np.uint8).reshape(nb,H+1).astype(float)/(1 if ki==0 else 100))
        ts.append(np.fromfile(b/'seconds.f64',np.float64).reshape(nb,H+1,2,3).mean(axis=3))
    rs=[np.concatenate(v) for v in rs]; t=np.concatenate(ts)
    hubs=np.fromfile(c['anchor']['ids'],np.int32); order=np.argsort(hubs,kind='stable')
    rec={'dataset':ds,'heads':{},'cv':{}}
    for name,info in tr['methods'].items():
        cv=info['cv']; a=str(info['alpha']); e=np.mean(cv[a]['response_mse_by_head'],axis=0); b=np.mean(cv[a]['intercept_mse_by_head'],axis=0)
        chosen=max(lock['ridge_alphas'],key=lambda x:(cv[str(x)]['mean_utility'],x))
        assert chosen==info['alpha']
        rec['cv'][name]={'alpha':chosen,'utilities':{k:v['mean_utility'] for k,v in cv.items()},'selected_MSE_reduction_vs_intercept_pct':((b-e)/b*100).tolist()}
    for ki,K in enumerate((1,100)):
        r=rs[ki]; dr=r[:,1:]-r[:,:1]; tref=t[:,0,ki].mean(); dt=(t[:,1:,ki]-t[:,:1,ki])/tref
        u=dr-lock['cost_weight']*dt
        oracle=float(np.maximum(dr.max(axis=1),0).mean())
        assert abs(oracle-tr['methods']['GraphRecall']['training'][str(K)]['oracle_utility'])<1e-12
        best_mean=max(0.,float(u.mean(axis=0).max()))
        assert best_mean==0. and tr['best_fixed'][str(K)]==-1
        head={'fit_GT10_recall_pct':float(r[:,0].mean()*100),'fit_recall_oracle_gain_pp':oracle*100,
              'fit_queries_with_positive_recall_opportunity':int((dr.max(axis=1)>0).sum()),
              'best_single_mean_utility':float(u.mean(axis=0).max()),'roles':{}}
        model=run/'models'/ds/'GraphCost'; W=np.fromfile(model/f'K{K}.weights.f32',np.float32).reshape(H,64).astype(float); b=np.fromfile(model/f'K{K}.bias.f32',np.float32).astype(float)
        for role in ('fit','accept'):
            X=np.fromfile(run/'results'/ds/f'{role}_features/graph.features.f32',np.float32).reshape(n,64).astype(float)
            scores=X@W.T+b; idx=order[np.argmax(scores[:,order],axis=1)]; best=scores[np.arange(n),idx]
            actions=np.where(best>0,idx+1,0).astype(np.int32)
            native=np.fromfile(run/'results'/ds/f'{role}_predictions/GraphCost_K{K}.actions.i32',np.int32)
            assert np.array_equal(native,actions)
            out={'queries':n,'fallback_queries':int((actions==0).sum()),'single_queries':int((actions>0).sum()),'max_predicted_utility_quantiles':np.quantile(best,[0,.01,.5,.99,1]).tolist(),'independent_forward_action_matches':n}
            if role=='fit':
                gain=np.zeros(n); take=np.flatnonzero(actions); gain[take]=dr[take,actions[take]-1]
                assert abs(gain.mean()-tr['methods']['GraphCost']['training'][str(K)]['recall_gain'])<1e-12
            head['roles'][role]=out
        rec['heads'][str(K)]=head
    records.append(rec)
paired=read(run/'results/paired.json'); curve=[x for x in paired if x['method']=='GraphCost' and x['reference']=='GT10']
assert len(curve)==20 and all(x['delta_recall_pp']==0 and x['qps_ranges_separated_negative'] for x in curve)
result={'status':'PASS','scope':'post-measurement diagnostic only; no new fit/search/model choice','datasets':records,'primary_curve_points':len(curve),'primary_all_recall_deltas_zero':True,'primary_all_three_round_ranges_slower':True,'seconds':time.time()-start,'new_searches':0,'new_fits':0,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(run/'reviews/review_diagnostics.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
print(json.dumps({'status':'PASS','seconds':result['seconds'],'datasets':[{ 'dataset':r['dataset'],'heads':r['heads']} for r in records]},indent=2))
