import pathlib,json,subprocess,os,time,datetime,hashlib
D=pathlib.Path(__file__).resolve().parent.parent
def save(name,x):
 p=D/name;t=p.with_suffix('.tmp');t.write_text(json.dumps(x,indent=2)+'\n');t.replace(p)
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
calls=0;start=time.time()
for variant in ['original','prefetch','active_pool','combined']:
 save('state.json',{'status':'RUNNING','variant':variant,'completed_search_calls':calls,'cap':600000,'start':start})
 with (D/f'logs/{variant}.log').open('w') as log:
  p=subprocess.run(['taskset','-c','15',str(D/f'bin/diagnose.{variant}'),str(D/'config.json'),str(D/f'results/{variant}'),variant],env=env,stdout=log,stderr=subprocess.STDOUT,timeout=1800)
 if p.returncode:
  save('state.json',{'status':'FAILED','variant':variant,'returncode':p.returncode,'completed_search_calls':calls});raise SystemExit(p.returncode)
 c=json.loads((D/f'results/{variant}/complete.json').read_text());calls+=c['search_calls'];assert calls<=600000
 print('FINISHED',variant,'calls',calls,'elapsed',time.time()-start,flush=True)
check={}
for name,old in json.loads((D/'reviews/protected.json').read_text()).items():
 p=pathlib.Path(name);check[name]=p.stat().st_size==old['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==old['sha256']
assert all(check.values());save('reviews/protection_check.json',check)
save('state.json',{'status':'MEASUREMENTS_COMPLETE','search_calls':calls,'wall_seconds':time.time()-start,'completed_at':datetime.datetime.now().isoformat(),'protected_unchanged':True})
