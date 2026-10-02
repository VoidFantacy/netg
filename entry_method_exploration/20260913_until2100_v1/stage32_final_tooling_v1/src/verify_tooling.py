from scoring import *
import copy,csv
threads();resources();paths=list((O/'src').glob('*.py'))+[O/'protocol.md',C/'session10_resource_protocol_v3.json',E74/'reviews/final_artifact_freeze.json']
paths += [p for ds in DS for folder in [E74/'inputs'/ds,E74/'results'/ds] for p in folder.rglob('*') if p.is_file()]
for ds in DS:
 c=read(E74/'inputs'/ds/'config.json');paths += [Path(c[k]) for k in ['queries_file','gt_file','row_ids']]
 for m in c['methods']:
  paths += [Path(m[k]) for k in ['W','graph_file','mapping','tie_ids'] if k in m]
freeze(O/'reviews/pretest_freeze.json',paths);check(E74/'reviews/final_artifact_freeze.json');started=time.monotonic();records=[];cropped=0;neg=[];allrows={k:[] for k in ['points','timings','paired','failures']}
def reject(label,fn):
 try:fn()
 except (AssertionError,KeyError,ValueError):neg.append(label);return
 raise AssertionError('Mutation not rejected: '+label)
for ds in DS:
 cfg=read(E74/'inputs'/ds/'config.json');result=analyze_dataset(cfg,E74/'results'/ds,{'best_all':'baseline_soft' if ds==DS[0] else 'gt10_hard','best_new':'best_new'});records.append(dict(dataset=ds,**result['verification']))
 for k in allrows:allrows[k].extend(result[k])
 old=list(csv.DictReader((E74/'results/points.csv').open()))
 for p in result['points']:
  expected=next(x for x in old if x['dataset']==ds and x['model']==p['model'] and int(x['L'])==p['L'])
  for k,v in p.items():assert v==expected[k] if isinstance(v,str) else abs(v-float(expected[k]))<1e-9
 gt=np.fromfile(cfg['gt_file'],np.int64).reshape(2048,100)
 for m in cfg['methods']:
  a=raw(E74/'results'/ds/m['name']);scores({k:v[:2000] for k,v in a.items()},gt[:2000],cfg['base_count']);cropped+=2000
 # In-memory 2000 fixture exercises scoring only; no 2000-QPS computed.
 m=cfg['methods'][0];a=raw(E74/'results'/ds/m['name']);bad={k:v[:2000].copy() for k,v in a.items()};bad['ids'][0,1]=bad['ids'][0,0];reject(ds+'_duplicate_id',lambda:scores(bad,gt[:2000],cfg['base_count']))
 bad={k:v[:2000].copy() for k,v in a.items()};bad['ids'][0,0]=-1;reject(ds+'_negative_id',lambda:scores(bad,gt[:2000],cfg['base_count']))
 bad={k:v[:2000].copy() for k,v in a.items()};bad['mask'][0]^=1;reject(ds+'_incorrect_mask',lambda:scores(bad,gt[:2000],cfg['base_count']))
 for label,key,value in [('wrong_threads','threads',2),('wrong_cap','real_call_cap',cfg['real_call_cap']-1),('wrong_cpu','query_cpu',14)]:
  b=copy.deepcopy(cfg);b[key]=value;reject(ds+'_'+label,lambda:validate_config(b))
 b=copy.deepcopy(cfg);b['methods'][1]['distinct_hub_width']=7;reject(ds+'_unsupported_distinct',lambda:validate_config(b))
 b=copy.deepcopy(cfg);b['num_queries']=2000;b['real_call_cap']=len(b['methods'])*(7*2000+16);assert validate_config(b)['NSG']==len(b['methods'])*14016
sample=dict(status='FINAL_SELECTION_FROZEN',final_feedback_used=False,selection_rule='fixture only',tie_rule='fixture only',datasets={ds:dict(best_all='P',best_new='new',best_new_inventory_name='fixture') for ds in DS});validate_selection_record(sample)
for label,key,value in [('unselected','status','DRAFT'),('final_feedback','final_feedback_used',True),('missing_rule','selection_rule',''),('missing_tie','tie_rule','')]:
 s=copy.deepcopy(sample);s[key]=value;reject(label,lambda:validate_selection_record(s))
for k,rows in allrows.items():table(O/'results'/(k+'.csv'),rows)
assert sum(r['set_mask_rows'] for r in records)==112640 and cropped==110000 and sum(r['wall_batches'] for r in records)==275
# Count complete zero unions independently from raw matrices, not from generated rows.
expected_cells=0;unique_queries=set();events=0
for ds in DS:
 cfg=read(E74/'inputs'/ds/'config.json');rows=np.fromfile(cfg['row_ids'],np.int64)
 for L in LS:
  names=[m['name'] for m in cfg['methods'] if m['L']==L];zero=np.stack([np.fromfile(E74/'results'/ds/name/'hits.u8',np.uint8)==0 for name in names]);ix=np.flatnonzero(zero.any(0));events+=len(ix);expected_cells+=len(ix)*len(names);unique_queries.update((ds,int(rows[i])) for i in ix)
assert expected_cells==len(allrows['failures']);dump(O/'results/tooling_verification.json',dict(status='PASS',records=records,old_2048_set_rows=112640,in_memory_2000_score_rows=cropped,negative_guard_tests=neg,existing_wall_batches_verified=275,complete_failure_cells=expected_cells,query_L_zero_union_events=events,unique_zero_union_queries=len(unique_queries),new_ANN=0,new_QPS_points=0,final_payload_opened=False,actual_final_controller_run=False,scope='Existing E74 software reanalysis only. 2000 fixture has no timing/QPS.',seconds=time.monotonic()-started));check(O/'reviews/pretest_freeze.json');resources();print('E91_TOOLING_TESTS_PASS',records,neg,len(allrows['failures']))
