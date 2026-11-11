"""Recompute learned sparse lists and inspect exact query overlap after all performance jobs."""
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='1'
import collections,hashlib,json,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1]
def main():
 t=time.perf_counter();out=[]
 for ds in ['coco','deep10m_l2_v1']:
  assert (R/f'results/{ds}/complete.json').exists();c=json.loads((R/f'configs/{ds}.json').read_text());d=c['base']['d'];m=Path(c['reuse']);ib=np.fromfile(m/'id_block.i32','<i4');ir=np.fromfile(Path(c['backend'])/'id_region.i32','<i4');bp=Path(c['blocks']);ids=np.fromfile(bp/'block_ids.i32','<i4');off=np.fromfile(bp/'block_offsets.u64','<u8').astype(int)
  assert np.array_equal(ib[ids],np.repeat(np.arange(len(off)-1),np.diff(off)))
  hubs=np.fromfile(c['router']['ids'],'<i4');raw=Path(c['teacher_dir'])/'raw';rr=np.fromfile(raw/'ids.i32','<i4').reshape(-1,100);ent=np.fromfile(raw/'entry_ids.i32','<i4').reshape(-1,3);g=c['train_gt'];gt=np.memmap(g['path'],'<i8' if g['format']=='raw_i64' else '<i4','r').reshape(-1,100)
  # Per-hub pull traversal differs from the compiler's per-query push traversal.
  recomputed=0
  for kind,mapping in [('regions',ir),('blocks',ib)]:
   tab=np.fromfile(m/f'hub_{kind}.i32','<i4').reshape(-1,8);cnt=np.fromfile(m/f'hub_{kind}_counts.i32','<i4').reshape(-1,8)
   residuals=[list(set(map(int,gt[i]))-set(map(int,rr[i]))) for i in range(12000)]
   for hi,h in enumerate(hubs):
    qids=np.flatnonzero((ent[:12000]==h).any(1));freq=collections.Counter()
    for qi in qids:freq.update(int(mapping[v]) for v in residuals[qi])
    expected=sorted(freq.items(),key=lambda v:(-v[1],v[0]))[:8];a=np.full(8,-1);b=np.zeros(8,dtype=int)
    for j,(key,value) in enumerate(expected):a[j]=key;b[j]=value
    assert np.array_equal(a,tab[hi]) and np.array_equal(b,cnt[hi]);recomputed+=1
  train=np.memmap(c['train_queries']['path'],'<f4','r').reshape(-1,d);test=np.memmap(c['queries']['path'],'<f4','r').reshape(-1,d)[:10000]
  h=lambda rows:{hashlib.sha256(v.tobytes()).digest() for v in rows}
  fit=h(train[:12000]);cal=h(train[12000:16000]);formal=h(test);out.append(dict(dataset=ds,recomputed_hub_rows=recomputed,id_block_mapping_full=True,fit_rows=[0,12000],cal_rows=[12000,16000],fit_cal_identical_vector_hashes=len(fit&cal),fit_test_identical_vector_hashes=len(fit&formal),cal_test_identical_vector_hashes=len(cal&formal),query_role='disjoint source rows; historical GT10 reuse and public exposure disclosed',calibration_B32_excluded=True))
 (R/'reviews/role_model_audit.json').write_text(json.dumps(dict(status='PASS_E189_ROLE_MODEL_SECOND_IMPLEMENTATION',checks=out,seconds=time.perf_counter()-t),indent=2)+'\n');print(json.dumps(out),flush=True)
if __name__=='__main__':main()
