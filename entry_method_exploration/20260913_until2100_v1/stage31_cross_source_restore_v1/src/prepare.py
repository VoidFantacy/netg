from common import *
threads();resources();check(E89/'reviews/final_artifact_freeze.json');paths=[E89/'reviews/final_artifact_freeze.json',O/'protocol.md',C/'session10_resource_protocol_v2.json'];start=time.monotonic()
for ds in DS:
 p=O/'inputs'/ds;p.mkdir();old=read(E89/'inputs'/ds/'aux.json');nc=read(E89/'inputs'/ds/'native_training.json');d=old['dim']
 for key,dt,w,fn in [('queries_file',np.float32,d,'queries.f32'),('gt_file',np.int64,100,'gt.i64'),('row_ids',np.int64,1,'rows.i64')]:
  data=np.fromfile(old[key],dt,count=3976*w);assert data.size==3976*w;data.tofile(p/fn);paths += [Path(old[key]),p/fn]
 rows=np.fromfile(p/'rows.i64',np.int64);assert np.array_equal(rows,np.arange(2048,6024))
 m=next(m for m in old['methods'] if m['model_name']=='compact10');aux=dict(nc,num_queries=3976,queries_file=str(p/'queries.f32'),gt_file=str(p/'gt.i64'),row_ids=str(p/'rows.i64'),native_call_cap=32768)
 fit=dict(nc,native_call_cap=32768);dump(p/'native_support.json',aux);dump(p/'native_fit.json',fit)
 for role,n,cfg in [('support',3976,aux),('fit',20000,fit)]:dump(p/('routes_'+role+'.json'),dict(dataset=ds,threads=1,dim=d,num_queries=n,input_total_rows=n,queries_file=cfg['queries_file'],row_ids=cfg['row_ids'],method=m))
 actions=read(E89/'models'/ds/'selected_actions.json');assert len(actions)==(13 if ds==DS[0] else 8)
 dump(p/'candidates.json',actions)
 for x in actions:assert next(r for r in read(E89/'results'/ds/'fit/action_statistics.json') if r['hub']==x['hub'])['accepted']
 paths += [E89/'models'/ds/'selected_actions.json',E89/'results'/ds/'fit/action_statistics.json']
 for role in ['support','fit']:
  if role=='support':sources=[E89/'results'/ds/'aux'/(m+'_L128') for m in ['baseline10','compact10','restore10']];paths += [p/f for p in sources for f,dt,w in FIELDS.values()]
  else:paths += [E66/'results'/ds/'fit/baseline_L128'/f for f,dt,w in FIELDS.values()]+[E89/'results'/ds/'fit'/(m+'.npz') for m in ['compact_baseline','restore10']]
 for key in ['queries_file','gt_file','row_ids']:paths.append(Path(fit[key]))
 paths += [Path(m[k]) for k in ['W','mapping','tie_ids','graph_file']]
for x in read(E89/'reviews/base_graph_identity.json')['sources']:
 st=Path(x['path']).stat();assert (st.st_size,st.st_mtime_ns)==(x['bytes'],x['mtime_ns'])
shutil.copy2(E89/'reviews/base_graph_identity.json',O/'reviews/base_graph_identity.json')
dump(O/'config.locked.json',dict(training_NSG_cap=65536,per_dataset_training_NSG_cap=32768,training_HNSW_cap=454704,aux_NSG=161920,aux_HNSW=161600,NSG_hard_cap=227456,HNSW_hard_cap=616304,latest_training_launch=1789296300,latest_aux_launch=1789297200,query_hard_stop=1789297680,output_cap_MiB=96,free_min_GiB=6.45,threads=1,CPU=15))
paths += [p for p in (O/'src').glob('*') if p.is_file()]+list((O/'inputs').rglob('*'))+[E89/'bin/routes.so',C/'stage10_exact_triple_utility_v1/bin/inject.so',E73/'bin/evaluate',O/'config.locked.json']
freeze(O/'reviews/pretraining_freeze.json',[p for p in paths if p.is_file()]);dump(O/'logs/training_jobs.json',[]);dump(O/'logs/jobs.json',[])
dump(O/'results/preparation_cost.json',dict(operation_seconds=time.monotonic()-start,compile_seconds=0,new_ANN=0,source_scope='Only support prefix3976 copied; fit references existing exact20K. Historical old aux payload identity hashes include already exposed second half; no new single-action labels there.'))
print('E90_PREPARED',[(ds,len(read(O/'inputs'/ds/'candidates.json'))) for ds in DS])
