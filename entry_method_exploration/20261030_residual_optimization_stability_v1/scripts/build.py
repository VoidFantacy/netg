from common import *
import subprocess
argv=read(OLD/'reviews/build_receipt.json')['argv']
argv=[str(R/'src/benchmark.cpp') if x.endswith('/20261028_seven_dataset_scoring_v1/src/benchmark.cpp') else str(R/'storage/benchmark') if x.endswith('/20261028_seven_dataset_scoring_v1/storage/benchmark') else x for x in argv]
t=time.perf_counter();p=subprocess.run(argv,cwd=REPO,capture_output=True,text=True);(R/'reviews/build.log').write_text(p.stdout+p.stderr);dump(R/'reviews/build.json',dict(argv=argv,returncode=p.returncode,seconds=time.perf_counter()-t));assert p.returncode==0,p.stderr[-8000:]
print('E194_BUILD_PASS',flush=True)
