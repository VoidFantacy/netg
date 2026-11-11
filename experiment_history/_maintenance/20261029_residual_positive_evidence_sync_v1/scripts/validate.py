from pathlib import Path
import json,hashlib,re,csv,subprocess
R=Path(__file__).resolve().parents[1];REPO=Path(__file__).resolve().parents[4]
def read(p):return json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
roots=['summary.md','spec.md','s-target.md','s-experiment.md','LOCAL_CODEX_START.md','experiment_history/README.md','AGENTS.md']
for x in read(R/'source_manifest.json'):assert sha(Path(x['path']))==x['sha256'],x['path']
oldpath=REPO/'entry_method_exploration/20261029_adaptive_completion_gate_v1/delivery_manifest.json';old=read(oldpath);assert sha(oldpath)==read(R/'previous_seal_before.json')['manifest_sha256'];bridge=[]
for x in old['files']:
 p=Path(x['path'])
 try:rel=str(p.relative_to(REPO))
 except ValueError:rel=None
 effective=R/'source_before'/rel if rel in roots else p
 assert sha(effective)==x['sha256'] and effective.stat().st_size==x['bytes'],p
 if p!=effective:bridge.append(dict(original=str(p),snapshot=str(effective),sha256=x['sha256']))
dump(R/'E193_seal_bridge.json',dict(status='PASS_ALL_ORIGINAL_E193_BYTES_VIA_ROOT_SNAPSHOT_MAPPING',files=len(old['files']),mapped_roots=bridge,original_seal_modified=False))
rows=list(csv.DictReader((R/'positive_examples.csv').open()));assert len(rows)==11
for x in rows:
 source=list(csv.DictReader((REPO/x['source_csv']).open()));qkey='qps_median' if x['campaign']=='E173' else 'qps'
 a=next(y for y in source if all(y[k]==x[k] for k in ['dataset','K','L','method']));b=next(y for y in source if y['dataset']==x['dataset'] and y['K']==x['K'] and y['method']==x['GT_method'] and y['L']==x['GT_L'])
 assert float(a[qkey])==float(x['qps']) and float(a['recall_pct'])==float(x['recall_pct']);assert float(b[qkey])==float(x['GT_qps']) and float(b['recall_pct'])==float(x['GT_recall_pct']);assert abs((float(a[qkey])/float(b[qkey])-1)*100-float(x['QPS_gain_pct']))<1e-10
 if x['comparison_type']=='DISCRETE_RECALL_QPS_DOUBLE_GAIN':assert float(a['recall_pct'])>float(b['recall_pct']) and float(a[qkey])>float(b[qkey])
 else:assert float(b['recall_pct'])+1e-10>=float(a['recall_pct'])
assert len(list(csv.DictReader((R/'E191_retained_12.csv').open())))==12
assert len(list(csv.DictReader((R/'E191_retained_nondominated_7.csv').open())))==7
bad=[]
for p in [R/'README.md',R/'conclusion_zh.md']+[REPO/x for x in roots if x!='AGENTS.md']:
 for url in re.findall(r'\[[^\]]*\]\(([^)]+)\)',p.read_text()):
  if url.startswith(('http:','https:','#')):continue
  if p.is_relative_to(R) or '20261029_residual_positive_evidence_sync_v1' in url:
   if not (p.parent/url.split('#')[0]).exists():bad.append((str(p),url))
assert not bad,bad
rec=read(R/'memory_update_receipt.json');assert sha(Path(rec['path']))==rec['sha256'];assert Path(rec['path']).is_relative_to('/root/.codex/memories/extensions/ad_hoc/notes')
check=subprocess.run(['git','diff','--check','--',*roots],cwd=REPO,capture_output=True,text=True);assert check.returncode==0,check.stdout+check.stderr
assert not list(R.rglob('*.pdf'))
validation=dict(status='PASS_DOCUMENT_SYNC_AND_AUTHORIZED_MEMORY_NOTE',original_E193_sealed_files_verified=len(old['files']),positive_same_campaign_pairs=11,E191_retained=12,E191_retained_nondominated=7,new_ANN=False,new_training=False,new_performance=False,default_changed=False,new_PDF=False,memory_note_written=True,source_manifest_verified=True,links_verified=True,old_seal_unchanged=True)
dump(R/'validation.json',validation)
files=[p for p in R.rglob('*') if p.is_file() and '__pycache__' not in str(p) and p.name!='delivery_manifest.json']+[REPO/x for x in roots]
dump(R/'delivery_manifest.json',dict(status='SEALED_DOCUMENT_SYNC_WITH_POSITIVE_EVIDENCE',files=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(files)]))
print(json.dumps(validation,ensure_ascii=False,indent=2))
