from verify_candidates import *
import csv
threads();check(O/'reviews/preanalysis_freeze.json');total=0;pr=list(csv.DictReader((O/'results/paired.csv').open()));checks=0
for ds in DS:
 c=read(O/'inputs'/ds/'aux.json');gt=np.fromfile(c['gt_file'],np.int64).reshape(-1,100);raw={}
 for m in c['methods']:
  a=load_raw(O/'results'/ds/'aux'/m['name'],7952);raw[m['model_name']]=a
  for i,ids in enumerate(a['ids']):
   assert len(set(ids.tolist()))==10 and np.all((ids>=0)&(ids<c['base_count']))
   mask=sum(1<<j for j,x in enumerate(gt[i,:10]) if x in set(ids.tolist()))
   assert mask==a['mask'][i] and mask.bit_count()==a['hits'][i];total+=1
 raw['mode3P30']=load_raw(C/'stage11_width_control_v1/results'/ds/'aux/mode3P30_L128',7952)
 for r in [x for x in pr if x['dataset']==ds]:
  sl={'all':slice(None),'first_half':slice(0,3976),'second_half':slice(3976,None)}[r['split']]
  a=raw[r['candidate']];b=raw[r['reference']];ah=a['hits'][sl].astype(int);bh=b['hits'][sl].astype(int)
  assert int(r['net_hits'])==sum((ah-bh).tolist())
  assert int(r['failure_change'])==int((ah==0).sum()-(bh==0).sum())
  assert int(r['member_gained'])==sum((int(x)&~int(y)).bit_count() for x,y in zip(a['mask'][sl],b['mask'][sl]))
  assert int(r['member_lost'])==sum((int(y)&~int(x)).bit_count() for x,y in zip(a['mask'][sl],b['mask'][sl]));checks+=1
dump(O/'reviews/independent_verification.json',dict(status='PASS',scalar_set_and_mask_rows=total,paired_member_and_failure_checks=checks));print('E72_INDEPENDENT_PASS',total,checks)
