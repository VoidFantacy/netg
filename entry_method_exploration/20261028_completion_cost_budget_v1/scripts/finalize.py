#!/usr/bin/env python3
import csv,hashlib,json,re,time,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];REPO=R.parents[1]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def dump(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def main():
 t=time.perf_counter();audit=json.loads((R/'reviews/results_audit.json').read_text());score=json.loads((R/'reviews/score_binding_audit.json').read_text());pdf=json.loads((R/'reviews/pdf_validation.json').read_text());visual=json.loads((R/'reviews/pdf_visual_review.json').read_text());assert audit['points']==100 and audit['formal_batches']==300 and audit['old_E187_seal_files_unchanged']==689;assert score['status']=='PASS_E188_INDEPENDENT_FLOAT64_SCORE_BINDING' and pdf['status']=='PASS_SIX_PAGE_PDF' and visual['pages_checked']==[1,2,3,4,5,6]
 for filename in ['freeze.json','formal_analysis_binding.json']:
  v=json.loads((R/filename).read_text());assert all(sha(x['path'])==x['sha256'] for x in v['files'])
 correction=json.loads((R/'corrected_selection_freeze.json').read_text());assert sha(R/'calibration_role_correction.md')==correction['correction_sha256']
 docs=[REPO/n for n in ['summary.md','spec.md','s-target.md','s-experiment.md','LOCAL_CODEX_START.md','experiment_history/README.md','experiment_history/188_completion_cost_budget_v1.md']]+[R/'report_zh.md',R/'protocol.md',R/'calibration_role_correction.md'];broken=[]
 for p in docs:
  s=p.read_text()
  for raw in re.findall(r'\[[^\]]*\]\(([^)]+)\)',s):
   raw=raw.split('#')[0].strip('<>')
   if not raw or '://' in raw:continue
   target=Path(raw) if raw.startswith('/') else p.parent/raw
   if not target.exists():broken.append(dict(file=str(p),target=raw))
 assert not broken,broken
 assert sha(REPO/'AGENTS.md')==sha(R/'source_before/AGENTS.md')
 changed=[str(p.relative_to(REPO)) for p in docs if p.is_relative_to(REPO)]
 subprocess.run(['git','diff','--check','--',*changed],cwd=REPO,check=True)
 comp=list(csv.DictReader((R/'analysis/discrete_comparisons.csv').open()));blocks=[x for x in comp if x['method'].startswith('BLOCK-')];dom=sum(bool(x['dominated_by_GT_L']) for x in blocks)
 state=json.loads((R/'state.json').read_text());state.update(status='COMPLETED_NO_DEFAULT_CHANGE',formal_points=100,formal_batches=300,calibration_points=100,calibration_batches=300,block_points=24,block_points_dominated_by_measured_GT10=dom,default_changed=False,remaining_matrix=False,calibration_role_correction=True);state.pop('next_steps_after_formal',None);dump(R/'state.json',state)
 rec=dict(status='PASS_E188_LOCAL_DELIVERY',formal_points=100,formal_batches=300,calibration_points=100,calibration_batches=300,original_and_corrected_selection_preserved=True,source_models_inputs_unchanged=True,original_E187_seal_unchanged=True,quality_audit=audit['status'],score_audit=score['status'],PDF=pdf['status'],visual=visual['status'],local_links_checked=True,broken_links=broken,current_docs=[dict(path=str(p),sha256=sha(p)) for p in docs],default_changed=False,seconds=time.perf_counter()-t);dump(R/'delivery_validation.json',rec)
 files=[]
 for p in sorted(R.rglob('*')):
  if not p.is_file() or p.name=='delivery_manifest.json' or '__pycache__' in p.parts:continue
  files.append(dict(path=p.relative_to(R).as_posix(),bytes=p.stat().st_size,sha256=sha(p)))
 total=sum(x['bytes'] for x in files);assert total<2*1024**3,total;dump(R/'delivery_manifest.json',dict(status='SEALED_E188_LOCAL_DELIVERY',files=files,total_bytes=total,default_changed=False,old_scientific_artifacts_modified=False));print(json.dumps(dict(status=rec['status'],files=len(files),MiB=total/2**20,blocks_dominated=dom),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
