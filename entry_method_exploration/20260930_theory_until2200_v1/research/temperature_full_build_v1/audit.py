import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='8'
os.sched_setaffinity(0,range(8))
import hashlib,json,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent;C=json.loads((R/'config.locked.json').read_text());DS='webvid2_5m_light_v1'
def ident(p):
    p=Path(p);return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def dump(p,x):
    with Path(p).open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def unit(x):return x/np.maximum(np.linalg.norm(x,axis=1,keepdims=True),1e-12)
def main():
    started=time.perf_counter();c=C['datasets'][DS];out=Path(c['output']);ref=json.loads((R/'reviews/validation_references.json').read_text())[DS]
    old=Path(ref['demand_build']);done=json.loads((R/'reviews/run_complete.json').read_text());assert done['status']=='BUILT_PENDING_IDENTITY_AUDIT'
    dump(R/'reviews/audit_frozen.json',{'source':ident(__file__),'run_complete':ident(R/'reviews/run_complete.json'),'references':ident(R/'reviews/validation_references.json')})
    for name in ['selected_rows.i32','selected2048.ids.i64','selected2048.dist.f32','qgt_demand.rows.i32','qgt_demand.ids.i64','qgt_demand.dist.f32','ids.i32']:
        assert (out/name).read_bytes()==(old/name).read_bytes(),name
    assert (out/'labels/ids.i32').read_bytes()==Path(ref['approx_ids']).read_bytes()
    assert (out/'labels/distances.f32').read_bytes()==Path(ref['approx_distances']).read_bytes()
    teacher=json.loads((out/'labels/complete.json').read_text());exact=json.loads((out/'exact_complete.json').read_text())
    assert teacher['new_NSG_calls']==20032 and teacher['n']==20000 and teacher['threads']==1 and teacher['GT10_route_calls']==0 and teacher['GT10_files_read']==0
    assert exact['new_GT']==2863 and exact['GT']['qgt_demand']['fallback_batches']==0
    assert done['jobs'][DS+'_teacher']['single_thread_samples']>0
    n,d=20000,c['dimension'];base=np.memmap(c['base'],'<f4',mode='r').reshape(c['base_n'],d+1)[:,1:];h=unit(np.array(base[np.fromfile(out/'ids.i32','<i4')],dtype='f4'))
    q=unit(np.fromfile(c['fit_queries'],'<f4').reshape(n,d)).astype('f8');rows=np.fromfile(out/'selected_rows.i32','<i4')
    ap=np.fromfile(out/'labels/ids.i32','<i4').reshape(n,100);gt=np.fromfile(out/'selected2048.ids.i64','<i8').reshape(len(rows),100)
    targets=ap.astype('i8');targets[rows]=gt;records={};diagnostic=np.load(R.parent/'temperature_cdf_v1/results/gaps_and_estimates.npz')
    for mode,j in [(C['primary'],2),(C['control'],1)]:
        dest=out/mode;p=json.loads((dest/'profile_complete.json').read_text());allg=np.fromfile(dest/'proxy_gaps.f64','<f8');trueg=np.fromfile(dest/'sample_true_gaps.f64','<f8')
        assert np.array_equal(allg,diagnostic['approx']) and np.array_equal(trueg,diagnostic['exact'][rows])
        # Independent full-sort gap reconstruction from the actual new labels, same block dimensions.
        for label,ids,expected in [('all',ap[:,0],allg),('sample',gt[:,0],trueg)]:
            z=unit(np.array(base[ids],dtype='f4'))
            for lo in range(0,len(ids),4096):
                sorted_scores=np.sort(z[lo:lo+4096]@h.T,axis=1);gap=(sorted_scores[:,-1]-sorted_scores[:,-2]).astype('f8');assert np.array_equal(gap,expected[lo:lo+4096])
        if mode==C['primary']:
            # Independent signed events rather than searchsorted ECDFs.
            m=len(rows);grid,inv=np.unique(np.r_[allg,trueg,allg[rows]],return_inverse=True);mass=np.zeros(len(grid),dtype='i8')
            np.add.at(mass,inv[:n],m);np.add.at(mass,inv[n:n+m],n);np.add.at(mass,inv[n+m:],-n);nums=np.cumsum(mass);temp=max(float(grid[np.argmin(np.abs(2*nums-n*m))]),1e-4)
        else:temp=max(float(np.median(allg)),1e-4)
        assert temp==p['temperature']==diagnostic['temperatures'][0,j]
        # Builder overwrites separate approximate/pilot assignments; this path assembles mixed IDs first.
        weights=np.zeros((n,len(h)))
        for rank in range(10):
            z=unit(np.array(base[targets[:,rank]],dtype='f4'))
            for lo in range(0,n,4096):
                hi=min(lo+4096,n);score=(z[lo:hi]@h.T).astype('f8');score-=score.max(1,keepdims=True);score/=temp;v=np.exp(score);v/=v.sum(1,keepdims=True);weights[lo:hi]+=v/10
        assert hashlib.sha256(weights.tobytes()).hexdigest()==p['assignment_sha256']
        v=h.astype('f8')+weights.T@q;w=unit(v).astype('f4');assert w.tobytes()==(dest/'W.f32').read_bytes()
        assert v.tobytes()==(dest/'v.f64').read_bytes();router=json.loads((dest/'router_complete.json').read_text());assert router['graph_builds']==1 and router['all_label_vector_checks']==815
        records[mode]={'temperature':temp,'profile_sha256':p['profile_sha256'],'assignment_sha256':p['assignment_sha256'],'W_bit_independent_recovery':True,
            'minimum_resultant_norm':p['minimum_resultant_norm'],'graph_all_labels_vectors':router['all_label_vector_checks']}
    native=json.loads((out/'router_audit.json').read_text());assert native['status']=='PASS' and native['new_ANN_calls']==1024 and native['threads']==1
    assert set(native['methods'])==set(records)
    for method,x in native['methods'].items():assert x['query_pairs']==256 and x['status']=='PASS'
    identities=0
    for fn in ['preparation.json','run_frozen.json']:
        for path,expected in json.loads((R/'reviews'/fn).read_text())['inputs'].items():assert ident(path)==expected;identities+=1
    for path,x in json.loads((R/'reviews/preparation.json').read_text())['large_stat_only'].items():
        s=Path(path).stat();assert s.st_size==x['bytes'] and s.st_mtime_ns==x['mtime_ns']
    timing=done['datasets'][DS];assert timing['complete_build_wall_seconds']>=timing['job_seconds_sum']
    result={'status':'FROZEN_TEMPERATURE_MODELS_AND_PRIMARY_FULL_COST_REPRODUCED','dataset':DS,'methods':records,'primary':C['primary'],
        'primary_complete_build_wall_seconds':timing['complete_build_wall_seconds'],'control_incremental_wall_seconds':timing['control_incremental_wall_seconds'],
        'job_wall_seconds':{k:v['seconds'] for k,v in done['jobs'].items()},'new_exact_GT':2863,'new_teacher_NSG':20032,'new_audit_ANN':1024,
        'new_profiles':2,'new_graphs':2,'new_online_performance':False,'default_changed':False,
        'scope':'primary from query/base/index only; includes loads and I/O, excludes public bottom index original construction, embedding, tool preparation and audits; control only incremental'}
    dump(R/'results/summary.json',result);dump(R/'reviews/independent_audit.json',{'status':'PASS','seconds':time.perf_counter()-started,'identities':identities,
        'new_models_independent_W_bit_recovery':2,'temperature_independent_recovery':2,'all_20000_approx_GT_bit_recovery':True,'query_route_plain_count_pairs':512})
    print('AUDIT PASS',result,flush=True)
if __name__=='__main__':main()
