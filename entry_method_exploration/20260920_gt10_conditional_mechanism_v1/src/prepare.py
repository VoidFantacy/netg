from common import *
import csv,resource,itertools

def decomposition(a,q,groups,h,prior):
    count=np.bincount(groups,minlength=h);active=count>0
    sa=np.zeros((h,h));sq=np.zeros((h,q.shape[1]))
    np.add.at(sa,groups,a);np.add.at(sq,groups,q)
    ma=np.divide(sa,count[:,None],out=np.zeros_like(sa),where=active[:,None])
    mq=np.divide(sq,count[:,None],out=np.zeros_like(sq),where=active[:,None])
    between=ma.T@sq
    centered_a=a-ma[groups];centered_q=q-mq[groups]
    residual=centered_a.T@centered_q
    total=a.T@q
    error=float(np.max(np.abs(total-between-residual)));assert error<1e-9,error
    qenergy=np.zeros(h);aenergy=np.zeros((h,h))
    np.add.at(qenergy,groups,np.einsum('ij,ij->i',centered_q,centered_q))
    np.add.at(aenergy,groups,centered_a*centered_a)
    factors=np.divide(qenergy,count-1,out=np.zeros(h),where=count>1)
    noise=factors@aenergy
    return dict(count=count,mean_a=ma,mean_q=mq,B=prior+between,D=residual,V=prior+total,
                decomposition_error=error,permutation_noise_energy=noise)

def analytic_check():
    # Exhaust every within-group permutation in a small independent fixture.
    a=np.array([[1.,0.],[.5,.5],[0.,1.],[.25,.75]])
    q=np.array([[1.,.2],[-.1,1.],[.7,.3],[.2,.6]])
    g=np.array([0,0,0,1]);prior=np.eye(2)
    z=decomposition(a,q,g,2,prior)
    draws=[]
    for perm in itertools.permutations(range(3)):
        ix=np.array([*perm,3]);draws.append(prior+a[ix].T@q)
    draws=np.stack(draws)
    assert np.allclose(draws.mean(0),z['B'],atol=1e-14)
    observed=((draws-z['B'])**2).sum(2).mean(0)
    assert np.allclose(observed,z['permutation_noise_energy'],atol=1e-14)
    direct=np.zeros_like(z['B'])
    for j in range(2):
        for i in range(4):direct[j]+=a[g==g[i],j].mean()*q[i]
    assert np.allclose(prior+direct,z['B'],atol=1e-14)
    dump(RUN/'reviews/analytic_check.json',dict(status='PASS',exhaustive_permutations=6,checks=['group mean independent sum','permutation expectation','permutation variance','V=B+D']))

