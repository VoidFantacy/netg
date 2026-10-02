import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[key]='8'
import hashlib,json,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1];C=json.loads((R/'config.locked.json').read_text());OLD=Path(C['historical_root']);HIST=Path(C['assignment_history_config'])
HC=json.loads(HIST.read_text());inputs={}
def ident(p):return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def raw(p,t):inputs[str(p)]=ident(p);return np.fromfile(p,t)
def loaded(p):inputs[str(p)]=ident(p);return dict(np.load(p))
def dump(p,v):assert not p.exists(),p;p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def norm(x):return x/np.maximum(np.linalg.norm(x,axis=1,keepdims=True),1e-12)
dump(R/'reviews/prepare_frozen.json',{'files':{str(p):ident(p) for p in [Path(__file__),R/'protocol.md',R/'config.locked.json']}})
started=time.perf_counter();results={}
for di,(ds,dc) in enumerate(C['datasets'].items()):
    out=R/'inputs'/ds;out.mkdir(parents=True);n=C['n'];d=dc['dimension'];ids=raw(Path(dc['anchor']['ids']),'<i4');H=len(ids)
    p=OLD/'inputs'/ds/'fit';gt=raw(p/'gt.i64','<i8').reshape(n,100);rows=raw(p/'row_ids.i64','<i8');roles=loaded(Path(C['roles_root'])/ds/'roles.npz');assert np.array_equal(roles['rows'],rows)
    source=loaded(Path(HC['datasets'][ds]['assignments']));ix=np.searchsorted(source['row_ids'],rows);assert np.array_equal(rows,source['row_ids'][ix]);assert np.array_equal(ids,source['hub_ids'])
    original=np.searchsorted(ids,source['rank_hubs'][ix]);bp=Path(dc['base']);st=bp.stat();assert gt.min()>=0 and gt.max()<dc['base_n']
    base=np.memmap(bp,dtype='<f4',mode='r').reshape(dc['base_n'],d+1);hubraw=np.array(base[ids,1:],dtype='f4');hubs=norm(hubraw)
    reference_hubs=raw(Path(HC['datasets'][ds]['fit_input'])/'raw_hubs.f32','<f4').reshape(H,d);assert np.array_equal(hubraw,reference_hubs)
    owners=np.empty((n,100),dtype='i4');targethashes=[];refmismatch=0;maxerror=0.
    for rank in range(100):
        target0=np.array(base[gt[:,rank],1:],dtype='<f4');targethashes.append(hashlib.sha256(target0.tobytes()).hexdigest());target=norm(target0);scores=target@hubs.T
        owners[:,rank]=scores.argmax(1)
        if rank<10:assert np.array_equal(owners[:,rank],original[:,rank])
        for i in np.linspace(0,n-1,16,dtype=int):
            ref=hubs.astype('f8')@target[i].astype('f8');maxerror=max(maxerror,float(np.abs(ref-scores[i]).max()));refmismatch+=int(ref.argmax()!=owners[i,rank])
        if rank%20==19:print(ds,'target rank',rank+1,flush=True)
    del base
    lowbits=np.array([1<<k if k<64 else 0 for k in range(100)],dtype='u8');highbits=np.array([1<<(k-64) if k>=64 else 0 for k in range(100)],dtype='u8')
    starts=[0];groups=[];los=[];his=[];counts=[]
    for row in owners:
        uni,inv,num=np.unique(row,return_inverse=True,return_counts=True);lo=np.zeros(len(uni),dtype='u8');hi=lo.copy();np.bitwise_or.at(lo,inv,lowbits);np.bitwise_or.at(hi,inv,highbits)
        groups.extend(uni);los.extend(lo);his.extend(hi);counts.extend(num);starts.append(len(groups))
    starts=np.array(starts,dtype='i8');groups=np.array(groups,dtype='i4');los=np.array(los,dtype='u8');his=np.array(his,dtype='u8');counts=np.array(counts,dtype='i4')
    assert np.array_equal(np.add.reduceat(counts,starts[:-1]),np.full(n,100))
    train=np.stack([np.flatnonzero(roles['folds']!=f) for f in range(4)]).astype('i4');outer=np.stack([np.flatnonzero(roles['folds']==f) for f in range(4)]).astype('i4')
    donors=np.stack([np.random.default_rng(C['seed']+di*10000+f).permutation(tr) for f,tr in enumerate(train)]).astype('i4')
    for tr,dr in zip(train,donors):assert np.array_equal(np.sort(tr),np.sort(dr))
    np.savez(out/'regions.npz',owners=owners,starts=starts,groups=groups,low_masks=los,high_masks=his,counts=counts,ids=ids,rows=rows,folds=roles['folds'],train=train,outer=outer,donors=donors)
    results[ds]={'n':n,'H':H,'unique_regions_per_query_mean':float(np.diff(starts).mean()),'unique_regions_per_query_median':float(np.median(np.diff(starts))),'first_ten_rank_parity':n*10,'float64_reference_comparisons':100*16,'float64_reference_owner_disagreements':refmismatch,'max_float32_float64_score_error':maxerror,'base_stat':{'path':str(bp),'bytes':st.st_size,'mtime_ns':st.st_mtime_ns},'consumed_target_sha256_by_rank':targethashes}
    assert bp.stat().st_size==st.st_size and bp.stat().st_mtime_ns==st.st_mtime_ns
    print(ds,'prepared',results[ds]['unique_regions_per_query_mean'],flush=True)
for path,v in inputs.items():assert ident(Path(path))==v,path
dump(R/'reviews/prepare_inputs.json',inputs);dump(R/'reviews/prepare_complete.json',{'status':'PASS','datasets':results,'seconds':time.perf_counter()-started,'input_files':len(inputs),'new_ann_nsg_gt':0,'new_response_reads':0})
