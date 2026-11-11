from common import *
stages=[('run_calibration_v2.py',R/'reviews/calibration_v2_complete.json'),
        ('freeze_formal.py',R/'formal_freeze.json'),
        ('run_public.py',R/'formal_complete.json'),
        ('decision_audit_all.py',R/'analysis/decision_audit.json'),
        ('analyze.py',R/'analysis/analysis_receipt.json'),
        ('audit_stdlib.py',R/'analysis/stdlib_audit.json'),
        ('costs.py',R/'analysis/cost_ledger.json'),
        ('plot.py',R/'analysis/figures/plot_receipt.json')]
records=[]
for script,completion in stages:
    if completion.exists():
        print('COMPLETED_STAGE_EXISTS',script,flush=True)
        continue
    argv=[str(REPO/'.venv_cpu/bin/python'),str(R/'scripts'/script)]
    t=time.perf_counter();p=subprocess.Popen(argv,cwd=REPO)
    dump(R/'pipeline_process.json',dict(stage=script,pid=p.pid,argv=argv,started_unix=time.time()))
    code=p.wait();records.append(dict(stage=script,pid=p.pid,returncode=code,seconds=time.perf_counter()-t))
    dump(R/'reviews/pipeline_progress.json',records)
    assert code==0,script
dump(R/'reviews/pipeline_complete.json',dict(status='PASS_FROZEN_EXPERIMENT_AND_NUMERICAL_ANALYSIS',
    records=records,human_report_and_final_delivery_validation_pending=True))
