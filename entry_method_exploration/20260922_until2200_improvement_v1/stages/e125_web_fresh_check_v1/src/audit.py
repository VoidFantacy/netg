from pathlib import Path
import json,time,hashlib,struct
import numpy as np
R=Path(__file__).resolve().parents[1];t=time.perf_counter();S=json.loads((R/'results/summary.json').read_text());C=json.loads((R/'config.locked.json').read_text());n=C['n']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):assert not p.exists();p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
dump(R/'reviews/audit_frozen.json',{'unix':time.time(),'source_sha256':sha(Path(__file__))})
g=struct.unpack('<'+'i'*(n*100),(R/'inputs/webvid2_5m_light_v1/gt.i32').read_bytes());hit=[]
for name,m in S['methods'].items():
 D=R/'results/evaluation/k1'/f'{name}_L1000';ids=struct.unpack('<'+'i'*n,(D/'ids.i32').read_bytes());h=[int(x==g[i*100]) for i,x in enumerate(ids)];assert sum(h)==m['hits'];secs=json.loads((D/'complete.json').read_text())['seconds'];assert abs(n/(sum(secs)/len(secs))-m['qps'])<1e-10;hit.append(h)
a,b=hit;plus=sum(x==0 and y==1 for x,y in zip(a,b));minus=sum(x==1 and y==0 for x,y in zip(a,b));assert (plus,minus)==(S['rescue'],S['damage']);assert (plus-minus)*100/n==S['recall_delta_pp']
# Independent exact conditional empirical-bootstrap distribution: n-fold convolution of {-1,0,+1}.
M=1
while M<2*n+1:M*=2
pm=np.zeros(M);pm[0]=1-(plus+minus)/n;pm[1]=plus/n;pm[-1]=minus/n
conv=np.fft.ifft(np.fft.fft(pm)**n).real;support=np.arange(-n,n+1);weights=np.maximum(conv[support%M],0);weights/=weights.sum();cdf=np.cumsum(weights);exact=[float(support[np.searchsorted(cdf,p)]*100/n) for p in [.025,.975]]
assert max(abs(x-y) for x,y in zip(exact,S['paired_bootstrap95_pp']))<=100/n+1e-10
identities=0
for fname in ['frozen_before_source.json','models_before_source.json']:
 for path,meta in json.loads((R/'reviews'/fname).read_text())['files'].items():assert sha(Path(path))==meta['sha256'];identities+=1
for path,hashv in S['output_hashes'].items():assert sha(R/path)==hashv;identities+=1
Q=R/'inputs/webvid2_5m_light_v1';q=np.fromfile(Q/'queries.f32',dtype='<f4').reshape(n,512);keys=[hashlib.sha256(row.tobytes()).digest() for row in q];assert len(set(keys))==n
manifest=json.loads((Q/'manifest.json').read_text());old=set()
for item in manifest['excluded_files']:
 p=Path(item['path']);assert sha(p)==item['sha256'];raw=np.fromfile(p,dtype='<f4');rows=raw.reshape(-1,513)[:,1:] if p.suffix=='.fvecs' else raw.reshape(-1,512);old.update(hashlib.sha256(row.tobytes()).digest() for row in rows)
assert not(set(keys)&old)
rows=np.fromfile(Q/'source_rows.i64',dtype='<i8');assert len(rows)==n and np.all(rows[1:]>rows[:-1]) and np.all((rows>=2470000)&(rows<2490000))
source=Path(manifest['source']['source']);
with source.open('rb') as f:
 for i in range(0,n,256):f.seek(8+int(rows[i])*512*4);assert f.read(512*4)==q[i].tobytes()
timing=json.loads((R/'results/evaluation/timing_progress.json').read_text());assert len(timing)==6 and all(x['threads']==1 and x['cpu']==15 and x['K']==1 and x['L']==1000 for x in timing)
for m in C['datasets']['webvid2_5m_light_v1']['methods']:
 for k in ['W','graph','ids']:assert sha(Path(m[k]))==json.loads((R/'reviews/models_before_source.json').read_text())['files'][m[k]]['sha256']
result={'status':'PASS','independent_all_return_rescores':n*2,'identities_checked':identities,'fresh_source_bytes_checked':16,'new_vs_registered_and_E105_and_fit_byte_overlap':0,'exact_empirical_bootstrap95_pp':exact,'monte_carlo95_pp':S['paired_bootstrap95_pp'],'bootstrap_scope':'conditional empirical bootstrap; descriptive small-discordance interval, not guaranteed finite-sample coverage','threads_all_rounds':1,'default_changed':False,'seconds':time.perf_counter()-t};dump(R/'reviews/independent_audit.json',result);print(json.dumps(result,indent=2))
