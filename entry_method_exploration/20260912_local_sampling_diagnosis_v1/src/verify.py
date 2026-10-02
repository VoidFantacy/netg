from shared import *
threads(8);resources();started=time.monotonic();check(O/'reviews/prequery_freeze.json')
report=read(O/'results/analysis.json');scored=regression=parity=graphs=coordinates=0
def independent_hits(ids,gt):
 return np.array([len(set(map(int,a))&set(map(int,b[:10]))) for a,b in zip(ids,gt)],dtype=np.int16)
def independent_gradient(values,eps):
 out=np.zeros((16,values.shape[1]))
 for j in range(16):
  for i in range(8):
   others=sum(values[k] for k in range(8) if k!=i)/7
   out[j]+=(values[i]-others)*float(eps[i,j])/(8*.3)
 return out
def scalar_variance(g,rows,n):
 if len(rows)<=1 or len(rows)==n:return 0.
 out=0.
 for j in range(16):
  x=g[j,rows];mean=float(sum(x)/len(x));ss=float(np.dot(x-mean,x-mean))
  out+=(1-n/len(x))*ss/((len(x)-1)*n)
 return out
for rec in read(O/'inputs/contexts.json'):
 ds=rec['dataset'];step=rec['step'];c=read(O/'inputs'/ds/'config.json');gt=np.fromfile(c['gt_file'],np.int64).reshape(5120,100)[:4096]
 base=dict(np.load(E37/'results'/ds/'baseline.npz'));t=dict(np.load(rec['trajectory']));eps=t['eps'];d=dict(np.load(O/'results'/ds/f'{step:04}'/'derived.npz'))
 hubs=np.fromfile(c['hub_ids'],np.int32);assert int(hubs[rec['slot']])==rec['hub']
 near=np.array([rec['hub'] in row for row in base['entries'][:4096]],bool);assert np.array_equal(near,d['near'])
 p=np.fromfile(c['P'],np.float32).reshape(c['hub_count'],c['dim']);w=np.fromfile(rec['current_W'],np.float32).reshape(p.shape)
 drift=[];raws=[];hits=[]
 for a in range(-1,8):
  dest=O/'results'/ds/f'{step:04}'/('C' if a<0 else f'A{a}');raw=dict(np.load(dest/'raw.npz'));identity=read(dest/'identity.json')
  assert sha(dest/'raw.npz')==identity['raw_sha'];assert digest(np.load(dest/'topology.npz')['topology'])==identity['topology_sha']
  expected=rec['current_topology_sha'] if a<0 else rec['candidate_topology_sha'][a];assert identity['topology_sha']==expected
  ww=w.copy()
  if a>=0:ww[rec['slot']]=t['candidate_rows'][a]
  assert digest(ww)==identity['W_sha'];drift.append(float(np.einsum('ij,ij->',ww.astype(float)-p,ww.astype(float)-p)/len(p)))
  hh=independent_hits(raw['ids'],gt);assert np.array_equal(hh,d['hits'][a+1]);hits.append(hh);raws.append(raw);scored+=4096;graphs+=1
  equal(subset(raw,t['rows']),{k:t['current_'+k] if a<0 else t[k][a] for k in FIELDS});regression+=128
  if step in [20,200]:
   assert sha(dest/'graph.hnsw')==identity['graph_sha'];equal(dict(np.load(dest/'parity.npz')),subset(raw,np.arange(16)));parity+=16
 h=np.stack(hits);dh=h[1:]-h[0];assert np.array_equal(dh,d['delta_hits'])
 den=(base['route_ndc'][:4096].astype(float)+base['graph_ndc'][:4096]);du=[]
 for a in range(8):
  nd=raws[a+1]['route_ndc'].astype(np.int64)+raws[a+1]['graph_ndc']-raws[0]['route_ndc']-raws[0]['graph_ndc']
  du.append(dh[a]-.1*nd/den-.1*((h[a+1]==0).astype(int)-(h[0]==0).astype(int)))
 du=np.array(du);np.testing.assert_allclose(du,d['delta_U'],atol=3e-15)
 gu=independent_gradient(du,eps);gh=independent_gradient(dh,eps);np.testing.assert_allclose(gu,d['gradient_U'],atol=3e-14);np.testing.assert_allclose(gh,d['gradient_hits'],atol=3e-14)
 dd=-np.array(drift[1:])+drift[0];gd=independent_gradient(dd[:,None],eps)[:,0]
 np.testing.assert_allclose(gd,d['gradient_drift'],atol=2e-17)
 old=gu[:,t['rows']].mean(1)+gd;np.testing.assert_allclose(old,t['gradient'],atol=3e-14)
 np.testing.assert_allclose(gu.mean(1)+gd,d['full_gradient'],atol=2e-14)
 rr=next(x for x in report['contexts'] if x['dataset']==ds and x['step']==step)
 for name,g in [('U',gu),('hit',gh)]:
  vu=scalar_variance(g,np.arange(4096),128);vs=0.
  for mask,n in [(near,rec['near_sample']),(~near,rec['far_sample'])]:
   rows=np.flatnonzero(mask)
   if len(rows):vs+=(len(rows)/4096)**2*scalar_variance(g,rows,n)
  np.testing.assert_allclose(vu,rr[name+'_uniform_variance'],rtol=2e-12,atol=1e-20)
  np.testing.assert_allclose(vs,rr[name+'_stratified_variance'],rtol=2e-12,atol=1e-20);coordinates+=16
 for a in range(8):
  aa=next(x for x in report['actions'] if x['dataset']==ds and x['step']==step and x['action']==a)
  for mask,prefix in [(np.ones(4096,bool),''),(near,'near_'),(~near,'far_')]:
   x=dh[a,mask];assert sum(int(v) for v in x if v>0)==aa[prefix+'gain_hits'];assert -sum(int(v) for v in x if v<0)==aa[prefix+'loss_hits']
  assert aa['net_hits']==int(sum(dh[a]));assert aa['entry_change_queries']==int(np.any(raws[a+1]['entries']!=raws[0]['entries'],axis=1).sum())
 oracle=sum(max(0,*map(int,dh[:,q])) for q in range(4096));nets=[0]+[int(sum(row)) for row in dh]
 assert oracle==rr['oracle_hit_gain'] and max(nets)==rr['best_net_hits']
 assert oracle-max(nets)==rr['oracle_coverage_gap']+rr['oracle_cancellation_gap']
 affected=np.any(dh!=0,axis=0);assert int(affected.sum())==rr['full_affected_queries'] and int(affected[t['rows']].sum())==rr['old_affected_queries']
