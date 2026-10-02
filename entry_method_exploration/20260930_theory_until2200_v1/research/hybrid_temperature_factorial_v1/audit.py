"""Run after all timed jobs; independent target substitution and score checks."""
import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='8'
os.sched_setaffinity(0,set(range(8)))
import hashlib
import json
import time
from pathlib import Path
import numpy as np

R=Path(__file__).resolve().parent
C=json.loads((R/'config.locked.json').read_text())

def ident(p):
    p=Path(p);return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}

def dump(p,x):
    with Path(p).open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')

def independent_profile(c,name):
    d=c['dimension'];n=c['n']
    base=np.memmap(c['base'],'<f4',mode='r').reshape(c['base_n'],d+1)[:,1:]
    def unit32(x):return x/np.maximum(np.sqrt(np.sum(x*x,axis=1,keepdims=True)),1e-12)
    ids=np.fromfile(c['hub_ids'],'<i4');h=unit32(np.array(base[ids],dtype='f4'))
    q=unit32(np.fromfile(c['queries'],'<f4').reshape(n,d)).astype('f8')
    rows=np.fromfile(c['selected_rows'],'<i4');gt=np.fromfile(c['selected_gt'],'<i8').reshape(2048,100)
    target=np.fromfile(c['approx_ids'],'<i4').reshape(n,100).copy()
    if name.startswith('Hybrid'):target[rows]=gt
    temp=c['old_temperature']
    if name.endswith('PilotTemperature'):
        z=unit32(np.array(base[gt[:,0]],dtype='f4'))
        scores=np.sort(z@h.T,axis=1)
        temp=max(float(np.median((scores[:,-1]-scores[:,-2]).astype('f8'))),1e-4)
    # Aggregate each rank separately, with target IDs replaced before assignment.
    # The production builder instead substitutes rows in a completed weight table.
    v=h.astype('f8')
    for rank in range(10):
        z=unit32(np.array(base[target[:,rank]],dtype='f4'))
        for lo in range(0,n,4096):
            hi=min(lo+4096,n);s=z[lo:hi]@h.T
            if temp is None:
                w=np.zeros((hi-lo,len(h)));w[np.arange(hi-lo),s.argmax(1)]=.1
            else:
                s=s.astype('f8');s-=s.max(1,keepdims=True);w=np.exp(s/temp);w/=w.sum(1,keepdims=True);w/=10
            v+=w.T@q[lo:hi]
    return (v/np.sqrt(np.sum(v*v,axis=1,keepdims=True))).astype('f4'),temp

def discrete_bootstrap_interval(values,K):
    n=len(values);low=int(values.min());high=int(values.max())
    probabilities=np.bincount(values.astype(int)-low,minlength=high-low+1)/n
    length=1
    while length<n*(high-low)+1:length*=2
    distribution=np.fft.irfft(np.fft.rfft(probabilities,n=length)**n,n=length)
    assert distribution.min()>-1e-10
    distribution=np.maximum(distribution,0);distribution/=distribution.sum()
    quantiles=np.searchsorted(np.cumsum(distribution),[.025,.975])
    return (quantiles+n*low)/(n*K)*100

