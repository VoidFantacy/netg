from pathlib import Path
import json,time,hashlib
import numpy as np
R=Path(__file__).resolve().parents[1];P=R.parent.parent;C=json.loads((R/'config.locked.json').read_text());n=C['n'];t=time.perf_counter()
def dump(p,x):assert not p.exists(),p;p.write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
dump(R/'reviews/analysis_frozen.json',{'unix':time.time(),'source_sha256':sha(Path(__file__))})
assert json.loads((R/'reviews/jobs_complete.json').read_text())['status']=='PASS'
gt=np.fromfile(R/'inputs/webvid2_5m_light_v1/gt.i32',dtype='<i4').reshape(n,100);hits=[];methods={};allfiles={}
for m in C['datasets']['webvid2_5m_light_v1']['methods']:
 name=m['name'];D=R/'results/evaluation/k1'/f'{name}_L1000';meta=json.loads((D/'complete.json').read_text());ids=np.fromfile(D/'ids.i32',dtype='<i4');assert ids.shape==(n,);h=(ids==gt[:,0]).astype(np.int8);hits.append(h);secs=np.array(meta['seconds']);assert len(secs)==3 and meta['threads']==1
 methods[name]={'hits':int(h.sum()),'n':n,'recall_percent':float(h.mean()*100),'seconds':secs.tolist(),'mean_seconds':float(secs.mean()),'qps':float(n/secs.mean()),'qps_rounds':(n/secs).tolist(),'qps_min':float((n/secs).min()),'qps_max':float((n/secs).max())}
 for p in D.iterdir():
  if p.is_file():allfiles[str(p.relative_to(R))]=sha(p)
a,b=hits;delta=b-a;rescue=int((delta>0).sum());damage=int((delta<0).sum());rng=np.random.default_rng(C['bootstrap_seed']);samples=[]
for start in range(0,C['bootstrap_replicates'],100):samples.extend(delta[rng.integers(n,size=(min(100,C['bootstrap_replicates']-start),n))].mean(axis=1)*100)
ci=np.percentile(samples,C['CI_percentiles']).tolist();names=list(methods);ratio=methods[names[1]]['qps']/methods[names[0]]['qps']
np.savez_compressed(R/'results/aligned.npz',default_hits=a,candidate_hits=b,delta=delta,bootstrap_pp=np.array(samples))
S={'status':'COMPLETED_DESCRIPTIVE_FOLLOWUP','dataset':'webvid2_5m_light_v1','K':1,'L':1000,'n':n,'methods':methods,'recall_delta_pp':float(delta.mean()*100),'paired_bootstrap95_pp':ci,'rescue':rescue,'damage':damage,'both_hit':int(((a==1)&(b==1)).sum()),'both_miss':int(((a==0)&(b==0)).sum()),'qps_change_percent':float((ratio-1)*100),'old_E125_same_point':{'recall_delta_pp':-4/4096*100,'rescue':3,'damage':7,'CI_level_percent':98.75,'CI_pp':[-.29296875,.0732421875],'old_gate':'STOP_APPROX_TARGET_PROFILE_PILOT'},'policy':'no automatic veto from CI; evaluate practical tradeoffs; no automatic default replacement','default_changed':False,'seconds':time.perf_counter()-t,'output_hashes':allfiles}
dump(R/'results/summary.json',S);print(json.dumps({k:v for k,v in S.items() if k not in ['output_hashes']},indent=2,ensure_ascii=False))
