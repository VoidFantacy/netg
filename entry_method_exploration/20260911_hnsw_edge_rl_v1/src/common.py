from pathlib import Path
import json,hashlib,shutil,time,os,subprocess
import numpy as np
R=Path('/data/netg/ACSG')
O=R/'entry_method_exploration/20260911_hnsw_edge_rl_v1'
E32=R/'entry_method_exploration/20260911_direct_reward_policy_v1'
E30=R/'entry_method_exploration/20260911_equivalent_teacher_sets_v1'
E28=R/'entry_method_exploration/20260911_gt10_shared_transform_v1'
E24=R/'entry_method_exploration/20260910_gt_topk_profiles_v1'
DS=['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1']
SEEDS=[20260911,20260912]
CAP=1200000
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def identity(p):
 p=Path(p);s=p.stat();return dict(path=str(p),bytes=s.st_size,mtime_ns=s.st_mtime_ns,sha256=sha(p))
def freeze(p,files):
 assert not Path(p).exists(),p
 dump(p,dict(files=[identity(x) for x in sorted(set(map(Path,files)))],time=time.time()))
def check_freeze(p):
 for x in read(p)['files']:assert identity(x['path'])==x,x['path']
def env():
 e=os.environ.copy();e.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1');return e
def resources():
 assert shutil.disk_usage(O).free>=10*(1<<30),'disk free below 10GiB'
 assert sum(p.stat().st_size for p in O.rglob('*') if p.is_file())<=768*(1<<20),'artifact cap'
def reserve(name,calls):
 p=O/'logs/jobs.json';jobs=read(p) if p.exists() else []
 assert sum(x['reserved_calls'] for x in jobs)+calls<=CAP
 assert all(x['name']!=name for x in jobs),name
 jobs.append(dict(name=name,reserved_calls=calls,status='RUNNING',start=time.time()));dump(p,jobs)
def finish(name,calls,status='COMPLETE',**kw):
 p=O/'logs/jobs.json';jobs=read(p);x=next(x for x in jobs if x['name']==name);assert calls<=x['reserved_calls'];x.update(status=status,actual_calls=calls,seconds=time.time()-x['start'],**kw);dump(p,jobs)
def policy(ds):
 c=read(E28/'inputs'/ds/'propose.json');p=c['policies'][1]
 if ds==DS[0]:p=dict(p,W=str(E24/'models'/ds/'gt10_soft_t1/W.f32'),name='gt10_soft',model_name='gt10_soft')
 return p
def score(ids,gt):return (ids[:,:,None]==gt[:,None,:10]).any(1).sum(1).astype(np.uint8)
