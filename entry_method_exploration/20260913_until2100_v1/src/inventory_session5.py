"""Append only new configuration identities; run after all E74 native jobs exit."""
from pathlib import Path
import sys,json,time,hashlib
C=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(C/'stage15_compact_wall_v1/src'))
from common import read,dump,identity,DS
assert all(x['status']=='COMPLETE' for x in read(C/'stage15_compact_wall_v1/logs/jobs.json'))
dst=C/'candidate_inventory_v5.json';assert not dst.exists();old=read(C/'candidate_inventory_v4.json');v=json.loads(json.dumps(old));original=len(v['candidates']);assert original==24
for ds in DS:
 for stage,tag,selected in [('stage13_distinct_hub_width_v1','E72',lambda m:m.get('distinct_hub_width')==10),('stage14_compact_modes_v1','E73',lambda m:m['model_name']=='compact10')]:
  p=C/stage;cfg=read(p/'inputs'/ds/'aux.json')
  for m in cfg['methods']:
   if not selected(m):continue
   kind='singleton_control' if m['model_name']=='baselineD10' else ('capacity_control' if 'duplicate' in m['model_name'] else 'new_method')
   record=dict(dataset=ds,name=tag+'_'+m['model_name'],kind=kind,selectable_for_final=kind=='new_method',recommended=False,passed_new_cal_gate=False,
    W=identity(m['W']),graph=identity(m['graph_file']),mapping=identity(m['mapping']),tie_ids=identity(m['tie_ids']),evaluator=identity(p/'bin/evaluate'),configuration=m,
    physical_profiles=m['hub_count'],unique_real_hubs=m.get('unique_hub_count',m['hub_count']),ef_search=10,distinct_hub_width=m.get('distinct_hub_width',0),variable_profiles=m.get('variable_profiles',False),
    load_contract='Use frozen graph/W/mapping and exact evaluator/config; do not rebuild for evaluation',
    development_configuration=identity(p/'inputs'/ds/'aux.json'),historical_auxiliary_quality_gate=read(p/'results/gate.json')['datasets'][ds],historical_auxiliary_feedback_is_training=True,
    full_development_wall='E74 fixed compact display' if tag=='E73' else 'not run; original E72 gate stopped',final_selection=False,final_validation_access=False)
   if tag=='E72':record['synthetic_scope_correction']=str(C/'reviews/e72_synthetic_scope_correction_session5.md')
   v['candidates'].append(record)
assert v['candidates'][:24]==old['candidates'] and len(v['candidates'])==32
v.update(status='SESSION5_FROZEN_DISTINCT_AND_COMPACT_CANDIDATES',old_inventory_v4_preserved=identity(C/'candidate_inventory_v4.json'),E74_display_choices=read(C/'stage15_compact_wall_v1/results/frozen_selection.json'),E74_display_is_global_best_selection=False,E74_same_binary=identity(C/'stage15_compact_wall_v1/bin/evaluate'),E73_compact_evaluator=identity(C/'stage14_compact_modes_v1/bin/evaluate'),final_validation_measured_today=False,heldout_opened=False)
dump(dst,v);dump(C/'reviews/session5_inventory_verification.json',dict(status='PASS',original_candidates_preserved=24,new_configuration_candidates=8,total=32,not_global_final_selection=True,epoch=time.time()));print('INVENTORY_V5_PASS',32)
