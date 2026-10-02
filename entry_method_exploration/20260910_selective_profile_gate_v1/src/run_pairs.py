import argparse
import numpy as np
from common import RUN,E24,DATASETS,LS,read,dump,check_lock,frozen_gate_check,update_state
from jobs import run_job
from verify_outputs import verify_folder

def run(stage):
    check_lock();assert read(RUN/'reviews/synthetic_gate.json')['status']=='PASS'
    if stage!='recovery':assert read(RUN/'reviews/recovery_gate.json')['status']=='PASS'
    if stage=='cal':assert all((RUN/'diagnostics'/ds/'fit/independent_verification.json').exists() for ds in DATASETS)
    if stage=='audit':frozen_gate_check()
    checks=[]
    for order,ds in enumerate(DATASETS):
        c=read(RUN/'inputs'/ds/stage/'config.json');c.update(timing_repeats=0,export_features=True,
             policies=read(RUN/'inputs'/ds/'policies.json'),dataset_order=order,methods=[])
        for L in (LS if stage=='recovery' else [64,128]):
            for kind in ['fast20k','e24']:c['methods'].append({'name':f'{kind}_L{L}','family':kind,'kind':kind,'L':L})
            if stage=='recovery':
                for name,force in [('force_base',0),('force_new',1)]:c['methods'].append({'name':f'{name}_L{L}','family':name,'kind':'dual_gate','force':force,'L':L})
        out=RUN/'diagnostics'/ds/stage;r=run_job(f'{stage}_{ds}',c,out);v=verify_folder(out)
        if stage=='recovery':
            original=E24/'diagnostics'/ds/'cal';old=read(original/'results.json');n=32
            names={'fast20k':'gt1_hard','e24':c['policies']['primary_E24']}
            for kind,model in names.items():
                m=next(x for x in old['methods'] if x['configuration'].get('model_name')==model and not x['configuration'].get('exact',False))
                for filename,dtype,width in [('ids.i32','<i4',10),('distances.f32','<u4',10),('entry_ids.i32','<i4',3),
                                             ('route_ndc.u32','<u4',1),('graph_ndc.u32','<u4',1),('hits.u8','u1',1),('hitmask.u16','<u2',1)]:
                    a=np.fromfile(out/f'{kind}_L128'/filename,dtype=dtype)
                    b=np.fromfile(original/m['name']/filename,dtype=dtype)[:n*width]
                    assert np.array_equal(a,b),(ds,kind,filename)
            v['E24_original_cal_first32_L128_bits_and_NDC']='PASS'
        checks.append({'dataset':ds,**v})
    if stage=='recovery':dump(RUN/'reviews/recovery_gate.json',{'status':'PASS','datasets':checks,'physical_calls':3200})
    else:dump(RUN/'reviews'/f'{stage}_pairs_verification.json',{'status':'PASS','datasets':checks})
    update_state(status=stage.upper()+'_PAIRS_COMPLETE',active_job=None)
    print(stage.upper()+'_ALL_PASS',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['recovery','fit','cal','audit']);run(p.parse_args().stage)
