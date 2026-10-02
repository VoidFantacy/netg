from common import *
from verify_queries import verify_point,baseline_reference
import csv,io
threads();resources();check(O/'reviews/prequery_freeze.json');check(O/'reviews/preflight_graph_freeze.json')
jobs=read(O/'logs/jobs.json');assert len(jobs)==6 and all(j['status']=='COMPLETE' and j['returncode']==0 for j in jobs)
assert all(jobs[i]['completed_at']<=jobs[i+1]['started_at'] for i in range(5))
models=['baseline','duplicate3P','mode3P'];points=[];paired=[];cases=[];cohorts=[];selection={};graphs=[];scored=0;recoveries=0
pop=np.array([int(i).bit_count() for i in range(1024)],np.uint8)
def comparison(ds,split,ref,name,a,b,rows):
    dh=b['hits'].astype(int)-a['hits'];gain=int(np.maximum(dh,0).sum());loss=int(np.maximum(-dh,0).sum())
    member_gain=int(pop[b['masks']&(~a['masks']&1023)].sum());member_loss=int(pop[a['masks']&(~b['masks']&1023)].sum())
    rescued=(a['hits']==0)&(b['hits']>0);newfail=(a['hits']>0)&(b['hits']==0)
    assert gain-loss==member_gain-member_loss==int(b['hits'].sum())-int(a['hits'].sum())
    assert int(rescued.sum())-int(newfail.sum())==int((a['hits']==0).sum())-int((b['hits']==0).sum())
    rec=dict(dataset=ds,split=split,reference=ref,model=name,n=len(rows),net_hits=gain-loss,recall_change_pp=(gain-loss)/len(rows)*10,
        net_query_gain_hits=gain,net_query_loss_hits=loss,member_gain=member_gain,member_loss=member_loss,rescued=int(rescued.sum()),new_failures=int(newfail.sum()),
        failure_net_change=int(newfail.sum())-int(rescued.sum()),changed_queries=int(np.any(a['entries']!=b['entries'],axis=1).sum()),
        total_ndc_change_pct=100*(np.mean(b['route_ndc'].astype(float)+b['graph_ndc'])/np.mean(a['route_ndc'].astype(float)+a['graph_ndc'])-1))
    for i in np.flatnonzero(rescued|newfail):
        cases.append(dict(dataset=ds,split=split,reference=ref,model=name,source_row=int(rows[i]),before_hits=int(a['hits'][i]),after_hits=int(b['hits'][i]),
            before_entries=' '.join(map(str,a['entries'][i])),after_entries=' '.join(map(str,b['entries'][i])),before_mask=int(a['masks'][i]),after_mask=int(b['masks'][i])))
    if ref=='baseline' and split in ['fit','aux']:
        for oldhits in range(11):
            ix=a['hits']==oldhits;dn=dh[ix]
            cohorts.append(dict(dataset=ds,split=split,model=name,baseline_hits=oldhits,n=int(ix.sum()),net_hits=int(dn.sum()),
                gain=int(np.maximum(dn,0).sum()),loss=int(np.maximum(-dn,0).sum()),member_gain=int(pop[(b['masks']&(~a['masks']&1023))[ix]].sum()),
                member_loss=int(pop[(a['masks']&(~b['masks']&1023))[ix]].sum()),rescued=int((rescued&ix).sum()),new_failures=int((newfail&ix).sum())))
    return rec
for ds in DS:
    allraw={};dspairs={}
    for split in ['fit','aux']:
        c=read(O/'inputs'/ds/(split+'.json'));rows=np.fromfile(c['row_ids'],np.int64)[:c['num_queries']];raw={}
        for m in models:
            raw[m],g=verify_point(ds,split,m);graphs.append(g);scored+=len(rows)
            assert g['sha256']==sha(O/'results'/ds/'preflight'/(m+'_L128.hnsw'))
        equal(raw['baseline'],baseline_reference(ds,split,len(rows)));recoveries+=len(rows);allraw[split]=raw
        slices=[(split,slice(None))] if split=='fit' else [('aux',slice(None)),('aux_first',slice(0,3976)),('aux_second',slice(3976,None))]
        for label,s in slices:
            subset={m:{k:v[s] for k,v in raw[m].items()} for m in models}
            for m,p in subset.items():
                points.append(dict(dataset=ds,split=label,model=m,L=128,n=len(p['hits']),hits=int(p['hits'].sum()),recall=float(p['hits'].mean()/10),
                    failures=int((p['hits']==0).sum()),failure_rate=float((p['hits']==0).mean()),route_ndc=float(p['route_ndc'].mean()),graph_ndc=float(p['graph_ndc'].mean()),
                    total_ndc=float(np.mean(p['route_ndc'].astype(float)+p['graph_ndc'])),QPS=None))
            for ref,name in [('baseline','duplicate3P'),('baseline','mode3P'),('duplicate3P','mode3P')]:
                rec=comparison(ds,label,ref,name,subset[ref],subset[name],rows[s]);paired.append(rec);dspairs[(label,ref,name)]=rec
    f=dspairs['fit','baseline','mode3P'];a=dspairs['aux','baseline','mode3P'];x=dspairs['aux_first','baseline','mode3P'];y=dspairs['aux_second','baseline','mode3P']
    rules=dict(fit_nonnegative=f['net_hits']>=0,aux_positive=a['net_hits']>0,both_halves_nonnegative=min(x['net_hits'],y['net_hits'])>=0,
        failures_nonincreasing=a['failure_net_change']<=0,total_NDC_within_one_percent=bool(a['total_ndc_change_pct']<=1))
    selection[ds]=dict(candidate='mode3P',passed=all(rules.values()),rules=rules,fit_net_hits=f['net_hits'],aux_net_hits=a['net_hits'],aux_halves=[x['net_hits'],y['net_hits']],
        aux_failure_net_change=a['failure_net_change'],duplicate_not_selectable=True,aux_net_vs_duplicate=dspairs['aux','duplicate3P','mode3P']['net_hits'])
for name,data in [('points',points),('paired',paired),('failure_cases',cases),('cohorts',cohorts)]:
    f=io.StringIO(newline='');w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
    target=O/'results'/(name+'.csv')
    expected=f.getvalue().replace('\r\n','\n')
    if target.exists():assert target.read_text()==expected
    else:target.write_text(expected)
dump(O/'results/selection.json',dict(status='FROZEN_DEVELOPMENT_GATE_NO_FINAL_FEEDBACK',datasets=selection))
dump(O/'reviews/verification.json',dict(status='PASS',independent_query_sets=scored,baseline_recovered_queries=recoveries,
    full_plain_count_queries=scored+768,original_kernel_parity_queries=288,all_seven_slot_dedup_verified=True,graphs=graphs,
    new_NSG=sum(j['actual_NSG'] for j in jobs),new_HNSW=sum(j['actual_NSG']-48 for j in jobs),new_builds=4,baseline_graph_source_loads=2,
    subsequent_graph_source_loads=12,plain_count_loads=18,synthetic=read(O/'reviews/synthetic/verification.json'),jobs=jobs,
    final_validation_access=False,heldout_access=False,roles='fit historical training; auxiliary7952 historically exposed selection training'))
dump(O/'state.json',dict(status='COMPLETE_MULTIMODE_DEVELOPMENT',selection=selection,new_NSG=sum(j['actual_NSG'] for j in jobs),native_pids=[],formal_QPS_points=0,day_goal_complete=False))
print('ANALYSIS_PASS',json.dumps(selection),flush=True)
