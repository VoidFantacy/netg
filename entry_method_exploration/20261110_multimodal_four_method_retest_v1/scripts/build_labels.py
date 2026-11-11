from pathlib import Path
import os,json,time,subprocess,hashlib
RUN=Path(__file__).resolve().parents[1];ROOT=RUN.parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
old=ROOT/'entry_method_exploration/20260915_gate_l2_r1_r100_v1/src'
libs=[Path('/root/acsg-e172-storage-v2/campaign/common/acsg_current.o'),ROOT/'build/ACSG/libACSG.a',ROOT/'build/MRNN_Descent/libmrnndescent.a',ROOT/'build/faiss/faiss/libfaiss.a']
target=RUN/'bin/labels';assert not target.exists()
cmd=['g++','-O3','-march=native','-std=c++17','-fopenmp',f'-I{ROOT}',f'-I{ROOT}/faiss',f'-I{old}',f'-I{ROOT}/build/_deps/json-src/single_include',str(RUN/'src/labels.cpp'),*map(str,libs),'-lopenblas','-llapack','-lz','-lpthread','-ldl','-o',str(target)]
t=time.monotonic()
with (RUN/'logs/build_labels.log').open('x') as f:
    p=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1'))
receipt={'command':cmd,'exit_code':p.returncode,'seconds':time.monotonic()-t,'sources':{str(q):sha(q) for q in [RUN/'src/labels.cpp',RUN/'src/observer.hpp',RUN/'src/native_common.hpp',*libs]},'binary_sha256':sha(target) if target.exists() else None}
(RUN/'reviews/build_labels.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:receipt[k] for k in ['exit_code','seconds']}),flush=True)
assert p.returncode==0
