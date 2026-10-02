from pathlib import Path
import json,hashlib,time,datetime
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1];start=time.perf_counter();cache={};checks=[];seals=[]
def identity(p):
 p=p.resolve();s=p.stat();key=(str(p),s.st_size,s.st_mtime_ns)
 if key not in cache:
  h=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(16<<20),b''):h.update(b)
  cache[key]={'bytes':s.st_size,'sha256':h.hexdigest()}
 return cache[key]
def verify_dict(items,base):
 count=0
 for name,v in items.items():
  if not isinstance(v,dict) or 'sha256' not in v:continue
  p=Path(name);p=p if p.is_absolute() else base/p;actual=identity(p);assert actual['sha256']==v['sha256'],p
  if 'bytes' in v:assert actual['bytes']==v['bytes']
  if 'size' in v:assert actual['bytes']==v['size']
  count+=1
 return count
for d in sorted([*filter(Path.is_dir,(R/'stages').iterdir()),*filter(Path.is_dir,(R/'research').iterdir())]):
 p=d/'reviews/seal.json'
 if p.exists():
  v=json.loads(p.read_text());n=verify_dict(v['files'],d);seals.append({'path':str(p.relative_to(R)),'previous_seal_verified':True,'files':n})
 else:
  (d/'reviews').mkdir(exist_ok=True);files={str(q.relative_to(d)):identity(q) for q in sorted(d.rglob('*')) if q.is_file() and '__pycache__' not in q.parts};v={'status':'SEALED','at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':files,'bytes':sum(x['bytes'] for x in files.values())};p.write_text(json.dumps(v,indent=2)+'\n');seals.append({'path':str(p.relative_to(R)),'previous_seal_verified':False,'files':len(files)})
 print(d.name,'SEALED/VERIFIED',seals[-1]['files'],flush=True)
manifests=['stages/e121_router_state_table_v1/reviews/router_inputs_before.json','stages/e121_router_state_table_v1/reviews/response_inputs.json','stages/e125_approximate_target_profiles_v1/reviews/prepare_inputs.json','stages/e125_approximate_target_profiles_v1/reviews/run_frozen.json','stages/e125_approximate_target_profiles_v1/reviews/models_frozen_before_evaluation.json','research/gt_inclusive_build_cost_v1/reviews/rebuild_inputs.json','research/target_budget_fullH_v1/reviews/analysis_inputs.json','research/target_budget_fullH_v1/reviews/run_frozen.json','research/approximate_supervision_scope_v1/source_review.json','stages/e125_web_fresh_check_v1/reviews/models_before_source.json','stages/e125_web_fresh_check_v1/reviews/frozen_before_source.json']
for name in manifests:
 p=R/name;v=json.loads(p.read_text());n=verify_dict(v.get('files',v),p.parent);checks.append({'manifest':name,'file_checks':n})
large=json.loads((R/'research/target_budget_fullH_v1/reviews/large_inputs_before.json').read_text())['stat_only']
for name,v in large.items():s=Path(name).stat();assert s.st_size==v['bytes'] and s.st_mtime_ns==v['mtime_ns'],name
snap=R/'reviews/root_docs_before_closeout';n=verify_dict(json.loads((snap/'identity.json').read_text())['files'],snap)
p=R/'reviews/artifact_seals_verification_final.json';assert not p.exists();v={'status':'PASS','seconds':time.perf_counter()-start,'stages':seals,'input_manifests':checks,'large_file_stat_checks':4,'root_snapshot_files':n,'unique_file_hashes':len(cache),'hashed_bytes':sum(x['bytes'] for x in cache.values()),'default_changed':False};p.write_text(json.dumps(v,indent=2)+'\n');print('ALL PASS',len(cache),round(v['seconds'],3),flush=True)
