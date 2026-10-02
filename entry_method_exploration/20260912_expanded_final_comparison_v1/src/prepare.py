from common import *
import ast,sys
assert os.sched_getaffinity(0)=={8};resources();assert not (O/'config.locked.json').exists()
for name in ['inputs','results','reviews','logs','figures','source_before','bin']:(O/name).mkdir(exist_ok=True)
assert read(E56/'reviews/final_audit.json')['status']=='PASS';check(E56/'reviews/final_artifact_freeze.json')
freeze(O/'reviews/protected.json',[p for root in [E55,E56] for p in root.rglob('*') if p.is_file()])
check(E56/'reviews/native_dependencies.json');shutil.copy2(E56/'reviews/native_dependencies.json',O/'reviews/native_dependencies.json')
for name in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md']:shutil.copy2(R/name,O/'source_before'/name.replace('/','__'))
shutil.copy2(E55/'bin/evaluate',O/'bin/evaluate');assert sha(O/'bin/evaluate')==sha(E37/'bin/evaluate')
pool=read(E55/'inputs/candidate_pool.json');upstream=[]
for ds in DS:
 c=read(E55/'inputs'/ds/'config.json');dump(O/'inputs'/ds/'config.json',c)
 for phase in ['fit_parity','cal','validation']:
  src=E55/'inputs'/ds/phase;dest=O/'inputs'/ds/phase;dest.mkdir(parents=True)
  for name in ['queries.f32','gt.i64','row_ids.i64','source.json']:shutil.copy2(src/name,dest/name);assert sha(src/name)==sha(dest/name);upstream.append(src/name)
 for seed in SEEDS:
  p=E56/'models'/ds/f'graph_rl_{seed}';m=read(p/'model.json');iden=read(p/'selected/identity.json');assert m['construction_only'] and sha(p/'selected/W.f32')==sha(c['P'])==iden['W_sha']
  pool[ds].append(dict(pool[ds][0],model_name=f'E56_graph_rl_{seed}',W=str(p/'selected/W.f32'),graph_file=str(p/'selected/graph.hnsw'),prior_raw=str(p/'checkpoints'/f'{m["selected_step"]:04}.npz')))
 assert len(pool[ds])==19
 for m in pool[ds]:upstream.extend(Path(m[k]) for k in ['W','mapping','tie_ids','graph_file','prior_raw'])
 upstream.append(E55/'inputs'/ds/'config.json')
dump(O/'inputs/candidate_pool.json',pool)
split=read(E55/'reviews/split_isolation.json');assert split['status']=='PASS';split.update(source_stage='E55 exact copied split files; original provenance and vector isolation retained');dump(O/'reviews/split_isolation.json',split)
upstream.extend([E55/'inputs/candidate_pool.json',E55/'results/cal_selection.json',E55/'reviews/split_isolation.json',E55/'bin/evaluate'])
freeze(O/'reviews/upstream.json',upstream)
dump(O/'config.locked.json',dict(candidate_models_per_dataset=19,fit_points=38,cal_points=38,final_points=45,base_new_NSG=88768,max_NSG=719488,NSG_cap=750000,available_wall_repeats=225,threads=1,LS=LS,
 selection='max mean_U; lower total NDC; lower fixed pool index; default first; E56 seeds appended',reuse='Entire E55 dataset final matrix if best_new source identity unchanged',query_stop=QUERY_STOP))
for p in (O/'src').rglob('*.py'):ast.parse(p.read_text())
freeze(O/'reviews/prequery_freeze.json',[p for name in ['src','inputs','bin'] for p in (O/name).rglob('*') if p.is_file()]+[O/'protocol.md',O/'config.locked.json'])
dump(O/'state.json',dict(status='PREPARED_EXPANDED_COMPARISON',NSG_calls=0,selection_frozen=False));print('E57 PREPARED; max719488 new NSG',flush=True)
