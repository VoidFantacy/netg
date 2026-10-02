from shared import *
threads(8);resources();started=time.monotonic();check(O/'reviews/prequery_freeze.json')
assert all(read(O/'results'/ds/'query_complete.json')['status']=='PASS' for ds in DS)
records=[];points=[];scored=rows_exact=parity=0;context_cost=[]
for ds in DS:
 c=read(O/'inputs'/ds/'config.json');gt=np.fromfile(c['gt_file'],np.int64).reshape(5120,100)[:4096]
 base={k:v[:4096] for k,v in dict(np.load(E37/'results'/ds/'baseline.npz')).items()};cost=read(O/'results'/ds/'query_complete.json');context_cost.append(cost)
 for rec in [x for x in read(O/'inputs/contexts.json') if x['dataset']==ds]:
  step=rec['step'];t=dict(np.load(rec['trajectory']));current=dict(np.load(E44/'results'/ds/f'{step:04}'/'C/raw.npz'));us=[];hs=[]
  for a in range(-1,8):
   tag='C' if a<0 else f'A{a}';dest=O/'results'/ds/f'{step:04}'/tag;out=dict(np.load(dest/'raw.npz'));patch=dict(np.load(dest/'patch.npz'));iden=read(dest/'identity.json')
   old=dict(np.load(E44/'results'/ds/f'{step:04}'/tag/'raw.npz'));equal(out,old);rows_exact+=4096
   assert sha(dest/'raw.npz')==iden['raw_sha'];assert digest(np.load(dest/'topology.npz')['topology'])==iden['topology_sha']
   assert iden['topology_sha']==(rec['current_topology_sha'] if a<0 else rec['candidate_topology_sha'][a])
   changed=np.array([q for q in range(4096) if tuple(out['entries'][q])!=tuple(current['entries'][q])],np.int32)
   assert np.array_equal(changed,patch['changed_rows']) and len(changed)==iden['new_NSG']
   mask=np.ones(4096,bool);mask[changed]=False
   for k in ['ids','distances','graph_ndc']:
    assert out[k][mask].tobytes()==current[k][mask].tobytes();assert out[k][changed].tobytes()==patch[k].tobytes()
   assert out['entries'][changed].tobytes()==patch['entries'].tobytes()
   hits=np.array([len(set(map(int,ii))&set(map(int,gg[:10]))) for ii,gg in zip(out['ids'],gt)],np.uint8);scored+=4096
   np.testing.assert_array_equal(hits,score(out['ids'],gt));u=utility(out,base,gt);us.append(u);hs.append(hits)
   if step in [20,200]:
    assert sha(dest/'graph.hnsw')==iden['graph_sha'];equal(dict(np.load(dest/'parity.npz')),subset(out,np.arange(16)));parity+=16
   points.append(iden)
  U=np.stack(us);eps=t['eps'];values=U[1:]-U[0];g=np.zeros(16)
  rewards=values.mean(1)-(t['drift']-t['current_drift'])
  for j in range(16):
   g[j]=sum((rewards[i]-sum(rewards[k] for k in range(8) if k!=i)/7)*eps[i,j] for i in range(8))/(8*.3)
  oldderived=dict(np.load(E44/'results'/ds/f'{step:04}'/'derived.npz'));np.testing.assert_allclose(g,oldderived['full_gradient'],atol=3e-14)
  np.testing.assert_array_equal(np.stack(hs),oldderived['hits']);np.testing.assert_allclose(U,oldderived['U'],atol=2e-15)
  records.append(dict(dataset=ds,step=step,new_NSG=sum(x['new_NSG'] for x in points if x['dataset']==ds and x['step']==step),gradient_recovery='PASS'))
def table(p,rr):
 with p.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rr[0]));w.writeheader();w.writerows(rr)
table(O/'results/points.csv',points);table(O/'results/contexts.csv',records)
total_new=sum(x['normal_new_NSG'] for x in context_cost);assert total_new==1333 and scored==rows_exact==737280 and parity==576
projection=1.5*800*sum(np.mean([x['seconds'] for x in cost['contexts']]) for cost in context_cost)+600
query_completed_epoch=max(x['completed_at'] for x in read(O/'logs/jobs.json'));projected_finish=query_completed_epoch+projection
semantic=True;sparse=total_new/655360<=.1;timely=projected_finish<1789212300
gate=dict(status='PASS_EXACT_FEEDBACK_CACHE_AND_TRAINING_PROJECTION' if semantic and sparse and timely else 'STOP_CACHE_TRAINING_GATE',
 exact_recovery=semantic,candidate_NSG_fraction=total_new/655360,candidate_cost_pass=sparse,projected_training_seconds=float(projection),
 projection_start_epoch=query_completed_epoch,projected_finish_epoch=float(projected_finish),finish_gate_epoch=1789212300,time_projection_pass=timely,
 projection_is_not_a_guarantee=True,optimizer_updates=0)
dump(O/'results/gate.json',gate)
cost=dict(NSG_calls=sum(x['NSG_calls'] for x in context_cost),HNSW_calls=sum(x['HNSW_calls'] for x in context_cost),builds=sum(x['builds'] for x in context_cost),
 normal_new_NSG=total_new,parity_NSG=1728,reused_current_seed_NSG=81920,cold_all_contexts_normal_NSG=81920+total_new,
 logical_full_rows=737280,full_candidate_rows=655360,optimizer_updates=0,new_GT=0,QPS_points=0,
 datasets=[{k:v for k,v in x.items() if k!='contexts'} for x in context_cost],
 components={k:sum(x[k] for x in points) for k in ['build_seconds','route_seconds','change_mask_seconds','new_NSG_seconds','assemble_seconds','seconds']})
assert cost['NSG_calls']==3061 and cost['HNSW_calls']==738432 and cost['builds']==180;dump(O/'results/cost.json',cost)
dump(O/'reviews/verification.json',dict(status='PASS',independent_set_scores=scored,bit_exact_full_rows=rows_exact,cache_identity_rows=737280,
 physical_parity_rows=parity,full_gradients=20,graphs=180,invalid_input_batches=8,new_search=0,seconds=time.monotonic()-started))
print(json.dumps(dict(gate=gate,cost=cost),indent=2),flush=True)
