from common import *
BINARY_SHA='4ca4af2d896a13ef8dc785dda73be11707e22a383fc3ced6f037b6ba2d9c49e2'

def validate_config(c):
 n=c['num_queries'];assert isinstance(n,int) and n>=16;assert c['threads']==1 and c['query_cpu']==15 and c['timing_repeats']==5 and c['gt_k']==100
 assert c.get('input_total_rows',n)==n,'Use exact final input shape; prefix configs are not accepted here'
 ms=c['methods'];assert len(ms)==len({m['name'] for m in ms});names=None
 for L in LS:
  current=[m['model_name'] for m in ms if m['L']==L];assert len(current)==len(set(current)) and current
  if names is None:names=current
  assert current==names,'Same methods and initial order at every L required'
 assert len(ms)==len(names)*len(LS)
 for m in ms:
  assert m['name']==m['model_name']+'_L'+str(m['L']) and m['dim']==c['dim'];assert not m.get('component_wall',False) and not m.get('exact',False)
  assert m.get('distinct_hub_width',0)==0 and not m.get('adaptive_distinct',False),'E73 binary has no distinct callback'
  assert m['family'] in ['nsg','profile','fast30k_3'] and m.get('reference_graph') is True
  if m['family']=='nsg':assert m['k']==1
  else:
   assert m['k']==3 and m.get('ef_search',10) in [10,30]
   assert all(m.get(k) for k in ['W','graph_file','mapping','tie_ids'])
   if m.get('multi_profile'):
    assert m.get('slot_labels') and m.get('canonical_entry_order');mapping=np.fromfile(m['mapping'],np.int32);hubs,counts=np.unique(mapping,return_counts=True);assert len(mapping)==m['hub_count'] and (mapping>=0).all() and (mapping<c['base_count']).all();assert len(hubs)==m['unique_hub_count']
    assert ((counts>=1)&(counts<=3)).all() if m.get('variable_profiles',False) else (counts==3).all()
 assert c['real_call_cap']==len(ms)*(7*n+16)
 return dict(points=len(ms),NSG=c['real_call_cap'],HNSW=sum(7*n for m in ms if m['family']!='nsg'),wall_batches=5*len(ms))

def signature(m):
 x={k:v for k,v in m.items() if k not in ['name','model_name','L','selected_source_name','display_name']}
 for k in ['W','graph_file','mapping','tie_ids']:
  if k in x:x[k]=sha(x[k])
 return x

def validate_selection_record(sel):
 assert sel['status']=='FINAL_SELECTION_FROZEN' and sel['final_feedback_used'] is False and sel['selection_rule'].strip() and sel['tie_rule'].strip()
 assert all(sel['datasets'][ds].get('best_all') and sel['datasets'][ds].get('best_new') and sel['datasets'][ds].get('best_new_inventory_name') and sel['datasets'][ds].get('inventory_names') for ds in DS)

def validate_frozen(run):
 run=Path(run).resolve();assert run.is_relative_to(C) and run!=O;sel=read(run/'selection.json');validate_selection_record(sel);lock=read(run/'config.locked.json')
 files={x['path']:x for x in read(run/'reviews/prequery_freeze.json')['files']};required=[run/'selection.json',run/'config.locked.json',run/'protocol.md',run/'reviews/base_graph_identity.json',Path(sel['candidate_inventory']),Path(sel['candidate_score_table']),E73/'bin/evaluate']+list((O/'src').glob('*.py'))
 assert lock['threads']==1 and lock['query_cpu']==15 and lock['query_stop']<=1789303200 and lock['latest_launch']<lock['query_stop'] and lock['per_job_seconds']<=1800 and lock['output_cap_MiB']<=64
 assert sha(E73/'bin/evaluate')==BINARY_SHA;inventory=read(sel['candidate_inventory'])['candidates'];metadata=read(C/'session9_final_preparation/matrix_metadata_draft.json');totals=dict(points=0,NSG=0,HNSW=0,wall_batches=0)
 for ds in DS:
  cp=run/'inputs'/ds/'config.json';required.append(cp);c=read(cp);assert c['num_queries']==2000 and c['dataset']==ds and c['dataset_order']==DS.index(ds);assert all(c[k]==metadata['datasets'][ds][k] for k in ['dim','gt_k','base_count','index_path','num_queries']);z=validate_config(c)
  for k in totals:totals[k]+=z[k]
  base={m['model_name']:m for m in c['methods'] if m['L']==64};roles=sel['datasets'][ds];assert roles['best_all'] in base and roles['best_new'] in base
  for m in metadata['datasets'][ds]['required_baselines']:assert signature(base[m['model_name']])==signature(m)
  required_names={m['model_name'] for m in metadata['datasets'][ds]['required_baselines']}
  assert roles['best_new'] not in required_names and roles['inventory_names'][roles['best_new']]==roles['best_new_inventory_name']
  for name in set(base)-required_names:
   entry=next(x for x in inventory if x['dataset']==ds and x['name']==roles['inventory_names'][name]);assert entry['kind']=='new_method' and entry.get('selectable_for_final',True) and not entry.get('zero_update_alias_of'),('ineligible additional model',name)
   assert signature(base[name])==signature(entry['configuration']);assert base[name]['family']!='nsg'
  assert roles['best_all'] in required_names or roles['best_all'] in roles['inventory_names']
  for k in ['queries_file','gt_file','row_ids']:
   expected=metadata['datasets'][ds]['inputs'][k];assert c[k]==expected['path'];st=Path(c[k]).stat();assert(st.st_size,st.st_mtime_ns)==(expected['bytes'],expected['mtime_ns']);required.append(Path(c[k]))
  for m in base.values():required += [Path(m[k]) for k in ['W','graph_file','mapping','tie_ids'] if k in m]
  for m in c['methods']:assert signature(m)==signature(base[m['model_name']]),'Method changed across L'
  assert len({json.dumps(signature(m),sort_keys=True) for m in base.values()})==len(base),'Use explicit roles for aliases, do not measure duplicate configurations'
 for p in required:assert str(p.resolve()) in files,('missing frozen identity',str(p))
 assert totals['NSG']==lock['planned_NSG'] and totals['HNSW']==lock['planned_HNSW'] and totals['points']==lock['points'] and totals['wall_batches']==lock['timing_batches']
 for x in read(run/'reviews/base_graph_identity.json')['sources']:
  st=Path(x['path']).stat();assert(st.st_size,st.st_mtime_ns)==(x['bytes'],x['mtime_ns'])
 # Hashing includes final payloads only after complete selection/config/eligibility checks.
 check(run/'reviews/prequery_freeze.json')
 return lock,totals
