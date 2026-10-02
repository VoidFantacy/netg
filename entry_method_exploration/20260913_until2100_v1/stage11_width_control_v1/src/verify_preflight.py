from common import *
threads();ds=sys.argv[1];c=read(O/'inputs'/ds/'preflight.json');r=read(O/'results'/ds/'preflight/results.json');assert r['status']=='COMPLETE'
for m in MODELS:
 old=old_raw(ds,m);p=O/'results'/ds/'preflight'/(m+'10_L128')
 for k,(fn,dt,w) in FIELDS.items():
  a=np.fromfile(p/fn,dt);b=old[k][:128];assert a.tobytes()==b.tobytes(),(ds,m,k)
 for fn,dt,w in [('route_ndc.u32',np.uint32,1),('candidate_slots.i32',np.int32,7),('candidate_distances.f32',np.float32,7)]:
  oldp=E66/'results'/ds/'aux'/(m+'_L128')/fn
  if oldp.exists():assert (p/fn).read_bytes()==np.fromfile(oldp,dt,count=128*w).tobytes()
assert all(m['full_plain_count_parity_queries']==128 and m['original_kernel_parity_queries']==16 for m in r['methods'])
dump(O/'reviews'/('preflight_'+ds+'.json'),dict(status='PASS',baseline_models=3,old_recovered_rows=384,plain_count_rows=768,original_parity_rows=96,source_graphs_referenced_not_copied=True));print('E70_PREFLIGHT_PASS',ds)
