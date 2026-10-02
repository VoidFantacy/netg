import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='8'
import hashlib,json,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent;P=R.parent.parent;ROOT=P.parents[1];E=P/'stages/e124_semantic_service_ridge_v1';BASE=ROOT/'entry_method_exploration/20260910_gt_topk_profiles_v1'
C=json.loads((E/'config.locked.json').read_text());I={}
def ident(p):return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def read(p):I[str(p)]=ident(p);return json.loads(p.read_text())
def load(p):I[str(p)]=ident(p);return np.load(p)
def raw(p,t):I[str(p)]=ident(p);return np.fromfile(p,t)
def dump(p,v):assert not p.exists(),p;p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def unit(x):return x/np.maximum(np.linalg.norm(x,axis=1,keepdims=True),1e-12)
def describe(a):return {'min':float(np.min(a)),'median':float(np.median(a)),'mean':float(np.mean(a)),'q90':float(np.quantile(a,.9)),'max':float(np.max(a))}
def agreement(pa,pb,subset):
    a=pa[subset];b=pb[subset];cos=np.sum(a*b,axis=1);ac=a-a.mean(0);bc=b-b.mean(0)
    den=float((ac*ac).sum()+(bc*bc).sum())
    return {'hubs':len(a),'cosine':describe(cos),'angle_degrees':describe(np.degrees(np.arccos(np.clip(cos,-1,1)))),'centered_profile_replicability':float(2*(ac*bc).sum()/den),'centered_energy_A':float((ac*ac).sum()),'centered_energy_B':float((bc*bc).sum())}
