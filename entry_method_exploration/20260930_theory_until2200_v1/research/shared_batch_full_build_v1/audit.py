import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[key]='8'
os.sched_setaffinity(0,range(8))
import hashlib,importlib.util,json,time
from pathlib import Path
import numpy as np
from threadpoolctl import threadpool_limits
from graph_decode import decode_graph
R=Path(__file__).resolve().parent;C=json.loads((R/'config.locked.json').read_text());REF=json.loads((R/'reviews/validation_references.json').read_text())

def sha(x):return hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()

def ident(p):
    p=Path(p);h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(16<<20),b''):h.update(b)
    return {'bytes':p.stat().st_size,'sha256':h.hexdigest()}

def dump(p,x):
    with Path(p).open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')

def check_time():
    assert time.time()<C['deadline_unix'] and time.time()-C['stage_started_unix']<C['seconds_cap']

def arrays(p,name,n):
    return np.fromfile(p/(name+'.ids.i64'),'<i8').reshape(n,11),np.fromfile(p/(name+'.dist.f32'),'<f4').reshape(n,11)

def labels(c):
    p=Path(c['output']);rows=np.fromfile(p/'exact_rows.i32','<i4');method=c['method']
    name={'Default':'fit20000','Uniform':'selected2048','EnergyTree':'pilot1024'}[method];ii,dd=arrays(p,name,len(rows))
    if method=='EnergyTree':
        added=np.fromfile(p/'selection/added_rows.i32','<i4');i2,d2=arrays(p/'selection','additional1024',len(added))
        rows=np.r_[rows,added];ii=np.r_[ii,i2];dd=np.r_[dd,d2]
    return rows,ii,dd

def full_top11(base,q):
    best=np.full((len(q),11),-np.inf);ids=np.full((len(q),11),-1,dtype='i8')
    for lo in range(0,len(base),65536):
        check_time();score=q@np.array(base[lo:lo+65536],dtype='f8').T
        pick=np.argpartition(score,-11,axis=1)[:,-11:];val=np.take_along_axis(score,pick,axis=1);pick+=lo
        merged=np.c_[best,val];mi=np.c_[ids,pick];take=np.argpartition(merged,-11,axis=1)[:,-11:]
        best=np.take_along_axis(merged,take,axis=1);ids=np.take_along_axis(mi,take,axis=1)
    order=np.lexsort((ids,-best),axis=1);return np.take_along_axis(ids,order,axis=1),np.take_along_axis(best,order,axis=1)

def exact_comparison(rows,ii,dd,old,oldd):
    a=np.asarray(old[rows,:11]);b=np.asarray(oldd[rows,:11]);bad=np.any(ii[:,:10]!=a[:,:10],axis=1)
    return {'ordered_first10_changed_queries':int(bad.sum()),'set_first10_changed_queries':int(np.any(np.sort(ii[:,:10],axis=1)!=np.sort(a[:,:10],axis=1),axis=1).sum()),
        'changed_source_rows':rows[bad].tolist(),'first10_distance_bits_changed_cells':int(np.sum(dd[:,:10].view('u4')!=b[:,:10].view('u4'))),
        'first10_max_abs_distance_difference':float(np.max(np.abs(dd[:,:10].astype('f8')-b[:,:10]))),
        'all11_ids_identity':bool(np.array_equal(ii,a)),'all11_distance_bits_identity':bool(np.array_equal(dd.view('u4'),b.view('u4')))}

def score_returned(base,query,rows,ii,dd):
    maxerr=0.
    for lo in range(0,len(rows),256):
        values=np.einsum('nkd,nd->nk',np.array(base[ii[lo:lo+256]],dtype='f8'),query[rows[lo:lo+256]].astype('f8'))
        np.testing.assert_allclose(values,dd[lo:lo+256],rtol=1e-5,atol=3e-5);maxerr=max(maxerr,float(np.max(np.abs(values-dd[lo:lo+256]))))
    return maxerr

