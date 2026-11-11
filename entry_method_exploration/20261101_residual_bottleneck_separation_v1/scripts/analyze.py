from common import *
from archive import load_packets
import collections, gzip, struct
assert read(R/'formal_complete.json')['status']=='PASS_FROZEN_FORMAL_MATRIX_COMPLETE'
if not (R/'analysis/decision_audit.json').exists():
    subprocess.run([str(REPO/'.venv_cpu/bin/python'),str(R/'scripts/decision_audit_all.py')],cwd=REPO,check=True)
started=time.perf_counter();points=[];comparisons=[];diagnosis=[];native_audits=[];old_parities=[]
query_hits={};model_comparisons=[];point_payload_checks=0;witness_queries=0;diagnostic_probes=0

def hit_counts(ids,g,K):
    result=np.empty(len(ids),dtype=np.int16)
    for off in range(0,len(ids),64):
        result[off:off+64]=(ids[off:off+64,:,None]==g[off:off+64,None,:K]).any(2).sum(1)
    return result

def paired_rescue(final,baseline,g,K):
    gain=loss=outside=0
    for f,b,G in zip(final,baseline,g[:,:K]):
        truth=set(map(int,G));Fset=set(map(int,f))&truth;Bset=set(map(int,b))&truth
        gain+=len(Fset-Bset);loss+=len(Bset-Fset)
    return gain,loss

