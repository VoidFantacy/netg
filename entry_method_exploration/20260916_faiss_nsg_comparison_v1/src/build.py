import pathlib,subprocess,time,json
D=pathlib.Path(__file__).resolve().parent.parent;R=D.parent.parent;E=D.parent/'20260916_nsg_search_optimization_v1'
flags=['c++','-std=c++17','-O3','-g','-march=native','-fopenmp','-fPIC','-I'+str(R/'build/_deps/json-src/include'),'-I'+str(D/'src'),'-I'+str(D/'src/common'),'-I'+str(R),'-I'+str(R/'faiss')]
libs=[str(E/'bin/libACSG.optimized.a'),str(R/'build/faiss/faiss/libfaiss.a'),str(R/'build/MRNN_Descent/libmrnndescent.a'),'-lopenblas','-llapack','-lz','-lpthread','-ldl']
commands=[flags+[str(D/'src/regression.cpp'),*libs,'-o',str(D/'bin/regression')],flags+[str(D/'src/compare.cpp'),*libs,'-o',str(D/'bin/compare')],flags+['-O1','-fsanitize=address,undefined','-fno-omit-frame-pointer',str(D/'src/regression.cpp'),*libs,'-o',str(D/'bin/regression_sanitized')]]
records=[]
for cmd in commands:
 t=time.time();subprocess.run(cmd,check=True);records.append({'command':cmd,'seconds':time.time()-t});print('BUILT',cmd[-1],flush=True)
(D/'reviews/build.json').write_text(json.dumps(records,indent=2)+'\n')
