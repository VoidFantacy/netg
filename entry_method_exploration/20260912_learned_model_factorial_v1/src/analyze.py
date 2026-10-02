from shared import *
threads(8);resources();check(O/'reviews/prequery_freeze.json');started=time.monotonic()
rows=[];interactions=[];scores=parities=endpoints=patches=0;costs=[]
def ihits(ids,gt):return np.array([len(set(map(int,a))&set(map(int,b[:10]))) for a,b in zip(ids,gt)],np.int16)
for ds in DS:
 done=read(O/'results'/ds/'query_complete.json');assert done['status']=='PASS';costs.append(done)
 c=read(O/'inputs'/ds/'config.json');gt=np.fromfile(c['gt_file'],np.int64).reshape(5120,100);P=np.fromfile(c['P'],np.float32).reshape(c['hub_count'],c['dim'])
 base=dict(np.load(E37/'results'/ds/'baseline.npz'));h0=ihits(base['ids'],gt);assert np.array_equal(h0,base['hits'])
 gc=np.load(O/'results'/ds/'baseline/C/topology.npz')['topology'];outs={};hs={}
 for rec in read(O/'results'/ds/'points.json'):
  dest=O/'results'/ds/rec['key']/rec['cell'];out=dict(np.load(dest/'raw.npz'));patch=dict(np.load(dest/'patch.npz'));cr=patch['changed_rows']
  assert np.array_equal(cr,np.flatnonzero((out['entries']!=base['entries']).any(1)));assert len(cr)==rec['new_NSG'];patches+=len(cr)
  assert np.all(np.diff(out['entries'],axis=1)>0);assert sha(dest/'W.f32')==rec['W_sha'] and sha(dest/'graph.hnsw')==rec['graph_sha']
  top=np.load(dest/'topology.npz')['topology'];assert digest(top)==rec['topology_sha']
  for k in ['ids','distances','graph_ndc']:
   z=base[k].copy();z[cr]=patch[k];assert z.tobytes()==out[k].tobytes()
  assert patch['entries'].tobytes()==out['entries'][cr].tobytes()
  pr=np.r_[np.arange(32),np.arange(4096,4128)];equal(dict(np.load(dest/'parity.npz')),subset(out,pr));parities+=64
  h=ihits(out['ids'],gt);scores+=5120;outs[(rec['key'],rec['cell'])]=out;hs[(rec['key'],rec['cell'])]=h
  if rec['cell']=='C':equal(out,base);assert sha(dest/'W.f32')==digest(P);endpoints+=5120
  else:
   src=next(x for x in read(O/'inputs/contexts.json') if x['dataset']==ds and x['key']==rec['key'])
   if rec['cell']=='A':equal(out,dict(np.load(src['checkpoint'])));assert sha(dest/'W.f32')==sha(src['W']);endpoints+=5120
   if rec['cell']=='S':assert top.tobytes()==gc.tobytes() and sha(dest/'W.f32')==sha(src['W'])
   if rec['cell']=='T':assert sha(dest/'W.f32')==digest(P) and rec['topology_sha']==src['topology_sha']
  for phase,sl in [('train',slice(0,4096)),('monitor',slice(4096,5120))]:
   d=h[sl]-h0[sl];bb=h0[sl];hh=h[sl];total=out['route_ndc'][sl].astype(float)+out['graph_ndc'][sl];btotal=base['route_ndc'][sl].astype(float)+base['graph_ndc'][sl]
   rows.append(dict(dataset=ds,key=rec['key'],cell=rec['cell'],phase=phase,n=len(d),recall_pct=float(hh.mean()*10),delta_recall_pp=float(d.mean()*10),gain_hits=int(np.maximum(d,0).sum()),loss_hits=int(np.maximum(-d,0).sum()),
    net_hits=int(d.sum()),improved_queries=int((d>0).sum()),damaged_queries=int((d<0).sum()),failure_queries=int((hh==0).sum()),rescued_failures=int(((bb==0)&(hh>0)).sum()),new_failures=int(((bb>0)&(hh==0)).sum()),
    total_NDC_change_pct=float((total.mean()/btotal.mean()-1)*100),mean_U=float((d-.1*(total/btotal-1)-.1*((hh==0).astype(int)-(bb==0).astype(int))).mean())))
 for rec in [x for x in read(O/'inputs/contexts.json') if x['dataset']==ds]:
  key=rec['key'];a=hs[(key,'A')]-h0;s=hs[(key,'S')]-h0;t=hs[(key,'T')]-h0;i=a-s-t
  for phase,sl in [('train',slice(0,4096)),('monitor',slice(4096,5120))]:
   aa,ss,tt,ii=[x[sl] for x in [a,s,t,i]]
   interactions.append(dict(dataset=ds,key=key,phase=phase,interaction_queries=int((ii!=0).sum()),interaction_L1=int(np.abs(ii).sum()),interaction_net=int(ii.sum()),
    score_only_response=int(((ss!=0)&(tt==0)).sum()),topology_only_response=int(((ss==0)&(tt!=0)).sum()),joint_only_response=int(((ss==0)&(tt==0)&(aa!=0)).sum()),
    opposing_main_effects=int((ss*tt<0).sum()),A_net=int(aa.sum()),S_net=int(ss.sum()),T_net=int(tt.sum())))
  save(O/'results'/ds/key/'effects.npz',A=a,S=s,T=t,interaction=i)
