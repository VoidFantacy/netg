#!/usr/bin/env python3
import json,hashlib,subprocess,time,sys,datetime
from pathlib import Path
R=Path(__file__).resolve().parents[1];OLD=R.parent/'20261028_adaptive_completion_pilot_v1';REPO=R.parents[1]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 t=time.perf_counter();assert not (R/'freeze.json').exists();checks=[]
 for ds in ['coco','deep10m_l2_v1']:
  v=json.loads((R/f'reviews/qualification_{ds}/complete.json').read_text());assert v['points']==24 and v['batches']==24
  for L in [100,200,400]:
   for m in ['GT10','B32','REG-R']:
    for name in ['ids.i32','distances.f32','entry_ids.i32','profile_distances.f32']:
     x=(R/f'reviews/qualification_{ds}/{m}_L{L}/raw/{name}').read_bytes();assert (OLD/f'results/{ds}/{m}_L{L}/raw/{name}').open('rb').read(len(x))==x
  checks.append(dict(dataset=ds,prefix_queries=128,points=24,all_merge_oracles=True,original_GT10_B32_REGR_bits_equal=True,OPTR_REGR_bits_equal=True))
 oldman=json.loads((OLD/'delivery_manifest.json').read_text());oldchecks=0
 for row in oldman['files']:
  p=Path(row['path']);p=p if p.is_absolute() else OLD/p
  assert sha(p)==row['sha256'],str(p);oldchecks+=1
 # Bind all local compilation dependencies, not just the top-level source.
 a=json.loads((R/'reviews/build_receipt.json').read_text())['argv'];inc=[v for v in a if v.startswith('-I')];deps=subprocess.check_output(['g++','-std=c++17','-fopenmp',*inc,'-MM',str(R/'src/cost_budget.cpp')],cwd=REPO,text=True)
 (R/'reviews/compile_dependencies.txt').write_text(deps);dep_paths=[Path(p).resolve() for p in deps.replace('\\\n',' ').split(':',1)[1].split()]
 files=set(dep_paths)
 for folder in ['src','configs','models','bin']:
  files.update(p for p in (R/folder).rglob('*') if p.is_file())
 files.update(R/'scripts'/n for n in ['prepare_blocks.py','train_selector.py','run_native.py','freeze.py'])
 files.update([R/'protocol.md',R/'reviews/build_receipt.json',OLD/'freeze.json',OLD/'delivery_manifest.json'])
 for p in a:
  if p.endswith(('.a','.o')): files.add((REPO/p).resolve() if not Path(p).is_absolute() else Path(p))
 large=[]
 for ds in ['coco','deep10m_l2_v1']:
  c=json.loads((R/f'configs/{ds}.json').read_text())
  for k in ['base','index']:
   p=Path(c[k]['path'] if k=='base' else c[k]);s=p.stat();large.append(dict(dataset=ds,role=k,path=str(p),bytes=s.st_size,mtime_ns=s.st_mtime_ns,inode=s.st_ino))
  for k in ['queries','test_gt','train_queries','train_gt']:files.add(Path(c[k]['path']))
  files.update(Path(c['router'][k]) for k in ['ids','W','graph']);files.add(Path(c['table']))
  files.update(Path(c['teacher_dir'])/'raw'/k for k in ['ids.i32','distances.f32'])
  files.update(Path(c['backend'])/n for n in ['centroids.f32','codebooks.f32','codes.u8','region_ids.i32','id_region.i32','offsets.u64','models.json'])
 frozen=dict(status='FROZEN_BEFORE_CALIBRATION_MATRIX_AND_FORMAL',timestamp=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),files=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(files)],large_assets=large,qualification=checks,old_E187_seal_files_verified=oldchecks,formal_quality_read=False,calibration_matrix_read=False,seconds=time.perf_counter()-t)
 (R/'freeze.json').write_text(json.dumps(frozen,indent=2)+'\n');print(json.dumps({k:v for k,v in frozen.items() if k not in ['files','large_assets']}),flush=True)
if __name__=='__main__':main()
