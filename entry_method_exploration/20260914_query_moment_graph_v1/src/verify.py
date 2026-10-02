from common import *
import csv, sys
os.sched_setaffinity(0,{8})
phase=sys.argv[1];assert phase in ['preflight','aux']
check(O/'reviews/prequery_freeze.json');check(O/'reviews/protected_before.json')
check(O/'reviews/analysis_source_freeze.json')
sources=read(O/'inputs/sources.json');rows_out=[];aligned={};verified=0;regression=0;failures=[];gate=[]
DT={'ids.i32':np.int32,'distances.f32':np.float32,'entry_ids.i32':np.int32,'hits.u8':np.uint8,'hitmask.u16':np.uint16,'route_ndc.u32':np.uint32,'graph_ndc.u32':np.uint32,'router_labels.i32':np.int32}
def data(p,n):
    result={}
    for f,dtype in DT.items():
        k=10 if f in ['ids.i32','distances.f32'] else 3 if f in ['entry_ids.i32','router_labels.i32'] else 1
        a=np.fromfile(p/f,dtype);assert a.size==n*k,(p,f,a.size)
        result[f]=a.reshape(n,k) if k>1 else a
    return result
for ds in DS:
    cfg=read(O/'inputs'/f'{ds}_{phase}.json');out=O/'results'/ds/phase;r=read(out/'results.json');n=cfg['num_queries']
    assert r['status']=='COMPLETE' and r['threads']==1 and r['timing_repeats']==0
    assert r['GT_opened_after_all_raw_search'] and r['physical_graph_calls']==6*(2*n+16)
    assert read(out/'thread_contract.json')=={'status':'PASS','process_threads':1,'actual_openmp_threads':1,'cpu':15}
    gt=np.fromfile(cfg['gt_file'],np.int64).reshape(7952,100)[:n,:10]
    rows=np.fromfile(out/'row_ids.i64',np.int64);assert np.array_equal(rows,np.fromfile(cfg['row_ids'],np.int64)[:n])
    assert np.all((gt>=0)&(gt<cfg['base_count'])) and all(len(set(map(int,x)))==10 for x in gt)
    measured={}
    for rec in r['methods']:
        name=rec['name'];a=data(out/name,n);measured[name]=a
        assert rec['full_plain_count_parity_queries']==n and rec['original_kernel_parity_queries']==16 and rec['repeated_output_parity']
        assert rec['qps'] is None and rec['end_to_end_seconds']==[]
        assert np.all((a['ids.i32']>=0)&(a['ids.i32']<cfg['base_count'])) and np.isfinite(a['distances.f32']).all()
        allowed=set(map(int,np.fromfile(rec['configuration']['mapping'],np.int32)))
        assert all(len(set(map(int,x)))==3 and list(x)==sorted(x) and set(map(int,x))<=allowed for x in a['entry_ids.i32'])
        masks=np.array([sum(1<<j for j,v in enumerate(g) if int(v) in set(map(int,vv))) for vv,g in zip(a['ids.i32'],gt)],np.uint16)
        hits=np.array([int(x).bit_count() for x in masks],np.uint8)
        assert np.array_equal(hits,a['hits.u8']) and np.array_equal(masks,a['hitmask.u16'])
        assert int(hits.sum())==rec['total_hits'] and int((hits==0).sum())==rec['failed_queries']
        for f,key in [('route_ndc.u32','mean_route_ndc'),('graph_ndc.u32','mean_graph_ndc')]:assert a[f].mean()==rec[key]
        assert rec['mean_total_ndc']==(a['route_ndc.u32'].astype(float)+a['graph_ndc.u32']).mean()
        verified+=n
        if phase=='aux':
            old=data(O/'results'/ds/'preflight'/name,128)
            for f in DT:assert a[f][:128].tobytes()==old[f].tobytes(),(ds,name,f)
    for name in ['identity','full','diag']:
        lo,hi=measured[name+'_L64'],measured[name+'_L128']
        assert lo['entry_ids.i32'].tobytes()==hi['entry_ids.i32'].tobytes()
        assert lo['route_ndc.u32'].tobytes()==hi['route_ndc.u32'].tobytes()
    old=data(E73/'results'/ds/'aux'/'baseline10_L128',7952);new=measured['identity_L128']
    for f in DT:assert old[f][:n].tobytes()==new[f].tobytes(),(ds,f,'baseline')
    regression+=n
    for name in ['full','diag']:
        feasible=True;signal_found=False;conditions=[]
        for L in [64,128]:
            b=measured[f'identity_L{L}'];a=measured[f'{name}_L{L}'];delta=a['hits.u8'].astype(int)-b['hits.u8'].astype(int)
            if phase=='aux':aligned[f'{ds}_{name}_L{L}']=dict(source_rows=rows,delta=delta,old_hits=b['hits.u8'],new_hits=a['hits.u8'],old_entries=b['entry_ids.i32'],new_entries=a['entry_ids.i32'])
            ranges=[('full',slice(None))]+([('half0',slice(0,3976)),('half1',slice(3976,None))] if phase=='aux' else [])
            for group,sl in ranges:
                bh=b['hits.u8'][sl];ah=a['hits.u8'][sl];dd=delta[sl]
                rec=dict(dataset=ds,model=name,L=L,group=group,queries=len(dd),baseline_recall_pp=float(bh.mean()*10),recall_pp=float(ah.mean()*10),net_hits=int(dd.sum()),delta_recall_pp=float(dd.mean()*10),helped_queries=int((dd>0).sum()),harmed_queries=int((dd<0).sum()),gain_hits=int(dd[dd>0].sum()),loss_hits=int(-dd[dd<0].sum()),rescued=int(((bh==0)&(ah>0)).sum()),new_failures=int(((bh>0)&(ah==0)).sum()),delta_failures=int((ah==0).sum()-(bh==0).sum()),changed_entries=int(np.any(a['entry_ids.i32'][sl]!=b['entry_ids.i32'][sl],axis=1).sum()),route_change_pct=float((a['route_ndc.u32'][sl].mean()/b['route_ndc.u32'][sl].mean()-1)*100),graph_change_pct=float((a['graph_ndc.u32'][sl].mean()/b['graph_ndc.u32'][sl].mean()-1)*100),QPS=None)
                assert rec['net_hits']==rec['gain_hits']-rec['loss_hits'] and rec['delta_failures']==rec['new_failures']-rec['rescued']
                rows_out.append(rec);feasible &= rec['net_hits']>=0 and rec['delta_failures']<=0
                if group=='full':
                    feasible &= rec['graph_change_pct']<=1.0
                    signal_found |= rec['delta_recall_pp']>=.1 or rec['route_change_pct']<=-10
                conditions.append(rec)
            for i in np.flatnonzero((b['hits.u8']==0)|(a['hits.u8']==0)):
                failures.append(dict(dataset=ds,model=name,L=L,source_row=int(rows[i]),baseline_hits=int(b['hits.u8'][i]),candidate_hits=int(a['hits.u8'][i]),GT10=' '.join(map(str,gt[i])),baseline_entries=' '.join(map(str,b['entry_ids.i32'][i])),candidate_entries=' '.join(map(str,a['entry_ids.i32'][i])),baseline_ids=' '.join(map(str,b['ids.i32'][i])),candidate_ids=' '.join(map(str,a['ids.i32'][i]))))
        if phase=='aux':gate.append(dict(dataset=ds,model=name,quality_and_failure_and_cost=bool(feasible),signal=bool(signal_found),pass_development=bool(feasible and signal_found)))
