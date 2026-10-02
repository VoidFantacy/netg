import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[key]='8'
import hashlib,json,time,itertools
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent;P=R.parents[1];E=P.parent
OLD=E/'20260921_comparison_direction_pilot_v1';BASE=E/'20260910_gt_topk_profiles_v1';HISTORY=E/'20260920_gt10_conditional_mechanism_v1'
def read(p):return json.loads(p.read_text())
C=read(OLD/'config.locked.json');HC=read(HISTORY/'config.locked.json');inputs={}
def ident(p):return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def raw(p,t):inputs[str(p)]=ident(p);return np.fromfile(p,t)
def loaded(p):inputs[str(p)]=ident(p);return dict(np.load(p))
def dump(p,v):assert not p.exists(),p;p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def norm(x):return x/np.maximum(np.linalg.norm(x,axis=1,keepdims=True),1e-12)
def moment(x,y,center):
    if center:x=x-x.mean(0);y=y-y.mean(0)
    m=x.T@y/(len(x)-1 if center else len(x))
    return m-m.mean(1,keepdims=True)
def comparison(a,b):
    aa=float((a*a).sum());bb=float((b*b).sum());ab=float((a*b).sum())
    return {'norm_A_squared':aa,'norm_B_squared':bb,'inner_product':ab,'cosine':ab/np.sqrt(aa*bb),'replicability':2*ab/(aa+bb),'half_difference_energy':.5*float(((a-b)**2).sum())}
