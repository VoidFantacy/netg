import copy
import os
import shutil
import subprocess
import numpy as np
from common import RUN,E25,ALPHAS,NAMES,LS,read,dump,identity,check_lock,frozen_check
from build_profiles import mix
from effect_stats import selftest
from jobs import run_job
from verify_outputs import verify_folder


def main():
    lock=check_lock();frozen_check('cal')
    dump(RUN/'reviews/effect_accounting_selftest.json',selftest())
    old=read(E25/'reviews/synthetic_evaluate/config.json')
    inp=RUN/'reviews/synthetic_inputs';inp.mkdir(exist_ok=False)
    c={k:old[k] for k in ['dataset','split','dim','num_queries','gt_k','index_path']}
    sources=[]
    for key,name in [('queries_file','queries.f32'),('gt_file','gt.i64'),('row_ids','row_ids.i64')]:
        sources.append(identity(old[key]));shutil.copy2(old[key],inp/name);c[key]=str(inp/name)
    q=np.fromfile(c['queries_file'],dtype='<f4').reshape(c['num_queries'],c['dim']);assert not np.any(q[-1])
    p0=old['policies']['A0'];p1=old['policies']['A1']
    w0=np.fromfile(p0['W'],dtype='<f4').reshape(p0['hub_count'],c['dim']);w1=np.fromfile(p1['W'],dtype='<f4').reshape(w0.shape)
    profiles={'nsg':{'family':'nsg','model_name':'nsg','seed':20260828,'dim':c['dim'],'k':1}}
    for name,alpha in [('fast20k',0.),*zip(NAMES,ALPHAS),('e24',1.)]:
        w=mix(w0,w1,alpha);path=inp/f'{name}_W.f32';w.tofile(path)
        profiles[name]={**p0,'name':name,'model_name':name,'family':name,'W':str(path),'alpha':alpha}
    c.update(timing_repeats=0,dataset_order=0,methods=[])
    for L in LS:
        for name,p in profiles.items():c['methods'].append({**p,'name':f'{name}_L{L}','L':L,'component_wall':False})
    out=RUN/'reviews/synthetic_diagnostic';result=run_job('synthetic_diagnostic',c,out,synthetic=True);v=verify_folder(out)
    for kind in ['fast20k','e24']:
        for L in LS:
            for name,dtype in [('ids.i32','<i4'),('distances.f32','<u4'),('entry_ids.i32','<i4'),('hits.u8','u1'),('hitmask.u16','<u2'),('route_ndc.u32','<u4'),('graph_ndc.u32','<u4')]:
                assert np.array_equal(np.fromfile(out/f'{kind}_L{L}'/name,dtype=dtype),
                    np.fromfile(E25/'reviews/synthetic_evaluate'/f'{kind}_L{L}'/name,dtype=dtype)),(kind,L,name)
    measured=copy.deepcopy(c);measured['timing_repeats']=3
    measured['methods']=[{**m,'component_wall':True} for m in c['methods'] if m['L']==128 and m['family'] in ['nsg','fast20k','alpha050']]
    wall_out=RUN/'reviews/synthetic_wall';wall=run_job('synthetic_wall',measured,wall_out,synthetic=True);v2=verify_folder(wall_out)
    invalid=copy.deepcopy(c);invalid['threads']=2;dump(inp/'invalid_threads.json',invalid)
    env={**os.environ,'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1'}
    failed=subprocess.run(['taskset','-c',str(lock['query_cpu']),str(RUN/'bin/evaluate'),str(inp/'invalid_threads.json'),str(inp/'must_not_exist')],env=env,capture_output=True,text=True)
    assert failed.returncode and not (inp/'must_not_exist').exists()
    calls=result['physical_graph_calls']+wall['physical_graph_calls'];assert calls==2268
    dump(RUN/'reviews/synthetic_gate.json',{'status':'PASS','calls':calls,'diagnostic':v,'wall_components':v2,
        'five_L':True,'three_wall_repeats':True,'all_three_alpha_profiles':True,'original_endpoints_E25_bit_regression':True,
        'zero_query':True,'invalid_threads_rejected_before_search':True,'input_sources':sources})
    frozen_check('cal')
    print('E26_SYNTHETIC_ALL_PASS',calls,flush=True)


if __name__=='__main__':main()
