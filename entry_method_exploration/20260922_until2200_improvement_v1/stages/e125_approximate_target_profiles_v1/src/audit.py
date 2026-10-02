import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='8'
os.sched_setaffinity(0,set(range(8)))
import json,time,hashlib
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1];P=R.parent.parent;C=json.loads((R/'config.locked.json').read_text());S=json.loads((R/'results/summary.json').read_text());start=time.perf_counter();profile_errors={};scored=0;baseline_checks=0;cis=0;max_boot_error=0.;oldfiles=0;float_scores=0
def ident(p):return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def dump(p,x):assert not p.exists();p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
dump(R/'reviews/audit_frozen.json',{'files':{str(p):ident(p) for p in [Path(__file__),R/'src/analyze.py',R/'results/summary.json']}})
def norm(x):return x/np.maximum(np.sqrt(np.square(x).sum(1,keepdims=True)),1e-12)
for di,(ds,dc) in enumerate(C['datasets'].items()):
    c=dc['original'];ec=dc['evaluate'];d=c['dimension'];q=np.fromfile(c['fit_source']['queries_file'],'<f4').reshape(20000,d);x=norm(q);base=np.memmap(c['base'],'<f4',mode='r').reshape(c['base_n'],d+1);hids=np.fromfile(c['anchor']['ids'],'<i4');h=norm(np.array(base[hids,1:],'f4'));labels=np.fromfile(R/'results'/ds/'labels/ids.i32','<i4').reshape(20000,100);dist=np.fromfile(R/'results'/ds/'labels/distances.f32','<f4').reshape(20000,100);temp=json.loads((R/'models'/ds/'profiles.json').read_text())['temperature'];v=h.astype('f8')
    # Different batching and aggregation from matrix A.T@X in the builder.
    for lo in range(0,20000,512):
        hi=min(lo+512,20000);nb=hi-lo;mass=np.zeros((nb,len(hids)))
        for r in range(10):
            target=norm(np.array(base[labels[lo:hi,r],1:],'f4'));sim=target@h.T
            if temp is None:
                groups=sim.argmax(1);np.add.at(v,groups,x[lo:hi].astype('f8')*.1)
            else:
                z=sim.astype('f8')/temp;z-=z.max(1,keepdims=True);z=np.exp(z);mass+=z/z.sum(1,keepdims=True)/10
        if temp is not None:v+=mass.T@x[lo:hi].astype('f8')
    w=norm(v);actual=np.fromfile(R/'models'/ds/'W.f32','<f4').reshape(w.shape);err=float(np.abs(w-actual).max());assert err<2e-7;profile_errors[ds]=err
    for j in np.linspace(0,19999,32,dtype=int):
        for rank in [0,9,99]:
            true=-np.dot(q[j].astype('f8'),np.array(base[labels[j,rank],1:],'f8'));assert abs(true-float(dist[j,rank]))<2e-6*(1+abs(true));float_scores+=1
    gt=np.fromfile(ec['gt'],'<i4').reshape(4096,100);aligned=np.load(R/'results'/f'{ds}.aligned.npz')
    for point in S['datasets'][ds]['points']:
        K,L=point['K'],point['L'];pair=[]
        for m,method in enumerate(ec['methods']):
            pp=R/'results'/ds/'evaluation'/f'k{K}'/f'{method["name"]}_L{L}';out=np.fromfile(pp/'ids.i32','<i4').reshape(4096,K);checked=[]
            for j in range(4096):
                truth=set(map(int,gt[j,:K]));checked.append(sum(int(y) in truth for y in out[j]))
            hits=np.array(checked,dtype='u1');pair.append(hits);scored+=len(out)
            assert np.array_equal(hits,aligned[f'K{K}_L{L}_hits'][m]);meta=json.loads((pp/'complete.json').read_text());qps=4096/(sum(meta['seconds'])/3);assert abs(qps-point['methods'][m]['QPS'])<1e-9
            if m==0:
                old=Path(ec['baseline_reference'])/f'k{K}'/f'{method["name"]}_L{L}'
                for name in ['ids.i32','distances.f32','entry_ids.i32','route_ndc.u64','graph_ndc.u64']:assert (pp/name).read_bytes()==(old/name).read_bytes();baseline_checks+=1
        delta=(pair[1].astype('f8')-pair[0])/K;assert np.array_equal(delta,aligned[f'K{K}_L{L}_delta']);assert abs(delta.mean()*100-point['delta_recall_pp'])<1e-13
        if point['primary']:
            rng=np.random.default_rng(C['bootstrap_seed']+di*100+(0 if K==1 else 1));boot=[]
            for lo in range(0,C['bootstrap_reps'],97):
                ix=rng.integers(0,4096,(min(97,C['bootstrap_reps']-lo),4096));boot.append(delta[ix].sum(1)/4096)
            boot=np.concatenate(boot);be=float(np.abs(boot-aligned[f'K{K}_L{L}_bootstrap']).max());assert be<1e-14;max_boot_error=max(max_boot_error,be);assert np.max(np.abs(np.quantile(boot,[.00625,.99375])*100-point['primary_98_75_interval_pp']))<1e-12;cis+=1
    labeljob=json.loads((R/'reviews'/f'{ds}_labels.job.json').read_text());evaljob=json.loads((R/'reviews'/f'{ds}_evaluate.job.json').read_text());assert labeljob['max_threads']==1 and evaljob['max_threads']==1
for file in ['reviews/prepare_inputs.json','reviews/analysis_inputs.json']:
    for p,v in json.loads((R/file).read_text()).items():assert ident(Path(p))==v,p;oldfiles+=1
for file in ['reviews/run_frozen.json','reviews/models_frozen_before_evaluation.json']:
    for p,v in json.loads((R/file).read_text())['files'].items():assert ident(Path(p))==v,p;oldfiles+=1
for p,v in json.loads((R/'reviews/run_frozen.json').read_text())['large_stat_only'].items():st=Path(p).stat();assert st.st_size==v['bytes'] and st.st_mtime_ns==v['mtime_ns']
assert scored==98304 and baseline_checks==60 and cis==4
dump(R/'reviews/independent_audit.json',{'status':'PASS','seconds':time.perf_counter()-start,'candidate_profiles_reaggregated':2,'candidate_profile_max_abs_errors':profile_errors,'teacher_float64_score_samples':float_scores,'all_query_return_vectors_scalar_scored':scored,'old_default_full_array_bit_recoveries':baseline_checks,'primary_intervals_recomputed':cis,'maximum_bootstrap_error':max_boot_error,'source_identity_checks':oldfiles,'new_searches':0,'new_models':0,'independent_implementation_same_agent':True})
print('PASS',scored,profile_errors,flush=True)
