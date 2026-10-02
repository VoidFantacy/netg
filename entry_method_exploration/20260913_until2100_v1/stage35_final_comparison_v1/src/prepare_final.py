from pathlib import Path
import sys,time,shutil
O=Path(__file__).resolve().parents[1];C=O.parent
sys.path.insert(0,str(C/'stage32_final_tooling_v1/src'))
from common import *
from contracts_v3 import validate_selection_record,validate_config,validate_frozen,BINARY_SHA,signature
O=Path(__file__).resolve().parents[1];S=C/'stage34_final_selection_v1'
threads();assert not (O/'selection.json').exists();check(S/'reviews/selection_artifact_freeze.json')
chosen=read(S/'results/selected.json');inventory=read(S/'results/final_inventory.json');metadata=read(C/'session9_final_preparation/matrix_metadata_draft.json')
sel=dict(status='FINAL_SELECTION_FROZEN',created_at=time.time(),final_feedback_used=False,selection_rule=(S/'protocol.md').read_text(),tie_rule='net_hits descending; failures ascending; total_NDC ascending; original catalog order ascending',candidate_inventory=str(S/'results/final_inventory.json'),candidate_score_table=str(S/'results/candidate_score_table.csv'),datasets={},selection_scope='Matched P and 39 static main configurations with common historically exposed aux7952; not all project methods')
required=[O/'protocol.md',Path(__file__),S/'protocol.md',S/'results/selected.json',S/'results/final_inventory.json',S/'results/candidate_score_table.csv',S/'results/eligibility.csv',S/'reviews/selection_artifact_freeze.json',C/'candidate_inventory_v12.json',C/'session11_resource_protocol.json',C/'session9_final_preparation/matrix_metadata_draft.json',E73/'bin/evaluate']+list((C/'stage32_final_tooling_v1/src').glob('*.py'))
totals=dict(points=0,NSG=0,HNSW=0,wall_batches=0);payload=[]
for di,ds in enumerate(DS):
 meta=metadata['datasets'][ds];z=chosen[ds];best=next(x for x in inventory['candidates'] if x['dataset']==ds and x['name']==z['best_new_inventory']);compact=next(x for x in inventory['candidates'] if x['dataset']==ds and x['name']=='E73_compact10')
 assert best['evaluator']['sha256']==BINARY_SHA and sha(best['evaluator']['path'])==BINARY_SHA
 methods=[dict(m) for m in meta['required_baselines']];additional=[best]+([] if best['name']==compact['name'] else [compact]);mapping={}
 for x in additional:
  m=dict(x['configuration']);mapping[m['model_name']]=x['name'];methods.append(m)
 best_name=best['configuration']['model_name'];all_name=best_name if z['passing_count'] else ('baseline_soft' if di==0 else 'gt10_hard')
 sel['datasets'][ds]=dict(best_all=all_name,best_new=best_name,best_new_inventory_name=best['name'],inventory_names=mapping,development_gate_pass=bool(z['passing_count']),aliases={'best_all':all_name,'best_new':best_name,'compact_origin':'compact10'},score_record=z['selection_score'])
 c=dict(dataset=ds,source_namespace='validation',split='E94_final_historical_validation2000',num_queries=2000,input_total_rows=2000,dim=meta['dim'],gt_k=100,base_count=meta['base_count'],index_path=meta['index_path'],threads=1,query_cpu=15,dataset_order=di,timing_repeats=5,methods=[dict(m,L=L,name=m['model_name']+'_L'+str(L)) for L in LS for m in methods],real_call_cap=len(methods)*5*14016)
 for k in ['queries_file','gt_file','row_ids']:
  x=meta['inputs'][k];p=Path(x['path']);st=p.stat();assert (st.st_size,st.st_mtime_ns)==(x['bytes'],x['mtime_ns']);c[k]=str(p);payload.append(p)
 cp=O/'inputs'/ds/'config.json';dump(cp,c);required.append(cp);b=validate_config(c)
 for k in totals:totals[k]+=b[k]
 for m in methods:required += [Path(m[k]) for k in ['W','mapping','tie_ids','graph_file'] if k in m]
 assert len({str(signature(m)) for m in methods})==len(methods)
validate_selection_record(sel);dump(O/'selection.json',sel);required.append(O/'selection.json')
lock=dict(created_at=time.time(),threads=1,query_cpu=15,planned_NSG=totals['NSG'],planned_HNSW=totals['HNSW'],points=totals['points'],timing_batches=totals['wall_batches'],output_cap_MiB=64,free_min_GiB=6.45,latest_launch=1789299600,query_stop=1789300380,per_job_seconds=1200,dataset_operation_budget_seconds={DS[0]:780,DS[1]:600},day_goal_complete=False)
assert totals==dict(points=50,NSG=700800,HNSW=560000,wall_batches=250);dump(O/'config.locked.json',lock);required.append(O/'config.locked.json')
base=read(C/'stage15_compact_wall_v1/reviews/base_graph_identity.json')
for x in base['sources']:
 st=Path(x['path']).stat();assert(st.st_size,st.st_mtime_ns)==(x['bytes'],x['mtime_ns'])
dump(O/'reviews/base_graph_identity.json',base);required.append(O/'reviews/base_graph_identity.json')
assert all(p not in payload for p in required)
freeze(O/'reviews/preselection_freeze.json',required)
check(O/'reviews/preselection_freeze.json')
dump(O/'reviews/final_input_access.json',dict(preselection_seal=identity(O/'reviews/preselection_freeze.json'),selection_frozen_before_payload=True,first_payload_hash_start_epoch=time.time(),payload_paths=list(map(str,payload)),scope='First session11 final payload read starts in following freeze hashing; identity only before native search; no feedback returned to selection; namespace validation, historically exposed',heldout_opened=False))
freeze(O/'reviews/prequery_freeze.json',required+payload+[O/'reviews/preselection_freeze.json',O/'reviews/final_input_access.json'])
validate_frozen(O)
dump(O/'reviews/preflight.json',dict(status='PASS_FROZEN_FINAL_MATRIX_READY',budget=totals,base_graph_stat_verified=True,actual_selected_binary=BINARY_SHA,final_selection_unchanged=True,new_ANN=0))
state=read(C/'state.json');state.update(status='E94_FROZEN_READY_WEB',candidate_inventory=str(C/'candidate_inventory_v12.json'),final_selection=str(O/'selection.json'),final_run_directory=str(O),session11_final_payload_access=True,session11_final_feedback_used_for_training=False,native_pids=[]);dump(C/'state.json',state)
print('E94_READY',totals,flush=True)
