from common import *
import subprocess
finite_deadline()
name='label'
cmd=['g++','-O3','-march=native','-std=c++17','-fopenmp',
     '-I'+str(ROOT),'-I'+str(ROOT/'faiss'),'-I'+str(ROOT/'build/_deps/json-src/single_include'),
     '-I'+str(RUN/'src/common'),str(RUN/'src'/f'{name}.cpp'),
     str(ROOT/'entry_method_exploration/20260916_nsg_search_optimization_v1/bin/libACSG.optimized.a'),
     str(ROOT/'build/MRNN_Descent/libmrnndescent.a'),str(ROOT/'build/faiss/faiss/libfaiss.a'),
     '-lopenblas','-lz','-o',str(RUN/'bin'/name)]
with (RUN/'logs'/f'build_{name}.log').open('w') as f:
    t=time.time();p=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
dump(RUN/'reviews'/f'build_{name}.json',dict(argv=cmd,exit_code=p.returncode,seconds=time.time()-t))
assert p.returncode==0,'inspect build log'
dump(RUN/'reviews/label_source_lock.json',dict(status='FROZEN',protocol=identity(RUN/'protocol.md'),
    lock=identity(RUN/'config.locked.json'),sources=[identity(p) for p in sorted((RUN/'src').rglob('*')) if p.is_file()],
    binary=identity(RUN/'bin/label'),libraries=[identity(Path(x)) for x in cmd if x.endswith('.a')]))
print('label binary built and sources frozen')
