from common import *
import csv
threads(cpu=15);resources();check(O/'reviews/preanalysis_freeze.json');started=time.monotonic()
E66=C/'stage7_multimode_index_v1';E67=C/'stage8_multimode_wall_v1'
assert read(E67/'reviews/verification.json')['status']=='PASS'
assert all(j['status']=='COMPLETE' for j in read(E67/'logs/jobs.json'))
points=[];groups=[];occupancy=[];records=[]
for ds in DS:
    c=read(E66/'inputs'/ds/'construction.json');h=c['hub_count'];d=c['dim'];ids=np.fromfile(c['hub_ids'],np.int32);assert np.all(np.diff(ids)>0)
    P=np.fromfile(c['P'],np.float32).reshape(h,d);W=np.fromfile(E66/'models'/ds/'mode3P/W.f32',np.float32).reshape(3*h,d)
    dup=np.fromfile(E66/'models'/ds/'duplicate3P/W.f32',np.float32).reshape(h,3,d)
    assert dup.tobytes()==np.repeat(P[:,None,:],3,axis=1).tobytes() and W[::3].tobytes()==P.tobytes()
    for split in ['fit','aux']:
        tick=time.monotonic();sc=read(E66/'inputs'/ds/(split+'.json'));n=sc['num_queries'];q=np.fromfile(sc['queries_file'],np.float32,count=n*d).reshape(n,d)
        rows=np.fromfile(sc['row_ids'],np.int64)[:n];raw={}
        for m in ['baseline','duplicate3P','mode3P']:
            f=E66/'results'/ds/split/(m+'_L128');entry=np.fromfile(f/'entry_ids.i32',np.int32).reshape(n,3)
            raw[m]=dict(hits=np.fromfile(f/'hits.u8',np.uint8),entries=entry,local=np.searchsorted(ids,entry))
            assert np.array_equal(ids[raw[m]['local']],entry)
        exactP=np.empty((n,3),np.int32);exactM=np.empty((n,3),np.int32);nearP=np.zeros(n,bool);nearM=np.zeros(n,bool)
        stats={m:dict(agreement=np.empty(n,np.uint8),score_regret=np.empty(n,np.float64)) for m in raw}
        checkcount=0;max_distance_error=0.
        for start in range(0,n,512):
            end=min(start+512,n);qq=q[start:end].astype(float);sp=qq@P.astype(float).T
            sm_slots=qq@W.astype(float).T;sm=sm_slots.reshape(-1,h,3).max(2)
            orderP=np.argsort(-sp,axis=1,kind='stable')[:,:4];orderM=np.argsort(-sm,axis=1,kind='stable')[:,:4]
            exactP[start:end]=ids[orderP[:,:3]];exactM[start:end]=ids[orderM[:,:3]]
            eps=1e-5*np.maximum(1,np.linalg.norm(qq,axis=1));ind=np.arange(end-start)
            nearP[start:end]=(sp[ind,orderP[:,2]]-sp[ind,orderP[:,3]])<=eps
            nearM[start:end]=(sm[ind,orderM[:,2]]-sm[ind,orderM[:,3]])<=eps
            for m in raw:
                score=sm if m=='mode3P' else sp;order=orderM[:,:3] if m=='mode3P' else orderP[:,:3];actual=raw[m]['local'][start:end]
                agreement=np.sum(np.any(actual[:,:,None]==order[:,None,:],axis=2),axis=1)
                regret=np.take_along_axis(score,order,axis=1).sum(1)-np.take_along_axis(score,actual,axis=1).sum(1)
                assert regret.min()>-1e-10;stats[m]['agreement'][start:end]=agreement;stats[m]['score_regret'][start:end]=regret
            # Independent scalar exhaustive ranking at one predetermined row per chunk.
            index=start
            scalar=np.array([sum(float(a)*float(b) for a,b in zip(q[index],v)) for v in P])
            if not nearP[index]:
                assert np.array_equal(np.argsort(-scalar,kind='stable')[:3],orderP[0,:3]);checkcount+=1
            assert time.monotonic()-started<600
        output={'source_rows':rows,'exact_P_hubs':exactP,'exact_mode_hubs':exactM,'near_tie_P':nearP,'near_tie_mode':nearM}
        basehits=raw['baseline']['hits'].astype(int)
        for m in raw:
            st=stats[m];near=nearM if m=='mode3P' else nearP;dh=raw[m]['hits'].astype(int)-basehits
            for k,a in st.items():output[m+'_'+k]=a
            points.append(dict(dataset=ds,split=split,model=m,n=n,exact_hub_set_fraction=float((st['agreement']==3).mean()),
                mean_exact_hub_overlap=float(st['agreement'].mean()/3),mean_profile_score_regret=float(st['score_regret'].mean()),
                near_tie_queries=int(near.sum()),non_tie_exact_set_fraction=float((st['agreement'][~near]==3).mean()) if (~near).any() else None,
                observed_NSG_net_hits=int(dh.sum()),observed_NSG_failure_change=int((raw[m]['hits']==0).sum()-(basehits==0).sum()),new_NSG_queries=0))
            if m!='baseline':
                for name,ix in [('all',np.ones(n,bool)),('same_exhaustive_three',st['agreement']==3),('different_exhaustive_three',st['agreement']<3),
                    ('baseline_exact_candidate_inexact',(stats['baseline']['agreement']==3)&(st['agreement']<3)),('far_from_tie',~near)]:
                    groups.append(dict(dataset=ds,split=split,model=m,group=name,n=int(ix.sum()),net_hits=int(dh[ix].sum()),
                        rescued=int(((basehits==0)&(raw[m]['hits']>0)&ix).sum()),new_failures=int(((basehits>0)&(raw[m]['hits']==0)&ix).sum()),
                        scope='post-hoc association; no exhaustive-route NSG outcome measured'))
                f=E66/'results'/ds/split/(m+'_L128');slots=np.fromfile(f/'candidate_slots.i32',np.int32).reshape(n,7);distances=np.fromfile(f/'candidate_distances.f32',np.float32).reshape(n,7)
                unique=np.array([len(set(map(int,s//3))) for s in slots],np.uint8);output[m+'_candidate_unique_hubs']=unique
                assert unique.min()>=3 and unique.max()<=7
                for k in range(3,8):occupancy.append(dict(dataset=ds,split=split,model=m,distinct_hubs_in_seven=k,queries=int((unique==k).sum())))
                vectors=W if m=='mode3P' else dup.reshape(3*h,d)
                for i in range(0,n,137):
                    ref=1-vectors[slots[i]].astype(float)@q[i].astype(float);err=float(np.max(np.abs(ref-distances[i])));max_distance_error=max(max_distance_error,err)
                    assert np.allclose(ref,distances[i],atol=2e-5,rtol=2e-5)
        out=O/'results'/ds;out.mkdir(exist_ok=True);save(out/(split+'.npz'),**output)
        records.append(dict(dataset=ds,split=split,n=n,profile_score64=True,exact_P_vs_mode_set_changed_queries=int(np.any(np.sort(exactP,axis=1)!=np.sort(exactM,axis=1),axis=1).sum()),
            scalar_exhaustive_P_replays=checkcount,max_sampled_native_distance_error=max_distance_error,seconds=time.monotonic()-tick))
        print('RANK_DIAG',ds,split,records[-1],flush=True)
for name,data in [('points',points),('groups',groups),('occupancy',occupancy)]:
    with (O/'results'/(name+'.csv')).open('x',newline='') as f:w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
dump(O/'reviews/verification.json',dict(status='PASS',records=records,seconds=time.monotonic()-started,new_NSG=0,new_HNSW=0,new_GT=0,new_models=0,exhaustive_score_reference_queries=111808,duplicate_reference_alias_queries=55904,
    original_routing_and_NSG_outcomes_unchanged=True,exact_native_bit_parity_claim=False,full_profile_scores_not_search_utility=True))
dump(O/'state.json',dict(status='COMPLETE_PROFILE_RANKING_DIAGNOSIS',new_NSG=0,new_HNSW=0,formal_QPS_points=0,day_goal_complete=False))
