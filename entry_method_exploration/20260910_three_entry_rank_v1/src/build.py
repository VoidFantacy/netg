#!/usr/bin/env python3
import subprocess
import sys
import time
from common import ROOT, RUN, dump, identity, read, sha

for record in read(RUN / 'reviews/protected_before.json'):
    if record['path'].endswith(('.cpp', '.h', '.a')):
        assert sha(record['path']) == record['sha256'], record['path']
for name in sys.argv[1:] or ['label_triples', 'evaluate']:
    output = RUN / 'bin' / name
    assert not output.exists(), 'refuse binary overwrite'
    cmd = ['c++', '-std=c++17', '-O3', '-march=native', '-fopenmp', '-fPIC', '-Wall', '-Wextra',
           '-I'+str(ROOT), '-I'+str(ROOT/'faiss'), '-I'+str(ROOT/'benches'),
           '-I'+str(ROOT/'build/_deps/json-src/include'), str(RUN/'src'/f'{name}.cpp'),
           str(ROOT/'ACSG/ACSG.cpp'), str(ROOT/'build/faiss/faiss/libfaiss.a'),
           str(ROOT/'build/ACSG/libACSG.a'), str(ROOT/'build/MRNN_Descent/libmrnndescent.a'),
           str(ROOT/'build/faiss/faiss/libfaiss.a'), '/usr/lib/x86_64-linux-gnu/libopenblas.so',
           '-lm', '-ldl', '-lpthread', '-o', str(output)]
    sources = [identity(p) for p in sorted((RUN/'src').glob('*.cpp'))]
    t = time.monotonic()
    with (RUN/'logs'/f'build_{name}.log').open('w') as log:
        rc = subprocess.call(cmd, stdout=log, stderr=subprocess.STDOUT, cwd=ROOT)
    manifest = {'argv': cmd, 'exit_code': rc, 'seconds': time.monotonic()-t, 'sources': sources}
    if rc == 0:
        manifest['binary'] = identity(output)
    dump(RUN/'bin'/f'{name}.build.json', manifest)
    assert rc == 0, f'build failed: {name}'
    print(name, 'BUILT', flush=True)
