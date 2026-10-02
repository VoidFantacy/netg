from pathlib import Path
import json,hashlib,time
C=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def identity(p):
 p=Path(p);s=p.stat();return dict(path=str(p),bytes=s.st_size,mtime_ns=s.st_mtime_ns,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
old=read(C/'candidate_inventory_v7.json');x=json.loads(json.dumps(old));new=[]
for stage,eid,variants in [('stage22_joint_view_partition_v1','E81',[('joint10',True)])]:
 O=C/stage;assert (O/'reviews/final_artifact_freeze.json').exists();gate=read(O/'results/gate.json')
 for ds in ['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1']:
  c=read(O/'inputs'/ds/'aux.json')
  for name,selectable in variants:
   m=next(m for m in c['methods'] if m['model_name']==name);r=dict(dataset=ds,name=eid+'_'+name,kind='new_method' if selectable else 'mechanism_control',selectable_for_final=selectable,recommended=False,passed_new_cal_gate=False,configuration=m,W=identity(m['W']),graph=identity(m['graph_file']),mapping=identity(m['mapping']),tie_ids=identity(m['tie_ids']),evaluator=identity(O/'bin/evaluate'),development_configuration=identity(O/'inputs'/ds/'aux.json'),protocol=identity(O/'protocol.md'),physical_profiles=m['hub_count'],unique_real_hubs=m['unique_hub_count'],ef_search=10,distinct_hub_width=0,variable_profiles=True,load_contract='Reference frozen graph/W/mapping/tie and exact compatible evaluator; no rebuilding.',historical_auxiliary_quality_gate=gate['datasets'][ds] if selectable else None,control_gate_scope=None if selectable else 'Fixed target-row permutation; never promote to best_new.',historical_auxiliary_feedback_is_training=True,full_development_wall=None,wall_not_run_reason='Quality only at this stage; any conditional wall has separate stage identity.',final_selection=False,final_validation_access=False,independent_final_protocol_required=True,selection_scope='Actual new method may be frozen in a separate final comparison; old stage gate remains.' if selectable else 'Excluded from best_new.',offline_source='P-fit20K router_train[10000:30000], historically exposed',aligned_aux_raw=str(O/'results'/ds/'aux'/m['name']))
   x['candidates'].append(r);new.append(r['name']+':'+ds)
assert x['candidates'][:len(old['candidates'])]==old['candidates'] and len(x['candidates'])==52
x.update(status='SESSION7_DEVELOPMENT_INVENTORY_NO_FINAL_SELECTION',old_inventory_v7_preserved=identity(C/'candidate_inventory_v7.json'),session7_E81_added=new,session7_new_QPS_points=0,session7_final_feedback_used=False,final_selection='Not frozen for evening E34; no display alias is a global recommendation.')
p=C/'candidate_inventory_v8.json';assert not p.exists();p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
(C/'reviews/inventory_v8_verification.json').write_text(json.dumps(dict(status='PASS',epoch=time.time(),old_objects_preserved=50,new_objects=2,total_objects=52,new_main_methods=2,new_controls=0,inventory=identity(p)),indent=2)+'\n')
print('INVENTORY_V8_PASS',len(x['candidates']))
