from common import *
import gzip,struct,collections
t=time.perf_counter();points=[];mechanisms=[];probe_rows=[];audits=[];query_hits={};node_groups=collections.defaultdict(lambda:collections.Counter())
for ds in DS:
    for window in ['A','B']:
        c=read(R/'configs'/f'{ds}.{window}.json');root=Path(c['output_dir']);g=np.fromfile(c['test_gt']['path'],'<i4').reshape(-1,100);n=len(g)
        perf=read(root/'performance_complete.json');records={(x['K'],x['L'],x['method']):x for x in perf['results']};packets={}
        def packet(K,L,m):
            key=K,L,m
            if key not in packets:
                p=Path(records[key]['result_dir'])/'raw';ids=np.fromfile(p/'ids.i32','<i4').reshape(n,K);dist=np.fromfile(p/'distances.f32','<f4').reshape(n,K)
                assert np.all((ids>=0)&(ids<c['base']['n'])) and np.all(np.isfinite(dist));assert all(len(set(map(int,row)))==K for row in ids)
                packets[key]=ids,dist
            return packets[key]
        hit={}
        for (K,L,m),rec in records.items():
            ids,dist=packet(K,L,m);hit[K,L,m]=np.array([len(set(map(int,a))&set(map(int,b))) for a,b in zip(ids,g[:,:K])],dtype=np.int16)
        rng=np.random.default_rng(19520261102);boot=rng.integers(n,size=(1000,n))
        for (K,L,m),rec in records.items():
            ids,dist=packet(K,L,m);main,md=packet(K,L,'GT10');base,bd=packet(K,L,'B32');h=hit[K,L,m];delta=h-hit[K,L,'GT10'];db=h-hit[K,L,'B32'];lost=rescue=blost=brescue=0
            for i in range(n):
                G=set(map(int,g[i,:K]));M=set(map(int,main[i]))&G;B=set(map(int,base[i]))&G;F=set(map(int,ids[i]))&G;rescue+=len(F-M);lost+=len(M-F);brescue+=len(F-B);blost+=len(B-F)
            qps=np.array([x['qps'] for x in rec['rounds']]);ci=np.percentile(delta[boot].mean(1)*100/K,[2.5,97.5]);bi=np.percentile(db[boot].mean(1)*100/K,[2.5,97.5])
            row=dict(dataset=ds,window=window,K=K,L=L,method=m,n=n,hits=int(h.sum()),recall_pct=float(h.mean()*100/K),gain_vs_GT_pp=float(delta.mean()*100/K),gain_GT_ci_lo=float(ci[0]),gain_GT_ci_hi=float(ci[1]),gain_vs_B32_pp=float(db.mean()*100/K),gain_B32_ci_lo=float(bi[0]),gain_B32_ci_hi=float(bi[1]),rescued_vs_GT=rescue,lost_vs_GT=lost,rescued_vs_B32=brescue,lost_vs_B32=blost,improved_queries_vs_B32=int((db>0).sum()),harmed_queries_vs_B32=int((db<0).sum()),failed_lt10=int((h<10).sum()) if K==100 else '',qps=rec['qps'],mean_us=1e6/rec['qps'],qps_min=float(qps.min()),qps_max=float(qps.max()),qps_gain_vs_B32_pct=(rec['qps']/records[K,L,'B32']['qps']-1)*100)
            for j,name in enumerate(['C_exact','representative_exact','expansion_exact','expanded','neighbor_slots','selection_slots','seeds','SQ_scanned']):row[name+'_per_query']=rec['mean_work'][j] if m not in ['B32','GT10','OPT-B32'] else ''
            row['SQ_exact_per_query']=rec['mean_work'][2] if m=='REUSE-SQ' else ''
            if m=='REUSE-SQ':row['expansion_exact_per_query']=''
            points.append(row);query_hits[ds,window,K,L,m]=h
            if m in NAV:
                data=gzip.open(Path(rec['result_dir'])/'events.bin.gz','rb').read();pos=0;stage_rescue=np.zeros(3,dtype=np.int64);stage_counts=np.zeros(3,dtype=np.int64)
                for i in range(n):
                    qi,ne,ns=struct.unpack_from('<III',data,pos);pos+=12;assert qi==i and ne<=480 and ns<=3
                    e=np.frombuffer(data,dtype=np.dtype([('id','<i4'),('distance','<f4'),('stage','<u4')]),count=ne,offset=pos);pos+=ne*12;seeds=np.frombuffer(data,dtype='<i4',count=ns,offset=pos);pos+=ns*4
                    assert all(0<=int(x)<c['base']['n'] for x in seeds)
                    assert np.all((e['id']>=0)&(e['id']<c['base']['n'])) and np.all(np.isfinite(e['distance'])) and np.all(e['stage']<=2)
                    assert len(set(map(int,e['id'])))==ne and not(set(map(int,e['id']))&set(map(int,main[i])))
                    allids=np.concatenate((main[i],e['id']));alld=np.concatenate((md[i],e['distance']));order=np.lexsort((np.arange(K+ne),alld))[:K]
                    assert np.array_equal(allids[order],ids[i]) and np.array_equal(alld[order].view('<u4'),dist[i].view('<u4')),(ds,window,K,L,m,i,'numpy full sort oracle')
                    G=set(map(int,g[i,:K]));M=set(map(int,main[i]));F=set(map(int,ids[i]));
                    for stage in range(3):
                        ee=e['id'][e['stage']==stage];stage_counts[stage]+=len(ee);stage_rescue[stage]+=len((set(map(int,ee))&G&F)-M)
                assert pos==len(data)
                audits.append(dict(dataset=ds,window=window,K=K,L=L,method=m,queries=n,all_candidate_ids_unique=True,all_final_ids_and_distance_bits_match_numpy_full_sort=True))
                for stage in range(3):mechanisms.append(dict(dataset=ds,window=window,K=K,L=L,method=m,stage=['direct_C','representative','expansion'][stage],exact_scores=int(stage_counts[stage]),rescued_final_members_vs_GT=int(stage_rescue[stage])))
        # No new online decision reads these GT-derived diagnostics.
        with gzip.open(root/'query_diagnosis.csv.gz','rt') as f:
            qr=list(csv.DictReader(f))
        groups=collections.defaultdict(list)
        for a in qr:groups[int(a['K']),int(a['L'])].append(a)
        for L in [100,200,400]:
            a=groups[1,L];b=groups[100,L]
            assert len(a)==len(b) and all(x['query']==y['query'] and x['main_scores']==y['main_scores'] and x['main_expanded']==y['main_expanded'] for x,y in zip(a,b))
        for (K,L),vals in groups.items():
            total={key:sum(float(a[key]) for a in vals) for key in vals[0] if key not in ['K','L','query']}
            total.update(dataset=ds,window=window,K=K,L=L,n=len(vals));total['C_mean_indegree']/=len(vals);total['C_mean_outdegree']/=len(vals);total['GT_mean_indegree']/=len(vals);total['GT_mean_outdegree']/=len(vals)
            for key in ['main_scores','main_expanded','C_count','C_main_seen']:total[key+'_per_query']=total[key]/len(vals)
            assert total['missing']==total['missing_evaluated']+total['missing_frontier_adjacent']+total['missing_no_frontier_edge']
            assert total['missing_expanded_parent_unseen']==0
            assert 0<=total['SQ_rescued']<=total['SQ_short_missing']<=total['SQ_scan_missing']<=total['SQ_pool_missing']<=total['missing']
            assert total['SQ_rescued']==next(x['rescued_vs_GT'] for x in points if x['dataset']==ds and x['window']==window and x['K']==K and x['L']==L and x['method']=='REUSE-SQ')
            mechanisms.append(dict(total,method='DIAGNOSIS',stage='all',exact_scores='',rescued_final_members_vs_GT=''))
        with gzip.open(root/'single_seed.csv.gz','rt') as f:
            for a in csv.DictReader(f):probe_rows.append(dict(dataset=ds,window=window,**a))
        with gzip.open(root/'C_nodes.csv.gz','rt') as f:
            for a in csv.DictReader(f):
                key=ds,window,int(a['K']),int(a['L']),int(a['is_GT']);b=node_groups[key];b['n']+=1
                for name in ['indegree','outdegree','unseen_outneighbors','main_seen']:b[name]+=float(a[name])
                b['zero_indegree']+=int(a['indegree'])==0
        print('ANALYZED',ds,window,len(records),flush=True)