dump(R/'reviews/frozen.json',{'files':{str(p):ident(p) for p in [R/'protocol.md',Path(__file__),E/'reviews/seal.json']},'split_seed':2026092226})
started=time.perf_counter();summaries={};bigs={};scalar_checks=0;profile_aggregations=0
for di,(ds,dc) in enumerate(C['datasets'].items()):
    n=20000;d=dc['dimension'];sem=load(E/'inputs'/ds/'semantic.npz');ids=sem['ids'];H=len(ids);rows=raw(Path(dc['fit_source']['row_ids']),'<i8');qraw=raw(Path(dc['fit_source']['queries_file']),'<f4').reshape(n,d);q=unit(qraw).astype('f8');hraw=raw(BASE/'inputs'/ds/'raw_hubs.f32','<f4').reshape(H,d);hubs=unit(hraw);owner=sem['owners']
    assert np.array_equal(rows,sem['rows']);gt=raw(Path(dc['fit_source']['gt_file']),'<i8').reshape(n,100)
    assignment=load(ROOT/'entry_method_exploration/20260911_gt10_mechanism_v1/results'/f'{ds}_fit_assignments.npz')
    assert np.array_equal(assignment['rank_hubs'],ids[owner[:,:10]]) and np.array_equal(assignment['row_ids'],rows)
    labels={'GT1Hard':np.eye(H)[owner[:,0]],'GT10Hard':np.zeros((n,H))}
    for k in range(10):labels['GT10Hard'][np.arange(n),owner[:,k]]+=.1
    metadata={'all_original_rank_matches':n*10,'soft_target_hashes':[]};names={'GT1Hard':'gt1_hard','GT10Hard':'gt10_hard'}
    if ds.startswith('web'):
        names['GT10Soft']='gt10_soft_t1';manifest=read(BASE/'models'/ds/'gt10_soft_t1/manifest.json');temp=manifest['temperature'];labels['GT10Soft']=np.zeros((n,H));bp=Path(dc['base']);st=bp.stat();bigs[str(bp)]={'bytes':st.st_size,'mtime_ns':st.st_mtime_ns};base=np.memmap(bp,'<f4',mode='r').reshape(dc['base_n'],d+1)
        assert np.array_equal(base[ids,1:],hraw)
        for rank in range(10):
            targetraw=np.array(base[gt[:,rank],1:],dtype='f4');metadata['soft_target_hashes'].append(hashlib.sha256(targetraw.tobytes()).hexdigest());target=unit(targetraw)
            for lo in range(0,n,4096):
                hi=min(lo+4096,n);score=target[lo:hi]@hubs.T;assert np.array_equal(score.argmax(1),owner[lo:hi,rank]);z=score.astype('f8');z-=z.max(1,keepdims=True);z/=temp;np.exp(z,out=z);z/=z.sum(1,keepdims=True);labels['GT10Soft'][lo:hi]+=z/10
        del base
        metadata['soft_temperature']=temp;metadata['soft_assignment_sha256']=hashlib.sha256(labels['GT10Soft'].tobytes()).hexdigest();metadata['original_soft_assignment_sha256']=manifest['assignments_sha256'];metadata['soft_assignment_bytes_match_original']=metadata['soft_assignment_sha256']==manifest['assignments_sha256']
        np.savez_compressed(R/'results'/f'{ds}.soft_labels.npz',A=labels['GT10Soft'])
    rng=np.random.default_rng(2026092226+di);split=rng.permutation(n);halves=[np.sort(split[:n//2]),np.sort(split[n//2:])];perms=[rng.permutation(idx) for idx in halves]
    np.savez(R/'results'/f'{ds}.roles.npz',A=halves[0],B=halves[1],shuffle_A=perms[0],shuffle_B=perms[1],rows=rows)
    common=np.where((labels['GT1Hard'][halves[0]].sum(0)>0)&(labels['GT1Hard'][halves[1]].sum(0)>0))[0]
    out={};models={}
    for name,a in labels.items():
        assert np.abs(a.sum(1)-1).max()<1e-12
        full=unit(hubs.astype('f8')+a.T@q);ref=raw(BASE/'models'/ds/names[name]/'W.f32','<f4').reshape(H,d);diff=float(np.max(np.abs(full-ref)));assert diff<2e-5,(name,diff);profile_aggregations+=1
        moments=[a[idx].T@q[idx] for idx in halves];shuffled=[a[pi].T@q[idx] for idx,pi in zip(halves,perms)]
        pa=[unit(hubs.astype('f8')+x) for x in moments];ps=[unit(hubs.astype('f8')+x) for x in shuffled];profile_aggregations+=4
        models[name+'_actual']=np.stack(pa);models[name+'_shuffled']=np.stack(ps)
        supports=[];cross=[]
        for half,idx in enumerate(halves):
            mass=a[idx].sum(0);squared=(a[idx]**2).sum(0);ess=np.divide(mass**2,squared,out=np.zeros(H),where=squared>0)
            supports.append({'zero_mass_hubs':int((mass==0).sum()),'mass':describe(mass),'query_ESS_descriptor':describe(ess),'prior_mass_fraction':describe(1/(1+mass))})
            other=1-half;global_direction=unit(q[idx].mean(0,keepdims=True))[0]
            cross.append({'train_half':half,'test_half':other,'actual_profile_affinity':float((moments[other]*pa[half]).sum()/len(halves[other])),'shuffled_profile_affinity':float((moments[other]*ps[half]).sum()/len(halves[other])),'raw_hub_affinity':float((moments[other]*hubs).sum()/len(halves[other])),'training_global_query_mean_affinity':float(q[halves[other]].mean(0)@global_direction)})
            for h,j in zip(np.linspace(0,H-1,16,dtype=int),np.linspace(0,d-1,16,dtype=int)):
                x=sum(float(ai)*float(qi) for ai,qi in zip(a[idx,h],q[idx,j]));assert abs(x-moments[half][h,j])<1e-10;scalar_checks+=1
        out[name]={'full_profile_reference_max_abs_error':diff,'full_profile_float32_bytes_match':np.array_equal(full.astype('f4'),ref),'actual_all_hubs':agreement(pa[0],pa[1],np.arange(H)),'actual_shared_GT1_support':agreement(pa[0],pa[1],common),'shuffled_all_hubs':agreement(ps[0],ps[1],np.arange(H)),'shuffled_shared_GT1_support':agreement(ps[0],ps[1],common),'support_halves':supports,'cross_half_affinity':cross}
    np.savez(R/'results'/f'{ds}.profiles.npz',**models,ids=ids,common_support=common)
    summaries[ds]={'metadata':metadata,'families':out};print(ds,{name:{'angle':round(x['actual_all_hubs']['angle_degrees']['median'],3),'rho':round(x['actual_all_hubs']['centered_profile_replicability'],5),'shuffled_rho':round(x['shuffled_all_hubs']['centered_profile_replicability'],5),'affinity_minus_shuffle':round(np.mean([z['actual_profile_affinity']-z['shuffled_profile_affinity'] for z in x['cross_half_affinity']]),6)} for name,x in out.items()},flush=True)
for p,v in I.items():assert ident(Path(p))==v
for p,v in bigs.items():st=Path(p).stat();assert st.st_size==v['bytes'] and st.st_mtime_ns==v['mtime_ns']
dump(R/'results/summary.json',summaries);dump(R/'reviews/inputs.json',{'files':I,'bases_stat_only':bigs})
dump(R/'reviews/complete.json',{'status':'DESCRIPTIVE_ONLY','seconds':time.perf_counter()-started,'profile_aggregations':profile_aggregations,'scalar_checks':scalar_checks,'input_files':len(I),'new_gradient_fits':0,'new_ann_nsg_gt_graph_qps':0,'new_closed_form_profile_statistics':True})
