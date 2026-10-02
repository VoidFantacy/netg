from common import *
threads();records=[]
for ds in DS:
 f=O/'results'/ds/'fit';b=dict(np.load(f/'compact_baseline.npz'));u=dict(np.load(f/'utility10.npz'));es=read(f/'edge_statistics.json');v=np.zeros(20000,np.int32)
 for e in es:
  if e['accepted']:
   a=np.load(f/('edge_%03d.npz'%e['candidate']));v[a['rows']]+=a['hits'].astype(np.int32)-b['hits'][a['rows']].astype(np.int32)
 actual=u['hits'].astype(np.int32)-b['hits'].astype(np.int32)
 save(f/'merged_interaction.npz',independent_delta=v,merged_delta=actual,nonadditive_rows=np.flatnonzero(v!=actual))
 records.append(dict(dataset=ds,independent_selected_sum=int(v.sum()),actual_merged_sum=int(actual.sum()),nonadditive_queries=int(np.count_nonzero(v!=actual))))
dump(O/'reviews/merged_interaction.json',dict(status='PASS',records=records,scope='Frozen single-edge and union returns; no new query or selection.'))
check(O/'reviews/prequery_freeze.json');resources()
freeze(O/'reviews/final_artifact_freeze.json',[p for p in O.rglob('*') if p.is_file()])
print('E87_FINAL_SEALED',records)
