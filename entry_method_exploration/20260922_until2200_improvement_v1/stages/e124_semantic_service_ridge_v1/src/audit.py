"""Independent normal-equation and scalar-action audit; does not import fitter."""
import os
for name in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']: os.environ[name]='8'
import hashlib,json,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1]
C=json.loads((R/'config.locked.json').read_text())
start=time.perf_counter(); identities={}; max_model=0.; max_value=0.; count_actions=0; count_values=0; heads=0
def read(p): return json.loads(p.read_text())
def check_identity(path,expected):
    p=Path(path); got={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
    assert got==expected,(path,got,expected)
    identities[path]=got
for name in ['prepare_inputs.json','prepare_frozen.json','fit_frozen.json','response_inputs.json']:
    d=read(R/'reviews'/name)
    for p,v in d.get('files',d).items(): check_identity(p,v)
info=read(R/'results/information.json'); results={}
for ds,dc in C['datasets'].items():
    sem=np.load(R/'inputs'/ds/'semantic.npz'); role=np.load(R/'inputs'/ds/'roles.npz')
    q=sem['q_unit']; owner=sem['owners']; ids=sem['ids']; H=len(ids); rows=sem['rows']; ri=role['response_indices']; folds=role['response_folds']
    n=len(ri); actions_count=H+1
    # Histogram construction is distinct from fitter add.at scatter.
    labels=np.stack([np.bincount(o,minlength=H)/100 for o in owner])
    onehot=np.eye(H)[owner[:,0]]
    old=Path(C['historical_root'])/'results'/ds/'labels'; recalls=[]; timing=[]
    for b in sorted(read(old/'complete.json')['blocks'],key=lambda b:b['start']):
        p=old/f"block_{b['start']}"; nn=b['n']
        h1=np.fromfile(p/'hits1.u8','u1').reshape(nn,actions_count)
        h100=np.fromfile(p/'hits100.u8','u1').reshape(nn,actions_count)
        secs=np.fromfile(p/'seconds.f64','<f8').reshape(nn,actions_count,2,3)
        recalls.append(np.stack([h1,h100*.01],-1)); timing.append(np.sum(secs,axis=-1)/3)
    recall=np.concatenate(recalls); seconds=np.concatenate(timing)
    oof=np.load(R/'models'/ds/'oof.npz'); val=np.zeros_like(oof['values']); act=np.zeros_like(oof['actions'])
    for f in range(4):
        model=np.load(R/'models'/ds/f'fold_{f}.npz')
        service=np.load(Path(C['service_root'])/'models_v2'/ds/f'fold_{f}.npz')
        small=role[f'response_fit_{f}']; large=role[f'semantic_fit_{f}']; outer=role[f'outer_{f}']; out=np.where(folds==f)[0]; tr=np.where(folds!=f)[0]
        assert np.array_equal(ri[out],outer) and np.array_equal(ri[tr],small)
        assert np.array_equal(model['outer_rows'],rows[outer])
        rawq=np.fromfile(dc['fit_source']['queries_file'],'<f4').reshape(20000,dc['dimension'])
        outer_hash={hashlib.sha256(x.tobytes()).digest() for x in rawq[outer]}
        assert not any(hashlib.sha256(x.tobytes()).digest() in outer_hash for x in rawq[large])
        for size,idx in enumerate([small,large]):
            x=q[idx]; mx=np.mean(x,0); xc=x-mx; gram=xc.T@xc+C['alpha']*np.eye(x.shape[1])
            for k,yall in enumerate([onehot,labels]):
                y=yall[idx]; my=y.mean(0)
                w=np.linalg.solve(gram,xc.T@(y-my)); b=my-mx@w
                err=max(np.abs(w-model['semantic_maps'][size,k]).max(),np.abs(b-model['semantic_biases'][size,k]).max())
                assert err<1e-11,err; max_model=max(max_model,float(err)); heads+=1
                for m,ti in ([(2,1)] if size==0 else [(3,1),(4,2)]):
                    sequential=(q[outer]@w+b)@service['tables'][ti,k,:,1:]
                    compiled=q[outer]@model['weights'][m-1,k]+model['biases'][m-1,k]
                    assert np.max(np.abs(sequential-compiled))<1e-11
        tref=seconds[tr,0].mean(0)
        for k in range(2):
            for m in range(1,5):
                pred=q[outer]@model['weights'][m-1,k]+model['biases'][m-1,k]
                # Include default score zero and sort by descending score, default first then real id.
                scores=np.column_stack([np.zeros(len(out)),pred]); tie=np.r_[-1,ids]
                chosen=np.array([np.lexsort((tie,-row))[0] for row in scores])
                assert np.array_equal(chosen,oof['actions'][out,m,k])
                act[out,m,k]=chosen
                for j,a in zip(out,chosen):
                    gain=float(recall[j,a,k])-float(recall[j,0,k]); dt=(float(seconds[j,a,k])-float(seconds[j,0,k]))/float(tref[k])
                    val[j,m,k]=[gain,dt,gain-C['cost_weight']*dt]
            count_actions+=len(out)*5; count_values+=len(out)*5*3
    assert np.array_equal(act,oof['actions'])
    err=float(np.abs(val-oof['values']).max()); assert err<1e-12;max_value=max(max_value,err)
    for m,name in enumerate(C['arms']):
        expected=info['datasets'][ds]['methods'][name]
        assert abs(val[:,m,:,2].mean()-expected['equal_K_u_mean'])<1e-12
        for k,K in enumerate(C['K']):
            assert abs(val[:,m,k,0].mean()*100-expected['K'][str(K)]['recall_gain_pp'])<1e-10
            assert abs(val[:,m,k,1].mean()*100-expected['K'][str(K)]['graph_time_change_pct'])<1e-10
    results[ds]={'all_actions_match':True,'all_values_match':True,'outer_row_and_byte_isolation':True}
for p,x in identities.items(): check_identity(p,x)
out={'status':'PASS','independent_implementation_same_agent':True,'seconds':time.perf_counter()-start,'semantic_heads_solved_without_eigendecomposition':heads,'actions_checked':count_actions,'values_checked':count_values,'max_model_error':max_model,'max_value_error':max_value,'protected_files':len(identities),'datasets':results,'scope':'Normal equations, composition, all actions and actual values, role isolation and identities. Does not rerun graph searches or establish unexposed validation.'}
target=R/'reviews/independent_audit.json';assert not target.exists();target.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
