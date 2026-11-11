from common import *
from archive import archive
assert read(R/'reviews/single_seed_control_qualification.json')['status']=='PASS_SEVEN_SINGLE_SEED_CONTROLS'
state=read(R/'state.json');state.update(status='RUNNING_MINIMAL_CAPTURE_WALL_CALIBRATION',pending_work=True);dump(R/'state.json',state)
records=[];started=time.perf_counter()
for ds in DS:
    c=read(R/'configs'/f'{ds}.calibration.json')
    points={(int(p['K']),int(p['L']),p['method']) for p in c['points']}
    for K in [1,100]:
        for L in [100,200,400]:
            points.add((K,L,'DIST1'));points.add((K,L,'DIST1-FULL'))
        points.add((K,200,'SHARED-CAPTURE'));points.add((K,200,'SHARED-CAPTURE-FULL'))
        points.add((K,200,'AUX384-FAST'));points.add((K,200,'AUX384-FAST-FULL'))
        points.add((K,100,'REUSE-SQ'));points.add((K,400,'REUSE-SQ'))
    c['points']=[dict(K=K,L=L,method=m) for K,L,m in sorted(points)]
    c['output_dir']=str(R/'storage/calibration_v2'/ds)
    config=R/'configs'/f'{ds}.calibration_v2.json';dump(config,c)
    assert not Path(c['output_dir']).exists()
    argv=['taskset','-c','15',str(R/'storage/formal_benchmark'),'calibration',str(config)]
    t=time.perf_counter()
    with (R/'reviews'/f'{ds}.calibration_v2.log').open('w') as log:
        p=subprocess.Popen(argv,cwd=REPO,stdout=log,stderr=subprocess.STDOUT)
        dump(R/'live_process.json',dict(stage='minimal_capture_complete_wall_calibration',dataset=ds,pid=p.pid,argv=argv,started_unix=time.time()))
        code=p.wait()
    records.append(dict(dataset=ds,pid=p.pid,argv=argv,returncode=code,seconds=time.perf_counter()-t))
    dump(R/'reviews/calibration_v2_progress.json',records);print(ds,'calibration_v2',code,records[-1]['seconds'],flush=True)
    assert code==0,ds
    native=read(Path(c['output_dir'])/'complete.json')['results']
    bykey={(int(p['K']),int(p['L']),p['method']):p for p in native}
    for K in [1,100]:
        for fast,original in [('AUX384-FAST','AUX384'),('AUX384-FAST-FULL','REF-DIST384')]:
            assert bykey[K,200,fast]['rounds'][0]['packet_sha256']==bykey[K,200,original]['rounds'][0]['packet_sha256']
    a=archive(c['output_dir']);print(ds,'archived',a['archive_bytes'],flush=True)
dump(R/'reviews/calibration_v2_complete.json',dict(status='PASS_SEVEN_MINIMAL_CAPTURE_WALL_CALIBRATIONS',
    records=records,seconds=time.perf_counter()-started,previous_calibration_preserved=True,
    model_or_threshold_changed=False,public_query_response_consumed=False))
state=read(R/'state.json');state.update(status='CALIBRATION_V2_COMPLETE_FORMAL_FREEZE_PENDING');dump(R/'state.json',state)
