"""Preserve v5 exactly and register session6 artifacts; no final selection or ANN."""
from pathlib import Path
import copy,hashlib,json,time
C=Path(__file__).resolve().parents[1]
def read(p):return json.loads(Path(p).read_text())
def write(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def ident(p):
 p=Path(p);s=p.stat();return dict(path=str(p),bytes=s.st_size,mtime_ns=s.st_mtime_ns,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
old=read(C/'candidate_inventory_v5.json');out=copy.deepcopy(old)
out['status']='SESSION6_DEVELOPMENT_INVENTORY_NO_FINAL_SELECTION'
registered=[]
for stage,eid,names,controls in [
 ('stage16_preserved_levels_v1','E75',['preserved10'],[]),
 ('stage18_child_shrink_factorial_v1','E77',['shrink10','score10','topology10'],['score10','topology10']),
 ('stage19_child_mass_norm_v1','E78',['mass10','uniform10'],['uniform10'])]:
 O=C/stage;gate=read(O/'results/gate.json')
 for ds in ['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1']:
  cf=O/'inputs'/ds/'aux.json';conf=read(cf);assert conf['threads']==1 and conf['query_cpu']==15
  for n in names:
   m=next(m for m in conf['methods'] if m['model_name']==n);control=n in controls
   c=dict(dataset=ds,name=eid+'_'+n,kind='mechanism_control' if control else 'new_method',selectable_for_final=not control,
      recommended=False,passed_new_cal_gate=False,W=ident(m['W']),graph=ident(m['graph_file']),mapping=ident(m['mapping']),
      tie_ids=ident(m['tie_ids']),evaluator=ident(O/'bin/evaluate'),configuration=m,physical_profiles=m['hub_count'],
      unique_real_hubs=m['unique_hub_count'],ef_search=m['ef_search'],distinct_hub_width=0,variable_profiles=True,
      load_contract='Frozen graph/W/mapping/tie and exact evaluator/config. Reference, never rebuild for comparison.',
      development_configuration=ident(cf),historical_auxiliary_quality_gate=gate['datasets'][ds] if not control else None,
      control_gate_scope='Only the preregistered main method had a continuation gate. No automatic control promotion.' if control else None,
      historical_auxiliary_feedback_is_training=True,full_development_wall=None,
      wall_not_run_reason='Preregistered main continuation gate failed in both datasets; controls not selected.',
      final_selection=False,final_validation_access=False,protocol=ident(O/'protocol.md'),
      independent_final_protocol_required=True,
      selection_scope='Eligible only as an actual failed new method for a separately frozen final comparison; does not authorize a gated enhancement wall.' if not control else 'Excluded from final best_new selection under this stage protocol.')
   out['candidates'].append(c);registered.append(c['name']+':'+ds)
assert out['candidates'][:32]==old['candidates'] and len(out['candidates'])==44
out['old_inventory_v5_preserved']=ident(C/'candidate_inventory_v5.json')
out['session6_added']=registered
out['session6_main_gates_passed']=False
out['session6_new_development_wall_points']=0
out['session6_final_feedback_used']=False
out['session6_compile_cost_scope_correction']=ident(C/'reviews/e75_compile_cost_scope_session6.json')
write(C/'candidate_inventory_v6.json',out)
# Re-open both sides, validate every inventory identity/config, not just new models.
old2=read(C/'candidate_inventory_v5.json');v6=read(C/'candidate_inventory_v6.json');assert v6['candidates'][:32]==old2['candidates']
checks=0
for c in v6['candidates']:
 for key in ['W','graph','mapping','tie_ids','evaluator','development_configuration','protocol']:
  if key in c:
   row=c[key];assert ident(row['path'])['sha256']==row['sha256'],row['path'];checks+=1
 if c in v6['candidates'][32:]:
  conf=read(c['development_configuration']['path']);assert c['configuration'] in conf['methods']
  m=c['configuration'];assert c['W']['path']==m['W'] and c['graph']['path']==m['graph_file'] and c['mapping']['path']==m['mapping'] and c['tie_ids']['path']==m['tie_ids']
  assert c['W']['bytes']==m['hub_count']*m['dim']*4
  assert c['mapping']['bytes']==c['tie_ids']['bytes']==m['hub_count']*4
write(C/'reviews/session6_inventory_verification.json',dict(status='PASS',epoch=time.time(),old_entries_preserved=32,new_entries=12,total_entries=44,
    identity_checks=checks,new_method_entries=6,mechanism_control_entries=6,final_selection=False,final_feedback_used=False,
    inventory=ident(C/'candidate_inventory_v6.json')))
print(json.dumps(dict(status='PASS',entries=44,identities=checks,new_entries=registered)))
