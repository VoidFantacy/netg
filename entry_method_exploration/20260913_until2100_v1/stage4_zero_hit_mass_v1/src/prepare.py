"""Reuse E61 verified input namespaces and baseline cache, freeze zero-hit supervision."""
from shared import *
threads(); resources(); started=time.monotonic()
E61=C/'stage2_missing_targets_v1';E62=C/'stage3_missing_factorial_v1'
assert not (O/'reviews/prebuild_freeze.json').exists()
for f in ['inputs','models','results','reviews','logs','bin','source_before']:(O/f).mkdir(exist_ok=True)
for name in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md']:
    shutil.copy2(R/name,O/'source_before'/name)
shutil.copy2(R/'experiment_history/README.md',O/'source_before/history_README.md')
for name in ['state.json','handoff.md','candidate_inventory.json','next_stage_design.md']:
    shutil.copy2(C/name,O/'source_before'/name)
check(E61/'reviews/final_artifact_freeze.json');check(E62/'reviews/final_artifact_freeze.json')
shutil.copy2(E61/'bin/environment.so',O/'bin/environment.so')
protected=set(); records=[]
for ds in DS:
    folder=O/'inputs'/ds;folder.mkdir()
    source=E61/'inputs'/ds/'config.json';c=read(source);protected.add(source)
    baseline_path=E61/'inputs'/ds/'baseline.npz';b=dict(np.load(baseline_path));protected.add(baseline_path)
    gt=np.fromfile(c['gt_file'],np.int64).reshape(22048,100)
    h=ihits(b['ids'],gt);assert np.array_equal(h,b['hits'])
    rows=np.fromfile(c['row_ids'],np.int64);assert np.array_equal(rows,np.r_[np.arange(10000,30000),np.arange(2048)])
    zero=h[:20000]==0;n=int(zero.sum());assert n=={'webvid2_5m_light_v1':348,'yandex_t2i_official10M_ip_v1':311}[ds]
    selected=np.sort(np.random.default_rng(20260913).choice(20000,n,replace=False));sham=np.zeros(20000,bool);sham[selected]=True
    w=(1+zero.astype(float))*20000/(20000+n);ws=(1+sham.astype(float))*20000/(20000+n)
    assert abs(w.sum()-20000)<1e-8 and np.array_equal(np.sort(w),np.sort(ws))
    save(folder/'mass_supervision.npz',zero=zero,sham=sham,sham_rows=selected,weights=w,sham_weights=ws,source_rows=rows[:20000])
    shutil.copy2(baseline_path,folder/'baseline.npz')
    c.pop('lambda_value');c['weight_ratio']=2.;c['random_query_seed']=20260913;c['supervision_source']=str(baseline_path)
    dump(folder/'config.json',c)
    for k in ['P','raw_hubs','queries_file','gt_file','row_ids','hub_ids','parity_rows']:protected.add(Path(c[k]))
    records.append(dict(dataset=ds,zero_hit_queries=n,random_overlap_actual_zero=int((sham&zero).sum()),total_query_mass=float(w.sum()),
       namespace=c['namespace'],roles=c['roles'],history='All P-fit and cal/audit historically used. No unobserved or final-validation claim.',
       baseline_rows_independently_scored=22048,baseline_source=identity(baseline_path)))
dump(O/'reviews/input_audit.json',dict(status='PASS_ZERO_MASS_INPUTS',datasets=records,seconds=time.monotonic()-started,final_validation_access=False))
dump(O/'config.locked.json',dict(datasets=DS,models=LABELS,weight_ratio=2,random_query_seed=20260913,threads=1,query_cpu=15,
    per_dataset_NSG_reserved=45000,total_NSG_cap=90000,per_dataset_HNSW=66528,per_dataset_builds=3,
    candidate_selection='zero_mass2 only; cal net hits>0, failures nonincreasing, totalNDC<=baseline*1.01; sham excluded; audit descriptive',
    latest_launch=1789268100,query_stop=1789268700,session_safe_exit=1789269269,day_deadline=1789304400,final_validation_access=False))
# Current bytes of small dependencies; large immutable base/NSG retain the verified E61 SHA and live stat check.
large=[]
for x in read(E61/'reviews/prebuild_freeze.json')['files']:
    if x['bytes']>64*(1<<20):
        st=Path(x['path']).stat();assert st.st_size==x['bytes'] and st.st_mtime_ns==x['mtime_ns'];large.append(x)
protected.update(p for f in ['src','inputs','source_before'] for p in (O/f).rglob('*') if p.is_file())
protected.update([O/'protocol.md',O/'config.locked.json',O/'bin/environment.so',E61/'reviews/final_artifact_freeze.json',E62/'reviews/final_artifact_freeze.json'])
dump(O/'reviews/prebuild_freeze.json',dict(epoch=time.time(),files=[identity(p) for p in sorted(protected)]+large,
   large_identity_scope='SHA inherited from E61 frozen provenance, live size/mtime checked; no new full base/NSG hash read'))
state=read(C/'state.json');state.update(status='SESSION2_E63_PREPARED',stage='E63',day_goal_complete=False,native_pids=[],session_safe_exit_deadline=1789269269)
dump(C/'state.json',state);dump(O/'state.json',dict(status='PREPARED_ZERO_MASS',new_NSG=0,next_command='src/build.py'))
print('E63_PREPARE_PASS',time.monotonic()-started,flush=True)
