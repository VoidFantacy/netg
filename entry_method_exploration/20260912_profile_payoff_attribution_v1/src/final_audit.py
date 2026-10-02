from common import *
import re, ast
contract();start=time.monotonic()
check(O/'reviews/protected.json');check(O/'reviews/preanalysis_freeze.json')
protected=read(O/'reviews/protected.json')['files']
assert {x['path'] for x in protected}=={str(p) for root in [E37,E38,E39] for p in files(root)}
for name in ['independent_verification','neighborhood_verification','visual_review']:
 assert read(O/'reviews'/(name+'.json'))['status']=='PASS'
d=read(O/'results/diagnosis.json')
assert all(d[k]==0 for k in ['new_NSG','new_HNSW','new_builds','optimizer_updates','new_GT'])
assert d['existing_outputs_scored']==36864 and d['same_entry_outputs_checked']==26260
assert not (O/'models').exists() and not (O/'bin').exists()
for name in ['common.py','prepare.py','analyze.py','verify.py','verify_neighbors.py']:
 tree=ast.parse((O/'src'/name).read_text())
 imports=[a.name for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names]
 imports += [n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
 assert not any(x and any(word in x for word in ['native','ctypes','subprocess','train']) for x in imports),name
assert len(read(O/'results/attribution_cases.json')['cases'])==2
docs=[R/p for p in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md',
                   'experiment_history/README.md','experiment_history/29_profile_payoff_attribution.md']]+list(O.glob('*.md'))
links=0;broken=[]
for p in docs:
 for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if '://' in target or target.startswith('#'):continue
  path=(p.parent/target.split('#')[0]).resolve()
  if not path.exists() and path!=O/'reviews/final_audit.json':broken.append((str(p),target))
  links+=1
assert not broken,broken
reviewed=[R/'experiment_history'/name for name in ['11_ab_fixed_slot_exploration.md','17_gt10_shared_transform.md',
   '18_teacher_objective_alignment.md','19_equivalent_teacher_sets.md','20_training_effectiveness.md','21_direct_reward_policy.md']]
reviewed += [R/'entry_method_exploration'/p for p in ['20260909_ab_experiment_v1/src/train.py',
   '20260911_gt10_shared_transform_v1/src/train.py','20260911_equivalent_teacher_sets_v1/protocol.md',
   '20260911_training_effectiveness_v1/protocol.md','20260911_direct_reward_policy_v1/src/train.py']]
freeze(O/'reviews/historical_sources.json',reviewed)
status='COMPLETE_PAYOFF_ATTRIBUTION_LOCAL_OPPORTUNITY_WITH_CANCELLATION'
dump(O/'state.json',dict(status=status,completed_at=time.time(),NSG_calls=0,HNSW_calls=0,builds=0,
     optimizer_updates=0,new_GT=0,new_validation_heldout_raw_access=False,default_changed=False,
     queued_jobs=0,next_target_rest_factorial='DESIGNED_UNRUN'))
audit=dict(status='PASS',protected_files=len(protected),protected_counts={p.name:len(files(p)) for p in [E37,E38,E39]},
    new_NSG=0,new_HNSW=0,new_builds=0,optimizer_updates=0,new_GT=0,local_links=links,
    independent_verification=read(O/'reviews/independent_verification.json'),
    neighborhood_verification=read(O/'reviews/neighborhood_verification.json'),
    artifact_bytes=sum(p.stat().st_size for p in files(O)),seconds=time.monotonic()-start)
dump(O/'reviews/final_audit.json',audit)
freeze(O/'reviews/final_artifact_freeze.json',files(O)+docs)
print(json.dumps(audit,ensure_ascii=False,indent=2))
