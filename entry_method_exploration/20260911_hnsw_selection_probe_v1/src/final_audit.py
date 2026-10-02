from common import *
import re,csv,itertools,ast
assert not (O/'reviews/final_audit.json').exists()
state=read(O/'state.json');assert state['status']=='QUERY_COMPLETE_ANALYSIS_PENDING'
for f in ['before_queries.json','analysis_before_scoring.json','upstream.json']:check(O/'reviews'/f)
# Match actual code/libraries and graphs to the prior verified benchmark identities.
prior={x['path']:x for x in read(E34/'reviews/upstream.json')['files']};matched=0
for x in read(O/'reviews/upstream.json')['files']:
 if x['path'] in prior:assert x['sha256']==prior[x['path']]['sha256'];matched+=1
# No historical validation inputs are opened or hashed: only stat prior artifact inventories.
old_stat=0
for manifest,prefix in [(E34/'reviews/frozen_completion.json',E34),(E34/'reviews/E33_preserved.json',E33)]:
 for x in read(manifest)['files']:
  p=Path(x['path'])
  if p.is_relative_to(prefix):
   st=p.stat();assert st.st_size==x['bytes'] and st.st_mtime_ns==x['mtime_ns'],p;old_stat+=1
old_docs={x['path']:x for x in read(E34/'reviews/frozen_completion.json')['files']}
for name in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md']:
 if str(R/name) in old_docs:assert sha(O/'source_before'/name)==old_docs[str(R/name)]['sha256']
assert sha(R/'AGENTS.md')==sha(O/'source_before/AGENTS.md')
for p in (O/'src').glob('*.py'):ast.parse(p.read_text())
jobs=read(O/'reviews/jobs.json');assert sum(j['NSG_calls'] for j in jobs)==15200 and sum(j['HNSW_calls'] for j in jobs)==3072
assert all(j['status']=='COMPLETE' and j['peak_threads']==1 and j['peak_RSS_KiB']<40*(1<<20) and j['seconds']<1200 and not j['GT_read'] for j in jobs)
result=read(O/'results/diagnosis.json');query=read(O/'results/query_diagnostics.json');quality=read(O/'results/quality.json');checks=read(O/'reviews/result_verification.json');assert checks['status']=='PASS'
oldn=newn=0
for ds,z in zip(DS,result):
 p=O/'inputs'/ds;r=O/'results'/ds;c=read(p/'config.json');h=c['hub_count'];gt=np.fromfile(p/'gt.i64',np.int64).reshape(128,100)
 u=np.fromfile(p/'single.hitcount.u8',np.uint8).reshape(128,h);ids=np.fromfile(r/'ids.i32',np.int32).reshape(128,59,10);sg=np.fromfile(p/'single.ids.i32',np.int32).reshape(128,h,10)
 base_count=read(D/'inputs/prepared_v2'/ds/'runner_config.json')['base_count']
 assert (sg>=0).all() and (sg<base_count).all() and (ids>=0).all() and (ids<base_count).all()
 assert (np.diff(np.sort(sg,axis=-1),axis=-1)!=0).all()
 # Independent set intersection scoring, separate from broadcast implementation.
 expected=np.empty((128,59),np.uint8)
 for i in range(128):
  truth=set(gt[i,:10].tolist())
  for j in range(59):expected[i,j]=len(set(ids[i,j].tolist())&truth)
 scored=np.load(r/'scored.npz');assert np.array_equal(expected,scored['joint_hits']);oldn+=128*h;newn+=128*59
 ann=np.fromfile(r/'ann8_local.i32',np.int32).reshape(128,8);seen=np.fromfile(r/'seen.u8',np.uint8).reshape(128,h).astype(bool);hubs=np.fromfile(c['hub_ids'],np.int32)
 ent=np.fromfile(r/'entries.i32',np.int32).reshape(128,59,3)
 for col,trip in enumerate(itertools.combinations(range(8),3),3):assert np.array_equal(ent[:,col],np.sort(hubs[ann[:,trip]],axis=1))
 rows=[q for q in query if q['dataset']==ds];assert len(rows)==128
 informative=seen_unselected=unseen=selected=0
 for i,q in enumerate(rows):
  best=set(np.flatnonzero(u[i]==u[i].max()).tolist());observed=set(np.flatnonzero(seen[i]).tolist());chosen=set(ann[i,:3].tolist());nonconstant=len(set(u[i].tolist()))>1
  informative+=nonconstant;selected+=bool(nonconstant and best&chosen);seen_unselected+=bool(nonconstant and best&observed and not best&chosen);unseen+=bool(nonconstant and not best&observed)
  assert q['A0_seen']==bool(best&observed) and q['A0_ann3']==bool(best&chosen)
  assert q['C8_triple_oracle_hits']==int(expected[i,3:].max()) and q['ann3_hits']==int(expected[i,0]) and q['exact3_hits']==int(expected[i,1])
 assert informative==z['nonconstant_queries'] and selected==z['A0_in_ann3_nonconstant'] and seen_unselected==z['A0_seen_nonconstant']-z['A0_in_ann3_nonconstant'] and unseen==z['nonconstant_queries']-z['A0_seen_nonconstant']
 assert informative==selected+seen_unselected+unseen and z['QPS'] is None
 for name,col in [('ANN three',0),('Exact three',1),('ef40 three',2),('C8 true triple oracle',None)]:
  v=expected[:,col] if col is not None else expected[:,3:].max(axis=1);rec=next(q for q in quality if q['dataset']==ds and q['method']==name)
  assert rec['recall_pct']==v.mean()*10 and rec['failure_pct']==(v==0).mean()*100