for name,data in [('metrics',rows),('interactions',interactions)]:
 with (O/'results'/f'{name}.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
cost=dict(NSG_calls=sum(x['NSG_calls'] for x in costs),normal_new_NSG=patches,parity_NSG=4992,HNSW_calls=sum(x['HNSW_calls'] for x in costs),builds=18,installations=16,states=26,optimizer_updates=0,QPS_points=0,query_seconds=sum(x['seconds'] for x in costs))
assert scores==133120 and parities==1664 and endpoints==51200 and cost['HNSW_calls']==136448 and cost['NSG_calls']==patches+4992
dump(O/'results/summary.json',dict(metrics=rows,interactions=interactions,cost=cost));dump(O/'reviews/verification.json',dict(status='PASS',independent_set_scores=scores,parity_rows=parities,endpoint_bit_rows=endpoints,patch_rows=patches,all_physical_vectors_and_topologies=True,seconds=time.monotonic()-started,new_search=0))
sys.path.insert(0,str(R/'entry_method_exploration/20260911_gt10_shared_transform_v1/src/vendor'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,axes=plt.subplots(2,2,figsize=(12,7));colors=['#276f9b','#df9832','#598348']
for col,ds in enumerate(DS):
 keys=[x['key'] for x in read(O/'inputs/contexts.json') if x['dataset']==ds]
 for row,phase in enumerate(['train','monitor']):
  ax=axes[row,col]
  for j,(cell,color) in enumerate(zip(['A','S','T'],colors)):
   vals=[next(x['delta_recall_pp'] for x in rows if x['dataset']==ds and x['key']==key and x['cell']==cell and x['phase']==phase) for key in keys]
   ax.bar(np.arange(4)+(j-1)*.24,vals,.23,color=color,label={'A':'Learned W + G','S':'Learned W only','T':'Learned G only'}[cell])
  ax.axhline(0,color='grey',lw=.7);ax.set_xticks(np.arange(4),[x.replace('202609','seed') for x in keys],fontsize=9);ax.set_ylabel(f'{phase} recall change (pp)');ax.grid(axis='y',alpha=.2);ax.legend(fontsize=8)
 axes[0,col].set_title('WebVid' if col==0 else 'Yandex-IP')
fig.suptitle('Whole learned model: actual physical score / topology factorial');fig.tight_layout()
for ext in ['png','svg','pdf']:fig.savefig(O/'figures'/f'whole_model_factorial.{ext}',dpi=170)
plt.close(fig);print(json.dumps(dict(cost=cost,interactions=interactions),indent=2),flush=True)
