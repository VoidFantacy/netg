from common import *
assert not (O/'reviews/E37_preserved.json').exists()
assert read(E/'state.json')['final_audit']=='PASS'
for folder in ['reviews','source_before','results','figures','logs']:(O/folder).mkdir(exist_ok=True)
docs=['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md','experiment_history/26_offline_profile_rl.md']
for doc in docs:shutil.copy2(R/doc,O/'source_before'/doc.replace('/','__'))
files=sorted(p for p in E.rglob('*') if p.is_file());dump(O/'reviews/E37_preserved.json',dict(files=[ident(p) for p in files],file_count=len(files),created_at=time.time()))
dump(O/'state.json',dict(status='PREPARED_EXISTING_OUTPUT_ANALYSIS_ONLY',new_NSG=0,new_HNSW_queries=0,new_graph_builds=0,optimizer_updates=0,validation_heldout_raw_access=False))
print('PREPARED',len(files),'E37 files SHA frozen',flush=True)