assert oldn==209408 and newn==15104
for name in ['query_diagnostics','quality']:
 expected=read(O/'results'/(name+'.json'))
 with (O/'results'/(name+'.csv')).open() as f:actual=list(csv.DictReader(f))
 assert len(actual)==len(expected)
 for a,b in zip(actual,expected):assert a=={k:str(v) for k,v in b.items()}
assert read(O/'reviews/visual_review.json')['status']=='PASS'
for ext in ['png','svg','pdf']:assert (O/'figures'/('selection_diagnosis.'+ext)).stat().st_size>1000
docs=[R/f for f in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md','experiment_history/24_hnsw_selection_diagnosis.md']]+[O/f for f in ['README.md','report.md','protocol.md']]
links=0
for p in docs:
 for link in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if '://' in link or link.startswith('#'):continue
  target=(p.parent/link.split('#')[0]).resolve()
  assert target.exists() or target==O/'reviews/final_audit.json',(p,link)
  links+=1
subprocess.run(['git','diff','--check','--','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md'],cwd=R,check=True)
artifact=sum(p.stat().st_size for p in O.rglob('*') if p.is_file());free=shutil.disk_usage(O).free;assert artifact<128*(1<<20) and free>=10*(1<<30)
freeze(O/'reviews/frozen_completion.json',[p for p in O.rglob('*') if p.is_file() and p!=O/'state.json']+docs)
final=dict(status='PASS',new_NSG_calls=15200,HNSW_calls=3072,cached_single_outputs_verified=oldn,new_joint_outputs_verified=newn,native_single_regressions=96,
 routes_plain_count_checks=768,current_Policy_parity=256,all56_entry_triples_verified=True,independent_joint_set_scoring=True,CSV_JSON_equal=True,visual_review=True,
 old_artifact_stat_checks=old_stat,actual_upstream_prior_SHA_matches=matched,upstream_SHA_checked=True,old_validation_heldout_read_or_hash=False,document_links_checked=links,
 artifact_bytes_before_final_freeze=artifact,free_disk_bytes=free,training_calls=0,QPS_calls=0,default_replaced=False,closed_at=time.time())
dump(O/'reviews/final_audit.json',final);state.update(status='COMPLETE_HNSW_SELECTION_DIAGNOSIS',final_audit='PASS',closed_at=final['closed_at']);dump(O/'state.json',state)
print(json.dumps(final,indent=2),flush=True)
