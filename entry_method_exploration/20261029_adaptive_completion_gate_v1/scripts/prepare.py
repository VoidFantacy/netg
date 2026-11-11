from common import *
import shutil,datetime
from pathlib import Path
prev=R.parent/'20261029_sharing_necessity_v1'
files=read(prev/'delivery_manifest.json')['files'];bad=[]
for f in files:
 p=Path(f['path'])
 if p.stat().st_size!=f['bytes'] or sha(p)!=f['sha256']:bad.append(str(p))
assert not bad,bad
dump(R/'reviews/previous_seal_before.json',dict(status='PASS_ALL_E192_976_SEALED_FILES',count=len(files)))
assets=[]
for ds in ANCHORS:
 c=read(OLD/f'configs/{ds}.json');s=R/'storage/inputs'/ds;s.mkdir(parents=True)
 ids=np.sort(np.random.default_rng(19320261029).choice(c['queries']['n'],2048,replace=False)).astype('<i4');ids.tofile(s/'test_indices.i32')
 for role,qq,gg,sel in [('dev',c['train_queries'],c['train_gt'],slice(12000,16000)),('test',c['queries'],c['test_gt'],ids)]:
  q=np.asarray(view(qq)[sel],dtype='<f4');g=np.asarray(gt(gg)[sel],dtype='<i4');q.tofile(s/f'{role}.f32');g.tofile(s/f'{role}.gt.i32')
  cc=dict(c);cc.update(queries=dict(path=str(s/f'{role}.f32'),format='raw_f32',n=len(q),d=q.shape[1]),test_gt=dict(path=str(s/f'{role}.gt.i32'),format='raw_i32',n=len(q),k=100),Ks=[1,100],GT_L=read(R/'freeze.json')['GT_L'],output_dir=str(R/f'storage/{"labels" if role=="dev" else "formal"}/{ds}'))
  dump(R/f'configs/{ds}.{role}.json',cc)
 for p in [Path(c['base']['path']),Path(c['index'])]:
  st=p.stat();assets.append(dict(path=str(p),bytes=st.st_size,inode=st.st_ino,mtime_ns=st.st_mtime_ns))
 paths=[Path(c['models'])/'model.json',Path(c['table'])]
 m=read(Path(c['models'])/'model.json');paths += [Path(p) for p in m['files'].values() if isinstance(p,str) and Path(p).is_file()]
 for p in paths:
  st=p.stat();assets.append(dict(path=str(p),bytes=st.st_size,inode=st.st_ino,mtime_ns=st.st_mtime_ns,sha256=sha(p)))
dump(R/'reviews/inherited_assets.json',assets)
dump(R/'input_manifest.json',[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted((R/'storage/inputs').rglob('*')) if p.is_file()])
print('E193_INPUTS_FROZEN',flush=True)