for ds in DS:
 rr=[x for x in report['contexts'] if x['dataset']==ds];dr=next(x for x in report['datasets'] if x['dataset']==ds)
 q=sum(x['hit_population_variance']>1e-18 for x in rr);uv=sum(x['U_uniform_variance'] for x in rr);sv=sum(x['U_stratified_variance'] for x in rr)
 nz=[x for x in rr if x['U_uniform_variance']>1e-18];nw=sum(x['U_stratified_variance']<=x['U_uniform_variance'] for x in nz)/len(nz) if nz else None
 passed=q>=4 and uv>1e-18 and sv/uv<=.5 and nw is not None and nw>=.6;assert passed==dr['passed']
cost=read(O/'results/cost.json');assert cost['NSG_calls']==739008 and cost['HNSW_calls']==738432 and cost['builds']==180
assert scored==737280 and regression==23040 and parity==576 and graphs==180
dump(O/'reviews/verification.json',dict(status='PASS',independent_set_scores=scored,old_bit_regression_rows=regression,
 serialized_three_way_parity_rows=parity,graphs=graphs,scalar_variance_coordinates=coordinates,old_gradients=20,
 verified_gate=read(O/'results/gate.json')['status'],new_search=0,seconds=time.monotonic()-started))
print('E44 independent verification PASS',scored,'set scores',flush=True)
