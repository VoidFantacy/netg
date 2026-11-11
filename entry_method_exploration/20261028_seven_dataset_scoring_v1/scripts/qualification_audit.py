import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='1'
import json,collections,time,hashlib
from pathlib import Path
import numpy as np
from io_data import view,gt,read_array
R=Path(__file__).resolve().parents[1];OLD=R.parent/'20261017_gt10_residual_comprehensive_v1'
def main():
 t=time.perf_counter();checks=[]
 for cp in sorted((R/'configs').glob('*.json')):
  if cp.name.count('.')!=1:continue
  c=json.loads(cp.read_text());ds=c['dataset'];n=128;d=c['base']['d'];N=c['base']['n'];M=c['PQ_M'];model=json.loads((Path(c['models'])/'model.json').read_text());files=model['files'];root=R/'storage/qualification'/ds;done=json.loads((root/'complete.json').read_text());assert done['points']==20 and done['batches']==20
  hist=json.loads((OLD/f'results/{ds}/complete.json').read_text())['results'];matched=0
  for rr in done['results']:
   m,K,L=rr['method'],rr['K'],rr['L'];p=Path(rr['result_dir'])
   if m in ['GT10','B32']:
    hm=('GT10-soft-t1' if c['family']=='soft' else 'GT10-hard') if m=='GT10' else c['family']+'-JOINT32';old=next(v for v in hist if v['method']==hm and v['K']==K and v['L']==L)
    for name in ['ids.i32','distances.f32','entry_ids.i32','profile_distances.f32']:
     b=(p/'raw'/name).read_bytes();assert (Path(old['result_dir'])/'raw'/name).open('rb').read(len(b))==b,(ds,m,K,L,name)
    matched+=1
  q=view(dict(c['queries'],n=n));base=view(c['base']);bid=read_array(files['ids'],'<i4');off=read_array(files['offsets'],'<u8').astype(int);ib=read_array(files['id_block'],'<i4');cent=read_array(files['centres'],'<f4').reshape(-1,d);book=read_array(files['book'],'<f4').reshape(M,256,d//M);pq=np.memmap(files['pq_codes'],'u1','r').reshape(N,M);sq=np.memmap(files['sq_codes'],'u1','r').reshape(N,d);params=read_array(files['sq_trained'],'<f4').reshape(2,d);hubs=read_array(c['router']['ids'],'<i4');slots={int(h):i for i,h in enumerate(hubs)};tab=read_array(files['hub_blocks'],'<i4').reshape(-1,8);sample=np.random.default_rng(20261028).choice(n,16,False)
  # Independent reconstruction of all hub rows, grouping by hub instead of updating query counters.
  teacher=read_array(Path(c['teacher_dir'])/'raw/ids.i32','<i4').reshape(-1,100)[:12000];ent=read_array(Path(c['teacher_dir'])/'raw/entry_ids.i32','<i4').reshape(-1,3)[:12000];g=gt(c['train_gt'])[:12000];missing_blocks=[]
  for i in range(12000):
   found=set(map(int,teacher[i]));missing_blocks.append(ib[[int(z) for z in g[i] if int(z) not in found]])
  for j,h in enumerate(hubs):
   qr=np.flatnonzero((ent==h).any(1));v=np.concatenate([missing_blocks[i] for i in qr]) if len(qr) else np.empty(0,int);keys,cnt=np.unique(v,return_counts=True);order=np.lexsort((keys,-cnt))[:8];expect=np.full(8,-1);expect[:len(order)]=keys[order];assert np.array_equal(expect,tab[j]),(ds,'hub row',j)
  # SQ8 sample encoding is checked against original base values and explicit minmax arithmetic.
  take=np.random.default_rng(20261028).choice(N,min(N,4096),False);v=base[bid[take]];pred=(np.clip((v-params[0])/params[1],0,1)*255).astype('int16');ediff=np.abs(pred-sq[take].astype('int16'));assert ediff.max()<=1
  for rr in done['results']:
   m,K,L=rr['method'],rr['K'],rr['L'];p=Path(rr['result_dir']);out=read_array(p/'raw/ids.i32','<i4').reshape(n,K);dist=read_array(p/'raw/distances.f32','<f4').reshape(n,K)
   for i in sample:
    x=base[out[i]].astype('float64');qi=q[i].astype('float64');score=((x-qi)**2).sum(1) if c['metric_id']==1 else -(x*qi).sum(1);assert np.all(np.abs(score-dist[i])<=5e-5+3e-6*np.abs(score)),(ds,m,K,L,'native metric')
   if m in ['GT10','B32']:continue
   trace=read_array(p/'trace.i32','<i4').reshape(n,160);access=read_array(p/'access.u64','<u8').reshape(n,5);main=read_array(root/f'k{K}/GT10_L{L}/raw/ids.i32','<i4').reshape(n,K);routes=read_array(root/f'k{K}/GT10_L{L}/raw/entry_ids.i32','<i4').reshape(n,3)
   if m=='REUSE-SQ':assert np.array_equal(trace[:,:64],read_array(root/f'k{K}/REUSE-PQ_L{L}/trace.i32','<i4').reshape(n,160)[:,:64])
   for i in sample:
    count=collections.Counter(map(int,ib[main[i]]));pool=set(k for k,v in sorted(count.items(),key=lambda v:(-v[1],v[0]))[:8])
    if m!='MAIN-SQ':
     for h in routes[i]:pool.update(int(z) for z in tab[slots[int(h)]] if z>=0)
    pool=np.array(sorted(pool));assert pool.tolist()==trace[i,:32][trace[i,:32]>=0].tolist();x=cent[pool].astype('float64');qi=q[i].astype('float64');score=((x-qi)**2).sum(1) if c['metric_id']==1 else -(x*qi).sum(1);selected=[];consumed=0
    for b in pool[np.lexsort((pool,score))]:
     le=off[b+1]-off[b]
     if consumed+le<=2048:selected.append(int(b));consumed+=le
    assert selected==trace[i,32:64][trace[i,32:64]>=0].tolist() and consumed==access[i,0]
    loc=np.concatenate([np.arange(off[b],off[b+1]) for b in selected]);ids=bid[loc];keep=~np.isin(ids,main[i]);loc=loc[keep];ids=ids[keep]
    if m=='REUSE-PQ':
     approx=np.zeros(len(loc))
     for j in range(M):
      v=book[j].astype('float64');qq=qi[j*(d//M):(j+1)*(d//M)];lut=((v-qq)**2).sum(1) if c['metric_id']==1 else -(v*qq).sum(1);approx+=lut[pq[loc,j]]
    else:
     v=(sq[loc].astype('float32')+.5)/np.float32(255)*params[1]+params[0];v=v.astype('float64');approx=((v-qi)**2).sum(1) if c['metric_id']==1 else -(v*qi).sum(1)
    short=trace[i,64:][trace[i,64:]>=0];assert len(short)==min(96,len(ids)) and np.isin(short,ids).all();mask=np.isin(ids,short)
    if (~mask).any():assert approx[mask].max()<=approx[~mask].min()+5e-5+3e-6*abs(approx[mask].max()),(ds,m,K,L,'shortlist')
  checks.append(dict(dataset=ds,qualification_points=20,historical_prefix_packets_equal=matched,true_K1_only_one_main_return=True,hub_rows_independently_rebuilt=len(hubs),SQ8_encoding_sample_rows=len(take),SQ8_encoding_max_code_difference=int(ediff.max()),sample_queries_per_point=len(sample),pool_block_budget_and_score_checks=True))
 out=dict(status='PASS_E191_QUALIFICATION_SECOND_IMPLEMENTATION',checks=checks,seconds=time.perf_counter()-t,scope='same executing operator; separate implementations, not independent personnel')
 (R/'reviews/qualification_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out),flush=True)
if __name__=='__main__':main()
