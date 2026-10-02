import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='8'
import json,hashlib,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1];C=json.loads((R/'config.locked.json').read_text());I={};started=time.perf_counter();summaries={};new_calls=0;return_vectors=0
assert json.loads((R/'reviews/jobs_complete.json').read_text())['status']=='PASS'
def ident(p):return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def read(p):I[str(p)]=ident(p);return json.loads(p.read_text())
def raw(p,t):I[str(p)]=ident(p);return np.fromfile(p,t)
def load(p):I[str(p)]=ident(p);return np.load(p)
def dump(p,v):assert not p.exists(),p;p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
dump(R/'reviews/analysis_frozen.json',{'files':{str(p):ident(p) for p in [Path(__file__),R/'protocol.md',R/'config.locked.json']},'interval_coverage':.95})
def bootstrap(x,seed):
    rng=np.random.default_rng(seed);result=[]
    for lo in range(0,C['bootstrap_reps'],128):ix=rng.integers(0,len(x),(min(128,C['bootstrap_reps']-lo),len(x)));result.append(x[ix].mean(1))
    return np.concatenate(result)
for di,(ds,dc) in enumerate(C['datasets'].items()):
    p=R/'inputs_v2'/ds;old=load(p/'old_reference.npz');gt=raw(p/'gt.i64','<i8').reshape(256,100);ids=raw(Path(dc['anchor']['ids']),'<i4');H=len(ids);A=H+1;n=256;assert (np.diff(ids)>0).all();complete=read(R/'results'/ds/'complete.json');new_calls+=complete['new_search_calls'];assert complete['threads']==1
    row=np.arange(n);entry_actions=np.searchsorted(ids,old['entries'])+1;assert np.array_equal(ids[entry_actions-1],old['entries']);data={};records={}
    for k,K in enumerate([1,100]):
        L=1000 if ds.startswith('web') and K==1 else 1250 if ds.startswith('web') else 128 if K==1 else 256
        low=old['hits1'] if K==1 else old['hits100'];high=[];high_ndc=[]
        if ds.startswith('yandex') and K==1:high=low.copy();high_ndc=old['ndc'].copy();source='inherited E118 all-H K1/L128'
        else:
            pp=R/'results'/ds/f'K{K}_L{L}';source='new actual fixed-budget all-H response'
            for lo in range(0,n,16):
                bp=pp/f'block_{lo}';b=read(bp/'complete.json');nb=b['n'];out=raw(bp/'ids.i32','<i4').reshape(nb,A,K);dist=raw(bp/'distances.f32','<f4').reshape(nb,A,K);stored=raw(bp/'hits.u8','u1').reshape(nb,A);ndc=raw(bp/'ndc.u64','<u8').reshape(nb,A)
                assert (out>=0).all() and (out<dc['base_n']).all() and np.isfinite(dist).all();assert K==1 or (np.diff(np.sort(out,axis=-1),axis=-1)>0).all()
                scored=np.empty((nb,A),dtype='u1')
                for j in range(nb):
                    if K==1:scored[j]=(out[j,:,0]==gt[lo+j,0])
                    else:
                        sortedGT=np.sort(gt[lo+j]);pos=np.searchsorted(sortedGT,out[j]);scored[j]=((pos<100)&(sortedGT[np.minimum(pos,99)]==out[j])).sum(-1)
                assert np.array_equal(scored,stored),'all returned members independently scored';high.append(scored);high_ndc.append(ndc);return_vectors+=nb*A
            high=np.concatenate(high);high_ndc=np.concatenate(high_ndc)
        low_actions=low.argmax(1);high_actions=high.argmax(1);restricted=np.column_stack([high[:,0],high[row[:,None],entry_actions]]).max(1)
        methods={'Default':high[:,0],'FullHOracle':high[row,high_actions],'Top3SingleOracle':restricted,'LowL128OracleTransferred':high[row,low_actions],'E123TargetServiceTransferred':high[row,old['E123TargetService_actions'][:,k]],'E124SemanticService19kTransferred':high[row,old['E124SemanticService19k_actions'][:,k]]}
        names=list(methods);returns=np.column_stack(list(methods.values()))/K;delta=returns-returns[:,:1];boot=bootstrap(delta,C['bootstrap_seed']+di*100+k);low_headroom=(low.max(1)-low[:,0])/K;high_headroom=delta[:,1]
        old_new=np.column_stack([high_headroom,low_headroom,high_headroom-low_headroom]);head_boot=bootstrap(old_new,C['bootstrap_seed']+di*100+k+10)
        method_record={}
        for m,name in enumerate(names):
            dr=delta[:,m];ci=np.quantile(boot[:,m],[.025,.975]);method_record[name]={'recall':float(returns[:,m].mean()),'recall_gain_pp':float(dr.mean()*100),'gain_interval_pp':list(map(float,ci*100)),'positive_queries':int((dr>0).sum()),'negative_queries':int((dr<0).sum()),'positive_member_mass':int(np.maximum(dr*K,0).round().sum()),'negative_member_mass':int(np.maximum(-dr*K,0).round().sum())}
        oracle_mass=float(high_headroom.sum());low_mass=float(low_headroom.sum());records[str(K)]={'L':L,'response_source':source,'methods':method_record,'low_L128_fullH_oracle_gain_pp':float(low_headroom.mean()*100),'target_minus_low_oracle_gain_pp':float((high_headroom-low_headroom).mean()*100),'target_minus_low_interval_pp':list(map(float,np.quantile(head_boot[:,2],[.025,.975])*100)),'target_oracle_fraction_of_low':None if low_mass==0 else oracle_mass/low_mass,'top3_coverage_fraction':None if oracle_mass==0 else float(delta[:,2].sum()/oracle_mass),'low_oracle_transfer_fraction_of_target_oracle':None if oracle_mass==0 else float(delta[:,3].sum()/oracle_mass),'oracle_nondefault_queries':int((high_actions!=0).sum()),'oracle_distinct_selected_hubs':int(len(np.unique(high_actions[high_actions>0]))),'default_graph_NDC_mean':float(high_ndc[:,0].mean()),'oracle_graph_NDC_mean':float(high_ndc[row,high_actions].mean()),'NDC_is_not_QPS':True,'K1_one_query_step_pp':100/n if K==1 else None}
        data[f'K{K}_target_hits']=high;data[f'K{K}_target_ndc']=high_ndc;data[f'K{K}_high_oracle_actions']=high_actions;data[f'K{K}_low_oracle_actions']=low_actions;data[f'K{K}_method_returns']=returns;data[f'K{K}_method_delta']=delta;data[f'K{K}_bootstrap_delta']=boot
    np.savez(R/'results'/f'{ds}.derived.npz',**data);summaries[ds]=records;print(ds,json.dumps(records),flush=True)
for p,v in I.items():assert ident(Path(p))==v,p
dump(R/'results/summary.json',{'status':'DESCRIPTIVE_FULL_H_RESPONSE_ONLY','datasets':summaries,'default_changed':False,'new_candidate_eligible':False,'QPS_measured':False});dump(R/'reviews/analysis_inputs.json',I);dump(R/'reviews/analysis_complete.json',{'status':'PASS','seconds':time.perf_counter()-started,'new_NSG_calls':new_calls,'all_new_return_vectors_rescored':return_vectors,'input_files':len(I),'new_fits':0,'new_GT':0,'K10_evaluations':0})
