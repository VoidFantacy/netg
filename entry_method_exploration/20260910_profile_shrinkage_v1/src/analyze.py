"""Read-only analysis of all locked alpha candidates and the measured selected curve."""
import csv
import numpy as np
from common import RUN,DATASETS,NAMES,LS,read,dump,check_lock,frozen_check
from effect_stats import effect_stats
from select_alpha import load_stage,candidates_for

LABELS={'webvid2_5m_light_v1':'WebVid','yandex_t2i_official10M_ip_v1':'Yandex-IP'}
METHODS=['nsg','fast30k','fast20k','e24','shrink']
METHOD_LABELS={'nsg':'NSG','fast30k':'Fast30K','fast20k':'Fast20K','e24':'E24','shrink':'Shrink'}


def bootstrap_effects(h0,h1,ha):
    h0=np.asarray(h0,dtype='int16');h1=np.asarray(h1,dtype='int16');ha=np.asarray(ha,dtype='int16')
    if h0.ndim==1:h0=h0[:,None];h1=h1[:,None];ha=ha[:,None]
    d1=h1-h0;da=ha-h0;p1=np.maximum(d1,0);pa=np.maximum(da,0)
    rows=np.column_stack([(d1>0).sum(axis=1),((d1>0)&(da>0)).sum(axis=1),p1.sum(axis=1),np.minimum(p1,pa).sum(axis=1),
        (d1<0).sum(axis=1),(da<0).sum(axis=1),np.maximum(-d1,0).sum(axis=1),np.maximum(-da,0).sum(axis=1),
        da.sum(axis=1),(ha-h1).sum(axis=1)]).astype(float)
    rng=np.random.Generator(np.random.PCG64(20260910));samples=[]
    for _ in range(20):
        ids=rng.integers(0,len(h0),size=(100,len(h0)));s=rows[ids].sum(axis=1)
        div=lambda a,b:np.divide(a,b,out=np.full(100,np.nan),where=b>0)
        samples.append(np.column_stack([div(s[:,1],s[:,0]),div(s[:,3],s[:,2]),1-div(s[:,5],s[:,4]),1-div(s[:,7],s[:,6]),
                                       s[:,8]*10/h0.size,s[:,9]*10/h0.size]))
    samples=np.vstack(samples);intervals={}
    for j,name in enumerate(['R','Rh','A_all','Ah_all','delta_recall_pp_vs_A0','delta_recall_pp_vs_A1']):
        valid=samples[np.isfinite(samples[:,j]),j]
        intervals[name]={'low':float(np.quantile(valid,.025)) if len(valid) else None,
                         'high':float(np.quantile(valid,.975)) if len(valid) else None,'defined_replicates':len(valid)}
    return {'seed':20260910,'replicates':2000,'unit':'paired_query_all_L_kept_together',
            'interpretation':'descriptive_unadjusted_95_percentile_not_for_selection_or_formal_GO','intervals':intervals}


def bootstrap_difference(d):
    d=np.asarray(d,dtype=float)
    if d.ndim>1:d=d.mean(axis=1)
    rng=np.random.Generator(np.random.PCG64(20260910));samples=[]
    for _ in range(20):samples.append(d[rng.integers(0,len(d),size=(100,len(d)))].mean(axis=1)*10)
    samples=np.concatenate(samples)
    return {'low':float(np.quantile(samples,.025)),'high':float(np.quantile(samples,.975))}


def measured_frontier(points,key='qps'):
    return [p['name'] for p in points if not any(q['recall_at_10']>=p['recall_at_10'] and q[key]>=p[key] and
        (q['recall_at_10']>p['recall_at_10'] or q[key]>p[key]) for q in points if q is not p)]


