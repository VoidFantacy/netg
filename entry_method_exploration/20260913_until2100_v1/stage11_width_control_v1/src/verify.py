from common import *
import csv
threads();ncheck=0;exact_equal=0
for ds in DS:
 c=read(O/'inputs'/ds/'aux.json');gt=np.fromfile(c['gt_file'],np.int64).reshape(7952,100)
 for m in c['methods']:
  p=O/'results'/ds/'aux'/m['name'];ids=np.fromfile(p/'ids.i32',np.int32).reshape(7952,10);hits=np.fromfile(p/'hits.u8',np.uint8)
  h=np.array([len(set(map(int,a))&set(map(int,b[:10]))) for a,b in zip(ids,gt)]);assert np.array_equal(h,hits);ncheck+=7952
  entries=np.fromfile(p/'entry_ids.i32',np.int32).reshape(7952,3);ref=dict(np.load(C/'stage10_exact_triple_utility_v1/results'/ds/('exact_mode.npz' if m['model_name'].startswith('mode') else 'exact_P.npz')))
  ix=np.flatnonzero(np.all(entries==ref['entries'],axis=1));exact_equal+=len(ix)
  for k,fn,dt,w in [('ids','ids.i32',np.int32,10),('distances','distances.f32',np.float32,10),('graph_ndc','graph_ndc.u32',np.uint32,1)]:
   a=np.fromfile(p/fn,dt);a=a.reshape(7952,w) if w>1 else a;assert a[ix].tobytes()==ref[k][ix].tobytes()
dump(O/'reviews/independent_verification.json',dict(status='PASS',scalar_set_scored=ncheck,E69_identical_triple_return_rows=exact_equal,figure_visually_checked=True));print('E70_INDEPENDENT_PASS',ncheck,exact_equal)
