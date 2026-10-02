import pathlib,subprocess,os,time,datetime,json,hashlib
D=pathlib.Path(__file__).resolve().parent.parent
def check():
 for name in ['frozen.json','protected.json']:
  for p,h in json.loads((D/'reviews'/name).read_text()).items():assert hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()==h,p
def state(x):(D/'state.json').write_text(json.dumps(x,indent=2)+'\n')
check();env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1');start=time.time();calls=0
for mode in ['profile','probe']:
 state({'status':'DIAGNOSING','phase':mode,'started_at':datetime.datetime.fromtimestamp(start).isoformat(),'completed_search_calls':calls})
 with (D/'logs'/f'{mode}.log').open('w') as f:r=subprocess.run(['taskset','-c','15',str(D/'bin'/mode),str(D/'config.json'),str(D/'results'/mode)],env=env,stdout=f,stderr=subprocess.STDOUT,timeout=1800)
 if r.returncode:state({'status':'FAILED','phase':mode,'returncode':r.returncode});raise SystemExit(r.returncode)
 x=json.loads((D/'results'/mode/'complete.json').read_text());calls+=x['search_calls'];assert x['status']=='PASS' and calls<=100000;check();print('PASS',mode,calls,flush=True)
assert calls==80000
state({'status':'DIAGNOSIS_COMPLETE','search_calls':calls,'seconds':time.time()-start,'completed_at':datetime.datetime.now().isoformat()})
