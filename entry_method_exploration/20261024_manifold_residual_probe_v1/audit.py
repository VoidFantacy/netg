#!/usr/bin/env python3
"""Second stdlib implementation for paired ID sets, ranks, and adjusted contrasts."""
from pathlib import Path
import csv,hashlib,json,math,statistics,struct,time
R=Path(__file__).resolve().parent;A=R/'analysis'
E=R.parent/'20261017_gt10_residual_comprehensive_v1';G=R.parent/'20261024_residual_geometry_diagnosis_v1'
def rows(p):return list(csv.DictReader(p.open()))
def getter(d):
    raw=Path(d['path']).read_bytes();n=d['n'];k=d.get('width',d.get('k',100));start=d.get('row_start',0)
    head=int(d['format']=='ivecs');code='q' if d['format']=='raw_i64' else 'i';record=struct.Struct('<'+str(k+head)+code)
    def get(i):
        assert 0<=i<n;v=record.unpack_from(raw,(i+start)*record.size)
        if head:assert v[0]==k
        return v[head:head+100]
    return get
def packet(p,k):
    raw=p.read_bytes();st=struct.Struct('<'+str(k)+'i')
    return lambda i:st.unpack_from(raw,i*st.size)
def ranks(values):
    order=sorted(range(len(values)),key=values.__getitem__);r=[0.]*len(values);i=0
    while i<len(order):
        j=i+1
        while j<len(order) and values[order[j]]==values[order[i]]:j+=1
        for k in range(i,j):r[order[k]]=(i+1+j)/2
        i=j
    return r
def correlation(x,y):
    if len(set(x))<2 or len(set(y))<2:return None
    x=ranks(x);y=ranks(y);mx=statistics.mean(x);my=statistics.mean(y)
    vx=sum((v-mx)**2 for v in x);vy=sum((v-my)**2 for v in y)
    return sum((a-mx)*(b-my) for a,b in zip(x,y))/math.sqrt(vx*vy)
def adjusted(records,feature,control,minimum):
    freq=[float(v['residual_frequency']) for v in records];fb=[min(int((r-1)*4/len(records)),3) for r in ranks(freq)]
    used=0;strata=0;effect=0.;gain=0.
    for lo,hi in [(0,9),(10,49),(50,79),(80,89),(90,94),(95,99)]:
        for band in (range(4) if control.endswith('frequency') else [None]):
            ii=[i for i,v in enumerate(records) if lo<=int(v['GT_hits'])<=hi and (band is None or fb[i]==band)]
            if not ii:continue
            threshold=statistics.median(float(records[i][feature]) for i in ii)
            low=[i for i in ii if float(records[i][feature])<=threshold];high=[i for i in ii if float(records[i][feature])>threshold]
            if min(len(low),len(high))<minimum:continue
            delta=lambda ids:statistics.mean(int(records[i]['net_gain']) for i in ids)
            probability=lambda ids:sum(int(records[i]['net_gain'])>0 for i in ids)/len(ids)
            used+=len(ii);strata+=1;effect+=len(ii)*(probability(high)-probability(low));gain+=len(ii)*(delta(high)-delta(low))
    return used,strata,100*effect/used if used else None,gain/used if used else None
def checkfloat(actual,expected):
    if actual=='':assert expected is None
    else:assert expected is not None and abs(float(actual)-expected)<1e-9,(actual,expected)

