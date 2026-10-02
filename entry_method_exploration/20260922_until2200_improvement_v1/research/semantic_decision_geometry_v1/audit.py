import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='8'
import hashlib,json,time,math
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent;P=R.parent.parent;E=P/'stages/e124_semantic_service_ridge_v1';T=P/'stages/e123_target_service_gate_v1'
C=json.loads((E/'config.locked.json').read_text());start=time.perf_counter();checks=0;maxerr=0.;inputs=json.loads((R/'reviews/inputs.json').read_text())
for name,v in inputs.items():
    p=Path(name);assert p.stat().st_size==v['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==v['sha256']
summary=json.loads((R/'results/summary.json').read_text())
for ds in C['datasets']:
    d=np.load(R/'results'/f'{ds}.npz');eo=np.load(E/'models'/ds/'oof.npz');to=np.load(T/'models_v2'/ds/'oof.npz');sem=np.load(E/'inputs'/ds/'semantic.npz');role=np.load(E/'inputs'/ds/'roles.npz')
    q=sem['q_unit'][role['response_indices']];owner=sem['owners'][role['response_indices']]
    for size,m in enumerate([2,3]):
        gap=to['values'][:,3,:,2]-eo['values'][:,m,:,2]
        assert np.max(np.abs(gap-d['actual_u_gap'][:,size]))<1e-12
        assert np.max(np.abs(d['privileged_score_regret'][:,size]+d['service_residual_contrast'][:,size]-gap))<1e-12
        assert np.array_equal(d['action_agreement'][:,size],to['actions'][:,3]==eo['actions'][:,m])
        for k,K in enumerate([1,100]):
            for key in d.files:
                if key in ['folds','rows']:continue
                val=math.fsum(map(float,d[key][:,size,k]))/len(q)
                assert abs(val-summary[ds][str(K)][str([3072,18976][size])][key]['mean'])<1e-12;checks+=1
    # Reconstruct selected service scores with scalar target summation and compiled affine dot.
    for f in range(4):
        model=np.load(E/'models'/ds/f'fold_{f}.npz');table=np.load(T/'models_v2'/ds/f'fold_{f}.npz')['tables'][1]
        out=np.flatnonzero(d['folds']==f)
        for row in out[np.linspace(0,len(out)-1,32,dtype=int)]:
            for k,K in enumerate([1,100]):
                ap=int(to['actions'][row,3,k])
                for size,m in enumerate([2,3]):
                    ac=int(eo['actions'][row,m,k]);gt=owner[row,:K]
                    gp=math.fsum(float(table[k,z,ap]) for z in gt)/K
                    gc=math.fsum(float(table[k,z,ac]) for z in gt)/K
                    scoregap=gp-gc
                    err=abs(scoregap-d['privileged_score_regret'][row,size,k]);maxerr=max(maxerr,err);assert err<1e-12;checks+=1
                    uc=float(eo['values'][row,m,k,2]);up=float(to['values'][row,3,k,2])
                    assert abs((up-gp)-(uc-gc)-d['service_residual_contrast'][row,size,k])<1e-12;checks+=1
                    pred=0. if ac==0 else math.fsum(float(x)*float(y) for x,y in zip(q[row],model['weights'][m-1,k,:,ac-1]))+float(model['biases'][m-1,k,ac-1])
                    assert abs(pred-eo['selected_prediction'][row,m,k])<1e-12;checks+=1
# Exact member pooling example at K100. Region conditional mean can reverse a query action.
g=np.zeros((2,100),dtype=int);g[1,50:]=1
delta=np.ones((2,100));delta[1,:50]=-1;delta[1,50:]=0
s=np.array([delta[g==z].mean() for z in range(2)])
proxy=np.array([s[row].mean() for row in g]);actual=delta.mean(1)
assert (proxy>0).all() and actual[1]<0 and actual.mean()>0
result={'status':'PASS','seconds':time.perf_counter()-start,'same_agent_independent_implementation':True,'checks':checks,'max_scalar_error':maxerr,'protected_files':len(inputs),'all_original_actions_values_and_decompositions_match':True,'member_pooling_counterexample':{'K':100,'region_service':s.tolist(),'exact_region_proxy_scores':proxy.tolist(),'actual_query_utilities':actual.tolist(),'privileged_policy_average_utility':float(actual.mean()),'perfect_region_prediction_does_not_make_service_proxy_conditionally_correct':True}}
out=R/'reviews/independent_audit.json';assert not out.exists();out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
