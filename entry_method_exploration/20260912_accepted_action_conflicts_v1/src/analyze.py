from shared import *
from graph_bytes import inspect_serialized
threads(8);resources();check(O/'reviews/prequery_freeze.json');started=time.monotonic()
totals=dict(steps=0,accepted=0,monitor_patch_scores=0,historical_train_patch_scores=0,checkpoint_monitor_rows=0,checkpoint_train_rows=0,parity_rows=0,serialized_profile_rows=0)
runs=[];steps_all=[];query_rows=[];hub_rows=[];costs=[]
def ihits(ids,gg):return np.fromiter((len(set(map(int,a))&set(map(int,b[:10]))) for a,b in zip(ids,gg)),np.uint8,count=len(ids))
def change(a,b):
 d=a.astype(int)-b;return dict(gain_hits=int(np.maximum(d,0).sum()),loss_hits=int(np.maximum(-d,0).sum()),net_hits=int(d.sum()),helped=int((d>0).sum()),harmed=int((d<0).sum()),rescued=int(((b==0)&(a>0)).sum()),new_failures=int(((b>0)&(a==0)).sum()))
def restore_mon(parent,path,gt):
 p=dict(np.load(path));r=p['changed_rows'];assert r.dtype==np.int32 and np.array_equal(r,np.unique(r)) and np.all((r>=0)&(r<1024)) and raw_digest(parent)==str(p['parent_cache_sha'])
 assert np.all(np.any(p['entries']!=parent['entries'][r],axis=1)) and np.all(np.diff(p['entries'],axis=1)>0)
 out={k:v.copy() for k,v in parent.items()};out['route_ndc']=p['route_ndc']
 for k in ['ids','distances','entries','graph_ndc','hits']:out[k][r]=p[k]
 assert np.array_equal(ihits(p['ids'],gt[r]),p['hits']);totals['monitor_patch_scores']+=len(r)
 assert raw_digest(out)==str(p['cache_sha']);return out
