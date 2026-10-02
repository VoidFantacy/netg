import pathlib,json,subprocess,os,time,hashlib
R=pathlib.Path('/data/netg/ACSG');D=pathlib.Path(__file__).resolve().parent.parent;records=[]
flags=['c++','-std=c++17','-O3','-g','-march=native','-fopenmp','-fPIC','-I'+str(R/'build/_deps/json-src/include'),'-I'+str(R),'-I'+str(R/'faiss'),'-I'+str(D/'src')]
libs=[str(R/'build/faiss/faiss/libfaiss.a'),str(R/'build/MRNN_Descent/libmrnndescent.a')];end=['-lopenblas','-llapack','-lz','-lpthread','-ldl']
def run(c):
 t=time.time();subprocess.run(c,check=True);records.append({'command':c,'seconds':time.time()-t})
with (D/'bin/IndexACSG.original.o').open('wb') as f:subprocess.run(['ar','p',str(R/'build/ACSG/libACSG.a'),'IndexACSG.cpp.o'],stdout=f,check=True)
run(['ar','rcs',str(D/'bin/libACSG.optimized.a'),str(D/'bin/IndexACSG.original.o'),str(D/'bin/optimized.o')])
run(flags+[str(D/'src/benchmark.cpp'),str(D/'bin/legacy.o'),str(D/'bin/libACSG.optimized.a'),*libs,*end,'-o',str(D/'bin/benchmark')])
san=flags+['-O1','-fsanitize=address,undefined','-fno-omit-frame-pointer']
run(san+['-c',str(R/'ACSG/ACSG.cpp'),'-o',str(D/'bin/optimized.sanitized.o')])
run(san+[str(D/'src/regression.cpp'),str(D/'bin/legacy.o'),str(D/'bin/optimized.sanitized.o'),str(R/'build/ACSG/libACSG.a'),*libs,*end,'-o',str(D/'bin/regression.sanitized')])
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',ASAN_OPTIONS='detect_leaks=1')
with (D/'logs/regression_sanitized.log').open('w') as f:subprocess.run(['taskset','-c','0',str(D/'bin/regression.sanitized'),str(D/'reviews/regression_sanitized.json')],env=env,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=300)
records.append({'sanitizer_status':'PASS'});(D/'reviews/checked_build.json').write_text(json.dumps(records,indent=2)+'\n')
files=[R/'ACSG/ACSG.cpp',R/'ACSG/ACSG.h',R/'ACSG/detail/CandidatePool.h',*sorted((D/'src').rglob('*.cpp')),*sorted((D/'src').rglob('*.hpp')),*sorted((D/'src').rglob('*.h')),D/'bin/benchmark',D/'bin/libACSG.optimized.a']
(D/'reviews/frozen_code.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},indent=2)+'\n');print('LIBRARY_AND_SANITIZER_PASS',flush=True)