def compare(ds,method,baseline,L,points,h):
    a=next(p for p in points if p['family']==method and p['L']==L);b=next(p for p in points if p['family']==baseline and p['L']==L)
    d=h[method][L]-h[baseline][L];ratios=np.asarray(a['qps_runs'])/b['qps_runs']
    return {'dataset':ds,'method':method,'reference':baseline,'L':L,
        'recall':a['recall_at_10'],'reference_recall':b['recall_at_10'],'delta_recall_pp':float(d.mean()*10),
        'delta_recall_pp_95':bootstrap_difference(d),'qps_median':a['qps'],'reference_qps_median':b['qps'],
        'qps_percent_change_medians':float((a['qps']/b['qps']-1)*100),
        'qps_percent_change_by_repeat':((ratios-1)*100).tolist(),
        'same_L_recall_and_median_qps_better':bool(d.sum()>0 and a['qps']>b['qps']),
        'recall_better_and_qps_better_all_three_repeats':bool(d.sum()>0 and np.all(ratios>1)),
        'improved_queries':int((d>0).sum()),'harmed_queries':int((d<0).sum()),'same_hit_queries':int((d==0).sum()),
        'positive_hits':int(np.maximum(d,0).sum()),'negative_hits':int(np.maximum(-d,0).sum()),'net_hits':int(d.sum()),
        'mean_graph_ndc_difference':a['mean_graph_ndc']-b['mean_graph_ndc'],
        'mean_total_ndc_difference':a['mean_total_ndc']-b['mean_total_ndc'],
        'zero_hit_rescues':int(((h[baseline][L]==0)&(h[method][L]>0)).sum()),
        'new_zero_hit_failures':int(((h[baseline][L]>0)&(h[method][L]==0)).sum())}


def main():
    check_lock();frozen_check('audit')
    assert read(RUN/'reviews/validation_verification.json')['status']=='PASS'
    report={'status':'ANALYSIS_COMPLETE','datasets':{},'comparisons':[],'formal_performance_GO':False}
    for ds in DATASETS:
        chosen=read(RUN/'models'/ds/'selection.json');record={'selected_alpha':chosen['alpha'],'selected_name':chosen['selected'],
            'cal_selection_status':chosen['status'],'development':{},'validation':{}}
        for stage in ['cal','audit']:
            _,h,_=load_stage(ds,stage);_,candidates=candidates_for(ds,stage)
            for c in candidates:c['bootstrap']=bootstrap_effects(h['fast20k'],h['e24'],h[c['name']])
            record['development'][stage]={'candidates':candidates,'selected':next(c for c in candidates if c['name']==chosen['selected']),
                'controls':{'A0':effect_stats(h['fast20k'],h['e24'],h['fast20k']),
                            'A1':effect_stats(h['fast20k'],h['e24'],h['e24'])}}
        folder=RUN/'results'/ds;points=read(folder/'results.json')['methods'];record['measured_points']=points
        h={method:{L:np.fromfile(folder/f'{method}_L{L}/hits.u8',dtype='u1').astype('int16') for L in LS} for method in METHODS}
        for L in LS:
            record['validation'][str(L)]={'stats':effect_stats(h['fast20k'][L],h['e24'][L],h['shrink'][L]),
                'bootstrap':bootstrap_effects(h['fast20k'][L],h['e24'][L],h['shrink'][L])}
        for name,ls in [('pooled_L64_L128',[64,128]),('all_five_L_descriptive_only',LS)]:
            mats={m:np.column_stack([h[m][L] for L in ls]) for m in ['fast20k','e24','shrink']}
            record['validation'][name]={'stats':effect_stats(mats['fast20k'],mats['e24'],mats['shrink']),
                'bootstrap':bootstrap_effects(mats['fast20k'],mats['e24'],mats['shrink'])}
        for method,refs in [('shrink',['fast20k','e24','fast30k','nsg']),('e24',['fast20k','nsg']),('fast30k',['fast20k','nsg'])]:
            for ref in refs:
                for L in LS:report['comparisons'].append(compare(ds,method,ref,L,points,h))
        record['frontier_among_25_measured_points']=measured_frontier(points)
        record['frontier_by_repeat']=[measured_frontier([{**p,'qps_repeat':p['qps_runs'][j]} for p in points],'qps_repeat') for j in range(3)]
        report['datasets'][ds]=record
        print(ds,'ANALYZED',chosen['selected'],record['validation']['pooled_L64_L128']['stats'],flush=True)
    dump(RUN/'results/analysis.json',report)
    rows=[{k:v for k,v in c.items() if not isinstance(v,(dict,list))} for c in report['comparisons']]
    with (RUN/'results/comparisons.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    frozen_check('audit')
    print('E26_ANALYSIS_COMPLETE',flush=True)


if __name__=='__main__':main()