def actual_temperature(legacy,base,targets,h):
    z=legacy.unit(np.array(base[targets],dtype='f4'));pieces=[]
    for lo in range(0,len(z),4096):
        ordered=np.sort(z[lo:lo+4096]@h.T,axis=1);pieces.append((ordered[:,-1]-ordered[:,-2]).astype('f8'))
    gaps=np.concatenate(pieces);ordered=np.sort(gaps);mid=len(ordered)//2
    return max(float((ordered[mid-1]+ordered[mid])/2),1e-4),gaps

def graph_check(path,oldpath,w,hubids):
    x=decode_graph(path);y=decode_graph(oldpath)
    offset,num,size,labeloff,dataoff,maxlev,enter,maxM,maxM0,M,mult,efc,nodes=x
    assert num==len(hubids) and M==16 and efc==200 and maxlev==max(len(z[2])-1 for z in nodes)
    assert 0<=enter<num and len(nodes[enter][2])==maxlev+1;edges=0
    for i,(label,vector,levels) in enumerate(nodes):
        assert label==int(hubids[i]) and vector==w[i].tobytes()
        for lev,neighbors in enumerate(levels):
            assert len(neighbors)<=(maxM0 if lev==0 else maxM) and len(set(neighbors))==len(neighbors)
            assert all(0<=j<num and j!=i and len(nodes[j][2])>lev for j in neighbors);edges+=len(neighbors)
    return {'nodes':num,'edges':edges,'semantic_identity_to_old_model':x==y,'whole_file_identity_to_old_model':ident(path)==ident(oldpath)}

