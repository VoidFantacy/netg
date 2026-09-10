import subprocess
import time
from common import ROOT, RUN, check_lock, dump, identity, read, sha

check_lock()
for record in read(RUN / 'reviews/protected_before.json'):
    if record['path'].endswith(('.cpp', '.h', '.hpp', '.a')):
        assert sha(record['path']) == record['sha256'], record['path']
output = RUN / 'bin/evaluate'
assert not output.exists(), 'refuse binary overwrite'
argv = ['c++', '-std=c++17', '-O3', '-march=native', '-fopenmp', '-fPIC', '-Wall', '-Wextra',
        '-I'+str(ROOT), '-I'+str(ROOT/'faiss'), '-I'+str(ROOT/'benches'),
        '-I'+str(ROOT/'build/_deps/json-src/include'), str(RUN/'src/evaluate.cpp'), str(ROOT/'ACSG/ACSG.cpp'),
        str(ROOT/'build/faiss/faiss/libfaiss.a'), str(ROOT/'build/ACSG/libACSG.a'),
        str(ROOT/'build/MRNN_Descent/libmrnndescent.a'), str(ROOT/'build/faiss/faiss/libfaiss.a'),
        '/usr/lib/x86_64-linux-gnu/libopenblas.so', '-lm', '-ldl', '-lpthread', '-o', str(output)]
t = time.monotonic()
with (RUN/'logs/build_evaluate.log').open('w') as log:
    rc = subprocess.call(argv, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
record = {'argv': argv, 'exit_code': rc, 'seconds': time.monotonic()-t,
          'sources': [identity(x) for x in sorted((RUN/'src').glob('*.cpp'))]}
if rc == 0:
    record['binary'] = identity(output)
dump(RUN/'bin/evaluate.build.json', record)
assert rc == 0, 'build failed; inspect retained log'
print('EVALUATOR_BUILT', record['seconds'], flush=True)
