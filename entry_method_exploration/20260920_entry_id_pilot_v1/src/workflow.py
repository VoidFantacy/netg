from pathlib import Path
import json,hashlib,time,os,sys,shutil,subprocess
import numpy as np
RUN=Path(__file__).resolve().parents[1];ROOT=RUN.parents[1]
LOCK=json.loads((RUN/'config.locked.json').read_text())
def read(p):return json.loads(Path(p).read_text())
def dump(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n');tmp.replace(p)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(16<<20),b''):h.update(b)
 return h.hexdigest()
def ident(p):return dict(path=str(p),bytes=Path(p).stat().st_size,sha256=sha(p))
def common(ds):
 c=LOCK['datasets'][ds]
 return {k:c[k] for k in ['anchor','index','base','dimension','base_n']}|dict(dataset=ds,threads=1,max_search_calls=LOCK['max_search_calls'],seconds_cap=LOCK['seconds_cap'])
def prepare():
 for ds,c in LOCK['datasets'].items():
  src=c['fit_source'];d=c['dimension'];q=np.fromfile(src['queries_file'],np.float32).reshape(20000,d);g=np.fromfile(src['gt_file'],np.int64).reshape(20000,100);rows=np.fromfile(src['row_ids'],np.int64)
  assert np.array_equal(rows,np.arange(10000,30000)) and np.isfinite(q).all() and np.all(np.linalg.norm(q,axis=1)>0)
  seen=set();parts={'proposal':[],'fit':[]};dropped=[]
  for i,x in enumerate(q):
   b=x.tobytes()
   if b in seen:dropped.append(int(rows[i]));continue
   seen.add(b);parts['proposal' if i<10000 else 'fit'].append(i)
  for role,indices in parts.items():
   out=RUN/'inputs'/ds/role;out.mkdir(parents=True,exist_ok=False);q[indices].tofile(out/'queries.f32');g[indices].tofile(out/'gt.i64');rows[indices].tofile(out/'row_ids.i64')
   cfg=common(ds)|dict(n=len(indices),queries=str(out/'queries.f32'),gt=str(out/'gt.i64'),row_ids=str(out/'row_ids.i64'),mode='route')
   dump(out/'config.json',cfg)
  assets=[ident(c['anchor'][k]) for k in ['ids','W','graph']]
  dump(RUN/'inputs'/ds/'manifest.json',dict(source=[ident(src[k]) for k in ['queries_file','gt_file','row_ids']],assets=assets,parts={k:len(v) for k,v in parts.items()},dropped_duplicate_rows=dropped,role='historically exposed development training',index_stat=c['index_stat'],inherited_index_provenance=str(ROOT/'entry_method_exploration/20260920_wfree_frozen_replication_v1/inputs'/ds/'gt_manifest.json')))
 print('INPUTS_PREPARED',flush=True)
def propose():
 for ds,c in LOCK['datasets'].items():
  p=RUN/'inputs'/ds/'proposal';cfg=read(p/'config.json');n=cfg['n'];d=c['dimension'];q=np.fromfile(p/'queries.f32',np.float32).reshape(n,d);gt=np.fromfile(p/'gt.i64',np.int64).reshape(n,100)
  routes=np.fromfile(RUN/'results'/ds/'route_proposal/entries.i32',np.int32).reshape(n,3);hubs=np.fromfile(c['anchor']['ids'],np.int32);old=set(hubs.tolist());base=np.memmap(c['base'],np.float32,mode='r',shape=(c['base_n'],d+1));slots=[];rankweights=1/np.log2(np.arange(100)+2)
  for h in hubs:
   idx=np.flatnonzero(np.any(routes==h,axis=1))
   if len(idx)<LOCK['proposal_min_support']:continue
   pool,inverse=np.unique(gt[idx].ravel(),return_inverse=True);freq=np.bincount(inverse,weights=np.tile(rankweights,len(idx)));keep=np.array([int(e) not in old for e in pool]);pool=pool[keep];freq=freq[keep]
   assert len(pool)>8
   chosen=pool[np.lexsort((pool,-freq))[:4]].tolist();normq=q[idx].astype(np.float64);normq/=np.linalg.norm(normq,axis=1)[:,None];center=normq.mean(0);vecs=np.asarray(base[pool]);assert np.all(vecs[:,0].view(np.int32)==d)
   score=vecs[:,1:].astype(np.float64)@center
   for j in np.lexsort((pool,-score)):
    e=int(pool[j])
    if e not in chosen:chosen.append(e)
    if len(chosen)==8:break
   assert len(set(chosen))==8 and not set(chosen)&old
   slots.append(dict(old_id=int(h),proposal_support=len(idx),candidates=chosen,source=['weighted_GT100_frequency']*4+['mean_unit_query_raw_IP']*4))
  out=RUN/'models'/ds;out.mkdir(parents=True,exist_ok=False)
  dump(out/'candidates.json',dict(dataset=ds,slots=slots,proposal_config_sha256=sha(p/'config.json'),uses_fit_or_audit_gt=False,scope='fixed 4 frequency plus 4 geometry proposals; not a utility oracle'))
  cfg=read(RUN/'inputs'/ds/'fit/config.json')|dict(mode='labels',routes=str(RUN/'results'/ds/'route_fit/entries.i32'),candidates=str(out/'candidates.json'))
  dump(RUN/'inputs'/ds/'labels_config.json',cfg)
  print('CANDIDATES',ds,len(slots),sum(len(s['candidates']) for s in slots),flush=True)
 dump(RUN/'reviews/candidates_frozen.json',dict(created_unix=time.time(),files=[ident(RUN/'models'/ds/'candidates.json') for ds in LOCK['datasets']]))
def select():
 details=[]
 for ds in LOCK['datasets']:
  p=RUN/'results'/ds/'labels';done=read(p/'complete.json');m=np.fromfile(p/'meta.i32',np.int32).reshape(-1,4);h=np.fromfile(p/'hits.u16',np.uint16).reshape(-1,2).astype(np.float64);t=np.fromfile(p/'seconds.f64',np.float64).reshape(-1,2).mean(1);ndc=np.fromfile(p/'ndc.u64',np.uint64)
  assert len(m)==done['actions']==len(h)==len(t);baseline=np.flatnonzero(m[:,1]<0);assert np.array_equal(m[baseline,0],np.arange(done['n']));base_at=baseline[m[:,0]];delta=h-h[base_at];delta[:,1]/=100;dt=t-t[base_at];cost=[];quality=[];records=[]
  # Validate all labels independently from the stored returned IDs and GT.
  ids=np.memmap(p/'ids.i32',np.int32,mode='r',shape=(len(m),100));cfg=read(p/'config.json');gt=np.fromfile(cfg['gt'],np.int64).reshape(done['n'],100)
  for i in range(done['n']):
   a,b=np.searchsorted(m[:,0],[i,i+1]);x=np.asarray(ids[a:b]);hits=np.isin(x,gt[i],assume_unique=False).sum(1);assert np.array_equal(h[a:b,1],hits) and np.array_equal(h[a:b,0],x[:,0]==gt[i,0])
  keys=np.unique(m[m[:,1]>=0,1:3],axis=0)
  for old,new in keys:
   a=np.flatnonzero((m[:,1]==old)&(m[:,2]==new));folds=[]
   for f in [0,1]:
    ix=a[m[a,3]==f];v=delta[ix].mean(0) if len(ix) else np.full(2,np.nan);st=float(dt[ix].mean()) if len(ix) else None
    folds.append(dict(n=len(ix),delta_r1=float(v[0]) if len(ix) else None,delta_r100=float(v[1]) if len(ix) else None,delta_seconds=st,mean_base_seconds=float(t[base_at[ix]].mean()) if len(ix) else None,delta_ndc=float((ndc[ix].astype(float)-ndc[base_at[ix]]).mean()) if len(ix) else None))
   support=all(f['n']>=LOCK['fit_min_support_per_half'] for f in folds);qok=support and all(f['delta_r1']>=0 and f['delta_r100']>=0 and f['delta_r1']+f['delta_r100']>0 for f in folds);tok=qok and all(f['delta_seconds']<=0 for f in folds)
   value=min((f['delta_r1']+f['delta_r100'])/2 for f in folds) if support else -1
   rec=dict(old_id=int(old),new_id=int(new),folds=folds,support_pass=support,quality_pass=qok,cost_pass=tok,selection_score=value);records.append(rec)
   if qok:quality.append(rec)
   if tok:cost.append(rec)
  models=[]
  for name,candidates in [('Cost',cost),('RecallControl',quality)]:
   usedslots=set();usednew=set();edits=[]
   for x in sorted(candidates,key=lambda a:(-a['selection_score'],a['old_id'],a['new_id'])):
    if x['old_id'] in usedslots or x['new_id'] in usednew:continue
    edits.append([x['old_id'],x['new_id']]);usedslots.add(x['old_id']);usednew.add(x['new_id'])
    if len(edits)==LOCK['max_edits']:break
   models.append(dict(name=name,edits=sorted(edits)))
  dump(RUN/'models'/ds/'models.json',models);dump(RUN/'models'/ds/'selection_details.json',records)
  summary=dict(dataset=ds,actions=len(keys),support_pass=sum(x['support_pass'] for x in records),quality_pass=len(quality),cost_pass=len(cost),models=models)
  details.append(summary);print('SELECTION',json.dumps(summary),flush=True)
 dump(RUN/'reviews/models_frozen.json',dict(created_unix=time.time(),selection=details,files=[ident(RUN/'models'/ds/'models.json') for ds in LOCK['datasets']],audit_payload_read=False))
def audit_inputs():
 frozen=read(RUN/'reviews/models_frozen.json')
 for x in frozen['files']:assert sha(x['path'])==x['sha256']
 for order,(ds,c) in enumerate(LOCK['datasets'].items()):
  src=Path(c['audit_input']);out=RUN/'inputs'/ds/'audit';out.mkdir(exist_ok=False);d=c['dimension'];q=np.fromfile(src/'queries.f32',np.float32).reshape(LOCK['audit_n'],d);g=np.fromfile(src/'gt.i32',np.int32).reshape(LOCK['audit_n'],100).astype(np.int64)
  seen=set()
  for role in ['proposal','fit']:
   a=np.fromfile(RUN/'inputs'/ds/role/'queries.f32',np.float32).reshape(-1,d);seen.update(x.tobytes() for x in a)
  assert len(set(x.tobytes() for x in q))==len(q) and not any(x.tobytes() in seen for x in q)
  q.tofile(out/'queries.f32');g.tofile(out/'gt.i64');models=[dict(name='GT10',edits=[])]+read(RUN/'models'/ds/'models.json')
  cfg=common(ds)|dict(mode='evaluate',queries=str(out/'queries.f32'),gt=str(out/'gt.i64'),n=len(q),models=models,points=LOCK['audit_points'],repeats=LOCK['repeats'],dataset_order=order,audit_reference=c['audit_reference'])
  dump(out/'config.json',cfg);dump(out/'manifest.json',dict(role='previously exposed E105 development audit; no current fitting',source=[ident(src/'queries.f32'),ident(src/'gt.i32')],model_freeze_sha256=sha(RUN/'reviews/models_frozen.json'),byte_overlap_with_current_training=0))
 print('AUDIT_INPUTS_PREPARED_AFTER_FREEZE',flush=True)
if __name__=='__main__':globals()[sys.argv[1]]()
