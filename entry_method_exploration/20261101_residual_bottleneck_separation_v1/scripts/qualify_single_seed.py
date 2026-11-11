from common import *
from archive import archive
import shutil
assert read(R/'reviews/calibration_complete.json')['status']=='PASS_SEVEN_COMPLETE_WALL_CALIBRATIONS'
state=read(R/'state.json');state.update(status='QUALIFYING_MINIMAL_CAPTURE_AND_MATCHED_CONTROLS',labels_and_models_complete=True,pending_work=True);dump(R/'state.json',state)
old=R/'storage/formal_benchmark';preserved=R/'storage/calibration_benchmark'
assert not preserved.exists();shutil.copy2(old,preserved)
dump(R/'reviews/calibration_binary_identity.json',dict(path=str(preserved),sha256=sha(preserved),
    original_path=str(old),source_snapshot=str(R/'reviews/calibration_source_snapshot.json'),
    source_binary_unchanged_during_all_calibrations=True))
subprocess.run([str(REPO/'.venv_cpu/bin/python'),str(R/'scripts/build.py'),'formal'],cwd=REPO,check=True)
records=[];parities=0;started=time.perf_counter()
minimal_root=R/'storage/minimal_capture_qualification';(minimal_root/'reviews').mkdir(parents=True)
for ds in DS:
    base=read(R/'configs'/f'{ds}.labels.json');base['experiment_root']=str(minimal_root)
    minimal_config=R/'configs'/f'{ds}.minimal_qualification.json';dump(minimal_config,base)
    argv=['taskset','-c','15',str(R/'storage/formal_benchmark'),'qualification',str(minimal_config)]
    t=time.perf_counter()
    with (R/'reviews'/f'{ds}.minimal_capture_qualification.log').open('w') as log:
        p=subprocess.Popen(argv,cwd=REPO,stdout=log,stderr=subprocess.STDOUT)
        dump(R/'live_process.json',dict(dataset=ds,stage='minimal_capture_qualification',pid=p.pid,argv=argv,started_unix=time.time()))
        code=p.wait()
    records.append(dict(dataset=ds,stage='minimal_capture',pid=p.pid,argv=argv,returncode=code,seconds=time.perf_counter()-t))
    assert code==0,(ds,'minimal capture')
    c=read(R/'configs'/f'{ds}.runtime_qualification.json')
    points={(int(p['K']),int(p['L']),p['method']) for p in c['points']}
    for K in [1,100]:
        for L in [100,200,400]:
            points.add((K,L,'DIST1'));points.add((K,L,'DIST1-FULL'))
        points.add((K,200,'SHARED-CAPTURE'));points.add((K,200,'SHARED-CAPTURE-FULL'))
        points.add((K,100,'REUSE-SQ'));points.add((K,400,'REUSE-SQ'))
    c['points']=[dict(K=K,L=L,method=m) for K,L,m in sorted(points)]
    c['output_dir']=str(R/'storage/single_qualification'/ds)
    config=R/'configs'/f'{ds}.single_qualification.json';dump(config,c)
    argv=['taskset','-c','15',str(R/'storage/formal_benchmark'),'formal',str(config)]
    t=time.perf_counter()
    with (R/'reviews'/f'{ds}.single_qualification.log').open('w') as log:
        p=subprocess.Popen(argv,cwd=REPO,stdout=log,stderr=subprocess.STDOUT)
        dump(R/'live_process.json',dict(dataset=ds,stage='single_seed_control_qualification',pid=p.pid,argv=argv,started_unix=time.time()))
        code=p.wait()
    records.append(dict(dataset=ds,stage='all_runtime_branches',pid=p.pid,argv=argv,returncode=code,seconds=time.perf_counter()-t))
    dump(R/'reviews/single_seed_control_progress.json',records);print(ds,code,records[-1]['seconds'],flush=True)
    assert code==0,ds
    older=read(R/'storage/runtime_qualification'/ds/'complete.json')['results']
    older={(int(x['K']),int(x['L']),x['method']):x for x in older}
    actual=read(Path(c['output_dir'])/'complete.json')['results']
    for x in actual:
        key=int(x['K']),int(x['L']),x['method']
        if key in older:
            assert x['rounds'][0]['packet_sha256']==older[key]['rounds'][0]['packet_sha256'];parities+=1
    archive(c['output_dir'])
dump(R/'reviews/single_seed_control_qualification.json',dict(status='PASS_SEVEN_SINGLE_SEED_CONTROLS',
    records=records,previous_binary_packet_parities=parities,seconds=time.perf_counter()-started,
    source_semantics_change='Remove unused Trace statistics; add singleton and capture-only controls; prior method packets unchanged'))
state=read(R/'state.json');state.update(status='MINIMAL_CAPTURE_QUALIFIED_CALIBRATION_V2_PENDING');dump(R/'state.json',state)
