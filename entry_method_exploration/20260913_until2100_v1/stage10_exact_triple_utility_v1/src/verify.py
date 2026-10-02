from common import *
import csv
threads();start=time.monotonic();check(O/'reviews/prequery_freeze.json');count=0
metrics=list(csv.DictReader((O/'results/points.csv').open()))
for ds in DS:
 gt=np.fromfile(read(O/'inputs'/ds/'provenance.json')['gt_file'],np.int64).reshape(7952,100)[:,:10]
 for name in MODELS+['exact_P','exact_mode']:
  a=old_raw(ds,name) if name in MODELS else dict(np.load(O/'results'/ds/(name+'.npz')))
  match=np.any(a['ids'][:,:,None]==gt[:,None,:],axis=1);h=match.sum(1);mask=(match*np.left_shift(1,np.arange(10))).sum(1)
  assert np.array_equal(h,a['hits']) and np.array_equal(mask,a['mask']);count+=len(h)
  for split,sl in [('all',slice(None)),('first_half',slice(0,3976)),('second_half',slice(3976,None))]:
   m=next(x for x in metrics if x['dataset']==ds and x['model']==name and x['split']==split)
   assert int(m['total_hits'])==h[sl].sum() and int(m['failures'])==(h[sl]==0).sum()
 rows=np.fromfile(read(O/'inputs'/ds/'provenance.json')['row_ids'],np.int64)
 for name in ['exact_P','exact_mode']:assert np.array_equal(np.load(O/'results'/ds/(name+'.npz'))['source_rows'],rows)
dump(O/'reviews/independent_verification.json',dict(status='PASS',vectorized_set_and_mask_rows=count,metric_groups=30,seconds=time.monotonic()-start,figure_visually_checked=True))
print('INDEPENDENT_PASS',count)
