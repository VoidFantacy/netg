import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='1'
import json,sys,time,collections,csv
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1]
def main():
 mode=sys.argv[1];records=[];cover=[];t=time.perf_counter()
 for ds in ['coco','deep10m_l2_v1']:
  p=R/(f'reviews/qualification_{ds}' if mode=='qualification' else f'{"results" if mode=="formal" else "calibration"}/{ds}');c=json.loads((p/'config.json').read_text());n=c['queries']['n'];d=c['base']['d'];q=np.memmap(c['queries']['path'],'<f4','r').reshape(-1,d)[c['queries'].get('row_start',0):][:n]
  mr=np.fromfile(p/'GT10_L200/raw/ids.i32','<i4').reshape(n,100);ent=np.fromfile(p/'GT10_L200/raw/entry_ids.i32','<i4').reshape(n,3);model=Path(c['reuse']);ib=np.fromfile(model/'id_block.i32','<i4');tab=np.fromfile(model/'hub_blocks.i32','<i4').reshape(-1,8);hubs=np.fromfile(c['router']['ids'],'<i4');slots={int(h):i for i,h in enumerate(hubs)};bp=Path(c['blocks']);off=np.fromfile(bp/'block_offsets.u64','<u8').astype(int);ids=np.fromfile(bp/'block_ids.i32','<i4');codes=np.memmap(bp/'block_codes.u8','u1','r').reshape(-1,16);cent=np.fromfile(bp/'block_centres.f32','<f4').reshape(-1,d);book=np.fromfile(Path(c['backend'])/'codebooks.f32','<f4').reshape(16,256,d//16)
  sample=np.random.default_rng(20261028).choice(n,min(n,64),False)
  if mode!='qualification':
   g=c['test_gt'];gt=np.memmap(g['path'],'<i8' if g['format']=='raw_i64' else '<i4','r').reshape(-1,100)[g.get('row_start',0):][:n]
  for method in ['REUSE-BLOCK','MAIN-BLOCK']:
   trace=np.fromfile(p/f'{method}_L200/trace.i32','<i4').reshape(n,160);access=np.fromfile(p/f'{method}_L200/access.u64','<u8').reshape(n,3)
   for i in sample:
    counts=collections.Counter(map(int,ib[mr[i]]));pool=set(k for k,v in sorted(counts.items(),key=lambda v:(-v[1],v[0]))[:8])
    if method=='REUSE-BLOCK':
     for h in ent[i]:pool.update(int(v) for v in tab[slots[int(h)]] if v>=0)
    assert list(sorted(pool))==trace[i,:32][trace[i,:32]>=0].tolist();pool=np.array(sorted(pool));x=cent[pool].astype('float64');qi=q[i].astype('float64');scores=((x-qi)**2).sum(1) if c['metric_id']==1 else -(x*qi).sum(1);order=np.lexsort((pool,scores));expected=[];used=0
    for bi in pool[order]:
     length=off[bi+1]-off[bi]
     if used+length<=2048:expected.append(int(bi));used+=length
    selected=trace[i,32:64][trace[i,32:64]>=0].tolist();assert expected==selected,(ds,method,int(i),'block route');assert used==access[i,0] and len(pool)==access[i,1]
    loc=np.concatenate([np.arange(off[b],off[b+1]) for b in selected]);candids=ids[loc];legal=~np.isin(candids,mr[i]);loc=loc[legal];candids=candids[legal];lut=[]
    for j in range(16):
     b=book[j].astype('float64');qq=qi[j*(d//16):(j+1)*(d//16)];lut.append(((b-qq)**2).sum(1) if c['metric_id']==1 else -(b*qq).sum(1))
    approx=np.zeros(len(loc));cc=codes[loc]
    for j in range(16):approx+=lut[j][cc[:,j]]
    short=trace[i,64:][trace[i,64:]>=0];assert len(short)==min(96,len(candids)) and len(set(short))==len(short) and np.isin(short,candids).all();mask=np.isin(candids,short)
    if (~mask).any():assert approx[mask].max()<=approx[~mask].min()+5e-5+3e-6*abs(approx[mask].max()),(ds,method,int(i),'PQ shortlist threshold')
   records.append(dict(dataset=ds,method=method,queries=len(sample),pool_identity=True,original_metric_block_routing=True,whole_block_budget=True,PQ_threshold_float64_tolerance=True))
   if mode!='qualification':
    final=np.fromfile(p/f'{method}_L200/raw/ids.i32','<i4').reshape(n,100);cnt=collections.Counter()
    for i in range(n):
     missing=set(map(int,gt[i]))-set(map(int,mr[i]));pool=set(map(int,trace[i,:32]));selected=set(map(int,trace[i,32:64]));short=set(map(int,trace[i,64:]));returned=set(map(int,final[i]));cnt['missing_members']+=len(missing);cnt['pool_covered']+=sum(int(ib[k]) in pool for k in missing);cnt['scanned_covered']+=sum(int(ib[k]) in selected for k in missing);cnt['shortlist_covered']+=len(missing&short);cnt['rescued']+=len(missing&returned)
    assert cnt['missing_members']>=cnt['pool_covered']>=cnt['scanned_covered']>=cnt['shortlist_covered']>=cnt['rescued'];cover.append(dict(dataset=ds,method=method,L=200,**dict(cnt)))
 out=R/f'reviews/{mode}_trace_audit.json';out.write_text(json.dumps(dict(status='PASS_E189_TRACE_SECOND_IMPLEMENTATION',role=mode,checks=records,coverage=cover,trace='full-sort oracle reconstructed from actual timed main; not separate timed trace',seconds=time.perf_counter()-t),indent=2)+'\n');print(json.dumps(dict(role=mode,coverage=cover,seconds=time.perf_counter()-t)),flush=True)
if __name__=='__main__':main()
