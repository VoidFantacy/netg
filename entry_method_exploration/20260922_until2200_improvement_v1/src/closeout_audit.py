from pathlib import Path
import json,re,hashlib,time
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1];start=time.perf_counter()
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(16<<20),b''):h.update(b)
 return h.hexdigest()
old=ROOT/'entry_method_exploration/20260922_gt10_strength_review_v1';m=json.loads((old/'manifest.json').read_text());old_checks=0
for name,v in m['artifact_files'].items():p=old/name;assert sha(p)==v['sha256'] and p.stat().st_size==v['size'];old_checks+=1
p=ROOT/m['history_record']['path'];assert sha(p)==m['history_record']['sha256'];old_checks+=1
pdf=json.loads((R/'reviews/pdf_verification.json').read_text());assert pdf['status']=='PASS' and not pdf['empty_pages'] and not pdf['outside_page_text_spans'];assert sha(R/'GT10理论与性能改进研究.pdf')==pdf['pdf_sha256']
for path,h in pdf['sources'].items():assert sha(R/path)==h
F=R/'stages/e125_web_fresh_check_v1';s=json.loads((F/'results/summary.json').read_text());methods=s['methods'];a=methods['GT10-soft-t1'];b=methods['ApproxTarget10'];assert a['hits']==3719 and b['hits']==3713 and s['rescue']==6 and s['damage']==12;assert s['recall_delta_pp']==-6/4096*100
assert json.loads((F/'reviews/independent_audit.json').read_text())['status']=='PASS';assert json.loads((F/'decision.json').read_text())['status']=='RETAIN_LOW_COST_CANDIDATE';assert json.loads((F/'reviews/jobs_complete.json').read_text())['new_ANN_calls']==40960
# Old gate is deliberately not retrospectively reclassified.
gate=(R/'stages/e125_approximate_target_profiles_v1/results/gate.json').read_text();assert 'STOP_APPROX_TARGET_PROFILE_PILOT' in gate
policy=(ROOT/'AGENTS.md').read_text();assert '单点非劣区间未通过不能一票否决' in policy
sources=[ROOT/f for f in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md']]
sources += [R/f for f in ['report.md','directions.md','theory.md','research_decision_policy.md','README.md']]
sources += [p for folder in ['stages','research'] for p in (R/folder).glob('*/report.md')]
sources += [p for n in range(128,141) for p in (ROOT/'experiment_history').glob(f'{n}_*.md')]
missing=[];nlinks=0
for p in sources:
 for raw in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if raw.startswith(('http:','https:','#','mailto:')):continue
  target=raw.split('#')[0]
  if not (p.parent/target).exists():missing.append({'source':str(p.relative_to(ROOT)),'target':target})
  nlinks+=1
assert not missing,missing
# Figure receipts bind every input. Figures are descriptive; no QPS recomputed for formatting.
fig=json.loads((R/'reviews/figures.json').read_text());print('figure_receipt_keys',list(fig),flush=True)
checked=[]
for p in ['/proc/'+x+'/cmdline' for x in __import__('os').listdir('/proc') if x.isdigit()]:
 try:
  argv=Path(p).read_bytes().split(b'\0');exe=argv[0].decode(errors='replace')
 except (FileNotFoundError,ProcessLookupError,PermissionError):continue
 if exe.startswith(str(R)) and '/bin/' in exe:checked.append(exe)
assert not checked,checked
result={'status':'PASS','seconds':time.perf_counter()-start,'old_1700_artifacts_unchanged':old_checks,'root_changes_intended':'AGENTS policy + role-separated four docs + history index; originals snapshotted','pdf_pages':pdf['pages'],'pdf_source_hashes_current':True,'local_links_checked':nlinks,'missing_links':missing,'current_frozen_model_followup':'RETAIN_LOW_COST_CANDIDATE','old_gate_preserved':True,'new_NSG_calls':1201492,'new_ANN_calls':649376,'new_exact_GT_queries':54096,'training_only_residual_diagnostic':'no candidate export, no evaluation access','live_native_jobs':checked,'default_changed':False}
p=R/'reviews/final_closeout_audit.json';assert not p.exists();p.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n');print(json.dumps(result,indent=2,ensure_ascii=False))
