#!/usr/bin/env python3
import hashlib,json,os,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REPO=Path('/data/netg/ACSG')
OLD=Path('/root/acsg-e172-storage-v2/campaign')
cmd=['g++','-O3','-march=native','-std=c++17','-fopenmp','-rdynamic',
     '-I'+str(REPO),'-I'+str(REPO/'benches'),'-I'+str(REPO/'faiss'),
     '-I'+str(REPO/'build/_deps/json-src/single_include'),
     str(ROOT/'src/benchmark_v2.cpp'),str(OLD/'common/acsg_current.o'),
     str(REPO/'build/ACSG/libACSG.a'),str(REPO/'build/MRNN_Descent/libmrnndescent.a'),
     str(REPO/'build/faiss/faiss/libfaiss.a'),'-lopenblas','-lz','-ldl',
     '-o',str(ROOT/'bin/benchmark_v2')]
env=os.environ.copy()
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:env[k]='1'
t=time.monotonic()
p=subprocess.run(['taskset','-c','14']+cmd,env=env,capture_output=True,text=True)
(ROOT/'src/build_v2.log').write_text(p.stdout+p.stderr)
record={'argv':cmd,'build_cpu':14,'exit_code':p.returncode,'seconds':time.monotonic()-t,
        'source_sha256':{str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in [ROOT/'src/benchmark_v2.cpp',ROOT/'src/native.hpp',ROOT/'src/runtime.hpp',OLD/'common/acsg_current.o']},
        'runtime_started':False}
if p.returncode==0:record['binary_sha256']=hashlib.sha256((ROOT/'bin/benchmark_v2').read_bytes()).hexdigest()
(ROOT/'src/build_v2.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
raise SystemExit(p.returncode)
