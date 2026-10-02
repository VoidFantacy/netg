"""Read-only summaries of frozen historical responses; no search or model fitting."""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[key] = '1'
import csv, hashlib, json, time
from pathlib import Path
import numpy as np

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[1]
EXP = ROOT / 'entry_method_exploration'
consumed = {}

def source(path):
    path = Path(path)
    if str(path) not in consumed:
        h = hashlib.sha256()
        with path.open('rb') as f:
            for b in iter(lambda:f.read(1<<20), b''): h.update(b)
        consumed[str(path)] = {'size':path.stat().st_size,'sha256':h.hexdigest()}
    return path

def read(path): return json.loads(source(path).read_text())
def arr(path,dtype): return np.fromfile(source(path),dtype)
def dump(path,value):
    assert not path.exists(), path
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def quant(a):
    a=np.asarray(a)
    return None if not a.size else dict(zip(['min','p10','median','p90','max'],map(float,np.quantile(a,[0,.1,.5,.9,1]))))
def writecsv(path, rows):
    assert not path.exists()
    with path.open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def finite_responses():
    new=EXP/'20260922_target_budget_response_v1'
    old=EXP/'20260920_until1600_theory_v1/stages/e107_initialization_factorial'
    cfg=read(new/'config.locked.json')
    oldmetrics=list(csv.DictReader(source(new/'analysis/metrics.csv').open()))
    ref={(r['dataset'],int(r['K']),int(r['L']),r['method']):float(r['recall']) for r in oldmetrics}
    rows=[]; pairs=[]; aligned={}
    for ds,c in cfg['datasets'].items():
        names=[m['name'] for m in c['native']['methods']]
        assert names == ['NSGFixed1','UnitHub1','UnitHub3','GT11','GT13','GT101','GT103','DefaultANN']
        data=np.load(source(new/'analysis'/f'{ds}.npz'))
        entries={m:arr(old/'results'/f'main_{ds}'/m/'entries.i32','<i4').reshape(4096,3) for m in names}
        for K in (1,100):
            for L in sorted(set(c['old_K_L'][str(K)]+c['missing'][str(K)])):
                h=data[f'K{K}_L{L}'].astype(np.int16)
                assert h.shape == (4096,8) and h.min()>=0 and h.max()<=K
                for j,m in enumerate(names): assert abs(h[:,j].mean()/K-ref[ds,K,L,m])<1e-14
                base=h[:,-1]; a=h[:,[7,1,2,3,4,5,6]]
                alt=a[:,1:]; delta=alt-base[:,None]
                mx=a.max(1); mn=a.min(1)
                bestfixed=float(np.max(a.mean(0))/K)
                failed=base<K
                rec={'dataset':ds,'K':K,'L':L,'n':len(base),
                    'default_recall_pct':float(base.mean()/K*100),
                    'NSG_recall_pct':float(h[:,0].mean()/K*100),
                    'default_minus_NSG_pp':float((base-h[:,0]).mean()/K*100),
                    'all_seven_equal_hitcount_pct':float((mx==mn).mean()*100),
                    'all_eight_equal_hitcount_pct':float((h.max(1)==h.min(1)).mean()*100),
                    'default_tied_best_pct':float((base==mx).mean()*100),
                    'queries_any_better':int((mx>base).sum()),
                    'queries_any_worse':int((mn<base).sum()),
                    'queries_both_better_worse':int(((mx>base)&(mn<base)).sum()),
                    'oracle_gain_pp':float((mx-base).mean()/K*100),
                    'best_fixed_gain_pp':(bestfixed-base.mean()/K)*100,
                    'oracle_minus_best_fixed_pp':float(mx.mean()/K*100-bestfixed*100),
                    'missing_mass_recoverable_fraction':float((mx-base).sum()/(K-base).sum()) if (K-base).sum() else None,
                    'uniform_alt_gain_pp':float(delta.mean()/K*100),
                    'mean_pairwise_discordance_pct':float(np.mean([np.mean(a[:,i]!=a[:,j]) for i in range(7) for j in range(i+1,7)])*100)}
                if K==1:
                    rec['all_seven_wrong']=int((mx==0).sum())
                    rec['default_failures']=int((base==0).sum())
                    rec['all_eight_same_top1_id_pct']=float(np.mean(np.all(np.stack([
                        arr((new if L in c['missing'][str(K)] else old)/'results'/f'main_{ds}'/m/f'k{K}_L{L}'/'ids.i32','<i4') for m in names],axis=1)==
                        arr((new if L in c['missing'][str(K)] else old)/'results'/f'main_{ds}'/names[0]/f'k{K}_L{L}'/'ids.i32','<i4')[:,None],axis=1))*100)
                rows.append(rec)
                for j,m in enumerate(names[:-1]):
                    d=h[:,j]-base; change=np.any(entries[m]!=entries['DefaultANN'],axis=1)
                    pairs.append({'dataset':ds,'K':K,'L':L,'method':m,
                        'changed_entries':int(change.sum()),'changed_hitcount':int((d!=0).sum()),
                        'changed_entry_same_hit_fraction':float(np.mean(d[change]==0)) if change.any() else None,
                        'improved_queries':int((d>0).sum()),'harmed_queries':int((d<0).sum()),
                        'positive_hits':int(d[d>0].sum()),'negative_hits':int(-d[d<0].sum()),
                        'delta_pp':float(d.mean()/K*100)})
                aligned[f'{ds}_K{K}_L{L}']=a
    # Dictionaries differ for K1; JSON preserves explicit non-applicable fields.
    dump(RUN/'results/finite_responses.json',rows)
    writecsv(RUN/'results/finite_pairs.csv',pairs)
    np.savez_compressed(RUN/'results/finite_aligned.npz',**aligned)
    return rows

