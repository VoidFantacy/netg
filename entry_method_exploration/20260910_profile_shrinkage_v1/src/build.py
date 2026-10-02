import subprocess,time
from common import ROOT,RUN,check_lock,read,sha,identity,dump
check_lock()
for r in read(RUN/'reviews/protected_before.json'):
    if r['path'].endswith(('.cpp','.h','.hpp','.a')):assert sha(r['path'])==r['sha256'],r['path']
output=RUN/'bin/evaluate';assert not output.exists()
argv=['c++','-std=c++17','-O3','-march=native','-fopenmp','-fPIC','-Wall','-Wextra',
      '-I'+str(ROOT),'-I'+str(ROOT/'faiss'),'-I'+str(ROOT/'benches'),'-I'+str(ROOT/'build/_deps/json-src/include'),
      str(RUN/'src/evaluate.cpp'),str(ROOT/'ACSG/ACSG.cpp'),str(ROOT/'build/faiss/faiss/libfaiss.a'),
      str(ROOT/'build/ACSG/libACSG.a'),str(ROOT/'build/MRNN_Descent/libmrnndescent.a'),
      str(ROOT/'build/faiss/faiss/libfaiss.a'),'/usr/lib/x86_64-linux-gnu/libopenblas.so','-lm','-ldl','-lpthread','-o',str(output)]
start=time.monotonic()
with (RUN/'logs/build.log').open('w') as log:rc=subprocess.call(argv,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
record={'argv':argv,'exit_code':rc,'seconds':time.monotonic()-start,
        'sources':[identity(p) for p in sorted((RUN/'src').iterdir()) if p.suffix in ['.cpp','.hpp']]}
if rc==0:record['binary']=identity(output)
dump(RUN/'bin/evaluate.build.json',record)
assert rc==0,'compiler failed; retained build.log'
print('BUILD_PASS',round(record['seconds'],2),flush=True)
