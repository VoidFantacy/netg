from common import *
import csv
threads();jobs=read(O/'logs/jobs.json');assert len(jobs)==2 and all(j['status']=='COMPLETE' for j in jobs)
points=list(csv.DictReader((O/'results/points.csv').open()));paired=list(csv.DictReader((O/'results/paired.csv').open()));members=list(csv.DictReader((O/'results/member_deltas.csv').open()))
count=slotrows=0;raw={}
for ds in DS:
 c=read(O/'inputs'/ds/'config.json');gt=np.fromfile(c['gt_file'],np.int64).reshape(2048,100);q=np.fromfile(c['queries_file'],np.float32).reshape(2048,c['dim'])
 for m in c['methods']:
  p=O/'results'/ds/m['name'];ids=np.fromfile(p/'ids.i32',np.int32).reshape(2048,10);hits=np.fromfile(p/'hits.u8',np.uint8);mask=np.fromfile(p/'hitmask.u16',np.uint16)
  matched=np.any(gt[:,:10,None]==ids[:,None,:],axis=2);assert np.array_equal(matched.sum(1),hits) and np.array_equal((matched*(1<<np.arange(10))).sum(1),mask);count+=2048;raw[ds,m['model_name'],m['L']]=(hits.astype(int),mask)
  if m.get('multi_profile'):
   slots=np.fromfile(p/'candidate_slots.i32',np.int32).reshape(2048,7);dist=np.fromfile(p/'candidate_distances.f32',np.float32).reshape(2048,7);W=np.fromfile(m['W'],np.float32).reshape(-1,c['dim'])
   for b in range(0,2048,128):
    calculated=1-np.einsum('nkd,nd->nk',W[slots[b:b+128]].astype(float),q[b:b+128].astype(float));assert np.allclose(calculated,dist[b:b+128],atol=2e-5,rtol=2e-5)
   slotrows+=2048
   if m['L']==128:
    name=m['selected_source_name'];old=C/'stage14_compact_modes_v1/results'/ds/'aux'/(name+'_L128')
    for fn,dt in [('candidate_slots.i32',np.int32),('candidate_distances.f32',np.float32)]:assert (p/fn).read_bytes()==np.fromfile(old/fn,dt,count=2048*7).tobytes()
 for j in read(O/'results'/ds/'results.json')['methods']:
  rates=2048/np.asarray(j['end_to_end_seconds']);row=next(x for x in points if x['dataset']==ds and x['model']==j['model_name'] and int(x['L'])==j['L']);assert float(row['QPS'])==np.median(rates)
for r,m in zip(paired,members):
 ds=r['dataset'];L=int(r['L']);h,a=raw[ds,'best_new',L];bh,b=raw[ds,r['comparator'],L]
 assert int(r['rescued'])==int(((bh==0)&(h>0)).sum()) and int(r['new_failures'])==int(((bh>0)&(h==0)).sum())
 assert int(r['net_hits'])==int((h-bh).sum())==int(m['GT10_members_gained'])-int(m['GT10_members_lost'])
assert count==112640 and slotrows==40960
dump(O/'reviews/independent_verification.json',dict(status='PASS',broadcast_set_mask_rows=count,all_returned_slot_distance_rows=slotrows,E73_L128_slot_byte_rows=8192,paired_failure_member_checks=len(paired),five_run_QPS_identity=True,actual_threads=[j['peak_threads'] for j in jobs]));print('E74_INDEPENDENT_PASS',count,slotrows)
