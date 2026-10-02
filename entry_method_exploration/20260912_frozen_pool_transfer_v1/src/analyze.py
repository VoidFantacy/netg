from common import *
start();check(O/'reviews/analysis_freeze.json');assert time.time()<1789221000
started=time.monotonic();pool=read(O/'inputs/candidate_pool.json');selection=read(E57/'results/cal_selection.json')['selection'];models=[];splits=[];queries=[];transfers=[];verified_rows=0;matrices={}
def score(ids,gt):return (ids[...,None]==gt[:,None,:10]).any(1).sum(1).astype(np.uint8)
for ds in DS:
 c=read(O/'inputs'/ds/'config.json');gt=np.fromfile(c['gt_file'],np.int64).reshape(5120,100);cg=np.fromfile(E57/'inputs'/ds/'cal/gt.i64',np.int64).reshape(1024,100);names=[m['model_name'] for m in pool[ds]]
 chosen=names.index(selection[ds]['best_new']['model']);full=[];cal=[]
 for m in pool[ds]:
  a=dict(np.load(m['prior_raw']));h=score(a['ids'],gt);assert len(h)==5120
  if 'hits' in a:assert np.array_equal(h,a['hits'])
  # Independent scalar sets also verify the broadcast implementation and old labels.
  ih=np.array([len(set(map(int,rr))&set(map(int,gg[:10]))) for rr,gg in zip(a['ids'],gt)],np.uint8);assert np.array_equal(ih,h);verified_rows+=5120
  full.append(dict(hits=h,entries=a['entries'],total=a['route_ndc'].astype(float)+a['graph_ndc']))
  folder=E57/'results'/f'cal_{ds}'/(m['model_name']+'_L128');ids=np.fromfile(folder/'ids.i32',np.int32).reshape(1024,10);hh=score(ids,cg)
  assert np.array_equal(hh,np.fromfile(folder/'hits.u8',np.uint8)) and np.array_equal(hh,np.array([len(set(map(int,rr))&set(map(int,gg[:10]))) for rr,gg in zip(ids,cg)],np.uint8));verified_rows+=1024
  cal.append(dict(hits=hh,entries=np.fromfile(folder/'entry_ids.i32',np.int32).reshape(1024,3),total=np.fromfile(folder/'route_ndc.u32',np.uint32).astype(float)+np.fromfile(folder/'graph_ndc.u32',np.uint32)))
 for phase,aa in [('train',[{k:v[:4096] for k,v in a.items()} for a in full]),('monitor',[{k:v[4096:] for k,v in a.items()} for a in full]),('cal',cal)]:
  hits=np.stack([a['hits'] for a in aa]);base=hits[0];delta=hits.astype(np.int16)-base;gain=np.maximum(delta,0);loss=np.maximum(-delta,0);net=delta.sum(1);oracle=gain.max(0);best=int(np.argmax(net));n=len(base)
  u=np.stack([delta[i]-.1*(a['total']/aa[0]['total']-1)-.1*((a['hits']==0).astype(int)-(base==0).astype(int)) for i,a in enumerate(aa)])
  for rank,(name,a) in enumerate(zip(names,aa)):
   changed=np.any(a['entries']!=aa[0]['entries'],axis=1);null=delta[rank]==0;rescued=int(((base==0)&(a['hits']>0)).sum());newfail=int(((base>0)&(a['hits']==0)).sum())
   assert rescued-newfail==int((base==0).sum())-int((a['hits']==0).sum())
   models.append(dict(dataset=ds,phase=phase,model=name,rank=rank,queries=n,delta_recall_pp=float(net[rank]/n*10),gain_hits=int(gain[rank].sum()),loss_hits=int(loss[rank].sum()),net_hits=int(net[rank]),helped_queries=int((delta[rank]>0).sum()),harmed_queries=int((delta[rank]<0).sum()),changed_entry_queries=int(changed.sum()),changed_entries_quality_null=int((changed&null).sum()),rescued=rescued,new_failures=newfail,mean_U=float(u[rank].mean()),total_NDC=float(a['total'].mean()),fixed_cal_selected=rank==chosen))
  assert int(oracle.sum()-net[best])==int((oracle-gain[best]).sum()+loss[best].sum())
  assert int(oracle.sum()-net[chosen])==int((oracle-gain[chosen]).sum()+loss[chosen].sum())
  ss=dict(dataset=ds,phase=phase,queries=n,models=19,any_gain_queries=int((oracle>0).sum()),any_harm_queries=int((loss.max(0)>0).sum()),opposite_model_sign_queries=int(((oracle>0)&(loss.max(0)>0)).sum()),
   oracle_hits=int(oracle.sum()),oracle_delta_recall_pp=float(oracle.mean()*10),baseline_missing_hits=int((10-base).sum()),oracle_fraction_of_missing=float(oracle.sum()/(10-base).sum()),best_hit_model=names[best],best_hit_net=int(net[best]),best_hit_delta_recall_pp=float(net[best]/n*10),
   best_hit_uncovered=int((oracle-gain[best]).sum()),best_hit_own_loss=int(loss[best].sum()),selected_model=names[chosen],selected_net=int(net[chosen]),selected_uncovered=int((oracle-gain[chosen]).sum()),selected_own_loss=int(loss[chosen].sum()))
  for q in range(n):
   vals=[int(hits[i,q])-int(base[q]) for i in range(19)];assert max(vals)==int(oracle[q])
   queries.append(dict(dataset=ds,phase=phase,local_query=q,baseline_hits=int(base[q]),oracle_gain_hits=max(vals),models_helping=sum(v>0 for v in vals),models_harming=sum(v<0 for v in vals),selected_delta_hits=vals[chosen],best_hit_model_delta=vals[best]))
  matrices[(ds,phase)]=(hits,delta,u);np.savez_compressed(O/'results'/f'{ds}_{phase}.npz',names=np.array(names),hits=hits,delta_hits=delta,mean_U=u.mean(1),cal_selected_rank=np.array(chosen));splits.append(ss)
  if phase=='cal':
   old=read(E57/'results'/ds/'cal_selection_details.json');order=max(range(1,19),key=lambda i:(float(u[i].mean()),-float(aa[i]['total'].mean()),-i));assert order==chosen
   for rank in range(19):np.testing.assert_allclose(u[rank].mean(),old[rank]['mean_U'],atol=2e-15,rtol=0)
 for name in names[1:]:
  a={phase:next(x for x in models if x['dataset']==ds and x['phase']==phase and x['model']==name) for phase in ['train','monitor','cal']}
  transfers.append(dict(dataset=ds,model=name,**{phase+'_net_hits':x['net_hits'] for phase,x in a.items()},train_positive=a['train']['net_hits']>0,monitor_positive=a['monitor']['net_hits']>0,cal_positive=a['cal']['net_hits']>0,monitor_positive_cal_negative=a['monitor']['net_hits']>0 and a['cal']['net_hits']<0))
