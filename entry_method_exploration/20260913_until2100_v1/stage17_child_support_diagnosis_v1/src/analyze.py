from common import *
import csv
threads();resources();tick=time.monotonic();E73=C/'stage14_compact_modes_v1';E69=C/'stage10_exact_triple_utility_v1';paths=[O/'protocol.md']+list((O/'src').glob('*.py'));jobs=[]
for ds in DS:
 fit=read(E66/'inputs'/ds/'fit.json');aux=read(E73/'inputs'/ds/'aux.json');source=next(x for x in fit['methods'] if x['model_name']=='mode3P')
 paths += [E66/'inputs'/ds/'fit.json',E73/'inputs'/ds/'aux.json',E66/'models'/ds/'training.npz']+[Path(source[k]) for k in ['W','mapping','tie_ids']]
 for c in [fit,aux]:paths += [Path(c[k]) for k in ['queries_file','gt_file','row_ids']]
 for name,n,c,new,ref in [('fit_approx',20000,fit,E66/'results'/ds/'fit/mode3P_L128',E66/'results'/ds/'fit/baseline_L128'),('aux_compact',7952,aux,E73/'results'/ds/'aux/compact10_L128',E73/'results'/ds/'aux/baseline10_L128'),('aux_exact',7952,aux,E69/'results'/ds/'exact_mode.npz',E69/'results'/ds/'exact_P.npz')]:
  for p in [new,ref]:paths += list(p.glob('*')) if p.is_dir() else [p]
  jobs.append((ds,name,n,c,new,ref,source))
freeze(O/'reviews/preanalysis_freeze.json',paths)
groups=[];support_rows=[];profiles={};score_rows=0
for ds in DS:
 c=read(E66/'inputs'/ds/'fit.json');m=next(x for x in c['methods'] if x['model_name']=='mode3P');W=np.fromfile(m['W'],np.float32).reshape(-1,3,c['dim']);ids=np.fromfile(m['mapping'],np.int32)[::3];a=dict(np.load(E66/'models'/ds/'training.npz'));active=a['active'];h=len(W)
 mass=np.zeros((h,3));ess=np.zeros((h,3));frac=np.ones((h,3));mass[:,0]=a['parent_mass'];ess[:,0]=a['parent_ESS'];mass[active,1:]=a['child_mass'];ess[active,1:]=a['child_ESS'];frac[active,1:]=a['child_mass']/a['parent_mass'][active,None]
 cos=np.einsum('hmd,hd->hm',W.astype(float),W[:,0].astype(float));eligible=np.zeros(h,bool);eligible[active]=a['eligible'];coherence=np.zeros((h,3));coherence[active,0]=np.linalg.norm(a['sum0']+a['sum1'],axis=1)/a['parent_mass'][active];coherence[active,1]=np.linalg.norm(a['sum0'],axis=1)/a['child_mass'][:,0];coherence[active,2]=np.linalg.norm(a['sum1'],axis=1)/a['child_mass'][:,1]
 for i in range(h):
  for mode in [1,2]:support_rows.append(dict(dataset=ds,hub=int(ids[i]),slot=3*i+mode,eligible=bool(eligible[i]),parent_mass=float(mass[i,0]),parent_ESS=float(ess[i,0]),child_mass=float(mass[i,mode]),child_ESS=float(ess[i,mode]),fraction=float(frac[i,mode]),parent_cosine=float(cos[i,mode]),parent_coherence=float(coherence[i,0]),child_coherence=float(coherence[i,mode])))
 profiles[ds]=(W,ids,mass,ess,frac,cos,eligible)
def raw(p,n):
 if p.suffix=='.npz':return dict(np.load(p))
 return dict(ids=np.fromfile(p/'ids.i32',np.int32).reshape(n,10),entries=np.fromfile(p/'entry_ids.i32',np.int32).reshape(n,3),hits=np.fromfile(p/'hits.u8',np.uint8),mask=np.fromfile(p/'hitmask.u16',np.uint16))
