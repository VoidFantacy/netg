import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:
    os.environ[key]='1'
os.sched_setaffinity(0,{15})
from pathlib import Path
import json, struct, hashlib, time, csv, math, itertools, resource
from fractions import Fraction
import numpy as np

R=Path(__file__).resolve().parents[1]
started=time.time()
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(16<<20),b''):h.update(b)
    return h.hexdigest()
def ident(p):p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
def write(p,rows,fields=None):
    with Path(p).open('x') as f:
        w=csv.DictWriter(f,fieldnames=fields or list(rows[0]));w.writeheader();w.writerows(rows)
def native(path,n,d):
    with Path(path).open('rb') as f:
        def rd(fmt):return struct.unpack('<'+fmt,f.read(struct.calcsize('<'+fmt)))
        version,nn,dd,metric,trained,built,build=rd('iqii??c')
        assert version in (1,2) and nn==n and dd==d and metric==0 and trained and built
        rd('ffffiiiiiq')
        for _ in range(2):
            count,=rd('Q');assert count==n;f.seek(count*4,1)
        width,count=rd('iQ');assert count==n*width and 0<width<=64
        graph_offset=f.tell();f.seek(count*4,1)
        count,=rd('Q');assert count==n*d;vector_offset=f.tell()
    return (np.memmap(path,mode='r',dtype='<i4',offset=graph_offset,shape=(n,width)),
            np.memmap(path,mode='r',dtype='<f4',offset=vector_offset,shape=(n,d)))
def exact_margin(q,x,y):
    return sum((Fraction(float(a))*(Fraction(float(b))-Fraction(float(c)))
                for a,b,c in zip(q,x,y)),Fraction(0))
def tick():
    assert time.time()-started<580 and time.time()<cfg['deadline_unix']
    assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss<40*1024**2

cfg=read(R/'config.locked.json')
assert not (R/'reviews/numeric_verification.json').exists()
for x in read(R/'reviews/source_freeze.json')['files']:
    assert sha(x['path'])==x['sha256'],x['path']