def main():
    began=time.perf_counter();qq=rows(A/'sample_query_metrics.csv');ss=rows(A/'dataset_summary.csv')
    aa=rows(A/'adjusted_associations.csv');cc=rows(A/'within_dataset_correlations.csv')
    existing=rows(G/'analysis/query_metrics.csv');checks=[]
    aliases={'nearest_training_GT_overlap':'nearest_GT_overlap','nearest_training_query_distance':'nearest_query_distance'}
    for summary in ss:
        ds=summary['dataset'];q=[v for v in qq if v['dataset']==ds];assert len(q)==512
        cfg=json.loads((E/f'configs/{ds}.analysis.json').read_text());c=cfg['catalogue_entry']
        gt=getter(c['test_gt']);tg=getter(c['train_gt']);rt='soft' if ds in ['deep10m_l2_v1','sift10m_bigann_l2_v1','webvid2_5m_light_v1'] else 'hard'
        gm='GT10-soft-t1' if rt=='soft' else 'GT10-hard';teacher=Path(cfg['models'][rt]['teacher_dir'])
        train=packet(teacher/'raw/ids.i32',100);troute=packet(teacher/'raw/entry_ids.i32',3)
        baseline=packet(E/f'results/{ds}/k100/{gm}_L200/raw/ids.i32',100)
        post=packet(E/f'results/{ds}/k100/{rt}-JOINT32_L200/raw/ids.i32',100)
        route=packet(E/f'results/{ds}/k100/{gm}_L200/raw/entry_ids.i32',3)
        for r in q:
            qi=int(r['query_row']);truth=set(gt(qi));found=truth&set(baseline(qi));missing=truth-found;final=truth&set(post(qi))
            assert len(found)==int(r['GT_hits']) and len(final)-len(found)==int(r['net_gain'])
            assert len(missing)==int(r['missing_count'])
            for prefix in ['nearest','random','matched']:
                i=int(r[prefix+'_train_row']);target=set(tg(i));miss=target-set(train(i))
                assert len(truth&target)==int(r[prefix+'_GT_overlap'])
                assert len(missing&miss)==int(r[prefix+'_missing_covered'])
            vr=set(route(qi));near=int(r['nearest_train_row']);match=int(r['matched_train_row'])
            assert len(vr&set(troute(near)))==len(vr&set(troute(match)))==int(r['nearest_route_overlap'])
        den=sum(int(v['missing_count']) for v in q)
        for prefix in ['nearest','random','matched']:
            checkfloat(summary[prefix+'_GT_overlap_pct'],statistics.mean(int(v[prefix+'_GT_overlap']) for v in q))
            checkfloat(summary[prefix+'_missing_coverage_pct'],100*sum(int(v[prefix+'_missing_covered']) for v in q)/max(den,1))
        for x in [v for v in cc if v['dataset']==ds]:
            feature=aliases.get(x['feature'],x['feature']);xx=[float(v[feature]) for v in q]
            if x['outcome']=='baseline_missing':yy=[100-int(v['GT_hits']) for v in q]
            elif x['outcome']=='net_gain':yy=[int(v['net_gain']) for v in q]
            elif x['outcome']=='improved':yy=[int(v['net_gain'])>0 for v in q]
            else:yy=[int(v['nearest_missing_covered'])/max(int(v['missing_count']),1) for v in q]
            checkfloat(x['spearman'],correlation(xx,yy))
        full=[]
        for r in existing:
            if r['dataset']!=ds:continue
            full.append({**r,'GT_hits':r['GT_K100_hits'],'net_gain':r['K100_net_delta'],'residual_frequency':r['GT100_mean_residual_frequency']})
        for x in [v for v in aa if v['dataset']==ds]:
            sample=x['scope']=='fixed_512_sample';records=q if sample else full;feat=aliases.get(x['feature'],x['feature'])
            used,k,eff,gain=adjusted(records,feat,x['control'],4 if sample else 8)
            assert used==int(x['included_queries']) and k==int(x['strata'])
            checkfloat(x['improved_probability_high_minus_low_pp'],eff);checkfloat(x['mean_recall_gain_high_minus_low_pp'],gain)
        checks.append(dict(dataset=ds,paired_queries=512,status='PASS'))
        print('AUDIT',ds,flush=True)
    inputs=json.loads((A/'inputs_manifest.json').read_text())
    for path,v in inputs['small_inputs'].items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==v['sha256']
    for path,v in inputs['inherited_big_inputs'].items():
        p=Path(path);assert p.stat().st_size==v['bytes'] and p.stat().st_mtime_ns==v['mtime_ns']
    result=dict(status='PASS_SECOND_STDLIB_SET_RANK_STRATA_IMPLEMENTATION',paired_queries=3584,
        paired_GT_missing_comparisons=10752,correlations=len(cc),adjusted_associations=len(aa),
        independent_author=False,numpy_imported=False,bootstrap_not_independently_recomputed=True,
        local_geometry_gram_svd_and_neighbor_direct_checks='see receipt.json; separate algebra same main process',
        input_identities_unchanged=True,seconds=time.perf_counter()-began,checks=checks)
    (A/'audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(result['status'],result['seconds'])
if __name__=='__main__':main()
