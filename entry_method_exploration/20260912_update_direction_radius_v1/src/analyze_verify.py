from shared import *
from collections import Counter
threads(8);resources();started=time.monotonic();check(O/'reviews/prequery_freeze.json');assert all(read(O/'results'/ds/'query_complete.json')['status']=='PASS' for ds in DS)
points=[];contexts=[];scored=parity=graphs=patch_rows=endpoint=0
def ihits(ids,gt):return np.array([len(set(map(int,x))&set(map(int,g[:10]))) for x,g in zip(ids,gt)],np.int16)
def metrics(d):return dict(gain_hits=int(np.maximum(d,0).sum()),loss_hits=int(np.maximum(-d,0).sum()),net_hits=int(d.sum()),gain_queries=int((d>0).sum()),loss_queries=int((d<0).sum()))
for rec in read(O/'inputs/contexts.json'):
 ds=rec['dataset'];seed=rec['seed'];st=rec['step'];slot=rec['slot'];c=read(O/'inputs'/ds/'config.json');gt=np.fromfile(c['gt_file'],np.int64,count=4096*100).reshape(4096,100)
 p=np.fromfile(c['P'],np.float32).reshape(c['hub_count'],c['dim']);b=np.fromfile(c['basis'],np.float64).reshape(c['dim'],16);scale=np.load(E47/'inputs'/ds/'local_parameters.npz')['scale']
 t=dict(np.load(rec['trajectory']));inp=dict(np.load(rec['context']));w=np.fromfile(rec['current_W'],np.float32).reshape(p.shape);assert digest(w)==rec['current_W_sha']
 cur={k:inp['current_'+k] for k in FIELDS};mean={k:inp['mean_'+k] for k in FIELDS};best={k:inp['best_'+k] for k in FIELDS};assert raw_digest(cur)==str(t['current_cache_sha']) and raw_digest(mean)==str(t['mean_cache_sha'])
 bestidx=max(range(9),key=lambda i:(0. if i==0 else float(t['rewards'][i-1]),-i))-1;assert bestidx==rec['best_action']
 norms=[sum(float(x)**2 for x in row)**.5 for row in t['actions']-t['mu_before']];radius=sum(sorted(norms)[3:5])/2;np.testing.assert_allclose(radius,rec['radius'],atol=1e-15)
 direction=t['mu_after']-t['mu_before'];dn=sum(float(x)**2 for x in direction)**.5;direction=direction/dn if dn else np.zeros(16)
 expected=[t['mu_before']+f*radius*direction for f in [.25,.5,1.]]+[t['mu_before']+f*(np.zeros(16) if bestidx<0 else t['actions'][bestidx]-t['mu_before']) for f in [.25,.5]]
 for a,z in enumerate(expected):
  np.testing.assert_allclose(z,inp['unclipped'][a],atol=1e-15);zz=np.clip(z,-2,2);np.testing.assert_allclose(zz,inp['coeff'][a],atol=1e-15)
  rr=p[slot].astype(float).copy()
  if np.any(zz):
   for j in range(16):rr+=.0625*float(scale[slot])*float(np.tanh(zz[j]))*b[:,j]
   rr/=np.sqrt(rr@rr)
  np.testing.assert_allclose(rr,inp['proposed_rows'][a],atol=4e-8,rtol=1e-7)
 anchor=dict(np.load(E37/'results'/ds/'baseline.npz'));den=anchor['route_ndc'][:4096].astype(float)+anchor['graph_ndc'][:4096]
 tags=['C','M']+rec['tags'];raw=[];hh=[];djs=[];drifts=[]
 for i,tag in enumerate(tags):
  dest=O/'results'/ds/str(seed)/f'{st:04}'/tag;out=dict(np.load(dest/'raw.npz'));iden=read(dest/'identity.json');patch=dict(np.load(dest/'patch.npz'));ww=w.copy();row=t['current_row'] if tag=='C' else t['next_row'] if tag=='M' else inp['proposed_rows'][rec['tags'].index(tag)];ww[slot]=row
  assert digest(ww)==iden['W_sha'] and sha(dest/'raw.npz')==iden['raw_sha'];assert digest(np.load(dest/'topology.npz')['topology'])==iden['topology_sha']
  if tag in ['C','M']:equal(out,cur if tag=='C' else mean);assert iden['topology_sha']==rec['current_topology_sha' if tag=='C' else 'mean_topology_sha'];endpoint+=4096
  else:assert iden['W_sha']==rec['proposed_W_sha'][rec['tags'].index(tag)]
  changed=np.flatnonzero((out['entries']!=cur['entries']).any(1));assert np.array_equal(changed,patch['changed_rows']) and len(changed)==iden['new_NSG'];mask=np.ones(4096,bool);mask[changed]=False;patch_rows+=len(changed)
  for k in ['ids','distances','graph_ndc']:assert out[k][mask].tobytes()==cur[k][mask].tobytes() and out[k][changed].tobytes()==patch[k].tobytes()
  assert out['entries'][changed].tobytes()==patch['entries'].tobytes()
  if st in [20,200]:assert sha(dest/'graph.hnsw')==iden['graph_sha'];equal(dict(np.load(dest/'parity.npz')),subset(out,np.arange(16)));graphs+=1;parity+=16
  h=ihits(out['ids'],gt);scored+=4096;hh.append(h);raw.append(out)
  drift=float(t['current_drift'])+(np.square(row.astype(float)-p[slot]).sum()-np.square(t['current_row'].astype(float)-p[slot]).sum())/len(p);drifts.append(drift)
  d=h-hh[0];dc=out['route_ndc'].astype(np.int64)+out['graph_ndc']-cur['route_ndc']-cur['graph_ndc'];u=d-.1*dc/den-.1*((h==0).astype(int)-(hh[0]==0).astype(int));dj=float(u.mean()-(drift-float(t['current_drift'])));djs.append(dj)
  coef=t['mu_before'] if tag=='C' else t['mu_after'] if tag=='M' else inp['coeff'][rec['tags'].index(tag)]
  rr=dict(dataset=ds,seed=seed,step=st,tag=tag,**metrics(d),quality_null=bool(not np.any(d)),mean_delta_U=float(u.mean()),mean_delta_J=dj,
   new_zero_queries=int(((h==0)&(hh[0]>0)).sum()),rescued_zero_queries=int(((h>0)&(hh[0]==0)).sum()),delta_graph_NDC=int((out['graph_ndc'].astype(np.int64)-cur['graph_ndc']).sum()),delta_route_NDC=int((out['route_ndc'].astype(np.int64)-cur['route_ndc']).sum()),
   coefficient_displacement=float(np.linalg.norm(coef-t['mu_before'])),row_displacement=float(np.linalg.norm(row.astype(float)-t['current_row'])),clipped_coordinates=0 if tag in ['C','M'] else int(np.count_nonzero(inp['unclipped'][rec['tags'].index(tag)]!=inp['coeff'][rec['tags'].index(tag)])))
  points.append(rr)
 bh=ihits(best['ids'],gt);scored+=4096;bd=bh-hh[0];bj=0. if bestidx<0 else float(t['rewards'][bestidx]);local=[x for x in points if x['dataset']==ds and x['seed']==seed and x['step']==st]
 dsuc=any(x['tag'].startswith('D') and x['net_hits']>0 and x['mean_delta_J']>0 for x in local);bsuc=any(x['tag'].startswith('B') and x['net_hits']>0 and x['mean_delta_J']>0 for x in local)
 relevant=int(bd.sum())>0 and not np.any(hh[1]-hh[0]);kind='OUTSIDE_POSITIVE_CANDIDATE_MEAN_NULL_SUBSET'
 if relevant:kind='BOTH_D_AND_B_SUCCESS' if dsuc and bsuc else 'ONLY_D_SUCCESS' if dsuc else 'ONLY_B_SUCCESS' if bsuc else 'ONLY_FULL_CANDIDATE_SUCCESS'
 contexts.append(dict(dataset=ds,seed=seed,step=st,slot=slot,radius=radius,original_Adam_coefficient_step=dn,best_action=bestidx,**{'best_'+k:v for k,v in metrics(bd).items()},best_delta_J=bj,
  positive_candidate_mean_null=relevant,larger_Adam_success=dsuc,partial_best_direction_success=bsuc,classification=kind))
 dest=O/'results'/ds/str(seed)/f'{st:04}';save(dest/'derived.npz',hits=np.stack(hh),delta_hits=np.stack(hh)-hh[0],delta_J=np.array(djs),drifts=np.array(drifts),best_hits=bh,best_delta_hits=bd)
