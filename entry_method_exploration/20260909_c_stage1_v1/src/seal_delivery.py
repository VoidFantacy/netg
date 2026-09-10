#!/usr/bin/env python3
import datetime,hashlib,json,shutil
from pathlib import Path
V=Path(__file__).resolve().parents[1];R=Path('/data/netg/ACSG')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(p.read_text())
assert not (V/'delivery_manifest.json').exists()
assert read(V/'results/final_protection_audit.json')['status']=='PASS'
assert read(V/'reviews/kernel_review.json')['status']=='PASS'
assert read(V/'reviews/c2_statistics_final_review.json')['status']=='PASS'
assert (V/'reviews/docs_final_review.md').exists()
root_files=['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md',
            'experiment_history/09_research_designs_not_experiments.md','experiment_history/10_c_state_intervention.md']
roots=[]
for name in root_files:
 p=R/name;dest=V/'source_after'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
 roots.append({'path':str(p),'sha256':sha(p),'snapshot':str(dest.relative_to(V))})
files=[]
for p in sorted(V.rglob('*')):
 if p.is_file():files.append({'path':str(p.relative_to(V)),'bytes':p.stat().st_size,'sha256':sha(p)})
manifest={'schema_version':1,'status':'DELIVERY_COMPLETE_STOPPED_BEFORE_C3','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'method_decision':'NO_GO_UNCONDITIONAL_HEADROOM_STOP_C','root_documents':roots,'files':files,'file_count':len(files),
          'artifact_bytes':sum(x['bytes'] for x in files),'C3_run':False,'C4_run':False,'validation_accessed':False,'heldout_accessed':False}
(V/'delivery_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
# Verify the exact sealed bytes once; the manifest does not recursively hash itself.
for rec in files:assert sha(V/rec['path'])==rec['sha256'],rec['path']
for rec in roots:assert sha(Path(rec['path']))==rec['sha256'],rec['path']
(V/'delivery_checks.json').write_text(json.dumps({'status':'PASS','manifest_sha256':sha(V/'delivery_manifest.json'),
   'files_verified':len(files),'root_documents_verified':len(roots),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2)+'\n')
print(json.dumps({'status':'PASS','files':len(files),'bytes':manifest['artifact_bytes']}))