for ds in DS:
 done=read(O/'results'/ds/'query_complete.json');assert done['status']=='PASS';costs.append(done)
 c=read(O/'inputs'/ds/'config.json');P=np.fromfile(c['P'],np.float32).reshape(c['hub_count'],c['dim']);mapping=np.fromfile(c['hub_ids'],np.int32);gt=np.fromfile(c['gt_file'],np.int64).reshape(5120,100)
 anchor=dict(np.load(E37/'results'/ds/'baseline.npz'));tb={k:anchor[k][:4096] for k in FIELDS+['hits']};mb={k:anchor[k][4096:] for k in FIELDS+['hits']}
 for rec in [x for x in read(O/'inputs/contexts.json') if x['dataset']==ds]:
  src=Path(rec['source']);dest=O/'results'/ds/rec['key'];saved=read(dest/'steps.json');effects=dict(np.load(dest/'effects.npz'));W=P.copy();tr={k:v.copy() for k,v in tb.items()};mo=restore_mon(mb,dest/'monitor_patches/0000.npz',gt[4096:]);top=read(src/'checkpoints.json')[0]['topology_sha'];selected=rec['selected_step']
  alltr=[];allmo=[]
  for step in range(201):
   if step%20==0:
    cp=dict(np.load(src/'checkpoints'/f'{step:04}.npz'));equal(tr,{k:cp[k][:4096] for k in FIELDS});equal(mo,{k:cp[k][4096:] for k in FIELDS});equal(mo,dict(np.load(dest/'checkpoints'/f'{step:04}.npz')))
    assert digest(W)==digest(cp['W']) and np.array_equal(ihits(cp['ids'],gt),cp['hits']) and np.array_equal(mo['hits'],cp['hits'][4096:]) and np.array_equal(tr['hits'],cp['hits'][:4096]);totals['checkpoint_monitor_rows']+=1024;totals['checkpoint_train_rows']+=4096
   if step in rec['parity_steps']:
    folder=dest/'parity'/f'{step:04}';iden=read(folder/'identity.json');scoreW=P if rec['construction_only'] else W
    structure=inspect_serialized(folder/'graph.hnsw',scoreW,mapping);assert structure['topology_sha']==top==iden['topology_sha'] and digest(scoreW)==iden['W_sha'] and sha(folder/'graph.hnsw')==iden['graph_sha']
    equal(dict(np.load(folder/'raw.npz')),{k:mo[k][:16] for k in FIELDS});totals['parity_rows']+=16;totals['serialized_profile_rows']+=len(P)
   if step==200:break
   t=np.load(src/'trajectory'/f'{step+1:04}.npz');slot=int(t['slot']);choice=int(t['choice']);iscommit=rec['stage']=='E52';prefix='commit' if iscommit else 'accepted';oldtr=tr;oldmo=mo
   assert W[slot].tobytes()==t['current_row'].tobytes() and raw_digest(tr)==str(t['current_cache_sha']) and top==str(t['current_topology_sha']);W[slot]=t['next_row'];top=str(t[prefix+'_topology_sha']);assert digest(W)==str(t[prefix+'_W_sha'])
   if choice>=0:
    branch=f'a{choice}_' if iscommit else f'd{choice}_';rr=t[branch+'rows'];tr={k:v.copy() for k,v in tr.items()}
    for k in ['ids','distances','entries','graph_ndc','hits']:tr[k][rr]=t[branch+k]
    tr['route_ndc']=t['route_ndc' if iscommit else 'd_route_ndc'][choice];assert np.array_equal(ihits(t[branch+'ids'],gt[rr]),t[branch+'hits']);totals['historical_train_patch_scores']+=len(rr)
    mo=restore_mon(mo,dest/'monitor_patches'/f'{step+1:04}.npz',gt[4096:]);totals['accepted']+=1
   else:assert t['next_row'].tobytes()==t['current_row'].tobytes() and not (dest/'monitor_patches'/f'{step+1:04}.npz').exists()
   assert raw_digest(tr)==str(t[prefix+'_cache_sha']);a=tr['hits'].astype(np.int16)-oldtr['hits'];b=mo['hits'].astype(np.int16)-oldmo['hits'];alltr.append(a);allmo.append(b);row=saved[step]
   for key,val in dict(step=step+1,slot=slot,hub_id=int(mapping[slot]),choice=choice,accepted=choice>=0,train_cache_sha=raw_digest(tr),monitor_cache_sha=raw_digest(mo),topology_sha=top,construction_W_sha=digest(W),score_W_sha=digest(P if rec['construction_only'] else W)).items():assert row[key]==val
   assert float(t['selected_delta_J'])==row['selected_delta_J']>=0
   for phase,x,y in [('train',tr['hits'],oldtr['hits']),('monitor',mo['hits'],oldmo['hits'])]:
    for key,value in change(x,y).items():assert row[phase+'_'+key]==value
   steps_all.append(row);totals['steps']+=1;t.close()
  alltr=np.stack(alltr);allmo=np.stack(allmo);assert np.array_equal(alltr,effects['train_delta_hits']) and np.array_equal(allmo,effects['monitor_delta_hits'])
  assert np.array_equal(alltr.sum(0),tr['hits'].astype(int)-tb['hits']) and np.array_equal(allmo.sum(0),mo['hits'].astype(int)-mb['hits'])
  rr=dict(dataset=ds,stage=rec['stage'],seed=rec['seed'],selected_step=selected,steps=200,accepted=sum(x['accepted'] for x in saved),train_positive_steps=sum(x['train_net_hits']>0 for x in saved),
   train_positive_monitor_negative_steps=sum(x['train_net_hits']>0 and x['monitor_net_hits']<0 for x in saved),train_positive_monitor_positive_steps=sum(x['train_net_hits']>0 and x['monitor_net_hits']>0 for x in saved),
   train_positive_monitor_null_net_steps=sum(x['train_net_hits']>0 and x['monitor_net_hits']==0 for x in saved),monitor_conflict_steps=sum(x['monitor_gain_hits']>0 and x['monitor_loss_hits']>0 for x in saved),train_conflict_steps=sum(x['train_gain_hits']>0 and x['train_loss_hits']>0 for x in saved),
   monitor_negative_steps=sum(x['monitor_net_hits']<0 for x in saved),accepted_monitor_quality_null=sum(x['accepted'] and x['monitor_gain_hits']+x['monitor_loss_hits']==0 for x in saved))
  assert rr['accepted']==rec['accepted']
  for phase,d,basehits in [('train',alltr,tb['hits']),('monitor',allmo,mb['hits'])]:
   gain=np.maximum(d,0).sum(0);loss=np.maximum(-d,0).sum(0);net=d.sum(0);sel=d[:selected].sum(0);history=np.r_[basehits[None,:].astype(int),basehits[None,:].astype(int)+np.cumsum(d,axis=0)]
   assert np.all((history>=0)&(history<=10));gain_sum=int(gain.sum());loss_sum=int(loss.sum());final_losses=np.maximum(-net,0)
   rr.update({phase+'_cumulative_gain_hits':gain_sum,phase+'_cumulative_loss_hits':loss_sum,phase+'_final_delta_recall_pp':float(net.mean()*10),phase+'_selected_delta_recall_pp':float(sel.mean()*10),
    phase+'_last_failed_queries':int((history[-1]==0).sum()),phase+'_selected_failed_queries':int((history[selected]==0).sum()),phase+'_queries_with_both_gain_and_loss':int(((gain>0)&(loss>0)).sum()),
    phase+'_trajectory_loss_top5_share':float(np.sort(loss)[-5:].sum()/loss_sum) if loss_sum else None,phase+'_final_loss_top5_share':float(np.sort(final_losses)[-5:].sum()/final_losses.sum()) if final_losses.sum() else None})
   for q in range(d.shape[1]):
    signs=np.sign(d[:,q]);nz=signs[signs!=0];rescues=int(((history[:-1,q]==0)&(history[1:,q]>0)).sum());fails=int(((history[:-1,q]>0)&(history[1:,q]==0)).sum())
    query_rows.append(dict(dataset=ds,stage=rec['stage'],seed=rec['seed'],phase=phase,local_query=q,baseline_hits=int(basehits[q]),cumulative_gain_hits=int(gain[q]),cumulative_loss_hits=int(loss[q]),last_delta_hits=int(net[q]),selected_delta_hits=int(sel[q]),sign_reversals=int((nz[1:]!=nz[:-1]).sum()),rescue_events=rescues,new_failure_events=fails))
    assert rescues-fails==int(basehits[q]==0)-int(history[-1,q]==0)
  for slot in sorted({x['slot'] for x in saved}):
   ss=[x for x in saved if x['slot']==slot];hub_rows.append(dict(dataset=ds,stage=rec['stage'],seed=rec['seed'],slot=slot,hub_id=int(mapping[slot]),accepted=sum(x['accepted'] for x in ss),
    **{phase+'_'+key:sum(x[phase+'_'+key] for x in ss) for phase in ['train','monitor'] for key in ['gain_hits','loss_hits','net_hits']}))
  original=read(src/'model.json');np.testing.assert_allclose(rr['monitor_selected_delta_recall_pp'],original['selected']['monitor']['delta_recall_pp'],atol=1e-14);np.testing.assert_allclose(rr['monitor_final_delta_recall_pp'],original['last']['monitor']['delta_recall_pp'],atol=1e-14)
  runs.append(rr)