datasets=[]
for ds in DS:
 cc=[x for x in contexts if x['dataset']==ds];rr=[x for x in points if x['dataset']==ds];bytag={}
 for tag in ['C','M','D25','D50','D100','B25','B50']:
  tt=[x for x in rr if x['tag']==tag];bytag[tag]={k:sum(x[k] for x in tt) for k in ['gain_hits','loss_hits','net_hits','new_zero_queries','rescued_zero_queries','delta_graph_NDC','delta_route_NDC','clipped_coordinates']}
  bytag[tag].update(positive_contexts=sum(x['net_hits']>0 and x['mean_delta_J']>0 for x in tt),quality_null_contexts=sum(x['quality_null'] for x in tt),delta_J_sum=float(sum(x['mean_delta_J'] for x in tt)))
 datasets.append(dict(dataset=ds,contexts=20,positive_candidate_mean_null_contexts=sum(x['positive_candidate_mean_null'] for x in cc),classifications=dict(Counter(x['classification'] for x in cc)),tags=bytag))
for name,rows in [('points',points),('contexts',contexts)]:
 with (O/'results'/f'{name}.csv').open('w',newline='') as f:z=csv.DictWriter(f,fieldnames=list(rows[0]));z.writeheader();z.writerows(rows)
costs=[read(O/'results'/ds/'query_complete.json') for ds in DS];cost=dict(NSG_calls=sum(x['NSG_calls'] for x in costs),HNSW_calls=1148672,builds=280,states=280,new_counterfactual_states=200,parity_NSG=2688,optimizer_updates=0,new_development_queries=0,datasets=costs)
assert scored==1310720 and graphs==56 and parity==896 and endpoint==327680 and cost['NSG_calls']==patch_rows+2688
dump(O/'results/analysis.json',dict(datasets=datasets,contexts=contexts));dump(O/'results/cost.json',cost)
dump(O/'reviews/verification.json',dict(status='PASS',independent_set_scores=scored,states=280,coefficient_radius_controls=200,endpoint_bit_recovery_rows=endpoint,cache_identity_rows=1146880,new_patch_rows=patch_rows,
 physical_graphs=graphs,three_way_parity_rows=parity,new_search=0,seconds=time.monotonic()-started))
print(json.dumps(datasets,ensure_ascii=False,indent=2),flush=True)
