import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[key]='8'
import ctypes as ct,hashlib,json,time
from pathlib import Path
import numpy as np
from scipy.sparse import csr_matrix
R=Path(__file__).resolve().parents[1];C=json.loads((R/'config.locked.json').read_text());OLD=Path(C['historical_root']);inputs={}
def read(p):return json.loads(p.read_text())
def ident(p):return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def raw(p,t):inputs[str(p)]=ident(p);return np.fromfile(p,t)
def loaded(p):inputs[str(p)]=ident(p);return dict(np.load(p))
def dump(p,v):assert not p.exists(),p;p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
assert read(R/'reviews/prepare_complete.json')['status']=='PASS'
fixed=[R/'protocol.md',R/'config.locked.json',Path(__file__),R/'src/aggregate.cpp',R/'bin/aggregate.so',R/'pre_fit_semantics_v2.md',R/'reviews/pre_fit_bit0_audit.json',R/'reviews/pre_fit_tie_identity.json']+list((R/'inputs').glob('*/regions.npz'))
dump(R/'reviews/fit_frozen_v2.json',{'files':{str(p):ident(p) for p in fixed}})
lib=ct.CDLL(str(R/'bin/aggregate.so'));fn=lib.aggregate
nd=lambda t:np.ctypeslib.ndpointer(dtype=t,flags='C_CONTIGUOUS')
fn.argtypes=[ct.c_int,ct.c_int,nd('i4'),nd('i4'),nd('i8'),nd('i4'),nd('u8'),nd('u8'),nd('i4'),nd('u8'),nd('f8'),nd('i8'),nd('i8'),nd('i8'),nd('f8')];fn.restype=None
def aggregate(reg,fit,donors,masks,delta,H):
    A=masks.shape[1];members=np.zeros(H,dtype='i8');queries=np.zeros(H,dtype='i8');hits=np.zeros((H,A),dtype='i8');times=np.zeros((H,A,2))
    fn(len(fit),A,fit,donors,reg['starts'],reg['groups'],reg['low_masks'],reg['high_masks'],reg['counts'],masks,delta,members,queries,hits,times)
    assert members.sum()==len(fit)*100
    return members,queries,hits,times
def make_groups(owners):
    ss=[0];gs=[];ls=[];hs=[];cs=[]
    for row in owners:
        for g in np.unique(row):
            pos=np.flatnonzero(row==g);gs.append(g);ls.append(sum(1<<int(t) for t in pos if t<64));hs.append(sum(1<<int(t-64) for t in pos if t>=64));cs.append(len(pos))
        ss.append(len(gs))
    return dict(starts=np.array(ss,dtype='i8'),groups=np.array(gs,dtype='i4'),low_masks=np.array(ls,dtype='u8'),high_masks=np.array(hs,dtype='u8'),counts=np.array(cs,dtype='i4'))
