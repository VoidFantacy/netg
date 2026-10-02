import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='1'
import sys,json,time,subprocess,hashlib,csv
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent;TB=R.parents[1];ROOT=TB.parents[1];E=TB/'stages/e107_initialization_factorial'
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def ident(p):p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
assert not (R/'lock.json').exists()
started=time.time();datasets=list(read(E/'config.locked.json')['datasets']);locked=dict(created_unix=started,posthoc_mechanism_diagnostic=True,query_subset_selection=False,new_NSG=0,new_ANN=0,groups=['all','first_retained','first_changed'],families=['UnitHub','GT1','GT10'],source=[ident(R/'run.py'),ident(R/'inspect.cpp')],references=[])
configs=[]
for ds in datasets:
 c=read(E/'reviews'/('main_'+ds+'.json'));root=E/'results'/('main_'+ds)
 c={k:c[k] for k in ['dataset','dimension','H','n','queries','GT','hub_ids','base','K_L']};c['raw_hubs']=str(ROOT/'entry_method_exploration/20260910_gt_topk_profiles_v1/inputs'/ds/'raw_hubs.f32')
 c['methods']=[dict(name=name,count=count,entries=str(root/name/'entries.i32')) for name,count in [('UnitHub1',1),('UnitHub3',3),('GT11',1),('GT13',3),('GT101',1),('GT103',3)]]
 for p in [c['queries'],c['GT'],c['hub_ids'],c['raw_hubs']]+[m['entries'] for m in c['methods']]:locked['references'].append(ident(p))
 cfg=R/(ds+'.json');dump(cfg,c);configs.append((cfg,c));locked['source'].append(ident(cfg))
dump(R/'lock.json',locked)
argv=read(E/'reviews/jobs.json')[0]['argv'];argv=[str(R/'inspect.cpp') if x==str(E/'src/evaluate.cpp') else str(R/'inspect') if x==str(E/'bin/evaluate') else x for x in argv];jobs=[]
def execute(argv,log,timeout):
 j=dict(argv=argv,started_unix=time.time());jobs.append(j)
 with (R/log).open('x') as f:
  result=subprocess.run(argv,stdout=f,stderr=subprocess.STDOUT,timeout=timeout,env=os.environ,start_new_session=True)
 j.update(exit_code=result.returncode,seconds=time.time()-j['started_unix']);dump(R/'jobs.json',jobs);assert result.returncode==0
execute(argv,'build.log',120)
summaries=[];strata=[];raw_checks=[]
for path,c in configs:
 ds=c['dataset'];execute(['taskset','-c','15',str(R/'inspect'),str(path),str(R/ds)],ds+'.log',60)
 n=c['n'];d=c['dimension'];h=c['H'];raw=np.fromfile(c['raw_hubs'],'<f4').reshape(h,d);hids=np.fromfile(c['hub_ids'],'<i4');q=np.fromfile(c['queries'],'<f4').reshape(n,d);gt=np.fromfile(c['GT'],'<i4').reshape(n,100);norm=np.linalg.norm(raw.astype('float64'),axis=1);base=np.memmap(c['base'],dtype='<f4',mode='r').reshape(-1,d+1)[:,1:];assert np.array_equal(raw,base[hids])
 for family in locked['families']:
  a=family+'1';b=family+'3';es=[np.fromfile(E/'results'/('main_'+ds)/name/'entries.i32','<i4').reshape(n,3) for name in [a,b]];first=np.fromfile(R/ds/b/'first.i32','<i4');dist=np.fromfile(R/ds/b/'initial_distances.f32','<f4').reshape(n,3);double=np.sum(q[:,None,:].astype('float64')*raw[np.searchsorted(hids,es[1])].astype('float64'),axis=2)*-1;assert np.allclose(dist,double,atol=2e-6,rtol=2e-6)
  changed=first!=es[0][:,0];tie=(np.sort(dist,axis=1)[:,0]==np.sort(dist,axis=1)[:,1]);assert np.all(np.any(es[1]==es[0][:,:1],axis=1));assert np.array_equal(np.fromfile(R/ds/a/'first.i32','<i4'),es[0][:,0])
  summaries.append(dict(dataset=ds,family=family,n=n,first_changed=int(changed.sum()),first_changed_pct=100*changed.mean(),minimum_distance_ties=int(tie.sum()),hub_norm_min=norm.min(),hub_norm_max=norm.max(),hub_norm_cv=norm.std()/norm.mean(),max_initial_distance_float64_error=float(np.max(abs(dist-double)))))
  for K,Ls in c['K_L'].items():
   K=int(K)
   for L in Ls:
    hits=[];ndcs=[]
    for name in [a,b]:
     p=E/'results'/('main_'+ds)/name/f'k{K}_L{L}';ids=np.fromfile(p/'ids.i32','<i4').reshape(n,K);hit=(ids[:,:,None]==gt[:,None,:K]).any(1).sum(1);hits.append(hit);ndcs.append(np.fromfile(p/'ndc.u64','<u8'))
    delta=(hits[1].astype('int64')-hits[0])/K*100
    for group,mask in [('all',np.ones(n,bool)),('first_retained',~changed),('first_changed',changed)]:
     if not mask.any():continue
     strata.append(dict(dataset=ds,family=family,K=K,L=L,group=group,n=int(mask.sum()),delta_recall_pp=float(delta[mask].mean()),gained=int((delta[mask]>0).sum()),harmed=int((delta[mask]<0).sum()),baseline_failed=int((hits[0][mask]==0).sum()),three_failed=int((hits[1][mask]==0).sum()),delta_graph_ndc_pct=float((ndcs[1][mask].mean()/ndcs[0][mask].mean()-1)*100),posthoc_association_only=True))
 for p in (R/ds).rglob('*'):
  if p.is_file():raw_checks.append(ident(p))
def table(p,rows):
 with (R/p).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
table('initial_order.csv',summaries);table('stratified_results.csv',strata)
for x in locked['references']+locked['source']:assert ident(x['path'])==x
dump(R/'complete.json',dict(status='PASS_DIAGNOSTIC_COMPLETE',seconds=time.time()-started,NSG_calls=0,ANN_calls=0,new_training=0,raw_results=raw_checks,reference_hashes_preserved=len(locked['references']),full_query_groups=True,posthoc_association_only=True))
print(json.dumps(summaries,ensure_ascii=False,indent=2))
