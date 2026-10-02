import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='1'
os.sched_setaffinity(0,{14})
import ast,hashlib,json,struct,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent;C=json.loads((R/'config.locked.json').read_text());REF=json.loads((R/'reviews/validation_references.json').read_text())
def ident(p):
    p=Path(p);return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def dump(p,v):
    with Path(p).open('x') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def main():
    start=time.perf_counter();done=json.loads((R/'reviews/run_complete.json').read_text());assert done['status']=='BUILT_PENDING_IDENTITY_AUDIT'
    decode_source=R.parent/'demand_qgt_full_build_v1/audit_v2.py';tree=ast.parse(decode_source.read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='decode_graph');scope={'Path':Path,'struct':struct}
    exec(compile(ast.Module(body=[node],type_ignores=[]),str(decode_source),'exec'),scope);decode=scope['decode_graph']
    dump(R/'reviews/audit_frozen.json',{'unix':time.time(),'source':ident(__file__),'decoder_source':ident(decode_source),'references':ident(R/'reviews/validation_references.json')})
    records={};gt_count=ann_count=0
    for ds,c in C['datasets'].items():
        p=Path(c['output']);ref=REF[ds];d=c['dimension'];n=c['fit_n'];old=Path(ref['full_gt_build']);demand=Path(ref['demand_build'])
        exact=json.loads((p/'exact_complete.json').read_text());profile=json.loads((p/'profile_complete.json').read_text());router=json.loads((p/'router_complete.json').read_text())
        assert (p/'fit20000.ids.i64').read_bytes()==Path(ref['fit_gt']).read_bytes()
        assert (p/'fit20000.ids.i64').read_bytes()==(old/'profile20000.ids.i64').read_bytes()
        assert (p/'fit20000.dist.f32').read_bytes()==(old/'profile20000.dist.f32').read_bytes()
        for name in ['ids.i32','qgt_demand.rows.i32','qgt_demand.ids.i64','qgt_demand.dist.f32']:
            assert (p/name).read_bytes()==(demand/name).read_bytes(),name
        for name in ['qgt_trace.json','qgt_generation.json']:assert json.loads((p/name).read_text())==json.loads((demand/name).read_text())
        oldplan=np.load(demand/'cluster_plan.npz');newplan=np.load(p/'cluster_plan.npz')
        for key in oldplan.files:assert np.array_equal(oldplan[key],newplan[key])
        qrows=np.fromfile(p/'qgt_demand.rows.i32','<i4');gen=json.loads((p/'qgt_generation.json').read_text());trace=json.loads((p/'qgt_trace.json').read_text());generated=[row for b in gen for row in b['rows']]
        assert np.array_equal(np.unique(generated),qrows) and len(generated)==exact['GT']['qgt_demand']['computed_queries']
        assert len(set(x['row'] for x in trace))==exact['GT']['qgt_demand']['logical_consumed_rows'] and len(generated)-len(qrows)==exact['GT']['qgt_demand']['overlap_checks']
        assert np.array_equal(np.fromfile(p/'fit_rows.i32','<i4'),np.arange(n))
        assert exact['new_GT']==n+len(generated) and exact['affinity']==list(range(8)) and exact['faiss_threads']==8
        assert exact['GT']['fit20000']['n']==n and profile['exact_labels_consumed']==n and profile['approx_labels_consumed']==0 and router['graph_builds']==1
        assert (p/'ids.i32').read_bytes()==Path(ref['model']['ids']).read_bytes() and (p/'W.f32').read_bytes()==Path(ref['model']['W']).read_bytes()
        assert decode(p/'router.hnsw')==decode(ref['model']['graph'])
        manifest=json.loads(Path(ref['profile_manifest']).read_text());assert profile['assignment_sha256']==manifest['assignments_sha256'] and profile['temperature']==manifest['temperature']
        base=np.memmap(c['base'],'<f4',mode='r').reshape(c['base_n'],d+1)[:,1:];fit=np.fromfile(c['fit_queries'],'<f4').reshape(n,d);gt=np.fromfile(p/'fit20000.ids.i64','<i8').reshape(n,100);dist=np.fromfile(p/'fit20000.dist.f32','<f4').reshape(n,100)
        maxerr=0.
        for row in np.linspace(0,n-1,16,dtype=int):
            direct=np.array(base[gt[row]],dtype='f8')@fit[row].astype('f8');maxerr=max(maxerr,float(np.abs(direct-dist[row]).max()));np.testing.assert_allclose(direct,dist[row],rtol=1e-5,atol=3e-5)
        if c['soft']:
            h=base[np.fromfile(p/'ids.i32','<i4')].copy();h/=np.linalg.norm(h,axis=1,keepdims=True)
            target=base[gt[:,0]].copy();target/=np.linalg.norm(target,axis=1,keepdims=True);gaps=[]
            for lo in range(0,n,4096):
                scores=np.sort(target[lo:lo+4096]@h.T,axis=1);gaps.append((scores[:,-1]-scores[:,-2]).astype('f8'))
            gaps=np.concatenate(gaps);assert gaps.tobytes()==(p/'temperature_gaps.f64').read_bytes();assert max(float(np.median(gaps)),1e-4)==profile['temperature']
        else:assert profile['temperature'] is None
        ra=json.loads((p/'router_audit.json').read_text());assert ra['status']=='PASS' and ra['query_pairs']==256 and ra['new_ANN_calls']==512 and ra['threads']==1
        timing=done['datasets'][ds];assert timing['complete_build_wall_seconds']>=timing['job_seconds_sum'];assert abs(timing['job_seconds_sum']-sum(done['jobs'][x]['seconds'] for x in timing['jobs']))<1e-8
        for rec in exact['GT'].values():
            times=rec['batch_seconds'] if 'batch_seconds' in rec else [b['seconds'] for b in rec['batches']]
            assert abs(sum(times)-rec['search_seconds'])<1e-8
        gt_count+=exact['new_GT'];ann_count+=ra['new_ANN_calls']
        records[ds]={'complete_build_wall_seconds':timing['complete_build_wall_seconds'],'job_wall_seconds':{x.rsplit('_',1)[-1]:done['jobs'][x]['seconds'] for x in timing['jobs']},
            'base_load_flat_seconds':exact['base_load_flat_build_seconds'],'qgt_search_seconds':exact['GT']['qgt_demand']['search_seconds'],
            'fit20000_search_seconds':exact['GT']['fit20000']['search_seconds'],'qgt_computed_queries':len(generated),'qgt_unique_queries':len(qrows),
            'qgt_fallback_batches':exact['GT']['qgt_demand']['fallback_batches'],'temperature':profile['temperature'],'temperature_seconds':profile['temperature_seconds'],
            'profile_internal_seconds':profile['seconds'],'router_build_seconds':router['build_seconds'],'exact_resident_threads':exact['threads'],
            'GT_distance_bits_restored':True,'QGT_matches_audited_demand_builder':True,'H_W_graph_restored':True,'GT_return_score_max_abs_error':maxerr}
    identities=0
    for file in ['preparation.json','run_frozen.json']:
        for p,v in json.loads((R/'reviews'/file).read_text())['inputs'].items():assert ident(p)==v;identities+=1
    for p,v in json.loads((R/'reviews/preparation.json').read_text())['large_stat_only'].items():
        st=Path(p).stat();assert st.st_size==v['bytes'] and st.st_mtime_ns==v['mtime_ns']
    assert ann_count==1024 and gt_count<=C['max_exact_queries']
    dump(R/'results/cost_summary.json',{'status':'DEFAULT_DEMAND_FULL_BUILD_REPRODUCED','datasets':records,'new_exact_GT':gt_count,'new_NSG':0,'new_audit_ANN':ann_count,
        'new_profiles':2,'new_graphs':2,'new_qgt_kmeans_fits':2,'default_changed':False,'new_online_performance':False,
        'scope':'single complete no-label-input default rebuild using demand QGT; current OS cache; includes loading and output; excludes historic public bottom-index, embeddings, tool preparation and post-audit'})
    dump(R/'reviews/independent_audit.json',{'status':'PASS','seconds':time.perf_counter()-start,'identities':identities,'exact_GT_rows':gt_count,
        'fit20000_ID_and_distance_bit_identity':True,'demand_QGT_bit_identity':2,'default_W_bit_identity':2,'graph_semantic_identity':2,'native_query_pairs':512,'default_changed':False})
    print('DEFAULT AUDIT PASS',records,flush=True)
if __name__=='__main__':main()
