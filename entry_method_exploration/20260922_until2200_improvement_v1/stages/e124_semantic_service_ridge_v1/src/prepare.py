import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='8'
import hashlib,json,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1];C=json.loads((R/'config.locked.json').read_text());SERVICE=Path(C['service_root']);inputs={}
def read(p):return json.loads(p.read_text())
def ident(p):return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def raw(p,t):inputs[str(p)]=ident(p);return np.fromfile(p,t)
def loaded(p):inputs[str(p)]=ident(p);return dict(np.load(p))
def dump(p,v):assert not p.exists(),p;p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
assert read(SERVICE/'state.json')['status']=='PASS_PRIVILEGED_INFORMATION_ONLY' and read(SERVICE/'reviews/independent_audit_v2.json')['status']=='PASS'
for name,x in read(SERVICE/'reviews/seal.json')['files'].items():assert ident(SERVICE/name)==x,name
dump(R/'reviews/prepare_frozen.json',{'files':{str(p):ident(p) for p in [R/'protocol.md',R/'config.locked.json',Path(__file__),SERVICE/'reviews/seal.json']}})
hc=read(Path(C['assignment_history_config']));started=time.perf_counter();results={}
for ds,dc in C['datasets'].items():
    out=R/'inputs'/ds;out.mkdir(parents=True);d=dc['dimension'];src=Path(hc['datasets'][ds]['fit_input']);qraw=raw(src/'fit/queries.f32','<f4').reshape(20000,d);q=qraw.astype('f8');q/=np.linalg.norm(q,axis=1)[:,None]
    gt=raw(src/'fit/gt.i64','<i8').reshape(20000,100);rows=raw(src/'fit/row_ids.i64','<i8');ids=raw(Path(dc['anchor']['ids']),'<i4');H=len(ids)
    response=loaded(SERVICE/'inputs'/ds/'regions.npz');ri=np.searchsorted(rows,response['rows']);assert np.array_equal(rows[ri],response['rows']) and np.array_equal(ids,response['ids'])
    original=loaded(Path(hc['datasets'][ds]['assignments']));assert np.array_equal(original['row_ids'],rows);oldranks=np.searchsorted(ids,original['rank_hubs'])
    hashes=[hashlib.sha256(row.tobytes()).digest() for row in qraw];roles={};role_stats=[]
    for f in range(4):
        train=ri[response['train'][f]];outer=ri[response['outer'][f]];excluded=set(hashes[i] for i in outer);semantic=np.array([i for i,h in enumerate(hashes) if h not in excluded],dtype='i4')
        assert not set(hashes[i] for i in train)&excluded,'response-fold query byte duplicates'
        assert set(train)<=set(semantic) and not set(outer)&set(semantic)
        roles[f'semantic_fit_{f}']=semantic;roles[f'response_fit_{f}']=train.astype('i4');roles[f'outer_{f}']=outer.astype('i4')
        role_stats.append({'fold':f,'semantic_fit':len(semantic),'response_fit':len(train),'outer':len(outer),'additional_byte_duplicate_exclusions':20000-len(semantic)-len(outer)})
    np.savez(out/'roles.npz',response_indices=ri.astype('i4'),rows=rows,response_folds=response['folds'],**roles)
    dump(out/'roles_frozen.json',{'roles':role_stats,'roles_sha256':ident(out/'roles.npz')['sha256'],'frozen_before_full_GT_region_recovery':True})
    bp=Path(dc['base']);stat=bp.stat();base=np.memmap(bp,dtype='<f4',mode='r').reshape(dc['base_n'],d+1);h0=np.array(base[ids,1:],dtype='f4');h=h0/np.maximum(np.linalg.norm(h0,axis=1,keepdims=True),1e-12)
    owners=np.empty((20000,100),dtype='i4');target_hashes=[]
    for rank in range(100):
        traw=np.array(base[gt[:,rank],1:],dtype='<f4');target_hashes.append(hashlib.sha256(traw.tobytes()).hexdigest());target=traw/np.maximum(np.linalg.norm(traw,axis=1,keepdims=True),1e-12)
        for lo in range(0,20000,4096):owners[lo:lo+4096,rank]=(target[lo:lo+4096]@h.T).argmax(1)
        if rank<10:assert np.array_equal(owners[:,rank],oldranks[:,rank]),'E27 original GT assignment'
        assert np.array_equal(owners[ri,rank],response['owners'][:,rank]),'E123 full target assignment'
        if rank%20==19:print(ds,'rank',rank+1,flush=True)
    del base
    np.savez(out/'semantic.npz',q_unit=q,owners=owners,rows=rows,ids=ids)
    assert bp.stat().st_size==stat.st_size and bp.stat().st_mtime_ns==stat.st_mtime_ns
    results[ds]={'roles':role_stats,'same_query_byte_isolation':True,'E27_rank_checks':200000,'E123_rank_checks':409600,'target_sha256_by_rank':target_hashes,'base_stat':{'bytes':stat.st_size,'mtime_ns':stat.st_mtime_ns}}
for name,x in inputs.items():assert ident(Path(name))==x,name
dump(R/'reviews/prepare_inputs.json',inputs);dump(R/'reviews/prepare_complete.json',{'status':'PASS','datasets':results,'seconds':time.perf_counter()-started,'new_gt_search':0,'new_ann_nsg':0,'source_GT_already_existed':True})
