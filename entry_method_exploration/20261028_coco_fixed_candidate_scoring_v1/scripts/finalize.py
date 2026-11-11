import csv,hashlib,json,re,subprocess,shutil,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];REPO=R.parents[1];OLD=R.parent/'20261028_reuse_completion_routing_v1'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def dump(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def main():
 t=time.perf_counter();assert not (R/'delivery_manifest.json').exists();build=json.loads((R/'reviews/report_build.json').read_text());selection=json.loads((R/'selection.json').read_text());assert not selection['cascade_triggered'],'this closeout is for nontriggered fixed primary version'
 for name in ['formal_results_audit.json','calibration_results_audit.json','scoring_formal_audit.json','scoring_calibration_audit.json','scoring_qualification_audit.json','pdf_validation.json','pdf_visual_review.json']:
  assert json.loads((R/'reviews'/name).read_text())['status'].startswith('PASS'),name
 for name in ['freeze.json','postprocessing_binding.json']:
  for x in json.loads((R/name).read_text())['files']:assert sha(x['path'])==x['sha256'],x['path']
 for x in json.loads((OLD/'delivery_manifest.json').read_text())['files']:
  p=Path(x['path']);p=p if p.is_absolute() else OLD/p;assert sha(p)==x['sha256']
 for role in ['prepare','qualification','calibration','formal']:
  x=json.loads((R/f'reviews/{role}_coco.receipt.json').read_text());assert x['returncode']==0 and x['max_observed_threads']==1
 assert sha(REPO/'AGENTS.md')==sha(R/'source_before/AGENTS.md')
 docs=[REPO/x for x in ['summary.md','spec.md','s-target.md','s-experiment.md','LOCAL_CODEX_START.md','experiment_history/README.md','experiment_history/190_coco_fixed_candidate_scoring_v1.md']]+[R/'protocol.md',R/'report_zh.md'];links=0;broken=[]
 for p in docs:
  for raw in re.findall(r'\[[^\]]*\]\(([^)]+)\)',p.read_text()):
   raw=raw.split('#')[0].strip('<>')
   if not raw or '://' in raw:continue
   target=Path(raw) if raw.startswith('/') else p.parent/raw;links+=1
   if not target.exists():broken.append(dict(file=str(p),target=raw))
 assert not broken,broken
 subprocess.run(['git','diff','--check','--',*[str(x.relative_to(REPO)) for x in docs]],cwd=REPO,check=True)
 dump(R/'state.json',dict(status='COMPLETED_NO_DEFAULT_CHANGE',formal_points=29,formal_batches=87,calibration_points=26,calibration_batches=78,new_points=build['new_points'],dominated_new_points=build['dominated'],speed_screen=build['speed_screen'],budget_recall_screen=build['budget_recall_screen'],cascade_triggered=False,default_changed=False,remaining_matrix=False))
 dump(R/'delivery_validation.json',dict(status='PASS_E190_LOCAL_DELIVERY',old_E189_seal_files_unchanged=1570,frozen_scientific_inputs_unchanged=True,formal_points=29,calibration_points=26,default_changed=False,links_checked=links,broken_links=broken,docs=[dict(path=str(p),sha256=sha(p)) for p in docs],seconds=time.perf_counter()-t))
 files=[dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(R.rglob('*')) if p.is_file() and p.name!='delivery_manifest.json' and '__pycache__' not in p.parts];total=sum(x['bytes'] for x in files);free=shutil.disk_usage(R).free;assert total<.65*2**30 and free>.7*2**30,(total,free)
 dump(R/'delivery_manifest.json',dict(status='SEALED_E190_LOCAL_DELIVERY',files=files,total_bytes=total,disk_free_bytes=free,old_scientific_artifacts_modified=False));print(json.dumps(dict(status='PASS_E190_LOCAL_DELIVERY',files=len(files),MiB=total/2**20,remaining_GiB=free/2**30)),flush=True)
if __name__=='__main__':main()
