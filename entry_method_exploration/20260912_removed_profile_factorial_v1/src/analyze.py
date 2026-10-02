from shared import *
threads(8);resources();check(O/'reviews/prequery_freeze.json');start=time.monotonic()
jobs=read(O/'logs/jobs.json');assert len(jobs)==2 and all(x['status']=='COMPLETE' for x in jobs)
assert sum(x['actual'] for x in jobs)==8576
metrics=[];query_rows=[];case_rows=[];summaries=[]
for ds in DS:
 c=cfg(ds);ca=case(ds);rows=np.load(O/'inputs'/ds/'rows.npz')['rows']
 gt=np.fromfile(c['gt_file'],np.int64).reshape(4096,100)[rows]
 source=np.fromfile(c['row_ids'],np.int64)[rows]
 raw={cell:dict(np.load(O/'results'/ds/(cell+'.npz'))) for cell in CELLS}
 h={cell:score(raw[cell]['ids'],gt) for cell in CELLS}
 base=dict(np.load(E37/'results'/ds/'baseline.npz'));bh=base['hits'][rows].astype(float)
 baseline_total=base['route_ndc'][rows].astype(float)+base['graph_ndc'][rows]
 P=np.fromfile(c['P'],np.float32).reshape(c['hub_count'],c['dim']).astype(float)
 W={cell:np.fromfile(O/'models'/ds/cell/'W.f32',np.float32).reshape(P.shape).astype(float) for cell in CELLS}
 drift={cell:float(np.square(W[cell]-P).sum(1).mean()) for cell in CELLS}
 np.testing.assert_allclose(drift['F']-drift['S']-drift['R']+drift['C'],0,atol=1e-15)
 U={};delta={}
 for cell in CELLS:
  assert np.array_equal(raw[cell]['rows'],rows)
  r=raw[cell];total=r['route_ndc'].astype(float)+r['graph_ndc'];hh=h[cell].astype(float)
  U[cell]=hh-bh-.1*(total/baseline_total-1)-.1*((hh==0).astype(float)-(bh==0).astype(float))
  dh=h[cell]-h['C'];delta[cell]=dh
  met=dict(dataset=ds,cell=cell,recall_pct=float(hh.mean()*10),delta_recall_pp=float(dh.mean()*10),
    gain_hits=int(np.maximum(dh,0).sum()),loss_hits=int(np.maximum(-dh,0).sum()),net_hits=int(dh.sum()),
    helped_queries=int((dh>0).sum()),harmed_queries=int((dh<0).sum()),
    failure_queries=int((hh==0).sum()),rescued_zero=int(((h['C']==0)&(hh>0)).sum()),new_zero=int(((h['C']>0)&(hh==0)).sum()),
    route_NDC=float(r['route_ndc'].mean()),graph_NDC=float(r['graph_ndc'].mean()),total_NDC=float(total.mean()),
    graph_NDC_change_pct=float((r['graph_ndc'].mean()/raw['C']['graph_ndc'].mean()-1)*100),
    total_NDC_change_pct=float((total.mean()/(raw['C']['route_ndc'].astype(float)+raw['C']['graph_ndc']).mean()-1)*100),
    mean_U=float(U[cell].mean()),mean_U_delta_from_C=float((U[cell]-U['C']).mean()),
    drift=drift[cell],reward_delta_from_C=float((U[cell]-U['C']).mean()-(drift[cell]-drift['C'])),
    changed_entry_queries=int(np.any(r['entries']!=raw['C']['entries'],axis=1).sum()))
  metrics.append(met)
 interaction=h['F']-h['S']-h['R']+h['C'];iu=U['F']-U['S']-U['R']+U['C']
 for i,row in enumerate(rows):
  query_rows.append(dict(dataset=ds,row=int(row),source_row=int(source[i]),
   C_hits=int(h['C'][i]),F_hits=int(h['F'][i]),S_hits=int(h['S'][i]),R_hits=int(h['R'][i]),interaction=int(interaction[i]),
   target_effect_without_rest=int(h['S'][i]-h['C'][i]),target_effect_with_rest=int(h['F'][i]-h['R'][i]),
   rest_effect_without_target=int(h['R'][i]-h['C'][i]),rest_effect_with_target=int(h['F'][i]-h['S'][i]),
   C_entries=';'.join(map(str,raw['C']['entries'][i])),F_entries=';'.join(map(str,raw['F']['entries'][i])),
   S_entries=';'.join(map(str,raw['S']['entries'][i])),R_entries=';'.join(map(str,raw['R']['entries'][i]))))
 observations=[]
 for obs in ca['observations']:
  qi=int(obs['qi']);assert int(rows[qi])==int(obs['row'])
  role='positive' if int(obs['delta_hits'])>0 else 'negative'
  for cell in CELLS:
   cr=dict(dataset=ds,target_hub=ca['hub'],role=role,row=int(rows[qi]),source_row=int(source[qi]),cell=cell,
      hits=int(h[cell][qi]),entries=';'.join(map(str,raw[cell]['entries'][qi])),
      route_NDC=int(raw[cell]['route_ndc'][qi]),graph_NDC=int(raw[cell]['graph_ndc'][qi]))
   case_rows.append(cr)
  observations.append(dict(role=role,row=int(rows[qi]),source_row=int(source[qi]),hits={cell:int(h[cell][qi]) for cell in CELLS},interaction=int(interaction[qi])))
 positive=next(x for x in observations if x['role']=='positive');negative=next(x for x in observations if x['role']=='negative')
 retain=positive['hits']['S']>=positive['hits']['F'];repair=negative['hits']['S']>=negative['hits']['C']
 gainF=np.maximum(delta['F'],0);lossF=np.maximum(-delta['F'],0)
 gainS=np.maximum(delta['S'],0)
 s=dict(dataset=ds,context=ca['context'],original_action=ca['action'],target_hub=ca['hub'],cases=observations,
   specified_gain_fully_retained=bool(retain),specified_gain_partially_retained=bool(positive['hits']['C']<positive['hits']['S']<positive['hits']['F']),
   specified_damage_eliminated=bool(repair),specified_damage_partially_repaired=bool(negative['hits']['F']<negative['hits']['S']<negative['hits']['C']),
   local_case_isolation_signal=bool(retain and repair),
   whole_pool_F_gain_retained_by_S=int(np.minimum(gainF,gainS).sum()),
   whole_pool_F_loss_removed_by_S=int(np.minimum(np.maximum(delta['S']-delta['F'],0),lossF).sum()),
   S_new_loss_on_F_nonharmed_queries=int(np.maximum(-delta['S'][delta['F']>=0],0).sum()),
   S_new_gain_on_F_nonhelped_queries=int(np.maximum(delta['S'][delta['F']<=0],0).sum()),
   S_whole_pool_net=int(delta['S'].sum()),R_whole_pool_net=int(delta['R'].sum()),F_whole_pool_net=int(delta['F'].sum()),
   interaction_sum=int(interaction.sum()),interaction_recall_pp=float(interaction.mean()*10),
   interaction_nonzero_queries=int((interaction!=0).sum()),interaction_positive_queries=int((interaction>0).sum()),
   interaction_negative_queries=int((interaction<0).sum()),interaction_mean_U=float(iu.mean()),
   S_entry_changes=int(np.any(raw['S']['entries']!=raw['C']['entries'],axis=1).sum()),
   R_entry_changes_vs_F=int(np.any(raw['R']['entries']!=raw['F']['entries'],axis=1).sum()))
 n=negative['hits'];original_loss=n['C']-n['F'];assert original_loss>0
 s.update(negative_original_loss=original_loss,
   negative_S_loss=n['C']-n['S'],negative_R_loss=n['C']-n['R'],
   negative_S_any_damage=bool(n['S']<n['C']),negative_S_reproduces_full_damage=bool(n['S']<=n['F']),
   negative_R_eliminates_damage=bool(n['R']>=n['C']),negative_R_partially_repairs=bool(n['F']<n['R']<n['C']),
   negative_joint_sufficiency_necessity_signal=bool(n['S']<=n['F'] and n['R']>=n['C']),
   target_marginal_alone_hits=int((h['S']-h['C']).sum()),target_marginal_with_rest_hits=int((h['F']-h['R']).sum()))
 summaries.append(s)
 save_np(O/'results'/ds/'derived.npz',rows=rows,hits=np.stack([h[k] for k in CELLS]),delta=np.stack([delta[k] for k in CELLS]),
      U=np.stack([U[k] for k in CELLS]),interaction=interaction,interaction_U=iu)
 print(json.dumps(s,ensure_ascii=False),flush=True)
writecsv('metrics.csv',metrics);writecsv('queries.csv',query_rows);writecsv('cases.csv',case_rows)
dump(O/'results/diagnosis.json',dict(status='REMOVED_PROFILE_FACTORIAL_ANALYZED',datasets=summaries,metrics=metrics,
     actual_NSG=sum(j['actual'] for j in jobs),actual_HNSW=sum(j['native']['HNSW_calls'] for j in jobs),
     builds=sum(j['native']['builds'] for j in jobs),optimizer_updates=0,actual_threads=1,
     analysis_seconds=time.monotonic()-start,peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
