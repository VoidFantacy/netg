from pathlib import Path
import json,time,hashlib,resource
import numpy as np
import faiss
RUN=Path(__file__).resolve().parents[1];ROOT=Path("/data/netg/ACSG");LOCK=json.loads((RUN/'config.locked.json').read_text())
assert (RUN/'reviews/query_freeze.json').exists()
faiss.omp_set_num_threads(LOCK['GT_threads']);started=time.time();cost=[]
def dump(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(16<<20),b''):h.update(b)
 return h.hexdigest()
for ds,c in LOCK['datasets'].items():
 begin=time.time();out=RUN/'inputs'/ds;assert not(out/'gt.i32').exists();d=c['dimension'];n=LOCK['n']
 src=ROOT/'benches/datasets'/('WebVid2.5M_light_v1' if ds.startswith('webvid') else 'YandexT2I_official10M_ip_v1')
 name='base.webvid2_5m.fvecs' if ds.startswith('webvid') else 'base.official_first10M.fvecs';basepath=src/name
 source=json.loads((src/'manifest.json').read_text());base_sha=sha(basepath);assert base_sha==source['files'][name]['sha256']
 raw=np.memmap(basepath,dtype='<f4',mode='r').reshape(-1,d+1);assert len(raw)==c['base_n'] and np.all(raw[:,0].view('<i4')==d);base=raw[:,1:]
 q=np.fromfile(out/'queries.f32',dtype='<f4').reshape(n,d);index=faiss.IndexFlatIP(d)
 for j in range(0,len(base),100000):index.add(np.ascontiguousarray(base[j:j+100000]))
 ids=np.empty((n,100),dtype='<i4');dist=np.empty((n,100),dtype='<f4');search_start=time.time()
 for j in range(0,n,256):
  assert time.time()-started<LOCK['GT_seconds_cap'];dd,ii=index.search(q[j:j+256],100);ids[j:j+len(ii)]=ii;dist[j:j+len(ii)]=dd
  dump(RUN/'reviews/gt_progress.json',dict(dataset=ds,completed=min(j+256,n),n=n,seconds=time.time()-search_start));print(ds,min(j+256,n),'GT queries',round(time.time()-search_start,2),'s',flush=True)
 search_seconds=time.time()-search_start;del index
 # Independent float64 block multiplication and top-k merge for 8 predeclared evenly spaced rows.
 checkrows=np.arange(0,n,n//8);qq=q[checkrows].astype(np.float64);bestd=np.full((len(qq),100),-np.inf);besti=np.full((len(qq),100),-1,dtype=np.int64)
 for j in range(0,len(base),65536):
  assert time.time()-started<LOCK['GT_seconds_cap'];bb=base[j:j+65536].astype(np.float64);scores=qq@bb.T
  loc=np.argpartition(scores,-100,axis=1)[:,-100:];values=np.take_along_axis(scores,loc,axis=1);loc+=j
  dd=np.concatenate([bestd,values],axis=1);ii=np.concatenate([besti,loc],axis=1);take=np.argpartition(dd,-100,axis=1)[:,-100:]
  bestd=np.take_along_axis(dd,take,axis=1);besti=np.take_along_axis(ii,take,axis=1)
 verification=[]
 for j,row in enumerate(checkrows):
  expected=set(besti[j].tolist());actual=set(ids[row].tolist());common=len(expected&actual)
  threshold=float(np.min(bestd[j]));actual_scores=np.sum(base[ids[row]].astype(np.float64)*qq[j],axis=1)
  # Float32 Faiss/float64 tie ambiguity is disclosed and must stay within arithmetic tolerance.
  tol=2e-5*max(1.,abs(threshold));assert np.min(actual_scores)>=threshold-tol and len(actual)==100
  assert ids[row,0] in expected and actual_scores[0]>=np.max(bestd[j])-tol
  verification.append(dict(row=int(row),set_overlap=common,minimum_score=float(np.min(actual_scores)),float64_threshold=threshold,tolerance=tol,top1_float64_ok=True))
 ids.tofile(out/'gt.i32');dist.tofile(out/'gt_ip.f32')
 meta=dict(status='PASS_EXACT_GT',dataset=ds,n=n,k=100,metric='raw_inner_product',base=str(basepath),base_sha256=base_sha,query_sha256=sha(out/'queries.f32'),GT_sha256=sha(out/'gt.i32'),faiss_version=faiss.__version__,threads=LOCK['GT_threads'],search_seconds=search_seconds,total_seconds=time.time()-begin,independent_float64=verification,maxrss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
 dump(out/'gt_manifest.json',meta);cost.append(meta);dump(RUN/'reviews/gt_cost.json',cost);print(ds,'GT VERIFIED',flush=True)
 del raw,base,q,ids,dist
dump(RUN/'reviews/gt_complete.json',dict(status='PASS',datasets=len(cost),seconds=time.time()-started,independent_check_queries=8))
