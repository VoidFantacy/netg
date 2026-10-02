import pathlib,json,hashlib,subprocess,time
R=pathlib.Path('/data/netg/ACSG');D=pathlib.Path(__file__).resolve().parent.parent
old=(D/'source_before/ACSG/ACSG.cpp').read_text();hdr=(D/'source_before/ACSG/ACSG.h').read_text()
(D/'src/legacy/ACSG.h').write_text(hdr.replace('namespace acsg','namespace acsg_legacy'))
(D/'src/legacy.cpp').write_text(old.replace('#include <ACSG/ACSG.h>','#include "legacy/ACSG.h"').replace('namespace acsg','namespace acsg_legacy'))
begin=old.index('    inline int insert_into_pool(Neighbor');end=old.index('\n    ACSG::ACSG(',begin)
(D/'src/legacy_pool.hpp').write_text('#pragma once\nusing acsg::Neighbor;\n'+old[begin:end].replace('insert_into_pool(', 'legacy_insert('))
flags=['c++','-std=c++17','-O3','-g','-march=native','-fopenmp','-fPIC','-I'+str(R/'build/_deps/json-src/include'),'-I'+str(R),'-I'+str(R/'faiss'),'-I'+str(D/'src')]
commands=[]
for src,name in [(D/'src/legacy.cpp','legacy'),(R/'ACSG/ACSG.cpp','optimized')]:
 cmd=flags+['-c',str(src),'-o',str(D/f'bin/{name}.o')];t=time.time();subprocess.run(cmd,check=True);commands.append({'command':cmd,'seconds':time.time()-t});print('BUILT',name,flush=True)
libs=[str(R/'build/ACSG/libACSG.a'),str(R/'build/faiss/faiss/libfaiss.a'),str(R/'build/MRNN_Descent/libmrnndescent.a')]
for name in ['regression','benchmark']:
 cmd=flags+[str(D/f'src/{name}.cpp'),str(D/'bin/legacy.o'),str(D/'bin/optimized.o'),*libs,'-lopenblas','-llapack','-lz','-lpthread','-ldl','-o',str(D/'bin'/name)];t=time.time();subprocess.run(cmd,check=True);commands.append({'command':cmd,'seconds':time.time()-t});print('BUILT',name,flush=True)
(D/'reviews/native_build.json').write_text(json.dumps({'commands':commands,'compiled_source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [R/'ACSG/ACSG.cpp',R/'ACSG/detail/CandidatePool.h',R/'ACSG/ACSG.h',D/'src/benchmark.cpp',D/'src/regression.cpp',D/'src/legacy.cpp']},'binaries':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (D/'bin').iterdir() if p.is_file()}},indent=2)+'\n')
