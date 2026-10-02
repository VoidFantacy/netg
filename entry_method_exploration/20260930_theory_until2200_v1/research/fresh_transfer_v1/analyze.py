import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='1'
os.sched_setaffinity(0,{14})
import csv,hashlib,json,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent;C=json.loads((R/'config.locked.json').read_text())
def ident(p):
    p=Path(p);return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def dump(p,v):
    with Path(p).open('x') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def boot_integer_sums(strata,seed):
    # Multinomial counts are distribution-identical to resampling paired query differences.
    rng=np.random.default_rng(seed);total=np.zeros(C['bootstrap_replicates'],dtype='i4')
    for values in strata:
        support,counts=np.unique(values.astype('i4'),return_counts=True);prob=counts/len(values)
        for lo in range(0,len(total),1024):
            hi=min(lo+1024,len(total));draw=rng.multinomial(len(values),prob,size=hi-lo);total[lo:hi]+=draw@support
    return total
def main():
    start=time.perf_counter();assert json.loads((R/'reviews/run_complete.json').read_text())['status']=='COMPUTED_PENDING_INDEPENDENT_AUDIT'
    dump(R/'reviews/analysis_frozen.json',{'source':ident(__file__),'unix':time.time(),'bootstrap':'multinomial paired-query differences; pooled two independent stratum resamples'})
    records={};data={};saved={};tables=[];returned=0
    for case_index,(case,c) in enumerate(C['cases'].items()):
        n=c['n'];truth=np.fromfile(c['gt'],'<i4').reshape(n,100);points=[];data[case]={}
        for point in c['points']:
            k,L=point['K'],point['L'];stats=[];values=[];hitsets=[]
            for method in c['methods']:
                name=method['name'];p=R/'results'/case/f'k{k}'/f'{name}_L{L}';ids=np.fromfile(p/'ids.i32','<i4').reshape(n,k)
                dist=np.fromfile(p/'distances.f32','<f4').reshape(n,k);entries=np.fromfile(p/'entry_ids.i32','<i4').reshape(n,3)
                meta=json.loads((p/'complete.json').read_text());assert meta['threads']==1 and meta['formal'] and meta['warm_plain_count_bit_parity'] and len(meta['seconds'])==3
                assert ids.min()>=0 and ids.max()<c['base_n'] and np.isfinite(dist).all() and (np.diff(np.sort(ids,axis=1),axis=1)>0).all()
                if k==100:
                    assert (np.diff(dist,axis=1)>=0).all();sets=[set(row)&set(gt) for row,gt in zip(ids,truth)]
                else:sets=[{int(row[0])} if row[0]==gt[0] else set() for row,gt in zip(ids,truth)]
                hits=np.fromiter((len(s) for s in sets),dtype='i2',count=n);sec=meta['seconds'];qps=n/float(np.mean(sec))
                item={'method':name,'hits':int(hits.sum()),'recall':float(hits.mean()/k),'QPS':qps,'seconds':sec,'QPS_each_round':[n/x for x in sec],
                    'graph_ndc_mean':float(np.fromfile(p/'graph_ndc.u64','<u8').mean()),'route_ndc_mean':float(np.fromfile(p/'route_ndc.u64','<u8').mean())}
                stats.append(item);values.append({'hits':hits,'entries':entries,'ids':ids});hitsets.append(sets);saved[f'{case}__K{k}__{name}__hits']=hits;returned+=n
                tables.append({'scope':case,'dataset':c['dataset'],'batch':c['batch'],'K':k,'L':L,**{key:item[key] for key in ['method','hits','recall','QPS','graph_ndc_mean','route_ndc_mean']}})
            comparisons=[];delta_map={}
            for j in range(1,len(values)):
                for ref in range(j):
                    delta=values[j]['hits']-values[ref]['hits'];key=f'{stats[j]["method"]}__vs__{stats[ref]["method"]}'
                    boot=boot_integer_sums([delta],C['bootstrap_seed']+case_index*100+k);ci=np.quantile(boot,[.025,.975])/(n*k)*100
                    rescue=sum(len(a-b) for a,b in zip(hitsets[j],hitsets[ref]));damage=sum(len(b-a) for a,b in zip(hitsets[j],hitsets[ref]));assert rescue-damage==int(delta.sum())
                    support,counts=np.unique(delta,return_counts=True)
                    row={'method':stats[j]['method'],'reference':stats[ref]['method'],'delta_recall_pp':float(delta.sum()/(n*k)*100),
                        'descriptive_95_interval_pp':ci.tolist(),'positive_queries':int(np.sum(delta>0)),'negative_queries':int(np.sum(delta<0)),
                        'rescue_members':rescue,'damage_members':damage,'member_change_net':int(delta.sum()),
                        'entry_changes':int(np.any(values[j]['entries']!=values[ref]['entries'],axis=1).sum()),
                        'output_id_changes':int(np.any(values[j]['ids']!=values[ref]['ids'],axis=1).sum()),
                        'QPS_change_pct':float(100*(stats[j]['QPS']/stats[ref]['QPS']-1)),
                        'QPS_change_each_round_pct':[float(100*(stats[ref]['seconds'][i]/stats[j]['seconds'][i]-1)) for i in range(3)],
                        'query_hit_delta_values':support.tolist(),'query_hit_delta_counts':counts.tolist()}
                    comparisons.append(row);delta_map[key]=delta;saved[f'{case}__K{k}__{key}__boot_sums']=boot
            points.append({'K':k,'L':L,'n':n,'methods':stats,'comparisons':comparisons});data[case][k]={'methods':stats,'deltas':delta_map}
        records[case]={'dataset':c['dataset'],'batch':c['batch'],'points':points}
        print(case,'ANALYZED',flush=True)
    pooled={}
    for ds_index,ds in enumerate(C['datasets']):
        cases=[f'{ds}_b0',f'{ds}_b1'];points=[]
        for p in C['cases'][cases[0]]['points']:
            k,L=p['K'],p['L'];methods=[];comparisons=[];n=8192
            for j,m in enumerate(C['cases'][cases[0]]['methods']):
                stats=[data[case][k]['methods'][j] for case in cases];sec=[sum(s['seconds'][i] for s in stats) for i in range(3)];hits=sum(s['hits'] for s in stats)
                item={'method':m['name'],'hits':hits,'recall':hits/(n*k),'QPS':n/float(np.mean(sec)),'seconds_combined_per_round':sec,
                    'QPS_each_combined_round':[n/x for x in sec],'batch_recalls':[s['recall'] for s in stats],'batch_QPS':[s['QPS'] for s in stats]}
                methods.append(item);tables.append({'scope':'pooled_equal_batches','dataset':ds,'batch':'both','K':k,'L':L,
                    'method':m['name'],'hits':hits,'recall':item['recall'],'QPS':item['QPS'],'graph_ndc_mean':'','route_ndc_mean':''})
            for key in data[cases[0]][k]['deltas']:
                strata=[data[case][k]['deltas'][key] for case in cases];boot=boot_integer_sums(strata,C['bootstrap_seed']+5000+ds_index*100+k)
                ci=np.quantile(boot,[.025,.975])/(n*k)*100;name,reference=key.split('__vs__');m=next(x for x in methods if x['method']==name);ref=next(x for x in methods if x['method']==reference)
                per=[next(x for point in records[case]['points'] if point['K']==k for x in point['comparisons'] if x['method']==name and x['reference']==reference) for case in cases]
                rec={'method':name,'reference':reference,'delta_recall_pp':sum(int(x.sum()) for x in strata)/(n*k)*100,
                    'stratified_descriptive_95_interval_pp':ci.tolist(),'batch_delta_recall_pp':[x['delta_recall_pp'] for x in per],
                    'rescue_members':sum(x['rescue_members'] for x in per),'damage_members':sum(x['damage_members'] for x in per),
                    'positive_queries':sum(x['positive_queries'] for x in per),'negative_queries':sum(x['negative_queries'] for x in per),
                    'entry_changes':sum(x['entry_changes'] for x in per),'output_id_changes':sum(x['output_id_changes'] for x in per),
                    'QPS_change_pct':100*(m['QPS']/ref['QPS']-1),'batch_QPS_change_pct':[x['QPS_change_pct'] for x in per]}
                comparisons.append(rec);saved[f'{ds}__pooled__K{k}__{key}__boot_sums']=boot
            points.append({'K':k,'L':L,'n':n,'methods':methods,'comparisons':comparisons})
        pooled[ds]={'points':points}
    np.savez_compressed(R/'results/aligned_hits_and_bootstrap.npz',**saved)
    dump(R/'results/summary.json',{'status':'COMPUTED_PENDING_AUDIT','cases':records,'pooled_equal_batches':pooled,'new_source_validation':True,
        'returned_query_vectors_rescored':returned,'seconds':time.perf_counter()-start,'default_changed':False,
        'uncertainty_scope':'paired-query descriptive bootstrap, stratified across two fixed source windows; no multiplicity correction or semantic-iid guarantee',
        'timing_scope':'combined QPS is total 8192 queries divided by mean sum of the two complete query loop walls; file/index load excluded and separately logged'})
    with (R/'results/metrics.csv').open('x') as f:
        writer=csv.DictWriter(f,fieldnames=list(tables[0]));writer.writeheader();writer.writerows(tables)
    print('ALL ANALYZED',time.perf_counter()-start,flush=True)
if __name__=='__main__':main()
