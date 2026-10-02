from pathlib import Path
import json,hashlib,time
C=Path(__file__).resolve().parents[1]
def read(p):return json.loads(Path(p).read_text())
def ident(p):
 p=Path(p);s=p.stat();return dict(path=str(p),bytes=s.st_size,mtime_ns=s.st_mtime_ns,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
old=read(C/'candidate_inventory_v9.json');x=json.loads(json.dumps(old));added=[]
for stage,eid,main in [('stage27_edge_utility_v1','E86','utility10'),('stage28_utility_proposals_v1','E87','utility10')]:
 o=C/stage;assert (o/'reviews/final_artifact_freeze.json').exists();g=read(o/'results/gate.json')
 for ds in ['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1']:
  cfg=read(o/'inputs'/ds/'aux.json')
  for name in [main,'neighbor10']:
   m=next(m for m in cfg['methods'] if m['model_name']==name);is_main=name==main;zero=(eid=='E87' and ds.startswith('yandex'))
   row=dict(dataset=ds,name=eid+'_'+name,kind=('zero_update_alias' if zero else 'new_method') if is_main else 'mechanism_control',selectable_for_final=is_main and not zero,recommended=False,passed_new_cal_gate=False,configuration=m,W=ident(m['W']),graph=ident(m['graph_file']),mapping=ident(m['mapping']),tie_ids=ident(m['tie_ids']),evaluator=ident(C/'stage14_compact_modes_v1/bin/evaluate'),development_configuration=ident(o/'inputs'/ds/'aux.json'),protocol=ident(o/'protocol.md'),physical_profiles=m['hub_count'],unique_real_hubs=m['unique_hub_count'],ef_search=10,distinct_hub_width=0,variable_profiles=True,load_contract='Reference frozen graph/W/mapping/tie and compatible E73 evaluator, no rebuilding.',historical_auxiliary_quality_gate=g['datasets'][ds] if is_main else None,control_gate_scope=None if is_main else 'Matched source-node degree nearest-otherhub control; not eligible for promotion.',historical_auxiliary_feedback_is_training=True,full_development_wall=None,wall_not_run_reason='Locked quality gate failed; stopped original stage has no wall.',final_selection=False,final_validation_access=False,independent_final_protocol_required=True,selection_scope='Catalogue only, not recommended. A separate explicitly frozen final protocol may select actual new method; old stage stop unchanged.' if is_main else 'Excluded from best_new.',offline_source='P-fit20K actual complete-entry NSG single-edge responses; E87 P-better-query proposals. Fit includes old train/monitor. Auxiliary7952 and cal/audit historically exposed; acceptance feedback counts as training.',zero_update_alias_of='E73_compact10' if zero else None,aligned_aux_raw=str(o/'results'/ds/'aux'/m['name']))
   
   if zero:row['selection_scope']='Zero-update alias of original compact; excluded from best_new and new-method performance claims.'
   x['candidates'].append(row);added.append(row['name']+':'+ds)
assert x['candidates'][:len(old['candidates'])]==old['candidates'] and len(x['candidates'])==68
x.update(status='SESSION9_DEVELOPMENT_INVENTORY_NO_FINAL_SELECTION',old_inventory_v9_preserved=ident(C/'candidate_inventory_v9.json'),session9_added=added,session9_QPS_points=0,session9_final_feedback_used=False,session9_zero_update_aliases_excluded=True,final_selection='Not frozen for evening E34; actual best_all/best_new still pending.')
p=C/'candidate_inventory_v10.json';assert not p.exists();p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');(C/'reviews/inventory_v10_verification.json').write_text(json.dumps(dict(status='PASS',epoch=time.time(),old_objects_preserved=60,new_objects=8,total_objects=68,new_main_nonzero_methods=3,new_zero_update_aliases=1,new_controls=4,inventory=ident(p)),indent=2)+'\n');print('INVENTORY_V10_PASS',len(x['candidates']))
