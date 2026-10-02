from shared import *
threads(8)
for name in ['inputs','results','reviews','logs','figures','source_before']:(O/name).mkdir(exist_ok=True)
resources();check(E49/'reviews/final_artifact_freeze.json');assert read(E49/'reviews/final_audit.json')['status']=='PASS'
assert not (O/'config.locked.json').exists()
freeze(O/'reviews/protected.json',[Path(x['path']) for x in read(E49/'reviews/protected.json')['files']]+files(E49))
for name in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md','experiment_history/38_frozen_local_rl_evaluation.md']:
 shutil.copy2(R/name,O/'source_before'/name.replace('/','__'))
dump(O/'config.locked.json',dict(datasets=DS,arms=ARMS,seeds=SEEDS,steps=200,contexts=1600,candidates=12800,new_NSG=0,optimizer_updates=0,threads=1,
 followup_gate=dict(rl_positive_candidate_step_fraction_min=.2,mean_quality_null_fraction_on_positive_steps_min=.5,J_best_net_sum_above_mean=True,J_best_selected_coefficients_within_2=True,both_datasets=True)))
freeze(O/'reviews/preanalysis_freeze.json',files(O/'src')+[O/'protocol.md',O/'config.locked.json'])
dump(O/'state.json',dict(status='PREPARED_CANDIDATE_COMMIT_DIAGNOSIS',new_NSG=0));print('E50 fixed all 1600 contexts; no new queries',flush=True)
