import copy
import os
import subprocess
import numpy as np
from common import E23, RUN, check_lock, dump, read
from jobs import run_job

lock=check_lock()
source=read(E23/'reviews/synthetic_inputs/evaluate.json')
config=copy.deepcopy(source);config['split']='synthetic';config['query_cpu']=lock['query_cpu']
for m in config['methods']:
    m['component_wall']=m['L']==128
result=run_job('synthetic_evaluate',config,RUN/'reviews/synthetic_evaluate',synthetic=True)
base=next(x for x in source['methods'] if x['family']=='test_exact')
n,d=source['num_queries'],source['dim'];hubs=np.fromfile(base['mapping'],dtype='<i4')
q=np.fromfile(source['queries_file'],dtype='<f4').reshape(n,d)
p=np.fromfile(base['W'],dtype='<f4').reshape(len(hubs),d)
order=np.argsort(hubs,kind='stable')
expected=np.sort(hubs[order[np.argsort(-(q@p.T)[:,order],axis=1,kind='stable')[:,:3]]],axis=1)
gt=np.fromfile(source['gt_file'],dtype='<i8').reshape(n,source['gt_k'])[:,:10]
for m in result['methods']:
    path=RUN/'reviews/synthetic_evaluate'/m['name']
    ids=np.fromfile(path/'ids.i32',dtype='<i4').reshape(n,10)
    hits=np.array([len(set(ids[i])&set(gt[i])) for i in range(n)],dtype='u1')
    assert np.array_equal(hits,np.fromfile(path/'hits.u8',dtype='u1'))
    if m['family']=='test_exact':
        assert np.array_equal(expected,np.fromfile(path/'entry_ids.i32',dtype='<i4').reshape(n,3))
bad=copy.deepcopy(config);bad['threads']=2
dump(RUN/'reviews/invalid_threads.json',bad)
env={**os.environ,'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1'}
denied=subprocess.run(['taskset','-c',str(lock['query_cpu']),str(RUN/'bin/evaluate'),
    str(RUN/'reviews/invalid_threads.json'),str(RUN/'reviews/invalid_threads_must_not_exist')],env=env,capture_output=True,text=True)
assert denied.returncode!=0 and not (RUN/'reviews/invalid_threads_must_not_exist').exists()
dump(RUN/'reviews/synthetic_gate.json',{'status':'PASS','five_L':True,'exact_top3_independent_sort':True,
    'all_output_GT_rescoring':True,'component_timing_output_parity':True,'multithread_config_rejected':True,
    'fixture':'E23 synthetic fixture only, no real samples','physical_synthetic_calls':result['physical_graph_calls']})
print('SYNTHETIC_GATE_PASS',flush=True)
