from common import *
from graph_reader import inspect_serialized
import csv
threads();resources();check(O/'reviews/prequery_freeze.json');started=time.monotonic()
jobs=read(O/'logs/jobs.json');assert len(jobs)==2 and all(j['status']=='COMPLETE' and j['peak_threads']==1 and j['affinity']==[15] for j in jobs)
E64=C/'stage5_frozen_pool_aux_v1';points=[];timings=[];paired=[];failures=[];interp=[];records={};scored=regressed=graphs=0
def readpoint(folder):
    return dict(ids=np.fromfile(folder/'ids.i32',np.int32).reshape(-1,10),distances=np.fromfile(folder/'distances.f32',np.float32).reshape(-1,10),entries=np.fromfile(folder/'entry_ids.i32',np.int32).reshape(-1,3),
      route_ndc=np.fromfile(folder/'route_ndc.u32',np.uint32),graph_ndc=np.fromfile(folder/'graph_ndc.u32',np.uint32),hits=np.fromfile(folder/'hits.u8',np.uint8),hitmask=np.fromfile(folder/'hitmask.u16',np.uint16))
for ds in DS:
    cfg=read(O/'inputs'/ds/'config.json');out=O/'results'/ds;result=read(out/'results.json');n=cfg['num_queries'];assert n==2048
    gt=np.fromfile(cfg['gt_file'],np.int64).reshape(n,100);rows=np.fromfile(cfg['row_ids'],np.int64);assert np.array_equal(rows,np.arange(2048,4096))
    tc=read(out/'thread_contract.json');assert tc['process_threads']==tc['actual_openmp_threads']==1 and tc['cpu']==15
    assert result['timing_repeats']==5 and result['GT_opened_after_all_raw_search'] and result['physical_graph_calls']==cfg['real_call_cap']
    assert (out/'row_ids.i64').read_bytes()==Path(cfg['row_ids']).read_bytes();raw={};modelgraph={};modelentry={}
    progress=read(out/'timing_progress.json');expected_order=[]
    for rep in range(5):
        for ordinal,L in enumerate([64,128,256,400,800]):
            ms=[m['name'] for m in cfg['methods'] if m['L']==L];offset=(DS.index(ds)+rep+ordinal)%len(ms);ms=ms[offset:]+ms[:offset]
            expected_order.extend((name,rep,L) for name in ms)
    assert [(x['name'],x['repeat'],x['L']) for x in progress]==expected_order
    for m in result['methods']:
        name=m['model_name'];L=m['L'];c=m['configuration'];a=readpoint(out/m['name']);raw[name,L]=a
        h=ihits(a['ids'],gt);mask=np.array([sum(1<<r for r,g in enumerate(grow[:10]) if int(g) in set(map(int,ret))) for ret,grow in zip(a['ids'],gt)],np.uint16)
        assert np.array_equal(h,a['hits']) and np.array_equal(mask,a['hitmask']) and np.isfinite(a['distances']).all()
        assert (a['ids']>=0).all() and (a['ids']<cfg['base_count']).all() and all(len(set(map(int,row)))==10 for row in a['ids'])
        if name!='nsg':
            mapping=np.fromfile(c['mapping'],np.int32);W=np.fromfile(c['W'],np.float32).reshape(len(mapping),cfg['dim']);path=out/(m['name']+'.hnsw')
            assert sha(path)==sha(c['graph_file']);inspect_serialized(path,W,mapping);graphs+=1
            assert np.isin(a['entries'],mapping).all() and all(len(set(map(int,row)))==3 for row in a['entries'])
            if name in modelgraph:assert modelgraph[name]==sha(path) and modelentry[name]==a['entries'].tobytes()
            modelgraph[name]=sha(path);modelentry[name]=a['entries'].tobytes()
        else:assert (a['route_ndc']==0).all() and (a['entries'][:,0]==c['fixed_entry']).all()
        assert m['full_plain_count_parity_queries']==n and m['original_kernel_parity_queries']==16 and m['repeated_output_parity']
        assert int(h.sum())==m['total_hits'] and int((h==0).sum())==m['failed_queries']
        seconds=np.asarray(m['end_to_end_seconds']);qps=n/seconds;assert len(seconds)==5 and (seconds>0).all()
        np.testing.assert_allclose(qps,m['qps_runs'],rtol=1e-13,atol=0);assert float(np.median(qps))==m['qps']
        np.testing.assert_allclose([a['route_ndc'].mean(),a['graph_ndc'].mean()],[m['mean_route_ndc'],m['mean_graph_ndc']],atol=1e-10,rtol=0)
        pp=dict(dataset=ds,model=name,L=L,queries=n,recall_pct=float(h.mean()*10),failure_count=int((h==0).sum()),failure_rate_pct=float((h==0).mean()*100),QPS=float(np.median(qps)),QPS_min=float(qps.min()),QPS_max=float(qps.max()),mean_route_NDC=float(a['route_ndc'].mean()),mean_graph_NDC=float(a['graph_ndc'].mean()))
        points.append(pp)
        for rep,(sec,rate) in enumerate(zip(seconds,qps)):timings.append(dict(dataset=ds,model=name,L=L,repeat=rep,seconds=float(sec),QPS=float(rate)))
        if L==128 and name in ['best_new','baseline_soft','gt10_hard']:
            source=c.get('selected_source_name') if name=='best_new' else ('baseline' if (name=='baseline_soft' or ds==DS[1]) else None)
            if source:
                old=readpoint(E64/'results'/ds/(source+'_L128'))
                for key in FIELDS+['hits','hitmask']:assert a[key].tobytes()==old[key][:n].tobytes(),(ds,name,key)
                regressed+=n
        scored+=n
    records[ds]=raw
    for L in [64,128,256,400,800]:
        a=raw['best_new',L];h=a['hits'].astype(int);newp=next(x for x in points if x['dataset']==ds and x['model']=='best_new' and x['L']==L)
        for comparator in ['nsg','fast30k','gt10_hard']+(['baseline_soft'] if ds==DS[0] else []):
            b=raw[comparator,L];bh=b['hits'].astype(int);dh=h-bh;bp=next(x for x in points if x['dataset']==ds and x['model']==comparator and x['L']==L)
            net=int(dh.sum());rescued=int(((bh==0)&(h>0)).sum());newfail=int(((bh>0)&(h==0)).sum());assert rescued-newfail==int((bh==0).sum()-(h==0).sum())
            rng=np.random.default_rng(20260913);boots=np.array([dh[rng.integers(0,n,n)].mean()*10 for _ in range(2000)]);ci=np.quantile(boots,[.025,.975])
            paired.append(dict(dataset=ds,L=L,comparator=comparator,delta_recall_pp=float(dh.mean()*10),net_hits=net,gain_hits=int(np.maximum(dh,0).sum()),loss_hits=int(np.maximum(-dh,0).sum()),rescued=rescued,new_failures=newfail,
               QPS_change_pct=(newp['QPS']/bp['QPS']-1)*100,all_range_low_pct=(newp['QPS_min']/bp['QPS_max']-1)*100,all_range_high_pct=(newp['QPS_max']/bp['QPS_min']-1)*100,
               descriptive_query_bootstrap_low_pp=float(ci[0]),descriptive_query_bootstrap_high_pp=float(ci[1])))
            if comparator==('baseline_soft' if ds==DS[0] else 'gt10_hard'):
                for i in np.flatnonzero(((bh==0)&(h>0))|((bh>0)&(h==0))):
                    failures.append(dict(dataset=ds,L=L,source_row=int(rows[i]),baseline_hits=int(bh[i]),new_hits=int(h[i]),kind='rescued' if bh[i]==0 else 'new_failure',baseline_entries=' '.join(map(str,b['entries'][i])),new_entries=' '.join(map(str,a['entries'][i]))))
    # Descriptive interpolation only within the overlap of measured nondominated frontiers.
    def frontier(name):
        ps=[x for x in points if x['dataset']==ds and x['model']==name]
        return sorted([x for x in ps if not any(y['recall_pct']>=x['recall_pct'] and y['QPS']>=x['QPS'] and (y['recall_pct']>x['recall_pct'] or y['QPS']>x['QPS']) for y in ps)],key=lambda x:x['recall_pct'])
    an=frontier('best_new');bn=frontier('baseline_soft' if ds==DS[0] else 'gt10_hard');lo=max(an[0]['recall_pct'],bn[0]['recall_pct']);hi=min(an[-1]['recall_pct'],bn[-1]['recall_pct'])
    if hi>lo:
        for recall in np.linspace(lo,hi,5)[1:-1]:
            rates=[np.exp(np.interp(recall,[x['recall_pct'] for x in f],np.log([x['QPS'] for x in f]))) for f in [an,bn]]
            interp.append(dict(dataset=ds,recall_pct=float(recall),new_QPS_estimate=float(rates[0]),baseline_QPS_estimate=float(rates[1]),change_pct=float((rates[0]/rates[1]-1)*100),scope='descriptive log-QPS interpolation on historical development, not measured equal-Recall point'))