def synthetic():
    rng=np.random.default_rng(2026092223);n=7;H=9;A=5;own=rng.integers(H,size=(n,100),dtype='i4');reg=make_groups(own)
    bits=rng.integers(2,size=(n,A,100),dtype='i4');masks=np.zeros((n,A,2),dtype='u8')
    for rank in range(100):masks[:,:,rank//64]|=bits[:,:,rank].astype('u8')<<np.uint64(rank%64)
    delta=rng.normal(size=(n,A,2));fit=np.array([0,2,3,6],dtype='i4');donors=np.array([6,0,3,2],dtype='i4')
    observed=aggregate(reg,fit,donors,masks,delta,H);members=np.zeros(H,dtype='i8');queries=members.copy();hits=np.zeros((H,A),dtype='i8');times=np.zeros((H,A,2))
    for q,donor in zip(fit,donors):
        queries[np.unique(own[donor])]+=1
        for t,g in enumerate(own[donor]):members[g]+=1;hits[g]+=bits[q,:,t];times[g]+=delta[q]
    for got,ref in zip(observed[:3],[members,queries,hits]):assert np.array_equal(got,ref)
    err=float(np.max(np.abs(observed[3]-times)));assert err<1e-11
    dump(R/'reviews/aggregate_synthetic_v2.json',{'status':'PASS','max_time_sum_error':err,'checks':['members','distinct queries','per-action member hits','rank crossing 64-bit boundary','donor permutation','query-weighted time']})
synthetic()
def choose(pred,ids):
    order=np.r_[0,1+np.argsort(ids,kind='stable')]
    assert np.max(np.abs(pred[:,0]))<1e-14
    pred=pred.copy();pred[:,0]=0
    return order[pred[:,order].argmax(1)].astype('i4')
def bootstrap(x,seed):
    rng=np.random.default_rng(seed);pieces=[]
    for start in range(0,C['bootstrap_reps'],128):
        idx=rng.integers(0,len(x),size=(min(128,C['bootstrap_reps']-start),len(x)));pieces.append(x[idx].mean(1))
    return np.concatenate(pieces)
def ci(x):
    tail=(1-C['interval_coverage'])/2
    return list(map(float,np.quantile(x,[tail,1-tail])))
started=time.perf_counter();summaries={};all_u={};all_boot={};total_bit0=0
for di,(ds,dc) in enumerate(C['datasets'].items()):
    mp=R/'models_v2'/ds;mp.mkdir(parents=True);rp=R/'results_v2'/ds;rp.mkdir(parents=True)
    reg=loaded(R/'inputs'/ds/'regions.npz');ids=reg['ids'];H=len(ids);A=H+1;n=C['n'];owners=reg['owners'];rows=reg['rows'];folds=reg['folds']
    lab=OLD/'results'/ds/'labels';done=read(lab/'complete.json');rr=[];tt=[];mm=[]
    pop=np.array([i.bit_count() for i in range(256)],dtype='u1')
    for block in sorted(done['blocks'],key=lambda a:a['start']):
        b=lab/f"block_{block['start']}";nn=block['n'];assert block['A']==A
        h1=raw(b/'hits1.u8','u1').reshape(nn,A);h100=raw(b/'hits100.u8','u1').reshape(nn,A);mask=raw(b/'masks.u64','<u8').reshape(nn,A,2)
        expected_mismatch=read(R/'reviews/pre_fit_bit0_audit.json')[ds]['bit0_mismatches']; expected_block=sum(block['start']<=x['query']<block['start']+nn for x in expected_mismatch); assert int(((mask[:,:,0]&1).astype('u1')!=h1).sum())==expected_block;assert np.array_equal(pop[mask.view('u1')].sum(2),h100);assert (mask[:,:,1]>>np.uint64(36)).max()==0;total_bit0+=nn*A
        sec=raw(b/'seconds.f64','<f8').reshape(nn,A,2,3);assert np.isfinite(sec).all() and sec.min()>0
        rr.append(np.stack([h1,h100/100.],axis=2));tt.append(sec.mean(3));mm.append(mask)
    recall=np.concatenate(rr);seconds=np.concatenate(tt);masks=np.concatenate(mm);dr=recall-recall[:,:1,:];delta=np.ascontiguousarray(seconds-seconds[:,:1,:])
    count_matrix=np.zeros((n,H))
    for i in range(n):count_matrix[i]=np.bincount(owners[i],minlength=H)
    counts_sparse=csr_matrix(count_matrix/100.)
    M=len(C['arms']);actions=np.zeros((n,M,2),dtype='i4');values=np.zeros((n,M,2,3));predictions=np.zeros((n,M,2));records=[];supports=[]
    for f in range(4):
        fit=reg['train'][f];out=reg['outer'][f];donors=reg['donors'][f]
        assert not set(fit)&set(out) and set(fit)==set(donors)
        tref=seconds[fit,0].mean(0);dt=delta/tref;u=dr-C['cost_weight']*dt;global_mean=u[fit].mean(0)
        tables=np.zeros((3,2,H,A));statistics={}
        for slot,name,donor in [(1,'TargetService',fit),(2,'ShuffleService',donors)]:
            members,queries,hits,times=aggregate(reg,fit,donor,masks,delta,H);statistics[name+'_members']=members;statistics[name+'_queries']=queries;statistics[name+'_hits']=hits;statistics[name+'_time_sums']=times
            seen=members>0
            for k in range(2):
                table=np.repeat(global_mean[:,k][None,:],H,axis=0)
                table[seen]=(hits[seen]-hits[seen,:1])/members[seen,None]-C['cost_weight']*times[seen,:,k]/(members[seen,None]*tref[k])
                table[:,0]=0;tables[slot,k]=table
            supports.append({'fold':f,'method':name,'unseen_regions':int((~seen).sum()),'member_support_min':int(members.min()),'member_support_median':float(np.median(members)),'member_support_max':int(members.max()),'distinct_query_support_min':int(queries.min()),'distinct_query_support_median':float(np.median(queries)),'distinct_query_support_max':int(queries.max())})
        groups=owners[fit,0];counts=np.bincount(groups,minlength=H);seen=counts>0;statistics['GT1Group_queries']=counts
        for k,K in enumerate(C['K']):
            sums=np.zeros((H,A));np.add.at(sums,groups,u[fit,:,k]);table=np.repeat(global_mean[:,k][None,:],H,axis=0);table[seen]=sums[seen]/counts[seen,None];table[:,0]=0;tables[0,k]=table
            for m,name in enumerate(C['arms']):
                if name=='Default':pred=np.zeros((len(out),A));trainpred=np.zeros((len(fit),A))
                elif name=='GlobalCost':pred=np.repeat(global_mean[:,k][None,:],len(out),axis=0);trainpred=np.repeat(global_mean[:,k][None,:],len(fit),axis=0)
                else:
                    j={'GT1Group':0,'TargetService':1,'ShuffleService':2}[name];table=tables[j,k]
                    if name=='GT1Group' or K==1:pred=table[owners[out,0]];trainpred=table[owners[fit,0]]
                    else:pred=counts_sparse[out]@table;trainpred=counts_sparse[fit]@table
                a=choose(pred,ids);ta=choose(trainpred,ids);actions[out,m,k]=a;predictions[out,m,k]=pred[np.arange(len(out)),a]
                for col,quantity in enumerate([dr,dt,u]):values[out,m,k,col]=quantity[out,a,k]
                records.append({'fold':f,'method':name,'K':K,'train_u':float(u[fit,ta,k].mean()),'outer_u':float(u[out,a,k].mean()),'train_recall_gain_pp':float(dr[fit,ta,k].mean()*100),'outer_recall_gain_pp':float(dr[out,a,k].mean()*100),'predicted_outer_u':float(predictions[out,m,k].mean()),'switches':int((a>0).sum()),'time_reference_seconds':float(tref[k])})
        np.savez(mp/f'fold_{f}.npz',tables=tables,global_mean=global_mean,time_reference=tref,fit_rows=rows[fit],outer_rows=rows[out],**statistics)
        print(ds,'fold',f,'complete',flush=True)
    np.savez(mp/'oof.npz',actions=actions,values=values,selected_prediction=predictions,folds=folds,rows=rows)
    uu=values[:,:,:,2].mean(2);bb=bootstrap(uu,C['seed']+di*10000);all_u[ds]=uu;all_boot[ds]=bb;methods={}
    for m,name in enumerate(C['arms']):
        ks={}
        for k,K in enumerate(C['K']):
            g=values[:,m,k,0];t=values[:,m,k,1]
            ks[str(K)]={'recall_gain_pp':float(g.mean()*100),'graph_time_change_pct':float(t.mean()*100),'u_mean':float(values[:,m,k,2].mean()),'positive_queries':int((g>0).sum()),'negative_queries':int((g<0).sum()),'positive_mass':float(g[g>0].sum()),'negative_mass':float(-g[g<0].sum()),'switches':int((actions[:,m,k]>0).sum()),'predicted_selected_u_mean':float(predictions[:,m,k].mean())}
        methods[name]={'equal_K_u_mean':float(uu[:,m].mean()),'equal_K_u_interval':ci(bb[:,m]),'K':ks}
    summaries[ds]={'methods':methods};dump(rp/'fold_metrics.json',records);dump(rp/'supports.json',supports)
    print(ds,{name:round(v['equal_K_u_mean']*100,5) for name,v in methods.items()},flush=True)
candidate=C['eligible'];m=C['arms'].index(candidate);checks={};contrasts={}
for ds,s in summaries.items():
    v=s['methods'][candidate];checks[ds+'.positive_u']=v['equal_K_u_interval'][0]>0;checks[ds+'.recall_floor']=all(x['recall_gain_pp']>=-C['max_k_recall_loss_pp'] for x in v['K'].values())
for control in ['GlobalCost','ShuffleService']:
    j=C['arms'].index(control);bs=sum((v[:,m]-v[:,j])/len(all_boot) for v in all_boot.values());means={ds:float((u[:,m]-u[:,j]).mean()) for ds,u in all_u.items()};interval=ci(bs)
    checks['beats_'+control]=all(v>0 for v in means.values()) and interval[0]>0;contrasts[control]={'dataset_mean_differences':means,'equal_dataset_interval':interval}
passed=all(checks.values());status='PASS_PRIVILEGED_INFORMATION_ONLY' if passed else 'STOP_TARGET_SERVICE_PRIVILEGED_GATE'
dump(R/'results_v2/information.json',{'datasets':summaries,'checks':checks,'contrasts':contrasts,'status':status,'privileged_GT_input':True,'interval_coverage':C['interval_coverage']})
dump(R/'results_v2/gate.json',{'status':status,'eligible':candidate,'default_changed':False,'online_candidate':False})
dump(R/'reviews/response_inputs_v2.json',inputs)
for path,v in inputs.items():assert ident(Path(path))==v,path
dump(R/'reviews/fit_complete_v2.json',{'status':'PASS','seconds':time.perf_counter()-started,'conditional_tables':48,'global_mean_heads':16,'native_aggregations':16,'actual_bit0_checks':total_bit0,'known_tie_query_action_mismatches':107,'input_files':len(inputs),'new_ann_nsg_gt':0,'new_search_graphs':0,'new_online_models':0,'independent_audit_pending':True})
print(status,flush=True)
