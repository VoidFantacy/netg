from common import *
from graph_reader import inspect_serialized
import csv
threads();resources();started=time.monotonic();check(O/'reviews/prequery_freeze.json')
alljobs=read(O/'logs/jobs.json');jobs=[j for j in alljobs if j['status']=='COMPLETE'];assert len(jobs)==2 and all(j['status']=='COMPLETE' and j['peak_threads']==1 and j['affinity']==[15] for j in jobs)
points=[];failures=[];chosen={};allraw={};scored=0;graphs=0
def readpoint(folder):
    return dict(ids=np.fromfile(folder/'ids.i32',np.int32).reshape(-1,10),distances=np.fromfile(folder/'distances.f32',np.float32).reshape(-1,10),entries=np.fromfile(folder/'entry_ids.i32',np.int32).reshape(-1,3),
      route_ndc=np.fromfile(folder/'route_ndc.u32',np.uint32),graph_ndc=np.fromfile(folder/'graph_ndc.u32',np.uint32),hits=np.fromfile(folder/'hits.u8',np.uint8),hitmask=np.fromfile(folder/'hitmask.u16',np.uint16))
def metric(ds,name,phase,a,b,sl):
    h=a['hits'][sl].astype(int);h0=b['hits'][sl].astype(int);dh=h-h0;cost=a['route_ndc'][sl].astype(float)+a['graph_ndc'][sl];cost0=b['route_ndc'][sl].astype(float)+b['graph_ndc'][sl]
    return dict(dataset=ds,model=name,phase=phase,queries=len(h),recall_pct=float(h.mean()*10),delta_recall_pp=float(dh.mean()*10),net_hits=int(dh.sum()),gain_hits=int(np.maximum(dh,0).sum()),loss_hits=int(np.maximum(-dh,0).sum()),
      helped=int((dh>0).sum()),harmed=int((dh<0).sum()),failure_count=int((h==0).sum()),failure_rate_pct=float((h==0).mean()*100),rescued=int(((h0==0)&(h>0)).sum()),new_failures=int(((h0>0)&(h==0)).sum()),
      total_NDC=float(cost.mean()),total_NDC_change_pct=float((cost.mean()/cost0.mean()-1)*100),changed_entries=int((a['entries'][sl]!=b['entries'][sl]).any(1).sum()))
