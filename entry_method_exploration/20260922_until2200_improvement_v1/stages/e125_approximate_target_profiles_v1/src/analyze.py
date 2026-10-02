import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='1'
import json,time,hashlib,csv
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1];P=R.parent.parent;C=json.loads((R/'config.locked.json').read_text());start=time.perf_counter();I={};records={};rows=[];vectors=0
assert json.loads((R/'reviews/jobs_complete.json').read_text())['status']=='PASS'
def ident(p):return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def dump(p,x):assert not p.exists(),p;p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def raw(p,t):I[str(p)]=ident(p);return np.fromfile(p,t)
def read(p):I[str(p)]=ident(p);return json.loads(p.read_text())
dump(R/'reviews/analysis_frozen.json',{'files':{str(p):ident(p) for p in [Path(__file__),R/'protocol.md',R/'config.locked.json']}})
for di,(ds,dc) in enumerate(C['datasets'].items()):
    ec=dc['evaluate'];gt=raw(Path(ec['gt']),'<i4').reshape(4096,100);data={};points=[];costjob=read(R/'reviews'/f'{ds}_labels.job.json');oldcost=read(P/'research/gt_inclusive_build_cost_v1/results'/ds/'complete.json');labelratio=costjob['seconds']/oldcost['GT']['profile20000']['search_seconds'];model=read(R/'models'/ds/'profiles.json')
    for point in ec['points']:
        K,L=point['K'],point['L'];pair=[];stats=[]
        for m in ec['methods']:
            pp=R/'results'/ds/'evaluation'/f'k{K}'/f'{m["name"]}_L{L}';out=raw(pp/'ids.i32','<i4').reshape(4096,K);dist=raw(pp/'distances.f32','<f4').reshape(4096,K);meta=read(pp/'complete.json');assert meta['threads']==1 and len(meta['seconds'])==3
            assert (out>=0).all() and (out<ec['base_n']).all() and np.isfinite(dist).all();assert K==1 or ((np.diff(np.sort(out,axis=1),axis=1)>0).all() and (np.diff(dist,axis=1)>=0).all())
            if K==1:hits=(out[:,0]==gt[:,0]).astype('u1')
            else:
                hits=np.empty(4096,'u1')
                for j in range(4096):
                    ss=np.sort(gt[j]);ix=np.searchsorted(ss,out[j]);hits[j]=((ix<100)&(ss[np.minimum(ix,99)]==out[j])).sum()
            pair.append(hits);qps=4096/np.mean(meta['seconds']);stats.append({'name':m['name'],'recall':float(hits.mean()/K),'QPS':float(qps),'QPS_each_round':[4096/s for s in meta['seconds']],'seconds':meta['seconds']});vectors+=4096
        delta=(pair[1].astype('f8')-pair[0])/K;primary=L==dc['primary_L'][str(K)];ci=None;boot=None
        if primary:
            rng=np.random.default_rng(C['bootstrap_seed']+di*100+(0 if K==1 else 1));boot=[]
            for lo in range(0,C['bootstrap_reps'],64):
                ix=rng.integers(0,4096,(min(64,C['bootstrap_reps']-lo),4096));boot.append(delta[ix].mean(1))
            boot=np.concatenate(boot);ci=(np.quantile(boot,[.00625,.99375])*100).tolist();data[f'K{K}_L{L}_bootstrap']=boot
        dr=float(delta.mean()*100);ratio=stats[1]['QPS']/stats[0]['QPS'];record={'K':K,'L':L,'primary':primary,'methods':stats,'delta_recall_pp':dr,'primary_98_75_interval_pp':ci,'QPS_ratio':ratio,'QPS_change_pct':100*(ratio-1),'positive_queries':int((delta>0).sum()),'negative_queries':int((delta<0).sum()),'rescue_mass_members':int(np.maximum(delta*K,0).round().sum()),'damage_mass_members':int(np.maximum(-delta*K,0).round().sum())};points.append(record)
        data[f'K{K}_L{L}_hits']=np.stack(pair);data[f'K{K}_L{L}_delta']=delta;rows.append({'dataset':ds,'K':K,'L':L,'primary':primary,'default_recall':stats[0]['recall'],'candidate_recall':stats[1]['recall'],'delta_pp':dr,'default_QPS':stats[0]['QPS'],'candidate_QPS':stats[1]['QPS'],'QPS_change_pct':100*(ratio-1)})
    g=C['gate'];gates={'label_cost':labelratio<g['label_process_vs_exact20k_search_max_ratio'],'all_point_mean_quality':all(p['delta_recall_pp']>=g['all_point_mean_delta_recall_min_pp'] for p in points),'primary_quality_interval':all(p['primary_98_75_interval_pp'][0]>=g['primary_98_75_lower_min_pp'] for p in points if p['primary']),'all_point_speed':all(p['QPS_ratio']>=g['all_point_QPS_ratio_min'] for p in points)}
    records[ds]={'points':points,'candidate_label_job_seconds':costjob['seconds'],'exact_profile20k_search_seconds_reference':oldcost['GT']['profile20000']['search_seconds'],'candidate_label_cost_ratio':labelratio,'label_threads':1,'exact_reference_CPU_cap':8,'profile_directions':model['direction'],'gates':gates};np.savez(R/'results'/f'{ds}.aligned.npz',**data);print(ds,gates,flush=True)
passed=all(all(v['gates'].values()) for v in records.values());status='PASS_BUILD_COST_PILOT' if passed else 'STOP_APPROX_TARGET_PROFILE_PILOT';dump(R/'results/summary.json',{'status':status,'datasets':records,'default_changed':False,'new_source_validation':False,'complete_online_wall_at_12_matched_points':True,'new_default_eligible':False});dump(R/'results/gate.json',{'status':status,'passed_pilot':passed,'no_retuning':True,'default_changed':False,'eligible_method':'ApproxTarget10'})
with (R/'results/metrics.csv').open('x') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
for p,v in I.items():assert ident(Path(p))==v,p
dump(R/'reviews/analysis_inputs.json',I);dump(R/'reviews/analysis_complete.json',{'status':'PASS','seconds':time.perf_counter()-start,'all_return_vectors_rescored':vectors,'primary_paired_intervals':4,'matched_points':12,'source_files':len(I),'new_searches':0,'new_fits':0})
print(status)
