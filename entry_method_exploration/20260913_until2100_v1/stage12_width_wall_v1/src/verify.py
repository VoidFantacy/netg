from common import *
import csv
threads();start=time.monotonic();points=list(csv.DictReader((O/'results/points.csv').open()));timings=list(csv.DictReader((O/'results/timings.csv').open()));checked=0;slot_checked=0
for ds in DS:
 cfg=read(O/'inputs'/ds/'config.json');gt=np.fromfile(cfg['gt_file'],np.int64).reshape(2048,100)[:,:10];raw=read(O/'results'/ds/'results.json')
 for m in raw['methods']:
  p=O/'results'/ds/m['name'];ids=np.fromfile(p/'ids.i32',np.int32).reshape(2048,10);match=np.any(ids[:,:,None]==gt[:,None,:],axis=1);h=match.sum(1);mask=(match*(1<<np.arange(10))).sum(1)
  assert np.array_equal(h,np.fromfile(p/'hits.u8',np.uint8)) and np.array_equal(mask,np.fromfile(p/'hitmask.u16',np.uint16));checked+=2048
  point=next(x for x in points if x['dataset']==ds and x['model']==m['model_name'] and int(x['L'])==m['L']);tt=[x for x in timings if x['dataset']==ds and x['model']==m['model_name'] and int(x['L'])==m['L']]
  assert len(tt)==5 and int(point['failure_count'])==(h==0).sum() and abs(float(point['recall_pct'])-h.mean()*10)<1e-12
  rates=[2048/float(x['seconds']) for x in sorted(tt,key=lambda x:int(x['repeat']))];assert np.array_equal(rates,np.array(m['qps_runs']));assert float(point['QPS'])==np.median(rates)
  if m['configuration'].get('multi_profile'):
   for L in [64,128,256,400,800]:
    if L==64:continue
    for fn in ['candidate_slots.i32','candidate_distances.f32']:
     assert (O/'results'/ds/f"{m['model_name']}_L64"/fn).read_bytes()==(O/'results'/ds/f"{m['model_name']}_L{L}"/fn).read_bytes()
   slot_checked+=2048
check(O/'reviews/prequery_freeze.json')
dump(O/'reviews/independent_verification.json',dict(status='PASS',vectorized_set_mask_rows=checked,full_wall_points=len(points),full_wall_rounds=len(timings),multi_profile_slot_rows=slot_checked,source_and_config_freeze_unchanged=True,seconds=time.monotonic()-start));print('E71_INDEPENDENT_PASS',checked)