for ds in DS:
    for window in ['A','B']:
        c=read(R/'configs'/f'{ds}.{window}.json');root=Path(c['output_dir']);info=read(root/'complete.json')
        assert info['points']==len(c['points']) and info['batches']==3*len(c['points'])
        archive=load_packets(root);n=c['queries']['n'];G=np.fromfile(c['test_gt']['path'],'<i4').reshape(n,100)
        gs_sha=sha(c['test_gt']['path']);records={(int(p['K']),int(p['L']),p['method']):p for p in info['results']}
        packets={};local=[]
        for key,p in records.items():
            K,L,m=key;prefix=f'k{K}/{m}_L{L}'
            def raw(name):return archive[prefix+'/raw/'+name]
            ids=np.frombuffer(raw('ids.i32'),'<i4').reshape(n,K)
            values=np.frombuffer(raw('distances.f32'),'<f4').reshape(n,K)
            entries=np.frombuffer(raw('entry_ids.i32'),'<i4').reshape(n,3)
            profile=np.frombuffer(raw('profile_distances.f32'),'<f4').reshape(n,3)
            assert np.all((ids>=0)&(ids<c['base']['n'])) and np.isfinite(values).all()
            assert (np.diff(values,axis=1)>=0).all() and all(len(set(map(int,a)))==K for a in ids)
            digest=hashlib.sha256(struct.pack('<QQ',n,K))
            for name in ['ids.i32','distances.f32','entry_ids.i32','profile_distances.f32']:digest.update(raw(name))
            digest.update(bytes(16*n)) # Both native Batch NDC arrays remain zero in this scalar layout.
            for v in p['rounds']:
                assert v['packet_sha256']==digest.hexdigest() and v['threads']==1
                assert abs(v['qps']-n/v['wall_seconds'])<=1e-8*max(1,v['qps'])
            qps=[v['qps'] for v in p['rounds']];assert abs(p['qps']-sorted(qps)[1])<1e-9
            work=np.frombuffer(archive[prefix+'/work.u64'],'<u8').reshape(n,8)
            hits=hit_counts(ids,G,K);packets[key]=(ids,values,entries,profile,work,hits)
            query_hits['|'.join(map(str,[ds,window,K,L,m]))]=hits
            row=dict(dataset=ds,window=window,K=K,L=L,method=m,n=n,hits=int(hits.sum()),
                recall_pct=float(hits.mean()*100/K),qps=float(p['qps']),qps_min=min(qps),qps_max=max(qps),
                mean_us=1e6/float(p['qps']),formal_batch_seconds=sum(v['wall_seconds'] for v in p['rounds']),
                failed_lt10=int((hits<10).sum()) if K==100 else '',
                GT_privileged=m.startswith('ORACLE'),full_table=m.endswith('-FULL') or m in ['OPT-B32','REF-DIST384','REUSE-SQ'],
                seed_file_collected=p['seed_ids_in_separate_file_collected'])
            for j,name in enumerate(['C_exact','representative_exact','aux_exact','aux_expanded','neighbor_slots','selection_slots','seed_positions','reused_or_SQ_scans']):
                row[name+'_per_query']=float(work[:,j].mean()) if m not in ['GT10','OPT-B32','Q8-B32'] else ''
            local.append(row);point_payload_checks+=1
        bykey={(r['K'],r['L'],r['method']):r for r in local}
        # Validate each complete candidate witness with an independent full sort of all actual scores.
        for key,p in records.items():
            K,L,m=key;prefix=f'k{K}/{m}_L{L}';wkey=prefix+'/witness.bin.gz'
            if wkey not in archive:continue
            data=archive[wkey];pos=0;C_counts=[];saved_seed_counts=[]
            for qi in range(n):
                i,k,ne,ns=struct.unpack_from('<IIII',data,pos);pos+=16
                assert i==qi and k==K and ne<=480 and ns<=3
                dtype=np.dtype([('id','<i4'),('v','<f4')])
                main=np.frombuffer(data,dtype,count=K,offset=pos);pos+=8*K
                extra=np.frombuffer(data,dtype,count=ne,offset=pos);pos+=8*ne
                seeds=np.frombuffer(data,'<i4',count=ns,offset=pos);pos+=4*ns
                ii=np.r_[main['id'],extra['id']];vv=np.r_[main['v'],extra['v']]
                assert len(set(map(int,ii)))==len(ii) and np.isfinite(vv).all()
                assert np.all((ii>=0)&(ii<c['base']['n'])) and np.all((seeds>=0)&(seeds<c['base']['n']))
                selected=np.lexsort((np.arange(len(ii)),vv))[:K]
                actual=packets[key]
                assert np.array_equal(ii[selected],actual[0][qi])
                assert np.array_equal(vv[selected].view('<u4'),actual[1][qi].view('<u4'))
                if not m.startswith('EARLY') and (K,L,'GT10') in packets:
                    gtpacket=packets[K,L,'GT10']
                    assert np.array_equal(main['id'],gtpacket[0][qi])
                    assert np.array_equal(main['v'].view('<u4'),gtpacket[1][qi].view('<u4'))
                if p['seed_ids_in_separate_file_collected']:
                    chosen=np.frombuffer(archive[prefix+'/seeds.i32'],'<i4').reshape(n,3)[qi]
                    assert np.array_equal(chosen[:ns],seeds) and np.all(chosen[ns:]==-1)
                C_counts.append(ne if m in ['OPT-B32','Q8-B32'] else 0);saved_seed_counts.append(ns);witness_queries+=1
            assert pos==len(data)
            if m in ['OPT-B32','Q8-B32']:bykey[key]['C_exact_per_query']=float(np.mean(C_counts))
            native_audits.append(dict(dataset=ds,window=window,K=K,L=L,method=m,queries=n,
                fullsort_ID_and_float_bits=True,actual_main_byte_parity_checked=(not m.startswith('EARLY') and (K,L,'GT10') in packets),
                witness_seed_positions_per_query=float(np.mean(saved_seed_counts))))
        # Frozen original controls must reproduce E195 actual packets where a matching point exists.
        oldroot=Path(read(OLD/'configs'/f'{ds}.{window}.json')['output_dir'])
        for (K,L,m),value in packets.items():
            oldm={'GT10':'GT10','OPT-B32':'B32','REF-DIST384':'DIST384','REUSE-SQ':'REUSE-SQ'}.get(m)
            if oldm is None:continue
            op=oldroot/f'k{K}'/f'{oldm}_L{L}'/'raw'
            if not op.exists():continue
            for name,array in [('ids.i32',value[0]),('distances.f32',value[1]),('entry_ids.i32',value[2]),('profile_distances.f32',value[3])]:
                assert (op/name).read_bytes()==array.tobytes(),(ds,window,K,L,m,name)
            old_parities.append(dict(dataset=ds,window=window,K=K,L=L,method=m,old_method=oldm,all_four_arrays_byte_equal=True))
        # Query-level complete returns, rescue/damage, exact gate branch, and nearby-control comparison.
        for row in local:
            key=row['K'],row['L'],row['method'];K,L,m=key;ids,dist,entries,prof,work,hits=packets[key]
            for baseline,label in [('OPT-B32','strong'),('Q8-B32','Q8'),('GT10','GT10')]:
                bkey=(K,L,baseline)
                if bkey not in packets:continue
                base=packets[bkey];rescued,lost=paired_rescue(ids,base[0],G,K);delta=hits-base[5]
                assert rescued-lost==int(delta.sum())
                row.update({f'gain_vs_{label}_pp':float(delta.mean()*100/K),f'rescued_vs_{label}':rescued,
                    f'lost_vs_{label}':lost,f'improved_queries_vs_{label}':int((delta>0).sum()),
                    f'harmed_queries_vs_{label}':int((delta<0).sum())})
                if K==100:row.update({f'escaped_lt10_vs_{label}':int(((base[5]<10)&(hits>=10)).sum()),
                    f'new_lt10_vs_{label}':int(((base[5]>=10)&(hits<10)).sum())})
            if m.startswith('MODEL'):
                baseline='DIST1-FULL' if m.endswith('-FULL') else 'DIST1'
                base=packets[K,L,baseline];delta=hits-base[5]
                rescued,lost=paired_rescue(ids,base[0],G,K)
                row.update(gain_vs_distance1_pp=float(delta.mean()*100/K),rescued_vs_distance1=rescued,
                    lost_vs_distance1=lost,improved_queries_vs_distance1=int((delta>0).sum()),
                    harmed_queries_vs_distance1=int((delta<0).sum()),
                    qps_gain_vs_distance1_pct=(row['qps']/bykey[K,L,baseline]['qps']-1)*100)
            if m in ['MODEL-GATE','MODEL-GATE-FULL']:
                fullm='MODEL1' if m=='MODEL-GATE' else 'MODEL-FULL';basem='Q8-B32' if m=='MODEL-GATE' else 'OPT-B32'
                full=packets[K,L,fullm];base=packets[K,L,basem]
                for i in range(n):
                    enabled=work[i,6]>0;expected=full if enabled else base
                    assert np.array_equal(ids[i],expected[0][i]) and np.array_equal(dist[i].view('<u4'),expected[1][i].view('<u4'))
                row['actual_gate_enabled_queries']=int((work[:,6]>0).sum())
            if m in ['SHARED-CAPTURE','SHARED-CAPTURE-FULL']:
                baseline='Q8-B32' if m=='SHARED-CAPTURE' else 'OPT-B32'
                base=packets[K,L,baseline]
                assert ids.tobytes()==base[0].tobytes() and dist.tobytes()==base[1].tobytes()
                assert not np.any(work[:,2:7])
                row['capture_pipeline_delta_us_vs_direct']=row['mean_us']-bykey[K,L,baseline]['mean_us']
            if m in ['AUX384-FAST','AUX384-FAST-FULL']:
                original='AUX384' if m=='AUX384-FAST' else 'REF-DIST384'
                base=packets[K,L,original]
                assert ids.tobytes()==base[0].tobytes() and dist.tobytes()==base[1].tobytes()
                row['same_adapter_control_byte_equal']=True
            if m in ['CBRIDGE384-FULL','SHARED384-FULL']:
                base=packets[K,L,'AUX384-FAST-FULL']
                row['gain_vs_same_adapter_AUX_pp']=float((hits-base[5]).mean()*100/K)
                row['qps_gain_vs_same_adapter_AUX_pct']=(row['qps']/bykey[K,L,'AUX384-FAST-FULL']['qps']-1)*100
            if m in ['GT10','OPT-B32','REUSE-SQ'] or m.startswith('ORACLE'):continue
            controls=[b for b in local if b['K']==K and b['method'] in ['GT10','OPT-B32','REUSE-SQ']]
            dominates=lambda b:b['hits']>=row['hits'] and b['qps']>=row['qps'] and (b['hits']>row['hits'] or b['qps']>row['qps'])
            covering=[b for b in controls if dominates(b)]
            ranged=[b for b in covering if b['qps_min']>=row['qps_max']]
            no_slower=[b for b in controls if b['qps']>=row['qps']]
            quality=[b for b in controls if b['hits']>=row['hits']]
            cost=max(no_slower,key=lambda b:(b['hits'],b['qps'])) if no_slower else None
            fast=max(quality,key=lambda b:b['qps']) if quality else None
            item=dict(dataset=ds,window=window,K=K,L=L,method=m,recall_pct=row['recall_pct'],qps=row['qps'],
                strong_sameL_gain_pp=row.get('gain_vs_strong_pp',''),covered=bool(covering),range_covered=bool(ranged),
                covering_control=';'.join(f"{b['method']}/L{b['L']}" for b in covering),
                no_slower_control='' if cost is None else f"{cost['method']}/L{cost['L']}",
                no_slower_control_recall='' if cost is None else cost['recall_pct'],
                no_slower_control_qps='' if cost is None else cost['qps'],
                gain_vs_no_slower_pp='' if cost is None else row['recall_pct']-cost['recall_pct'],
                quality_threshold_control='' if fast is None else f"{fast['method']}/L{fast['L']}",
                quality_threshold_qps_gain_pct='' if fast is None else (row['qps']/fast['qps']-1)*100,
                diagnostic_only_public_single_graph=True)
            if cost:
                delta=hits-packets[K,cost['L'],cost['method']][5]
                rng=np.random.default_rng(19720261102)
                bootstrap=np.mean(delta[rng.integers(n,size=(1000,n))],axis=1)*100/K
                item['gain_no_slower_CI_lo'],item['gain_no_slower_CI_hi']=map(float,np.percentile(bootstrap,[2.5,97.5]))
            comparisons.append(item)
        points.extend(local)
        # Recompute every public diagnostic gain/loss and finite-pool oracle from actual GT hit masks.
        for bank,tag in [('Q8',window),('FULL',window+'-full')]:
            path=R/'storage/diagnosis'/ds/tag;dinfo=read(path/'complete.json')
            queries=[json.loads(a) for a in gzip.open(path/'queries.jsonl.gz','rt')]
            byquery={(int(q['K']),int(q['query'])):q for q in queries}
            native=gzip.open(path/'probes.bin.gz','rb').read();assert len(native)==72*dinfo['seed_probes']
            aggregate=collections.defaultdict(lambda:dict(best=0,positive=0,top6=0,shared_C=0,bestid=-1,closest=0))
            for offset in range(0,len(native),72):
                h=struct.unpack_from('<14i',native,offset);lo,hi=struct.unpack_from('<QQ',native,offset+56)
                qi,K,mode,seed,rank,source,bhits,gain,loss,net,extra,slots,expanded,reused=h
                q=byquery[K,qi];blo,bhi=int(q['base_mask_lo']),int(q['base_mask_hi'])
                assert bhits==blo.bit_count()+bhi.bit_count()==q['direct_hits']
                assert gain==(lo&~blo).bit_count()+(hi&~bhi).bit_count()
                assert loss==(blo&~lo).bit_count()+(bhi&~hi).bit_count() and net==gain-loss
                assert extra<=384 and slots<=64*384 and mode in [0,2]
                a=aggregate[K,qi,mode];a['positive']+=net>0
                if rank==0 and source==0:a['closest']=net
                if net>a['best']:a['best']=net;a['bestid']=seed
                if rank<6 and source==0:a['top6']=max(a['top6'],net)
                if mode==2 and source==0:a['shared_C']=max(a['shared_C'],net)
                diagnostic_probes+=1
            for (K,qi),q in byquery.items():
                a,b=aggregate[K,qi,0],aggregate[K,qi,2]
                assert a['best']==q['C_full_gain'] and a['top6']==q['C_top6_gain']
                assert b['best']==q['shared_pool_gain'] and b['shared_C']==q['shared_C_gain']
                assert a['bestid']==q['oracle_C_seed'] and b['bestid']==q['oracle_S_seed']
                baseline='OPT-B32' if bank=='FULL' else 'Q8-B32'
                model='MODEL-FULL' if bank=='FULL' else 'MODEL1'
                gate='MODEL-GATE-FULL' if bank=='FULL' else 'MODEL-GATE'
                q['model_gain']=int(packets[K,200,model][5][qi]-packets[K,200,baseline][5][qi])
                q['gate_gain']=int(packets[K,200,gate][5][qi]-packets[K,200,baseline][5][qi])
                q['gate_active']=bool(packets[K,200,gate][4][qi,6]>0)
                q['gate_wrong_reject_chosen_positive']=bool(not q['gate_active'] and q['model_gain']>0)
                q['gate_zero_or_negative_kept']=bool(q['gate_active'] and q['gate_gain']<=0)
                q['selector_missed_available_positive']=bool(q['C_full_gain']>0 and q['model_gain']<=0)
                q['distance_single_gain']=a['closest']
                dist='DIST1-FULL' if bank=='FULL' else 'DIST1'
                assert int(packets[K,200,dist][5][qi]-packets[K,200,baseline][5][qi])==q['distance_single_gain']
                q['model_regret']=q['C_full_gain']-q['model_gain']
                assert q['model_regret']>=0 and q['gate_gain']<=q['C_full_gain']
                q['teacher_replayed_in_formal']=bank=='Q8'
                if bank=='Q8':
                    for oracle,field in [('ORACLE-C1','C_full_gain'),('ORACLE-S1','shared_pool_gain')]:
                        observed=int(packets[K,200,oracle][5][qi]-packets[K,200,'Q8-B32'][5][qi])
                        assert observed==q[field],(ds,window,K,qi,oracle,observed,q[field])
                diagnosis.append(dict(dataset=ds,window=window,bank=bank,**q))
        assert sha(c['test_gt']['path'])==gs_sha
        print('ANALYZED',ds,window,len(local),flush=True)

