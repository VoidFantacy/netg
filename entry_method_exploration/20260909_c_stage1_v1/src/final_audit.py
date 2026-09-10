#!/usr/bin/env python3
"""Read-only final source/input/lock protection audit. No ANN; no evaluation split data."""
import hashlib,json,datetime
from pathlib import Path
V=Path(__file__).resolve().parents[1];R=Path('/data/netg/ACSG')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(p.read_text())
records=[]
mutable={'summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/09_research_designs_not_experiments.md'}
for rec in read(V/'source_manifest.json')['protected_sources']:
 p=R/rec['path'];snapshot=V/'source_before'/rec['path']
 assert sha(snapshot)==rec['sha256'],('snapshot changed',rec['path'])
 if rec['path'] not in mutable:
  current=sha(p);assert current==rec['sha256'],('protected source changed',p)
  records.append({'path':str(p),'sha256':current,'kind':'protected_source'})
for ds in ['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1']:
 identities=read(V/'inputs'/ds/'identities.json')
 for key,rec in identities.items():
  if key=='gt_train_deferred':
   # Only the now-authorized training GT is accessed, after all raw branches have completed.
   assert read(V/'results/analysis_v1/report.json')['status']=='C2_COMPLETE'
  p=Path(rec['path']);current=sha(p);assert current==rec['sha256'],('input changed',key,p)
  records.append({'path':str(p),'sha256':current,'kind':key})
lock=read(V/'protocol_lock.json')
for p,expected in [(V/'config.locked.json',lock['config_sha256']),(V/'protocol.md',lock['protocol_sha256'])]+[(Path(x['path']),x['sha256']) for x in lock['bound_files']]:
 assert sha(p)==expected,('locked file changed',p)
 records.append({'path':str(p),'sha256':expected,'kind':'C0_lock'})
for name in ['parity_v2','c2_v2']:
 build=read(V/'bin'/(name+'.build.json'));assert sha(V/'bin'/name)==build['binary_sha256']
 for rec in build['source_and_dependencies']:
  if '/entry_method_exploration/' not in rec['path']:
   assert sha(Path(rec['path']))==rec['sha256'],('library/native source changed',rec['path'])
assert read(V/'state.json')['status']=='NO_GO_UNCONDITIONAL_HEADROOM_STOP_C'
out={'status':'PASS','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'records':records,
     'all_preexisting_protected_sources_unchanged':True,'all_declared_inputs_unchanged':True,
     'C0_scientific_lock_unchanged':True,'validation_opened':False,'heldout_opened':False,
     'mutable_documents':sorted(mutable),'new_version_bytes':sum(p.stat().st_size for p in V.rglob('*') if p.is_file())}
p=V/'results/final_protection_audit.json';assert not p.exists();p.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'status':'PASS','checked_records':len(records),'new_version_bytes':out['new_version_bytes']}))
