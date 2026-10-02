import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='1'
os.sched_setaffinity(0,range(8))
import ast,hashlib,json,struct,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent;C=json.loads((R/'config.locked.json').read_text())
REF=json.loads((R/'reviews/validation_references.json').read_text())
def ident(p):
    p=Path(p);return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def dump(p,v):
    with Path(p).open('x') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def decode_graph(p):
    raw=Path(p).read_bytes();off=0
    def read(fmt):
        nonlocal off
        fmt='<'+fmt;z=struct.unpack_from(fmt,raw,off);off+=struct.calcsize(fmt);return z
    offset0,maxel,n,size,labeloff,dataoff=read('QQQQQQ');maxlev,enter=read('iI');maxM,maxM0,M=read('QQQ');mult,efc=read('dQ');nodes=[]
    for i in range(n):
        s=off+i*size;count=struct.unpack_from('<H',raw,s+offset0)[0];edges=struct.unpack_from('<'+'I'*count,raw,s+offset0+4)
        label=struct.unpack_from('<Q',raw,s+labeloff)[0];nodes.append([label,raw[s+dataoff:s+labeloff],[edges]])
    off+=n*size
    for i in range(n):
        nb=read('I')[0];step=4+4*maxM;assert nb%step==0
        for j in range(nb//step):
            s=off+j*step;count=struct.unpack_from('<H',raw,s)[0];nodes[i][2].append(struct.unpack_from('<'+'I'*count,raw,s+4))
        off+=nb
    assert off==len(raw)
    return offset0,n,size,labeloff,dataoff,maxlev,enter,maxM,maxM0,M,mult,efc,nodes
def main():
    start=time.perf_counter();done=json.loads((R/'reviews/run_complete.json').read_text());assert done['status']=='BUILT_PENDING_IDENTITY_AUDIT';records={}
    dump(R/'reviews/audit_frozen.json',{'source':ident(__file__),'router_source':ident(R/'audit_router.cpp'),'cost_run':ident(R/'reviews/run_complete.json'),'references':ident(R/'reviews/validation_references.json')})
    totalgt=totalteacher=totalann=0
    for ds,c in C['datasets'].items():
        p=Path(c['output']);ref=REF[ds];rows=np.fromfile(p/'selected_rows.i32','<i4');rest=np.fromfile(p/'approx_rows.i32','<i4');n,d=c['fit_n'],c['dimension']
        assert np.array_equal(rows,np.random.default_rng(c['pilot_seed']).permutation(n)[:2048]);assert rows.tobytes()==Path(ref['selected_rows']).read_bytes()
        assert np.array_equal(np.sort(np.r_[rows,rest]),np.arange(n))
        fit=np.fromfile(c['fit_queries'],'<f4').reshape(n,d);assert (p/'approx_queries.f32').read_bytes()==np.ascontiguousarray(fit[rest]).tobytes()
        oldq=np.fromfile(ref['qgt_gt'],'<i4').reshape(5000,101);assert (oldq[:,0]==100).all()
        oldselected=np.fromfile(ref['selected_gt'],'<i8').reshape(2048,100)
        qgt=np.fromfile(c['qgt_queries'],'<f4').reshape(5000,d+1)[:,1:];base=np.memmap(c['base'],'<f4',mode='r').reshape(c['base_n'],d+1)[:,1:]
        exact=json.loads((p/'exact_complete.json').read_text());maxerr=0.
        for label,truth,queries in [('qgt5000',oldq[:,1:],qgt),('selected2048',oldselected,fit[rows])]:
            ids=np.fromfile(p/f'{label}.ids.i64','<i8').reshape(len(queries),100);dist=np.fromfile(p/f'{label}.dist.f32','<f4').reshape(len(queries),100)
            assert np.array_equal(ids,truth);assert (np.diff(np.sort(ids,axis=1),axis=1)>0).all() and (np.diff(dist,axis=1)<=0).all()
            for i in np.linspace(0,len(queries)-1,16,dtype=int):
                calc=np.array(base[ids[i]],dtype='f8')@queries[i].astype('f8');maxerr=max(maxerr,float(np.max(np.abs(calc-dist[i]))));np.testing.assert_allclose(calc,dist[i],rtol=1e-5,atol=3e-5)
            assert abs(sum(exact['GT'][label]['batch_seconds'])-exact['GT'][label]['search_seconds'])<1e-8;totalgt+=len(queries)
        approx=np.fromfile(p/'labels/ids.i32','<i4').reshape(len(rest),100);apdist=np.fromfile(p/'labels/distances.f32','<u4').reshape(len(rest),100)
        assert np.array_equal(approx,np.fromfile(ref['approx_ids'],'<i4').reshape(n,100)[rest])
        assert np.array_equal(apdist,np.fromfile(ref['approx_distances'],'<u4').reshape(n,100)[rest])
        assert (p/'ids.i32').read_bytes()==Path(ref['model']['ids']).read_bytes()
        assert (p/'W.f32').read_bytes()==Path(ref['model']['W']).read_bytes(),'same frozen candidate W required'
        assert decode_graph(p/'router.hnsw')==decode_graph(ref['model']['graph'])
        teacher=json.loads((p/'labels/complete.json').read_text());profile=json.loads((p/'profile_complete.json').read_text());router=json.loads((p/'router_complete.json').read_text())
        ra=json.loads((p/'router_audit.json').read_text());assert ra['status']=='PASS' and ra['query_pairs']==256 and ra['new_ANN_calls']==512
        assert teacher['n']==17952 and teacher['new_NSG_calls']==17984 and teacher['GT10_files_read']==0 and teacher['threads']==1
        assert teacher['GT10_route_calls']==0 and exact['new_GT']==7048 and exact['affinity']==list(range(8)) and exact['faiss_threads']==8
        assert profile['exact_labels_consumed']==2048 and profile['approx_labels_consumed']==17952 and router['graph_builds']==1
        if c['soft']:
            h=base[np.fromfile(p/'ids.i32','<i4')].copy();h/=np.linalg.norm(h,axis=1,keepdims=True)
            target=base[oldselected[:,0]].copy();target/=np.linalg.norm(target,axis=1,keepdims=True)
            scores=np.sort(target@h.T,axis=1);temp=max(float(np.median((scores[:,-1]-scores[:,-2]).astype('f8'))),1e-4)
            assert temp==profile['temperature']
        else:assert profile['temperature'] is None
        timing=done['datasets'][ds];assert abs(timing['job_seconds_sum']-sum(done['jobs'][x]['seconds'] for x in timing['jobs']))<1e-8
        assert timing['complete_build_wall_seconds']>=timing['job_seconds_sum']
        totalteacher+=teacher['new_NSG_calls'];totalann+=ra['new_ANN_calls']
        records[ds]={'complete_build_wall_seconds':timing['complete_build_wall_seconds'],'job_wall_seconds':{x.rsplit('_',1)[-1]:done['jobs'][x]['seconds'] for x in timing['jobs']},
            'exact_GT_search_seconds':sum(x['search_seconds'] for x in exact['GT'].values()),'qgt_search_seconds':exact['GT']['qgt5000']['search_seconds'],
            'selected_search_seconds':exact['GT']['selected2048']['search_seconds'],'base_load_flat_seconds':exact['base_load_flat_build_seconds'],
            'H_select_seconds':exact['qgt_H_seconds'],'teacher_label_loop_seconds':teacher['label_loop_seconds'],'profile_process_internal_seconds':profile['seconds'],
            'router_build_seconds':router['build_seconds'],'temperature':profile['temperature'],'all_labels_H_W_graph_restored':True,'GT_score_max_error':maxerr,
            'exact_resident_threads':exact['threads'],'single_teacher_samples':done['jobs'][ds+'_teacher']['single_thread_samples']}
    identities=0
    for file in ['preparation.json','run_frozen.json']:
        for path,value in json.loads((R/'reviews'/file).read_text())['inputs'].items():assert ident(path)==value;identities+=1
    for path,v in json.loads((R/'reviews/preparation.json').read_text())['large_stat_only'].items():
        s=Path(path).stat();assert s.st_size==v['bytes'] and s.st_mtime_ns==v['mtime_ns']
    assert totalgt==14096 and totalteacher==35968 and totalann==1024
    dump(R/'results/cost_summary.json',{'status':'FROZEN_HYBRID_FULL_BUILD_REPRODUCED','datasets':records,'new_exact_GT':totalgt,'new_teacher_NSG':totalteacher,
        'new_audit_ANN':totalann,'new_profiles':2,'new_graphs':2,'default_changed':False,'new_online_performance':False,
        'scope':'single measured rebuild from no labels; current OS cache; includes loading and output; excludes public bottom-index original construction, embedding/download, tool preparation and post-build audits'})
    dump(R/'reviews/independent_audit.json',{'status':'PASS','seconds':time.perf_counter()-start,'identities':identities,'exact_GT_rows':totalgt,
        'approximate_label_rows':35904,'candidate_W_bit_identity':2,'graph_semantic_identity':2,'native_route_query_pairs':512,'default_changed':False})
    print('AUDIT PASS',records,flush=True)
if __name__=='__main__':main()
