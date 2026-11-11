import csv,hashlib,json,re,time,subprocess,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];REPO=R.parents[1]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def dump(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def main():
 t=time.perf_counter();assert not (R/'delivery_manifest.json').exists();audit=json.loads((R/'reviews/results_audit.json').read_text());cal=json.loads((R/'reviews/calibration_results_audit.json').read_text());assert audit['points']==70 and audit['formal_batches']==210 and audit['old_E188_seal_files_unchanged']==2145;assert cal['points']==64 and cal['calibration_batches']==192
 required=['score_binding_audit.json','formal_trace_audit.json','calibration_trace_audit.json','role_model_audit.json','comparison_audit.json','posthoc_scoring_audit.json','pdf_validation.json','pdf_visual_review.json']
 for name in required:assert json.loads((R/'reviews'/name).read_text())['status'].startswith('PASS'),name
 for filename in ['freeze.json','reviews/additional_audit_binding.json','reviews/postprocessing_binding.json']:
  v=json.loads((R/filename).read_text());assert all(sha(x['path'])==x['sha256'] for x in v['files'])
 for role in ['calibration','formal']:
  for ds in ['coco','deep10m_l2_v1']:
   v=json.loads((R/f'reviews/{role}_{ds}.receipt.json').read_text());assert v['returncode']==0 and v['max_observed_threads']==1 and v['peak_sampled_rss_bytes']<64*2**30
 docs=[REPO/n for n in ['summary.md','spec.md','s-target.md','s-experiment.md','LOCAL_CODEX_START.md','experiment_history/README.md','experiment_history/189_reuse_completion_routing_v1.md']]+[R/'report_zh.md',R/'protocol.md'];broken=[]
 for p in docs:
  for raw in re.findall(r'\[[^\]]*\]\(([^)]+)\)',p.read_text()):
   raw=raw.split('#')[0].strip('<>')
   if not raw or '://' in raw:continue
   target=Path(raw) if raw.startswith('/') else p.parent/raw
   if not target.exists():broken.append(dict(file=str(p),target=raw))
 assert not broken,broken;assert sha(REPO/'AGENTS.md')==sha(R/'source_before/AGENTS.md');subprocess.run(['git','diff','--check','--',*[str(p.relative_to(REPO)) for p in docs]],cwd=REPO,check=True)
 rec=json.loads((R/'reviews/report_build.json').read_text());dump(R/'state.json',dict(status='COMPLETED_NO_DEFAULT_CHANGE',formal_points=70,formal_batches=210,calibration_points=64,calibration_batches=192,new_points=18,new_points_dominated_by_measured_GT10=rec['dominated'],speed_screen=rec['speed_screen'],budget_recall_screen=rec['budget_recall_screen'],default_changed=False,remaining_matrix=False))
 dump(R/'delivery_validation.json',dict(status='PASS_E189_LOCAL_DELIVERY',old_E188_seal_unchanged=True,frozen_scientific_inputs_unchanged=True,formal_points=70,calibration_points=64,all_batches=402,default_changed=False,local_links_checked=True,broken_links=broken,current_docs=[dict(path=str(p),sha256=sha(p)) for p in docs],seconds=time.perf_counter()-t))
 files=[dict(path=p.relative_to(R).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(R.rglob('*')) if p.is_file() and p.name!='delivery_manifest.json' and '__pycache__' not in p.parts];total=sum(x['bytes'] for x in files);assert total<1.2*2**30;free=shutil.disk_usage(R).free;assert free>=.8*2**30
 dump(R/'delivery_manifest.json',dict(status='SEALED_E189_LOCAL_DELIVERY',files=files,total_bytes=total,disk_free_bytes=free,old_scientific_artifacts_modified=False));print(json.dumps(dict(status='PASS_E189_LOCAL_DELIVERY',files=len(files),MiB=total/2**20,remaining_GiB=free/2**30)),flush=True)
if __name__=='__main__':main()
