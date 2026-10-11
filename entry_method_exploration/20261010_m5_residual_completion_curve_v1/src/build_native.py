"""Build new native E176 runner only after FIT closes and source review passes."""
from pathlib import Path
import hashlib,json,os,subprocess,time
ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parents[1]
HEADERS=['native.hpp','runtime.hpp','region.hpp','optimized.hpp','residual.hpp','benchmark.cpp']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 os.sched_setaffinity(0,{14})
 fit=json.loads((ROOT/'fit_state.json').read_text())
 assert fit['status']=='FIT_COMPLETE_ALL_MODELS_FROZEN' and fit['active'] is None
 review=json.loads((ROOT/'reviews/benchmark_source_review.json').read_text())
 assert review['status'].startswith('PASS')
 sources={str(ROOT/'src'/name):sha(ROOT/'src'/name) for name in HEADERS}
 for p,h in sources.items():assert review['source_sha256_at_review'][p]==h
 target=ROOT/'bin/benchmark';receipt=ROOT/'reviews/build.json'
 assert not target.exists() and not receipt.exists()
 prior=json.loads((ROOT/'reviews/fit_build.json').read_text())
 argv=[str(x).replace(str(ROOT/'src/fit.cpp'),str(ROOT/'src/benchmark.cpp')).replace(str(ROOT/'bin/fit'),str(target)) for x in prior['argv']]
 assert str(ROOT/'src/benchmark.cpp') in argv and argv[-1]==str(target)
 env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',OMP_DYNAMIC='FALSE')
 started=time.monotonic();log=ROOT/'logs/benchmark.build.log'
 with log.open('x') as f:run=subprocess.run(argv,cwd=REPO,env=env,stdout=f,stderr=subprocess.STDOUT)
 record={'status':'PASS_E176_NATIVE_BUILD' if run.returncode==0 else 'FAILED_E176_NATIVE_BUILD_PRESERVED',
  'argv':argv,'exit_code':run.returncode,'elapsed_seconds':time.monotonic()-started,'source_sha256':sources,
  'binary':str(target),'binary_sha256':sha(target) if target.exists() else None,'log':str(log),
  'scope':'engineering compile only; no ANN/FIT or public result read','cpu':14}
 receipt.write_text(json.dumps(record,indent=2)+'\n')
 assert run.returncode==0 and all(sha(p)==h for p,h in sources.items())
 print(json.dumps({'status':record['status'],'seconds':record['elapsed_seconds']}))
if __name__=='__main__':main()
