import argparse
import numpy as np
from common import RUN,E25,DATASETS,LS,read,dump,check_lock,frozen_check,update_state
from jobs import run_job
from verify_outputs import verify_folder


def run(stage):
    check_lock();frozen_check('cal')
    assert read(RUN/'reviews/synthetic_gate.json')['status']=='PASS'
    if stage!='recovery':assert read(RUN/'reviews/recovery_gate.json')['status']=='PASS'
    if stage=='audit':frozen_check('audit')
    checks=[]
    for order,ds in enumerate(DATASETS):
        c=read(RUN/'inputs'/ds/stage/'config.json');profiles=read(RUN/'models'/ds/'profiles.json')
        names=['fast20k','e24'] if stage=='recovery' else ['fast20k','e24','alpha025','alpha050','alpha075']
        c.update(timing_repeats=0,dataset_order=order,methods=[])
        for L in LS if stage=='recovery' else [64,128]:
            for name in names:c['methods'].append({**profiles[name],'name':f'{name}_L{L}','L':L,'component_wall':False})
        out=RUN/'diagnostics'/ds/stage;r=run_job(f'{stage}_{ds}',c,out);v=verify_folder(out)
        if stage=='recovery':
            old=E25/'diagnostics'/ds/'recovery'
            for kind in names:
                for L in LS:
                    for file,dtype in [('ids.i32','<i4'),('distances.f32','<u4'),('entry_ids.i32','<i4'),('hits.u8','u1'),('hitmask.u16','<u2'),('route_ndc.u32','<u4'),('graph_ndc.u32','<u4')]:
                        assert np.array_equal(np.fromfile(out/f'{kind}_L{L}'/file,dtype=dtype),np.fromfile(old/f'{kind}_L{L}'/file,dtype=dtype)),(ds,kind,L,file)
            v['five_L_endpoint_E25_original_bit_regression']='PASS'
        checks.append({'dataset':ds,**v})
    dump(RUN/'reviews'/('recovery_gate.json' if stage=='recovery' else f'{stage}_verification.json'),{'status':'PASS','datasets':checks})
    update_state(status=stage.upper()+'_COMPLETE',active_job=None)
    print(stage.upper()+'_ALL_PASS',flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('stage',choices=['recovery','cal','audit']);run(ap.parse_args().stage)
