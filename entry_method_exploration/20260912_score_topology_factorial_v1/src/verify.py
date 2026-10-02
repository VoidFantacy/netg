from shared import *
threads(8);resources();started=time.monotonic();check(O/'reviews/prequery_freeze.json')
report=read(O/'results/analysis.json');scored=endpoint=parity=graphs=states=patches=0
def hits_set(ids,gt):return np.array([len(set(map(int,a))&set(map(int,b[:10]))) for a,b in zip(ids,gt)],np.int16)
for rec in read(O/'inputs/contexts.json'):
 ds=rec['dataset'];step=rec['step'];c=read(O/'inputs'/ds/'config.json');gt=np.fromfile(c['gt_file'],np.int64).reshape(5120,100)[:4096]
 dest=O/'results'/ds/f'{step:04}';old=E44/'results'/ds/f'{step:04}';parent=dict(np.load(old/'C/raw.npz'));w=np.fromfile(rec['current_W'],np.float32).reshape(c['hub_count'],c['dim']);t=dict(np.load(rec['trajectory']))
 tags=['C']+[f'{f}{a}' for f in ['A','S','T'] for a in range(8)];hh=[];rr=[]
 derived=dict(np.load(dest/'derived.npz'))
 for i,tag in enumerate(tags):
  folder=dest/tag;raw=dict(np.load(folder/'raw.npz'));iden=read(folder/'identity.json');patch=dict(np.load(folder/'patch.npz'));top=np.load(folder/'topology.npz')['topology'];ww=w.copy()
  if tag!='C' and tag[0] in ['A','S']:ww[rec['slot']]=t['candidate_rows'][int(tag[1:])]
  expected=rec['current_topology_sha'] if tag=='C' or tag[0]=='S' else rec['candidate_topology_sha'][int(tag[1:])]
  assert digest(ww)==iden['W_sha'] and digest(top)==expected==iden['topology_sha'] and iden['vector_bytes_match']
  assert sha(folder/'raw.npz')==iden['raw_sha'];rows=np.flatnonzero((raw['entries']!=parent['entries']).any(1));assert np.array_equal(rows,patch['changed_rows'])
  assert len(rows)==iden['new_NSG'];mask=np.ones(4096,bool);mask[rows]=False
  for k in ['ids','distances','graph_ndc']:
   assert raw[k][mask].tobytes()==parent[k][mask].tobytes();assert raw[k][rows].tobytes()==patch[k].tobytes()
  assert raw['entries'][rows].tobytes()==patch['entries'].tobytes();patches+=len(rows)
  if tag=='C' or tag[0]=='A':equal(raw,dict(np.load(old/tag/'raw.npz')));endpoint+=4096
  if step in [20,200]:
   assert sha(folder/'graph.hnsw')==iden['graph_sha'];equal(dict(np.load(folder/'parity.npz')),subset(raw,np.arange(16)));parity+=16;graphs+=1
  h=hits_set(raw['ids'],gt);assert np.array_equal(h,derived['hits'][i]);hh.append(h);rr.append(raw);scored+=4096;states+=1
 hh=np.stack(hh);delta=(hh[1:]-hh[0]).reshape(3,8,4096);assert np.array_equal(delta,derived['delta_hits'])
 # Conditional margins derive independently from the four absolute hit arrays.
 A=hh[1:9];S=hh[9:17];T=hh[17:25];C=hh[0]
 for k,value in [('score_alone',S-C),('score_with_new_topology',A-T),('topology_alone',T-C),('topology_with_new_score',A-S),('interaction_hits',A-S-T+C)]:assert np.array_equal(value,derived[k])
 base=dict(np.load(E37/'results'/ds/'baseline.npz'));den=base['route_ndc'][:4096].astype(float)+base['graph_ndc'][:4096]
 for f,family in enumerate(['A','S','T']):
  for a in range(8):
   i=1+f*8+a;x=rr[i];d=delta[f,a];dc=x['route_ndc'].astype(np.int64)+x['graph_ndc']-rr[0]['route_ndc']-rr[0]['graph_ndc']
   u=d-.1*dc/den-.1*((hh[i]==0).astype(int)-(hh[0]==0).astype(int));np.testing.assert_allclose(u,derived['delta_U'][f,a],atol=3e-15)
   ar=next(x for x in report['actions'] if x['dataset']==ds and x['step']==step and x['action']==a)
   assert sum(int(v) for v in d if v>0)==ar[family+'_gain_hits'];assert -sum(int(v) for v in d if v<0)==ar[family+'_loss_hits'];assert sum(map(int,d))==ar[family+'_net_hits']
  cr=next(x for x in report['contexts'] if x['dataset']==ds and x['step']==step and x['family']==family)
  oracle=sum(max(0,*map(int,delta[f,:,q])) for q in range(4096));best=max([0]+[sum(map(int,row)) for row in delta[f]])
  assert oracle==cr['oracle_hits'] and best==cr['best_net_hits'];assert oracle-best==cr['uncovered_oracle_hits']+cr['own_loss_gap']
gate=read(O/'results/gate.json');passed=[]
for dsr in report['datasets']:
 for f in ['S','T']:
  a=dsr['A'];m=dsr[f];yes=m['gain_hits']>0 and a['gain_hits']>0 and m['gain_hits']>=.75*a['gain_hits'] and m['loss_hits']<=.5*a['loss_hits'] and m['best_net_hits']>=a['best_net_hits'];assert yes==m['followup_pass']
assert gate['qualifying_factors']==[f for f in ['S','T'] if all(x[f]['followup_pass'] for x in report['datasets'])]
cost=read(O/'results/cost.json');jobs=read(O/'logs/jobs.json');assert all(x['status']=='COMPLETE' for x in jobs)
assert sum(x['actual'] for x in jobs)==cost['NSG_calls']==patches+4800
assert states==500 and scored==2048000 and endpoint==737280 and graphs==100 and parity==1600
dump(O/'reviews/verification.json',dict(status='PASS',states=states,independent_set_scores=scored,endpoint_bit_recovery_rows=endpoint,cache_identity_rows=scored,
 new_patch_rows=patches,physical_graphs=graphs,three_way_parity_rows=parity,query_interaction_cells=655360,invalid_topologies_rejected=8,new_search=0,seconds=time.monotonic()-started))
print('E48 independent verification PASS',flush=True)
