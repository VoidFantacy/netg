import pathlib,json,subprocess,os,time
D=pathlib.Path(__file__).resolve().parent.parent;R=D.parent.parent
s=json.loads((D/'state.json').read_text());assert s['status']=='MEASUREMENTS_COMPLETE'
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
flags=['c++','-std=c++17','-O2','-march=native','-fopenmp','-fPIC','-I'+str(R/'build/_deps/json-src/include'),'-I'+str(R),'-I'+str(R/'faiss'),'-I'+str(D/'src')]
commands=[]
# All compilation occurs after the primary benchmark process has exited.
for v in ['prefetch','active_pool','combined']:
 cmd=flags+[str(D/'src/check_counts.cpp'),str(D/f'bin/ACSG.{v}.o'),str(R/'build/ACSG/libACSG.a'),str(R/'build/faiss/faiss/libfaiss.a'),str(R/'build/MRNN_Descent/libmrnndescent.a'),'-lopenblas','-llapack','-lz','-lpthread','-ldl','-o',str(D/f'bin/counts.{v}')];commands.append(cmd)
 with (D/f'logs/build_counts.{v}.log').open('w') as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True,env=env)
(D/'reviews/counts_build.json').write_text(json.dumps(commands,indent=2)+'\n')
for v in ['prefetch','active_pool','combined']:
 with (D/f'logs/counts.{v}.log').open('w') as f:subprocess.run(['taskset','-c','15',str(D/f'bin/counts.{v}'),str(D/'config.json'),str(D/f'results/counts.{v}')],env=env,stdout=f,stderr=subprocess.STDOUT,check=False,timeout=1800)
 c=json.loads((D/f'results/counts.{v}/measurement_done.json').read_text());s['search_calls']+=c['search_calls'];assert s['search_calls']<=600000
 s.setdefault('count_checks',{})[v]='PASS' if (D/f'results/counts.{v}/complete.json').exists() else 'FAIL'
 (D/'state.json').write_text(json.dumps(s,indent=2)+'\n');print('COUNTS',v,s['count_checks'][v],flush=True)
subprocess.run([str(R/'.venv_cpu/bin/python'),str(D/'src/run_matched_control.py')],check=True,env=env)
