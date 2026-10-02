from setup import *
import numpy as np
records=[]
for ds in DS:
 c=json.loads((O/'inputs'/ds/'fit/config.json').read_text());dest=O/'labels'/ds;done=json.loads((dest/'complete.json').read_text());n=c['num_queries']
 ids=np.fromfile(dest/'ids.i32',np.int32).reshape(n,56,10);hits=np.fromfile(dest/'hits.u8',np.uint8).reshape(n,56);masks=np.fromfile(dest/'masks.u16',np.uint16).reshape(n,56)
 gt=np.fromfile(c['gt_file'],np.int64).reshape(n,100)[:,:10];checked=0
 for b in range(0,n,128):
  member=(ids[b:b+128,:,:,None]==gt[b:b+128,None,None,:]).any(2)
  rh=member.sum(2);rm=(member*(1<<np.arange(10,dtype=np.uint16))).sum(2)
  assert np.array_equal(rh,hits[b:b+128]) and np.array_equal(rm,masks[b:b+128]);checked+=rh.size
 assert done['physical_calls']+done['reused']==1120000
 records.append(dict(dataset=ds,status='PASS',checked_triples=checked,physical_calls=done['physical_calls'],reused=done['reused'],parity_calls=done['parity_calls']))
dump(O/'reviews/label_verification.json',records);print(json.dumps(records))
