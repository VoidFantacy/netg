import pathlib,subprocess,time,os,json,hashlib,datetime
D=pathlib.Path(__file__).resolve().parent.parent;R=D.parent.parent;E=D.parent/'20260916_nsg_search_optimization_v1';P=D.parent/'20260916_residual_cost_research_v1'
def read(p):return json.loads(p.read_text())
def save(p,x):
 t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(x,indent=2)+'\n');t.replace(p)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024**2),b''):h.update(b)
 return h.hexdigest()
assert not (D/'results/benchmark').exists()
assert all(read(D/'reviews'/n)['status']=='PASS' for n in ['regression.json','regression_sanitized.json'])
c=read(D/'config.json');start=time.time();save(D/'state.json',{'status':'FREEZING','pid':os.getpid(),'started_at':datetime.datetime.now().astimezone().isoformat()})
paths=[p for folder in ['src','bin'] for p in (D/folder).rglob('*') if p.is_file()]+[D/'config.json',D/'protocol.md']
frozen={str(p):sha(p) for p in paths};save(D/'reviews/frozen.json',frozen)
protected=read(P/'reviews/protected.json')
for p in [P/'report.md',P/'complete.json',P/'results/summary.json',R/'build/faiss/faiss/libfaiss.a',R/'faiss/faiss/impl/NSG.cpp',R/'faiss/faiss/IndexNSG.cpp']:
 protected[str(p)]=sha(p)
for p,h in protected.items():assert sha(pathlib.Path(p))==h,p
save(D/'reviews/protected.json',protected)
assets={c[k] for k in ['index','base','queries','gt','hnsw_topology','hnsw_complete','router']};assets.update(c['soft'][k] for k in ['ids','W'])
identities={p:{'bytes':pathlib.Path(p).stat().st_size,'sha256':sha(pathlib.Path(p))} for p in sorted(assets)};save(D/'reviews/assets.json',identities)
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
query_start=time.time()
with (D/'logs/benchmark.log').open('w') as log:
 proc=subprocess.Popen(['taskset','-c','15',str(D/'bin/compare'),str(D/'config.json'),str(D/'results/benchmark')],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 save(D/'state.json',{'status':'MEASURING','pid':os.getpid(),'child_pid':proc.pid,'started_at':datetime.datetime.fromtimestamp(start).astimezone().isoformat(),'measurement_started_at':datetime.datetime.now().astimezone().isoformat()})
 try:code=proc.wait(timeout=7200)
 except subprocess.TimeoutExpired:
  proc.terminate();proc.wait();save(D/'state.json',{'status':'FAILED_TIMEOUT','pid':os.getpid(),'child_pid':proc.pid});raise
if code:
 save(D/'state.json',{'status':'FAILED','returncode':code,'seconds':time.time()-start});raise SystemExit(code)
done=read(D/'results/benchmark/complete.json');assert done['status']=='PASS' and done['search_calls']==2000000 and done['wall_rounds']==120
save(D/'state.json',{'status':'VERIFYING_IDENTITIES','search_calls':done['search_calls'],'pid':os.getpid()})
for manifest in [frozen,protected]:
 for p,h in manifest.items():assert sha(pathlib.Path(p))==h,p
for p,v in identities.items():assert pathlib.Path(p).stat().st_size==v['bytes'] and sha(pathlib.Path(p))==v['sha256'],p
save(D/'reviews/post_run_identity.json',{'status':'PASS','code_files':len(frozen),'protected_files':len(protected),'assets':len(identities)})
save(D/'state.json',{'status':'MEASUREMENTS_COMPLETE','search_calls':done['search_calls'],'wall_rounds':done['wall_rounds'],'seconds_total':time.time()-start,'measurement_and_verification_seconds':time.time()-query_start,'completed_at':datetime.datetime.now().astimezone().isoformat()})
print(json.dumps(read(D/'state.json')),flush=True)
