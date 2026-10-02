import pathlib,json,subprocess,os,time
D=pathlib.Path(__file__).resolve().parent.parent
state=json.loads((D/'state.json').read_text());assert state['status']=='MEASUREMENTS_COMPLETE'
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
start=time.time()
with (D/'logs/original_only.log').open('w') as f:
 p=subprocess.run(['taskset','-c','15',str(D/'bin/diagnose.original'),str(D/'config.json'),str(D/'results/original_only'),'original_only'],env=env,stdout=f,stderr=subprocess.STDOUT,timeout=1800)
assert p.returncode==0
r=json.loads((D/'results/original_only/complete.json').read_text());state['search_calls']+=r['search_calls'];assert state['search_calls']<=600000
state['matched_memory_control_wall_seconds']=time.time()-start;state['matched_memory_control']='PASS';(D/'state.json').write_text(json.dumps(state,indent=2)+'\n')