def main():
    assert not (RUN/'reviews/pre_fit_lock.json').exists(),'no prepare restart'
    protected_check();start=time.time()
    dump(RUN/'reviews/pre_fit_lock.json',dict(created_unix=time.time(),files={str(p):sha(p) for p in [RUN/'config.locked.json',RUN/'protocol.md',RUN/'research.md',RUN/'src/prepare.py',RUN/'src/common.py']}))
    analytic_check();all_records={};summary=[];frozen=[]
    for ds,c in LOCK['datasets'].items():
        inp=Path(c['fit_input']);n=LOCK['fit_n'];h=c['H'];d=c['dimension']
        q=norm(np.fromfile(inp/'fit/queries.f32','<f4').reshape(n,d));q64=q.astype('float64')
        raw0=np.fromfile(inp/'raw_hubs.f32','<f4').reshape(h,d);raw=norm(raw0)
        ids=np.fromfile(inp/'hub_ids.i32','<i4');rows=np.fromfile(inp/'fit/row_ids.i64','<i8')
        old=np.load(c['assignments']);assert np.array_equal(rows,np.arange(10000,30000)) and np.array_equal(rows,old['row_ids'])
        assert np.array_equal(ids,old['hub_ids']) and (np.diff(ids)>0).all()
        ranks=np.searchsorted(ids,old['rank_hubs']);assert np.array_equal(ids[ranks],old['rank_hubs'])
        groups=ranks[:,0];a_hard=np.zeros((n,h),'float64')
        for j in range(10):a_hard[np.arange(n),ranks[:,j]]+=.1
        a1=np.zeros((n,h));a1[np.arange(n),groups]=1
        p1=norm(raw.astype('float64')+a1.T@q64).astype('float32')
        oldp1=np.fromfile(c['GT1'],'<f4').reshape(h,d);assert np.max(np.abs(p1-oldp1))<2e-6
        methods=[dict(name='GT1Exact',family='GT1',kind='original',route='exact',W=c['GT1'])]
        for family in c['families']:
            original=Path(c['family_models'][family]);manifest=read(original.parent/'manifest.json')
            if family=='hard':a=a_hard
            else:
                gt=np.fromfile(inp/'fit/gt.i64','<i8').reshape(n,100);meta=read(inp/'prepared.json')
                base=np.memmap(meta['base_file'],dtype='<f4',mode='r').reshape(c['base_n'],d+1)
                assert np.array_equal(base[ids,1:],raw0)
                a=np.zeros((n,h),'float64');temperature=manifest['temperature']
                for rank in range(10):
                    target=norm(np.asarray(base[gt[:,rank],1:],dtype='float32'))
                    for lo in range(0,n,4096):
                        hi=min(n,lo+4096);scores=target[lo:hi]@raw.T
                        assert np.array_equal(scores.argmax(1),ranks[lo:hi,rank]),'rank source parity'
                        z=scores.astype('float64');z-=z.max(1,keepdims=True);z/=temperature
                        np.exp(z,out=z);z/=z.sum(1,keepdims=True);a[lo:hi]+=z/10
                del base
            digest=hashlib.sha256(a.tobytes()).hexdigest();assert digest==manifest['assignments_sha256'],(ds,family,'assignment digest')
            assert np.max(np.abs(a.sum(1)-1))<1e-12
            data=decomposition(a,q64,groups,h,raw.astype('float64'))
            rebuilt=norm(data['V']).astype('float32');original_p=np.fromfile(original,'<f4').reshape(h,d)
            reduction=float(np.max(np.abs(rebuilt-original_p)));assert reduction<2e-6
            out=RUN/'models'/ds/family;out.mkdir(parents=True,exist_ok=False)
            np.savez_compressed(out/'decomposition.npz',hub_ids=ids,**data)
            mass=a.sum(0);squared=(a*a).sum(0);ess=mass*mass/squared
            candidate=out/'GroupMean.W.f32';norm(data['B']).astype('float32').tofile(candidate)
            title=family.title();methods.extend([dict(name=title+'OriginalExact',family=family,kind='original',route='exact',W=str(original)),dict(name=title+'GroupMeanExact',family=family,kind='candidate',route='exact',W=str(candidate))])
            permutation_details=[]
            for index,seed in enumerate(LOCK['permutation_seeds']):
                rng=np.random.Generator(np.random.PCG64(seed));permutation=np.arange(n)
                for group in range(h):
                    members=np.flatnonzero(groups==group);permutation[members]=rng.permutation(members)
                assert np.array_equal(np.sort(permutation),np.arange(n)) and np.array_equal(groups[permutation],groups)
                ap=a[permutation];assert np.max(np.abs(ap.sum(0)-mass))<1e-9
                assert np.max(np.abs((ap*ap).sum(0)-squared))<1e-9
                vp=raw.astype('float64')+ap.T@q64;path=out/f'Perm{index}.W.f32';norm(vp).astype('float32').tofile(path)
                permutation.astype('<i8').tofile(out/f'Perm{index}.rows.i64')
                methods.append(dict(name=title+f'Perm{index}Exact',family=family,kind='permutation',seed=seed,route='exact',W=str(path)))
                permutation_details.append(dict(seed=seed,moved_query_rows=int((permutation!=np.arange(n)).sum()),changed_assignment_rows=int(np.any(ap!=a,axis=1).sum()),residual_squared_norm=float(((vp-data['B'])**2).sum()),column_multisets_preserved=True,GT1_hard_labels_preserved=True))
            mean_a=data['mean_a'][groups];mean_sq=(mean_a*mean_a).sum(0);mean_ess=mass*mass/mean_sq
            angle=np.degrees(np.arccos(np.clip(np.sum(norm(data['V'])*norm(data['B']),axis=1),-1,1)))
            rec=dict(dataset=ds,family=family,assignment_sha256=digest,source_W_max_abs_reduction_error=reduction,decomposition_error=data['decomposition_error'],fit_n=n,H=h,nonempty_groups=int((data['count']>0).sum()),singleton_groups=int((data['count']==1).sum()),original_ESS_median=float(np.median(ess)),GroupMean_ESS_median=float(np.median(mean_ess)),GroupMean_angle_median=float(np.median(angle)),GroupMean_angle_max=float(angle.max()),residual_frobenius_squared=float((data['D']**2).sum()),null_permutation_expected_frobenius_squared=float(data['permutation_noise_energy'].sum()),permutations=permutation_details)
            dump(out/'manifest.json',rec);summary.append(rec)
            frozen.extend(identity(p) for p in out.iterdir() if p.is_file())
            print(ds,family,json.dumps({k:rec[k] for k in ['decomposition_error','GroupMean_angle_median','original_ESS_median','GroupMean_ESS_median','residual_frobenius_squared','null_permutation_expected_frobenius_squared']}),flush=True)
            assert time.time()-start<LOCK['prepare_seconds'];assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss<LOCK['max_rss_gib']*1024**2
        methods.append(dict(name='DefaultANN',family='default',kind='reference',route='ann',**{k:c['default'][k] for k in ['W','graph','ids']}))
        assert len(methods)==(14 if ds.startswith('webvid') else 8)
        all_records[ds]=methods
    dump(RUN/'results/fit_decomposition.json',summary)
    dump(RUN/'models/methods.json',all_records)
    frozen.append(identity(RUN/'models/methods.json'))
    protected_check()
    dump(RUN/'reviews/models_frozen.json',dict(status='PASS_FIT_DECOMPOSITION_MODELS_FROZEN',created_unix=time.time(),files=frozen,seconds=time.time()-start,new_gradient_training=0,new_graph_builds=0,evaluation_payload_access=False,maxrss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
    dump(RUN/'state.json',dict(status='MODELS_FROZEN',pending=['compile','mechanism experiment','analysis']))

if __name__=='__main__':main()
