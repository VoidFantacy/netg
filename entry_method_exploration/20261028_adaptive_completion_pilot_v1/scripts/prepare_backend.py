#!/usr/bin/env python3
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='8'
from pathlib import Path
import csv,hashlib,json,shutil,sys,time
import faiss,numpy as np
R=Path(__file__).resolve().parents[1];REPO=R.parents[1];OLD=R.parent/'20261017_gt10_residual_comprehensive_v1'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def dump(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def view(d):
 n=d['n'];total=d.get('total_n',n);dim=d['d'];start=d.get('row_start',0)
 if d['format']=='fvecs':
  m=np.memmap(d['path'],'<f4','r',shape=(total,dim+1));assert np.all(m[np.linspace(0,total-1,64,dtype=int),0].view('<i4')==dim);return m[start:start+n,1:]
 return np.memmap(d['path'],'<f4','r',shape=(total,dim))[start:start+n]
def main():
 ds=sys.argv[1];start=time.perf_counter();cfg=json.loads((OLD/f'configs/{ds}.analysis.json').read_text());c=cfg['catalogue_entry']
 root=R/'models'/ds;root.mkdir(exist_ok=False);faiss.omp_set_num_threads(8)
 base=view(c['base']);N,d=base.shape;assert d%16==0
 sample=np.random.default_rng(20261028).choice(N,65536,replace=False);x=np.asarray(base[sample],dtype='float32');sample.astype('<i4').tofile(root/'training_base_ids.i32')
 km=faiss.Clustering(d,1024);km.niter=20;km.seed=20261028;km.spherical=c['metric_id']==0;km.verbose=False
 quant=faiss.IndexFlatL2(d) if c['metric_id']==1 else faiss.IndexFlatIP(d)
 t=time.perf_counter();km.train(x,quant);cent=faiss.vector_to_array(km.centroids).reshape(1024,d);cent.astype('<f4').tofile(root/'centroids.f32');coarse_seconds=time.perf_counter()-t
 quant.reset();quant.add(cent)
 pq=faiss.ProductQuantizer(d,16,8);pq.cp.niter=20;pq.cp.seed=20261028
 t=time.perf_counter();pq.train(x);book=faiss.vector_to_array(pq.centroids).reshape(16,256,d//16);book.astype('<f4').tofile(root/'codebooks.f32');pq_seconds=time.perf_counter()-t
 ids_region=np.empty(N,dtype=np.int32);codes=np.empty((N,16),dtype=np.uint8);consumed=hashlib.sha256();t=time.perf_counter()
 for lo in range(0,N,32768):
  hi=min(N,lo+32768);v=np.ascontiguousarray(base[lo:hi]);assert np.isfinite(v).all();consumed.update(v.tobytes())
  _,idx=quant.search(v,1);ids_region[lo:hi]=idx[:,0];codes[lo:hi]=pq.compute_codes(v)
  if lo//32768%32==0:print(ds,'encoded',hi,'/',N,flush=True)
 encode_seconds=time.perf_counter()-t
 ids_region.astype('<i4').tofile(root/'id_region.i32');order=np.argsort(ids_region,kind='stable').astype(np.int32)
 counts=np.bincount(ids_region,minlength=1024);offset=np.r_[0,np.cumsum(counts)].astype('<u8');offset.tofile(root/'offsets.u64');order.tofile(root/'region_ids.i32')
 with (root/'codes.u8').open('wb') as f:
  for lo in range(0,N,65536):f.write(codes[order[lo:lo+65536]].tobytes())
 assert offset[-1]==N and len(np.unique(order))==N
 # Query identity check is before response/model fitting and does not inspect test quality.
 tq=view(c['train_queries']);vq=view(c['test_queries'])
 th=[hashlib.sha256(np.ascontiguousarray(v).tobytes()).digest() for v in tq]
 vh={hashlib.sha256(np.ascontiguousarray(v).tobytes()).digest() for v in vq}
 assert not set(th[:12000])&set(th[12000:]) and not set(th)&vh
 rt='hard' if ds=='coco' else 'soft';router=next(z for z in c['routers'] if z['name']==rt)
 new=dict(dataset=ds,base=c['base'],index=c['index'],metric_id=c['metric_id'],router=router,threads=1,cpu=15,
  queries=c['test_queries'],test_gt=c['test_gt'],train_queries=c['train_queries'],train_gt=c['train_gt'],
  teacher_dir=cfg['models'][rt]['teacher_dir'],table=str(OLD/f'models/{ds}/compiled/{rt}/tables/JOINT32.bin'),
  backend=str(root.resolve()),output_dir=str((R/'results'/ds).resolve()),
  main_L=[100,128,160,200,256,320,400,512,640,800,1200],completion_L=[100,200,400],
  methods=['GT10','B32','REG-NN','REG-Q','REG-R'],timing_repeats=3,warmup_n=256)
 dump(R/f'configs/{ds}.json',new)
 manifest={p.name:{'bytes':p.stat().st_size,'sha256':sha(p)} for p in root.iterdir() if p.is_file()}
 dump(root/'backend.json',dict(status='PASS_FULL_BASE_BACKEND',dataset=ds,N=N,d=d,nlist=1024,M=16,ksub=256,
  metric_id=c['metric_id'],fit_base_n=65536,base_vector_stream_sha256=consumed.hexdigest(),
  global_PQ_not_residual=True,centroid_spherical=c['metric_id']==0,files=manifest,
  query_exact_byte_overlap_fit_cal=0,query_exact_byte_overlap_train_test=0,
  group_identity_scope=c['training_role_scope'],coarse_seconds=coarse_seconds,pq_seconds=pq_seconds,
  encode_seconds=encode_seconds,elapsed_seconds=time.perf_counter()-start,threads=8,faiss_version=faiss.__version__,
  max_region_size=int(counts.max()),median_region_size=float(np.median(counts))))
 print('PASS',ds,time.perf_counter()-start,flush=True)
if __name__=='__main__':main()
