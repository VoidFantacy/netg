from common import *
start();assert not (O/'config.locked.json').exists()
for n in ['inputs','results','reviews','logs','source_before','figures']:(O/n).mkdir(exist_ok=True)
assert read(E58/'reviews/final_audit.json')['status']=='PASS';check(E58/'reviews/final_artifact_freeze.json')
for n in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md']:shutil.copy2(R/n,O/'source_before'/n.replace('/','__'))
pool=read(E57/'inputs/candidate_pool.json');dump(O/'inputs/candidate_pool.json',pool);protected=files(E57)+files(E58)
for ds in DS:
 c=read(E37/'inputs'/ds/'config.json');dump(O/'inputs'/ds/'config.json',c);protected.append(Path(c['gt_file']))
 assert len(pool[ds])==19 and pool[ds][0]['model_name']=='baseline'
 for m in pool[ds]:protected.extend(Path(m[k]) for k in ['prior_raw','W','graph_file','mapping','tie_ids'])
freeze(O/'reviews/protected.json',protected)
dump(O/'config.locked.json',dict(models_per_dataset=19,phases={'train':4096,'monitor':1024,'cal':1024},selected_source='E57 existing selection unchanged',new_NSG=0,new_HNSW=0,new_builds=0,new_optimizer=0,new_GT=0,new_QPS=0,analysis_stop=1789221000))
for p in files(O/'src'):
 if p.suffix=='.py':ast.parse(p.read_text())
freeze(O/'reviews/analysis_freeze.json',files(O/'src')+files(O/'inputs')+[O/'protocol.md',O/'config.locked.json'])
dump(O/'state.json',dict(status='PREPARED_READ_ONLY_FROZEN_POOL'));print('E59 PREPARED',flush=True)
