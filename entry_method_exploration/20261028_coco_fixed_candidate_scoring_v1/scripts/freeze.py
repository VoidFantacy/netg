import hashlib,json,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];REPO=R.parents[1];OLD=R.parent/'20261028_reuse_completion_routing_v1'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 t=time.perf_counter();assert not (R/'freeze.json').exists()
 done=json.loads((R/'reviews/qualification_coco/complete.json').read_text());assert done['points']==15
 for L in [100,200,400]:
  for m in ['GT10','B32','REUSE-BLOCK']:
   for name in ['ids.i32','distances.f32','entry_ids.i32','profile_distances.f32']:
    p=R/f'reviews/qualification_coco/{m}_L{L}/raw/{name}';b=p.read_bytes();assert (OLD/f'results/coco/{m}_L{L}/raw/{name}').open('rb').read(len(b))==b
 assert json.loads((R/'reviews/scoring_qualification_audit.json').read_text())['status'].startswith('PASS')
 old=json.loads((OLD/'delivery_manifest.json').read_text());n=0
 for v in old['files']:
  p=Path(v['path']);p=p if p.is_absolute() else OLD/p;assert sha(p)==v['sha256'],str(p);n+=1
 a=json.loads((R/'reviews/build_receipt.json').read_text())['argv'];incs=[x for x in a if x.startswith('-I')];dep=subprocess.check_output(['g++','-std=c++17','-fopenmp',*incs,'-MM',str(R/'src/scoring.cpp')],cwd=REPO,text=True);(R/'reviews/compile_dependencies.txt').write_text(dep)
 files={Path(p).resolve() for p in dep.replace('\\\n',' ').split(':',1)[1].split()}
 for folder in ['src','models','configs','bin','scripts']:files.update(p.resolve() for p in (R/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
 for x in a:
  if x.endswith(('.a','.o')):files.add((REPO/x).resolve() if not Path(x).is_absolute() else Path(x))
 c=json.loads((R/'configs/coco.json').read_text())
 for k in ['base','queries','test_gt','train_queries','train_gt']:files.add(Path(c[k]['path']))
 files.add(Path(c['index']));files.add(Path(c['table']));files.update(Path(c['router'][k]) for k in ['W','ids','graph'])
 for key in ['backend','blocks','reuse']:files.update(p for p in Path(c[key]).iterdir() if p.is_file())
 files.add(R/'protocol.md');files.add(OLD/'delivery_manifest.json')
 rec=dict(status='FROZEN_BEFORE_CALIBRATION_AND_FORMAL',files=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(files)],old_E189_seal_files_verified=n,qualification_points=15,source_before_binding=[dict(path=str(p),sha256=sha(p)) for p in (R/'source_before').rglob('*') if p.is_file()],seconds=time.perf_counter()-t)
 (R/'freeze.json').write_text(json.dumps(rec,indent=2)+'\n');print(json.dumps({k:v for k,v in rec.items() if k not in ['files','source_before_binding']}))
if __name__=='__main__':main()