for file,data in [('points',points),('timings',timings),('paired',paired),('failure_cases',failures),('frontier_interpolation',interp)]:
    with (O/'results'/f'{file}.csv').open('w',newline='') as f:
        if data:w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
assert scored==92160 and regressed==8192 and graphs==35 and sum(j['actual_NSG'] for j in jobs)==645840
dump(O/'results/cost.json',dict(NSG_calls=645840,HNSW_calls=501760,formal_development_points=45,plain_wall_batches=225,physical_graphs_loaded=35,plain_count_loads=70,new_builds=0,gradient_updates=0,new_GT=0,native_job_seconds=sum(j['seconds'] for j in jobs),
    route_only_seconds=None,graph_only_seconds=None,component_reason='Not separately measured in this bounded version; independent full end-to-end wall reported',jobs=jobs))
dump(O/'reviews/verification.json',dict(status='PASS',independent_set_and_mask_scores=scored,physical_graphs=graphs,E64_L128_byte_regression_rows=regressed,full_plain_count_rows=scored,original_kernel_parity_rows=720,wall_batches=225,rotation_order_verified=True,five_L_graph_and_entry_identity=True,selection_unchanged=True,analysis_seconds=time.monotonic()-started))
dump(O/'state.json',dict(status='COMPLETE_DEVELOPMENT_WALL_VERIFIED',formal_development_QPS_points=45,final_validation_QPS_points=0,day_goal_complete=False))
print('E65_ANALYZE_PASS',json.dumps({'points':len(points),'paired':paired,'frontier':interp}),flush=True)
