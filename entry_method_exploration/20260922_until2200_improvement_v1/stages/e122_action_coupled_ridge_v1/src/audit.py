"""Independent numerical/output audit; does not import the fitter."""
import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[key]='8'
import hashlib,json,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1]
C=json.loads((R/'config.locked.json').read_text());OLD=Path(C['historical_root']);started=time.perf_counter()
def read(p):return json.loads(p.read_text())
def identity(p):return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
report={'reviewer':'same agent, independently implemented numerical and action audit','datasets':{}}
frozen=read(R/'reviews/fit_frozen.json')['files'];inputs=read(R/'reviews/response_inputs.json')
for name,ident in {**frozen,**inputs}.items():assert identity(Path(name))==ident,name
report['protected_files_verified']=len(set(frozen)|set(inputs))
information=read(R/'results/information.json')
for ds,dc in C['datasets'].items():
    n=C['n'];d=dc['dimension'];ids=np.fromfile(dc['anchor']['ids'],'<i4');H=len(ids);A=H+1
    q=np.fromfile(OLD/'inputs'/ds/'fit/queries.f32','<f4').reshape(n,d).astype('f8');q/=np.sqrt(np.sum(q*q,axis=1))[:,None]
    rows=np.fromfile(OLD/'inputs'/ds/'fit/row_ids.i64','<i8');path=R/'models'/ds
    out=dict(np.load(path/'oof.npz'));geom=dict(np.load(path/'geometry.npz'));folds=out['folds'];assert np.array_equal(out['rows'],rows)
    labels=OLD/'results'/ds/'labels';rec=[];time_values=[]
    for block in sorted(read(labels/'complete.json')['blocks'],key=lambda b:b['start']):
        b=labels/f"block_{block['start']}";nn=block['n']
        h1=np.fromfile(b/'hits1.u8','u1').reshape(nn,A);h100=np.fromfile(b/'hits100.u8','u1').reshape(nn,A)
        rec.append(np.stack([h1,h100*.01],axis=2));time_values.append(np.fromfile(b/'seconds.f64','<f8').reshape(nn,A,2,3).sum(3)/3)
    recall=np.concatenate(rec);seconds=np.concatenate(time_values);dr=recall-recall[:,0,None,:]
    counts={'actions':0,'values':0,'spectral_mode_direct_solves':0};maxerr={};calibration=[]
    for f in range(4):
        tr=np.flatnonzero(folds!=f);te=np.flatnonzero(folds==f);model=dict(np.load(path/f'fold_{f}.npz'))
        assert np.array_equal(model['fit_rows'],rows[tr]) and np.array_equal(model['outer_rows'],rows[te])
        mean=q[tr].mean(0);x=q[tr]-mean;g=x.T@x;ref=seconds[tr,0].mean(0)
        assert np.max(np.abs(ref-model['time_reference']))<1e-16
        dt=(seconds-seconds[:,0,None,:])/ref;utility=dr-.1*dt
        for k,K in enumerate(C['K']):
            ym=utility[tr,1:,k].mean(0);y=utility[tr,1:,k]-ym;c=x.T@y
            for j,name in enumerate(C['arms'][2:]):
                m=j+2;w=model['weights'][j,k];bias=model['biases'][j,k]
                pred=(q[te]-mean)@w+ym;compiled=q[te]@w+bias
                err=float(np.max(np.abs(pred-compiled)));maxerr['affine_prediction']=max(maxerr.get('affine_prediction',0),err);assert err<1e-12
                if name=='Independent':
                    direct=np.linalg.solve(g+10*np.eye(d),c);err=float(np.max(np.abs(direct-w)))
                    maxerr['independent_direct_solve']=max(maxerr.get('independent_direct_solve',0),err);assert err<1e-11
                else:
                    lap=geom['permuted_lap'] if name=='PermutedFunction' else geom['lap'];e,v=np.linalg.eigh(lap)
                    for mode in [0,H//2,H-1]:
                        mat=g+(10+10*e[mode])*np.eye(d) if name=='CoefficientSmooth' else (1+e[mode])*g+10*np.eye(d)
                        direct=np.linalg.solve(mat,c@v[:,mode]);err=float(np.max(np.abs(direct-w@v[:,mode])))
                        maxerr['coupled_mode_direct_solve']=max(maxerr.get('coupled_mode_direct_solve',0),err);assert err<1e-11;counts['spectral_mode_direct_solves']+=1
                ordered=np.r_[0,1+np.argsort(ids)];with_default=np.c_[np.zeros(len(te)),pred]
                selected=ordered[with_default[:,ordered].argmax(1)]
                assert np.array_equal(selected,out['actions'][te,m,k]);counts['actions']+=len(te)
                mse=((pred-utility[te,1:,k])**2).sum(1)/H
                assert np.max(np.abs(mse-out['mse'][te,m,k]))<1e-12
            expected_global=int(np.r_[0,1+np.argsort(ids)][np.r_[0,ym][np.r_[0,1+np.argsort(ids)]].argmax()])
            assert np.all(out['actions'][te,1,k]==expected_global) and np.all(out['actions'][te,0,k]==0);counts['actions']+=2*len(te)
            for m,name in enumerate(C['arms']):
                selected=out['actions'][te,m,k]
                actual=np.column_stack([dr[te,selected,k],dt[te,selected,k],utility[te,selected,k]])
                assert np.max(np.abs(actual-out['values'][te,m,k]))<1e-12;counts['values']+=len(te)*3
    for m,name in enumerate(C['arms']):
        s=information['datasets'][ds]['methods'][name]
        assert abs(s['equal_K_u_mean']-out['values'][:,m,:,2].mean())<1e-14
        for k,K in enumerate(C['K']):
            ss=s['K'][str(K)];val=out['values'][:,m,k];pred=out['selected_prediction'][:,m,k];sw=out['actions'][:,m,k]>0
            assert abs(ss['recall_gain_pp']-val[:,0].mean()*100)<1e-12
            assert abs(ss['graph_time_change_pct']-val[:,1].mean()*100)<1e-12
            assert ss['switches']==int(sw.sum())
            calibration.append({'method':name,'K':K,'selected_predicted_u':float(pred.mean()),'selected_actual_u':float(val[:,2].mean()),'selection_optimism':float((pred-val[:,2]).mean()),'positive_actual_switches':int((sw&(val[:,2]>0)).sum()),'negative_actual_switches':int((sw&(val[:,2]<0)).sum()),'mse_relative_to_global':float(out['mse'][:,m,k].mean()/out['mse'][:,1,k].mean())})
    report['datasets'][ds]={'status':'PASS','checked':counts,'maximum_errors':maxerr,'calibration':calibration}
    print(ds,counts,maxerr,flush=True)
report.update(status='PASS',wall_seconds=time.perf_counter()-started,new_fits=0,new_searches=0,scope='Independent computation, not an independent person; descriptive post-hoc calibration only.')
target=R/'reviews/independent_audit.json';assert not target.exists();target.write_text(json.dumps(report,indent=2)+'\n')
print('AUDIT PASS',flush=True)
