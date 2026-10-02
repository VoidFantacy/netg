from common import *

assert read(O/'state.json')['status']=='PREFLIGHT_COMPLETE_TRAINING_PENDING'
env=os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='8',OPENBLAS_NUM_THREADS='8',MKL_NUM_THREADS='8')
with (O/'logs/training.log').open('x') as log:
    proc=subprocess.Popen([str(R/'.venv_cpu/bin/python'),str(O/'src/train.py')],stdout=log,stderr=subprocess.STDOUT,env=env)
    start=time.monotonic()
    while proc.poll() is None:
        if time.monotonic()-start>600:
            proc.terminate();proc.wait(timeout=3)
            raise RuntimeError('600 second external training wall limit; no restart allowed')
        assert shutil.disk_usage(O).free>=10*(1<<30)
        status=Path('/proc')/str(proc.pid)/'status'
        if status.exists():
            for line in status.read_text().splitlines():
                if line.startswith('VmRSS:'):assert int(line.split()[1])<40*(1<<20)
        time.sleep(.5)
    assert proc.returncode==0,proc.returncode
dump(O/'logs/training_process.json',dict(status='PASS',exit_code=proc.returncode,wall_seconds=time.monotonic()-start,hard_seconds=600,pid=proc.pid))
print('TRAINING_PROCESS_PASS',flush=True)
