from pathlib import Path
import json,hashlib,time
C=Path(__file__).resolve().parents[1]
def read(p):return json.loads(Path(p).read_text())
def ident(p):
 p=Path(p);s=p.stat();return dict(path=str(p),bytes=s.st_size,mtime_ns=s.st_mtime_ns,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
old=read(C/'candidate_inventory_v8.json');x=json.loads(json.dumps(old));added=[]
for stage,eid,main in [('stage24_sibling_links_v1','E83','sibling10'),('stage25_query_shortcuts_v1','E84','shortcut10')]:
 o=C/stage;assert (o/'reviews/final_artifact_freeze.json').exists();g=read(o/'results/gate.json')
 for ds in ['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1']:
  cfg=read(o/'inputs'/ds/'aux.json')
  for name in [main,'neighbor10']:
   m=next(m for m in cfg['methods'] if m['model_name']==name);is_main=name==main
   row=dict(dataset=ds,name=eid+'_'+name,kind='new_method' if is_main else 'mechanism_control',selectable_for_final=is_main,recommended=False,passed_new_cal_gate=False,configuration=m,W=ident(m['W']),graph=ident(m['graph_file']),mapping=ident(m['mapping']),tie_ids=ident(m['tie_ids']),evaluator=ident(o/'bin/evaluate'),development_configuration=ident(o/'inputs'/ds/'aux.json'),protocol=ident(o/'protocol.md'),physical_profiles=m['hub_count'],unique_real_hubs=m['unique_hub_count'],ef_search=10,distinct_hub_width=0,variable_profiles=True,load_contract='Reference frozen graph/W/mapping/tie and compatible E73 evaluator, no rebuilding.',historical_auxiliary_quality_gate=g['datasets'][ds] if is_main else None,control_gate_scope=None if is_main else 'Matched source-node degree nearest-otherhub control; not eligible for promotion.',historical_auxiliary_feedback_is_training=True,full_development_wall=None,wall_not_run_reason='Locked quality gate failed; stopped original stage has no wall.',final_selection=False,final_validation_access=False,independent_final_protocol_required=True,selection_scope='Catalogue only, not recommended. A separate explicitly frozen final protocol may select actual new method; old stage stop unchanged.' if is_main else 'Excluded from best_new.',offline_source='E73 compact graph; E84 additionally uses P-fit20K raw query ranking votes' if eid=='E84' else 'E73 compact fixed same-hub adjacency rule',aligned_aux_raw=str(o/'results'/ds/'aux'/m['name']))
   x['candidates'].append(row);added.append(row['name']+':'+ds)
assert x['candidates'][:len(old['candidates'])]==old['candidates'] and len(x['candidates'])==60
x.update(status='SESSION8_DEVELOPMENT_INVENTORY_NO_FINAL_SELECTION',old_inventory_v8_preserved=ident(C/'candidate_inventory_v8.json'),session8_added=added,session8_QPS_points=0,session8_final_feedback_used=False,offline_E85=dict(status='CACHE_FEASIBILITY_FAILED_NOT_NATIVE_METHOD',models=[ident(p) for p in sorted((C/'stage26_query_gate_feasibility_v1/models').rglob('*.npz'))],selectable_for_final=False),final_selection='Not frozen for evening E34; no display alias is a global recommendation.')
p=C/'candidate_inventory_v9.json';assert not p.exists();p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');(C/'reviews/inventory_v9_verification.json').write_text(json.dumps(dict(status='PASS',epoch=time.time(),old_objects_preserved=52,new_objects=8,total_objects=60,new_main_methods=4,new_controls=4,E85_offline_not_native_candidate=True,inventory=ident(p)),indent=2)+'\n');print('INVENTORY_V9_PASS',len(x['candidates']))
