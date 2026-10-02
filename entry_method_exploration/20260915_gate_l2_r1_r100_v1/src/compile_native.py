from common import *
import subprocess
flags=['c++','-I'+str(ROOT/'build/_deps/json-src/include'),'-std=c++17','-O3','-march=native','-fopenmp','-fPIC','-I'+str(ROOT),'-I'+str(ROOT/'faiss'),'-I'+str(RUN/'src')]
libs=[ROOT/'build/ACSG/libACSG.a',ROOT/'build/faiss/faiss/libfaiss.a',ROOT/'build/MRNN_Descent/libmrnndescent.a']
records=[]
def run(cmd):
 t=time.time();print('COMPILE',cmd,flush=True);subprocess.run(list(map(str,cmd)),check=True);records.append(dict(command=list(map(str,cmd)),seconds=time.time()-t))
obj=RUN/'bin/ACSG.original.o';run(flags+['-c',ROOT/'ACSG/ACSG.cpp','-o',obj])
for name in ['evaluate','labels','build_hnsw','build_nsg']:
 run(flags+[RUN/'src'/(name+'.cpp'),obj,*libs,'-lopenblas','-llapack','-lz','-lpthread','-ldl','-o',RUN/'bin'/name])
dump(RUN/'reviews/native_build.json',dict(status='PASS',builds=records,sources={str(p):sha(p) for p in [ROOT/'ACSG/ACSG.cpp',ROOT/'ACSG/ACSG.h',ROOT/'ACSG/IndexACSG.cpp',ROOT/'ACSG/IndexACSG.h',*libs]},binaries={p.name:sha(p) for p in (RUN/'bin').iterdir() if p.is_file()}))
