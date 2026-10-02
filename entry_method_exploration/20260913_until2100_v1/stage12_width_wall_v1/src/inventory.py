from common import *
import csv
threads();old=read(C/'candidate_inventory_v3.json');x=json.loads(json.dumps(old));assert len(x['candidates'])==18
E70=C/'stage11_width_control_v1';pts=list(csv.DictReader((E70/'results/points.csv').open()));gate=read(E70/'results/gate.json')
for ds in DS:
 c=read(E70/'inputs'/ds/'aux.json')
 for name in ['baseline30','duplicate3P30','mode3P30']:
  m=next(m for m in c['methods'] if m['model_name']==name)
  entry=dict(dataset=ds,name='E70_'+name,kind='width_candidate' if name=='mode3P30' else 'width_control',recommended=False,passed_new_cal_gate=False,passed_E70_aux_quality_gate=bool(gate['datasets'][ds]['passed']) if name=='mode3P30' else None,
   W=identity(m['W']),graph=identity(m['graph_file']),mapping=identity(m['mapping']),tie_ids=identity(m['tie_ids']),ef_search=30,physical_profile_count=m['hub_count'],unique_hub_count=m.get('unique_hub_count',m['hub_count']),multi_profile=m.get('multi_profile',False),reference_graph=True,
   load_contract='E70-compatible explicit ef_search30; source graph load with W/label validation; 7 slot dedup for multi-profile',source_protocol=identity(E70/'protocol.md'),historical_development_points=[p for p in pts if p['dataset']==ds and p['model']==name],final_validation_measured=False)
  x['candidates'].append(entry)
assert x['candidates'][:18]==old['candidates'];x.update(status='SESSION4_FROZEN_WIDTH_CANDIDATES',old_inventory_v3_preserved=identity(C/'candidate_inventory_v3.json'),E70_width_evaluator=identity(E70/'bin/evaluate'),E71_same_binary=identity(O/'bin/evaluate'),E71_display_choices=read(O/'results/frozen_selection.json'),E71_display_is_global_best_selection=False,final_selection='Not frozen for E34 final; do not use development display alias best_new as global selection.',final_validation_measured_today=False)
assert not (C/'candidate_inventory_v4.json').exists();dump(C/'candidate_inventory_v4.json',x);dump(O/'reviews/inventory_verification.json',dict(status='PASS',old_candidates_unchanged=18,new_width_configurations=6,total=24,final_selection_not_frozen=True));print('INVENTORY_V4_READY')