for ds,name,n,c,p,r,source in jobs:
 W,hubids,mass,ess,frac,cos,eligible=profiles[ds];a,b=raw(p,n),raw(r,n);gt=np.memmap(c['gt_file'],np.int64,mode='r').reshape(-1,100)[:n];q=np.memmap(c['queries_file'],np.float32,mode='r').reshape(-1,c['dim'])[:n];rows=np.fromfile(c['row_ids'],np.int64)[:n]
 if name=='aux_exact':assert np.array_equal(rows,a['source_rows']) and np.array_equal(rows,b['source_rows'])
 for out in [a,b]:
  hits=np.array([len(set(ids.tolist())&set(g[:10].tolist())) for ids,g in zip(out['ids'],gt)],np.uint8);assert np.array_equal(hits,out['hits']);score_rows+=n
  mask=np.array([sum((int(gj) in set(ids.tolist()))<<j for j,gj in enumerate(g[:10])) for ids,g in zip(out['ids'],gt)],np.uint16);assert np.array_equal(mask,out['mask'])
 local=np.searchsorted(hubids,a['entries']);assert np.array_equal(hubids[local],a['entries']);novel=~np.any(a['entries'][:,:,None]==b['entries'][:,None,:],axis=2)
 winner=np.zeros((n,3),np.int8);lift=np.zeros((n,3));score=np.zeros((n,3,3))
 for start in range(0,n,256):
  end=min(n,start+256);Q=q[start:end].astype(float);Q/=np.linalg.norm(Q,axis=1,keepdims=True);score[start:end]=np.einsum('ijdm,im->ijd',W[local[start:end]].astype(float),Q)
 winner=np.argmax(score,axis=2).astype(np.int8);best=np.take_along_axis(score,winner[:,:,None],axis=2)[:,:,0];lift=best-score[:,:,0];child=novel&(winner>0);mi=mass[local,winner];ei=ess[local,winner];fi=frac[local,winner];ci=cos[local,winner]
 actual_slots=np.full((n,3),-1,np.int32)
 if name!='aux_exact':
  actual_slots=np.fromfile(p/'router_labels.i32',np.int32).reshape(n,3)
  if name=='aux_compact':actual_slots=np.fromfile(E73/'models'/ds/'original_slots.i32',np.int32)[actual_slots]
  assert np.array_equal(actual_slots//3,local)
 flags=dict(new_child=np.any(child,1),child_mass_below8=np.any(child&(mi<8),1),child_ESS_below16=np.any(child&(ei<16),1),child_fraction_below_quarter=np.any(child&(fi<.25),1),child_parent_cosine_below_point9=np.any(child&(ci<.9),1),child_lift_above_point05=np.any(child&(lift>.05),1))
 delta=a['hits'].astype(int)-b['hits'].astype(int);res=(b['hits']==0)&(a['hits']>0);harm=(b['hits']>0)&(a['hits']==0)
 for axis,flag in flags.items():
  assert flag.shape==(n,)
  for value in [False,True]:
   ix=flag==value;d=delta[ix];groups.append(dict(dataset=ds,comparison=name,axis=axis,value=value,n=int(ix.sum()),positive_queries=int((d>0).sum()),negative_queries=int((d<0).sum()),gained_query_hits=int(np.maximum(d,0).sum()),lost_query_hits=int(np.maximum(-d,0).sum()),net_hits=int(d.sum()),rescued=int(res[ix].sum()),new_failures=int(harm[ix].sum()),reference_hit_histogram=' '.join(map(str,np.bincount(b['hits'][ix],minlength=11).tolist()))))
 save(O/'results'/ds/(name+'.npz'),source_rows=rows,entries=a['entries'],reference_entries=b['entries'],hits=a['hits'],reference_hits=b['hits'],winning_source_slots=local*3+winner,actual_source_slots=actual_slots,novel_hub=novel,new_child=child,child_mass=mi,child_ESS=ei,child_fraction=fi,parent_cosine=ci,score_lift=lift,**{'cohort_'+k:v for k,v in flags.items()})
 print(ds,name,'net',int(delta.sum()),'new child queries',int(flags['new_child'].sum()),flush=True);assert time.monotonic()-tick<120
for filename,data in [('cohorts',groups),('child_support',support_rows)]:
 with (O/'results'/(filename+'.csv')).open('x',newline='') as f:w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
check(O/'reviews/preanalysis_freeze.json');resources();dump(O/'reviews/verification.json',dict(status='PASS',set_and_mask_scored_rows=score_rows,comparisons=6,cohort_rows=len(groups),child_support_rows=len(support_rows),new_ANN=0,new_NSG=0,new_builds=0,new_GT=0,training_updates=0,seconds=time.monotonic()-tick,causal_single_profile_credit=False));dump(O/'state.json',dict(status='COMPLETE_CHILD_SUPPORT_DIAGNOSIS',NSG=0,HNSW=0,builds=0,day_goal_complete=False));print('E76_COMPLETE')
