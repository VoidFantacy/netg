"""Freeze bounded supplement, build one diagnostic control, and compile isolated evaluator."""
import os
import shutil
import subprocess
import time
from common import *

SUP=RUN/'supplement'

def calls(c):
    n=c['num_queries'];r=c['timing_repeats']
    return sum(((2*r+1) if r else 2)*n+16+(2*n if m.get('component_wall',False) else 0) for m in c['methods'])

def ident(p):
    p=Path(p).resolve();st=p.stat();return {'path':str(p),'bytes':st.st_size,'mtime_ns':st.st_mtime_ns,'sha256':sha(p)}

def main():
    started=time.monotonic();assert read(RUN/'results/existing_evidence.json')['status']=='EXISTING_EVIDENCE_COMPLETE'
    assert (RUN/'existing_report.md').exists() and not (SUP/'config.locked.json').exists()
    for name in ['models','inputs','src','bin','configs','results','reviews','logs']:(SUP/name).mkdir(exist_ok=True)
    lock={'protocol_sha256':sha(SUP/'protocol.md'),'existing_report_sha256':sha(RUN/'existing_report.md'),
        'normal_real_call_cap':181376,'repair_real_call_cap':640,'total_real_call_cap':182016,'synthetic_call_cap':0,
        'query_cpu':15,'threads':1,'shuffle_seed':20260911,'job_timeout_seconds':1200,'total_search_seconds':1800,
        'rss_limit_bytes':40<<30,'output_limit_bytes':512<<20,'min_free_bytes':10<<30,
        'positive_point_L':{DATASETS[0]:64,DATASETS[1]:128},'historical_validation':True,'heldout_access':False}
    assert 15 in os.sched_getaffinity(0)
    dump(SUP/'config.locked.json',lock);dump(SUP/'reviews/protocol_lock.json',ident(SUP/'config.locked.json'))
    upstream=[]
    old=read(VERSIONS[26]/'reviews/immutable_integrity.json')['protected_upstream']
    for x in old:
        # Bind kernel, headers, HNSW and linked libraries. Base/graph already fully verified in A-C.
        p=Path(x['path'])
        if p.parts[len(ROOT.parts)] in ['ACSG','build'] or '/benches/hnswlib/' in str(p):
            assert sha(p)==x['sha256'],str(p);upstream.append(ident(p))
    inputs=read(RUN/'reviews/existing_sources.json')['files']
    for x in inputs:
        if '/inputs/' in x['path'] or '/models/' in x['path'] or x['path'].endswith('.fvecs') or x['path'].endswith('acosp_nsg.json'):
            st=Path(x['path']).stat();assert st.st_size==x['bytes'] and st.st_mtime_ns==x['mtime_ns'];upstream.append(x)
    for name in ['benchmark_with_nsg.cpp','legacy_reference.cpp','evaluate.cpp']:
        src=VERSIONS[26]/'src'/name;shutil.copy2(src,SUP/'src'/name);upstream.append(ident(src))
    src=SUP/'src/evaluate.cpp';s=src.read_text()
    old_check='require(m.at("k")==3 && !m.value("exact",false),"three-entry HNSW profile required");'
    assert s.count(old_check)==1
    s=s.replace(old_check,'require(m.at("k")==3,"three-entry profile required (exact3 or HNSW3)");')
    src.write_text(s)
    dump(SUP/'reviews/source_change.json',{'source':str(VERSIONS[26]/'src/evaluate.cpp'),
        'change':'allow existing exact3 Policy in isolated diagnostic evaluator; no timer/kernel/Policy changes'})
    plan=[];model_records=[];perm=np.random.default_rng(lock['shuffle_seed']).permutation(20000)
    perm.astype('<i8').tofile(SUP/'models/row_permutation.i64')
    for ds in DATASETS:
        t=time.monotonic();inp=VERSIONS[24]/'inputs'/ds;meta=read(inp/'prepared.json');h,d=meta['H'],meta['dim']
        stored=np.load(RUN/'results'/f'{ds}_fit_assignments.npz');hids=stored['hub_ids'];rr=stored['rank_hubs']
        ix=np.searchsorted(hids,rr);assert np.array_equal(hids[ix],rr)
        q=norm(arr(inp/'fit/queries.f32','<f4',(20000,d)));raw=norm(arr(inp/'raw_hubs.f32','<f4',(h,d)))
        a=np.zeros((20000,h),'float64');actual=np.zeros_like(a);ii=np.arange(20000)
        for rank in range(10):
            actual[ii,ix[:,rank]]+=.1
            a[ii,ix[:,rank] if rank==0 else ix[perm,rank]]+=.1
        assert np.max(np.abs(a.sum(1)-1))<1e-12
        assert np.max(np.abs(a.sum(0)-actual.sum(0)))<1e-9
        w=norm(raw.astype('float64')+a.T@q.astype('float64')).astype('float32')
        folder=SUP/'models'/ds;folder.mkdir();w.tofile(folder/'W.f32')
        mass=a.sum(0);sq=(a*a).sum(0);ess=np.divide(mass*mass,sq,out=np.zeros(h),where=sq>0)
        realsq=(actual*actual).sum(0);realess=np.divide(mass*mass,realsq,out=np.zeros(h),where=realsq>0)
        sums=a.T@q.astype('float64');concentration=np.divide(np.linalg.norm(sums,axis=1),mass,out=np.zeros(h),where=mass>0)
        p0=arr(VERSIONS[24]/'models'/ds/'gt1_hard/W.f32','<f4',(h,d))
        angle=np.degrees(np.arccos(np.clip(np.sum(norm(w.astype('float64'))*norm(p0.astype('float64')),axis=1),-1,1)))
        np.savez_compressed(folder/'support.npz',mass=mass,ess=ess,real_GT10_ess=realess,concentration=concentration,angle_from_GT1=angle)
        rec={'dataset':ds,'name':'tail_shuffle','W':ident(folder/'W.f32'),'permutation':ident(SUP/'models/row_permutation.i64'),
             'fixed_points':int((perm==np.arange(20000)).sum()),'mass_max_abs_difference':float(np.abs(mass-actual.sum(0)).max()),
             'ESS':desc(ess),'real_GT10_ESS':desc(realess),'concentration':desc(concentration),'angle_from_GT1_degrees':desc(angle),
             'positive_query_count':desc((a>0).sum(0)),'seconds':time.monotonic()-t,
             'assignment_sha256':hashlib.sha256(a.tobytes()).hexdigest(),'depends_on_search_labels':False}
        dump(folder/'manifest.json',rec);model_records.append(rec)
        cal=read(VERSIONS[24]/'diagnostics'/ds/'cal/config.json')
        templates={m['family']:m for m in cal['methods'] if not m['exact'] and m['family'] in ['gt1_hard','gt10_hard']}
        def method(family,L,exact=False,component=False):
            m={**templates['gt10_hard' if family=='tail_shuffle' else family], 'family':family,'model_name':family,
                'L':L,'name':f'{family}_{"exact" if exact else "hnsw"}_L{L}','exact':exact,'component_wall':component}
            if family=='tail_shuffle':m['W']=str(folder/'W.f32')
            return m
        def add(name,c,methods,reps=0):
            config={**c,'methods':methods,'threads':1,'query_cpu':15,'timing_repeats':reps,'dataset_order':DATASETS.index(ds),
                    'protocol_sha256':lock['protocol_sha256']};config['real_call_cap']=calls(config)
            config.pop('measure_wall',None)
            dump(SUP/'configs'/f'{name}.json',config)
            plan.append({'name':name,'config':str(SUP/'configs'/f'{name}.json'),'output':str(SUP/'results'/name),
                         'reserved_calls':calls(config),'stage':name.split('_')[0]})
        # Recovery inputs are exact prefixes, independent files avoid size ambiguity.
        prefix=SUP/'inputs'/ds;prefix.mkdir()
        for key,dtype,width,file in [('queries_file','<f4',d,'queries.f32'),('gt_file','<i8',100,'gt.i64'),('row_ids','<i8',1,'row_ids.i64')]:
            x=arr(cal[key],dtype).reshape(1024,width)[:32];x.tofile(prefix/file)
        recovery={**cal,'num_queries':32,'queries_file':str(prefix/'queries.f32'),'gt_file':str(prefix/'gt.i64'),
                  'row_ids':str(prefix/'row_ids.i64'),'split':'historical_cal_prefix32'}
        add('recovery_'+ds,recovery,[method(f,128,ex) for f in ['gt1_hard','gt10_hard'] for ex in [False,True]])
        for stage in ['cal','audit']:
            c=read(VERSIONS[24]/'diagnostics'/ds/stage/'config.json')
            add('shuffle_'+stage+'_'+ds,c,[method('tail_shuffle',128,ex) for ex in [False,True]])
        val=read(VERSIONS[24]/'results'/ds/'config.json');L=lock['positive_point_L'][ds]
        add('exact_'+ds,val,[method(f,L,True) for f in ['gt1_hard','gt10_hard']])
        if ds==DATASETS[0]:
            add('repeat_'+ds,val,[method(f,L,False,L==128) for L in LS for f in ['gt1_hard','gt10_hard']],3)
    # Both recoveries finish and match E24 before any new diagnostic data are searched.
    plan.sort(key=lambda j:({'recovery':0,'shuffle':1,'exact':2,'repeat':3}[j['stage']],j['name']))
    assert sum(j['reserved_calls'] for j in plan)==lock['normal_real_call_cap'] and len(plan)==9
    build=read(VERSIONS[26]/'bin/evaluate.build.json');argv=[str(x).replace(str(VERSIONS[26]),str(SUP)) for x in build['argv']]
    t=time.monotonic()
    with (SUP/'logs/compile.log').open('w') as log:rc=subprocess.run(argv,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT).returncode
    dump(SUP/'bin/evaluate.build.json',{'argv':argv,'exit_code':rc,'seconds':time.monotonic()-t,
       'sources':[ident(p) for p in (SUP/'src').glob('*.cpp')],'binary':ident(SUP/'bin/evaluate') if rc==0 else None})
    assert rc==0,'isolated compile failed; no search has run'
    dump(SUP/'reviews/upstream.json',{'files':list({x['path']:x for x in upstream}.values())})
    dump(SUP/'reviews/plan.json',plan);dump(SUP/'models/construction.json',model_records)
    frozen=[]
    for p in SUP.rglob('*'):
        if p.is_file() and '/logs/' not in str(p) and '/results/' not in str(p):frozen.append(ident(p))
    dump(SUP/'reviews/frozen_before_search.json',{'status':'FROZEN','files':frozen,'unix':time.time(),
        'new_search_calls':0,'prepared_seconds':time.monotonic()-started})
    print('SUPPLEMENT_FROZEN',len(plan),sum(j['reserved_calls'] for j in plan),'calls',flush=True)

if __name__=='__main__':main()
