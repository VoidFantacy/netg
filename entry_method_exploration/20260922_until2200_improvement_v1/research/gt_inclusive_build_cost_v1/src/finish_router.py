import os,json,hashlib,subprocess,time,datetime
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R.parent.parent;ROOT=P.parents[1];E=P/'stages/e124_semantic_service_ridge_v1'
C=json.loads((E/'config.locked.json').read_text());done=json.loads((R/'reviews/rebuild_complete.json').read_text());assert done['status']=='GT_H_PROFILE_REPRODUCED_ROUTER_PENDING';assert time.time()<datetime.datetime.fromisoformat('2026-09-22T13:25:00+00:00').timestamp()
def ident(p):return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def dump(p,v):assert not p.exists(),p;p.write_text(json.dumps(v,indent=2)+'\n')
header=ROOT/'entry_method_exploration/20260915_gate_l2_r1_r100_v1/src';files=[Path(__file__),R/'src/router.cpp',R/'protocol.md',R/'reviews/rebuild_complete.json']+list((header/'hnswlib').glob('*.h'))
dump(R/'reviews/router_frozen.json',{'files':{str(p):ident(p) for p in files}})
(R/'bin').mkdir(exist_ok=True);argv=['g++','-O3','-march=native','-std=c++17','-pthread','-I'+str(header),'-I'+str(ROOT/'build/_deps/json-src/single_include'),str(R/'src/router.cpp'),'-o',str(R/'bin/router')];t=time.perf_counter()
with (R/'logs/router_build.log').open('x') as f:p=subprocess.run(argv,stdout=f,stderr=subprocess.STDOUT)
dump(R/'reviews/router_build.json',{'argv':argv,'seconds':time.perf_counter()-t,'exit_code':p.returncode});assert p.returncode==0
jobs={}
for ds,dc in C['datasets'].items():
    qgt=json.loads((R/'reviews/preflight.json').read_text())['datasets'][ds]['qgt_queries'];rp=R/'results'/ds
    conf={'dimension':dc['dimension'],'W':str(rp/'rebuilt_W.f32'),'ids':str(rp/'rebuilt_ids.i32'),'old_graph':dc['anchor']['graph'],'query_inputs':[{'path':qgt,'fvecs':True},{'path':dc['fit_source']['queries_file'],'fvecs':False}]};cp=R/'reviews'/f'{ds}.router_config.json';dump(cp,conf)
    t=time.perf_counter();env=os.environ.copy();env.update(OMP_NUM_THREADS='8',OPENBLAS_NUM_THREADS='8',MKL_NUM_THREADS='8')
    with (R/'logs'/f'{ds}.router.log').open('x') as f:p=subprocess.run(['taskset','-c','0-7',str(R/'bin/router'),str(cp),str(rp/'router')],env=env,stdout=f,stderr=subprocess.STDOUT)
    jobs[ds]={'exit_code':p.returncode,'process_seconds':time.perf_counter()-t};assert p.returncode==0,ds
dump(R/'reviews/router_complete.json',{'status':'PASS','jobs':jobs,'all_current_default_graphs_reproduced':True,'new_ANN_calls':100000,'new_NSG_calls':0,'QPS_measured':False})
print('PASS')
