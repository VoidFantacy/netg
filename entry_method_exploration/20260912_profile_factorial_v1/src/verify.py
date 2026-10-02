from shared import *
threads(8);resources();start=time.monotonic();check(O/'reviews/prequery_freeze.json')
diagnosis=read(O/'results/diagnosis.json');set_scored=0;old_regression=0;parity_rows=0
for ds in DS:
 c=cfg(ds);ca=case(ds);slot=ca['target_slot'];rows=np.load(O/'inputs'/ds/'rows.npz')['rows']
 assert len(rows)==1024 and len(set(map(int,rows)))==1024 and np.array_equal(rows,np.load(E39/'inputs'/ds/'rows.npz')['rows'])
 hubs=np.fromfile(c['hub_ids'],np.int32);assert int(hubs[slot])==ca['hub']
 dim=c['dim'];shape=(c['hub_count'],dim)
 wc=np.fromfile(E39/'models'/ds/ca['context']/'center/W.f32',np.float32).reshape(shape)
 wf=np.fromfile(E39/'models'/ds/ca['context']/ca['action']/'W.f32',np.float32).reshape(shape)
 gt=np.fromfile(c['gt_file'],np.int64).reshape(4096,100)[rows]
 base=dict(np.load(E37/'results'/ds/'baseline.npz'))
 p=np.fromfile(c['P'],np.float32).reshape(shape)
 all_hits=[];all_u=[];raw={};all_drift=[]
 for cell in CELLS:
  w=np.fromfile(O/'models'/ds/cell/'W.f32',np.float32).reshape(shape)
  for i in range(len(hubs)):
   take_f=cell=='F' or (cell=='S' and i==slot) or (cell=='R' and i!=slot)
   assert w[i].tobytes()==(wf if take_f else wc)[i].tobytes(),(ds,cell,i)
  raw[cell]=dict(np.load(O/'results'/ds/(cell+'.npz')));assert np.array_equal(raw[cell]['rows'],rows)
  hh=[];uu=[]
  for i in range(1024):
   returned=set(map(int,raw[cell]['ids'][i]));truth=set(map(int,gt[i,:10]));assert len(returned)==len(truth)==10
   value=len(returned&truth);hh.append(value);set_scored+=1
   h0=len(set(map(int,base['ids'][rows[i]]))&truth)
   assert h0==int(base['hits'][rows[i]])
   total=int(raw[cell]['route_ndc'][i])+int(raw[cell]['graph_ndc'][i])
   total0=int(base['route_ndc'][rows[i]])+int(base['graph_ndc'][rows[i]])
   uu.append(value-h0-.1*(total/total0-1)-.1*(int(value==0)-int(h0==0)))
  all_hits.append(hh);all_u.append(uu)
  all_drift.append(sum(sum((float(a)-float(b))**2 for a,b in zip(wi,pi)) for wi,pi in zip(w,p))/len(w))
  if cell in ['C','F']:
   old=dict(np.load(E39/'results'/ds/ca['context']/('center.npz' if cell=='C' else ca['action']+'.npz')))
   equal(raw[cell],old);old_regression+=1024
  par=dict(np.load(O/'models'/ds/cell/'parity.npz'))
  equal(par,{k:raw[cell][k][:16] for k in FIELDS});assert np.array_equal(par['rows'],rows[:16]);parity_rows+=16
 h=np.array(all_hits,dtype=np.int16);u=np.array(all_u);derived=dict(np.load(O/'results'/ds/'derived.npz'))
 assert np.array_equal(h,derived['hits']) and np.array_equal(h-h[0],derived['delta'])
 np.testing.assert_allclose(u,derived['U'],rtol=1e-13,atol=1e-13)
 interaction=np.array([int(h[1,i])-int(h[2,i])-int(h[3,i])+int(h[0,i]) for i in range(1024)])
 assert np.array_equal(interaction,derived['interaction'])
 np.testing.assert_allclose(u[1]-u[2]-u[3]+u[0],derived['interaction_U'],rtol=1e-12,atol=1e-12)
 for ai,cell in enumerate(CELLS):
  m=next(x for x in diagnosis['metrics'] if x['dataset']==ds and x['cell']==cell)
  gain=sum(max(int(h[ai,i])-int(h[0,i]),0) for i in range(1024))
  loss=sum(max(int(h[0,i])-int(h[ai,i]),0) for i in range(1024))
  assert m['gain_hits']==gain and m['loss_hits']==loss and m['net_hits']==gain-loss
  np.testing.assert_allclose(m['delta_recall_pp'],(gain-loss)*10/1024,atol=1e-14)
  np.testing.assert_allclose(m['drift'],all_drift[ai],rtol=1e-12,atol=1e-14)
  np.testing.assert_allclose(m['reward_delta_from_C'],(u[ai]-u[0]).mean()-(all_drift[ai]-all_drift[0]),rtol=1e-12,atol=1e-12)
 s=next(x for x in diagnosis['datasets'] if x['dataset']==ds)
 positive=next(o for o in ca['observations'] if int(o['delta_hits'])>0);negative=next(o for o in ca['observations'] if int(o['delta_hits'])<0)
 pi,ni=int(positive['qi']),int(negative['qi'])
 assert (int(h[0,pi]),int(h[1,pi]))==(int(positive['center_hits']),int(positive['action_hits']))
 assert (int(h[0,ni]),int(h[1,ni]))==(int(negative['center_hits']),int(negative['action_hits']))
 assert s['specified_gain_fully_retained']==bool(h[2,pi]>=h[1,pi])
 assert s['specified_damage_eliminated']==bool(h[2,ni]>=h[0,ni])
 assert s['local_case_isolation_signal']==bool(h[2,pi]>=h[1,pi] and h[2,ni]>=h[0,ni])
 assert s['interaction_sum']==int(interaction.sum()) and s['interaction_nonzero_queries']==int((interaction!=0).sum())
 for i,a in enumerate(CELLS):
  for b in CELLS[i+1:]:
   same=np.all(raw[a]['entries']==raw[b]['entries'],axis=1)
   for k in ['ids','distances','graph_ndc']:assert raw[a][k][same].tobytes()==raw[b][k][same].tobytes()
assert set_scored==8192 and old_regression==4096 and parity_rows==128
dump(O/'reviews/independent_verification.json',dict(status='PASS',set_scored=set_scored,
     old_full_regression=old_regression,parity_rows=parity_rows,W_constructions=8,metrics=8,
     interaction_queries=2048,frozen_case_queries=4,seconds=time.monotonic()-start,
     extra_NSG=0,optimizer_updates=0))
print(json.dumps(read(O/'reviews/independent_verification.json')))
