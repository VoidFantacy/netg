import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='1'
import hashlib,json,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1];E=R.parents[2];OLD=E/'20260921_comparison_direction_pilot_v1'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):
 assert not p.exists(),p
 p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
cfg=read(OLD/'config.locked.json');inputs={};start=time.perf_counter();result={};all_qstats={}
def raw(p,typ):inputs[str(p)]={'size':p.stat().st_size,'sha256':sha(p)};return np.fromfile(p,typ)
dump(R/'reviews/analysis_frozen.json',{'src_sha256':sha(Path(__file__)),'protocol_sha256':sha(R/'protocol.md'),'relations':{str(p.name):sha(p) for p in (R/'results').glob('*.relations.npz')}})
for ds,c in cfg['datasets'].items():
 ids=np.fromfile(c['anchor']['ids'],'<i4');H=len(ids);labeldir=OLD/'results'/ds/'labels';done=read(labeldir/'complete.json')
 hits={1:[],100:[]};top=[]
 for b in sorted(done['blocks'],key=lambda x:x['start']):
  p=labeldir/f"block_{b['start']}";n=b['n'];A=H+1
  for K in [1,100]:hits[K].append(raw(p/f'hits{K}.u8','u1').reshape(n,A)[:,1:].astype('f8')/K)
  top.append(raw(p/'top1_ids.i32','<i4').reshape(n,A)[:,1:])
 hits={k:np.concatenate(v) for k,v in hits.items()};top=np.concatenate(top);pairs=dict(np.load(R/'results'/f'{ds}.relations.npz'));record={};qstats={}
 for geometry in ['Profile','RawHub']:
  x,y=pairs[geometry+'_left'],pairs[geometry+'_right'];sx,sy=pairs[geometry+'_shuffle_left'],pairs[geometry+'_shuffle_right']
  for K in [1,100]:
   h=hits[K];centered=h-h.mean(0);qs=np.zeros((len(h),4),dtype='f8')
   for begin in range(0,len(h),64):
    stop=min(begin+64,len(h));a=centered[begin:stop]
    qs[begin:stop,0]=((a[:,x]-a[:,y])**2).mean(1);qs[begin:stop,1]=((a[:,sx]-a[:,sy])**2).mean(1)
    if K==1:
     qs[begin:stop,2]=(top[begin:stop,x]==top[begin:stop,y]).mean(1);qs[begin:stop,3]=(top[begin:stop,sx]==top[begin:stop,sy]).mean(1)
   means=qs.mean(0);rng=np.random.default_rng(2026092218);boots=[]
   for begin in range(0,10000,128):
    ind=rng.integers(0,len(h),size=(min(128,10000-begin),len(h)));mb=qs[ind,:2].mean(1);boots.append(mb[:,0]/mb[:,1])
   b=np.concatenate(boots);ci=list(map(float,np.quantile(b,[.025,.975])));ratio=float(means[0]/means[1]);key=geometry+f'_K{K}'
   record[key]={'neighbor_centered_mse':float(means[0]),'permuted_centered_mse':float(means[1]),'ratio':ratio,'ratio_CI95':ci,'passed_local_condition':ratio<=.8 and ci[1]<1}
   if K==1:record[key].update(neighbor_top1_same_fraction=float(means[2]),permuted_top1_same_fraction=float(means[3]))
   qstats[key]=qs
   # Independent scalar-vector verification on 32 deterministically spaced queries.
   for i in np.linspace(0,len(h)-1,32,dtype=int):
    for col,lft,rgt in [(0,x,y),(1,sx,sy)]:
     ref=sum((float(centered[i,a])-float(centered[i,b]))**2 for a,b in zip(lft,rgt))/len(lft)
     assert abs(ref-qs[i,col])<1e-12
 result[ds]=record;np.savez(R/'results'/f'{ds}.query_statistics.npz',**qstats)
 print(ds,{k:round(v['ratio'],5) for k,v in record.items()},flush=True)
gate={geometry:all(result[ds][geometry+f'_K{K}']['passed_local_condition'] for ds in result for K in [1,100]) for geometry in ['Profile','RawHub']}
dump(R/'results/summary.json',{'datasets':result,'structure_gate':gate,'status':'STRUCTURE_ONLY' if any(gate.values()) else 'STOP_LOCAL_ACTION_SMOOTHNESS','seconds':time.perf_counter()-start,'new_searches':0,'new_training':0,'not_deployment_gate':True})
dump(R/'reviews/inputs.json',inputs)
for p,v in inputs.items():assert sha(Path(p))==v['sha256']
dump(R/'reviews/complete.json',{'status':'PASS','protected_input_files':len(inputs),'independent_scalar_checks':2*2*2*32*2,'new_searches':0,'new_training':0})
print(gate,flush=True)
