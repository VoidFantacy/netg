from common import *
from fit import predict
import struct,array

def main(ds,mode):
 c=read(R/f'configs/{ds}.{mode}.json');done=read(Path(c['output_dir'])/'complete.json');n=c['queries']['n'];q=np.asarray(view(c['queries']),dtype=np.float64);g=np.asarray(gt(c['test_gt']))[:n];rows=[];oldc=read(OLD/f'configs/{ds}.json');ind=np.fromfile(R/f'storage/inputs/{ds}/test_indices.i32','<i4')[:n]
 for rec in done['results']:
  K=rec['K'];p=Path(rec['result_dir']);ids=arr(p/'raw/ids.i32','<i4').reshape(n,K);D=arr(p/'raw/distances.f32','<f4').reshape(n,K);ent=arr(p/'raw/entry_ids.i32','<i4').reshape(n,3);prof=arr(p/'raw/profile_distances.f32','<f4').reshape(n,3);enabled=arr(p/'enabled.u8','u1');h=hashlib.sha256(struct.pack('<QQ',n,K))
  for name in ['ids.i32','distances.f32','entry_ids.i32','profile_distances.f32']:h.update((p/'raw'/name).read_bytes())
  h.update(bytes(n*16));assert all(v['packet_sha256']==h.hexdigest() and v['threads']==1 for v in rec['rounds']);assert len(rec['rounds'])==(3 if mode=='formal' else 1)
  hits=[]
  for i in range(n):
   il=ids[i].tolist();assert len(set(il))==K and all(0<=x<c['base']['n'] for x in il);assert all(math.isfinite(float(x)) for x in D[i]);assert all(D[i,j]>=D[i,j-1] for j in range(1,K));hits.append(len(set(il)&set(g[i,:K].tolist())))
  hmain=[];resc=0;lost=0;improved=0;damaged=0
  base=Path(c['output_dir'])/f'k{K}/GT10_L200';bi=arr(base/'raw/ids.i32','<i4').reshape(n,K);bd=arr(base/'raw/distances.f32','<f4').reshape(n,K)
  for i in range(n):
   gs=set(g[i,:K].tolist());a=set(bi[i].tolist())&gs;z=set(ids[i].tolist())&gs;resc+=len(z-a);lost+=len(a-z);improved+=len(z)>len(a);damaged+=len(z)<len(a);hmain.append(len(a))
  if rec['method'].startswith('GATE'):
   si=arr(Path(c['output_dir'])/f'k{K}/REUSE-SQ_L200/raw/ids.i32','<i4').reshape(n,K);sd=arr(Path(c['output_dir'])/f'k{K}/REUSE-SQ_L200/raw/distances.f32','<f4').reshape(n,K)
   assert np.array_equal(ids,np.where(enabled[:,None],si,bi));assert np.array_equal(D.view('<i4'),np.where(enabled[:,None],sd,bd).view('<i4'))
   if rec['method']=='GATE-LEARNED':
    z=np.sort(prof.astype(float),axis=1);span=z[:,2]-z[:,0];gap=bd[:,-1].astype(float)-bd[:,0];X=np.c_[z[:,0],z[:,1]-z[:,0],span,(q*q).sum(1),span/(1+abs(z[:,0])),bd[:,0],bd[:,K//4],bd[:,K//2],bd[:,3*K//4],bd[:,-1],gap,gap/(1+abs(bd[:,0].astype(float)))];model=read(c['gate_models'][str(K)]);score=predict(model,X);on=score if score.dtype==bool else score>=model['threshold'];assert np.array_equal(on,enabled.astype(bool)),(ds,K,'Python/C++ gate inference')
   acc=arr(p/'access.u64','<u8').reshape(n,5);sqacc=arr(Path(c['output_dir'])/f'k{K}/REUSE-SQ_L200/access.u64','<u8').reshape(n,5);assert np.array_equal(acc,np.where(enabled[:,None],sqacc,0))
  if rec['L']==200 and rec['method'] in ['GT10','B32','REUSE-SQ']:
   op=Path(oldc['output_dir'])/f'k{K}'/f'{rec["method"]}_L200/raw'
   for name,dt,width in [('ids.i32','<i4',K),('distances.f32','<i4',K),('entry_ids.i32','<i4',3),('profile_distances.f32','<i4',3)]:
    old=arr(op/name,dt).reshape(oldc['queries']['n'],width)[ind];new=arr(p/'raw'/name,dt).reshape(n,width);assert np.array_equal(old,new),(ds,K,rec['method'],name)
  rows.append(dict(dataset=ds,K=K,L=rec['L'],method=rec['method'],n=n,recall=sum(hits)/(n*K),main_recall=sum(hmain)/(n*K),rescued=resc,lost=lost,net_members=resc-lost,improved_queries=improved,damaged_queries=damaged,on_rate=float(enabled.mean()),qps=rec['qps'],qps_min=min(v['qps'] for v in rec['rounds']),qps_max=max(v['qps'] for v in rec['rounds']),wall_us=1e6/rec['qps'],scans_per_query=rec['scans_per_query'],exact_per_query=rec['exact_per_query']))
 csvwrite(R/f'analysis/{ds}.{mode}.csv',rows);dump(R/f'reviews/{ds}.{mode}.audit.json',dict(status='PASS_PYTHON_RECALL_PACKET_SELECTION_INFERENCE_ACCESS_OLD_PARITY',points=len(rows),queries=n,all_packet_hashes=True,true_K=True,old_actual_bytes_equal=True));print('AUDIT_PASS',ds,mode,len(rows),flush=True)
if __name__=='__main__':
 import math
 main(*sys.argv[1:])
