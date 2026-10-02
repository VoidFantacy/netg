import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[key]='8'
os.environ['OMP_DYNAMIC']='FALSE';os.environ['OMP_MAX_ACTIVE_LEVELS']='1';os.sched_setaffinity(0,set(range(8)))
import ast,hashlib,json,time,platform,resource
from pathlib import Path
import numpy as np,faiss
faiss.omp_set_num_threads(8)
R=Path(__file__).resolve().parents[1];P=R.parent.parent;ROOT=P.parents[1];E=P/'stages/e124_semantic_service_ridge_v1';C=json.loads((E/'config.locked.json').read_text());source=ROOT/'benches/run/build_fast_entry_variants.py';inputs={}
def ident(p):return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def read(p):inputs[str(p)]=ident(p);return json.loads(p.read_text())
def vectors(p,typ):
    inputs[str(p)]=ident(p);z=np.fromfile(p,typ);d=int(z[:1].view('<i4')[0]);v=z.reshape(-1,d+1);assert (v[:,0].view('<i4')==d).all();return np.ascontiguousarray(v[:,1:])
def dump(p,v):assert not p.exists(),p;p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
dump(R/'reviews/preflight_frozen.json',{'files':{str(p):ident(p) for p in [R/'protocol.md',Path(__file__),source,E/'config.locked.json']}})
nodes=[n for n in ast.parse(source.read_text()).body if isinstance(n,ast.FunctionDef) and n.name in ['normalize','choose_unique_gt_hubs']];assert len(nodes)==2
scope={'np':np,'faiss':faiss};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(source),'exec'),scope)
results={};started=time.perf_counter()
for ds,dc in C['datasets'].items():
    mp=ROOT/'fast_entry_variants'/(ds+'_seed20260828')/'manifest.json';m=read(mp);ss=m['sources'];qp=ROOT/ss['aco_queries'];gp=ROOT/ss['aco_gt'];q=vectors(qp,'<f4');gt=vectors(gp,'<i4');assert q.shape==(5000,dc['dimension']) and gt.shape==(5000,100)
    assert inputs[str(qp)]['sha256']==ss['aco_queries_sha256'] and inputs[str(gp)]['sha256']==ss['aco_gt_sha256']
    ip=Path(dc['anchor']['ids']);inputs[str(ip)]=ident(ip);ref=np.fromfile(ip,'<i4');start=time.perf_counter();ids,details=scope['choose_unique_gt_hubs'](q,gt,len(ref),20260828,25);duration=time.perf_counter()-start
    match=np.array_equal(ids,ref);results[ds]={'exact_current_H_match':bool(match),'selected_H':len(ids),'different_positions':int((ids!=ref).sum()),'seconds':duration,'details':details,'qgt_queries':str(qp),'qgt_GT':str(gp),'source_manifest':str(mp)}
    print(ds,results[ds],flush=True)
    if not match:break
passed=len(results)==2 and all(v['exact_current_H_match'] for v in results.values())
for p,v in inputs.items():assert ident(Path(p))==v
dump(R/'reviews/preflight_inputs.json',inputs)
dump(R/'reviews/preflight.json',{'status':'PASS' if passed else 'STOP_REBUILD_H_NOT_IDENTICAL','datasets':results,'seconds':time.perf_counter()-started,'faiss_version':faiss.__version__,'numpy_version':np.__version__,'python':platform.python_version(),'faiss_threads':faiss.omp_get_max_threads(),'affinity':sorted(os.sched_getaffinity(0)),'maxrss_GiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20,'new_qgt_fits':len(results),'new_GT_queries':0})
print('PASS' if passed else 'STOP_REBUILD_H_NOT_IDENTICAL',flush=True)
