"""Independent complete GT identity, graph serialization and cost accounting audit."""
import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='1'
import json,hashlib,struct,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1];P=R.parent.parent;C=json.loads((P/'stages/e124_semantic_service_ridge_v1/config.locked.json').read_text());pre=json.loads((R/'reviews/preflight.json').read_text());done=json.loads((R/'reviews/rebuild_complete.json').read_text());router=json.loads((R/'reviews/router_complete.json').read_text());start=time.perf_counter()
assert done['status']=='GT_H_PROFILE_REPRODUCED_ROUTER_PENDING' and router['status']=='PASS'
def ident(p):return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def dump(p,x):assert not p.exists();p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
dump(R/'reviews/audit_frozen.json',{'files':{str(p):ident(p) for p in [Path(__file__),R/'reviews/rebuild_complete.json',R/'reviews/router_complete.json',R/'src/router.cpp']}})
def graph(p):
    b=p.read_bytes();off=0
    def take(fmt):
        nonlocal off
        z=struct.unpack_from('<'+fmt,b,off);off+=struct.calcsize('<'+fmt);return z
    # Original hnswlib native x86_64 serialization; semantic bytes exclude unused slots.
    offset0,maxel,n,size,labeloff,dataoff=take('QQQQQQ');maxlev,enter=take('iI');maxM,maxM0,M=take('QQQ');mult,efc=take('dQ');nodes=[]
    for i in range(n):
        s=off+i*size;count=struct.unpack_from('<H',b,s+offset0)[0];neighbors=struct.unpack_from('<'+'I'*count,b,s+offset0+4);label=struct.unpack_from('<Q',b,s+labeloff)[0];vec=b[s+dataoff:s+labeloff];nodes.append([label,vec,[neighbors]])
    off+=n*size
    for i in range(n):
        nb=take('I')[0];step=4+4*maxM;assert nb%step==0
        for j in range(nb//step):
            s=off+j*step;count=struct.unpack_from('<H',b,s)[0];nodes[i][2].append(struct.unpack_from('<'+'I'*count,b,s+4))
        off+=nb
    assert off==len(b)
    return (offset0,n,size,labeloff,dataoff,maxlev,enter,maxM,maxM0,M,mult,efc,nodes)
records={};total_rows=0;oldfiles=0
for ds,c in C['datasets'].items():
    rp=R/'results'/ds;record=done['datasets'][ds];r=json.loads((rp/'router/complete.json').read_text());dp=pre['datasets'][ds]
    assert (rp/'rebuilt_ids.i32').read_bytes()==Path(c['anchor']['ids']).read_bytes()
    assert (rp/'rebuilt_W.f32').read_bytes()==Path(c['anchor']['W']).read_bytes()
    for label,n,src in [('qgt5000',5000,dp['qgt_GT']),('profile20000',20000,c['fit_source']['gt_file'])]:
        new=np.fromfile(rp/f'{label}.ids.i64','<i8').reshape(n,100)
        if label=='qgt5000':
            old=np.fromfile(src,'<i4').reshape(n,101);assert (old[:,0]==100).all();old=old[:,1:]
        else:old=np.fromfile(src,'<i8').reshape(n,100)
        assert np.array_equal(old,new);assert (np.diff(np.sort(new,axis=1),axis=1)>0).all()
        dist=np.fromfile(rp/f'{label}.dist.f32','<f4').reshape(n,100);assert np.isfinite(dist).all() and (np.diff(dist,axis=1)<=0).all()
        t=record['GT'][label];assert t['exact_rank_rows']==n and abs(sum(t['batch_seconds'])-t['search_seconds'])<1e-8;total_rows+=n
    assert graph(Path(c['anchor']['graph']))==graph(rp/'router/router.hnsw')
    assert r['query_parity_pairs']==25000 and r['new_ANN_calls']==50000 and r['new_NSG_calls']==0
    gt=sum(v['search_seconds'] for v in record['GT'].values());kernel=record['base_load_and_flat_build_seconds']+gt+record['qgt_H_build_seconds']+record['target_assignment_and_profile_seconds']+r['router_build_seconds']
    records[ds]={'GT_search_seconds':gt,'base_load_flat_seconds':record['base_load_and_flat_build_seconds'],'H_select_seconds':record['qgt_H_build_seconds'],'profile_seconds':record['target_assignment_and_profile_seconds'],'router_build_seconds':r['router_build_seconds'],'nonoverlapping_core_stage_sum_seconds':kernel,'full_GT_H_profile_process_seconds':record['dataset_process_seconds'],'router_process_seconds_including_audit':router['jobs'][ds]['process_seconds'],'GT_fraction_of_core_stage_sum':gt/kernel,'GT_exact_rows':25000,'graph_semantics_independently_equal':True}
for name,key in [('reviews/rebuild_inputs.json','files'),('reviews/rebuild_frozen.json','files'),('reviews/router_frozen.json','files')]:
    for p,v in json.loads((R/name).read_text())[key].items():assert ident(Path(p))==v,p;oldfiles+=1
for p,v in json.loads((R/'reviews/rebuild_inputs.json').read_text())['bases_stat_only'].items():
    st=Path(p).stat();assert st.st_size==v['bytes'] and st.st_mtime_ns==v['mtime_ns']
assert total_rows==50000==done['GT_query_calls'] and done['faiss_threads']==8 and done['affinity']==list(range(8))
dump(R/'results/cost_summary.json',{'status':'CURRENT_GT10_REBUILT_WITH_GT_COST','datasets':records,'new_exact_GT_queries':50000,'new_ANN_calls':100000,'new_NSG_calls':0,'QPS_measured':False,'default_changed':False,'excluded':['embedding extraction','download','bottom NSG construction'],'timing_scope':'single run current cache state without cache flush; offline CPU0-7; router insertion serial; stage sum excludes audit and I/O; whole process includes them'})
dump(R/'reviews/independent_audit.json',{'status':'PASS','seconds':time.perf_counter()-start,'complete_GT_rows_checked':total_rows,'serialized_graphs_independently_decoded':2,'old_small_file_identity_checks':oldfiles,'large_bases_stat_checked':2,'new_searches':0,'independent_implementation_same_agent':True})
print('PASS',total_rows,flush=True)
