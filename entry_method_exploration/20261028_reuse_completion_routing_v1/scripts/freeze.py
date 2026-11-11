import json,hashlib,subprocess,time,datetime
from pathlib import Path
R=Path(__file__).resolve().parents[1];OLD=R.parent/'20261028_completion_cost_budget_v1';REPO=R.parents[1]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 t=time.perf_counter();assert not (R/'freeze.json').exists();checks=[]
 for ds in ['coco','deep10m_l2_v1']:
  v=json.loads((R/f'reviews/qualification_{ds}/complete.json').read_text());assert v['points']==18 and v['batches']==18
  for L in [100,200,400]:
   for m in ['GT10','B32','BLOCK-R2048']:
    for name in ['ids.i32','distances.f32','entry_ids.i32','profile_distances.f32']:
     x=(R/f'reviews/qualification_{ds}/{m}_L{L}/raw/{name}').read_bytes();assert (OLD/f'results/{ds}/{m}_L{L}/raw/{name}').open('rb').read(len(x))==x
  checks.append(dict(dataset=ds,prefix_queries=128,points=18,full_merge_oracles=True,old_control_bits_equal=True))
 assert json.loads((R/'reviews/qualification_trace_audit.json').read_text())['status'].startswith('PASS')
 a=json.loads((R/'reviews/build_receipt.json').read_text())['argv'];inc=[v for v in a if v.startswith('-I')];dep=subprocess.check_output(['g++','-std=c++17','-fopenmp',*inc,'-MM',str(R/'src/reuse.cpp')],cwd=REPO,text=True);(R/'reviews/compile_dependencies.txt').write_text(dep);files={Path(p).resolve() for p in dep.replace('\\\n',' ').split(':',1)[1].split()}
 for folder in ['src','configs','models','bin','scripts']:files.update(p for p in (R/folder).rglob('*') if p.is_file() and '__pycache__' not in str(p))
 files.update([R/'protocol.md',R/'preparation.json',R/'reviews/build_receipt.json',OLD/'freeze.json',OLD/'delivery_manifest.json'])
 for p in a:
  if p.endswith(('.a','.o')):files.add((REPO/p).resolve() if not Path(p).is_absolute() else Path(p))
 large=[]
 for ds in ['coco','deep10m_l2_v1']:
  c=json.loads((R/f'configs/{ds}.json').read_text())
  for key in ['base','index']:
   p=Path(c[key]['path'] if key=='base' else c[key]);s=p.stat();large.append(dict(dataset=ds,role=key,path=str(p),bytes=s.st_size,mtime_ns=s.st_mtime_ns,inode=s.st_ino))
  for key in ['queries','test_gt','train_queries','train_gt']:files.add(Path(c[key]['path']))
  files.update(Path(c['router'][k]) for k in ['ids','W','graph']);files.add(Path(c['table']))
  files.update(Path(c['teacher_dir'])/'raw'/k for k in ['ids.i32','entry_ids.i32'])
  for key in ['backend','blocks']:files.update(p for p in Path(c[key]).iterdir() if p.is_file())
 v=dict(status='FROZEN_BEFORE_CALIBRATION_AND_FORMAL',timestamp=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),files=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(files)],large_assets=large,qualification=checks,formal_quality_read=False,calibration_quality_read=False,no_configuration_selection=True,seconds=time.perf_counter()-t)
 (R/'freeze.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps({k:v for k,v in v.items() if k not in ['files','large_assets']}),flush=True)
if __name__=='__main__':main()