for a in points:
    peers=[x for x in points if (x['dataset'],x['window'],x['K'])==(a['dataset'],a['window'],a['K'])]
    for label,methods in [('GT',['GT10']),('B32',['B32','OPT-B32']),('existing',['GT10','B32','OPT-B32','REUSE-SQ'])]:
        pp=[x for x in peers if x['method'] in methods and x['hits']>=a['hits']]
        good=[x for x in pp if x['qps']>=a['qps'] and (x['hits']>a['hits'] or x['qps']>a['qps'])]
        a[label+'_covers']=';'.join(f"{x['method']}@{x['L']}" for x in good)
        best=max(pp,key=lambda x:x['qps']) if pp else None
        a[label+'_threshold_method']=best['method'] if best else '';a[label+'_threshold_L']=best['L'] if best else '';a[label+'_threshold_recall_pct']=best['recall_pct'] if best else '';a[label+'_threshold_qps']=best['qps'] if best else '';a[label+'_threshold_speed_gain_pct']=(a['qps']/best['qps']-1)*100 if best else ''
        same=[x for x in peers if x['method'] in methods and x['qps']>=a['qps']]
        a[label+'_same_cost_recall_gain_pp']=a['recall_pct']-max(x['recall_pct'] for x in same) if same else ''
csvwrite(R/'analysis/points.csv',points)
# Union schema accommodates stage attribution and query mechanism summaries without hiding either role.
fields=list(dict.fromkeys(k for x in mechanisms for k in x))
csvwrite(R/'analysis/mechanisms.csv',[{k:x.get(k,'') for k in fields} for x in mechanisms])
csvwrite(R/'analysis/single_seed.csv',probe_rows);csvwrite(R/'analysis/candidate_oracle_audit.csv',audits)
nodes=[]
for (ds,w,K,L,isgt),v in node_groups.items():nodes.append(dict(dataset=ds,window=w,K=K,L=L,is_GT=isgt,n=v['n'],**{k:v[k]/v['n'] for k in ['indegree','outdegree','unseen_outneighbors','main_seen','zero_indegree']}))
csvwrite(R/'analysis/node_groups.csv',nodes)
def ranks(x):
    x=np.asarray(x);order=np.argsort(x,kind='stable');out=np.empty(len(x),float);i=0
    while i<len(x):
        j=i+1
        while j<len(x) and x[order[j]]==x[order[i]]:j+=1
        out[order[i:j]]=(i+j-1)/2;i=j
    return out
