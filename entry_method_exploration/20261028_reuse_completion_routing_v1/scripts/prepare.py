import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='1'
import json,time,hashlib,shutil,collections,datetime
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1];P=R.parent/'20261028_completion_cost_budget_v1';REPO=R.parents[1]
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 assert not (R/'preparation.json').exists();beg=time.perf_counter();old=json.loads((P/'delivery_manifest.json').read_text());checked=0
 for v in old['files']:
  p=Path(v['path']);p=p if p.is_absolute() else P/p
  assert sha(p)==v['sha256'],str(p);checked+=1
 binding=[]
 for n in ['LOCAL_CODEX_START.md','AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md']:
  p=REPO/n;q=R/'source_before'/n;q.parent.mkdir(exist_ok=True,parents=True);shutil.copyfile(p,q);binding.append(dict(path=str(p),sha256=sha(p)))
 dump(R/'reviews/live_docs_binding.json',binding)
 costs=[]
 for ds in ['coco','deep10m_l2_v1']:
  t=time.perf_counter();c=json.loads((P/f'configs/{ds}.json').read_text());m=R/'models'/ds;m.mkdir();b=Path(c['blocks']);N=c['base']['n']
  ids=np.fromfile(b/'block_ids.i32','<i4');off=np.fromfile(b/'block_offsets.u64','<u8').astype(np.int64);ib=np.empty(N,dtype='<i4');ib[ids]=np.repeat(np.arange(len(off)-1,dtype='<i4'),np.diff(off));ib.tofile(m/'id_block.i32')
  assert np.array_equal(np.sort(ids),np.arange(N));assert np.all(np.diff(off)<=128)
  reg=np.fromfile(Path(c['backend'])/'id_region.i32','<i4');hub=np.fromfile(c['router']['ids'],'<i4');slots={int(v):i for i,v in enumerate(hub)}
  td=Path(c['teacher_dir'])/'raw';rr=np.memmap(td/'ids.i32','<i4','r').reshape(-1,100)[:12000];ent=np.memmap(td/'entry_ids.i32','<i4','r').reshape(-1,3)[:12000]
  g=c['train_gt'];gt=np.memmap(g['path'],'<i8' if g['format']=='raw_i64' else '<i4','r').reshape(-1,100)[:12000]
  rc=[collections.Counter() for _ in hub];bc=[collections.Counter() for _ in hub];missing=0
  for i in range(12000):
   absent=[int(v) for v in gt[i] if int(v) not in set(map(int,rr[i]))];missing+=len(absent)
   ar=collections.Counter(map(int,reg[absent]));ab=collections.Counter(map(int,ib[absent]))
   assert len(set(map(int,ent[i])))==3
   for h in ent[i]:rc[slots[int(h)]].update(ar);bc[slots[int(h)]].update(ab)
  for name,counts in [('regions',rc),('blocks',bc)]:
   a=np.full((len(hub),8),-1,dtype='<i4');w=np.zeros((len(hub),8),dtype='<i4')
   for i,row in enumerate(counts):
    v=sorted(row.items(),key=lambda v:(-v[1],v[0]))[:8]
    for j,(key,val) in enumerate(v):a[i,j]=key;w[i,j]=val
   a.tofile(m/f'hub_{name}.i32');w.tofile(m/f'hub_{name}_counts.i32')
  c['reuse']=str(m);c['main_L']=[100,104,112,128,160,200,208,216,224,240,256,288,320,400,416,432,448,480,512,640];c['methods']=['GT10','B32','BLOCK-R2048','REUSE-REG','REUSE-BLOCK','MAIN-BLOCK'];c['output_dir']=str(R/'results'/ds)
  dump(R/f'configs/{ds}.json',c);cal=json.loads(json.dumps(c));cal['queries']=dict(c['train_queries'],row_start=12000,n=4000);cal['test_gt']=dict(c['train_gt'],row_start=12000,n=4000);cal['methods'].remove('B32');cal['output_dir']=str(R/'calibration'/ds);dump(R/f'configs/{ds}.calibration.json',cal)
  q=json.loads(json.dumps(c));q['queries']['n']=128;q['main_L']=[100,200,400];q['output_dir']=str(R/f'reviews/qualification_{ds}');dump(R/f'configs/{ds}.qualification.json',q)
  v=dict(dataset=ds,n_fit=12000,fit_rows=[0,12000],cal_rows=[12000,16000],missing_member_incidences=missing,hub_count=len(hub),blocks=len(off)-1,bytes=sum(p.stat().st_size for p in m.iterdir()),seconds=time.perf_counter()-t,old_assets_reused=True,test_GT_used_for_fit=False,cal_GT_used_for_fit=False)
  dump(m/'fit.json',v);costs.append(v)
 dump(R/'preparation.json',dict(status='PASS_E189_PREPARATION',old_E188_files_verified=checked,models=costs,seconds=time.perf_counter()-beg,timestamp=datetime.datetime.now().isoformat()));dump(R/'state.json',dict(status='IMPLEMENTING',default='E99 GT10 unchanged',authorized_request='继续研究吧'));print(json.dumps(costs),flush=True)
if __name__=='__main__':main()
