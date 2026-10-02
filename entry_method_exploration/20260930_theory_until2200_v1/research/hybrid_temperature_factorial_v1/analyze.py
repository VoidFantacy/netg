import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='1'
import csv
import hashlib
import json
import time
from pathlib import Path
import numpy as np

R=Path(__file__).resolve().parent
C=json.loads((R/'config.locked.json').read_text())

def ident(p):
    p=Path(p);return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}

def dump(p,x):
    with Path(p).open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')

def bootstrap(values,seed):
    rng=np.random.default_rng(seed);out=[];n=len(values)
    for lo in range(0,C['bootstrap_reps'],64):
        indices=rng.integers(0,n,(min(64,C['bootstrap_reps']-lo),n))
        out.append(values[indices].mean(1))
    samples=np.concatenate(out)
    return (np.quantile(samples,[.025,.975])*100).tolist(),samples

def main():
    started=time.perf_counter();records={};csvrows=[];arrays_count=0
    assert json.loads((R/'reviews/jobs_complete.json').read_text())['status']=='PASS'
    dump(R/'reviews/analysis_frozen.json',{'source':ident(Path(__file__)),'unix':time.time()})
    for di,(ds,dc) in enumerate(C['datasets'].items()):
        ec=dc['evaluate'];n=ec['n'];gt=np.fromfile(ec['gt'],'<i4').reshape(n,100);records[ds]={'points':[]}
        saved={}
        for point in ec['points']:
            K,L=point['K'],point['L'];data=[];stats=[]
            for m in ec['methods']:
                path=R/'results'/ds/'evaluation'/f'k{K}'/f'{m["name"]}_L{L}'
                ids=np.fromfile(path/'ids.i32','<i4').reshape(n,K)
                distances=np.fromfile(path/'distances.f32','<f4').reshape(n,K)
                entries=np.fromfile(path/'entry_ids.i32','<i4').reshape(n,3)
                count=np.fromfile(path/'graph_ndc.u64','<u8');route=np.fromfile(path/'route_ndc.u64','<u8')
                meta=json.loads((path/'complete.json').read_text())
                assert meta['threads']==1 and meta['warm_plain_count_bit_parity'] and len(meta['seconds'])==3
                assert ids.min()>=0 and ids.max()<ec['base_n'] and np.isfinite(distances).all()
                if K==100:
                    assert (np.diff(np.sort(ids,axis=1),axis=1)>0).all() and (np.diff(distances,axis=1)>=0).all()
                    hits=np.array([len(set(row).intersection(truth)) for row,truth in zip(ids,gt)],dtype='i2')
                else:hits=(ids[:,0]==gt[:,0]).astype('i2')
                seconds=meta['seconds'];qps=n/np.mean(seconds)
                stats.append({'method':m['name'],'recall':float(hits.mean()/K),'QPS':float(qps),'seconds':seconds,
                              'QPS_each_round':[n/x for x in seconds],'graph_ndc_mean':float(count.mean()),
                              'route_ndc_mean':float(route.mean())})
                data.append({'hits':hits,'ids':ids,'entries':entries})
                saved[f'K{K}_{m["name"]}_hits']=hits
                arrays_count+=n
            comparisons=[]
            seed=C['bootstrap_seed']+di*100+K
            for j in range(1,len(data)):
                for ref in [0,1]:
                    if j==ref:continue
                    delta=(data[j]['hits']-data[ref]['hits']).astype('f8')/K
                    ci,boot=bootstrap(delta,seed)
                    row={'method':stats[j]['method'],'reference':stats[ref]['method'],
                         'delta_recall_pp':float(delta.mean()*100),'descriptive_95_interval_pp':ci,
                         'positive_queries':int(np.sum(delta>0)),'negative_queries':int(np.sum(delta<0)),
                         'rescue_members':int(np.maximum(data[j]['hits']-data[ref]['hits'],0).sum()),
                         'damage_members':int(np.maximum(data[ref]['hits']-data[j]['hits'],0).sum()),
                         'entry_set_changes':int(np.any(np.sort(data[j]['entries'],axis=1)!=np.sort(data[ref]['entries'],axis=1),axis=1).sum()),
                         'entry_order_changes':int(np.any(data[j]['entries']!=data[ref]['entries'],axis=1).sum()),
                         'output_id_changes':int(np.any(data[j]['ids']!=data[ref]['ids'],axis=1).sum()),
                         'QPS_change_pct':float(100*(stats[j]['QPS']/stats[ref]['QPS']-1))}
                    comparisons.append(row)
                    saved[f'K{K}_{stats[j]["method"]}_vs_{stats[ref]["method"]}_bootstrap']=boot
                    csvrows.append({'dataset':ds,'K':K,'L':L,**{k:v for k,v in row.items() if k!='descriptive_95_interval_pp'},
                                    'ci_low_pp':ci[0],'ci_high_pp':ci[1]})
            interaction=None
            if len(data)==5:
                # Default, ApproxFixed, HybridFixed, ApproxPilot, HybridPilot.
                values=(data[4]['hits']-data[3]['hits']-data[2]['hits']+data[1]['hits']).astype('f8')/K
                ci,boot=bootstrap(values,seed)
                interaction={'temperature_by_replacement_delta_pp':float(values.mean()*100),'descriptive_95_interval_pp':ci}
                saved[f'K{K}_factorial_interaction_bootstrap']=boot
            records[ds]['points'].append({'K':K,'L':L,'methods':stats,'comparisons':comparisons,'interaction':interaction})
            print(ds,K,{'methods':stats,'comparisons':comparisons,'interaction':interaction},flush=True)
        # Only after every candidate and graph was frozen do we compare to the exact default.
        d=ec['dimension'];default=np.fromfile(ec['methods'][0]['W'],'<f4').reshape(-1,d).astype('f8')
        default/=np.linalg.norm(default,axis=1,keepdims=True)
        geometry={}
        for m in ec['methods'][1:]:
            w=np.fromfile(m['W'],'<f4').reshape(-1,d).astype('f8');w/=np.linalg.norm(w,axis=1,keepdims=True)
            chord=((w-default)**2).sum(1)
            geometry[m['name']]={'chord2_sum':float(chord.sum()),'chord2_mean':float(chord.mean()),
                                'angle_degrees_quantiles':np.quantile(np.degrees(np.arccos(np.clip((w*default).sum(1),-1,1))),[.5,.9,.99,1]).tolist()}
        for item in geometry.values():item['chord_ratio_to_approx']=item['chord2_sum']/geometry['ApproxTarget10']['chord2_sum']
        records[ds]['geometry']=geometry
        np.savez_compressed(R/'results'/(ds+'.aligned.npz'),**saved)
    dump(R/'results/summary.json',{'status':'COMPUTED_PENDING_AUDIT','datasets':records,'default_changed':False,
         'n_return_vectors_rescored':arrays_count,'new_GT':0,'new_source_validation':False,
         'cold_start_wall_measured':False,'seconds':time.perf_counter()-started})
    with (R/'results/metrics.csv').open('x') as f:
        writer=csv.DictWriter(f,fieldnames=list(csvrows[0]));writer.writeheader();writer.writerows(csvrows)
    print('ANALYZED',round(time.perf_counter()-started,3),flush=True)

if __name__=='__main__':main()
