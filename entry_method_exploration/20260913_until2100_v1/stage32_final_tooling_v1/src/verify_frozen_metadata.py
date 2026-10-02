from contracts_v2 import *
from unittest.mock import patch
import copy
threads();F=O/'results/non_executable_metadata_fixture';F.mkdir();meta=read(C/'session9_final_preparation/matrix_metadata_draft.json');inv=read(C/'candidate_inventory_v10.json');picked=[next(x for x in inv['candidates'] if x['dataset']==ds and x['name']=='E73_compact10') for ds in DS];dump(F/'inventory.json',dict(candidates=picked));(F/'scores.csv').write_text('SOFTWARE_FIXTURE_ONLY\n');(F/'protocol.md').write_text('Non-executable software fixture, no actual final selection. Identity records deliberately omit hash and cannot authorize a run.\n');sel=dict(status='FINAL_SELECTION_FROZEN',software_fixture_only=True,final_feedback_used=False,selection_rule='SOFTWARE FIXTURE ONLY, not a research selection',tie_rule='SOFTWARE FIXTURE ONLY',candidate_inventory=str(F/'inventory.json'),candidate_score_table=str(F/'scores.csv'),datasets={});configs={};totals=dict(points=0,NSG=0,HNSW=0,wall_batches=0)
for ds in DS:
 c=read(E74/'inputs'/ds/'config.json');md=meta['datasets'][ds];base=copy.deepcopy(md['required_baselines']);new=copy.deepcopy(next(x for x in picked if x['dataset']==ds)['configuration']);new.update(model_name='best_new',name='best_new_L64');base.append(new);c.update(num_queries=2000,methods=[dict(m,L=L,name=m['model_name']+'_L'+str(L)) for L in LS for m in base],split='SOFTWARE_FIXTURE_ONLY_NOT_FINAL_SELECTION');c.update({k:md['inputs'][k]['path'] for k in ['queries_file','gt_file','row_ids']});c['real_call_cap']=len(c['methods'])*14016;configs[ds]=c;dump(F/'inputs'/ds/'config.json',c)
 for k,v in validate_config(c).items():totals[k]+=v
 sel['datasets'][ds]=dict(best_all='baseline_soft' if ds==DS[0] else 'gt10_hard',best_new='best_new',best_new_inventory_name='E73_compact10',inventory_names={'best_new':'E73_compact10'})
dump(F/'selection.json',sel);lock=dict(threads=1,query_cpu=15,query_stop=1789303200,latest_launch=1789301700,per_job_seconds=1200,output_cap_MiB=64,planned_NSG=totals['NSG'],planned_HNSW=totals['HNSW'],points=totals['points'],timing_batches=totals['wall_batches']);dump(F/'config.locked.json',lock);dump(F/'reviews/base_graph_identity.json',read(E74/'reviews/base_graph_identity.json'))
paths=[F/'selection.json',F/'config.locked.json',F/'protocol.md',F/'inventory.json',F/'scores.csv',F/'reviews/base_graph_identity.json',E73/'bin/evaluate']+list((O/'src').glob('*.py'))
for ds,c in configs.items():
 paths.append(F/'inputs'/ds/'config.json');paths += [Path(c[k]) for k in ['queries_file','gt_file','row_ids']]
 for m in c['methods']:paths += [Path(m[k]) for k in ['W','graph_file','mapping','tie_ids'] if k in m]
dump(F/'reviews/prequery_freeze.json',dict(software_fixture_only=True,files=[dict(path=str(p.resolve())) for p in set(paths)]));calls=[]
with patch('contracts_v2.check',side_effect=lambda *a:calls.append(a)):
 _,b=validate_frozen(F)
assert len(calls)==1 and b==totals
# A control named best_all must be rejected before the payload hashing hook.
ds=DS[0];sel['datasets'][ds]['best_all']='control';sel['datasets'][ds]['inventory_names']['control']='fixture_control';entry=copy.deepcopy(picked[0]);entry.update(name='fixture_control',kind='mechanism_control',selectable_for_final=False);dump(F/'inventory.json',dict(candidates=picked+[entry]));dump(F/'selection.json',sel);c=configs[ds];ms=[]
for L in LS:
 group=[m for m in c['methods'] if m['L']==L];ms+=group+[dict(group[-1],name='control_L'+str(L),model_name='control')]
c['methods']=ms;c['real_call_cap']=len(ms)*14016;dump(F/'inputs'/ds/'config.json',c);calls=[];rejected=False
with patch('contracts_v2.check',side_effect=lambda *a:calls.append(a)):
 try:validate_frozen(F)
 except AssertionError as ex:rejected=True;reason=str(ex)
assert rejected and not calls and 'ineligible additional model' in reason
# Leave the fixture deliberately invalid and non-executable; never run it.
dump(O/'results/frozen_metadata_verification.json',dict(status='PASS',valid_metadata_schema_under_mocked_hash=True,best_all_control_rejected_before_final_hash=True,reason=reason,valid_shape_budget=totals,final_payload_opened=False,final_selection_made=False,actual_controller_run=False,fixture=str(F),fixture_warning='Contains source paths but only stat was performed. Hash hook mocked; final fixture left invalid with path-only identity records, cannot be run.',new_ANN=0));print('E91_FROZEN_METADATA_PASS')
