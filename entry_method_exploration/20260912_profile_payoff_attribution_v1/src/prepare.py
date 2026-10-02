from common import *
contract()
for d in ['reviews','results','logs','figures','source_before']:(O/d).mkdir(exist_ok=True)
assert read(E39/'reviews/final_audit.json')['status']=='PASS'
# Verify the immediately preceding freeze, including current root documents, before editing them.
check(E39/'reviews/final_artifact_freeze.json')
freeze(O/'reviews/protected.json',files(E37)+files(E38)+files(E39))
for name in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md',
             'experiment_history/README.md','experiment_history/28_fixed_profile_batch_diagnosis.md']:
 shutil.copy2(R/name,O/'source_before'/name.replace('/','__'))
freeze(O/'reviews/preanalysis_freeze.json',files(O/'src')+[O/'protocol.md'])
dump(O/'state.json',dict(status='PREPARED_EXISTING_PAYOFF_ANALYSIS',NSG_calls=0,HNSW_calls=0,builds=0,optimizer_updates=0))
print('Existing sources and current documents verified; no new search.')
