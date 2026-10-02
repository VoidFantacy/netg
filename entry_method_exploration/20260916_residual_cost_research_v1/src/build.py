import pathlib,subprocess,json,hashlib,time
D=pathlib.Path(__file__).resolve().parent.parent;R=D.parent.parent;E=D.parent/'20260916_nsg_search_optimization_v1'
flags=['c++','-std=c++17','-O3','-g','-march=native','-fopenmp','-fPIC','-I'+str(R/'build/_deps/json-src/include'),'-I'+str(D/'src'),'-I'+str(R),'-I'+str(R/'faiss')]
libs=[str(E/'bin/libACSG.optimized.a'),str(R/'build/faiss/faiss/libfaiss.a'),str(R/'build/MRNN_Descent/libmrnndescent.a'),'-lopenblas','-llapack','-lz','-lpthread','-ldl']
commands=[flags+['-I'+str(D/'src/common'),'-no-pie',str(D/'src/profile.cpp'),*libs,'-o',str(D/'bin/profile')],
          ['c++','-I'+str(D/'src/probe_include'),*flags[1:],'-I'+str(D/'src/probe_common'),'-c',str(D/'src/ACSG.probe.cpp'),'-o',str(D/'bin/ACSG.probe.o')],
          flags+['-I'+str(D/'src/probe_common'),'-no-pie',str(D/'src/probe.cpp'),str(D/'bin/ACSG.probe.o'),*libs,'-o',str(D/'bin/probe')]]
logs=[]
for cmd in commands:
 t=time.time();subprocess.run(cmd,check=True);logs.append({'command':cmd,'seconds':time.time()-t});print('BUILT',cmd[-1],flush=True)
(D/'reviews/build.json').write_text(json.dumps(logs,indent=2)+'\n')
ps=[p for folder in ['src','bin'] for p in (D/folder).rglob('*') if p.is_file()]+[D/'config.json',D/'protocol.md']
(D/'reviews/frozen.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in ps},indent=2)+'\n')
