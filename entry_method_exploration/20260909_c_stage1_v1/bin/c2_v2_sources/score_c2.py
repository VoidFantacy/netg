#!/usr/bin/env python3
"""Offline scoring only, after both datasets' complete GT-free branch execution."""
import csv,datetime,hashlib,json
from pathlib import Path
import numpy as np
V=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def dump(p,j):p.write_text(json.dumps(j,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def stats(x):
 x=np.asarray(x,dtype=np.float64)
 return dict(zip(['min','p25','p50','p75','p90','p95','p99','max'],map(float,np.percentile(x,[0,25,50,75,90,95,99,100]))),mean=float(x.mean()))
def intervals(diff,seed=20260909,repetitions=20000):
 rng=np.random.Generator(np.random.PCG64(seed));n=len(diff);boot=np.empty(repetitions)
 for off in range(0,repetitions,200):
  k=min(200,repetitions-off);idx=rng.integers(0,n,size=(k,n));boot[off:off+k]=diff[idx].mean(axis=1)
 return {'mean':float(diff.mean()),'ci95':np.quantile(boot,[.025,.975]).tolist(),
         'ci_bonferroni4_family95':np.quantile(boot,[.00625,.99375]).tolist()},boot
def main():
 lock=read(V/'protocol_lock.json');cfg=read(V/'config.locked.json')
 assert sha(V/'config.locked.json')==lock['config_sha256'] and sha(V/'protocol.md')==lock['protocol_sha256']
 assert read(V/'results/c1_gate.json')['status']=='PASS' and read(V/'results/c2_smoke_gate.json')['status']=='PASS'
 datasets=[('webvid2_5m_light_v1','c2_main_webvid_v1'),('yandex_t2i_official10M_ip_v1','c2_main_yandex_v1')]
 # Validate completion of all four points before opening the first GT file.
 all_raw={}
 for ds,label in datasets:
  root=V/'results'/label;done=read(root/'complete.json');meta=read(root/'metadata.json')
  assert done['status']==meta['status']=='COMPLETE' and done['queries']==2000 and done['rows']==4000 and done['GT_accessed'] is False
  assert meta['dataset']==ds and meta['locked_config']==cfg
  raw=[json.loads(s) for s in (root/'branches.jsonl').read_text().splitlines()];assert len(raw)==4000
  ids=np.fromfile(V/'inputs'/ds/'row_ids.i64',dtype='<i8');assert len(ids)==2000
  for i,row in enumerate(raw):
   assert row['sample_index']==i//2 and row['row_id']==int(ids[i//2]) and row['L']==[64,128][i%2]
   assert len(row['branches'])==9 and row['B']==cfg['B'] and row['K']==10
   assert [b['action'] for b in row['branches']]==['continue']+[f'natural_{s}' for s in range(4)]+[f'force_{s}' for s in range(4)]
   for b in row['branches']:
    assert b['graph_ndc']==row['prefix_ndc']+b['suffix_graph_ndc'] and b['suffix_graph_ndc']<=cfg['B']
    assert b['limit']==row['prefix_ndc']+cfg['B'] and b['remaining']==cfg['B']-b['suffix_graph_ndc']
    assert b['natural_finished']!=b['cap_exhausted']
    valid=[x for x in b['ids'] if x>=0];assert len(valid)==len(set(valid))
    assert all(x<meta['config']['base_count'] for x in valid)
  all_raw[ds]=raw
 out=V/'results/analysis_v1';out.mkdir(exist_ok=False)
 s=read(V/'state.json');s.update({'status':'C2_RAW_COMPLETE_OFFLINE_SCORING','quality_scoring_started':True,
     'quality_scoring_started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()});dump(V/'state.json',s)
 points=[];artifacts=[]
 for ds,label in datasets:
  c=read(V/'inputs'/ds/'config.json');p=Path(c['gt_train_path']);assert sha(p)==c['gt_train_sha256']
  gt=np.memmap(p,mode='r',dtype='<i4').reshape(-1,101);assert len(gt)==30000 and np.all(gt[:,0]==100)
  raw=all_raw[ds];arrays={};dataset_rows=[]
  for L in [64,128]:
   rows=[r for r in raw if r['L']==L];assert len(rows)==2000
   hit=np.zeros((2000,9),dtype=np.uint8)
   for i,row in enumerate(rows):
    target=set(map(int,gt[row['row_id'],1:11]));assert len(target)==10
    for a,b in enumerate(row['branches']):hit[i,a]=len(target.intersection(b['ids']))
   recall=hit.astype(np.float64)/10.0
   force_columns=np.array([0,5,6,7,8]);choices=force_columns[np.argmax(hit[:,force_columns],axis=1)]
   natural_columns=np.array([0,1,2,3,4]);nchoices=natural_columns[np.argmax(hit[:,natural_columns],axis=1)]
   oracle=recall[np.arange(2000),choices];baseline=recall[:,0];diff=oracle-baseline
   primary,boot=intervals(diff,cfg['bootstrap_seed'],cfg['bootstrap_repetitions'])
   ndc=np.array([[b['graph_ndc'] for b in r['branches']] for r in rows],dtype=np.int64)
   suffix=np.array([[b['suffix_graph_ndc'] for b in r['branches']] for r in rows],dtype=np.int64)
   eligible=np.array([[r['branches'][5+j]['eligibility']=='eligible' for j in range(4)] for r in rows])
   effective=np.array([[r['branches'][5+j]['effective_action'] for j in range(4)] for r in rows])
   early=np.array([r['early_finished'] for r in rows]);noeligible=~eligible.any(axis=1)
   # These are distinct indicators; no survivor conditioning is used for main statistics.
   selected_effective=np.array([r['branches'][int(a)]['effective_action'] for r,a in zip(rows,choices)])
   action_names=[b['action'] for b in rows[0]['branches']]
   costs={}
   for a,name in enumerate(action_names):
    costs[name]={'graph_ndc':stats(ndc[:,a]),'suffix_graph_ndc':stats(suffix[:,a]),
                 'natural_finished_fraction':float(np.mean([r['branches'][a]['natural_finished'] for r in rows])),
                 'plain_branch_seconds':stats([r['branches'][a]['plain_wall_seconds'] for r in rows]),
                 'plain_wall_alias_fraction':float(np.mean([not r['branches'][a]['physical_branch_executed'] for r in rows]))}
   oracle_ndc=ndc[np.arange(2000),choices];natural_recall=recall[np.arange(2000),nchoices]
   same_natural=np.where(choices==0,0,choices-4)
   same_candidate_diff=oracle-recall[np.arange(2000),same_natural]
   coverage={'denominator':2000,'early_finished_fraction':float(early.mean()),'no_eligible_fraction':float(noeligible.mean()),
      'no_eligible_among_non_early_fraction_of_all':float((noeligible & ~early).mean()),'any_eligible_fraction':float(eligible.any(axis=1).mean()),
      'any_effective_force_fraction':float(effective.any(axis=1).mean()),'all_force_no_op_fraction':float((~effective.any(axis=1)).mean()),
      'oracle_strict_quality_gain_fraction':float((diff>0).mean()),'oracle_selected_effective_fraction':float(selected_effective.mean()),
      'per_slot_eligible_fraction':eligible.mean(axis=0).tolist(),
      'per_slot_visited_fraction':[float(np.mean([r['branches'][5+j]['eligibility']=='visited' for r in rows])) for j in range(4)],
      'per_slot_no_op_fraction':(~effective).mean(axis=0).tolist()}
   point_pass=bool(primary['mean']>=.005 and primary['ci_bonferroni4_family95'][0]>0 and selected_effective.any() and np.all(suffix<=cfg['B']))
   point={'dataset':ds,'L':L,'N':2000,'continue_recall':float(baseline.mean()),'oracle_recall':float(oracle.mean()),'primary':primary,
       'gate_pass':point_pass,'coverage':coverage,
       'oracle_action_fractions':{action_names[a]:float(np.mean(choices==a)) for a in force_columns},
       'all_actions_recall':[{'action':name,'mean':float(recall[:,a].mean()),'delta_vs_continue':float((recall[:,a]-baseline).mean()),
                            'secondary_inference':'descriptive; not in primary four-comparison family'} for a,name in enumerate(action_names)],
       'mechanism':{'per_slot_force_minus_same_natural_mean':(recall[:,5:9]-recall[:,1:5]).mean(axis=0).tolist(),
                    'natural_oracle_delta_vs_continue':float((natural_recall-baseline).mean()),
                    'force_oracle_minus_natural_oracle':float((oracle-natural_recall).mean()),
                    'force_oracle_winner_minus_its_same_candidate_natural':float(same_candidate_diff.mean()),
                    'interpretation':'same-slot contrasts descriptive; oracle-winner contrast has GT selection bias; different oracle winners are not pure mechanism'},
       'ndc':{'branches':costs,'oracle_graph_ndc':stats(oracle_ndc),'oracle_suffix_graph_ndc':stats(suffix[np.arange(2000),choices]),
              'oracle_vs_continue_ratio_of_means_minus_one':float(oracle_ndc.mean()/ndc[:,0].mean()-1),
              'per_query_envelope_min':stats(ndc.min(axis=1)),'per_query_envelope_max':stats(ndc.max(axis=1)),
              'all_branches_in_common_cap':bool(np.all(suffix<=cfg['B']))},
       'bookkeeping':{k:stats([r[k] for r in rows]) for k in ['state_serialization_seconds','state_deserialization_seconds','serialized_state_bytes','prefix_init_plain_seconds','prefix_resume_plain_seconds']},
       'clone_seconds_physical_branches':stats([b['clone_seconds'] for r in rows for b in r['branches'] if b['physical_branch_executed']]),
       'alias_materialization_seconds_per_query':stats([sum(b['alias_materialization_seconds'] for b in r['branches']) for r in rows]),
       'routing':{'Fast3_NDC':stats([r['route3_ndc'] for r in rows]),'candidate_top7_NDC':stats([r['route7_candidate_ndc'] for r in rows]),
                  'Fast3_wall_seconds':stats([r['route3_wall_seconds'] for r in rows]),'candidate_wall_seconds':stats([r['route7_wall_seconds'] for r in rows]),
                  'top3_top7_prefix_mismatch_count':sum(not r['direct_top3_equals_top7_prefix'] for r in rows)},
       'timing_publishable':False,'performance_GO':False}
   arrays[f'L{L}_hitcount']=hit;arrays[f'L{L}_ndc']=ndc;arrays[f'L{L}_oracle_action']=choices;arrays[f'L{L}_bootstrap']=boot
   for i,r in enumerate(rows):dataset_rows.append({'sample_index':i,'row_id':r['row_id'],'L':L,'continue_recall':baseline[i],'oracle_recall':oracle[i],
       'delta':diff[i],'oracle_action':action_names[choices[i]],'oracle_ndc':oracle_ndc[i],'continue_ndc':ndc[i,0],
       'envelope_min':ndc[i].min(),'envelope_max':ndc[i].max(),'early_finished':bool(early[i]),'no_eligible':bool(noeligible[i])})
   points.append(point)
  np.savez_compressed(out/(ds+'_aligned.npz'),**arrays)
  with (out/(ds+'_per_query.csv')).open('w') as f:
   writer=csv.DictWriter(f,fieldnames=list(dataset_rows[0]));writer.writeheader();writer.writerows(dataset_rows)
  artifacts.append({'dataset':ds,'gt_train_path':str(p),'gt_train_sha256':sha(p),'raw_path':str(V/'results'/label/'branches.jsonl'),
                    'raw_sha256':sha(V/'results'/label/'branches.jsonl')})
 passed=all(p['gate_pass'] for p in points)
 report={'status':'C2_COMPLETE','decision':'COMMON_CAP_HEADROOM_PASS_STOP_BEFORE_C3' if passed else 'NO_GO_UNCONDITIONAL_HEADROOM_STOP_C',
     'points':points,'gate':{'all_four_pass':passed,'mean_threshold':.005,'corrected_lower_threshold':0,'family_size':4,'bootstrap':20000,
           'next_action':'STOP_AND_REPORT_TO_USER','C3_run':False,'C4_run':False},'scoring_provenance':artifacts,
     'scorer_sha256':sha(Path(__file__)),'protocol_lock_sha256':sha(V/'protocol_lock.json'),
     'limits':['fixed historical drl_train development pool, not held-out','single paired build','same cap is not equal actual work','oracle is offline GT privileged','C2 bookkeeping/branch wall is not method QPS']}
 dump(out/'report.json',report);dump(out/'gate.json',report['gate']|{'decision':report['decision']})
 lines=['# C2 finite-action oracle — observed result','',f"Decision: **{report['decision']}**. Stop before C3; no C3/C4/validation/held-out executed.",'',
 '| Dataset | L | continue R@10 | oracle R@10 | unconditional Δ pp | Bonferroni4 family95 CI pp | eligible % | strict gain % | oracle actual NDC mean | gate |',
 '|---|---:|---:|---:|---:|---|---:|---:|---:|---|']
 for p in points:
  ci=p['primary']['ci_bonferroni4_family95'];lines.append(f"| {p['dataset']} | {p['L']} | {p['continue_recall']*100:.3f}% | {p['oracle_recall']*100:.3f}% | {p['primary']['mean']*100:+.3f} | [{ci[0]*100:+.3f}, {ci[1]*100:+.3f}] | {p['coverage']['any_eligible_fraction']*100:.2f} | {p['coverage']['oracle_strict_quality_gain_fraction']*100:.2f} | {p['ndc']['oracle_graph_ndc']['mean']:.2f} | {'PASS' if p['gate_pass'] else 'FAIL'} |")
 lines+=['','All 2000 queries per dataset are retained at each L, including early-finished, no-eligible and no-op cases. GT was opened only after both datasets completed raw branch execution.','',
         'The primary oracle selects among continue and up to four legal force actions; Recall ties choose continue first, then frozen candidate slot order. Natural controls are paired with the same candidate. All branch costs, action proportions, mechanism contrasts, state serialization and clone costs are in report.json; aligned IDs/distances remain in raw branches.jsonl.','',
         'This is common-cap headroom only. Actual NDC differs among branches, the historical drl_train pool and single paired build limit inference, and branch wall is not formal QPS.']
 (out/'report.md').write_text('\n'.join(lines)+'\n')
 s=read(V/'state.json');s.update({'status':report['decision'],'C2':'COMPLETE','decision':report['decision'],'stopped':True,
       'C3':'NOT_AUTHORIZED_NOT_RUN','C4':'NOT_AUTHORIZED_NOT_RUN','validation_accessed':False,'heldout_accessed':False,
       'new_labels_generated':True,'controller_trained':False,'method_performance_GO':False,'C2_headroom_pass':passed});dump(V/'state.json',s)
 print('\n'.join(lines[:9]))
if __name__=='__main__':main()
