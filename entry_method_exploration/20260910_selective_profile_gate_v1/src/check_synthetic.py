import copy,os,subprocess
import numpy as np
from common import ROOT,RUN,LS,read,dump,check_lock,identity
from jobs import run_job
from verify_outputs import verify_folder

lock=check_lock();old=read(ROOT/'entry_method_exploration/20260910_three_entry_rank_v1/reviews/synthetic_inputs/evaluate.json')
folder=RUN/'reviews/synthetic_inputs';folder.mkdir(exist_ok=False)
q=np.fromfile(old['queries_file'],dtype='<f4').reshape(old['num_queries'],old['dim']);gt=np.fromfile(old['gt_file'],dtype='<i8').reshape(old['num_queries'],100)
assert np.max(gt)>=99
q[-1]=0;gt[-1]=np.arange(100) # all raw-IP scores are tied for the zero-query fixture
q.tofile(folder/'queries.f32');gt.tofile(folder/'gt.i64')
a0={**old['methods'][0],'dim':old['dim']};w0=np.fromfile(a0['W'],dtype='<f4').reshape(a0['hub_count'],old['dim'])
w1=np.roll(w0,5,axis=0).copy();w1.tofile(folder/'new_W.f32')
a1={**a0,'W':str(folder/'new_W.f32')}
cos=(w0.astype('float64')*w1).sum(1)/(np.linalg.norm(w0.astype('float64'),axis=1)*np.linalg.norm(w1.astype('float64'),axis=1))
hub=np.column_stack([np.log1p(np.arange(len(w0))),np.log1p(np.arange(len(w0))+2),1-np.clip(cos,-1,1)]).astype('<f8');hub.tofile(folder/'hub_features.f64')
models={}
for kind,p in [('base_gate',7),('dual_gate',13)]:
 beta=np.zeros(p);beta[1]=3;beta[2]=-2
 if p==13:beta[7]=2;beta[12]=-.2
 m={'feature_set':kind,'mean':[0.]*p,'scale':[1.]*p,'beta':beta.tolist(),'bias':-1.,'threshold':0.}
 dump(folder/f'{kind}.json',m);models[kind]=str(folder/f'{kind}.json')
config={k:old[k] for k in ['dataset','split','dim','num_queries','gt_k','index_path','row_ids']}
config.update(queries_file=str(folder/'queries.f32'),gt_file=str(folder/'gt.i64'),timing_repeats=3,export_features=True,
              policies={'A0':a0,'A1':a1,'hub_features':str(folder/'hub_features.f64')},methods=[])
for L in LS:
 for name,kind,force in [('fast20k','fast20k',None),('e24','e24',None),('force_base','dual_gate',0),('force_new','dual_gate',1),('base_gate','base_gate',None),('dual_gate','dual_gate',None)]:
  m={'name':f'{name}_L{L}','family':name,'kind':kind,'L':L,'component_wall':L==128}
  if force is not None:m['force']=force
  elif kind in models:m['model_path']=models[kind]
  config['methods'].append(m)
out=RUN/'reviews/synthetic_evaluate';r=run_job('synthetic_evaluate',config,out,synthetic=True);v=verify_folder(out)
# Same-route case is a separate fixture: both frozen profile matrices identical.
same=copy.deepcopy(config);same.update(timing_repeats=0);same['policies']['A1']=same['policies']['A0']
same['methods']=[{**m,'component_wall':False} for m in config['methods'] if m['L']==128 and m['family'] in ['fast20k','e24','force_base','force_new']]
same_out=RUN/'reviews/synthetic_same_routes';r2=run_job('synthetic_same_routes',same,same_out,synthetic=True);v2=verify_folder(same_out)
bad=copy.deepcopy(config);bad['threads']=2;dump(folder/'bad_threads.json',bad)
env={**os.environ,'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1'}
denied=subprocess.run(['taskset','-c',str(lock['query_cpu']),str(RUN/'bin/evaluate'),str(folder/'bad_threads.json'),str(folder/'invalid_must_not_exist')],env=env,capture_output=True,text=True)
assert denied.returncode and not (folder/'invalid_must_not_exist').exists()
dump(RUN/'reviews/synthetic_gate.json',{'status':'PASS','calls':r['physical_graph_calls']+r2['physical_graph_calls'],
     'zero_norm_case':True,'forced_A0_A1':True,'same_entries':True,'five_L':True,'three_timing_repeats':True,
     'decision_feature_and_all_cost_checks':v,'same_route_checks':v2,'multithread_rejected':True,
     'upstream_fixture_files':[identity(old[k]) for k in ['queries_file','gt_file','index_path','row_ids']]})
print('SYNTHETIC_PASS',flush=True)