def save_csv(path,records):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
save_csv(O/'results'/f'{phase}_paired.csv',rows_out)
save_csv(O/'results'/f'{phase}_failures.csv',failures)
for name,values in aligned.items():np.savez_compressed(O/'results'/(name+'.npz'),**values)
verification=dict(status='PASS',phase=phase,independent_set_mask_rows=verified,baseline_full_fields_regression_rows=regression,baseline_fields=list(DT),cross_L_entries_unchanged=True,parity_samples=12*16,GT_after_search=True,QPS_points=0)
dump(O/'reviews'/f'{phase}_verification.json',verification)
if phase=='aux':
    any_pass=any(x['pass_development'] for x in gate)
    dump(O/'results/gate.json',dict(status='GO_TO_FROZEN_WALL_DESIGN' if any_pass else 'STOP_E95_NO_DEVELOPMENT_GATE',candidates=gate,rule_source='protocol.md',default_changed=False,performance_GO=False))
    jobs=read(O/'logs/jobs.json');calls=sum(x['reserved_NSG'] for x in jobs if x['kind']=='query');assert calls==194304 and all(x['exit_code']==0 for x in jobs)
    dump(O/'results/cost.json',dict(NSG=calls,HNSW=193920,builds=6,vector_installs=4,gradient_updates=0,new_GT=0,new_training_search_labels=0,new_QPS_points=0,statistics_seconds=sum(x['statistics_seconds'] for x in read(O/'results/construction.json')['records']),build_process_seconds=sum(x['seconds'] for x in jobs if x['kind']=='build'),native_build_seconds=sum(x['native_build']['build_seconds'] for x in jobs if x['kind']=='build'),query_native_operation_seconds=sum(x['seconds'] for x in jobs if x['kind']=='query'),pure_performance_wall_seconds=None,inherited_full_GT_P_training_cost=None,unknown_reason='not remeasured; operation seconds are not QPS',output_bytes=sum(p.stat().st_size for p in O.rglob('*') if p.is_file())))
    dump(O/'state.json',dict(status='DEVELOPMENT_GATE_PASSED' if any_pass else 'COMPLETE_E95_STOP',default_changed=False,NSG=calls,HNSW=193920,builds=6,new_QPS_points=0,pending_native_jobs=[]))
check(O/'reviews/protected_before.json')
print(json.dumps(verification),flush=True)
if phase=='aux':print(json.dumps(gate),flush=True)