def main():
    start=time.perf_counter();summary=json.loads((R/'results/summary.json').read_text());records={}
    assert json.loads((R/'reviews/jobs_complete.json').read_text())['status']=='PASS'
    for ds,dc in C['datasets'].items():
        ec=dc['evaluate'];c=dc['profiles'];d=ec['dimension'];n=ec['n']
        model_errors={}
        for name in dc['new_methods']:
            expected,temp=independent_profile(c,name)
            actual=np.fromfile(R/'models'/ds/name/'W.f32','<f4').reshape(-1,d)
            error=float(np.max(np.abs(expected-actual)))
            np.testing.assert_allclose(expected,actual,rtol=1e-5,atol=3e-8)
            model_errors[name]={'max_absolute_profile_error':error,'independently_estimated_temperature':temp}
        gt=np.fromfile(ec['gt'],'<i4').reshape(n,100)
        q=np.fromfile(ec['queries'],'<f4').reshape(n,d)
        base=np.memmap(ec['base'],'<f4',mode='r').reshape(ec['base_n'],d+1)[:,1:]
        arrays=np.load(R/'results'/(ds+'.aligned.npz'))
        count=0;intervals=[];max_distance_error=0
        for point in summary['datasets'][ds]['points']:
            K,L=point['K'],point['L'];hits={};native={}
            for m in ec['methods']:
                name=m['name'];p=R/'results'/ds/'evaluation'/f'k{K}'/f'{name}_L{L}'
                ids=np.fromfile(p/'ids.i32','<i4').reshape(n,K)
                dist=np.fromfile(p/'distances.f32','<f4').reshape(n,K)
                entries=np.fromfile(p/'entry_ids.i32','<i4').reshape(n,3)
                graph_ndc=np.fromfile(p/'graph_ndc.u64','<u8')
                assert np.all(np.diff(entries,axis=1)>0),'all real entries are sorted by ID'
                native[name]={'ids':ids,'dist':dist,'entries':entries,'graph_ndc':graph_ndc}
                if K==1:hh=(ids[:,0]==gt[:,0]).astype('i2')
                else:
                    sorted_gt=np.sort(gt,axis=1)
                    hh=np.array([np.isin(row,truth,assume_unique=True).sum() for row,truth in zip(ids,sorted_gt)],dtype='i2')
                np.testing.assert_array_equal(hh,arrays[f'K{K}_{name}_hits']);hits[name]=hh;count+=n
                metric=next(s for s in point['methods'] if s['method']==name)
                assert abs(metric['recall']-float(hh.sum()/(n*K)))<1e-14
                job=json.loads((R/'reviews'/(ds+'_evaluate.job.json')).read_text())
                assert job['max_threads']==1 and job['affinity_thread_samples']>0
                if name in [ec['methods'][0]['name'],'ApproxTarget10']:
                    old=Path(ec['baseline_reference'])/f'k{K}'/f'{name}_L{L}'
                    for filename in ['ids.i32','distances.f32','entry_ids.i32','graph_ndc.u64','route_ndc.u64']:
                        assert (old/filename).read_bytes()==(p/filename).read_bytes(),(name,filename)
                # Ground-truth scoring is independent of native distance storage;
                # verify the latter against float64 dot products at fixed rows.
                for row in np.linspace(0,n-1,8,dtype=int):
                    exact=-np.asarray(base[ids[row]],dtype='f8')@q[row].astype('f8')
                    err=float(np.max(np.abs(exact-dist[row])))
                    max_distance_error=max(max_distance_error,err)
                    np.testing.assert_allclose(exact,dist[row],rtol=3e-5,atol=3e-5)
            for item in point['comparisons']:
                name,ref=item['method'],item['reference'];delta=hits[name]-hits[ref]
                changed=np.any(native[name]['entries']!=native[ref]['entries'],axis=1)
                for key in ['ids','dist','graph_ndc']:
                    assert native[name][key][~changed].tobytes()==native[ref][key][~changed].tobytes(),(name,ref,key,'same entries imply same graph search')
                assert item['entry_set_changes']==item['entry_order_changes']==int(changed.sum())
                assert abs(item['delta_recall_pp']-float(delta.sum()/(n*K)*100))<1e-13
                assert item['rescue_members']==int(np.maximum(delta,0).sum())
                assert item['damage_members']==int(np.maximum(-delta,0).sum())
                exact_ci=discrete_bootstrap_interval(delta,K)
                monte_carlo=np.array(item['descriptive_95_interval_pp'])
                sd=float(np.std(delta/K)/np.sqrt(n)*100)
                tolerance=max(4*100/(n*K),.15*sd)
                assert np.max(np.abs(exact_ci-monte_carlo))<=tolerance,(name,ref,exact_ci,monte_carlo)
                samples=arrays[f'K{K}_{name}_vs_{ref}_bootstrap']
                assert abs(float(samples.mean())-float(delta.mean()/K))<=max(1e-14,6*np.std(delta/K)/np.sqrt(n*len(samples)))
                intervals.append({'K':K,'method':name,'reference':ref,'exact_discrete_95_pp':exact_ci.tolist(),
                                  'bootstrap_95_pp':monte_carlo.tolist()})
        records[ds]={'candidate_profiles':model_errors,'returned_vectors_rescored':count,
                     'float64_distance_max_absolute_error':max_distance_error,'interval_checks':intervals}
        print(ds,{'profiles':model_errors,'returned_vectors':count,'interval_checks':len(intervals)},flush=True)
    identities=0
    for freeze in ['prepare_inputs.json','run_frozen.json','models_frozen_before_evaluation.json']:
        for path,value in json.loads((R/'reviews'/freeze).read_text())['files'].items():
            assert ident(path)==value,path;identities+=1
    dump(R/'reviews/independent_audit.json',{'status':'PASS','datasets':records,'seconds':time.perf_counter()-start,
        'identities_checked':identities,'source':ident(Path(__file__)),'new_GT':0,'new_searches':0,
        'scope':'same agent, separate target-ID substitution aggregation, scoring and exact bootstrap distribution'})
    print('PASS',round(time.perf_counter()-start,3),flush=True)

if __name__=='__main__':main()