all_methods=[];all_pairs=[];all_datasets=[];exceptions=[];verification=[]
input_identities=read(R/'reviews/input_sources.json')['files']
for x in input_identities:assert sha(x['path'])==x['sha256'],x['path']
for ds,c in cfg['datasets'].items():
    tick();local_start=time.time();p=R/'results'/ds;p.mkdir()
    n=c['n'];d=c['dimension'];graph,base=native(c['index'],c['base_n'],d)
    stat=Path(c['index']).stat()
    assert stat.st_size==c['index_stat']['bytes'] and stat.st_mtime_ns==c['index_stat']['mtime_ns']
    q=np.fromfile(c['queries'],'<f4').reshape(n,d)
    gt=np.fromfile(c['GT'],'<i4').reshape(n,100)[:,0]
    names=[m['name'] for m in c['methods']]
    ids=np.stack([np.fromfile(m['ids'],'<i4') for m in c['methods']],axis=1)
    old_dist=np.stack([np.fromfile(m['distances'],'<f4') for m in c['methods']],axis=1)
    assert ids.shape==(n,8) and old_dist.shape==(n,8)
    assert np.all(ids>=0) and np.all(ids<c['base_n']) and np.all(np.isfinite(old_dist))
    hit=(ids==gt[:,None]);peak_lookup=np.empty((n,8),'<i4');records=[]
    certified_negative=uncertain_exact=independent_edges=0;max_independent_error=0.
    exact_sign_checked=distance_evaluations=edges=0
    for i in range(n):
        if i%128==0:tick()
        qi=q[i].astype('f8');aq=np.abs(qi);qnorm=float(np.linalg.norm(qi))
        gtvec=base[int(gt[i])].copy();gtscore=float(qi@gtvec.astype('f8'))
        for peak in np.unique(ids[i]):
            peak=int(peak);x32=base[peak].copy();x=x32.astype('f8');score=float(qi@x)
            row=np.unique(np.asarray(graph[peak]));assert np.all(row<c['base_n'])
            row=row[(row>=0)&(row!=peak)]
            nb32=base[row].copy();nb=nb32.astype('f8');ns=nb@qi
            assert np.all(np.isfinite(qi)) and np.all(np.isfinite(x)) and np.all(np.isfinite(nb))
            margin=score-ns
            diff=x[None,:]-nb;norm=np.linalg.norm(diff,axis=1)
            identical=np.all(nb32.view('<u4')==x32.view('<u4'),axis=1)
            # Float32 products are exactly representable in float64.  This
            # deliberately loose bound covers summation and subtraction.
            gamma=((2*d+3)*2.0**-53)/(1-(2*d+3)*2.0**-53)
            bound=2*gamma*(float(aq@np.abs(x))+np.abs(nb)@aq)
            signs=np.where(margin>bound,1,np.where(margin < -bound,-1,0)).astype('i1')
            signs[identical]=0
            candidates=np.flatnonzero((~identical)&(margin<=bound))
            exact_values={}
            for j in candidates:
                value=exact_margin(q[i],x32,nb32[j]);sgn=(value>0)-(value<0)
                assert sgn in (-1,0,1)
                if margin[j] < -bound[j]:certified_negative+=1;assert sgn==-1
                else:uncertain_exact+=1
                signs[j]=sgn;exact_values[int(j)]=value;exact_sign_checked+=1
                exceptions.append(dict(dataset=ds,query=i,peak=peak,neighbor=int(row[j]),
                    margin_float64=float(margin[j]),bound=float(bound[j]),exact_sign=sgn,
                    exact_numerator=str(value.numerator),exact_denominator=str(value.denominator)))
            if i in cfg['independent_query_positions']:
                ref_score=math.fsum(float(a)*float(b) for a,b in zip(q[i],x32))
                for j in range(len(row)):
                    ref=ref_score-math.fsum(float(a)*float(b) for a,b in zip(q[i],nb32[j]))
                    err=abs(ref-float(margin[j]));max_independent_error=max(max_independent_error,err)
                    assert err<=float(bound[j])+np.finfo('f8').tiny
                    independent_edges+=1
            nonzero=norm>0
            radius=None if not nonzero.any() else float(np.min(margin[nonzero]/norm[nonzero]))
            exact_negative=int((signs<0).sum())
            r=dict(query=i,peak=peak,GT1=int(gt[i]),hit=int(peak==gt[i]),neighbors=len(row),
                   improving_neighbors_exact=exact_negative,equal_vector_neighbors=int(identical.sum()),
                   min_margin_float64=None if not len(row) else float(margin.min()),
                   radius_float64=radius,radius_over_query_norm=None if radius is None else radius/qnorm,
                   query_norm=qnorm,peak_score_float64=score,GT1_score_float64=gtscore,
                   GT1_gap_float64=gtscore-score,
                   GT1_same_vector_bits=bool(np.array_equal(x32.view('<u4'),gtvec.view('<u4'))))
            peak_lookup[i,ids[i]==peak]=len(records);records.append(r)
            edges+=len(row);distance_evaluations+=len(row)+2
    write(p/'query_peaks.csv',records);peak_lookup.tofile(p/'method_peak_rows.i32')
    rows_arr=np.asarray([[records[int(peak_lookup[i,j])]['peak_score_float64'] for j in range(8)] for i in range(n)])
    same_vector=np.empty((n,8,8),bool)
    for a,b in itertools.product(range(8),repeat=2):
        same_vector[:,a,b]=[np.array_equal(base[int(x)].view('<u4'),base[int(y)].view('<u4')) for x,y in zip(ids[:,a],ids[:,b])]
    for j,name in enumerate(names):
        rr=[records[int(v)] for v in peak_lookup[:,j]]
        radii=[x['radius_float64'] for x in rr if x['radius_float64'] is not None]
        all_methods.append(dict(dataset=ds,method=name,n=n,recall1_pct=100*float(hit[:,j].mean()),
            failed_queries=int((~hit[:,j]).sum()),violating_query_peaks=sum(x['improving_neighbors_exact']>0 for x in rr),
            zero_or_negative_radius_queries=sum(x['radius_float64'] is not None and x['radius_float64']<=0 for x in rr),
            no_nonzero_edge_queries=sum(x['radius_float64'] is None for x in rr),
            radius_p10=float(np.quantile(radii,.1)),radius_median=float(np.median(radii)),radius_p90=float(np.quantile(radii,.9)),
            wrong_ID_same_GT1_vector=sum(not x['hit'] and x['GT1_same_vector_bits'] for x in rr),
            old_distance_plus_reference_score_max_abs=float(np.max(np.abs(old_dist[:,j].astype('f8')+rows_arr[:,j])))))
    for a,b in itertools.combinations(range(8),2):
        both_fail=(~hit[:,a])&(~hit[:,b]);different=ids[:,a]!=ids[:,b]
        change=rows_arr[:,b]-rows_arr[:,a]
        all_pairs.append(dict(dataset=ds,method_a=names[a],method_b=names[b],n=n,
            same_peak_ID=int((~different).sum()),same_peak_vector=int(same_vector[:,a,b].sum()),
            b_rescues_a=int((hit[:,b]&~hit[:,a]).sum()),b_harms_a=int((~hit[:,b]&hit[:,a]).sum()),
            both_failed=int(both_fail.sum()),both_failed_different_ID=int((both_fail&different).sum()),
            both_failed_b_higher_float64=int((both_fail&different&(change>0)).sum()),
            both_failed_b_lower_float64=int((both_fail&different&(change<0)).sum()),
            both_failed_float64_equal=int((both_fail&different&(change==0)).sum())))
    diversity=np.asarray([len(set(row.tolist())) for row in ids]);default=names.index('DefaultANN')
    diversity_rows=[dict(query=i,distinct_terminal_IDs=int(diversity[i]),default_hit=int(hit[i,default]),
                         any_of_eight_hit=int(hit[i].any()),all_eight_hit=int(hit[i].all())) for i in range(n)]
    write(p/'query_diversity.csv',diversity_rows)
    summary=dict(dataset=ds,n=n,method_rows=n*8,unique_query_peaks=len(records),out_edges_checked=edges,
        reference_inner_products=distance_evaluations,violating_unique_query_peaks=sum(x['improving_neighbors_exact']>0 for x in records),
        error_bound_certified_negative_edges=certified_negative,
        exact_negative_edges=sum(x['improving_neighbors_exact'] for x in records),
        uncertain_nonidentical_edges_exact_checked=uncertain_exact,
        exact_sign_checks=exact_sign_checked,independent_edges=independent_edges,
        maximum_independent_margin_error=max_independent_error,
        all_eight_same_terminal_ID=int((diversity==1).sum()),all_eight_same_terminal_ID_pct=100*float((diversity==1).mean()),
        default_failures=int((~hit[:,default]).sum()),
        default_failed_all_eight_same_terminal_ID=int(((~hit[:,default])&(diversity==1)).sum()),
        no_preset_method_hits=int((~hit.any(axis=1)).sum()),any_preset_method_hits=int(hit.any(axis=1).sum()),
        any_preset_method_recall1_pct=100*float(hit.any(axis=1).mean()),
        max_distinct_terminal_IDs=int(diversity.max()),median_distinct_terminal_IDs=float(np.median(diversity)),
        seconds=time.time()-local_start)
    dump(p/'summary.json',summary);all_datasets.append(summary)
    verification.append(dict(dataset=ds,independent_query_positions=cfg['independent_query_positions'],independent_edges=independent_edges))
    print(json.dumps(summary,ensure_ascii=False),flush=True)
    del base,graph,q,ids,old_dist,rows_arr,same_vector