assert verified_rows==233472 and len(models)==114 and len(splits)==6 and len(queries)==12288 and len(transfers)==36
for name,rows in [('models',models),('splits',splits),('queries',queries),('transfers',transfers)]:table(name,rows)
dump(O/'results/summary.json',dict(splits=splits,transfers=transfers,models=models));check(O/'reviews/protected.json');check(O/'reviews/analysis_freeze.json')
dump(O/'reviews/verification.json',dict(status='PASS',independent_set_scoring_rows=verified_rows,model_split_points=114,query_decompositions=12288,fixed_cal_selection_unchanged=True,all_gain_loss_gap_identities=True,seconds=time.monotonic()-started,new_NSG=0,new_HNSW=0,new_builds=0,new_training=0,new_GT=0,new_QPS=0))
sys.path.insert(0,str(R/'entry_method_exploration/20260911_gt10_shared_transform_v1/src/vendor'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,axes=plt.subplots(3,2,figsize=(13,11));xx=np.arange(19)
for col,ds in enumerate(DS):
 names=[m['model_name'].replace('202609','').replace('graph_rl','G').replace('baseline','P0') for m in pool[ds]]
 for row,phase in enumerate(['train','monitor','cal']):
  a=[x for x in models if x['dataset']==ds and x['phase']==phase];n=a[0]['queries'];axes[row,col].bar(xx,[x['gain_hits']/n*10 for x in a],color='#398680',label='Gain');axes[row,col].bar(xx,[-x['loss_hits']/n*10 for x in a],color='#c76c50',label='Loss');axes[row,col].plot(xx,[x['delta_recall_pp'] for x in a],'ko',ms=3,label='Net');axes[row,col].axhline(0,color='grey',lw=.7);axes[row,col].set_xticks(xx,names,rotation=90,fontsize=7);axes[row,col].set_ylabel(phase+' recall change (pp)');axes[row,col].grid(axis='y',alpha=.2)
 axes[0,col].set_title('WebVid' if col==0 else 'Yandex-IP')
handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc='upper center',ncol=3,bbox_to_anchor=(.5,.972));fig.suptitle('Frozen19-model pool: gains, harms and transfer (no new search)');fig.tight_layout(rect=(0,0,1,.94))
for ext in ['png','svg','pdf']:fig.savefig(O/'figures'/f'pool_transfer.{ext}',dpi=160,bbox_inches='tight')
plt.close(fig);print(json.dumps(splits,indent=2),flush=True)
