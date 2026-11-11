"""Stdlib set/array implementation independent of NumPy analyzer."""
import array,csv,hashlib,json,statistics,struct,time,math,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];OLD=R.parent/'20261028_reuse_completion_routing_v1';SOURCE=R.parent/'20261017_gt10_residual_comprehensive_v1'
def load(p,k='i'):
 a=array.array(k)
 with Path(p).open('rb') as f:a.fromfile(f,Path(p).stat().st_size//a.itemsize)
 return a
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 t=time.perf_counter();role=sys.argv[1];formal=role=='formal';root=R/('results/coco' if formal else 'calibration/coco');out=R/('analysis' if formal else 'calibration_analysis');rows={(x['method'],int(x['L'])):x for x in csv.DictReader((out/'points.csv').open())};pairs={(x['method'],int(x['L'])):x for x in csv.DictReader((out/'paired.csv').open())};c=json.loads((root/'config.json').read_text());n=c['queries']['n'];N=c['base']['n'];g=load(c['test_gt']['path'],'q');start=c['test_gt'].get('row_start',0);truth=[set(g[(i+start)*100:(i+start+1)*100]) for i in range(n)];source=set(load(SOURCE/'models/coco/compiled/hard/source/global_ids.i32'));done=json.loads((root/'complete.json').read_text());masks={};historical=0;bs=[]
 for rr in done['results']:
  m,L=rr['method'],rr['L'];p=Path(rr['result_dir']);ids=load(p/'raw/ids.i32');dd=load(p/'raw/distances.f32','f');h=hashlib.sha256(struct.pack('<QQ',n,100))
  for name in ['ids.i32','distances.f32','entry_ids.i32','profile_distances.f32']:h.update((p/'raw'/name).read_bytes())
  h.update(bytes(n*16));assert all(x['packet_sha256']==h.hexdigest() and x['threads']==1 for x in rr['rounds']);assert len(rr['rounds'])==3
  previous=OLD/('results' if formal else 'calibration')/f'coco/{m}_L{L}/raw'
  if m in ['GT10','B32','REUSE-BLOCK']:
   for name in ['ids.i32','distances.f32','entry_ids.i32','profile_distances.f32']:assert (p/'raw'/name).read_bytes()==(previous/name).read_bytes(),(role,m,L,name)
   historical+=1
  hh=[]
  for i in range(n):
   v=ids[i*100:(i+1)*100];d=dd[i*100:(i+1)*100];assert len(set(v))==100 and all(0<=z<N for z in v);assert all(math.isfinite(x) for x in d) and all(x<=z for x,z in zip(d,d[1:]));hh.append(set(v)&truth[i])
  masks[m,L]=hh;row=rows[m,L];assert sum(map(len,hh))==int(row['hits']);assert sum(len(x)<10 for x in hh)==int(row['failed_lt10']);assert abs(statistics.median(z['qps'] for z in rr['rounds'])-float(row['qps']))<1e-9
  if m not in ['GT10','B32']:
   a=load(p/'access.u64','Q');assert len(a)==n*3 and max(a[0::3])<=2048 and max(a[2::3])<=96;assert sum(a[0::3])==rr['rounds'][0]['scanned_codes'];bs.append((m,L))
   if m!='REUSE-BLOCK':
    z=load(p/'sq_scores.u64','Q');assert len(z)==n and sum(z)==rr['rounds'][0]['sq8_scores'];assert max(z)<= (384 if m=='PQ384-SQ8' else 2048)
 for (m,L),hh in masks.items():
  if m=='GT10':continue
  cnt={k:0 for k in ['members_missing','members_rescued','members_damaged','rescued_source_out','rescued_source_in','improved_queries','worsened_queries','full_recovered_queries','original_lt10','final_lt10','lt10_improved','lt10_escaped','new_lt10','rescued_from_original_lt10']}
  for a,z in zip(masks['GT10',L],hh):
   new=z-a;lost=a-z;cnt['members_missing']+=100-len(a);cnt['members_rescued']+=len(new);cnt['members_damaged']+=len(lost);cnt['rescued_source_out']+=len(new-source);cnt['rescued_source_in']+=len(new&source);cnt['improved_queries']+=len(z)>len(a);cnt['worsened_queries']+=len(z)<len(a);cnt['full_recovered_queries']+=len(z)==100 and len(a)<100;cnt['original_lt10']+=len(a)<10;cnt['final_lt10']+=len(z)<10;cnt['lt10_improved']+=len(a)<10 and len(z)>len(a);cnt['lt10_escaped']+=len(a)<10 and len(z)>=10;cnt['new_lt10']+=len(a)>=10 and len(z)<10;cnt['rescued_from_original_lt10']+=len(new) if len(a)<10 else 0
  for k,v in cnt.items():assert int(pairs[m,L][k])==v,(m,L,k)
 controls=[x for (m,L),x in rows.items() if m=='GT10'];comp=list(csv.DictReader((out/'discrete_comparisons.csv').open()))
 for v in comp:
  x=rows[v['method'],int(v['L'])];quality=float(x['recall_pct']);qps=float(x['qps']);target=[z for z in controls if float(z['recall_pct'])>=quality];target=max(target,key=lambda z:float(z['qps'])) if target else None;budget=[z for z in controls if float(z['qps'])>=qps];budget=max(budget,key=lambda z:float(z['recall_pct'])) if budget else None;dom=[z for z in controls if float(z['recall_pct'])>=quality and float(z['qps'])>=qps];assert v['target_GT_L']==(target['L'] if target else '');assert v['budget_GT_L']==(budget['L'] if budget else '');assert v['dominated_by_GT_L']==','.join(z['L'] for z in dom)
 frozen=json.loads((R/'freeze.json').read_text());assert all(sha(x['path'])==x['sha256'] for x in frozen['files']);old=json.loads((OLD/'delivery_manifest.json').read_text())
 for x in old['files']:
  p=Path(x['path']);p=p if p.is_absolute() else OLD/p;assert sha(p)==x['sha256']
 rec=dict(status='PASS_E190_STDLIB_SECOND_IMPLEMENTATION',role=role,points=len(rows),batches=3*len(rows),paired_points=len(pairs),historical_packets_equal=historical,hard_budget_points=len(bs),old_E189_seal_files_unchanged=len(old['files']),frozen_inputs_unchanged=True,discrete_comparisons_recomputed=len(comp),scope='same operator separate implementation; no independent personnel/blind confirmation',seconds=time.perf_counter()-t)
 (R/f'reviews/{role}_results_audit.json').write_text(json.dumps(rec,indent=2)+'\n');print(json.dumps(rec),flush=True)
if __name__=='__main__':main()
