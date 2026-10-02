from common import *
import struct,csv,collections
def hits(ids,gt):
 g=gt[:,:10].reshape((len(gt),)+(1,)*(ids.ndim-1)+(10,))
 return (ids[...,None]==g).any(axis=-1).sum(axis=-1).astype(np.uint8)
def load(p,dtype,shape):return np.fromfile(p,dtype).reshape(shape)
def topology(path):
 b=Path(path).read_bytes();head=struct.unpack_from('<6QiI3QdQ',b);off,mx,n,size,label,data,level,entry,M,M0,m,mult,ef=head
 assert off==0 and mx==n and M==m==16 and M0==32 and ef==200
 adj=[];rev=[[] for _ in range(n)]
 for i in range(n):
  deg=struct.unpack_from('<H',b,96+i*size)[0];row=np.frombuffer(b,np.uint32,deg,96+i*size+4).tolist();assert len(set(row))==len(row) and i not in row and all(0<=v<n for v in row)
  adj.append(row)
  for v in row:rev[v].append(i)
 def bfs(a):
  dist=np.full(n,-1,np.int32);dist[entry]=0;q=collections.deque([entry])
  while q:
   u=q.popleft()
   for v in a[u]:
    if dist[v]<0:dist[v]=dist[u]+1;q.append(v)
  return dist
 forward=bfs(adj);reverse=bfs(rev);strong=bool((forward>=0).all() and (reverse>=0).all())
 from scipy.sparse import csr_matrix
 from scipy.sparse.csgraph import connected_components
 rr=[];cc=[]
 for u,row in enumerate(adj):rr.extend([u]*len(row));cc.extend(row)
 matrix=csr_matrix((np.ones(len(rr)),(rr,cc)),shape=(n,n));components,labels=connected_components(matrix,directed=True,connection='strong')
 assert strong==(components==1)
 return dict(nodes=n,directed_edges=len(rr),strong_components=int(components),largest_component=int(np.bincount(labels).max()),start_internal_id=entry,
  reachable_from_start=int((forward>=0).sum()),can_reach_start=int((reverse>=0).sum()),mean_outdegree=float(np.mean([len(x) for x in adj])),min_outdegree=min(map(len,adj)),
  mean_indegree=float(np.mean([len(x) for x in rev])),min_indegree=min(map(len,rev)),max_directed_hops=int(forward.max()),median_directed_hops=float(np.median(forward)),upper_maxlevel=level),forward
def stats(h):return dict(recall_pct=float(np.mean(h)*10),failure_pct=float(np.mean(h==0)*100))
def delta(a,b):
 x=a.astype(float)-b;return dict(delta_recall_pp=float(x.mean()*10),helped=int((x>0).sum()),harmed=int((x<0).sum()),unchanged=int((x==0).sum()))
def ci(x,seed):
 rng=np.random.default_rng(seed);means=x[rng.integers(0,len(x),(5000,len(x)))].mean(axis=1)
 return np.quantile(means,[.025,.975]).tolist()
