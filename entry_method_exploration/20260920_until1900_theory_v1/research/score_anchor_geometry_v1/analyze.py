import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='1'
os.sched_setaffinity(0,{15})
from pathlib import Path
import json,hashlib,time,csv,shutil,resource
import numpy as np
TB=Path(__file__).resolve().parents[1];E104=TB.parent/'20260920_query_representation_pilot_v1';E105=TB.parent/'20260920_wfree_frozen_replication_v1'
R=TB/'research/score_anchor_geometry_v1';started=time.time()
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def ident(p):p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def write(p,rows):
    with Path(p).open('x') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
assert not R.exists();R.mkdir();shutil.copy2(__file__,R/'analyze.py');shutil.copy2(TB/'research/score_anchor_geometry_protocol.md',R/'protocol.md')
cells=[];sources=[E104/'results/training_runs.json',E104/'src/train.py',E104/'config.locked.json']
for ds in read(E104/'config.locked.json')['datasets']:
    model_path=E104/'models'/ds/'WFree/model.json';m=read(model_path);sources.append(model_path)
    paths={role:read(E104/'inputs'/ds/role/'config.json')['queries'] for role in ['fit','cal']}
    paths['exposed_E105']=str(E105/'inputs'/ds/'queries.f32');sources.extend(Path(p) for p in paths.values())
    lab=E104/'labels'/ds/'fit_labels'
    cell=dict(dataset=ds,d=m['dim'],H=m['h'],P=m['P'],W=m['W'],queries=paths,
              candidates=str(lab/'candidates.i32'),teacher_mask=str(lab/'teacher_mask.u8'))
    sources.extend(Path(cell[k]) for k in ['P','W','candidates','teacher_mask']);cells.append(cell)
source_ids=[ident(p) for p in dict.fromkeys(sources)]
dump(R/'config.locked.json',dict(created_unix=time.time(),cells=cells,source_files=source_ids,
    source=ident(R/'analyze.py'),protocol=ident(R/'protocol.md'),cpu=15,threads=1,
    matrix_positive_threshold='10*d*float64_eps*largest_eigenvalue',fit_monitor_rtol=1e-4,fit_monitor_atol=1e-10,
    historical_data_already_exposed=True,NSG_calls=0,new_training=0))
summary=[];support_summary=[];hub_rows=[];query_rows=[];eigen_rows=[];linear_score_coordinates=0
runs=read(E104/'results/training_runs.json')
for c in cells:
    d,H=c['d'],c['H'];P=np.fromfile(c['P'],'<f4').reshape(H,d).astype('f8');W=np.fromfile(c['W'],'<f4').reshape(H,d).astype('f8');delta=W-P
    mask=np.fromfile(c['teacher_mask'],'u1').reshape(2048,56);can=np.fromfile(c['candidates'],'<i4').reshape(2048,8)
    assert np.all(np.diff(np.sort(can,axis=1),axis=1)>0) and can.min()>=0 and can.max()<H
    active=mask.sum(axis=1)<56;counts=np.bincount(can.ravel(),minlength=H);acounts=np.bincount(can[active].ravel(),minlength=H)
    for h in range(H):hub_rows.append(dict(dataset=c['dataset'],hub_slot=h,C8_queries=int(counts[h]),
        nonconstant_loss_C8_queries=int(acounts[h]),supervision_rank_upper_bound=min(d,int(acounts[h])),parameter_dimension=d))
    support_summary.append(dict(dataset=c['dataset'],H=H,d=d,fit_n=2048,nonconstant_teacher_queries=int(active.sum()),
        C8_support_median=float(np.median(counts)),nonconstant_support_median=float(np.median(acounts)),
        nonconstant_support_min=int(acounts.min()),nonconstant_support_max=int(acounts.max()),
        zero_potential_teacher_support_hubs=int((acounts==0).sum()),potential_teacher_rank_below_d_hubs=int((acounts<d).sum())))
    matrices={};drifts={};fit_eigen=None;fit_vectors=None
    for role,path in c['queries'].items():
        qraw=np.fromfile(path,'<f4').reshape(-1,d).astype('f8');n=len(qraw);assert n in [2048,512,4096]
        norms=np.linalg.norm(qraw,axis=1,keepdims=True);assert np.all(norms>0)
        # Match the stored training normalization before taking float64 moments.
        q=(qraw/norms).astype('f4').astype('f8');C=q.T@q/n;matrices[role]=C
        residual=q@delta.T;per_query=(residual*residual).mean(axis=1);direct=float(per_query.mean());trace=float(np.sum((delta@C)*delta)/H)
        assert abs(direct-trace)<=1e-10*max(direct,1e-12)
        drifts[role]=direct;linear_score_coordinates+=n*H
        for i,z in enumerate(per_query):query_rows.append(dict(dataset=c['dataset'],source=role,query=i,mean_squared_score_drift=float(z)))
        if role=='fit':
            fit_eigen,fit_vectors=np.linalg.eigh(C);threshold=10*d*np.finfo('f8').eps*fit_eigen[-1]
            positive=bool(fit_eigen[0]>threshold)
            old=[r for r in runs if r['dataset']==c['dataset'] and r['family']=='WFree'][0]['final']['score_drift']
            assert np.isclose(direct,old,rtol=1e-4,atol=1e-10),(c['dataset'],direct,old)
            eigen_rows.append(dict(dataset=c['dataset'],min_eigenvalue=float(fit_eigen[0]),max_eigenvalue=float(fit_eigen[-1]),
                positive_threshold=float(threshold),numerically_positive_definite=positive,
                condition_number=float(fit_eigen[-1]/fit_eigen[0]) if positive else None,
                fit_drift_original_float32_monitor=old,fit_drift_reference_float64=direct))
        worst=None
        if positive:
            whitener=fit_vectors/np.sqrt(fit_eigen)[None,:]
            B=whitener.T@C@whitener;worst=float(np.linalg.eigvalsh((B+B.T)/2)[-1])
            assert direct/drifts['fit']<=worst*(1+1e-9)
        summary.append(dict(dataset=c['dataset'],source=role,n=n,H=H,d=d,
            score_drift=direct,score_drift_over_fit=direct/drifts['fit'],worst_direction_covariance_ratio=worst,
            direct_trace_abs_difference=abs(direct-trace),per_query_drift_median=float(np.median(per_query)),
            per_query_drift_p95=float(np.quantile(per_query,.95)),parameter_delta_Frobenius=float(np.linalg.norm(delta))))
    assert time.time()-started<30
write(R/'summary.csv',summary);write(R/'hub_support.csv',hub_rows);write(R/'support_summary.csv',support_summary);write(R/'query_score_drift.csv',query_rows);dump(R/'fit_spectrum.json',eigen_rows)
for x in source_ids:assert ident(x['path'])==x
assert time.time()-started<30
dump(R/'complete.json',dict(status='PASS',seconds=time.time()-started,source_files_checked=len(source_ids),
    matrix_trace_parity=True,original_fit_score_anchor_restored=True,linear_score_coordinates=linear_score_coordinates,
    new_model_score_residual_calculations=True,NSG_calls=0,ANN_calls=0,new_GT=0,new_graphs=0,new_training=0,
    maxrss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    outputs=[ident(R/p) for p in ['summary.csv','hub_support.csv','support_summary.csv','query_score_drift.csv','fit_spectrum.json']],
    source=ident(R/'analyze.py'),default_changed=False))
print(json.dumps(dict(summary=summary,support=support_summary,fit_spectrum=eigen_rows,complete=read(R/'complete.json')),indent=2))
