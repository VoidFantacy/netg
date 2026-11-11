from model_io import *
from archive import load_packets
import collections,struct
assert read(R/'reviews/formal_complete.json')['status']=='PASS_FROZEN_EIGHT_WINDOW_MATRIX'
start=time.perf_counter();points=[];gaterows=[];costrows=[];rankrows=[];frontier=[];placement=[];checks=collections.Counter();hitarrays={}
def write(name,rows):
    fields=list(dict.fromkeys(k for r in rows for k in r))
    with open(R/'analysis'/name,'w') as f:w=csv.DictWriter(f,fields);w.writeheader();w.writerows(rows)
def pair_events(a,b,G,K):
    gain=loss=0
    for aa,bb,gg in zip(a,b,G[:,:K]):
        x=set(aa)&set(gg);y=set(bb)&set(gg);gain+=len(x-y);loss+=len(y-x)
    return gain,loss
STAGES=['route','main_search','gate_features','gate_predict','candidate_C','student_shortlist','rerank_features','rerank_predict','expansion','merge','query_total_excluding_route']
for ds in DS:
 for window in ['A','B']:
    c=read(R/'configs'/f'{ds}.{window}.formal.json');root=Path(c['output_dir']);info=read(root/'complete.json');raw=load_packets(root);n=c['queries']['n'];G=np.fromfile(c['test_gt']['path'],'<i4').reshape(-1,100);G=G[c['test_gt'].get('row_start',0):c['test_gt'].get('row_start',0)+n];pack={};local=[];profiles={}
    for p in info['results']:
        K,L,m=p['K'],p['L'],p['method'];key=(K,L,m);prefix=f'k{K}/{m}_L{L}';get=lambda fn:raw[prefix+'/raw/'+fn];ids=np.frombuffer(get('ids.i32'),'<i4').reshape(n,K);dist=np.frombuffer(get('distances.f32'),'<f4').reshape(n,K)
        assert np.isfinite(dist).all() and (np.diff(dist,axis=1)>=0).all() and ((ids>=0)&(ids<c['base']['n'])).all();assert all(len(set(x))==K for x in ids)
        h=hashlib.sha256(struct.pack('<QQ',n,K))
        for name in ['ids.i32','distances.f32','entry_ids.i32','profile_distances.f32']:h.update(get(name))
        h.update(bytes(16*n))
        for rr in p['rounds']:assert rr['threads']==1 and h.hexdigest()==rr['packet_sha256'] and abs(rr['qps']-n/rr['wall_seconds'])<1e-8
        qp=[rr['qps'] for rr in p['rounds']];assert abs(p['qps']-sorted(qp)[1])<1e-8;checks['packets']+=1
        hits=np.array([len(set(a)&set(g[:K])) for a,g in zip(ids,G)],dtype='<i2');work=np.frombuffer(raw[prefix+'/work.u64'],'<u8').reshape(n,8);dec=np.frombuffer(raw[prefix+'/decisions.i32'],'<i4').reshape(n,7);pack[key]=(ids,dist,hits,work,dec);hitarrays[f'{ds}|{window}|{K}|{L}|{m}']=hits
        row=dict(dataset=ds,window=window,K=K,L=L,method=m,n=n,hits=int(hits.sum()),recall_pct=100*float(hits.mean())/K,qps=p['qps'],qps_min=min(qp),qps_max=max(qp),mean_us=1e6/p['qps'],formal_batch_seconds=sum(rr['wall_seconds'] for rr in p['rounds']),failed_lt10=int((hits<10).sum()) if K==100 else '',
            C_exact_per_query=float(work[:,0].mean()),aux_exact_per_query=float(work[:,2].mean()),aux_expanded_per_query=float(work[:,3].mean()),aux_neighbor_slots_per_query=float(work[:,4].mean()),gate_enabled=int(dec[:,6].sum()),actual_expansion_queries=int(dec[:,0].sum()),rerank_rows_per_query=float(dec[:,3].mean()),rerank_neighbor_slots_per_query=float(dec[:,4].mean()))
        if prefix+'/profile.f64' in raw:
            us=np.frombuffer(raw[prefix+'/profile.f64'],'<f8').reshape(n,11);assert np.isfinite(us).all() and (us>=0).all();profiles[key]=us;pr=p['profile'];assert pr['actual_packet_equal'];checks['profile_packet_parity']+=1
            cr=dict(dataset=ds,window=window,K=K,L=L,method=m,formal_us=row['mean_us'],profile_batch_us=pr['profile_batch_wall_seconds']*1e6/n,profile_vs_formal_pct=100*(pr['profile_batch_wall_seconds']*p['qps']/n-1))
            enabled=dec[:,6].astype(bool)
            for j,name in enumerate(STAGES):
                cr[name+'_mean_us']=float(us[:,j].mean());cr[name+'_p50_us']=float(np.median(us[:,j]));cr[name+'_p95_us']=float(np.quantile(us[:,j],.95));cr[name+'_enabled_mean_us']=float(us[enabled,j].mean()) if enabled.any() else None
            cr['rerank_total_mean_us']=float(us[:,6:8].sum(1).mean());cr['gate_total_mean_us']=float(us[:,2:4].sum(1).mean());cr['profile_unallocated_us']=cr['profile_batch_us']-float(us[:,:10].sum(1).mean());costrows.append(cr)
        if prefix+'/witness.bin.gz' in raw:
            b=raw[prefix+'/witness.bin.gz'];pos=0;dtype=np.dtype([('id','<i4'),('v','<f4')]);counts=[]
            for qi in range(n):
                q,k,ne,ns=struct.unpack_from('<IIII',b,pos);pos+=16;assert q==qi and k==K;a=np.frombuffer(b,dtype,count=K,offset=pos);pos+=8*K;e=np.frombuffer(b,dtype,count=ne,offset=pos);pos+=8*ne;seeds=np.frombuffer(b,'<i4',count=ns,offset=pos);pos+=4*ns;ii=np.r_[a['id'],e['id']];vv=np.r_[a['v'],e['v']];assert len(set(ii))==len(ii);order=np.lexsort((np.arange(len(ii)),vv))[:K]
                assert np.array_equal(ii[order],ids[qi]) and np.array_equal(vv[order].view('<u4'),dist[qi].view('<u4'));checks['linear_fullsort_queries']+=1
                if m in ['OPT-B32','Q8-B32']:counts.append(ne)
                elif m!='REUSE-SQ':assert ns<=1 and (not ns or seeds[0]==dec[qi,1]) and work[qi,2]<=384 and work[qi,4]<=64*384
            assert pos==len(b)
            if counts:row['C_exact_per_query']=float(np.mean(counts))
        local.append(row)
    by={(r['K'],r['L'],r['method']):r for r in local}
    for key,pkt in pack.items():
        K,L,m=key;r=by[key]
        for bm,label in [('GT10','main'),('Q8-B32','direct')]:
            if (K,L,bm) not in pack:continue
            gain,loss=pair_events(pkt[0],pack[K,L,bm][0],G,K);assert gain-loss==int((pkt[2]-pack[K,L,bm][2]).sum());r[f'rescued_vs_{label}']=gain;r[f'lost_vs_{label}']=loss;r[f'gain_vs_{label}_pp']=100*(gain-loss)/(n*K)
        if m.startswith(('F-','N-')):
            family=m[0];base=pack[K,200,'GT10' if family=='F' else 'Q8-B32'];always=pack[K,200,'ALWAYS'];enabled=pkt[4][:,6].astype(bool)
            for qi in range(n):
                expected=always if enabled[qi] else base;assert np.array_equal(pkt[0][qi],expected[0][qi]) and np.array_equal(pkt[1][qi].view('<u4'),expected[1][qi].view('<u4'));checks['gate_branch_queries']+=1
            gains=(always[2]-base[2]).clip(0);kept=(pkt[2]-base[2]).clip(0)
            gr=dict(dataset=ds,window=window,K=K,L=L,method=m,family=family,target=75 if '75' in m else 90,n=n,enabled=int(enabled.sum()),enable_pct=100*float(enabled.mean()),always_positive_hits=int(gains.sum()),kept_positive_hits=int(kept.sum()),positive_retention_pct=100*float(kept.sum()/gains.sum()) if gains.sum() else None,
                false_rejected_positive_queries=int(((gains>0)&~enabled).sum()),enabled_zero_or_negative_queries=int(((gains<=0)&enabled).sum()),recall_pct=r['recall_pct'],qps=r['qps'],formal_us=r['mean_us'],qps_vs_always_pct=100*(r['qps']/by[K,200,'ALWAYS']['qps']-1),net_gain_vs_off_pp=100*float((pkt[2]-base[2]).mean())/K,
                measured_saved_vs_always_us=by[K,200,'ALWAYS']['mean_us']-r['mean_us'])
            pu=profiles[key];ap=profiles[K,200,'ALWAYS'];bp=profiles[K,200,'GT10' if family=='F' else 'Q8-B32'];saved=((ap[:,4:10].sum(1)-bp[:,4:10].sum(1))*(~enabled)).mean();gr.update(gate_profile_us=float(pu[:,2:4].sum(1).mean()),skipped_action_profile_estimate_us=float(saved),
                replay_estimate_net_saving_us=float(saved-pu[:,2:4].sum(1).mean()),estimate_not_formal_wall=True);gaterows.append(gr)
        if m not in ['GT10','OPT-B32','REUSE-SQ']:
            control=[p for p in local if p['K']==K and p['method'] in ['GT10','OPT-B32','REUSE-SQ']];covered=[p for p in control if p['hits']>=r['hits'] and p['qps']>=r['qps'] and (p['hits']>r['hits'] or p['qps']>r['qps'])];quality=[p for p in control if p['hits']>=r['hits']];best=max(quality,key=lambda p:p['qps']) if quality else None
            frontier.append(dict(dataset=ds,window=window,K=K,L=L,method=m,covered=bool(covered),range_covered=any(p['qps_min']>=r['qps_max'] for p in covered),quality_threshold_control=f"{best['method']}/L{best['L']}" if best else '',quality_threshold_QPS_change_pct=100*(r['qps']/best['qps']-1) if best else None))
    for K,L in STATES:
        b=raw[f'k{K}/ALWAYS_L200/selection.bin.gz'];pos=0;features=[];ids=[];groups=[];pre=[];post=[];cp=[]
        for qi in range(n):
            q,nc=struct.unpack_from('<II',b,pos);pos+=8;assert q==qi;gx=np.frombuffer(b,'<f4',count=62,offset=pos).copy();pos+=248;pre.append(gx[:22]);post.append(gx[22:50]);cp.append(gx[50:]);begin=len(ids)
            for j in range(nc):ids.append(struct.unpack_from('<i',b,pos)[0]);pos+=4;features.append(np.frombuffer(b,'<f4',count=104,offset=pos).copy());pos+=416
            groups.append(np.arange(begin,len(ids)))
        assert pos==len(b);f=np.asarray(features);ids=np.asarray(ids);mf=[x['path'] for x in c['model_files'] if x['K']==K][0];model=read(mf);model['_ids']=ids;ni=np.fromfile(model['node_ids'],'<i4');ne=np.fromfile(model['node_embeddings'],'<f8').reshape(-1,32);sp=student_predict(model,f,ne,ni)[:,1];tp=predict_tree(model['teacher'][1],f)
        for qi,ix in enumerate(groups):
            if not len(ix):continue
            order=ix[np.argsort(-sp[ix],kind='stable')];sl=sorted(set([int(ix[0])]+[int(x) for x in order[:5]]));choices={'DIST384':int(ix[0]),'FAST384':int(order[0]),'ALWAYS':max(sl,key=lambda j:(tp[j],-j)),'TEACHER384':max(ix,key=lambda j:(tp[j],-j))}
            for m,j in choices.items():assert pack[K,L,m][4][qi,1]==ids[j];checks['student_teacher_decisions']+=1
        gj=read(R/'storage/gates'/ds/f'k{K}.json')
        for family in ['F','N']:
          for variant,X in [('PRE',pre),('POST',post),('CPOST',cp)]:
            if family=='F' and variant=='CPOST':continue
            tr=gj['gates'][family+'_'+variant];pred=predict_tree(tr['model'],np.asarray(X,dtype='float64'))
            for target in [75,90]:
                expected=(pred>=tr[f'threshold{target}']) if not tr['model']['gate_all_off'] else np.zeros(n,dtype=bool);actual=pack[K,L,f'{family}-{variant}{target}'][4][:,6];assert np.array_equal(expected,actual);checks['independent_gate_decisions']+=n
        for family in ['F','N']:
            a,z=pack[K,L,f'{family}-PRE90'],pack[K,L,f'{family}-PRE90-LATE'];assert np.array_equal(a[0],z[0]) and np.array_equal(a[1].view('<u4'),z[1].view('<u4'));placement.append(dict(dataset=ds,window=window,K=K,family=family,identical_answers_and_actions=True,pre_qps=by[K,L,f'{family}-PRE90']['qps'],late_qps=by[K,L,f'{family}-PRE90-LATE']['qps'],late_vs_pre_qps_pct=100*(by[K,L,f'{family}-PRE90-LATE']['qps']/by[K,L,f'{family}-PRE90']['qps']-1)))
        for method,reference in [('ALWAYS','FAST384'),('ALWAYS','DIST384'),('TEACHER384','ALWAYS')]:
            a,z=by[K,L,method],by[K,L,reference];ua,uz=profiles[K,L,method],profiles[K,L,reference]
            rankrows.append(dict(dataset=ds,window=window,K=K,L=L,method=method,reference=reference,recall_gain_pp=a['recall_pct']-z['recall_pct'],formal_extra_us=a['mean_us']-z['mean_us'],qps_change_pct=100*(a['qps']/z['qps']-1),
                rerank_feature_delta_us=float((ua[:,6]-uz[:,6]).mean()),rerank_predict_delta_us=float((ua[:,7]-uz[:,7]).mean()),expansion_delta_us=float((ua[:,8]-uz[:,8]).mean()),rerank_rows_delta=a['rerank_rows_per_query']-z['rerank_rows_per_query'],aux_exact_delta=a['aux_exact_per_query']-z['aux_exact_per_query']))
    points+=local;print('ANALYZED',ds,window,len(local),flush=True)
write('points.csv',points);write('gates.csv',gaterows);write('stage_costs.csv',costrows);write('rerank_costs.csv',rankrows);write('frontier.csv',frontier);write('placement.csv',placement);np.savez_compressed(R/'analysis/query_hits.npz',**hitarrays)
dump(R/'analysis/analysis_receipt.json',dict(status='PASS_ALL_PACKETS_PROFILES_GATE_BRANCHES_MODEL_DECISIONS_AND_MERGE',checks=dict(checks),points=len(points),formal_complete_batch_seconds=sum(x['formal_batch_seconds'] for x in points),seconds=time.perf_counter()-start))
print('ANALYSIS_PASS',len(points),dict(checks),flush=True)
