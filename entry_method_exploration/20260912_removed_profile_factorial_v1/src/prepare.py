from shared import *
threads(8);resources()
assert not (O/'config.locked.json').exists()
for name in ['inputs','models','results','reviews','logs','figures','source_before']:(O/name).mkdir(exist_ok=True)
check(E41/'reviews/final_artifact_freeze.json')
freeze(O/'reviews/protected.json',[p for root in [E37,E38,E39,E40,E41] for p in files(root)])
check(E39/'reviews/native_dependencies.json')
shutil.copy2(E39/'reviews/native_dependencies.json',O/'reviews/native_dependencies.json')
for name in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md','experiment_history/30_profile_factorial.md']:
 shutil.copy2(R/name,O/'source_before'/name.replace('/','__'))
cases=read(E40/'results/attribution_cases.json')['cases'];identities=[]
for ca in cases:
 original_hub=ca['hub'];negative=next(x for x in ca['observations'] if int(x['delta_hits'])<0)
 removed=set(map(int,negative['center_entries'].split(';')))-set(map(int,negative['action_entries'].split(';')))
 assert len(removed)==1 and removed==set(map(int,negative['removed'].split(';')))
 ca['original_added_hub']=original_hub;ca['hub']=removed.pop();ca['target_selection']='unique_removed_hub_in_frozen_negative'
 assert ca['hub']=={'webvid2_5m_light_v1':1627796,'yandex_t2i_official10M_ip_v1':8309868}[ca['dataset']]
 ds=ca['dataset'];c=read(E39/'inputs'/ds/'config.json');c['native_call_cap']=4288
 inp=O/'inputs'/ds;inp.mkdir();dump(inp/'config.json',c)
 rows=np.load(E39/'inputs'/ds/'rows.npz')['rows'];assert len(np.unique(rows))==1024
 save_np(inp/'rows.npz',rows=rows)
 hub_ids=np.fromfile(c['hub_ids'],np.int32);slot=int(np.flatnonzero(hub_ids==ca['hub'])[0])
 cp=E39/'models'/ds/ca['context']/'center';fp=E39/'models'/ds/ca['context']/ca['action']
 C=np.fromfile(cp/'W.f32',np.float32).reshape(c['hub_count'],c['dim'])
 F=np.fromfile(fp/'W.f32',np.float32).reshape(C.shape)
 S=C.copy();S[slot]=F[slot];Rest=F.copy();Rest[slot]=C[slot]
 assert C[slot].tobytes()!=F[slot].tobytes()
 for cell,w in zip(CELLS,[C,F,S,Rest]):
  assert np.all(np.abs(np.linalg.norm(w.astype(float),axis=1)-1)<1e-4)
  dst=O/'models'/ds/cell;dst.mkdir(parents=True);w.tofile(dst/'W.f32')
  ident=dict(dataset=ds,cell=cell,W_sha=digest(w),target_hub=ca['hub'],target_slot=slot,
       changed_rows_from_C=int(np.any(w!=C,axis=1).sum()),changed_rows_from_F=int(np.any(w!=F,axis=1).sum()))
  if cell in ['C','F']:
   old=read((cp if cell=='C' else fp)/'identity.json')
   ident.update(expected_topology_sha=old['topology_sha'],expected_graph_sha=old['graph_file_sha'],old_result=str(E39/'results'/ds/ca['context']/('center.npz' if cell=='C' else ca['action']+'.npz')))
  dump(dst/'construction.json',ident);identities.append(ident)
 source=np.fromfile(c['row_ids'],np.int64)
 for obs in ca['observations']:
  assert int(rows[int(obs['qi'])])==int(obs['row']) and int(source[int(obs['row'])])==int(obs['source_row_id'])
 ca['target_slot']=slot
dump(O/'config.locked.json',dict(cases=cases,cells=CELLS,normal_NSG=8192,parity_NSG=384,expected_NSG=8576,
       hard_NSG_cap=10000,expected_HNSW=8448,expected_builds=8,optimizer_updates=0,threads=1,query_cpu=15))
freeze(O/'reviews/prequery_freeze.json',files(O/'src')+files(O/'inputs')+files(O/'models')+[O/'protocol.md',O/'config.locked.json'])
dump(O/'reviews/construction.json',dict(status='PASS',cells=identities))
dump(O/'state.json',dict(status='PREPARED_REMOVED_PROFILE_FACTORIAL',NSG_calls=0,builds=0,optimizer_updates=0))
print(json.dumps(identities,ensure_ascii=False),flush=True)