associations=[]
for ds in DS:
    for w in ['A','B']:
        for K in [1,100]:
            rows=[x for x in probe_rows if x['dataset']==ds and x['window']==w and int(x['K'])==K]
            y=np.array([float(x['net_vs_B32']) for x in rows]);groups=collections.defaultdict(list)
            for i,a in enumerate(rows):groups[int(a['query'])].append(i)
            for feature in ['indegree','outdegree','unseen_outneighbors','C_rank']:
                x=np.array([float(a[feature]) for a in rows]);within_x=x.copy();within_y=y.copy()
                for ix in groups.values():within_x[ix]-=within_x[ix].mean();within_y[ix]-=within_y[ix].mean()
                corr=lambda a,b:float(np.corrcoef(a,b)[0,1]) if len(a)>1 and np.std(a)>0 and np.std(b)>0 else ''
                associations.append(dict(dataset=ds,window=w,K=K,feature=feature,seed_probes=len(rows),queries=len(groups),positive_probes=int((y>0).sum()),zero_probes=int((y==0).sum()),negative_probes=int((y<0).sum()),mean_net=float(y.mean()) if len(y) else '',spearman=corr(ranks(x),ranks(y)),within_query_centered_pearson=corr(within_x,within_y),scope='descriptive fixed query-best six seeds, not causal or deployable oracle'))
csvwrite(R/'analysis/seed_associations.csv',associations)
stable=[]
for ds in DS:
    for K in [1,100]:
        for L in [100,200,400]:
            for m in NAV:
                aa=[x for x in points if x['dataset']==ds and x['K']==K and x['L']==L and x['method']==m];assert len(aa)==2
                a,b=sorted(aa,key=lambda x:x['window']);stable.append(dict(dataset=ds,K=K,L=L,method=m,A_gain_vs_B32_pp=a['gain_vs_B32_pp'],B_gain_vs_B32_pp=b['gain_vs_B32_pp'],A_existing_covered=bool(a['existing_covers']),B_existing_covered=bool(b['existing_covers']),A_B32_threshold_speed_gain_pct=a['B32_threshold_speed_gain_pct'],B_B32_threshold_speed_gain_pct=b['B32_threshold_speed_gain_pct'],both_positive_net=a['gain_vs_B32_pp']>0 and b['gain_vs_B32_pp']>0,both_not_existing_covered=not a['existing_covers'] and not b['existing_covers']))
csvwrite(R/'analysis/stability.csv',stable)
np.savez_compressed(R/'analysis/query_hits.npz',**{'|'.join(map(str,k)):v for k,v in query_hits.items()})
# Historical full-query controls retain campaign identity.
for name,path in [('historical_fixed_ID_chain',R.parent/'20261024_residual_geometry_diagnosis_v1/analysis/coverage_chain.csv'),('historical_block_chain',OLD/'analysis/all_coverage.csv'),('historical_scoring_diagnostic',OLD/'analysis/scoring_diagnostic.csv')]:
    (R/f'analysis/{name}.csv').write_bytes(path.read_bytes())
dump(R/'analysis/analysis_receipt.json',dict(status='PASS_ANALYSIS_AND_SECOND_IMPLEMENTATION_FULL_SORT',points=len(points),auxiliary_candidate_audit_points=len(audits),auxiliary_candidate_audit_queries=sum(x['queries'] for x in audits),single_seed_probes=len(probe_rows),seconds=time.perf_counter()-t,GT_changed=False,scientific_old_files_changed=False))
print('ANALYSIS_COMPLETE',len(points),flush=True)
