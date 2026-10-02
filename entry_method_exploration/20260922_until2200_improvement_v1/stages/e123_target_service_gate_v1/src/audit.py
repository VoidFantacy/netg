import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[key]='8'
import hashlib,json,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1];C=json.loads((R/'config.locked.json').read_text());OLD=Path(C['historical_root']);started=time.perf_counter()
def read(p):return json.loads(p.read_text())
report={'scope':'Same agent independent NumPy rank expansion and action audit; no native aggregator import','datasets':{}}
identities=read(R/'reviews/response_inputs_v2.json');fixed=read(R/'reviews/fit_frozen_v2.json')['files']
for path,x in {**identities,**fixed}.items():
    p=Path(path);assert p.stat().st_size==x['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==x['sha256']
for ds,dc in C['datasets'].items():
    reg=dict(np.load(R/'inputs'/ds/'regions.npz'));owners=reg['owners'];ids=reg['ids'];H=len(ids);A=H+1;n=C['n'];mp=R/'models_v2'/ds;oof=dict(np.load(mp/'oof.npz'));lab=OLD/'results'/ds/'labels';done=read(lab/'complete.json');rec=[];sec=[];ms=[]
    for b in sorted(done['blocks'],key=lambda a:a['start']):
        p=lab/f"block_{b['start']}";nn=b['n'];h1=np.fromfile(p/'hits1.u8','u1').reshape(nn,A);h100=np.fromfile(p/'hits100.u8','u1').reshape(nn,A)
        rec.append(np.stack([h1,h100*.01],axis=2));sec.append(np.fromfile(p/'seconds.f64','<f8').reshape(nn,A,2,3).sum(3)/3);ms.append(np.fromfile(p/'masks.u64','<u8').reshape(nn,A,2))
    recall=np.concatenate(rec);seconds=np.concatenate(sec);masks=np.concatenate(ms);dr=recall-recall[:,0,None,:];delta=seconds-seconds[:,0,None,:]
    columns=np.unique(np.linspace(0,A-1,32,dtype=int));bits=np.empty((n,len(columns),100),dtype='u1')
    for t in range(100):bits[:,:,t]=((masks[:,columns,t//64]>>np.uint64(t%64))&1).astype('u1')
    counts=np.zeros((n,H))
    for i in range(n):
        for g in owners[i]:counts[i,g]+=1
    checked_actions=0;checked_values=0;checked_hit_cells=0;worst_time=0.;worst_prediction=0.
    order=np.r_[0,1+np.argsort(ids)]
    for f in range(4):
        tr=np.flatnonzero(reg['folds']!=f);te=np.flatnonzero(reg['folds']==f);model=dict(np.load(mp/f'fold_{f}.npz'));ref=seconds[tr,0].mean(0);u=dr-.1*delta/ref
        assert np.array_equal(model['fit_rows'],reg['rows'][tr]) and np.array_equal(model['outer_rows'],reg['rows'][te]);assert np.max(np.abs(model['time_reference']-ref))<1e-16
        global_mean=u[tr].mean(0);assert np.max(np.abs(global_mean-model['global_mean']))<1e-12
        for slot,name,donor in [(1,'TargetService',tr),(2,'ShuffleService',reg['donors'][f])]:
            hist=counts[donor];members=hist.sum(0).astype('i8');queries=(hist>0).sum(0)
            assert np.array_equal(members,model[name+'_members']) and np.array_equal(queries,model[name+'_queries'])
            owner_flat=owners[donor].ravel()
            for j,a in enumerate(columns):
                actual=np.bincount(owner_flat,weights=bits[tr,j,:].ravel(),minlength=H).astype('i8')
                assert np.array_equal(actual,model[name+'_hits'][:,a]);checked_hit_cells+=H
            ts=(hist.T@delta[tr].reshape(len(tr),A*2)).reshape(H,A,2)
            err=float(np.max(np.abs(ts-model[name+'_time_sums'])));worst_time=max(worst_time,err);assert err<1e-11
            seen=members>0
            for k in range(2):
                expected=np.repeat(global_mean[:,k][None,:],H,axis=0)
                h=model[name+'_hits'];expected[seen]=(h[seen]-h[seen,:1])/members[seen,None]-.1*ts[seen,:,k]/(members[seen,None]*ref[k]);expected[:,0]=0
                assert np.max(np.abs(expected-model['tables'][slot,k]))<1e-11
        group=owners[tr,0]
        for g in range(H):
            where=tr[group==g]
            for k in range(2):
                expected=u[where,:,k].mean(0) if len(where) else global_mean[:,k]
                assert np.max(np.abs(expected-model['tables'][0,k,g]))<1e-12
        for m,name in enumerate(C['arms']):
            for k,K in enumerate(C['K']):
                if name=='Default':pred=np.zeros((len(te),A))
                elif name=='GlobalCost':pred=np.tile(global_mean[:,k],(len(te),1))
                else:
                    table=model['tables'][{'GT1Group':0,'TargetService':1,'ShuffleService':2}[name],k]
                    if name=='GT1Group' or K==1:pred=table[owners[te,0]]
                    else:
                        pred=np.empty((len(te),A))
                        for lo in range(0,len(te),16):
                            subset=te[lo:lo+16];pred[lo:lo+16]=table[owners[subset]].sum(1)/100
                pred[:,0]=0;selected=order[pred[:,order].argmax(1)]
                assert np.array_equal(selected,oof['actions'][te,m,k]);checked_actions+=len(te)
                err=float(np.max(np.abs(pred[np.arange(len(te)),selected]-oof['selected_prediction'][te,m,k])));worst_prediction=max(worst_prediction,err);assert err<1e-12
                val=np.column_stack([dr[te,selected,k],delta[te,selected,k]/ref[k],u[te,selected,k]])
                assert np.max(np.abs(val-oof['values'][te,m,k]))<1e-12;checked_values+=val.size
    report['datasets'][ds]={'status':'PASS','checked_actions':checked_actions,'checked_values':checked_values,'checked_hit_count_cells':checked_hit_cells,'hit_count_action_columns':columns.tolist(),'all_time_sums_max_error':worst_time,'all_selected_predictions_max_error':worst_prediction}
    print(ds,report['datasets'][ds],flush=True)
report.update(status='PASS',seconds=time.perf_counter()-started,protected_files=len(set(identities)|set(fixed)),new_training=0,new_searches=0)
target=R/'reviews/independent_audit_v2.json';assert not target.exists();target.write_text(json.dumps(report,indent=2)+'\n')