def csv_union(path,rows):
    names=list(dict.fromkeys(k for r in rows for k in r))
    with Path(path).open('w') as f:
        w=csv.DictWriter(f,fieldnames=names);w.writeheader();w.writerows(rows)
csv_union(R/'analysis/points.csv',points);csv_union(R/'analysis/comparisons.csv',comparisons)
csv_union(R/'analysis/witness_audit.csv',native_audits);csv_union(R/'analysis/old_packet_parity.csv',old_parities)
with gzip.open(R/'analysis/query_diagnosis.csv.gz','wt',compresslevel=6) as f:
    w=csv.DictWriter(f,fieldnames=list(diagnosis[0]));w.writeheader();w.writerows(diagnosis)
np.savez_compressed(R/'analysis/query_hits.npz',**query_hits)
groups=collections.defaultdict(list)
for c in comparisons:groups[c['dataset'],c['K'],c['L'],c['method']].append(c)
stability=[]
for (ds,K,L,m),v in sorted(groups.items()):
    assert len(v)==2 and {r['window'] for r in v}=={'A','B'}
    stability.append(dict(dataset=ds,K=K,L=L,method=m,both_uncovered=all(not r['covered'] for r in v),
        both_positive_sameL_strong=all(r['strong_sameL_gain_pp']!='' and r['strong_sameL_gain_pp']>0 for r in v),
        both_positive_vs_no_slower=all(r['gain_vs_no_slower_pp']!='' and r['gain_vs_no_slower_pp']>0 for r in v),
        both_no_slower_CI_positive=all(r.get('gain_no_slower_CI_lo',-1)>0 for r in v),
        windows_range_covered=sum(r['range_covered'] for r in v)))
