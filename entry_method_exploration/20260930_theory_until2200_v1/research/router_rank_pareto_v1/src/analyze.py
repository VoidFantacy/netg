import os
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[k]='1'
import json,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1];C=json.loads((R/'config.locked.json').read_text())
def read(p):return json.loads(Path(p).read_text())
def put(p,v):
    with Path(p).open('x') as f:f.write(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def main():
    start=time.perf_counter();assert read(R/'reviews/jobs_complete.json')['status']=='PASS';rng=np.random.default_rng(C['bootstrap_seed']);result={}
    for ds,c in C['datasets'].items():
        n=c['n'];a=np.load(R/'models'/ds/'development_arrays.npz');hits=a['hits'];actions=a['actions'];folds=a['folds'];rows=np.arange(n)
        selected=np.stack([hits[rows[:,None],actions[:,:,ki],ki] for ki in range(2)],axis=2).astype('i4')
        delta=selected-selected[:,:1,:];values=delta.astype('f8')*np.array([100.,1.]);flat=values.reshape(n,12)
        boot=np.empty((C['bootstrap_reps'],12),'f8')
        groups=[np.flatnonzero(folds==f) for f in range(4)]
        for lo in range(0,len(boot),128):
            m=min(128,len(boot)-lo);ix=np.concatenate([g[rng.integers(0,len(g),size=(m,len(g)))] for g in groups],axis=1)
            boot[lo:lo+m]=flat[ix].mean(1)
        boot=boot.reshape(-1,6,2);walls=read(R/'results'/ds/'wall/timings.json');gates=read(R/'results'/ds/'gate/timings.json');points={}
        for ki,pt in enumerate(c['points']):
            K,L=pt['K'],pt['L'];methods={};by={}
            for name in C['methods']:
                data=sorted([x for x in walls if x['K']==K and x['method']==name],key=lambda x:x['repeat']);assert [x['repeat'] for x in data]==[0,1,2]
                t=np.array([x['seconds'] for x in data]);assert (t>0).all();by[name]=t
            base=by['Default'];base_pool=3*n/base.sum()
            for mi,name in enumerate(C['methods']):
                dh=delta[:,mi,ki];t=by[name];qps=n/t;pooled=3*n/t.sum();acts=actions[:,mi,ki]
                assert np.array_equal(acts,np.fromfile(R/'results'/ds/'wall'/f'k{K}_L{L}'/f'{name}.actions.i32','<i4'))
                methods[name]={'recall_pct':float(selected[:,mi,ki].mean()*100/K),'delta_recall_pp':float(dh.mean()*100/K),
                    'delta_recall_95pct_descriptive_interval_pp':np.quantile(boot[:,mi,ki],[.025,.975]).tolist(),
                    'rescued_queries':int((dh>0).sum()),'damaged_queries':int((dh<0).sum()),'rescued_hits':int(dh[dh>0].sum()),'damaged_hits':int(-dh[dh<0].sum()),
                    'seconds':t.tolist(),'qps_each':qps.tolist(),'qps_median':float(np.median(qps)),'qps_min':float(qps.min()),'qps_max':float(qps.max()),'qps_pooled':float(pooled),
                    'delta_qps_pooled_pct':float((pooled/base_pool-1)*100),'paired_repeat_delta_qps_pct':((base/t-1)*100).tolist(),
                    'extra_wall_us_per_query':float((t.mean()-base.mean())/n*1e6),'actions':np.bincount(acts,minlength=4).tolist(),
                    'R_nonnegative_and_pooled_QPS_positive_mean_only':bool(dh.sum()>=0 and pooled>base_pool)}
            controls={}
            for name in ('GlobalPareto','ShufflePareto','FeaturePareto'):
                mi=C['methods'].index(name);dh=selected[:,2,ki]-selected[:,mi,ki]
                controls[name]={'State_minus_control_recall_pp':float(dh.mean()*100/K),
                    'State_minus_control_recall_interval_pp':np.quantile(boot[:,2,ki]-boot[:,mi,ki],[.025,.975]).tolist(),
                    'State_relative_pooled_QPS_pct':float((by[name].sum()/by['StatePareto'].sum()-1)*100)}
            gt={name:np.array([x['seconds'] for x in sorted([x for x in gates if x['K']==K and x['method']==name],key=lambda x:x['repeat'])]) for name in ('Default','ForcedDefault')}
            points[str(K)]={'K':K,'L':L,'methods':methods,'State_vs_controls':controls,
                'four_action_oracle_gain_pp':float((hits[:,:,ki].max(1)-hits[:,0,ki]).mean()*100/K),
                'gate_forced_default':{'default_seconds':gt['Default'].tolist(),'forced_seconds':gt['ForcedDefault'].tolist(),
                    'delta_pooled_QPS_pct':float((gt['Default'].sum()/gt['ForcedDefault'].sum()-1)*100),
                    'extra_us_per_query':float((gt['ForcedDefault'].mean()-gt['Default'].mean())/n*1e6),'outputs_bit_identical':True}}
        result[ds]={'n':n,'points':points,'state_count':int(len(np.unique(a['states']))),'history_exposed':True,'OOF':True,'bootstrap_stratified_by_original_fold':True}
    put(R/'results/analysis.json',{'status':'COMPLETE_DESCRIPTIVE_RECALL_QPS_COMPARISON','datasets':result,'default_changed':False,
        'bootstrap_seed':C['bootstrap_seed'],'bootstrap_reps':C['bootstrap_reps'],'bootstrap_scope':'query paired and fold stratified; history exposure and overlapping training folds remain',
        'QPS_intervals':'only three observed repetitions, no population confidence interval','seconds':time.perf_counter()-start})
    for ds,r in result.items():print(ds,{k:v['methods']['StatePareto'] for k,v in r['points'].items()},flush=True)
if __name__=='__main__':main()
