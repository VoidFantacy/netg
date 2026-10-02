from pathlib import Path
import json, hashlib, shutil, time, subprocess
R=Path('/data/netg/ACSG'); O=R/'entry_method_exploration/20260911_gt10_shared_transform_v1'
E24=R/'entry_method_exploration/20260910_gt_topk_profiles_v1'
E23=R/'entry_method_exploration/20260910_three_entry_rank_v1'
E27=R/'entry_method_exploration/20260911_gt10_mechanism_v1/supplement'
DS=['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1']
def dump(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2)+'\n')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def identity(p):
 p=Path(p);s=p.stat();return dict(path=str(p),bytes=s.st_size,mtime_ns=s.st_mtime_ns,sha256=sha(p))
if __name__=='__main__':
 assert not (O/'reviews/protocol_lock.json').exists()
 dump(O/'reviews/protocol_lock.json',dict(timestamp=time.time(),protocol=identity(O/'protocol.md'),real_search_calls=0,training_runs=0))
 for name in ['legacy_reference.cpp','benchmark_with_nsg.cpp','evaluate.cpp']:shutil.copy2(E27/'src'/name,O/'src'/name)
 protected=[]
 for root in [E23,E24,E27.parent]:
  for p in sorted(root.rglob('*')):
   if p.is_file():
    s=p.stat();protected.append(dict(path=str(p),bytes=s.st_size,mtime_ns=s.st_mtime_ns,sha256=sha(p)))
 for ds in DS:
  prep=json.loads((E24/'inputs'/ds/'prepared.json').read_text())
  for name in ['base_file','index_path']:protected.append(identity(prep[name]))
  for split in ['fit','cal','audit','validation']:
   c=json.loads((E24/'inputs'/ds/split/'config.json').read_text())
   c.update(query_cpu=15,protocol_sha256=sha(O/'protocol.md'))
   dump(O/'inputs'/ds/split/'config.json',c)
  # Compatibility is an identity check; no old cached scores are consumed here.
  for name in ['queries.f32','gt.i64','row_ids.i64']:
   assert sha(E23/'inputs'/ds/'fit'/name)==sha(E24/'inputs'/ds/'fit'/name),(ds,name)
  assert sha(E23/'inputs'/ds/'hub_ids.i32')==sha(E24/'inputs'/ds/'hub_ids.i32')
  old=json.loads((E23/'labels'/ds/'config.json').read_text());assert old['L']==128 and old['index_path']==prep['index_path']
 for p in [R/'ACSG/ACSG.cpp',R/'ACSG/ACSG.h',R/'build/faiss/faiss/libfaiss.a',R/'build/ACSG/libACSG.a',R/'build/MRNN_Descent/libmrnndescent.a']:
  if p.exists():protected.append(identity(p))
 dump(O/'reviews/protected_before.json',protected)
 dump(O/'reviews/preflight.json',dict(status='PASS',cache_input_identity=True,free_bytes=shutil.disk_usage(O).free,protected_files=len(protected)))
 dump(O/'state.json',dict(status='PROTOCOL_LOCKED_IMPLEMENTATION',real_search_calls=0,training_runs=0,heldout_access=False))
 print(json.dumps(dict(status='PASS',protected_files=len(protected))))