for ds in DS:
    c=read(O/'inputs'/ds/'config.json');dest=O/'results'/ds;result=read(dest/'results.json');gt=np.fromfile(c['gt_file'],np.int64).reshape(7952,100);rows=np.fromfile(c['row_ids'],np.int64)
    tc=read(dest/'thread_contract.json');assert tc['process_threads']==tc['actual_openmp_threads']==1 and tc['cpu']==15
    assert result['timing_repeats']==0 and result['GT_opened_after_all_raw_search'] and result['physical_graph_calls']==111440
    assert (dest/'row_ids.i64').read_bytes()==Path(c['row_ids']).read_bytes();base=readpoint(dest/'baseline_L128');raw={}
    for m in result['methods']:
        name=m['model_name'];a=readpoint(dest/m['name']);raw[name]=a;cfg=m['configuration']
        h=ihits(a['ids'],gt);mask=np.array([sum(1<<r for r,g in enumerate(grow[:10]) if int(g) in set(map(int,ret))) for ret,grow in zip(a['ids'],gt)],np.uint16)
        assert np.array_equal(h,a['hits']) and np.array_equal(mask,a['hitmask']);assert np.isfinite(a['distances']).all()
        assert (a['ids']>=0).all() and (a['ids']<c['base_count']).all() and all(len(set(map(int,row)))==10 for row in a['ids'])
        mapping=np.fromfile(cfg['mapping'],np.int32);W=np.fromfile(cfg['W'],np.float32).reshape(len(mapping),c['dim'])
        assert np.isin(a['entries'],mapping).all() and (np.diff(a['entries'],axis=1)>0).all()
        assert sha(dest/(m['name']+'.hnsw'))==sha(cfg['graph_file']);inspect_serialized(dest/(m['name']+'.hnsw'),W,mapping);graphs+=1
        assert int(h.sum())==m['total_hits'] and int((h==0).sum())==m['failed_queries'] and m['qps'] is None
        assert m['full_plain_count_parity_queries']==7952 and m['original_kernel_parity_queries']==16 and m['repeated_output_parity']
        np.testing.assert_allclose([a['route_ndc'].mean(),a['graph_ndc'].mean()],[m['mean_route_ndc'],m['mean_graph_ndc']],atol=1e-10,rtol=0)
        scored+=len(h)
        for phase,sl in [('aux7952',slice(None)),('half1',slice(0,3976)),('half2',slice(3976,7952))]:points.append(metric(ds,name,phase,a,base,sl))
        b=base['hits'];ix=np.flatnonzero(((b==0)&(h>0))|((b>0)&(h==0)))
        for i in ix:failures.append(dict(dataset=ds,model=name,source_row=int(rows[i]),baseline_hits=int(b[i]),new_hits=int(h[i]),kind='rescued' if b[i]==0 else 'new_failure',baseline_entries=' '.join(map(str,base['entries'][i])),new_entries=' '.join(map(str,a['entries'][i]))))
    allraw[ds]=raw
    eligibility=[];names=read(O/'config.locked.json')['new_candidates']
    for rank,name in enumerate(names):
        p=next(x for x in points if x['dataset']==ds and x['model']==name and x['phase']=='aux7952');bp=next(x for x in points if x['dataset']==ds and x['model']=='baseline' and x['phase']=='aux7952')
        halves=[next(x['net_hits'] for x in points if x['dataset']==ds and x['model']==name and x['phase']==phase) for phase in ['half1','half2']]
        rules=dict(net_positive=p['net_hits']>0,both_halves_nonnegative=min(halves)>=0,failures_nonincreasing=p['failure_count']<=bp['failure_count'],total_NDC_within_one_percent=p['total_NDC_change_pct']<=1)
        eligibility.append(dict(model=name,rules=rules,passed=all(rules.values()),net_hits=p['net_hits'],failure_count=p['failure_count'],total_NDC=p['total_NDC'],halves_net_hits=halves,fixed_rank=rank))
    key=lambda x:(x['net_hits'],-x['failure_count'],-x['total_NDC'],-x['fixed_rank']);valid=[x for x in eligibility if x['passed']]
    chosen[ds]=dict(best_all=max(valid,key=key)['model'] if valid else 'baseline',best_new=max(eligibility,key=key)['model'],candidates=eligibility,sham_selectable=False)
dump(O/'results/selection.json',dict(status='FROZEN_AUX_SELECTION_NOT_FINAL_VALIDATION',datasets=chosen,old_cal_failure_unchanged=True,auxiliary_feedback_is_training=True,final_validation_access=False))
for file,data in [('points',points),('failure_cases',failures)]:
    with (O/'results'/f'{file}.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
assert scored==111328 and graphs==14
dump(O/'results/cost.json',dict(NSG_calls=222880,HNSW_calls=222656,physical_graphs_loaded=14,plain_count_loads=28,failed_reserved_NSG=sum(j['reserved_NSG'] for j in alljobs if j['status']!='COMPLETE'),total_reserved_NSG=sum(j['reserved_NSG'] for j in alljobs),new_builds=0,new_GT=0,gradient_updates=0,QPS_points=0,native_job_seconds=sum(j['seconds'] for j in jobs),jobs=jobs))
dump(O/'reviews/verification.json',dict(status='PASS',independent_set_and_mask_scores=scored,physical_graphs=graphs,full_plain_count_rows=scored,original_kernel_parity_rows=224,selection_recomputed=True,actual_threads=1,analysis_seconds=time.monotonic()-started))
dump(O/'state.json',dict(status='COMPLETE_FIXED_POOL_AUXILIARY_REVIEW',selection=chosen,new_NSG=222880,QPS_points=0,day_goal_complete=False))
print(json.dumps(chosen,indent=2),flush=True)