aggregates=[]
for ds in DS:
 for stage in ['E52','E53','E56']:
  ss=[x for x in steps_all if x['dataset']==ds and x['stage']==stage];rows=[x for x in runs if x['dataset']==ds and x['stage']==stage]
  a=dict(dataset=ds,stage=stage,decision_steps=400,accepted=sum(x['accepted'] for x in ss),train_positive_steps=sum(x['train_net_hits']>0 for x in ss),train_positive_monitor_negative_steps=sum(x['train_net_hits']>0 and x['monitor_net_hits']<0 for x in ss),
   monitor_positive_steps=sum(x['monitor_net_hits']>0 for x in ss),monitor_negative_steps=sum(x['monitor_net_hits']<0 for x in ss),monitor_conflict_steps=sum(x['monitor_gain_hits']>0 and x['monitor_loss_hits']>0 for x in ss),train_conflict_steps=sum(x['train_gain_hits']>0 and x['train_loss_hits']>0 for x in ss),
   accepted_monitor_quality_null=sum(x['accepted'] and x['monitor_gain_hits']+x['monitor_loss_hits']==0 for x in ss),**{phase+'_'+key:sum(x[phase+'_'+key] for x in ss) for phase in ['train','monitor'] for key in ['gain_hits','loss_hits','net_hits','rescued','new_failures']})
  a['monitor_negative_share_among_train_positive']=a['train_positive_monitor_negative_steps']/a['train_positive_steps'] if a['train_positive_steps'] else None;aggregates.append(a)
