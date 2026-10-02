from pathlib import Path
import hashlib,json,time,os,shutil,sys
import numpy as np
RUN=Path(__file__).resolve().parents[1];ROOT=RUN.parents[1]
LOCK=json.loads((RUN/'config.locked.json').read_text())
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');t.replace(p)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(16<<20),b''):h.update(b)
 return h.hexdigest()
def ident(p):return dict(path=str(p),bytes=Path(p).stat().st_size,sha256=sha(p))
def baseconfig(ds):
 c=LOCK['datasets'][ds]
 return {k:c[k] for k in ['anchor','index','base','base_n','dimension']}|dict(dataset=ds,threads=1,max_search_calls=LOCK['max_search_calls'],seconds_cap=LOCK['job_seconds_cap'])
def prepare(role):
 if role=='accept':
  freeze=read(RUN/'reviews/models_frozen.json')
  for a in freeze['files']:assert sha(a['path'])==a['sha256']
 for order,(ds,c) in enumerate(LOCK['datasets'].items()):
  src=c['fit_source'];d=c['dimension'];lo,hi=LOCK[role+'_positions'];n=hi-lo;out=RUN/'inputs'/ds/role;out.mkdir(parents=True,exist_ok=False)
  # Only materialize/read payload rows assigned to the current role.
  q=np.memmap(src['queries_file'],np.float32,mode='r',shape=(20000,d))[lo:hi].copy();g=np.memmap(src['gt_file'],np.int64,mode='r',shape=(20000,100))[lo:hi].copy();rows=np.memmap(src['row_ids'],np.int64,mode='r',shape=(20000,))[lo:hi].copy()
  assert np.array_equal(rows,np.arange(10000+lo,10000+hi));assert np.isfinite(q).all() and np.all(np.linalg.norm(q,axis=1)>0)
  query_hashes=[hashlib.sha256(v.tobytes()).hexdigest() for v in q];assert len(set(query_hashes))==n
  if role=='accept':assert not set(query_hashes)&set(read(RUN/'inputs'/ds/'fit/query_hashes.json'))
  q.tofile(out/'queries.f32');g.tofile(out/'gt.i64');rows.tofile(out/'row_ids.i64');dump(out/'query_hashes.json',query_hashes)
  cfg=baseconfig(ds)|dict(n=n,queries=str(out/'queries.f32'),gt=str(out/'gt.i64'),row_ids=str(out/'row_ids.i64'))
  if role=='fit':cfg.update(mode='labels',label_repeats=LOCK['label_repeats'],label_block_size=LOCK['label_block_size'],route_reference=str(Path(c['E116_routes'])/'entries.i32'))
  else:cfg.update(mode='evaluate',methods=read(RUN/'models'/ds/'models.json')['methods'],points=LOCK['points'],repeats=LOCK['repeats'],dataset_order=order)
  dump(out/'config.json',cfg);dump(out/'manifest.json',dict(role=role,positions=[lo,hi],historically_exposed=True,original_profile_used_these_rows=True,current_policy_fit=role=='fit',byte_overlap_with_fit=0 if role=='accept' else None,source_paths={k:src[k] for k in ['queries_file','gt_file','row_ids']},files=[ident(out/k) for k in ['queries.f32','gt.i64','row_ids.i64']],assets=[ident(c['anchor'][k]) for k in ['ids','W','graph']],index_stat=c['index_stat']))
 print('PREPARED',role,flush=True)
def predict(nodes,X):
 def rec(j,ix,result):
  node=nodes[j]
  if node['feature']<0:result[ix]=node['action'];return
  keep=X[ix,node['feature']]<=node['threshold'];rec(node['left'],ix[keep],result);rec(node['right'],ix[~keep],result)
 result=np.zeros(len(X),np.int32);rec(0,np.arange(len(X)),result);return result
