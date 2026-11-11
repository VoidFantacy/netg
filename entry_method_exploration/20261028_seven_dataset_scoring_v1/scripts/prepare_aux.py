import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='8'
import json,sys,time,hashlib,collections
from pathlib import Path
import numpy as np
import faiss
R=Path(__file__).resolve().parents[1]
def dump(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def view(d):
 dim=d['d'];a=np.memmap(d['path'],'<f4','r');start=d.get('row_start',0);n=d['n']
 if d['format']=='fvecs':a=a.reshape(-1,dim+1);assert np.all(a[np.linspace(0,len(a)-1,64,dtype=int),0].view('<i4')==dim);return a[start:start+n,1:]
 if d['format']=='fbin':a=a[2:]
 return a.reshape(-1,dim)[start:start+n]
def gt(d):
 dt='<i8' if d['format']=='raw_i64' else '<i4';a=np.memmap(d['path'],dt,'r').reshape(-1,101 if d['format']=='ivecs' else 100);return a[d.get('row_start',0):][:d['n'],1 if d['format']=='ivecs' else 0:]
def main():
 ds=sys.argv[1];t=time.perf_counter();c=json.loads((R/f'configs/{ds}.json').read_text());root=Path(c['models']);root.mkdir();N,d=c['base']['n'],c['base']['d'];M=c['PQ_M'];faiss.omp_set_num_threads(8);base=view(c['base']);cost={};files={}
 if 'existing_blocks' in c:
  b=Path(c['existing_blocks']);book=Path(c['existing_backend'])/'codebooks.f32';files=dict(ids=str(b/'block_ids.i32'),offsets=str(b/'block_offsets.u64'),centres=str(b/'block_centres.f32'),pq_codes=str(b/'block_codes.u8'),book=str(book),id_block=str(Path(c['existing_reuse'])/'id_block.i32'),hub_blocks=str(Path(c['existing_reuse'])/'hub_blocks.i32'));old_reused=True
 else:
  old_reused=False;sample=np.random.default_rng(20261028).choice(N,min(N,65536),False);x=np.asarray(base[sample],dtype='float32');sample.astype('<i4').tofile(root/'training_base_ids.i32');km=faiss.Clustering(d,1024);km.niter=20;km.seed=20261028;km.spherical=c['metric_id']==0
  quant=faiss.IndexFlatL2(d) if c['metric_id']==1 else faiss.IndexFlatIP(d);started=time.perf_counter();km.train(x,quant);cent=faiss.vector_to_array(km.centroids).reshape(1024,d);cent.astype('<f4').tofile(root/'coarse_centres.f32');quant.reset();quant.add(cent);cost['coarse_seconds']=time.perf_counter()-started
  pq=faiss.ProductQuantizer(d,M,8);pq.cp.niter=20;pq.cp.seed=20261028;started=time.perf_counter();pq.train(x);book=faiss.vector_to_array(pq.centroids).reshape(M,256,d//M);book.astype('<f4').tofile(root/'codebooks.f32');cost['PQ_train_seconds']=time.perf_counter()-started
  started=time.perf_counter();regions=np.empty(N,dtype='int32');codes=np.empty((N,M),dtype='uint8');stream=hashlib.sha256()
  for lo in range(0,N,32768):
   hi=min(N,lo+32768);v=np.ascontiguousarray(base[lo:hi]);assert np.isfinite(v).all();stream.update(v.tobytes());regions[lo:hi]=quant.search(v,1)[1][:,0];codes[lo:hi]=pq.compute_codes(v)
   if lo//32768%32==0:print(json.dumps(dict(dataset=ds,stage='PQ encode/partition',rows=hi,N=N)),flush=True)
  cost['encode_seconds']=time.perf_counter()-started;cost['base_consumed_vector_sha256']=stream.hexdigest();order=np.argsort(regions,kind='stable').astype('int32');roff=np.r_[0,np.cumsum(np.bincount(regions,minlength=1024))];boff=[0];bc=[];started=time.perf_counter()
  with (root/'block_ids.i32').open('xb') as fi,(root/'block_codes.u8').open('xb') as fc:
   for reg in range(1024):
    orig=order[roff[reg]:roff[reg+1]];cr=codes[orig];v=np.concatenate([book[m,cr[:,m]] for m in range(M)],axis=1)
    def split(a):
     if len(a)<=128:
      if not len(a):return
      a=np.sort(a);orig[a].astype('<i4').tofile(fi);cr[a].tofile(fc);bc.append(v[a].mean(0,dtype='float64').astype('<f4'));boff.append(boff[-1]+len(a));return
     axis=int(np.argmax(v[a].var(0,dtype='float64')));a=a[np.argsort(v[a,axis],kind='stable')];mid=len(a)//2;split(a[:mid]);split(a[mid:])
    split(np.arange(len(orig)))
    if reg%256==0:print(json.dumps(dict(dataset=ds,stage='block partition',regions=reg,blocks=len(bc))),flush=True)
  np.asarray(boff,'<u8').tofile(root/'block_offsets.u64');np.asarray(bc,'<f4').tofile(root/'block_centres.f32');cost['block_seconds']=time.perf_counter()-started
  files=dict(ids=str(root/'block_ids.i32'),offsets=str(root/'block_offsets.u64'),centres=str(root/'block_centres.f32'),pq_codes=str(root/'block_codes.u8'),book=str(root/'codebooks.f32'),id_block=str(root/'id_block.i32'),hub_blocks=str(root/'hub_blocks.i32'))
 ids=np.fromfile(files['ids'],'<i4');off=np.fromfile(files['offsets'],'<u8').astype('int64');assert len(ids)==N and np.array_equal(np.sort(ids),np.arange(N));assert (np.diff(off)>0).all() and np.diff(off).max()<=128
 inverse=np.empty(N,dtype='<i4');inverse[ids]=np.repeat(np.arange(len(off)-1,dtype='<i4'),np.diff(off))
 if old_reused:assert np.array_equal(inverse,np.fromfile(files['id_block'],'<i4'))
 else:inverse.tofile(files['id_block'])
 # Rebuild all 12K training counts, even for reused rows, without any test labels.
 td=Path(c['teacher_dir'])/'raw';teacher=np.memmap(td/'ids.i32','<i4','r').reshape(-1,100)[:12000];ent=np.memmap(td/'entry_ids.i32','<i4','r').reshape(-1,3)[:12000];g=gt(c['train_gt'])[:12000];hubs=np.fromfile(c['router']['ids'],'<i4');slots={int(h):i for i,h in enumerate(hubs)};count=[collections.Counter() for h in hubs];missing=0
 for i in range(12000):
  found=set(map(int,teacher[i]));absent=[int(v) for v in g[i] if int(v) not in found];missing+=len(absent);row=collections.Counter(map(int,inverse[absent]));assert len(set(map(int,ent[i])))==3
  for h in ent[i]:count[slots[int(h)]].update(row)
 tab=np.full((len(hubs),8),-1,dtype='<i4')
 for i,row in enumerate(count):
  for j,(key,v) in enumerate(sorted(row.items(),key=lambda v:(-v[1],v[0]))[:8]):tab[i,j]=key
 if old_reused:assert np.array_equal(tab,np.fromfile(files['hub_blocks'],'<i4').reshape(-1,8))
 else:tab.tofile(files['hub_blocks'])
 if 'existing_sq8' in c:files.update(sq_codes=str(Path(c['existing_sq8'])/'block_sq8.u8'),sq_trained=str(Path(c['existing_sq8'])/'trained.f32'))
 else:files.update(sq_codes=str(root/'block_sq8.u8'),sq_trained=str(root/'trained.f32'))
 # Exact row-byte role checks are descriptive, not semantic independence.
 train=view(c['train_queries']);test=view(c['queries']);a={hashlib.sha256(np.ascontiguousarray(v).tobytes()).digest() for v in train[:12000]};b={hashlib.sha256(np.ascontiguousarray(v).tobytes()).digest() for v in train[12000:16000]};z={hashlib.sha256(np.ascontiguousarray(v).tobytes()).digest() for v in test};assert not a&b and not a&z and not b&z
 model=dict(status='PASS_E191_AUX_PREPARATION',dataset=ds,N=N,d=d,M=M,n_blocks=len(off)-1,files=files,blocks_reused=old_reused,training_rows=[0,12000],teacher_missing_member_events=missing,hub_rows_recomputed=len(hubs),fit_cal_exact_vector_overlap=len(a&b),fit_test_exact_vector_overlap=len(a&z),cal_test_exact_vector_overlap=len(b&z),cost=cost,seconds=time.perf_counter()-t,threads=8,query_roles='disjoint source rows; no semantic or blind guarantee',no_pdf=True)
 dump(root/'model.json',model);print(json.dumps({k:v for k,v in model.items() if k not in ['files','cost']}),flush=True)
if __name__=='__main__':main()
