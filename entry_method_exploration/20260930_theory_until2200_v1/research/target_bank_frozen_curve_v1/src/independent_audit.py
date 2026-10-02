import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[key]='1'
import hashlib,json,math,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1];C=json.loads((R/'config.locked.json').read_text())
def read(p):return json.loads(Path(p).read_text())
def ident(p):
    p=Path(p);h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b)
    return {'bytes':p.stat().st_size,'sha256':h.hexdigest()}
def close(a,b,tol=1e-9):assert abs(a-b)<tol,(a,b)
def main():
    start=time.perf_counter();a=read(R/'results/analysis.json');jobs=read(R/'reviews/jobs_complete.json');assert jobs['status']=='PASS'
    assert (jobs['new_NSG'],jobs['new_ANN'])==(596160,595584)
    for name,v in read(R/'reviews/consumed_inputs.json').items():assert ident(name)==v,name
    for name,v in read(R/'reviews/run_frozen.json')['files'].items():assert ident(name)==v,name
    for name,v in read(R/'reviews/large_inputs_stat.json').items():
        s=Path(name).stat();assert (s.st_size,s.st_mtime_ns)==(v['bytes'],v['mtime_ns'])
    for name,v in read(R/'reviews/copied_source.json')['files'].items():assert ident(R/'src'/name)==v,name
    rng=np.random.default_rng(C['bootstrap_seed']);result={};total=0;maxerr=0.
    for ds,c in C['datasets'].items():
        n=c['n'];root=R/'results'/ds;d=a['datasets'][ds];gt=np.fromfile(c['GT'],'<i4').reshape(n,100)
        allhits=np.zeros((n,6,3),dtype='i4');sets={};loaded={};times={};center_rows=0
        timings=read(root/'timings.json');assert len(timings)==54
        for pi,p in enumerate(c['points']):
            K,L=p['K'],p['L'];point=f'k{K}_L{L}'
            for mi,name in enumerate(C['methods']):
                loc=root/point/name;ids=np.fromfile(loc/'ids.i32','<i4').reshape(n,K);correct=[]
                for i,row in enumerate(ids):
                    truth={int(x):True for x in gt[i,:K]};seen={};ok=set()
                    for x in row:
                        v=int(x);assert 0<=v<c['base_n'] and v not in seen;seen[v]=True
                        if v in truth:ok.add(v)
                    allhits[i,pi,mi]=len(ok);correct.append(ok)
                sets[pi,mi]=correct;total+=n
                rr={name2:np.fromfile(loc/file,dt).reshape(shape) for name2,file,dt,shape in [('ids','ids.i32','<i4',(n,K)),('distance','distances.f32','<f4',(n,K)),('entries','entry_ids.i32','<i4',(n,3)),('slots','route_slots.i32','<i4',(n,)),('graph','graph_ndc.u64','<u8',(n,)),('route','route_ndc.u64','<u8',(n,))]};loaded[pi,mi]=rr
                if mi==0:
                    old=Path(c['old_results'])/f'k{K}'/f'{c["anchor"]["name"]}_L{L}'
                    for file in ['ids.i32','distances.f32','entry_ids.i32','route_ndc.u64','graph_ndc.u64']:assert ident(loc/file)==ident(old/file)
                old=Path(c['previous_results'])/point/name
                if old.exists():
                    for file in ['ids.i32','distances.f32','entry_ids.i32','route_ndc.u64','graph_ndc.u64','route_slots.i32']:assert ident(loc/file)==ident(old/file)
                    center_rows+=n
                rows=sorted([x for x in timings if (x['K'],x['L'],x['method'])==(K,L,name)],key=lambda x:x['repeat'])
                assert [x['repeat'] for x in rows]==[0,1,2] and all(x['threads']==1 and x['n']==n for x in rows)
                times[pi,mi]=[x['seconds'] for x in rows]
                m=d['points'][point]['methods'][name]
                close(m['recall_pct'],sum(int(x) for x in allhits[:,pi,mi])*100/(n*K));assert m['hits']==int(allhits[:,pi,mi].sum())
                close(m['qps_pooled'],3*n/math.fsum(times[pi,mi]))
                for x,y in zip(m['qps_each'],times[pi,mi]):close(x,n/y)
                assert m['seconds']==times[pi,mi]
                for key,rkey in [('route_NDC','route'),('graph_NDC','graph')]:close(m[key],sum(int(x) for x in rr[rkey])/n)
                close(m['total_NDC'],m['route_NDC']+m['graph_NDC'])
        assert np.array_equal(np.load(root/'score_arrays.npz')['hits'],allhits)
        for pi in range(1,6):
            for mi in range(3):
                for key in ['entries','slots','route']:assert np.array_equal(loaded[pi,mi][key],loaded[0,mi][key])
        targets=np.fromfile(c['targets'],'<i4');slots=loaded[0,2]['slots'];assert ((slots>=0)&(slots<20000)).all()
        assert np.array_equal(loaded[0,2]['entries'][:,0],targets[slots]) and (loaded[0,2]['entries'][:,1:]==-1).all()
        assert (loaded[0,0]['slots']==-1).all() and (loaded[0,1]['slots']==-1).all()
        for pi,p in enumerate(c['points']):
            if p['K']!=1:continue
            matches=[j for j,x in enumerate(c['points']) if x['K']==100 and x['L']==p['L']]
            for pj in matches:
                for mi in range(3):
                    for key in ['ids','distance']:
                        left=loaded[pi,mi][key];right=loaded[pj,mi][key][:,:1]
                        assert left.tobytes()==right.tobytes(),(ds,pi,pj,mi,key)
                    assert np.array_equal(loaded[pi,mi]['graph'],loaded[pj,mi]['graph'])
        flat=allhits.reshape(n,18).astype('i8');samples=np.empty((C['bootstrap_reps'],18),'i8')
        for lo in range(0,len(samples),128):
            count=min(128,len(samples)-lo);idx=rng.integers(0,n,size=(count,n))
            weights=np.zeros((count,n),'i8')
            for i,row in enumerate(idx):weights[i]=np.bincount(row,minlength=n)
            samples[lo:lo+count]=weights@flat
        samples=samples.reshape(-1,6,3)
        def verify(v,ai,am,bi,bm):
            nonlocal maxerr
            K=c['points'][ai]['K'];assert K==c['points'][bi]['K'];delta=allhits[:,ai,am]-allhits[:,bi,bm]
            means=(samples[:,ai,am]-samples[:,bi,bm])*(100./(n*K));ci=np.quantile(means,[.025,.975]);err=float(np.max(np.abs(ci-v['descriptive_interval_pp'])));maxerr=max(maxerr,err);assert err<1e-10
            close(v['delta_recall_pp'],sum(int(x) for x in delta)*100/(n*K))
            t1=times[ai,am];t0=times[bi,bm];speed=(math.fsum(t0)/math.fsum(t1)-1)*100;close(v['delta_QPS_pct'],speed)
            for i,x in enumerate(v['paired_repeat_delta_QPS_pct']):close(x,(t0[i]/t1[i]-1)*100)
            close(v['extra_us_per_query'],(math.fsum(t1)-math.fsum(t0))/(3*n)*1e6)
            assert v['rescued_queries']==sum(x>0 for x in delta) and v['damaged_queries']==sum(x<0 for x in delta)
            assert v['net_positive_hits']==sum(max(0,int(x)) for x in delta) and v['net_negative_hits']==sum(max(0,-int(x)) for x in delta)
            added=lost=0
            for x,y in zip(sets[ai,am],sets[bi,bm]):added+=sum(z not in y for z in x);lost+=sum(z not in x for z in y)
            assert (added,lost)==(v['true_member_added'],v['true_member_lost']) and added-lost==int(delta.sum())
            assert v['empirical_dominates']==bool(delta.sum()>=0 and speed>0)
            assert v['all_three_paired_QPS_faster']==all(x<y for x,y in zip(t1,t0))
            q1=[n/x for x in t1];q0=[n/x for x in t0];assert v['QPS_ranges_overlap']==(max(min(q1),min(q0))<=min(max(q1),max(q0)))
        for pi,p in enumerate(c['points']):
            point=d['points'][f'k{p["K"]}_L{p["L"]}']
            for mi,name in enumerate(C['methods']):verify(point['methods'][name]['vs_Default3'],pi,mi,pi,0)
            verify(point['TargetBank_vs_DefaultRank1'],pi,2,pi,1)
        seen=set()
        for row in d['all_TargetBank_cross_budget_comparisons']:
            ai=next(i for i,p in enumerate(c['points']) if p['K']==row['K'] and p['L']==row['TargetBank_L']);bi=next(i for i,p in enumerate(c['points']) if p['K']==row['K'] and p['L']==row['control_L']);bm=C['methods'].index(row['control']);assert bm in (0,1)
            assert (ai,bi,bm) not in seen;seen.add((ai,bi,bm));verify(row,ai,2,bi,bm)
        assert len(seen)==36
        for K in (1,100):
            for mi,name in enumerate(C['methods']):
                eligible=[i for i,p in enumerate(c['points']) if p['K']==K and int(allhits[:,i,mi].sum())*100>=90*n*K]
                chosen=d['fastest_measured_R90'][str(K)][name]
                if not eligible:assert chosen is None;continue
                selected=min(eligible,key=lambda i:(math.fsum(times[i,mi]),c['points'][i]['L']))
                assert chosen['L']==c['points'][selected]['L'];close(chosen['qps_pooled'],3*n/math.fsum(times[selected,mi]));close(chosen['recall_pct'],int(allhits[:,selected,mi].sum())*100/(n*K))
        result[ds]={'complete_return_rows':6*3*n,'center_165_parity_rows':center_rows,'all_Default3_E105_fields_equal':True,'all_frozen_slots_entries_NDC_consistent':True,'all_36_cross_budget_comparisons_checked':True,'R90_selection_checked':True,'integer_weight_bootstrap_checked':True,'same_L_K_prefix_checked':True}
    with (R/'reviews/independent_audit.json').open('x') as f:json.dump({'status':'PASS','datasets':result,'complete_return_rows':total,'max_bootstrap_error_pp':maxerr,'all_sources_inputs_models_unchanged':True,'independence_scope':'same agent, separate scoring and integer weighted resampling; original verified GT provenance and frozen graph validation reused','seconds':time.perf_counter()-start},f,ensure_ascii=False,indent=2);f.write('\n')
    print('INDEPENDENT_CURVE_AUDIT_PASS',total,maxerr,flush=True)
if __name__=='__main__':main()
