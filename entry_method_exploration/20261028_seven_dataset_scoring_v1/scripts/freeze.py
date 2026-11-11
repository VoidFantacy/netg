import json,hashlib,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];REPO=R.parents[1];OLD=R.parent/'20261028_coco_fixed_candidate_scoring_v1'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 t=time.perf_counter();assert not (R/'freeze.json').exists();assert json.loads((R/'reviews/qualification_audit.json').read_text())['status'].startswith('PASS');files=set();large=[]
 a=json.loads((R/'reviews/build_receipt.json').read_text())['argv'];inc=[x for x in a if x.startswith('-I')];dep=subprocess.check_output(['g++','-std=c++17','-fopenmp',*inc,'-MM',str(R/'src/benchmark.cpp')],cwd=REPO,text=True);(R/'reviews/compile_dependencies.txt').write_text(dep);files.update(Path(p).resolve() for p in dep.replace('\\\n',' ').split(':',1)[1].split())
 for folder in ['src','scripts','configs']:files.update(p.resolve() for p in (R/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
 for x in a:
  if x.endswith(('.a','.o')):files.add((REPO/x).resolve() if not Path(x).is_absolute() else Path(x))
 files.update([R/'storage/benchmark',R/'protocol.md',REPO/'AGENTS.md',R/'reviews/build_receipt.json'])
 datasets=[]
 for p in sorted((R/'configs').glob('*.json')):
  if p.name.count('.')!=1:continue
  c=json.loads(p.read_text());ds=c['dataset'];done=json.loads((R/f'storage/qualification/{ds}/complete.json').read_text());assert done['points']==20 and done['batches']==20
  m=Path(c['models']);model=json.loads((m/'model.json').read_text());files.update(x.resolve() for x in m.iterdir() if x.is_file());files.update(Path(x) for x in model['files'].values());files.update(Path(c['router'][k]) for k in ['ids','W','graph']);files.add(Path(c['table']));files.add(Path(c['source_dir'])/'global_ids.i32')
  for k in ['queries','test_gt','train_queries','train_gt']:files.add(Path(c[k]['path']))
  for k in ['base','index']:
   path=Path(c[k]['path'] if k=='base' else c[k]);s=path.stat();large.append(dict(dataset=ds,role=k,path=str(path),bytes=s.st_size,mtime_ns=s.st_mtime_ns,inode=s.st_ino,authority='inherited E183 original source/GT/index receipts, current stat plus embedded-vector sample check'))
  files.update(Path(c['teacher_dir'])/'raw'/k for k in ['ids.i32','entry_ids.i32']);datasets.append(ds)
 old=json.loads((OLD/'delivery_manifest.json').read_text())
 for v in old['files']:
  p=Path(v['path']);p=p if p.is_absolute() else OLD/p;assert sha(p)==v['sha256'],str(p)
 rec=dict(status='FROZEN_BEFORE_PRIMARY_FORMAL',datasets=datasets,planned_primary_points=448,planned_primary_batches=1344,files=[dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(files)],large_assets=large,old_E190_seal_files_verified=len(old['files']),no_PDF=True,no_configuration_selection=True,seconds=time.perf_counter()-t)
 (R/'freeze.json').write_text(json.dumps(rec,indent=2)+'\n');print(json.dumps({k:v for k,v in rec.items() if k not in ['files','large_assets']}),flush=True)
if __name__=='__main__':main()
