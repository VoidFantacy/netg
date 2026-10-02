from common import *
threads();groups=[]
for ds in DS:
 rt=np.load(O/'inputs'/ds/'routes.npz');root=E73/'models'/ds;orig=np.fromfile(root/'original_slots.i32',np.int32);inv=np.fromfile(root/'old_to_compact.i32',np.int32);cc=read(C/'stage7_multimode_index_v1/inputs'/ds/'construction.json');hubs=np.fromfile(cc['hub_ids'],np.int32);mapping=np.fromfile(root/'mapping.i32',np.int32);fm=np.repeat(hubs,3);assert np.array_equal(mapping[inv],fm) and np.array_equal(mapping,fm[orig])
 for bi,b in enumerate(BANKS):
  a=np.load(O/'results'/ds/('exact_'+b+'.npz'));old=old_raw(ds,b);near=rt['near_ties'][bi]
  for label,sel in [('near_tie',near),('far_from_tie',~near)]:
   x=a['hits'][sel].astype(int);y=old['hits'][sel].astype(int);groups.append(dict(dataset=ds,bank=b,group=label,n=int(sel.sum()),net_hits=int((x-y).sum()),rescued=int(((y==0)&(x>0)).sum()),new_failures=int(((y>0)&(x==0)).sum()),failure_change=int((x==0).sum()-(y==0).sum())))
table(O/'results/precision_groups.csv',groups);dump(O/'reviews/precision_and_mapping.json',dict(status='PASS',compact_full_W_and_mapping_equivalent=True,exact_reference_float64=True,native_SIMD_bit_parity=False,records=groups))
print(groups)
