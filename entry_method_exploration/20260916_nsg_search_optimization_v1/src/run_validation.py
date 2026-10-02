import pathlib,json,hashlib,subprocess,os,time,datetime,shutil
R=pathlib.Path('/data/netg/ACSG');D=pathlib.Path(__file__).resolve().parent.parent;E=R/'entry_method_exploration/20260915_gate_l2_r1_r100_v1'
def dump(name,x):
 p=D/name;t=p.with_suffix('.tmp');t.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');t.replace(p)
def check_code():
 for name,h in json.loads((D/'reviews/frozen_code.json').read_text()).items():assert hashlib.sha256(pathlib.Path(name).read_bytes()).hexdigest()==h,name
for name in ['regression','regression_sanitized']:assert json.loads((D/f'reviews/{name}.json').read_text())['status']=='PASS'
check_code()
items=['webvid2_5m_light_v1','gist1m_l2_v1','deep10m_l2_v1','sift10m_bigann_l2_v1','yandex_t2i_official10M_ip_v1']
configs=[]
for dataset in items:
 source=E/f'inputs/{dataset}/eval_k100.json';c=json.loads(source.read_text());k1=json.loads((source.parent/'eval_k1.json').read_text());performance=dataset.startswith('webvid')
 c={k:c[k] for k in ['dataset','metric_id','threads','n','index','base','queries','gt','methods','hnsw_complete','hnsw_topology']}
 c.update(performance=performance,reference_results=str(E/f'results/{dataset}'),source_eval_config=str(source),points=[{'K':1,'L':96},{'K':100,'L':100},{'K':1,'L':800 if performance else 1250},{'K':100,'L':1250}])
 for point in c['points']:
  ec=json.loads((source.parent/f'eval_k{point["K"]}.json').read_text());assert point['L'] in ec['L'];assert ec['queries']==c['queries'] and ec['n']==c['n']
  for m in c['methods']:
   if m['name']=='HNSW' and not performance:continue
   p=pathlib.Path(c['reference_results'])/f'k{point["K"]}'/f'{m["name"]}_L{point["L"]}'/'complete.json';assert json.loads(p.read_text())['status']=='PASS'
 dump(f'configs/{dataset}.json',c);configs.append(D/f'configs/{dataset}.json')
dump('reviews/frozen_configs.json',{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in configs})
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1');started=time.time();calls=0;completed=[]
for p in configs:
 dataset=p.stem;check_code();dump('state.json',{'status':'VALIDATING','current_dataset':dataset,'started_at':datetime.datetime.fromtimestamp(started).isoformat(),'completed':completed,'completed_search_calls':calls,'search_call_cap':2600000,'git_backup':'2739b09a67f3ca0b6f145d43690d36345df3182c'})
 with (D/f'logs/{dataset}.log').open('w') as f:
  r=subprocess.run(['taskset','-c','15',str(D/'bin/benchmark'),str(p),str(D/'results'/dataset)],env=env,stdout=f,stderr=subprocess.STDOUT,timeout=7200)
 if r.returncode:
  dump('state.json',{'status':'VALIDATION_FAILED','dataset':dataset,'returncode':r.returncode,'completed':completed,'completed_search_calls':calls});raise SystemExit(r.returncode)
 c=json.loads((D/'results'/dataset/'complete.json').read_text());calls+=c['search_calls'];assert calls<=2600000;completed.append(dataset);print('PASS',dataset,'calls',calls,'elapsed',time.time()-started,flush=True)
check_code();dump('state.json',{'status':'MEASUREMENTS_COMPLETE','completed':completed,'search_calls':calls,'wall_seconds':time.time()-started,'completed_at':datetime.datetime.now().isoformat(),'git_backup':'2739b09a67f3ca0b6f145d43690d36345df3182c'})
