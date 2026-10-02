import datetime,hashlib,json,os,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):
 assert not p.exists(),p
 p.write_text(json.dumps(v,indent=2)+'\n')
c=json.loads((R/'config.locked.json').read_text())
identity={str(p.relative_to(R)):sha(p) for p in sorted((R/'src').rglob('*')) if p.is_file()}
for p in [R/'config.locked.json',R/'protocol.md']+list((R/'models').rglob('roles.npz')):identity[str(p.relative_to(R))]=sha(p)
dump(R/'reviews/pre_run_frozen.json',{'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':identity})
cmd=['g++','-O3','-march=native','-std=c++17','-DNDEBUG','-pthread','-I/data/netg/ACSG/build/_deps/json-src/include',str(R/'src/observe.cpp'),'-o',str(R/'bin/observe')]
start=time.perf_counter()
with (R/'logs/build.log').open('w') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
dump(R/'reviews/build.json',{'argv':cmd,'seconds':time.perf_counter()-start,'binary_sha256':sha(R/'bin/observe')})
env=os.environ.copy()
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:env[k]='1'
jobs=[]
for ds in c['datasets']:
 cmd=['taskset','-c','15',str(R/'bin/observe'),str(R/'reviews'/f'{ds}.observe.json'),str(R/'results'/ds)]
 start=time.perf_counter()
 with (R/'logs'/f'{ds}.observe.log').open('w') as log:subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
 result=json.loads((R/'results'/ds/'complete.json').read_text());assert result['status']=='PASS'
 jobs.append({'dataset':ds,'argv':cmd,'seconds':time.perf_counter()-start,'result':result})
 print(ds,'PARITY_PASS',result['observed_states'],'states',flush=True)
dump(R/'reviews/observer_jobs.json',jobs)
for name,h in identity.items():assert sha(R/name)==h,name
for name,v in json.loads((R/'reviews/router_inputs_before.json').read_text()).items():assert sha(Path(name))==v['sha256'],name
dump(R/'reviews/observer_complete.json',{'status':'PASS','router_calls':sum(x['result']['router_calls'] for x in jobs),'new_nsg':0,'new_GT':0,'input_identity_pass':True})