assert read(O/'state.json')['status']=='QUERY_COMPLETE_ANALYSIS_PENDING'
records=[];summary=[];quality=[];checks=[]
for ds in DS:
 p=O/'inputs'/ds;r=O/'results'/ds;c=read(p/'config.json');h=c['hub_count'];n=128;rows=load(p/'row_ids.i64',np.int64,(n,));gt=load(p/'gt.i64',np.int64,(n,100));complete=read(r/'complete.json')
 u=load(p/'single.hitcount.u8',np.uint8,(n,h));singleids=load(p/'single.ids.i32',np.int32,(n,h,10));sndc=load(p/'single.ndc.u32',np.uint32,(n,h));mask=load(p/'single.hitmask.u16',np.uint16,(n,h))
 assert np.array_equal(hits(singleids,gt),u)
 expected_mask=np.zeros((n,h),np.uint16)
 for k in range(10):expected_mask|=((singleids==gt[:,None,None,k]).any(axis=-1).astype(np.uint16)<<k)
 assert np.array_equal(mask,expected_mask)
 par=load(r/'parity_ids.i32',np.int32,(16,3,10));pndc=load(r/'parity_ndc.u32',np.uint32,(16,3));sample=[0,h//2,h-1]
 assert np.array_equal(par,singleids[:16,sample]) and np.array_equal(pndc,sndc[:16,sample])
 ann=load(r/'ann8_local.i32',np.int32,(n,8));exact=load(r/'exact_local.i32',np.int32,(n,h));ann40=load(r/'ann40_local.i32',np.int32,(n,3));annH=load(r/'annH_local.i32',np.int32,(n,3));dist=load(r/'exact_distance.f32',np.float32,(n,h))
 seen=load(r/'seen.u8',np.uint8,(n,h)).astype(bool);seen40=load(r/'seen40.u8',np.uint8,(n,h)).astype(bool);seenH=load(r/'seenH.u8',np.uint8,(n,h)).astype(bool)
 events=read(r/'trace_events.json');rndc=load(r/'route_ndc.u32',np.uint32,(n,3));assert len(events)==n
 for i,event in enumerate(events):assert len(event)==rndc[i,0] and set(event)==set(np.flatnonzero(seen[i]))
 assert np.array_equal(np.sort(exact,axis=1),np.tile(np.arange(h),(n,1))) and (np.diff(dist,axis=1)>=0).all()
 assert seen[np.arange(n)[:,None],ann].all()
 ids=load(r/'ids.i32',np.int32,(n,59,10));entries=load(r/'entries.i32',np.int32,(n,59,3));ndc=load(r/'graph_ndc.u32',np.uint32,(n,59));dh=hits(ids,gt)
 assert (np.diff(np.sort(ids,axis=-1),axis=-1)!=0).all() and (ids>=0).all() and (np.diff(entries,axis=-1)>0).all()
 assert np.array_equal(ids[:,0],ids[:,3]) and np.array_equal(ndc[:,0],ndc[:,3])
 hubids=load(c['hub_ids'],np.int32,(h,))
 for col,a in [(0,ann[:,:3]),(1,exact[:,:3]),(2,ann40)]:assert np.array_equal(entries[:,col],np.sort(hubids[a],axis=1))
 index=np.arange(n);ua=u[index,ann[:,0]];ue=u[index,exact[:,0]];uv=np.max(np.where(seen,u,-1),axis=1);ug=u.max(axis=1);uc8=np.take_along_axis(u,ann,axis=1).max(axis=1)
 A0=u==ug[:,None];nonconstant=u.min(axis=1)<ug;sub=ua<ug;seenA=(A0&seen).any(axis=1);seenA40=(A0&seen40).any(axis=1);annA=A0[index[:,None],ann[:,:3]].any(axis=1);exactA=A0[index[:,None],exact[:,:3]].any(axis=1)
 ranks=np.empty_like(exact);ranks[index[:,None],exact]=np.arange(h);best_rank=np.min(np.where(A0,ranks,h),axis=1)+1;best_hops=[]
 topo,hops=topology(c['graph_file']);topo['graph_file']=c['graph_file']
 for i in range(n):best_hops.append(int(hops[A0[i]].min()))
 matches=np.all(np.sort(ann[:,:3],axis=1)==np.sort(exact[:,:3],axis=1),axis=1);matches40=np.all(np.sort(ann40,axis=1)==np.sort(exact[:,:3],axis=1),axis=1);matchesH=np.all(np.sort(annH,axis=1)==np.sort(exact[:,:3],axis=1),axis=1)
 oracle=dh[:,3:].max(axis=1);same3=dh[:,0];costs={'ann3':rndc[:,0]+ndc[:,0].astype(float),'exact3':h+ndc[:,1].astype(float),'ef40_3':rndc[:,1]+ndc[:,2].astype(float)}
 for name,hh in [('ANN single',ua),('Exact single',ue),('Visited single oracle',uv),('C8 single oracle',uc8),('Full-H single oracle',ug),('ANN three',same3),('Exact three',dh[:,1]),('ef40 three',dh[:,2]),('C8 true triple oracle',oracle)]:quality.append(dict(dataset=ds,method=name,**stats(hh)))
 diagnostic=dict(dataset=ds,n=n,topology=topo,nonconstant_queries=int(nonconstant.sum()),ann1_suboptimal_queries=int(sub.sum()),
  single_gap_recall_pp=float((ug.astype(float)-ua).mean()*10),visited_recoverable_gap_pp=float((uv-ua).mean()*10),unvisited_gap_pp=float((ug-uv).mean()*10),
  suboptimal_but_optimum_seen=int((sub&seenA).sum()),suboptimal_and_no_optimum_seen=int((sub&~seenA).sum()),
  A0_any_seen_queries=int(seenA.sum()),A0_any_seen_ef40_queries=int(seenA40.sum()),A0_in_ann3_queries=int(annA.sum()),A0_in_exact3_queries=int(exactA.sum()),
  A0_in_ann3_nonconstant=int((annA&nonconstant).sum()),A0_seen_nonconstant=int((seenA&nonconstant).sum()),
  A0_size_median=float(np.median(A0.sum(axis=1))),A0_size_mean=float(A0.sum(axis=1).mean()),best_A0_exact_rank_median=float(np.median(best_rank)),best_A0_exact_rank_p90=float(np.quantile(best_rank,.9)),
  best_A0_hops_median=float(np.median(best_hops)),visited_unique_mean=float(seen.sum(axis=1).mean()),visited_unique_ef40_mean=float(seen40.sum(axis=1).mean()),visited_unique_efH_mean=float(seenH.sum(axis=1).mean()),
  exact_top3_set_match_queries=int(matches.sum()),ef40_exact_top3_set_match_queries=int(matches40.sum()),efH_exact_top3_set_match_queries=int(matchesH.sum()),
  mean_route_NDC_ef10=float(rndc[:,0].mean()),mean_route_NDC_ef40=float(rndc[:,1].mean()),mean_route_NDC_efH=float(rndc[:,2].mean()),
  exact3_vs_ann3=delta(dh[:,1],same3),ef40_vs_ann3=delta(dh[:,2],same3),C8_oracle_vs_ann3=delta(oracle,same3),exact1_vs_ann1=delta(ue,ua),
  total_NDC_means={k:float(v.mean()) for k,v in costs.items()},NSG_NDC_means={k:float(ndc[:,i].mean()) for i,k in enumerate(['ann3','exact3','ef40_3'])},
  C8_oracle_delta_95pct_bootstrap_pp=ci((oracle.astype(float)-same3)*10,20260916),exact3_delta_95pct_bootstrap_pp=ci((dh[:,1].astype(float)-same3)*10,20260916),
  C8_oracle_below_fullH_single_queries=int((oracle<ug).sum()),C8_oracle_above_fullH_single_queries=int((oracle>ug).sum()),
  all56_triples_mean_NDC=float(ndc[:,3:].sum(axis=1).mean()),QPS=None)
 summary.append(diagnostic)
 for i in range(n):
  records.append(dict(dataset=ds,local_row=i,train_row=int(rows[i]),ann1_hits=int(ua[i]),exact1_hits=int(ue[i]),visited_best_single_hits=int(uv[i]),C8_best_single_hits=int(uc8[i]),fullH_best_single_hits=int(ug[i]),
   ann3_hits=int(same3[i]),exact3_hits=int(dh[i,1]),ef40_3_hits=int(dh[i,2]),C8_triple_oracle_hits=int(oracle[i]),A0_count=int(A0[i].sum()),A0_seen=bool(seenA[i]),A0_ann3=bool(annA[i]),A0_exact3=bool(exactA[i]),
   best_A0_exact_rank=int(best_rank[i]),best_A0_hops=best_hops[i],visited_unique=int(seen[i].sum()),ann3_exact_set=bool(matches[i])))
 np.savez_compressed(r/'scored.npz',single_hits=u,joint_hits=dh,ann1=ua,exact1=ue,visited_oracle=uv,fullH_oracle=ug,C8_triple_oracle=oracle,A0=A0)
 checks.append(dict(dataset=ds,status='PASS',cached_single_outputs_rescored=n*h,new_joint_outputs_rescored=n*59,cached_single_native_parity=48,route_parity_checks=complete['route_parity_checks'],current_Policy_parity=128,top8_prefix=128,duplicate_ann3_C8_result_parity=128))
for name,data in [('query_diagnostics',records),('quality',quality)]:
 dump(O/'results'/(name+'.json'),data)
 with (O/'results'/(name+'.csv')).open('w') as f:
  wr=csv.DictWriter(f,fieldnames=list(data[0]));wr.writeheader();wr.writerows(data)
dump(O/'results/diagnosis.json',summary);dump(O/'reviews/result_verification.json',dict(status='PASS',datasets=checks))
print(json.dumps(summary,indent=2),flush=True)
