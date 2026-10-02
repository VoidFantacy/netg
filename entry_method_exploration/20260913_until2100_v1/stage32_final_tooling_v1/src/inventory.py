from common import *
import copy
threads();resources();old=read(C/'candidate_inventory_v10.json');new=copy.deepcopy(old);new.update(status='SESSION10_DEVELOPMENT_INVENTORY_NO_FINAL_SELECTION',prior_inventory=identity(C/'candidate_inventory_v10.json'),final_selection=False,final_payload_opened=False);added=[]
for stage,ename,main in [('stage30_local_parent_restore_v1','E89','restore10'),('stage31_cross_source_restore_v1','E90','supported10')]:
 S=C/stage;check(S/'reviews/final_artifact_freeze.json')
 for ds in DS:
  c=read(S/'inputs'/ds/'aux.json');gate=read(S/'results/gate.json')['datasets'][ds]
  for name in [main,'random10']:
   m=next(x for x in c['methods'] if x['model_name']==name);zero=(ename=='E90' and ds==DS[1]);control=name=='random10';entry=dict(dataset=ds,name=ename+'_'+name,kind='mechanism_control' if control else 'new_method',selectable_for_final=not(control or zero),recommended=False,passed_new_cal_gate=False,configuration=m,W=identity(m['W']),graph=identity(m['graph_file']),mapping=identity(m['mapping']),tie_ids=identity(m['tie_ids']),evaluator=identity(E73/'bin/evaluate'),development_configuration=identity(S/'inputs'/ds/'aux.json'),protocol=identity(S/'protocol.md'),gate=identity(S/'results/gate.json'),cost=identity(S/'results/cost.json'),physical_profiles=m['hub_count'],unique_real_hubs=m['unique_hub_count'],ef_search=m['ef_search'],distinct_hub_width=0,variable_profiles=True,historical_auxiliary_quality_gate=None if control else gate,historical_auxiliary_feedback_is_training=True,full_development_wall=None,wall_not_run_reason='Locked complete quality gate failed; fixed version stopped. No new QPS.',final_selection=False,final_validation_access=False,independent_final_protocol_required=True,offline_source='E89 P-fit20K actual complete-entry NSG single-parent-group response; E90 additionally trains on router_train[2048:6024]. P-fit includes old train/monitor, all auxiliary/cal/audit previously exposed.',acceptance_scope='E89 all7952 with halves; E90 suffix3976 [6024:10000] with1988 halves. Different acceptance populations must not be conflated.',aligned_aux_raw=str(S/'results'/ds/'aux'/m['name']),zero_update_alias_of='E73_compact10' if zero else None,selection_scope='Excluded control or zero alias.' if control or zero else 'Nonzero main model may be considered only under a new explicit final-selection protocol. Not gate/performance GO.')
   assert read(entry['development_configuration']['path'])['methods'][c['methods'].index(m)]==m;added.append(entry)
new['candidates']+=added;assert new['candidates'][:len(old['candidates'])]==old['candidates'] and len(new['candidates'])==76
# Verify every actual nested identity in the complete inherited inventory.
identities=[]
def visit(x):
 if isinstance(x,dict):
  if {'path','sha256','bytes'}.issubset(x):identities.append(x)
  for v in x.values():visit(v)
 elif isinstance(x,list):
  for v in x:visit(v)
visit(new);seen={}
for x in identities:
 if x['path'] not in seen:seen[x['path']]=identity(x['path'])
 y=seen[x['path']];assert x['bytes']==y['bytes'] and x['sha256']==y['sha256'];assert 'mtime_ns' not in x or x['mtime_ns']==y['mtime_ns']
path=C/'candidate_inventory_v11.json';assert not path.exists();dump(path,new);dump(O/'results/inventory_verification.json',dict(status='PASS',old_objects_preserved=68,added=8,total=76,added_nonzero_main=3,added_zero_main=1,added_controls=4,nested_identities=len(identities),unique_files=len(seen),output=identity(path),new_ANN=0,final_payload_opened=False,final_selection=False));print('E91_INVENTORY76_PASS',len(identities),len(seen))
