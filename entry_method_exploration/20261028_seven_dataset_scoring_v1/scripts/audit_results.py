"""Independent stdlib implementation of quality, trace coverage and comparisons."""
import array,csv,gzip,hashlib,json,math,statistics,struct,sys,time,collections
from pathlib import Path
R=Path(__file__).resolve().parents[1];OLD=R.parent/'20261017_gt10_residual_comprehensive_v1'
def load(p,k='i'):
 p=Path(p);a=array.array(k)
 if p.exists():
  with p.open('rb') as f:a.fromfile(f,p.stat().st_size//a.itemsize)
 else:a.frombytes(gzip.open(str(p)+'.gz','rb').read())
 return a
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def truth_rows(c):
 d=c['test_gt'];g=load(d['path'],'q' if d['format']=='raw_i64' else 'i');stride=101 if d['format']=='ivecs' else 100;start=d.get('row_start',0);return [list(g[(i+start)*stride+(stride==101):(i+start+1)*stride]) for i in range(d['n'])]
def main():
 ds=sys.argv[1];t=time.perf_counter();root=R/'storage/results'/ds;out=R/'analysis'/ds;c=json.loads((root/'config.json').read_text());done=json.loads((root/'complete.json').read_text());n=c['queries']['n'];N=c['base']['n'];g=truth_rows(c);truth={K:[set(a[:K]) for a in g] for K in [1,100]};source=set(load(Path(c['source_dir'])/'global_ids.i32'));model=json.loads((Path(c['models'])/'model.json').read_text());ib=load(model['files']['id_block']);points={(int(v['K']),v['method'],int(v['L'])):v for v in csv.DictReader((out/'points.csv').open())};pairs={(int(v['K']),v['method'],int(v['L'])):v for v in csv.DictReader((out/'paired.csv').open())};covers={(int(v['K']),v['method'],int(v['L'])):v for v in csv.DictReader((out/'coverage.csv').open())};hitsets={};rawids={};matched=0;hist=json.loads((OLD/f'results/{ds}/complete.json').read_text())['results']
 for rr in done['results']:
  K,m,L=rr['K'],rr['method'],rr['L'];p=Path(rr['result_dir']);ids=load(p/'raw/ids.i32');scores=load(p/'raw/distances.f32','f');h=hashlib.sha256(struct.pack('<QQ',n,K))
  for name in ['ids.i32','distances.f32','entry_ids.i32','profile_distances.f32']:h.update((p/'raw'/name).read_bytes())
  h.update(bytes(n*16));assert len(rr['rounds'])==3 and all(v['packet_sha256']==h.hexdigest() and v['threads']==1 for v in rr['rounds']);hh=[]
  for i in range(n):
   vals=ids[i*K:(i+1)*K];dd=scores[i*K:(i+1)*K];assert len(set(vals))==K and all(0<=a<N for a in vals);assert all(math.isfinite(v) for v in dd) and all(a<=b for a,b in zip(dd,dd[1:]));hh.append(set(vals)&truth[K][i])
  hitsets[K,m,L]=hh;rawids[K,m,L]=ids;x=points[K,m,L];assert sum(map(len,hh))==int(x['hits']);assert abs(sum(map(len,hh))/n/K*100-float(x['recall_pct']))<1e-10;assert int(x['zero_hit_queries'])==sum(not a for a in hh);assert int(x['complete_queries'])==sum(len(a)==K for a in hh)
  if K==100:assert int(x['failed_lt10'])==sum(len(a)<10 for a in hh)
  assert abs(statistics.median(v['qps'] for v in rr['rounds'])-float(x['qps']))<1e-9
  if m in ['GT10','B32']:
   hm=('GT10-soft-t1' if c['family']=='soft' else 'GT10-hard') if m=='GT10' else c['family']+'-JOINT32';old=next((v for v in hist if v['K']==K and v['L']==L and v['method']==hm),None)
   if old:
    for name in ['ids.i32','distances.f32','entry_ids.i32','profile_distances.f32']:assert (p/'raw'/name).read_bytes()==(Path(old['result_dir'])/'raw'/name).read_bytes(),(ds,K,m,L,'historical packet')
    matched+=1
  else:
   a=load(p/'access.u64','Q');assert len(a)==n*5 and max(a[0::5])<=2048 and max(a[2::5])<=96;assert sum(a[0::5])==rr['rounds'][0]['scanned_codes'] and sum(a[2::5])==rr['rounds'][0]['extra_exact_scores'];assert sum(a[3::5])==rr['rounds'][0]['PQ_scores'] and sum(a[4::5])==rr['rounds'][0]['SQ_scores']
 for key,hh in hitsets.items():
  K,m,L=key
  if m=='GT10':continue
  base=hitsets[K,'GT10',L];cnt=collections.Counter()
  for i,(a,z) in enumerate(zip(base,hh)):
   new=z-a;lost=a-z;cnt['members_missing']+=K-len(a);cnt['missing_in_old_source']+=len((truth[K][i]-a)&source);cnt['members_rescued']+=len(new);cnt['members_damaged']+=len(lost);cnt['rescued_source_out']+=len(new-source);cnt['rescued_source_in']+=len(new&source);cnt['improved_queries']+=len(z)>len(a);cnt['worsened_queries']+=len(z)<len(a);cnt['complete_recovered_queries']+=len(z)==K and len(a)<K;cnt['zero_hit_to_hit']+=not a and bool(z)
   if K==100:
    cnt['original_lt10']+=len(a)<10;cnt['final_lt10']+=len(z)<10;cnt['lt10_improved']+=len(a)<10 and len(z)>len(a);cnt['lt10_escaped']+=len(a)<10 and len(z)>=10;cnt['new_lt10']+=len(a)>=10 and len(z)<10
  for name,val in cnt.items():assert int(pairs[key][name])==val,(ds,key,name)
  if m in ['REUSE-PQ','REUSE-SQ','MAIN-SQ']:
   trace=load(root/f'k{K}/{m}_L{L}/trace.i32');cnt=collections.Counter();mainids=rawids[K,'GT10',L]
   if m=='REUSE-SQ':
    other=load(root/f'k{K}/REUSE-PQ_L{L}/trace.i32');assert all(trace[i*160+j]==other[i*160+j] for i in range(n) for j in range(64))
   for i in range(n):
    absent=truth[K][i]-set(mainids[i*K:(i+1)*K]);pool=set(trace[i*160:i*160+32]);scanned=set(trace[i*160+32:i*160+64]);short=set(trace[i*160+64:(i+1)*160]);cnt['members_missing']+=len(absent);cnt['pool_covered']+=sum(ib[z] in pool for z in absent);cnt['scanned_covered']+=sum(ib[z] in scanned for z in absent);cnt['shortlist_covered']+=len(absent&short);cnt['rescued']+=len(absent&hh[i])
   for name,val in cnt.items():assert int(covers[key][name])==val,(ds,key,name)
 comps=list(csv.DictReader((out/'discrete_comparisons.csv').open()))
 for x in comps:
  K=int(x['K']);v=points[K,x['method'],int(x['L'])];controls=[z for (k,m,L),z in points.items() if k==K and m=='GT10'];r=float(v['recall_pct']);q=float(v['qps']);target=[z for z in controls if float(z['recall_pct'])>=r];target=max(target,key=lambda z:float(z['qps'])) if target else None;budget=[z for z in controls if float(z['qps'])>=q];budget=max(budget,key=lambda z:float(z['recall_pct'])) if budget else None;dom=[z for z in controls if float(z['recall_pct'])>=r and float(z['qps'])>=q];assert x['target_GT_L']==(target['L'] if target else '') and x['budget_GT_L']==(budget['L'] if budget else '') and x['dominated_by_GT_L']==','.join(z['L'] for z in dom)
 rec=dict(status='PASS_E191_STDLIB_RESULTS_AUDIT',dataset=ds,points=len(points),batches=3*len(points),paired_points=len(pairs),coverage_points=len(covers),historical_full_packets_equal=matched,all_actual_packet_hashes_recomputed=True,true_K1_GT1_checked=True,all_query_pool_scan_parity=True,strict_GT_ID_counts=True,seconds=time.perf_counter()-t,scope='same operator stdlib implementation; not independent personnel; bootstrap not independently recomputed');(R/f'reviews/results_audit_{ds}.json').write_text(json.dumps(rec,indent=2)+'\n');print(json.dumps(rec),flush=True)
if __name__=='__main__':main()