csvwrite(R/'analysis/stability.csv',stability)
pooled=[]
for ds in DS:
    for K in [1,100]:
        for bank in ['Q8','FULL']:
            v=[r for r in diagnosis if r['dataset']==ds and r['K']==K and r['bank']==bank]
            row=dict(dataset=ds,K=K,bank=bank,queries=len(v))
            for key in ['main_hits','direct_hits','C_top6_gain','C_full_gain','shared_C_gain','shared_pool_gain','positive_C','positive_shared_C','model_gain','gate_gain','model_regret','distance_single_gain']:
                row[key]=sum(int(r[key]) for r in v)
            row['C_full_gain_pp']=row['C_full_gain']*100/(len(v)*K)
            row['shared_C_gain_pp']=row['shared_C_gain']*100/(len(v)*K)
            row['shared_pool_gain_pp']=row['shared_pool_gain']*100/(len(v)*K)
            row['queries_C_full_better_top6']=sum(r['C_full_gain']>r['C_top6_gain'] for r in v)
            row['queries_shared_C_better_AUX']=sum(r['shared_C_gain']>r['C_full_gain'] for r in v)
            row['queries_shared_C_worse_AUX']=sum(r['shared_C_gain']<r['C_full_gain'] for r in v)
            row['queries_boundary_additional']=sum(r['shared_pool_gain']>r['shared_C_gain'] for r in v)
            row['queries_any_C_gain']=sum(r['C_full_gain']>0 for r in v)
            row['queries_model_positive']=sum(r['model_gain']>0 for r in v)
            row['model_gain_over_distance1']=row['model_gain']-row['distance_single_gain']
            row['gate_enabled_queries']=sum(r['gate_active'] for r in v)
            row['gate_positive_queries']=sum(r['gate_active'] and r['gate_gain']>0 for r in v)
            row['gate_wrong_reject_positive_queries']=sum(r['gate_wrong_reject_chosen_positive'] for r in v)
            row['gate_zero_or_negative_kept_queries']=sum(r['gate_zero_or_negative_kept'] for r in v)
            row['selector_missed_available_positive_queries']=sum(r['selector_missed_available_positive'] for r in v)
            row['gate_useful_precision']=row['gate_positive_queries']/row['gate_enabled_queries'] if row['gate_enabled_queries'] else ''
            model_positive=sum(max(r['model_gain'],0) for r in v)
            row['gate_chosen_positive_gain_retention']=sum(max(r['gate_gain'],0) for r in v)/model_positive if model_positive else ''
            row['model_oracle_gain_fraction']=row['model_gain']/row['C_full_gain'] if row['C_full_gain'] else ''
            row['gate_oracle_gain_fraction']=row['gate_gain']/row['C_full_gain'] if row['C_full_gain'] else ''
            pooled.append(row)
csvwrite(R/'analysis/bottlenecks.csv',pooled)
for ds in DS:
    model_comparisons.extend(csv.DictReader((R/'storage/models'/ds/'model_comparisons.csv').open()))
csvwrite(R/'analysis/model_calibration.csv',model_comparisons)
receipt=dict(status='PASS_FULL_ACTUAL_PACKET_WITNESS_GT_MASK_ANALYSIS',points=len(points),
    batches=3*len(points),point_packet_hashes_checked=point_payload_checks,witness_queries=witness_queries,
    original_packet_parities=len(old_parities),all_diagnostic_probes_recounted=diagnostic_probes,
    gate_exact_branch_and_full_model_finite_oracle_bounds=True,configuration_pairs=len(stability),
    both_uncovered=sum(r['both_uncovered'] for r in stability),
    both_uncovered_and_positive_vs_no_slower=sum(r['both_uncovered'] and r['both_positive_vs_no_slower'] for r in stability),
    seconds=time.perf_counter()-started,bootstrap_scope='1000 paired query descriptive, not simultaneous or blind',
    default_changed=False)
dump(R/'analysis/analysis_receipt.json',receipt);print(json.dumps(receipt),flush=True)
