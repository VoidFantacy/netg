#!/usr/bin/env python3
"""Separate stdlib implementation of quality, packet identity and budget checks."""
import array,csv,hashlib,json,statistics,struct,time,math
from pathlib import Path
R=Path(__file__).resolve().parents[1];OLD=R.parent/'20261028_completion_cost_budget_v1';SOURCE=R.parent/'20261017_gt10_residual_comprehensive_v1'
def load(p,kind='i'):
 a=array.array(kind)
 with Path(p).open('rb') as f:a.fromfile(f,Path(p).stat().st_size//a.itemsize)
 return a
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 t=time.perf_counter();rows={(r['dataset'],r['method'],int(r['L'])):r for r in csv.DictReader((R/'analysis/points.csv').open())};paired={(r['dataset'],r['method'],int(r['L'])):r for r in csv.DictReader((R/'analysis/paired.csv').open())};checked=0;historical=0;budgets=0;b32=[]
 for ds in ['coco','deep10m_l2_v1']:
  c=json.loads((R/f'configs/{ds}.json').read_text());g=load(c['test_gt']['path'],'q' if c['test_gt']['format']=='raw_i64' else 'i');start=c['test_gt'].get('row_start',0);n=c['queries']['n'];truth=[set(g[(i+start)*100:(i+start+1)*100]) for i in range(n)];source=set(load(SOURCE/f"models/{ds}/compiled/{c['router']['name']}/source/global_ids.i32"));results=json.loads((R/f'results/{ds}/complete.json').read_text())['results'];masks={};rawids={}
  for r in results:
   m,L=r['method'],r['L'];p=Path(r['result_dir']);raw=p/'raw';ids=load(raw/'ids.i32');scores=load(raw/'distances.f32','f');h=hashlib.sha256(struct.pack('<QQ',n,100))
   for name in ['ids.i32','distances.f32','entry_ids.i32','profile_distances.f32']:h.update((raw/name).read_bytes())
   h.update(bytes(n*16));assert all(x['packet_sha256']==h.hexdigest() and x['threads']==1 for x in r['rounds']);assert len(r['rounds'])==3
   previous=OLD/f'results/{ds}/{m}_L{L}/raw'
   if m in ['GT10','B32','BLOCK-R2048'] and previous.exists():
    for name in ['ids.i32','distances.f32','entry_ids.i32','profile_distances.f32']:assert (raw/name).read_bytes()==(previous/name).read_bytes()
    historical+=1
   hits=[]
   for i in range(n):
    v=ids[i*100:(i+1)*100];dd=scores[i*100:(i+1)*100];assert len(set(v))==100 and all(0<=x<c['base']['n'] for x in v);assert all(math.isfinite(x) for x in dd) and all(a<=b for a,b in zip(dd,dd[1:]));hits.append(set(v)&truth[i])
   masks[m,L]=hits;rawids[m,L]=ids;x=rows[ds,m,L];count=sum(map(len,hits));assert count==int(x['hits']) and sum(len(a)<10 for a in hits)==int(x['failed_lt10']);assert abs(statistics.median(z['qps'] for z in r['rounds'])-float(x['qps']))<1e-9
   if m not in ['GT10','B32']:
    a=load(p/'access.u64','Q');cap=2048;assert len(a)==n*3 and max(a[0::3])<=cap and max(a[2::3])<=96;assert sum(a[0::3])==r['rounds'][0]['scanned_codes'];budgets+=1
   checked+=1
  for (m,L),hh in masks.items():
   if m=='GT10':continue
   base=masks['GT10',L];cnt={k:0 for k in ['members_missing','members_rescued','members_damaged','rescued_source_out','rescued_source_in','improved_queries','worsened_queries','full_recovered_queries','original_lt10','final_lt10','lt10_improved','lt10_escaped','new_lt10','rescued_from_original_lt10']}
   for a,z in zip(base,hh):
    new=z-a;lost=a-z;cnt['members_missing']+=100-len(a);cnt['members_rescued']+=len(new);cnt['members_damaged']+=len(lost);cnt['rescued_source_out']+=len(new-source);cnt['rescued_source_in']+=len(new&source);cnt['improved_queries']+=len(z)>len(a);cnt['worsened_queries']+=len(z)<len(a);cnt['full_recovered_queries']+=len(z)==100 and len(a)<100;cnt['original_lt10']+=len(a)<10;cnt['final_lt10']+=len(z)<10;cnt['lt10_improved']+=len(a)<10 and len(z)>len(a);cnt['lt10_escaped']+=len(a)<10 and len(z)>=10;cnt['new_lt10']+=len(a)>=10 and len(z)<10;cnt['rescued_from_original_lt10']+=len(new) if len(a)<10 else 0
   for k,v in cnt.items():assert int(paired[ds,m,L][k])==v,(ds,m,L,k)
  # B32 exact callback count independently recovered from immutable table.
  blob=Path(c['table']).read_bytes();head=struct.unpack_from('<8I',blob,8);H,b=head[1:3];labs=struct.unpack_from('<'+str(H)+'i',blob,40);off=40+4*H;counts=blob[off:off+H];off+=H;targets=struct.unpack_from('<'+str(H*b)+'i',blob,off);table={lab:set(targets[i*b:i*b+counts[i]]) for i,lab in enumerate(labs)}
  for L in [100,200,400]:
   routes=load(R/f'results/{ds}/GT10_L{L}/raw/entry_ids.i32');ids=rawids['GT10',L];num=sum(len(set.union(*(table[k] for k in routes[i*3:(i+1)*3]))-set(ids[i*100:(i+1)*100])) for i in range(n));b32.append(dict(dataset=ds,L=L,extra_exact_per_query=num/n))
 frozen=json.loads((R/'freeze.json').read_text());assert all(sha(x['path'])==x['sha256'] for x in frozen['files'])
 for x in frozen['large_assets']:
  s=Path(x['path']).stat();assert (s.st_size,s.st_mtime_ns,s.st_ino)==(x['bytes'],x['mtime_ns'],x['inode'])
 oldman=json.loads((OLD/'delivery_manifest.json').read_text());oldchecked=0
 for x in oldman['files']:
  p=Path(x['path']);p=p if p.is_absolute() else OLD/p;assert sha(p)==x['sha256'];oldchecked+=1
 rec=dict(status='PASS_E189_STDLIB_SECOND_IMPLEMENTATION',points=checked,paired_points=len(paired),formal_batches=checked*3,hard_budget_points=budgets,historical_packets_equal=historical,frozen_inputs_unchanged=True,old_E188_seal_files_unchanged=oldchecked,no_adaptive_selection=True,B32_exact_counts=b32,seconds=time.perf_counter()-t,scope='same operator separate implementation; no independent personnel or blind replication')
 (R/'reviews/results_audit.json').write_text(json.dumps(rec,indent=2)+'\n');print(json.dumps(rec),flush=True)
if __name__=='__main__':main()
