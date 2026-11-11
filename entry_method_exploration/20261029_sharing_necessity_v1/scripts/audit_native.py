"""Separate stdlib/set implementation of timed quality, support and control checks."""
import array,collections,csv,hashlib,json,math,statistics,struct,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];OLD=R.parent/'20261028_seven_dataset_scoring_v1'
sys.path.insert(0,str(OLD/'scripts'))
from packet_archive import read_bytes
def read(p):return json.loads(Path(p).read_text())
def a(p,k='i'):
 v=array.array(k);v.frombytes(Path(p).read_bytes());return v
def main():
 ds=sys.argv[1];mode=sys.argv[2] if len(sys.argv)>2 else 'results';root=R/'storage'/mode/ds;c=read(root/'config.json');done=read(root/'complete.json');n=c['queries']['n'];N=c['base']['n'];d=c['test_gt'];g=a(d['path'],'q' if d['format']=='raw_i64' else 'i');stride=101 if d['format']=='ivecs' else 100;start=d.get('row_start',0);truth={K:[set(g[(i+start)*stride+(stride==101):(i+start)*stride+(stride==101)+K]) for i in range(n)] for K in [1,100]};hits={};raw={};legacy=0;t=time.perf_counter()
 points={(x['method'],int(x['L'])):x for x in csv.DictReader((R/f'analysis/{ds}/points.csv').open())} if mode=='results' else {}
 for rr in done['results']:
  p=Path(rr['result_dir']);K=rr['K'];m=rr['method'];L=rr['L'];ids=a(p/'raw/ids.i32');dist=a(p/'raw/distances.f32','f');h=hashlib.sha256(struct.pack('<QQ',n,K))
  for name in ['ids.i32','distances.f32','entry_ids.i32','profile_distances.f32']:h.update((p/'raw'/name).read_bytes())
  h.update(bytes(n*16));assert all(x['packet_sha256']==h.hexdigest() and x['threads']==1 for x in rr['rounds'])
  assert len(rr['rounds'])==(1 if mode=='qualification' else 3);ss=[]
  for i in range(n):
   row=ids[i*K:(i+1)*K];dd=dist[i*K:(i+1)*K];assert len(row)==len(set(row))==K and all(0<=v<N for v in row);assert all(math.isfinite(v) for v in dd) and all(x<=y for x,y in zip(dd,dd[1:]));ss.append(set(row)&truth[K][i])
  hits[K,m,L]=ss;raw[K,m,L]=ids
  if mode=='results':
   x=points[m,L];assert sum(map(len,ss))==int(x['hits']);assert sum(len(v)<10 for v in ss)==int(x['failed_lt10']);assert abs(statistics.median(v['qps'] for v in rr['rounds'])-float(x['qps']))<1e-9
  if m!='SHUFFLE-SQ':
   old=OLD/f'storage/results/{ds}/k{K}/{m}_L{L}/raw'
   if old.parent.parent.parent.joinpath('complete.json').exists() and (OLD/f'analysis/{ds}/points.csv').exists():
    available=any(x['K']==str(K) and x['method']==m and x['L']==str(L) for x in csv.DictReader((OLD/f'analysis/{ds}/points.csv').open()))
    if available:
     for name,cols in [('ids.i32',K),('distances.f32',K),('entry_ids.i32',3),('profile_distances.f32',3)]:assert (p/'raw'/name).read_bytes()==read_bytes(old/name)[:n*cols*4],(ds,K,m,L,'E191 same output')
     legacy+=1
  if m not in ['GT10','B32']:
   access=a(p/'access.u64','Q');assert len(access)==n*5 and max(access[0::5])<=2048 and max(access[2::5])<=96
   for j,name in [(0,'scanned_codes'),(1,'block_centres'),(2,'extra_exact_scores'),(3,'PQ_scores'),(4,'SQ_scores')]:assert sum(access[j::5])==rr['rounds'][0][name]
 if mode=='results':
  source=set(a(Path(c['source_dir'])/'global_ids.i32'));model=read(Path(c['models'])/'model.json');ib=a(model['files']['id_block']);pairs={x['method']:x for x in csv.DictReader((R/f'analysis/{ds}/paired.csv').open())};covers={x['method']:x for x in csv.DictReader((R/f'analysis/{ds}/coverage.csv').open())}
  base=hits[100,'GT10',200];mainids=raw[100,'GT10',200]
  for (K,m,L),ss in hits.items():
   if m=='GT10':continue
   new=[z-b for z,b in zip(ss,base)];lost=[b-z for z,b in zip(ss,base)];v=pairs[m]
   assert int(v['members_rescued'])==sum(map(len,new));assert int(v['members_damaged'])==sum(map(len,lost));assert int(v['rescued_source_out'])==sum(len(x-source) for x in new)
   controls=[p for p in points.values() if p['method']=='GT10'];dom=[p['L'] for p in controls if int(p['hits'])>=int(points[m,L]['hits']) and float(p['qps'])>=float(points[m,L]['qps'])];assert v['dominated_by_GT_L']==','.join(dom)
   if m=='B32':assert sum(len(z-source) for z in new)==0;continue
   trace=a(root/f'k100/{m}_L200/trace.i32');cnt=collections.Counter()
   for i in range(n):
    missing=truth[100][i]-set(mainids[i*100:(i+1)*100]);pool=set(trace[i*160:i*160+32]);scan=set(trace[i*160+32:i*160+64]);short=set(trace[i*160+64:(i+1)*160]);cnt['missing_members']+=len(missing);cnt['pool_covered']+=sum(ib[z] in pool for z in missing);cnt['scan_covered']+=sum(ib[z] in scan for z in missing);cnt['shortlist_covered']+=len(missing&short)
   for key,val in cnt.items():assert int(covers[m][key])==val,(ds,m,key)
  pq=a(root/'k100/REUSE-PQ_L200/trace.i32');sq=a(root/'k100/REUSE-SQ_L200/trace.i32');assert all(pq[i*160+j]==sq[i*160+j] for i in range(n) for j in range(64))
  normal=hits[100,'REUSE-SQ',200];shuffled=hits[100,'SHUFFLE-SQ',200];impact=read(R/f'analysis/{ds}/intervention.json');assert impact['normal_minus_shuffled_hits']==sum(len(x)-len(y) for x,y in zip(normal,shuffled))
 v=dict(status='PASS_E192_STDLIB_PACKET_QUALITY_AND_SUPPORT_AUDIT',mode=mode,dataset=ds,points=done['points'],batches=done['batches'],all_native_packet_SHAs_recomputed=True,E191_actual_prefix_or_full_packets_equal=legacy,seconds=time.perf_counter()-t,scope='Different implementation, same operator; no independent personnel or blind-data claim')
 (R/f'reviews/audit_{mode}_{ds}.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v),flush=True)
if __name__=='__main__':main()
