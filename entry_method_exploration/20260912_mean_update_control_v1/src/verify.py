from shared import *
threads(8);resources();started=time.monotonic();check(O/'reviews/prequery_freeze.json')
report=read(O/'results/analysis.json');scored=graphs=parity=0
def ihits(ids,gt):return np.array([len(set(map(int,a))&set(map(int,b[:10]))) for a,b in zip(ids,gt)],np.int16)
for rec in read(O/'inputs/contexts.json'):
 ds=rec['dataset'];step=rec['step'];slot=rec['slot'];c=read(O/'inputs'/ds/'config.json');gt=np.fromfile(c['gt_file'],np.int64).reshape(5120,100)[:4096]
 p=np.fromfile(c['P'],np.float32).reshape(c['hub_count'],c['dim']);b=np.fromfile(c['basis'],np.float64).reshape(c['dim'],16);scale=np.load(E43/'inputs'/ds/'local_parameters.npz')['scale']
 up=dict(np.load(O/'inputs'/ds/f'{step:04}_updates.npz'));t=dict(np.load(rec['trajectory']));cp=dict(np.load(rec['checkpoint']))
 oldmu=cp['mu'][slot].copy();oldm=cp['m'][slot].copy();oldv=cp['v'][slot].copy();oldcount=int(cp['counts'][slot])
 for k in range(((step-1)//20)*20+1,step):
  tt=dict(np.load(E43/'models'/ds/'rl_20260921'/'trajectory'/f'{k:04}.npz'))
  if int(tt['slot'])==slot:oldmu=tt['mu_after'];oldm=tt['m_after'];oldv=tt['v_after'];oldcount=int(tt['local_count'])
 for name,value in [('mu_before',oldmu),('m_before',oldm),('v_before',oldv)]:assert up[name].tobytes()==value.tobytes()
 assert int(up['count_before'])==oldcount
 assert up['batch_mu'].tobytes()==t['mu_after'].tobytes() and up['batch_row'].tobytes()==t['next_row'].tobytes()
 assert up['full_gradient'].tobytes()==np.load(E44/'results'/ds/f'{step:04}'/'derived.npz')['full_gradient'].tobytes()
 for tag in ['batch','full']:
  g=up[tag+'_gradient'];norm=sum(float(x)**2 for x in g)**.5;nn=oldcount+1;lr=.003+.0135*(1+np.cos(np.pi*(step-1)/199))
  mu=[];mm=[];vv=[]
  for j in range(16):
   gj=float(g[j])/max(1.,norm);mj=.9*float(oldm[j])+.1*gj;vj=.999*float(oldv[j])+.001*gj*gj
   x=float(oldmu[j])+lr*(mj/(1-.9**nn))/((vj/(1-.999**nn))**.5+1e-8);mu.append(max(-2.,min(2.,x)));mm.append(mj);vv.append(vj)
  np.testing.assert_allclose(mu,up[tag+'_mu'],atol=2e-14);np.testing.assert_allclose(mm,up[tag+'_m'],atol=2e-14);np.testing.assert_allclose(vv,up[tag+'_v'],atol=2e-14)
  row=np.array([float(p[slot,j])+.0625*float(scale[slot])*sum(float(np.tanh(mu[k]))*float(b[j,k]) for k in range(16)) for j in range(c['dim'])])
  if any(mu):row/=np.linalg.norm(row)
  else:row=p[slot].astype(float)
  np.testing.assert_allclose(row,up[tag+'_row'],atol=4e-8,rtol=1e-7)
 w=np.fromfile(rec['current_W'],np.float32).reshape(p.shape);assert digest(w)==rec['current_W_sha']
 raw=[dict(np.load(rec['current_raw']))]+[dict(np.load(O/'results'/ds/f'{step:04}'/tag/'raw.npz')) for tag in ['batch','full']]
 derived=dict(np.load(O/'results'/ds/f'{step:04}'/'derived.npz'));hh=[]
 for i,tag in enumerate(['C','batch','full']):
  dest=O/'results'/ds/f'{step:04}'/tag;stored=dict(np.load(dest/'raw.npz'));iden=read(dest/'identity.json');ww=w.copy()
  if tag!='C':ww[slot]=up[tag+'_row']
  assert digest(ww)==iden['W_sha'];assert sha(dest/'graph.hnsw')==iden['graph_sha'] and sha(dest/'raw.npz')==iden['raw_sha']
  assert digest(np.load(dest/'topology.npz')['topology'])==iden['topology_sha']
  if tag=='C':assert iden['topology_sha']==rec['current_topology_sha'];equal(stored,subset(raw[0],np.arange(16)))
  equal(dict(np.load(dest/'parity.npz')),subset(raw[i],np.arange(16)));graphs+=1;parity+=16
  hits=ihits(raw[i]['ids'],gt);np.testing.assert_array_equal(hits,derived['hits'][i]);hh.append(hits);scored+=4096
 hh=np.stack(hh);dh=hh[1:]-hh[0];np.testing.assert_array_equal(dh,derived['delta_hits'])
 base=dict(np.load(E37/'results'/ds/'baseline.npz'));den=base['route_ndc'][:4096].astype(float)+base['graph_ndc'][:4096];du=[]
 for i in [1,2]:
  delta_ndc=raw[i]['route_ndc'].astype(np.int64)+raw[i]['graph_ndc']-raw[0]['route_ndc']-raw[0]['graph_ndc']
  du.append(hh[i]-hh[0]-.1*delta_ndc/den-.1*((hh[i]==0).astype(int)-(hh[0]==0).astype(int)))
 np.testing.assert_allclose(du,derived['delta_U'],atol=3e-15)
 rr=next(x for x in report['contexts'] if x['dataset']==ds and x['step']==step)
 for tag,i,j in [('batch',1,0),('full',2,0),('full_vs_batch',2,1)]:
  diff=hh[i]-hh[j];assert sum(int(v) for v in diff if v>0)==rr[tag+'_gain_hits'] and -sum(int(v) for v in diff if v<0)==rr[tag+'_loss_hits']
  assert int(sum(diff))==rr[tag+'_net_hits'];assert int(((hh[i]==0)&(hh[j]>0)).sum())==rr[tag+'_new_zero_queries']
  delta=du[i-1] if j==0 else np.array(du[1])-du[0];np.testing.assert_allclose(float(np.mean(delta)),rr[tag+'_mean_delta_U'],atol=2e-16)
for ds in DS:
 rr=[x for x in report['contexts'] if x['dataset']==ds];dr=next(x for x in report['datasets'] if x['dataset']==ds)
 for tag in ['batch','full','full_vs_batch']:
  for field in ['gain_hits','loss_hits','net_hits','gain_queries','loss_queries','new_zero_queries','rescued_zero_queries']:assert sum(x[tag+'_'+field] for x in rr)==dr[tag+'_'+field]
 passed=dr['full_net_hits']>0 and dr['full_mean_delta_U']>0 and dr['full_vs_batch_net_hits']>=0 and dr['full_vs_batch_mean_delta_U']>0 and dr['full_graph_NDC_change_pct']<=1
 assert passed==dr['passed']
assert scored==245760 and graphs==60 and parity==960
dump(O/'reviews/verification.json',dict(status='PASS',independent_full_set_scores=scored,reused_current_rows=81920,new_full_update_rows=163840,
 current_bit_regression_rows=320,graphs=60,three_way_parity_rows=960,independent_Adam_steps=40,new_counterfactual_steps=20,historical_steps_replayed=20,
 continuous_training_updates=0,new_search=0,seconds=time.monotonic()-started))
print('E45 independent verification PASS',flush=True)