def table(name,rr):
 with (O/'results'/f'{name}.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rr[0]));w.writeheader();w.writerows(rr)
for name,rr in [('runs',runs),('steps',steps_all),('queries',query_rows),('hubs',hub_rows),('aggregates',aggregates)]:table(name,rr)
cost=dict(NSG_calls=sum(x['NSG_calls'] for x in costs),normal_new_NSG=sum(x['normal_new_NSG'] for x in costs),HNSW_calls=sum(x['HNSW_calls'] for x in costs),builds=sum(x['builds'] for x in costs),query_seconds=sum(x['seconds'] for x in costs),decision_steps=2400,accepted=totals['accepted'],optimizer_updates=0,new_QPS=0)
assert totals['steps']==2400 and totals['checkpoint_monitor_rows']==135168 and totals['checkpoint_train_rows']==540672 and totals['monitor_patch_scores']==cost['normal_new_NSG']
dump(O/'results/summary.json',dict(runs=runs,aggregates=aggregates,cost=cost));dump(O/'reviews/verification.json',dict(status='PASS',**totals,all_checkpoint_bits_and_full_trajectory_telescoping=True,new_search=0,seconds=time.monotonic()-started))
sys.path.insert(0,str(R/'entry_method_exploration/20260911_gt10_shared_transform_v1/src/vendor'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,axes=plt.subplots(2,2,figsize=(12,7));colors={'E52':'#267792','E53':'#b96b35','E56':'#728746'}
for col,ds in enumerate(DS):
 for rec in [x for x in read(O/'inputs/contexts.json') if x['dataset']==ds]:
  eff=np.load(O/'results'/ds/rec['key']/'effects.npz')
  for row,phase in enumerate(['train','monitor']):
   yy=np.r_[0,np.cumsum(eff[phase+'_delta_hits'].sum(1))/(4096 if phase=='train' else 1024)*10]
   axes[row,col].plot(np.arange(201),yy,'-' if rec['seed']==SEEDS[0] else '--',color=colors[rec['stage']],lw=1.4,label=f'{rec["stage"]} seed{rec["seed"]%100}')
 for row in range(2):axes[row,col].axhline(0,color='grey',lw=.7);axes[row,col].grid(alpha=.2);axes[row,col].set_xlabel('Immutable decision step');axes[row,col].legend(fontsize=8)
 axes[0,col].set_title('WebVid' if col==0 else 'Yandex-IP');axes[0,col].set_ylabel('Train4096 recall change (pp)');axes[1,col].set_ylabel('Monitor1024 recall change (pp)')
fig.suptitle('Every accepted action: frozen trajectories, no checkpoint reselection');fig.tight_layout()
for ext in ['png','svg','pdf']:fig.savefig(O/'figures'/f'accepted_action_trajectories.{ext}',dpi=170)
plt.close(fig);print(json.dumps(dict(cost=cost,aggregates=aggregates),indent=2),flush=True)