dump(R/'frozen.json',{'files':{str(p):ident(p) for p in [Path(__file__),R/'protocol.md']},'permutation_seed':2026092221})
start=time.perf_counter();summary={};big_inputs={};scalar_checks=0
for di,(ds,c) in enumerate(C['datasets'].items()):
    d=c['dimension'];p=OLD/'inputs'/ds/'fit';q0=raw(p/'queries.f32','<f4').reshape(4096,d);q=norm(q0).astype('f8')
    gt=raw(p/'gt.i64','<i8').reshape(4096,100);rows=raw(p/'row_ids.i64','<i8');ids=raw(Path(c['anchor']['ids']),'<i4');H=len(ids)
    roles=loaded(P/'stages/e121_router_state_table_v1/models'/ds/'roles.npz');assert np.array_equal(rows,roles['rows']);folds=roles['folds']
    original=loaded(Path(HC['datasets'][ds]['assignments']));idx=np.searchsorted(original['row_ids'],rows)
    assert np.array_equal(rows,original['row_ids'][idx]) and np.array_equal(ids,original['hub_ids'])
    old_ranks=np.searchsorted(ids,original['rank_hubs'][idx]);assert np.array_equal(ids[old_ranks],original['rank_hubs'][idx])
    original_q=raw(BASE/'inputs'/ds/'fit/queries.f32','<f4').reshape(20000,d);assert np.array_equal(original_q[idx],q0)
    original_gt=raw(BASE/'inputs'/ds/'fit/gt.i64','<i8').reshape(20000,100);assert np.array_equal(original_gt[idx],gt)
    bh=raw(BASE/'inputs'/ds/'raw_hubs.f32','<f4').reshape(H,d);hubs=norm(bh)
    basepath=Path(c['base']);stat=basepath.stat();big_inputs[str(basepath)]={'bytes':stat.st_size,'mtime_ns':stat.st_mtime_ns,'scope':'stat plus hashes of consumed selected vectors; not a new full-file SHA'}
    base=np.memmap(basepath,dtype='<f4',mode='r').reshape(c['base_n'],d+1);assert np.array_equal(base[ids,1:],bh)
    labels={'GT1Hard':np.zeros((4096,H)),'GT10Hard':np.zeros((4096,H))};labels['GT1Hard'][np.arange(4096),old_ranks[:,0]]=1
    soft=ds.startswith('web');temp=None
    if soft:
        manifest=BASE/'models'/ds/'gt10_soft_t1/manifest.json';inputs[str(manifest)]=ident(manifest);temp=read(manifest)['temperature'];assert abs(temp-.016201138496398926)<1e-18;labels['GT10Soft']=np.zeros((4096,H))
    target_hashes=[];rank_checks=0;max_dot_error=0.
    chosen_rows=np.linspace(0,4095,16,dtype=int)
    for rank in range(10):
        target0=np.array(base[gt[:,rank],1:],dtype='<f4');target_hashes.append(hashlib.sha256(target0.tobytes()).hexdigest());target=norm(target0)
        scores=target@hubs.T;best=scores.argmax(1);assert np.array_equal(best,old_ranks[:,rank]);rank_checks+=len(best)
        labels['GT10Hard'][np.arange(4096),best]+=.1
        if soft:
            z=scores.astype('f8');z-=z.max(1,keepdims=True);z/=temp;np.exp(z,out=z);z/=z.sum(1,keepdims=True);labels['GT10Soft']+=z/10
        for i in chosen_rows:
            exact=hubs.astype('f8')@target[i].astype('f8');err=float(np.abs(exact-scores[i]).max());max_dot_error=max(max_dot_error,err)
            assert int(exact.argmax())==int(best[i]);assert err<2e-6;scalar_checks+=1
    del base
    for name,a in labels.items():assert a.min()>=0 and np.max(np.abs(a.sum(1)-1))<1e-12
    target_info={'consumed_target_sha256_by_rank':target_hashes,'all_rank_assignments_match_old':rank_checks,'float64_reference_max_dot_difference':max_dot_error,'temperature':temp}
    lab=OLD/'results'/ds/'labels';done=read(lab/'complete.json')
    for K in [1,100]:
        chunks=[]
        for b in sorted(done['blocks'],key=lambda a:a['start']):chunks.append(raw(lab/f"block_{b['start']}"/f'hits{K}.u8','u1').reshape(b['n'],H+1)[:,1:]/K)
        labels[f'R{K}']=np.concatenate(chunks)
    rolesA=np.flatnonzero(folds<2);rolesB=np.flatnonzero(folds>=2);rng=np.random.default_rng(2026092221+di)
    shuffledA=rng.permutation(rolesA);shuffledB=rng.permutation(rolesB)
    np.savez(R/f'{ds}.roles.npz',A=rolesA,B=rolesB,shuffle_A=shuffledA,shuffle_B=shuffledB,folds=folds,rows=rows)
    outputs={};moments={}
    for name,y in labels.items():
        result={}
        for center in [False,True]:
            key='centered_covariance' if center else 'uncentered_moment'
            a=moment(q[rolesA],y[rolesA],center);b=moment(q[rolesB],y[rolesB],center)
            sa=moment(q[rolesA],y[shuffledA],center);sb=moment(q[rolesB],y[shuffledB],center)
            result[key]={'actual':comparison(a,b),'label_permutation':comparison(sa,sb)}
            moments[name+'_'+key+'_A']=a;moments[name+'_'+key+'_B']=b
            fm=[moment(q[folds==f],y[folds==f],center) for f in range(4)]
            result[key]['four_fold_pairs']=[dict(fold_pair=[j,k],**comparison(fm[j],fm[k])) for j,k in itertools.combinations(range(4),2)]
            # Scalar summation after centering and action projection, independent coordinates.
            xx=q[rolesA].copy();yy=y[rolesA].copy()
            if center:xx-=xx.mean(0);yy-=yy.mean(0)
            yy-=yy.mean(1,keepdims=True)
            for fi,hi in zip(np.linspace(0,d-1,16,dtype=int),np.linspace(0,H-1,16,dtype=int)):
                value=sum(float(xv)*float(yv) for xv,yv in zip(xx[:,fi],yy[:,hi]))/(len(xx)-1 if center else len(xx))
                assert abs(value-a[fi,hi])<1e-12;scalar_checks+=1
        outputs[name]=result
    np.savez(R/f'{ds}.moments.npz',**moments)
    # Derived labels retained for provenance/reuse in independent read-only verification only.
    np.savez(R/f'{ds}.derived_labels.npz',**labels)
    summary[ds]={'labels':outputs,'target_recovery':target_info}
    print(ds,{name:round(x['centered_covariance']['actual']['replicability'],5) for name,x in outputs.items()},flush=True)
for path,v in inputs.items():assert ident(Path(path))==v,path
for path,s in big_inputs.items():
    st=Path(path).stat();assert st.st_size==s['bytes'] and st.st_mtime_ns==s['mtime_ns']
dump(R/'inputs.json',{'small_files':inputs,'bases':big_inputs})
dump(R/'summary.json',{'status':'DESCRIPTIVE_ONLY','datasets':summary,'seconds':time.perf_counter()-start,'scalar_checks':scalar_checks,'input_files':len(inputs),'new_model_fits':0,'new_ann_nsg_gt':0})
