from common import *
from archive import archive
assert read(R/'reviews/runtime_qualification_complete.json')['status']=='PASS_ALL_MODELS_AND_RUNTIME_BRANCHES'
records=[];started=time.perf_counter()
for ds in DS:
    archive(R/'storage/runtime_qualification'/ds)
    c=read(R/'configs'/f'{ds}.calibration.json');out=Path(c['output_dir'])
    assert not out.exists(),('preserve existing calibration output',out)
    argv=['taskset','-c','15',str(R/'storage/formal_benchmark'),'calibration',str(R/'configs'/f'{ds}.calibration.json')]
    t=time.perf_counter()
    with (R/'reviews'/f'{ds}.calibration.log').open('w') as log:
        p=subprocess.Popen(argv,cwd=REPO,stdout=log,stderr=subprocess.STDOUT)
        dump(R/'live_process.json',dict(stage='complete_wall_calibration',dataset=ds,pid=p.pid,argv=argv,started_unix=time.time()))
        code=p.wait()
    records.append(dict(dataset=ds,argv=argv,pid=p.pid,returncode=code,seconds=time.perf_counter()-t))
    dump(R/'reviews/calibration_progress.json',records);print(ds,'calibration',code,records[-1]['seconds'],flush=True)
    assert code==0,ds
    a=archive(out);print(ds,'archived_bytes',a['archive_bytes'],flush=True)
dump(R/'reviews/calibration_complete.json',dict(status='PASS_SEVEN_COMPLETE_WALL_CALIBRATIONS',records=records,seconds=time.perf_counter()-started))
