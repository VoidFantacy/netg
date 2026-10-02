"""Independent profile construction, cal selection and immutable asset checks."""
import time
from pathlib import Path
import numpy as np
from common import RUN,DATASETS,NAMES,ALPHAS,LS,read,dump,identity,sha,check_lock,frozen_check
from select_alpha import load_stage


def main():
    start=time.monotonic();lock=check_lock();precal=frozen_check('cal');selected=frozen_check('audit')
    assert read(RUN/'reviews/validation_verification.json')['status']=='PASS'
    jobs=read(RUN/'reviews/search_jobs.json')
    assert len(jobs)==8 and all(j['status']=='COMPLETE' and j['max_observed_process_threads']==1 for j in jobs)
    assert sum(j['actual_calls'] for j in jobs)==897280==lock['normal_real_call_cap']
    assert not any(j['repair'] for j in jobs)
    assert sum(j['process_seconds'] for j in jobs)<lock['total_search_seconds']
    assert min(j['start_unix'] for j in jobs if j['name'].startswith('cal_'))>precal['frozen_unix']
    assert min(j['start_unix'] for j in jobs if j['name'].startswith('audit_'))>selected['frozen_unix']
    assert min(j['start_unix'] for j in jobs if j['name'].startswith('validation_'))>(RUN/'reviews/audit_report.json').stat().st_mtime
    upstream=[]
    for before in read(RUN/'reviews/protected_before.json'):
        after=identity(before['path']);assert after==before,before['path'];upstream.append(after)
    profile_checks=[];selection_checks=[];graphs=[]
    for ds in DATASETS:
        profiles=read(RUN/'models'/ds/'profiles.json');p0=profiles['fast20k'];p1=profiles['e24']
        h=p0['hub_count'];d=p0['dim'];w0=np.fromfile(p0['W'],dtype='<f4').reshape(h,d);w1=np.fromfile(p1['W'],dtype='<f4').reshape(h,d)
        original=read(RUN/'inputs'/ds/'endpoints.json')
        assert sha(p0['W'])==sha(original['A0']['W']) and sha(p1['W'])==sha(original['A1']['W'])
        for name,alpha in zip(NAMES,ALPHAS):
            w=np.fromfile(profiles[name]['W'],dtype='<f4').reshape(h,d)
            reference=np.empty((h,d),dtype='float64')
            for j in range(h):
                v=(1-alpha)*w0[j].astype('float64')+alpha*w1[j].astype('float64')
                reference[j]=v/np.sqrt(np.dot(v,v))
            error=float(np.max(np.abs(w-reference)))
            assert error<6e-8 and np.max(np.abs(np.linalg.norm(w.astype('float64'),axis=1)-1))<1e-6
            profile_checks.append({'dataset':ds,'name':name,'alpha':alpha,'independent_scalar_reference_max_error':error,'status':'PASS'})
        _,hits,entries=load_stage(ds,'cal');d1=hits['e24']-hits['fast20k'];good=d1>0;bad=d1<0
        table=read(RUN/'models'/ds/'selection.json');candidates=[]
        assert [c['alpha'] for c in table['candidates']]==ALPHAS
        for c in table['candidates']:
            da=hits[c['name']]-hits['fast20k']
            R=np.sum(good & (da>0))/np.sum(good)
            Rh=np.minimum(np.maximum(da,0),np.maximum(d1,0)).sum()/np.maximum(d1,0).sum()
            A=1-np.sum(da<0)/np.sum(bad);Ah=1-np.maximum(-da,0).sum()/np.maximum(-d1,0).sum()
            s={'R':float(R),'Rh':float(Rh),'A_all':float(A),'Ah_all':float(Ah),
               'S':float(min(R/.75,Rh/.75,A/.25,Ah/.25)),'net_delta_hits':int(da.sum()),
               'total_negative_events':int((da<0).sum()),'total_negative_hits':int(np.maximum(-da,0).sum()),
               'target_met':bool(R>=.75 and Rh>=.75 and A>=.25 and Ah>=.25 and da.sum()>=max(0,d1.sum()))}
            for k,v in s.items():assert abs(float(c['pooled'][k])-float(v))<1e-12,(ds,c['name'],k)
            changed=int((entries[c['name']]!=entries['fast20k']).any(axis=1).sum())
            assert changed==c['entry_changes_vs_A0'];candidates.append({'name':c['name'],'alpha':c['alpha'],'changes':changed,**s})
        feasible=[c for c in candidates if c['target_met']]
        def key(c):
            tail=(-c['net_delta_hits'],c['total_negative_events'],c['total_negative_hits'],c['changes'],c['alpha'])
            return tail if feasible else (-c['S'],*tail)
        winner=sorted(feasible or candidates,key=key)[0]
        assert winner['name']==table['selected'] and winner['alpha']==table['alpha']
        assert table['status']==('CAL_TARGET_MET' if feasible else 'CAL_TARGET_NOT_MET')
        selection_checks.append({'dataset':ds,'alpha':winner['alpha'],'status':'PASS','all_candidate_ratios_raw_hits_and_ties_recomputed':True})
        for name in ['fast20k','e24',*NAMES]:
            paths=[RUN/'diagnostics'/ds/stage/f'{name}_L{L}.hnsw' for stage in ['cal','audit'] for L in [64,128]]
            val_name='shrink' if name==winner['name'] else name
            if val_name in ['fast20k','e24','shrink']:
                paths.extend([RUN/'results'/ds/f'{val_name}_L{L}.hnsw' for L in LS])
            hashes=[sha(p) for p in paths];assert len(set(hashes))==1,(ds,name)
            graphs.append({'dataset':ds,'name':name,'files':len(paths),'sha256':hashes[0],'same_across_L_and_stages':True})
        paths=[RUN/'results'/ds/f'fast30k_L{L}.hnsw' for L in LS];assert len({sha(p) for p in paths})==1
    for stage in ['cal','audit','validation']:assert read(RUN/'reviews'/f'{stage}_entry_transitions.json')['status']=='PASS'
    dump(RUN/'reviews/immutable_integrity.json',{'status':'PASS','seconds':time.monotonic()-start,
        'protected_upstream':upstream,'precal_frozen_files':len(precal['files']),'preaudit_frozen_files':len(selected['files']),
        'profile_checks':profile_checks,'selection_checks':selection_checks,'micro_graph_checks':graphs,
        'normal_real_calls':897280,'repair_calls':0,'heldout_opened':False,
        'chronology':'new profiles before cal; cal choices before audit; validation after audit report'})
    print('E26_IMMUTABLE_AND_SELECTION_AUDIT_PASS',len(upstream),flush=True)


if __name__=='__main__':main()
