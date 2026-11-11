import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='1'
import json,sys,time,collections,csv
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1]
def main():
 mode=sys.argv[1];t=time.perf_counter();p=R/('reviews/qualification_coco' if mode=='qualification' else ('dense_control/coco' if mode=='formal' else 'calibration/coco'));c=json.loads((p/'config.json').read_text());n=c['queries']['n'];d=c['base']['d'];N=c['base']['n'];q=np.memmap(c['queries']['path'],'<f4','r').reshape(-1,d)[c['queries'].get('row_start',0):][:n];base=np.memmap(c['base']['path'],'<f4','r').reshape(N,d)
 bp=Path(c['blocks']);off=np.fromfile(bp/'block_offsets.u64','<u8').astype(int);ids=np.fromfile(bp/'block_ids.i32','<i4');cent=np.fromfile(bp/'block_centres.f32','<f4').reshape(-1,d);pq=np.memmap(bp/'block_codes.u8','u1','r').reshape(N,16);book=np.fromfile(Path(c['backend'])/'codebooks.f32','<f4').reshape(16,256,d//16);ib=np.fromfile(Path(c['reuse'])/'id_block.i32','<i4');tab=np.fromfile(Path(c['reuse'])/'hub_blocks.i32','<i4').reshape(-1,8);hubs=np.fromfile(c['router']['ids'],'<i4');slots={int(h):i for i,h in enumerate(hubs)}
 params=np.fromfile(R/'models/trained.f32','<f4').reshape(2,d);sq=np.memmap(R/'models/block_sq8.u8','u1','r').reshape(N,d);pos=np.empty(N,int);pos[ids]=np.arange(N)
 encode_max=0;encode_diff=0
 if mode=='qualification':
  assert np.array_equal(params[0],base.min(0));assert np.array_equal(params[1],base.max(0)-base.min(0))
  for lo in range(0,N,1024):
   values=base[ids[lo:lo+1024]];z=np.clip((values-params[0])/params[1],0,1);expected=(z*255).astype('int16');delta=np.abs(expected-sq[lo:lo+1024].astype('int16'));encode_max=max(encode_max,int(delta.max()));encode_diff+=int((delta!=0).sum())
  assert encode_max<=1
 checks=[];coverage=[];rng=np.random.default_rng(20261028);sample=rng.choice(n,min(n,32),False)
 done=json.loads((p/'complete.json').read_text());methods=[m for m in c['methods'] if m not in ['GT10','B32']]
 for L in [400]:
  main=np.fromfile(p/f'GT10_L{L}/raw/ids.i32','<i4').reshape(n,100);ent=np.fromfile(p/f'GT10_L{L}/raw/entry_ids.i32','<i4').reshape(n,3);original_trace=np.fromfile(p/f'REUSE-BLOCK_L{L}/trace.i32','<i4').reshape(n,160)
  for method in methods:
   trace=np.fromfile(p/f'{method}_L{L}/trace.i32','<i4').reshape(n,160);assert np.array_equal(trace[:,:64],original_trace[:,:64]),'all query pools / scanned blocks identical';acc=np.fromfile(p/f'{method}_L{L}/access.u64','<u8').reshape(n,3);final=np.fromfile(p/f'{method}_L{L}/raw/ids.i32','<i4').reshape(n,100);dist=np.fromfile(p/f'{method}_L{L}/raw/distances.f32','<f4').reshape(n,100)
   for i in sample:
    count=collections.Counter(map(int,ib[main[i]]));pool=set(k for k,v in sorted(count.items(),key=lambda v:(-v[1],v[0]))[:8])
    for h in ent[i]:pool.update(int(v) for v in tab[slots[int(h)]] if v>=0)
    pool=np.array(sorted(pool));assert pool.tolist()==trace[i,:32][trace[i,:32]>=0].tolist();s=-(cent[pool].astype('float64')*q[i].astype('float64')).sum(1);selected=[];used=0
    for b in pool[np.lexsort((pool,s))]:
     length=off[b+1]-off[b]
     if used+length<=2048:selected.append(int(b));used+=length
    assert selected==trace[i,32:64][trace[i,32:64]>=0].tolist();assert used==acc[i,0]
    loc=np.concatenate([np.arange(off[b],off[b+1]) for b in selected]);cand=ids[loc];keep=~np.isin(cand,main[i]);loc=loc[keep];cand=cand[keep];pqs=np.zeros(len(loc))
    for j in range(16):
     lut=-(book[j].astype('float64')*q[i,j*(d//16):(j+1)*(d//16)].astype('float64')).sum(1);pqs+=lut[pq[loc,j]]
    if method=='REUSE-BLOCK':approx=pqs
    else:
     if method=='PQ384-SQ8':
      chosen=np.argsort(pqs,kind='stable')[:384];loc=loc[chosen];cand=cand[chosen]
     dec=(sq[loc].astype('float32')+.5)/np.float32(255)*params[1]+params[0];approx=-(dec.astype('float64')*q[i].astype('float64')).sum(1)
    shortlist=trace[i,64:][trace[i,64:]>=0];assert len(shortlist)==min(96,len(cand));present=np.isin(cand,shortlist);assert np.isin(shortlist,cand).all()
    if (~present).any():assert approx[present].max()<=approx[~present].min()+5e-5+3e-6*abs(approx[present].max()),(method,L,int(i),'shortlist cutoff')
    native=-(base[final[i]].astype('float64')*q[i].astype('float64')).sum(1);assert np.all(np.abs(native-dist[i])<5e-5+3e-6*np.abs(native))
   checks.append(dict(method=method,L=L,sampled_queries=len(sample),all_query_pool_and_scan_parity=True,shortlist_threshold_checked=True,native_raw_IP_scores_checked=True))
   if mode!='qualification':
    g=c['test_gt'];gt=np.memmap(g['path'],'<i8','r').reshape(-1,100)[g.get('row_start',0):][:n];cnt=collections.Counter()
    for i in range(n):
     absent=set(map(int,gt[i]))-set(map(int,main[i]));poolset=set(map(int,trace[i,:32]));scanset=set(map(int,trace[i,32:64]));short=set(map(int,trace[i,64:]));returned=set(map(int,final[i]));cnt['missing_members']+=len(absent);cnt['pool_covered']+=sum(int(ib[k]) in poolset for k in absent);cnt['scanned_covered']+=sum(int(ib[k]) in scanset for k in absent);cnt['shortlist_covered']+=len(absent&short);cnt['rescued']+=len(absent&returned)
    coverage.append(dict(method=method,L=L,**dict(cnt)))
 rec=dict(status='PASS_E190_SCORING_SECOND_IMPLEMENTATION',role=mode,checks=checks,coverage=coverage,SQ8_all_base_encode_max_code_difference=encode_max if mode=='qualification' else None,SQ8_all_base_encode_differing_components=encode_diff if mode=='qualification' else None,scope='same operator; NumPy float64 diagnostics and separate native oracle; no independent personnel',seconds=time.perf_counter()-t)
 (R/f'reviews/scoring_dense_control_audit.json').write_text(json.dumps(rec,indent=2)+'\n');print(json.dumps({k:v for k,v in rec.items() if k not in ['checks']}),flush=True)
if __name__=='__main__':main()
