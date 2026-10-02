import numpy as np
from common import RUN,E25,DATASETS,LS,read,dump,identity,check_lock,frozen_check,update_state
from jobs import run_job
from verify_outputs import verify_folder


def main():
    check_lock();frozen_check('audit')
    assert read(RUN/'reviews/audit_report.json')['status']=='REPORT_ONLY_COMPLETE'
    checks=[]
    for order,ds in enumerate(DATASETS):
        c=read(RUN/'inputs'/ds/'validation/config.json');profiles=read(RUN/'models'/ds/'profiles.json')
        selected=read(RUN/'models'/ds/'selection.json')['selected']
        old_folder=E25/'results'/ds;old=read(old_folder/'results.json')
        direct=next(m['configuration']['direct'] for m in old['methods'] if m['kind']=='fast30k' and m['L']==128)
        direct={**direct,'family':'fast30k','model_name':'fast30k'}
        nsg={'family':'nsg','model_name':'nsg','seed':20260828,'dim':c['dim'],'k':1}
        all_profiles={'nsg':nsg,'fast30k':direct,'fast20k':profiles['fast20k'],'e24':profiles['e24'],
                      'shrink':{**profiles[selected],'family':'shrink'}}
        c.update(timing_repeats=3,dataset_order=order,methods=[])
        for L in LS:
            for name,profile in all_profiles.items():c['methods'].append({**profile,'name':f'{name}_L{L}','L':L,'component_wall':L==128})
        out=RUN/'results'/ds;results=run_job(f'validation_{ds}',c,out);v=verify_folder(out)
        for m in results['methods']:
            if m['family']=='shrink':continue
            original=next(o for o in old['methods'] if o['kind']==m['family'] and o['L']==m['L'])
            for file,dtype in [('ids.i32','<i4'),('distances.f32','<u4'),('entry_ids.i32','<i4'),('hits.u8','u1'),('hitmask.u16','<u2'),('route_ndc.u32','<u4'),('graph_ndc.u32','<u4')]:
                assert np.array_equal(np.fromfile(out/m['name']/file,dtype=dtype),np.fromfile(old_folder/original['name']/file,dtype=dtype)),(ds,m['name'],file)
        for family in all_profiles:
            entries=np.fromfile(out/f'{family}_L64/entry_ids.i32',dtype='<i4')
            for L in LS[1:]:assert np.array_equal(entries,np.fromfile(out/f'{family}_L{L}/entry_ids.i32',dtype='<i4'))
        v.update(dataset=ds,all_five_L_entry_identity='PASS',four_original_curves_E25_bit_regression='PASS',results=identity(out/'results.json'))
        checks.append(v);frozen_check('audit')
    dump(RUN/'reviews/validation_verification.json',{'status':'PASS','points':50,'datasets':checks})
    update_state(status='VALIDATION_COMPLETE_ALL_PARITY_PASS',active_job=None)
    print('VALIDATION_ALL_PASS',flush=True)


if __name__=='__main__':main()
