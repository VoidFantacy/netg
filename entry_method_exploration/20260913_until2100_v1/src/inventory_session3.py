from pathlib import Path
import sys,csv
C=Path(__file__).resolve().parents[1];O=C/'stage8_multimode_wall_v1';sys.path.insert(0,str(O/'src'))
from common import *
threads();assert read(O/'reviews/verification.json')['status']=='PASS'
E66=C/'stage7_multimode_index_v1';v=read(C/'candidate_inventory_v2.json');points=list(csv.DictReader((E66/'results/points.csv').open()));gates=read(E66/'results/selection.json')['datasets']
for ds in DS:
    c=read(E66/'inputs'/ds/'fit.json')
    for source,kind in [('duplicate3P','control'),('mode3P','new_method')]:
        m=next(m for m in c['methods'] if m['model_name']==source)
        v['candidates'].append(dict(dataset=ds,name='E66_'+source,kind=kind,recommended=False,passed_new_cal_gate=False,cal_role='No new cal queries in E66; old cal historically exposed',
            passed_E66_development_gate=False if kind=='control' else gates[ds]['passed'],E66_gate=None if kind=='control' else gates[ds],
            W=identity(m['W']),graph=identity(m['graph_file']),mapping=identity(m['mapping']),tie_ids=identity(m['tie_ids']),
            load_contract='E66 multi_profile slot labels; graph_file and 7-slot dedup required; original E34 binary is incompatible',
            policy_configuration=m,physical_profile_count=m['hub_count'],unique_hub_count=m['unique_hub_count'],
            historical_development_points=[p for p in points if p['dataset']==ds and p['model']==source],source_protocol=identity(E66/'protocol.md')))
v.update(status='SESSION3_FROZEN_ENDPOINTS_E66_E67',old_inventory_preserved=str(C/'candidate_inventory_v2.json'),
    final_selection='Not frozen for final E34 yet. A new final protocol must include current candidates and use only disclosed development feedback; never final responses.',
    E67_display_choices={ds:'E66_mode3P' for ds in DS},E67_display_is_global_best_selection=False,
    validated_multi_profile_evaluator=identity(E66/'bin/evaluate'),E67_same_binary=identity(O/'bin/evaluate'),
    final_validation_measured_today=False,heldout_opened=False)
assert len(v['candidates'])==18
path=C/'candidate_inventory_v3.json';assert not path.exists();dump(path,v);print('INVENTORY_V3_PASS',len(v['candidates']))
