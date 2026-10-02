"""Independent selection/provenance audit after all performance measurements finish."""
import time
from pathlib import Path
import numpy as np
from common import RUN, DATASETS, LS, read, dump, identity, sha, check_lock, frozen_gate_check
from gate_stats import load_pair


def decision(x, model):
    standardized=np.clip((x[:,:len(model['beta'])]-model['mean'])/model['scale'],-6,6)
    z=np.full(len(x),model['bias'],dtype='float64')
    for j,b in enumerate(model['beta']):z=z+standardized[:,j]*b
    return z,z>=model['threshold']


def stats(h0,h1,c):
    d=h1-h0;selected=d*c[:,None]
    positive=d>0;negative=d<0
    R=int((positive & c[:,None]).sum())/int(positive.sum())
    A=int((negative & ~c[:,None]).sum())/int(negative.sum())
    Rh=int(np.maximum(selected,0).sum())/int(np.maximum(d,0).sum())
    Ah=1-int(np.maximum(-selected,0).sum())/int(np.maximum(-d,0).sum())
    return {'R':R,'A':A,'Rh':Rh,'Ah':Ah,'S':min(R/.75,A/.25,Rh/.75,Ah/.25),
            'net_delta_hits':int(selected.sum()),'negative_events_retained':int((selected<0).sum()),
            'switch_queries':int(c.sum()),'nonconstant_on_this_split':bool(c.any() and (~c).any()),
            'target_met':bool(R>=.75 and A>=.25 and Rh>=.75 and Ah>=.25 and selected.sum()>=max(0,d.sum()))}


def main():
    started=time.monotonic();lock=check_lock();frozen=frozen_gate_check()
    assert read(RUN/'reviews/validation_verification.json')['status']=='PASS'
    jobs=read(RUN/'reviews/search_jobs.json')
    assert len(jobs)==10 and all(j['status']=='COMPLETE' and j['exit_code']==0 for j in jobs)
    assert sum(j['actual_calls'] for j in jobs)==lock['normal_real_call_cap']==1089152
    assert not any(j['repair'] for j in jobs)
    assert sum(j['process_seconds'] for j in jobs)<=lock['total_search_seconds']
    assert all(j['max_observed_process_threads']==1 for j in jobs)
    assert min(j['start_unix'] for j in jobs if j['name'].startswith('audit_'))>frozen['frozen_unix']
    assert min(j['start_unix'] for j in jobs if j['name'].startswith('validation_'))>(RUN/'reviews/audit_report.json').stat().st_mtime
    upstream=[]
    for before in read(RUN/'reviews/protected_before.json'):
        after=identity(before['path'])
        assert after==before,before['path']
        upstream.append(after)
    selection_checks=[];graph_checks=[]
    selections=read(RUN/'models/selections.json')
    for ds in DATASETS:
        _,xf,bf,af=load_pair(ds,'fit');_,xc,bc,ac=load_pair(ds,'cal')
        by_kind={}
        for kind,width in [('base_gate',7),('dual_gate',13)]:
            table=read(RUN/'models'/ds/f'{kind}_candidates.json')
            assert len(table['candidates'])==15 and len(table['fits'])==3
            assert [f['model_at_threshold_zero']['lambda'] for f in table['fits']]==[.01,.1,1.]
            recomputed=[]
            for candidate in table['candidates']:
                m=candidate['model'];zf,cf=decision(xf,m);_,cc=decision(xc,m)
                assert np.array_equal(m['mean'],xf[:,:width].mean(axis=0))
                assert np.array_equal(m['scale'],np.maximum(xf[:,:width].std(axis=0),1e-6))
                thresholds=[0.]+np.quantile(zf,[.10,.25,.50,.75],method='linear').tolist()
                assert m['threshold']==thresholds[candidate['threshold_index']]
                s=stats(bc,ac,cc)
                for k,v in s.items():
                    expected=candidate['cal'][k]
                    assert abs(float(v)-float(expected))<1e-12,(ds,kind,candidate['name'],k)
                recomputed.append({**candidate,'cal_independent':s})
            for fit in table['fits']:
                model=fit['model_at_threshold_zero']
                assert model['status']=='CONVERGED' and fit['optimization_trace'][-1]['gradient_inf']<=1e-8
                z,_=decision(xf,model);d=af-bf;P=np.maximum(d,0).sum(axis=1);N=np.maximum(-d,0).sum(axis=1)
                objective=(P*np.logaddexp(0,-z)+N*np.logaddexp(0,z)).sum()/(P+N).sum()+.5*model['lambda']*np.dot(model['beta'],model['beta'])
                assert abs(objective-fit['optimization_trace'][-1]['loss'])<1e-12
            eligible=[r for r in recomputed if r['cal_independent']['nonconstant_on_this_split']]
            feasible=[r for r in eligible if r['cal_independent']['target_met']]
            pool=feasible or eligible or recomputed
            def sort_key(r):
                s=r['cal_independent']
                tail=(-s['net_delta_hits'],s['negative_events_retained'],s['switch_queries'],-r['model']['lambda'],r['threshold_index'])
                return tail if feasible else (-s['S'],*tail)
            chosen=sorted(pool,key=sort_key)[0]
            assert chosen['name']==table['selected']==selections[ds]['gates'][kind]['candidate']
            deployed=read(RUN/'models'/ds/f'{kind}.json')
            assert all(deployed[k]==v for k,v in chosen['model'].items())
            by_kind[kind]=chosen['cal_independent']
            selection_checks.append({'dataset':ds,'kind':kind,'candidate':chosen['name'],
                'cal_predicted_from_raw_features':True,'ratios_and_tie_order_independently_recomputed':True,
                'fit_objective_and_locked_thresholds_verified':True,'optimized_models':3,'candidates':15})
        primary=sorted(by_kind,key=lambda k:(-int(by_kind[k]['target_met']),-by_kind[k]['S'],
            -by_kind[k]['net_delta_hits'],by_kind[k]['negative_events_retained'],int(k!='base_gate')))[0]
        assert primary==selections[ds]['primary']
        folder=RUN/'results'/ds
        for role,suffixes in [('base',['fast20k.base','base_gate.base','dual_gate.base']),
                              ('new',['e24.new','base_gate.new','dual_gate.new']),('fast30k',['fast30k.direct'])]:
            files=[]
            for suffix in suffixes:
                kind,branch=suffix.split('.')
                files.extend([folder/f'{kind}_L{L}.{branch}.hnsw' for L in LS])
            hashes=[sha(p) for p in files];assert len(set(hashes))==1,(ds,role)
            graph_checks.append({'dataset':ds,'role':role,'files':len(files),'sha256':hashes[0],
                                 'same_binary_micro_graph_across_L_and_consumers':True})
    dump(RUN/'reviews/immutable_integrity.json',{'status':'PASS','seconds':time.monotonic()-started,
        'protected_upstream':upstream,'frozen_files_checked':len(frozen['files']),
        'selection_checks':selection_checks,'micro_graph_checks':graph_checks,
        'real_calls':1089152,'repair_calls':0,'heldout_opened':False,
        'scope':'all bound upstream hashes; frozen inputs/model/source/binary; raw-cal choice and objective; graph identity; chronology'})
    print('IMMUTABLE_AND_INDEPENDENT_SELECTION_PASS',len(upstream),flush=True)


if __name__=='__main__':
    main()
