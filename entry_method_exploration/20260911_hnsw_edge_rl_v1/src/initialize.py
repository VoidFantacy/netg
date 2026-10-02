from common import *

assert not (O/'reviews/protected_before.json').exists()
# Preserve E32 exactly and record earlier protection identities without reading unrelated validation bytes.
older=read(E32/'reviews/protected_before.json')
dump(O/'reviews/older_protection_reference.json',older)
files=[p for p in E32.rglob('*') if p.is_file() and '__pycache__' not in str(p)]
deps=[R/'ACSG/ACSG.cpp',R/'ACSG/ACSG.h',R/'ACSG/IndexACSG.cpp',R/'ACSG/IndexACSG.h',R/'build/ACSG/libACSG.a',R/'build/MRNN_Descent/libmrnndescent.a',R/'build/faiss/faiss/libfaiss.a']
deps += list((R/'benches/hnswlib').glob('*.h'))
for ds in DS:
 c=read(E28/'inputs'/ds/'propose.json');c.pop('anchor');c.pop('policies');c.update(policy=policy(ds),graph_file=str(O/'inputs'/ds/'base.hnsw'))
 assert Path(c['policy']['W']).is_file()
 dump(O/'inputs'/ds/'config.json',c)
 permutation=np.random.default_rng(20260913).permutation(20000).astype(np.int32)
 permutation[:16000].tofile(O/'inputs'/ds/'train_rows.i32');permutation[16000:].tofile(O/'inputs'/ds/'monitor_rows.i32')
 deps += [Path(c[k]) for k in ['queries_file','gt_file','row_ids','hub_ids','index_path']]+[Path(c['policy']['W'])]
 # Explicitly no cal/audit/validation/held-out data access here.
for p in sorted(set(deps)):assert p.exists(),p
freeze(O/'reviews/protected_before.json',files+deps)
dump(O/'reviews/access_scope.json',dict(fit_hash=True,fit_decoded=False,cal_decoded=False,audit_decoded=False,validation_decoded=False,heldout_hash=False,heldout_decoded=False,older_validation_stat_only=True))
dump(O/'state.json',dict(status='IMPLEMENTATION_IN_PROGRESS',real_calls=0,optimizer_updates=0))
dump(O/'reviews/source_dependencies.json',[str(p) for p in sorted(set(deps))])
print('INITIALIZE_PASS',len(files),len(set(deps)),flush=True)