def full_h():
    old=EXP/'20260921_comparison_direction_pilot_v1'
    cfg=read(old/'config.locked.json'); records=[]
    for ds,c in cfg['datasets'].items():
        d=old/'results'/ds/'labels'; done=read(d/'complete.json'); A=done['A']; n=4096
        tr=read(old/'models'/ds/'training_report.json')
        for K,name in [(1,'hits1.u8'),(100,'hits100.u8')]:
            h=np.concatenate([arr(d/f"block_{b['start']}"/name,'u1').reshape(b['n'],A) for b in sorted(done['blocks'],key=lambda b:b['start'])]).astype(np.int16)
            assert h.shape==(n,A) and h.min()>=0 and h.max()<=K
            b=h[:,0]; x=h[:,1:]; delta=x-b[:,None]; mx=np.maximum(b,x.max(1))
            oracle=float((mx-b).mean()/K)
            assert abs(oracle-tr['methods']['GraphRecall']['training'][str(K)]['oracle_utility'])<1e-12
            p=(delta>0).mean(1); damage=(delta<0).mean(1)
            rec={'dataset':ds,'K':K,'L':128,'n':n,'H':A-1,
                'default_recall_pct':float(b.mean()/K*100),'oracle_gain_pp':oracle*100,
                'queries_with_better':int((p>0).sum()),'queries_with_worse':int((damage>0).sum()),
                'queries_both_better_worse':int(((p>0)&(damage>0)).sum()),
                'uniform_single_gain_pp':float(delta.mean()/K*100),
                'best_fixed_single_gain_pp':float(delta.mean(0).max()/K*100),
                'positive_query_action_pairs':int((delta>0).sum()),'negative_query_action_pairs':int((delta<0).sum()),
                'positive_pair_fraction':float((delta>0).mean()),'negative_pair_fraction':float((delta<0).mean()),
                'better_action_fraction_on_opportunity_queries':quant(p[p>0]),
                'worse_action_fraction_on_damage_queries':quant(damage[damage>0]),
                'missing_mass_recoverable_fraction':float((mx-b).sum()/(K-b).sum()),
                'oracle_is_ex_post':True,'QPS_available':False}
            if K==1:
                fail=b==0;success=~fail
                rec.update(default_failures=int(fail.sum()),unrescuable_by_any_H=int((mx==0).sum()),
                    success_fraction_of_single_actions_on_default_failures=quant(x[fail].mean(1)),
                    damage_fraction_of_single_actions_on_default_successes=quant(1-x[success].mean(1)),
                    random_rescue_rate_given_failure=float(x[fail].mean()),
                    random_damage_rate_given_success=float((1-x[success]).mean()))
                # Even with an oracle failure detector, random single selection only obtains this gain.
                rec['perfect_failure_detector_uniform_single_gain_pp']=float(x[fail].sum()/((A-1)*n)*100)
            records.append(rec)
    dump(RUN/'results/full_h_opportunity.json',records)
    return records

def e103():
    path=EXP/'20260916_optimized_five_dataset_r1_r100_v1/results/metrics.csv'
    rows=list(csv.DictReader(source(path).open()));assert len(rows)==800
    datasets=sorted(set(r['dataset'] for r in rows));out=[]
    for ds in datasets:
        for K in (1,100):
            methods=sorted(set(r['method'] for r in rows if r['dataset']==ds and int(r['K'])==K))
            for target in (.9,.95,.99):
                chosen={}
                for m in methods:
                    eligible=[r for r in rows if r['dataset']==ds and int(r['K'])==K and r['method']==m and float(r['recall'])>=target]
                    if eligible:
                        r=max(eligible,key=lambda r:float(r['qps_mean']))
                        chosen[m]={k:float(r[k]) for k in ('recall','qps_mean','qps_min','qps_max','route_ndc_mean','graph_ndc_mean')}
                        chosen[m]['L']=int(r['L'])
                out.append({'dataset':ds,'K':K,'target':target,'methods':chosen,'scope':'fastest measured feasible point; not equal achieved Recall or significance'})
    dump(RUN/'results/e103_thresholds.json',out)

if __name__=='__main__':
    start=time.perf_counter();os.sched_setaffinity(0,{15})
    a=finite_responses();b=full_h();e103()
    dump(RUN/'reviews/consumed_inputs.json',consumed)
    dump(RUN/'reviews/analysis_complete.json',{'status':'PASS','finite_points':len(a),'full_H_heads':len(b),'seconds':time.perf_counter()-start,
        'new_searches':0,'new_training':0,'new_graphs':0,'new_GT':0,'new_performance_timing':0,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    print(json.dumps({'finite_points':len(a),'full_H':b,'seconds':time.perf_counter()-start},ensure_ascii=False,indent=2))
