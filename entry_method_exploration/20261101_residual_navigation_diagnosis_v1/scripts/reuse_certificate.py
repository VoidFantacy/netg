from common import *
import gzip,collections
t=time.perf_counter();summary=[];violations=[]
for ds in DS:
    for w in ['A','B']:
        c=read(R/'configs'/f'{ds}.{w}.json');root=Path(c['output_dir']);n=c['queries']['n'];cache={};stats=collections.defaultdict(collections.Counter)
        with gzip.open(root/'C_nodes.csv.gz','rt') as f:
            for a in csv.DictReader(f):
                K,L,i=int(a['K']),int(a['L']),int(a['query']);key=K,L
                if key not in cache:cache[key]=np.fromfile(root/f'k{K}/GT10_L{L}/raw/distances.f32','<f4').reshape(n,K)
                v=np.float32(float(a['score']));bound=cache[key][i,-1];ss=stats[key];ss['C_scored']+=1;ss['C_already_main_seen']+=int(a['main_seen']);ss['C_correct']+=int(a['is_GT'])
                if a['main_seen']=='1':
                    ss['C_main_seen_and_correct']+=int(a['is_GT']);ss['score_equal_threshold']+=v==bound
                    if v<bound:violations.append(dict(dataset=ds,window=w,K=K,L=L,query=i,target=int(a['target']),score=float(v),main_threshold=float(bound)))
        for (K,L),a in stats.items():summary.append(dict(dataset=ds,window=w,K=K,L=L,**{k:a[k] for k in ['C_scored','C_already_main_seen','C_correct','C_main_seen_and_correct','score_equal_threshold']},already_seen_fraction=a['C_already_main_seen']/a['C_scored'] if a['C_scored'] else 0))
csvwrite(R/'analysis/C_redundant_scoring.csv',summary)
if violations:csvwrite(R/'analysis/C_redundancy_violations.csv',violations)
dump(R/'analysis/C_reuse_certificate.json',dict(status='PASS_SEEN_C_NONIMPROVING_CERTIFICATE' if not violations else 'FAIL_SEEN_C_NONIMPROVING_CERTIFICATE',checked_C_events=sum(x['C_scored'] for x in summary),already_seen_events=sum(x['C_already_main_seen'] for x in summary),strictly_better_than_main_threshold_violations=len(violations),seconds=time.perf_counter()-t,scope='finite original scalar main results and fresh C words, K1/K100 L100/200/400 two exposed windows; no optimized online implementation or QPS measured',proof='With finite stateless scores and exact top-L maintenance, a main-seen C excluded from returned top-K cannot strictly improve the terminal K threshold; removing such no-op merge events preserves surviving arrival order. General deployment guards and end-to-end timing remain separate.'))
print('C_CERTIFICATE',len(violations),flush=True)
