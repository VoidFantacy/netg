from common import *
contract();start=time.monotonic()
neighbors=list(csv.DictReader((O/'results/query_neighbors.csv').open()))
pairs=list(csv.DictReader((O/'results/query_pairs.csv').open()))
sets={};checked=0
for ds in DS:
 c,rows,q,gt,source,hubs=inputs(ds);q=q/np.linalg.norm(q,axis=1,keepdims=True)
 lookup={int(row):i for i,row in enumerate(rows)}
 for row in rows:
  qi=lookup[int(row)];saved=sorted([x for x in neighbors if x['dataset']==ds and int(x['row'])==row],key=lambda x:int(x['rank']))
  assert len(saved)==5
  all_scores=np.array([np.dot(q[qi],q[j]) if qi!=j else -2 for j in range(1024)])
  selected=[lookup[int(x['neighbor_row'])] for x in saved]
  outside=np.ones(1024,bool);outside[selected]=False
  assert min(all_scores[selected])>=max(all_scores[outside])-1e-12
  assert qi not in selected and len(set(selected))==5
  for x,j in zip(saved,selected):assert abs(float(x['cosine'])-all_scores[j])<1e-12
  sets[ds,int(row)]=set(int(x['neighbor_row']) for x in saved);checked+=5
 for name in ['zero','selected']:
  ps=[p for p in pairs if p['dataset']==ds and p['context']==name]
  positive=set(int(p[k]) for p in ps for k in ['row_a','row_b']);positive_sets={}
  for row in positive:
   candidates=[r for r in positive if r!=row]
   ordered=sorted(candidates,key=lambda r:(-float(q[lookup[row]]@q[lookup[r]]),r))[:5]
   positive_sets[row]=set(ordered)
  for p in ps:
   a,b=int(p['row_a']),int(p['row_b'])
   assert (p['nearest5_all']=='True')==(b in sets[ds,a] or a in sets[ds,b])
   assert (p['nearest5_positive']=='True')==(b in positive_sets[a] or a in positive_sets[b])
assert checked==10240
dump(O/'reviews/neighborhood_verification.json',dict(status='PASS',nearest_query_rows_checked=checked,
     pair_neighborhood_flags_checked=len(pairs),seconds=time.monotonic()-start,new_ANN_calls=0))
print('Neighborhood verification PASS')