def main():
    started=time.perf_counter();check_time();run=json.loads((R/'reviews/run_complete.json').read_text());assert run['status']=='BUILT_PENDING_IDENTITY_AUDIT'
    assert set(run['cases'])==set(C['cases']) and json.loads((R/'reviews/active_process.json').read_text())['pid'] is None
    prep=json.loads((R/'reviews/preparation.json').read_text())
    for group in ['inputs','libraries']:
        for p,v in prep[group].items():assert ident(p)==v,p
    source=R.parent/'energy_temperature_clean_v1/common.py';spec=importlib.util.spec_from_file_location('legacy_formula',source);legacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(legacy)
    frozen={str(source):ident(source)}
    for name,c in C['cases'].items():
        r=REF[name];prior=Path(r['full_default']);pr=Path(r['profile_root'])
        paths=[Path(r['model'][k]) for k in ['ids','W','graph']]
        paths += [prior/'fit20000.ids.i64',prior/'fit20000.dist.f32',prior/'cluster_plan.npz',prior/'ids.i32',
                  prior/'qgt_demand.rows.i32',prior/'qgt_demand.ids.i64',prior/'qgt_demand.dist.f32',prior/'qgt_trace.json',prior/'qgt_generation.json',pr/'profile_complete.json']
        if c['method']!='Default':paths += [Path(r['teacher_ids']),Path(r['teacher_distances'])]
        if c['method']=='EnergyTree':paths += [pr/'selection.json',pr/'selection.npz',pr/'selected_rows.i32',pr/'added_rows.i32']
        for p in paths:frozen[str(p)]=ident(p)
    # Fix complete mismatch audit sets before any extra full-base float64 pass.
    plans={};comparisons={}
    for ds in dict.fromkeys(c['dataset'] for c in C['cases'].values()):
        first=next(c for c in C['cases'].values() if c['dataset']==ds);prior=Path(REF[first['case']]['full_default'])
        old=np.memmap(prior/'fit20000.ids.i64','<i8',mode='r',shape=(20000,100));oldd=np.memmap(prior/'fit20000.dist.f32','<f4',mode='r',shape=(20000,100))
        selected=set(range(0,20000,1250));changed=set()
        for name,c in C['cases'].items():
            if c['dataset']!=ds:continue
            rows,ii,dd=labels(c);co=exact_comparison(rows,ii,dd,old,oldd);comparisons[name]=co;changed.update(co['changed_source_rows'])
        selected.update(changed);plan={'selected_source_rows':sorted(selected),'changed_source_rows':sorted(changed)};plans[ds]=plan
    dump(R/'reviews/float64_plan.json',plans)
    assert all(len(x['selected_source_rows'])<=C['float64_audit_cap_per_dataset'] for x in plans.values()),'STOP: full prefix-disagreement audit exceeds fixed cap'
    records={};gt_calls=nsg_calls=ann_calls=fullchecks=scalar_hubs=tree_predictions=0
    with threadpool_limits(8):
        for ds,plan in plans.items():
            check_time();first=next(c for c in C['cases'].values() if c['dataset']==ds);d=first['dimension'];prior=Path(REF[first['case']]['full_default'])
            raw=np.memmap(first['base'],'<f4',mode='r',shape=(first['base_n'],d+1));base=raw[:,1:]
            query=np.fromfile(first['fit_queries'],'<f4').reshape(20000,d);q=legacy.unit(query).astype('f8');old=np.memmap(prior/'fit20000.ids.i64','<i8',mode='r',shape=(20000,100))
            selected=np.asarray(plan['selected_source_rows'],dtype='i4');t=time.perf_counter();bestids,best=full_top11(base,query[selected].astype('f8'));full_seconds=time.perf_counter()-t
            fullchecks+=len(selected);qchecks={int(qi):{'float64_top11_ids':bestids[j].tolist(),'float64_top11_scores':best[j].tolist(),
                'rank10_11_gap':float(best[j,9]-best[j,10]),'configs':{}} for j,qi in enumerate(selected)}
            for name,c in C['cases'].items():
                if c['dataset']!=ds:continue
                check_time();p=Path(c['output']);r=REF[name];pr=Path(r['profile_root']);method=c['method'];hubids=np.fromfile(p/'ids.i32','<i4')
                for f in ['ids.i32','qgt_demand.rows.i32','qgt_demand.ids.i64','qgt_demand.dist.f32','qgt_trace.json','qgt_generation.json']:assert (p/f).read_bytes()==(prior/f).read_bytes(),(name,f)
                cp=np.load(p/'cluster_plan.npz');oldcp=np.load(prior/'cluster_plan.npz')
                for key in ['assignment','first_representatives']:assert np.array_equal(cp[key],oldcp[key])
                exact=json.loads((p/'exact_complete.json').read_text());profile=json.loads((p/'profile_complete.json').read_text())
                assert hubids.tobytes()==Path(r['model']['ids']).read_bytes()
                assert profile['affinity']==list(range(8)) and all(x['num_threads']<=8 for x in profile['threadpools'])
                assert exact['cluster_centroids_sha256']==sha(oldcp['centroids'])
                assert exact['faiss_threads']==8 and exact['affinity']==list(range(8)) and all(x['num_threads']<=8 for x in exact['threadpools'])
                rows,ii,dd=labels(c);assert len(rows)==len(np.unique(rows)) and np.all((rows>=0)&(rows<20000));gt_calls+=exact['new_GT']
                assert exact['new_GT']==c['H']+(20000 if method=='Default' else (2048 if method=='Uniform' else 1024))
                phase={'Default':'fit20000','Uniform':'selected2048','EnergyTree':'pilot1024'}[method];es=exact['GT'][phase]
                initial=np.fromfile(p/'exact_rows.i32','<i4');want=np.arange(20000) if method=='Default' else np.random.default_rng(c['pilot_seed']).permutation(20000)[:len(initial)]
                assert np.array_equal(initial,want);expected_sizes=[1024]*(len(initial)//1024)+([len(initial)%1024] if len(initial)%1024 else [])
                assert es['batch_sizes']==expected_sizes and len(es['batch_seconds'])==len(expected_sizes)
                distance_error=score_returned(base,query,rows,ii,dd);lookup={int(qi):j for j,qi in enumerate(rows)}
                for j,qi in enumerate(selected):
                    if int(qi) not in lookup:continue
                    row=lookup[int(qi)];scores=np.asarray(base[ii[row,:10]],dtype='f8')@query[qi].astype('f8');threshold=float(best[j,9]);tol=2e-5*max(1.,abs(threshold))
                    assert scores.min()>=threshold-tol and scores[0]>=best[j,0]-tol
                    qchecks[int(qi)]['configs'][name]={'first10_ids':ii[row,:10].tolist(),'float64_scores':scores.tolist(),
                        'ordered_first10_matches_float64':bool(np.array_equal(ii[row,:10],bestids[j,:10])),
                        'boundary_deficit':float(max(0.,threshold-scores.min())),'tolerance':tol}
                h=legacy.unit(np.array(base[hubids],dtype='f4'));ap=None;teacher_n=0;teacher_meta=None;old_selection_identity=None
                if method!='Default':
                    teacher_meta=json.loads((p/'labels/complete.json').read_text());teacher_n=teacher_meta['n'];rest=np.fromfile(p/'approx_rows.i32','<i4') if method=='Uniform' else None
                    tr=rest if method=='Uniform' and not c['soft'] else np.arange(20000)
                    assert teacher_n==len(tr) and teacher_meta['K']==100 and teacher_meta['stored_prefix']==11 and teacher_meta['new_NSG_calls']==len(tr)+32
                    assert teacher_meta['threads']==1 and teacher_meta['native_parity_checks']==32 and teacher_meta['GT10_files_read']==teacher_meta['GT10_route_calls']==0
                    oldi=np.memmap(r['teacher_ids'],'<i4',mode='r',shape=(20000,100));oldd=np.memmap(r['teacher_distances'],'<f4',mode='r',shape=(20000,100))
                    assert teacher_meta['all100_ids_sha256']==sha(oldi[tr]) and teacher_meta['all100_dist_sha256']==sha(oldd[tr])
                    ap=np.fromfile(p/'labels/ids.i32','<i4').reshape(teacher_n,11);ad=np.fromfile(p/'labels/distances.f32','<f4').reshape(teacher_n,11)
                    assert np.array_equal(ap,oldi[tr,:11]) and np.array_equal(ad.view('u4'),oldd[tr,:11].view('u4'));nsg_calls+=len(tr)+32
                    assert run['jobs'][name+'_teacher']['single_thread_samples']>0 and run['jobs'][name+'_teacher']['max_threads']==1
                temp=None;gaps=None
                if c['soft']:temp,gaps=actual_temperature(legacy,base,ii[:,0] if method=='Default' else ap[:,0],h)
                assert profile['temperature']==temp
                if (p/'temperature_gaps.f64').exists():assert np.array_equal(np.fromfile(p/'temperature_gaps.f64','<f8'),gaps)
                if method=='Default':a=legacy.assignment(base,ii,h,temp)
                elif method=='Uniform' and not c['soft']:
                    target=np.empty((20000,11),dtype='i8');target[rows]=ii;target[rest]=ap;a=legacy.assignment(base,target,h,None)
                else:
                    a=legacy.assignment(base,ap,h,temp);approx_hash=sha(a)
                    if method=='EnergyTree':
                        # Rebuild pilot information from actual new labels and independently walk every stored tree.
                        sel=json.loads((p/'selection/selection.json').read_text());data=np.load(p/'selection/selection.npz');tree=sel['tree']
                        assert sel['temperature']==temp and sel['approx_assignment_sha256']==approx_hash
                        assert np.array_equal(data['proxy_gaps'],gaps if gaps is not None else np.zeros(20000))
                        assert np.array_equal(data['shuffle'],np.random.default_rng(c['shuffle_seed']).permutation(1024))
                        vp=h.astype('f8')+a.T@q;norm=np.linalg.norm(vp,axis=1);pp=vp/norm[:,None];tq=np.maximum(np.sum(q*q,axis=1)[:,None]-(q@pp.T)**2,0)
                        pa=legacy.assignment(base,ii[:1024],h,temp);energy=np.sum((pa-a[initial])**2*tq[initial]/norm[None,:]**2,axis=1)
                        np.testing.assert_allclose(energy,data['pilot_energy'],rtol=2e-13,atol=2e-15)
                        qn=np.linalg.norm(query.astype('f8'),axis=1);dist=ad.astype('f8')
                        features=np.column_stack([qn,dist[:,:10].mean(1)/qn,(dist[:,10]-dist[:,9])/qn,(dist[:,9]-dist[:,0])/qn,
                            -np.sum(a*np.log(np.maximum(a,1e-300)),axis=1),np.sum(a*a,axis=1),(a*a*tq)@(1/norm**2),a@(1/norm)])
                        assert np.array_equal(features,data['features']);manual=[]
                        for row in features.astype('f4'):
                            node=0;depth=0
                            while tree['children_left'][node]>=0:
                                node=tree['children_left'][node] if row[tree['feature'][node]]<=tree['threshold'][node] else tree['children_right'][node];depth+=1
                            assert depth<=2 and tree['samples'][node]>=128;manual.append(tree['values'][node])
                        np.testing.assert_array_equal(manual,data['predictions']);tree_predictions+=20000
                        order=np.random.default_rng(c['pilot_seed']).permutation(20000);added=order[1024:][np.argsort(-np.asarray(manual)[order[1024:]],kind='stable')[:1024]]
                        assert np.array_equal(rows,np.r_[initial,added]) and np.array_equal(rows,np.fromfile(p/'selection/selected_rows.i32','<i4'))
                        add=json.loads((p/'selection/additional_complete.json').read_text());assert add['n']==add['new_GT']==1024 and add['batch_sizes']==[1024]
                        assert add['affinity']==list(range(8)) and add['faiss_threads']==8 and all(x['num_threads']<=8 for x in add['threadpools']);gt_calls+=1024
                        oldsel=json.loads((pr/'selection.json').read_text())
                        old_selection_identity={'source_rows':np.array_equal(rows,np.fromfile(pr/'selected_rows.i32','<i4')),'tree':tree==oldsel['tree']}
                        old_selection_identity={k:bool(v) for k,v in old_selection_identity.items()}
                        for fp,v in json.loads((p/'selection/selection_frozen.json').read_text())['files'].items():assert ident(fp)==v
                    a[rows]=legacy.assignment(base,ii,h,temp)
                assert sha(a)==profile['assignment_sha256'];v=h.astype('f8')+a.T@q;w=legacy.unit(v).astype('<f4')
                assert sha(v)==profile['resultant_sha256'] and w.tobytes()==(p/'W.f32').read_bytes()
                max_hub_error=0.
                for slot in np.linspace(0,len(h)-1,32,dtype=int):
                    independent=h[slot].astype('f8')+np.sum(a[:,slot,None]*q,axis=0);err=float(np.max(np.abs(independent-v[slot])));max_hub_error=max(max_hub_error,err)
                    np.testing.assert_allclose(independent,v[slot],rtol=1e-12,atol=1e-12);scalar_hubs+=1
                oldw=np.fromfile(r['model']['W'],'<f4').reshape(len(h),d);gc=graph_check(p/'router.hnsw',r['model']['graph'],w,hubids)
                ra=json.loads((p/'router_audit.json').read_text());assert ra['status']=='PASS' and ra['query_pairs']==256 and ra['new_ANN_calls']==512 and ra['threads']==1;ann_calls+=512
                assert ra['cpu']==15 and run['jobs'][name+'_router_audit']['max_threads']<=1
                slots={int(hid):j for j,hid in enumerate(hubids)}
                for qi,entry in enumerate(ra['returns']):
                    for item in entry:
                        value=1.-float(np.dot(query[qi].astype('f8'),w[slots[item['id']]].astype('f8')));assert abs(value-item['distance'])<=item['round_bound']
                oldprofile=json.loads((pr/'profile_complete.json').read_text());w_identity=np.array_equal(w.view('u4'),oldw.view('u4'));temp_identity=profile['temperature']==oldprofile['temperature']
                cost=run['cases'][name];assert cost['complete_build_wall_seconds']>=cost['job_seconds_sum'] and abs(cost['job_seconds_sum']-sum(run['jobs'][x]['seconds'] for x in cost['jobs']))<1e-8
                records[name]={'dataset':ds,'method':method,**cost,'exact_prefix_comparison':comparisons[name],
                    'max_consumed_distance_abs_error_vs_float64':distance_error,'H_identity':True,'temperature_identity':temp_identity,'W_bits_identity':bool(w_identity),
                    'W_changed_float32_cells':int(np.sum(w.view('u4')!=oldw.view('u4'))),'W_max_abs_difference':float(np.max(np.abs(w.astype('f8')-oldw))),
                    'old_assignment_hash_identity':profile['assignment_sha256']==oldprofile['assignment_sha256'],'selection_identity':old_selection_identity,
                    'graph':gc,'deployment_identity_restored':bool(w_identity and temp_identity and gc['semantic_identity_to_old_model']),
                    'independent_scalar_hub_max_error':max_hub_error,'new_exact_queries':exact['new_GT']+(1024 if method=='EnergyTree' else 0),
                    'teacher_queries':teacher_n,'teacher_NSG_calls':teacher_n+32 if teacher_n else 0,'native_audit_ANN_calls':512,
                    'profile':profile,'exact_search_seconds':sum(x['search_seconds'] for x in exact['GT'].values())+(add['search_seconds'] if method=='EnergyTree' else 0)}
                print(name,'NUMERICAL AUDIT PASS','identity',records[name]['deployment_identity_restored'],flush=True)
                del a,v,w
            dump(R/'reviews'/(ds+'_float64.json'),{'selected_source_rows':selected.tolist(),'full_base_seconds':full_seconds,'checks':qchecks})
            del raw,base,query,q,old
    assert (gt_calls,nsg_calls,ann_calls)==(C['expected_GT_calls'],C['expected_NSG_calls'],C['expected_ANN_calls'])
    for kind,actual in [('GT',gt_calls),('NSG',nsg_calls),('ANN',ann_calls)]:
        l=json.loads((R/'reviews'/(kind+'_ledger.json')).read_text());assert l['completed']==l['reserved']==actual
    for group in ['inputs','libraries']:
        for p,v in prep[group].items():assert ident(p)==v,p
    for p,v in frozen.items():assert ident(p)==v
    for p,v in prep['large'].items():
        st=Path(p).stat();assert st.st_size==v['bytes'] and st.st_mtime_ns==v['mtime_ns']
    pairs={}
    for ds in plans:
        by={v['method']:v for v in records.values() if v['dataset']==ds};base=by['Default']['complete_build_wall_seconds']
        pairs[ds]={m:{'complete_wall_seconds':v['complete_build_wall_seconds'],'ratio_to_default':v['complete_build_wall_seconds']/base,
                    'deployment_identity_restored':v['deployment_identity_restored'],'old_quality_pair_may_be_reused':v['deployment_identity_restored'] and by['Default']['deployment_identity_restored']} for m,v in by.items()}
    check_time();assert sum(p.stat().st_size for p in R.rglob('*') if p.is_file())<C['max_new_bytes']
    dump(R/'results/cost_summary.json',{'status':'AUDITED_FULL_BUILD_COST_IDENTITY_SEPARATE','cases':records,'datasets':pairs,
        'all_deployment_identities_restored':all(v['deployment_identity_restored'] for v in records.values()),'new_GT':gt_calls,'new_NSG':nsg_calls,'new_ANN':ann_calls,
        'new_profiles':6,'new_graphs':6,'new_qgt_kmeans_fits':6,'new_energy_trees':2,'default_changed':False,'new_online_performance':False})
    dump(R/'reviews/independent_audit.json',{'status':'PASS','seconds':time.perf_counter()-started,'references':frozen,'scalar_hub_checks':scalar_hubs,
        'manual_tree_predictions':tree_predictions,'full_base_float64_queries':fullchecks,'native_ANN_calls':ann_calls,
        'all_deployment_identities_restored':all(v['deployment_identity_restored'] for v in records.values()),'default_changed':False,
        'scope':'same agent, separate stored legacy formula plus scalar sums, full graph decoder, tree walk and float64 full-base checks; numerical tolerance is not ID identity'})
    print('ALL FULL BUILD AUDITS PASS',time.perf_counter()-started,flush=True)

if __name__=='__main__':main()
