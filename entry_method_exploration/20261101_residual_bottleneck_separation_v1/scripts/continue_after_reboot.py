from common import *
started=time.perf_counter()
if not (R/'formal_complete.json').exists():
    script=R/'scripts/run_reboot_recovery.py';argv=[str(REPO/'.venv_cpu/bin/python'),str(script)]
    p=subprocess.Popen(argv,cwd=REPO)
    dump(R/'pipeline_process.json',dict(stage='run_reboot_recovery.py',pid=p.pid,argv=argv,started_unix=time.time()))
    assert p.wait()==0,'recovery stopped: inspect native log and checkpoint before retry'
p=subprocess.run([str(REPO/'.venv_cpu/bin/python'),str(R/'scripts/continue_experiment.py')],cwd=REPO)
assert p.returncode==0
print('POST_REBOOT_NUMERICAL_PIPELINE_COMPLETE',time.perf_counter()-started,flush=True)
