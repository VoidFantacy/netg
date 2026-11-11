from common import *
assert read(R/'reviews/calibration_complete.json')['status']=='PASS_SEVEN_COMPLETE_WALL_CALIBRATIONS'
assert read(R/'reviews/calibration_v2_complete.json')['status']=='PASS_SEVEN_MINIMAL_CAPTURE_WALL_CALIBRATIONS'
assert read(R/'reviews/single_seed_control_qualification.json')['status']=='PASS_SEVEN_SINGLE_SEED_CONTROLS'
for item in read(R/'reviews/build_formal.json')['source_files']:
    assert sha(item['path'])==item['sha256'],('formal binary source mismatch',item['path'])
point_rows=[];cost_proposals=[]
for ds in DS:
    cal=read(R/'storage/calibration_v2'/ds/'complete.json')['results']
    initial=read(R/'configs'/f'{ds}.calibration_v2.json')['points']
    points={(int(r['K']),int(r['L']),r['method']) for r in initial}
    for L in [32,64,80,96]:
        points.add((1,L,'GT10'));points.add((1,L,'OPT-B32'))
    for K in [1,100]:
        candidates=[r for r in cal if int(r['K'])==K and r['method'] not in ['GT10','OPT-B32']]
        for control in ['GT10','OPT-B32']:
            curve=sorted((1e6/float(r['qps']),int(r['L'])) for r in cal if int(r['K'])==K and r['method']==control)
            times,budgets=zip(*curve)
            for r in candidates:
                target=1e6/float(r['qps']);estimate=int(round(float(np.interp(target,times,budgets))))
                proposed=sorted(set(max(100,L) for L in [estimate-2,estimate,estimate+2,int(r['L'])+1]))
                for L in proposed:points.add((K,L,control))
                cost_proposals.append(dict(dataset=ds,K=K,method=r['method'],base_L=r['L'],control=control,
                    cal_target_us=target,estimated_L=estimate,proposed_L=';'.join(map(str,proposed)),
                    interpolation='time-sorted measured curve; proposals only, no Recall inference'))
        points.add((K,200,'ORACLE-C1'));points.add((K,200,'ORACLE-S1'))
        # Historical SQ positives include L400. Keep applicable strong residual controls visible.
        points.add((K,100,'REUSE-SQ'));points.add((K,400,'REUSE-SQ'))
        for L in [100,200,400]:
            points.add((K,L,'DIST1'));points.add((K,L,'DIST1-FULL'))
        points.add((K,200,'SHARED-CAPTURE'));points.add((K,200,'SHARED-CAPTURE-FULL'))
    for window in ['A','B']:
        c=read(R/'configs'/f'{ds}.{window}.json')
        c['points']=[dict(K=K,L=L,method=m) for K,L,m in sorted(points)]
        c['teacher_masks']=str(R/'storage/diagnosis'/ds/window/'teacher_masks.i32')
        dump(R/'configs'/f'{ds}.{window}.json',c)
        full=dict(c,q8_table=c['table'],window=window+'-full')
        full.pop('teacher_masks',None)
        dump(R/'configs'/f'{ds}.{window}.full_diagnosis.json',full)
        point_rows.extend(dict(dataset=ds,window=window,**p) for p in c['points'])
csvwrite(R/'analysis/frozen_formal_points.csv',point_rows)
csvwrite(R/'analysis/cost_control_proposals.csv',cost_proposals)
paths=[R/'protocol.md',R/'storage_format.md',R/'measurement_boundaries.md',R/'role_freeze.json',R/'feature_contract.json',
       R/'analysis/frozen_formal_points.csv',R/'analysis/cost_control_proposals.csv',R/'reviews/machine.json',R/'storage/formal_benchmark']
paths+=list((R/'src').glob('*.inc'))+[R/'src/benchmark.cpp']
paths += [R/'src/decision_audit.cpp',R/'reviews/decision_source_identity.json']
paths += [R/'scripts'/name for name in ['common.py','prepare.py','train.py','build.py',
          'prepare_matrix.py','freeze_formal.py','run_public.py','archive.py','run_calibration.py','run_calibration_v2.py','qualify_single_seed.py','decision_audit_all.py']]
paths+=list((R/'configs').glob('*.json'))
large_aux=[]
for ds in DS:
    c=read(R/'configs'/f'{ds}.A.json')
    paths+=list((R/'storage/models'/ds).glob('*.json'))
    paths += [Path(c['table']),Path(c['q8_table']),Path(c['router']['ids']),Path(c['router']['W']),Path(c['router']['graph'])]
    paths += [Path(c['meta_dir'])/f for f in ['indegree.u32','outdegree.u16','representatives.i32','complete.json']]
    backend_manifest=Path(c['models'])/'model.json';paths.append(backend_manifest)
    for role,path in read(backend_manifest)['files'].items():
        asset=Path(path);s=asset.stat()
        if s.st_size<=8*(1<<20):paths.append(asset)
        else:large_aux.append(dict(dataset=ds,role=role,path=str(asset),bytes=s.st_size,mtime_ns=s.st_mtime_ns,
            identity='inherited E191 frozen backend; source model manifest bound, current stat, not a fresh whole-file SHA'))
    for window in ['A','B']:
        c=read(R/'configs'/f'{ds}.{window}.json')
        paths += [Path(c[k]['path']) for k in ['queries','test_gt']]
argv=read(R/'reviews/build_formal.json')['argv']
paths += [Path(x) if Path(x).is_absolute() else REPO/x for x in argv if x.endswith(('.a','.o'))]
unique=sorted(set(paths));files=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in unique]
large=list(large_aux)
for ds in DS:
    c=read(R/'configs'/f'{ds}.A.json')
    for p in [Path(c['index']),Path(c['base']['path'])]:
        s=p.stat();large.append(dict(dataset=ds,path=str(p),bytes=s.st_size,mtime_ns=s.st_mtime_ns,
            identity='inherited sealed E195 source, current stat checked; no new full-container SHA'))
dump(R/'formal_freeze.json',dict(status='FROZEN_BEFORE_PUBLIC_DIAGNOSIS_AND_FORMAL_MATRIX',files=files,
    points=len(point_rows),batches=3*len(point_rows),cost_proposals=len(cost_proposals),large_inherited_inputs=large,
    explicit_diagnostic_masks_generated_after_this_freeze=True,public_windows_exposed=True,
    model_and_gate_selection_only_legal_cal=True,no_default_change=True,created_unix=time.time()))
s=read(R/'state.json');s.update(status='FROZEN_PUBLIC_DIAGNOSIS_AND_FORMAL_MATRIX_PENDING',formal_points=len(point_rows),formal_batches=3*len(point_rows));dump(R/'state.json',s)
print('FORMAL_FROZEN',len(point_rows),'points',3*len(point_rows),'batches',flush=True)
