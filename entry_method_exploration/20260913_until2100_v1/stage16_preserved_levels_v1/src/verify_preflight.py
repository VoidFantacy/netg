from verify_candidates import *
threads();ds=sys.argv[1];E73=C/'stage14_compact_modes_v1';c=read(O/'inputs'/ds/'preflight.json');r=read(O/'results'/ds/'preflight/results.json');assert r['status']=='COMPLETE'
gt=np.fromfile(c['gt_file'],np.int64).reshape(7952,100)[:128];scored=recovered=candidate_rows=0
for m in c['methods']:
 p=O/'results'/ds/'preflight'/m['name'];a=load_raw(p,128);name=m['model_name']
 h=np.array([len(set(x.tolist())&set(y[:10].tolist())) for x,y in zip(a['ids'],gt)]);assert np.array_equal(h,a['hits']);scored+=128
 if name!='preserved10':
  old=load_raw(E73/'results'/ds/'aux'/m['name'],7952)
  for k in a:assert a[k].tobytes()==old[k][:128].tobytes(),(ds,name,k)
  recovered+=128
 candidate_rows+=verify_candidates(c,m,p,a,128)
assert all(m['full_plain_count_parity_queries']==128 and m['original_kernel_parity_queries']==16 for m in r['methods'])
dump(O/'reviews'/('preflight_'+ds+'.json'),dict(status='PASS',set_scored_rows=scored,old_recovered_rows=recovered,candidate_rows=candidate_rows,plain_count_rows=384,original_parity_rows=48));print('E75_PREFLIGHT_PASS',ds)
