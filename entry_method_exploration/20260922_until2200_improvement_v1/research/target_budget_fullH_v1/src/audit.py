"""Independent scalar membership/oracle and resampling audit; no search or fitting."""
import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:
    os.environ[key]='1'
import json,time,hashlib
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1];C=json.loads((R/'config.locked.json').read_text());start=time.perf_counter()
def ident(p):return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def dump(p,x):assert not p.exists();p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
dump(R/'reviews/audit_frozen.json',{'files':{str(p):ident(p) for p in [Path(__file__),R/'src/analyze.py',R/'results/summary.json',R/'config.locked.json']}})
summary=json.loads((R/'results/summary.json').read_text());checks=0;vectors=0;calls=0;maximum_error=0.;ci_checks=0
for di,(ds,c) in enumerate(C['datasets'].items()):
    ip=R/'inputs_v2'/ds;ref=np.load(ip/'old_reference.npz');z=np.load(R/'results'/f'{ds}.derived.npz');gt=np.fromfile(ip/'gt.i64','<i8').reshape(256,100);ids=np.fromfile(c['anchor']['ids'],'<i4');A=len(ids)+1
    pos=np.fromfile(ip/'original_positions.i64','<i8');expected=np.sort(np.random.default_rng(C['seed']+di).choice(4096,256,False));assert np.array_equal(pos,expected)
    done=json.loads((R/'results'/ds/'complete.json').read_text());calls+=done['new_search_calls'];assert done['old_full_return_matches']==12 and done['native_parity_checks']==24*(1+len(c['points']))
    job=json.loads((R/'reviews'/f'{ds}.job.json').read_text());assert job['max_process_threads']==1 and job['exit_code']==0
    for k,K in enumerate([1,100]):
        rec=summary['datasets'][ds][str(K)];L=rec['L'];high=z[f'K{K}_target_hits'];low=ref['hits1' if K==1 else 'hits100'];assert high.shape==(256,A)
        if not(ds.startswith('yandex') and K==1):
            for lo in range(0,256,16):
                bp=R/'results'/ds/f'K{K}_L{L}'/f'block_{lo}';out=np.fromfile(bp/'ids.i32','<i4').reshape(16,A,K)
                for j in range(16):
                    truth=set(map(int,gt[lo+j,:K]))
                    for a in range(A):
                        got=sum(int(v) in truth for v in out[j,a]);assert got==int(high[lo+j,a]);vectors+=1
        else:assert np.array_equal(high,low)
        actual=[];ha=[];la=[]
        for j in range(256):
            h=list(map(int,high[j]));l=list(map(int,low[j]));ah=h.index(max(h));al=l.index(max(l));ha.append(ah);la.append(al)
            entry=[0]+[list(map(int,ids)).index(int(e))+1 for e in ref['entries'][j]]
            actual.append([h[0],max(h),max(h[a] for a in entry),h[al],h[int(ref['E123TargetService_actions'][j,k])],h[int(ref['E124SemanticService19k_actions'][j,k])]])
            checks+=6
        ret=np.array(actual,dtype='f8')/K;delta=ret-ret[:,:1]
        assert np.array_equal(ha,z[f'K{K}_high_oracle_actions']) and np.array_equal(la,z[f'K{K}_low_oracle_actions'])
        assert np.array_equal(ret,z[f'K{K}_method_returns']) and np.array_equal(delta,z[f'K{K}_method_delta'])
        rng=np.random.default_rng(C['bootstrap_seed']+di*100+k);boot=[]
        # Chunk size differs from the analysis while the frozen random stream stays fixed.
        for lo in range(0,C['bootstrap_reps'],73):
            ii=rng.integers(0,256,(min(73,C['bootstrap_reps']-lo),256));boot.append(delta[ii].sum(1)/256)
        boot=np.concatenate(boot);err=float(np.max(np.abs(boot-z[f'K{K}_bootstrap_delta'])));maximum_error=max(maximum_error,err);assert err<1e-14
        for m,(name,v) in enumerate(rec['methods'].items()):
            assert abs(v['recall']-ret[:,m].sum()/256)<1e-14
            assert abs(v['recall_gain_pp']-delta[:,m].sum()*100/256)<1e-12
            assert np.max(np.abs(np.quantile(boot[:,m],[.025,.975])*100-v['gain_interval_pp']))<1e-11
            assert v['positive_queries']==int((delta[:,m]>0).sum()) and v['negative_queries']==int((delta[:,m]<0).sum());ci_checks+=1
        low_gain=(low.max(1).astype('f8')-low[:,0])/K;target_gain=delta[:,1]
        assert abs(rec['low_L128_fullH_oracle_gain_pp']-low_gain.mean()*100)<1e-12
        assert abs(rec['target_minus_low_oracle_gain_pp']-(target_gain-low_gain).mean()*100)<1e-12
assert calls==628404 and vectors==628224 and calls<=C['max_new_NSG']
protected=0
for file in ['reviews/prepare_inputs.json','reviews/analysis_inputs.json']:
    for p,v in json.loads((R/file).read_text()).items():assert ident(Path(p))==v,p;protected+=1
for p,v in json.loads((R/'reviews/run_frozen.json').read_text())['files'].items():assert ident(Path(p))==v,p;protected+=1
dump(R/'reviews/independent_audit.json',{'status':'PASS','seconds':time.perf_counter()-start,'all_new_return_vectors_scalar_rescored':vectors,'integer_method_values_checked':checks,'method_intervals_checked':ci_checks,'max_resampling_error':maximum_error,'protected_identity_checks':protected,'new_NSG_accounting':calls,'audit_new_searches':0,'new_fits':0,'QPS_measured':False,'independent_implementation_same_agent':True})
print('PASS',vectors,checks,calls,flush=True)