write(R/'results/methods.csv',all_methods);write(R/'results/pairs.csv',all_pairs)
write(R/'results/exact_edge_checks.csv',exceptions,fields=['dataset','query','peak','neighbor','margin_float64','bound','exact_sign','exact_numerator','exact_denominator'])
dump(R/'results/summary.json',all_datasets)
original=list(csv.DictReader(Path(cfg['original_metrics']).open()))
for row in all_methods:
    matched=[x for x in original if x['dataset']==row['dataset'] and x['method']==row['method'] and int(x['K'])==1 and int(x['L'])==128]
    assert len(matched)==1
    # Actual CSV schema is fixed in setup, rather than inferred from quality.
    assert abs(float(matched[0][cfg['recall_column']])*cfg['recall_multiplier']-row['recall1_pct'])<1e-9
    assert int(matched[0][cfg['failed_column']])==row['failed_queries']
for x in input_identities:assert sha(x['path'])==x['sha256'],x['path']
tick()
dump(R/'reviews/numeric_verification.json',dict(status='PASS',source=ident(__file__),
    all_original_16_metrics_restored=True,independent_checks=verification,
    input_files_checked=len(input_identities),NSG_calls=0,ANN_calls=0,new_GT=0,new_graphs=0,new_training=0,
    seconds=time.time()-started,maxrss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    result_files=[ident(p) for p in (R/'results').rglob('*') if p.is_file()]))
dump(R/'state.json',dict(status='NUMERIC_REVIEW_COMPLETE',pending=['interpretation','report and closeout'],NSG_calls=0))
