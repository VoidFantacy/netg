import sys
from pathlib import Path
RUN=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(RUN/'src'))
from common import *
import csv,resource
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def table(path,rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def bootstrap(delta):
    # The input is one paired observation per query, including all zero differences.
    rng=np.random.default_rng(LOCK['bootstrap_seed']);B=LOCK['bootstrap_replicates'];means=np.empty(B)
    for lo in range(0,B,128):
        ix=rng.integers(len(delta),size=(min(128,B-lo),len(delta)));means[lo:lo+len(ix)]=delta[ix].mean(1)
    return dict(CI95=np.quantile(means,[.025,.975]).tolist(),CI98_75=np.quantile(means,[.00625,.99375]).tolist())

assert read(RUN/'reviews/search_complete.json')['status']=='PASS'
assert not (RUN/'reviews/analysis_complete.json').exists(),'preserve analysis output'
start=time.time();protected_check();methods=read(RUN/'models/methods.json');metrics=[];pairs=[];primary=[];mechanism=[];failures=[];aligned={};verification=[]
dump(RUN/'reviews/analysis_source_lock.json',dict(created_unix=time.time(),source=identity(Path(__file__)),config=identity(RUN/'config.locked.json')))
for ds,c in LOCK['datasets'].items():
    inp=RUN/'inputs'/ds;n=LOCK['evaluation_n'];d=c['dimension'];h=c['H'];manifest=read(inp/'manifest.json')
    for name,digest in manifest['files'].items():assert sha(inp/name)==digest
    gt=np.fromfile(inp/'gt.i32','<i4').reshape(n,100);q=np.fromfile(inp/'queries.f32','<f4').reshape(n,d);rows=np.fromfile(inp/'source_rows.i64','<i8')
    assert len(np.unique(rows))==n and np.all(np.diff(np.sort(gt,axis=1),axis=1)>0)
    basepath=read(c['evaluation_manifest'])['base'];base=np.memmap(basepath,dtype='<f4',mode='r').reshape(c['base_n'],d+1)[:,1:]
    hubids=np.fromfile(Path(c['fit_input'])/'hub_ids.i32','<i4');cache={};entries={};files=[]
    for m in methods[ds]:
        name=m['name'];p=RUN/'results'/ds/name;done=read(p/'complete.json');assert done['n']==n and done['K']==[1,100] and done['L']==128 and done['plain_count_bit_parity']
        e=np.fromfile(p/'entries.i32','<i4').reshape(n,3);assert np.all(np.diff(e,axis=1)>0) and np.isin(e,hubids).all();entries[name]=e
        if m['route']=='exact':
            w=np.fromfile(m['W'],'<f4').reshape(h,d)
            for i in range(0,n,256):
                score=w.astype('float64')@q[i].astype('float64');selected=np.searchsorted(hubids,e[i]);bound=np.partition(score,-3)[-3]
                tol=2e-6*max(1.,float(np.linalg.norm(q[i])))
                assert score[selected].min()>=bound-tol,'independent full-H score ranking'
        rn=np.fromfile(p/'route_ndc.u64','<u8');assert rn.shape==(n,)
        for K in LOCK['K']:
            ids=np.fromfile(p/f'k{K}.ids.i32','<i4').reshape(n,K);dist=np.fromfile(p/f'k{K}.distances.f32','<f4').reshape(n,K);ndc=np.fromfile(p/f'k{K}.ndc.u64','<u8')
            assert ndc.shape==(n,) and np.isfinite(dist).all() and np.all((ids>=0)&(ids<c['base_n'])) and np.all(np.diff(dist,axis=1)>=0)
            assert K==1 or np.all(np.diff(np.sort(ids,axis=1),axis=1)>0)
            hits=(ids[:,:,None]==gt[:,None,:K]).any(2).sum(1).astype('int16')
            independent=np.array([len(set(ids[i])&set(gt[i,:K])) for i in range(n)],dtype='int16');assert np.array_equal(hits,independent)
            for i in range(0,n,512):
                exact=-np.sum(base[ids[i]].astype('float64')*q[i].astype('float64'),axis=1)
                assert np.allclose(exact,dist[i],atol=2e-5,rtol=2e-5),'independent raw-IP distances'
            cache[(name,K)]=(hits,ids,dist.view('u4'),ndc)
            metrics.append(dict(dataset=ds,method=name,family=m['family'],kind=m['kind'],route=m['route'],K=K,L=128,n=n,recall=float(hits.mean()/K),failed_queries=int((hits==0).sum()),graph_ndc=float(ndc.mean()),route_ndc=float(rn.mean()),formal_QPS=False))
            aligned[ds+'__'+name+'__K'+str(K)]=hits
        files.extend(identity(f) for f in p.iterdir() if f.is_file())
    # Check every duplicate query/entry combination across all methods.
    for K in LOCK['K']:
        seen={}
        for m in methods[ds]:
            name=m['name'];hit,ids,bits,ndc=cache[(name,K)]
            for i,e in enumerate(entries[name]):
                key=(i,*map(int,e));value=(ids[i].tobytes(),bits[i].tobytes(),int(ndc[i]))
                if key in seen:assert seen[key]==value,'same entries changed output/cost'
                else:seen[key]=value
    for family in c['families']:
        title=family.title();original=title+'OriginalExact';candidate=title+'GroupMeanExact'
        for K in LOCK['K']:
            original_hits=cache[(original,K)][0];candidate_hits=cache[(candidate,K)][0];default=cache[('DefaultANN',K)][0]
            difference=(candidate_hits.astype('float64')-original_hits)/K*100
            row=dict(dataset=ds,family=family,K=K,L=128,baseline_recall=float(original_hits.mean()/K),candidate_recall=float(candidate_hits.mean()/K),delta_recall_pp=float(difference.mean()),delta_vs_current_ANN_pp=float(((candidate_hits.astype(float)-default)/K*100).mean()),baseline_failed=int((original_hits==0).sum()),candidate_failed=int((candidate_hits==0).sum()),rescued=int(((original_hits==0)&(candidate_hits>0)).sum()),newly_harmed=int(((original_hits>0)&(candidate_hits==0)).sum()),first_half_delta_pp=float(difference[:n//2].mean()),second_half_delta_pp=float(difference[n//2:].mean()),same_entries=int(np.all(entries[original]==entries[candidate],axis=1).sum()),delta_graph_ndc_pct=float((cache[(candidate,K)][3].mean()/cache[(original,K)][3].mean()-1)*100),**bootstrap(difference))
            assert row['rescued']-row['newly_harmed']==row['baseline_failed']-row['candidate_failed']
            pairs.append(row)
            if family==('soft' if ds.startswith('webvid') else 'hard'):primary.append(row)
            perm_hits=np.stack([cache[(title+f'Perm{j}Exact',K)][0] for j in range(4)])
            delta=(original_hits-perm_hits.mean(0))/K*100
            seed_deltas=((original_hits[None,:]-perm_hits)/K*100).mean(1)
            record=dict(dataset=ds,family=family,K=K,L=128,real_minus_permutation_mean_pp=float(delta.mean()),real_minus_each_permutation_pp=seed_deltas.tolist(),all_four_directions_positive=bool((seed_deltas>0).all()),CI95_descriptive=bootstrap(delta)['CI95'],seed_count=4,query_count=n,interpretation='Fixed-intervention paired query uncertainty; not a conditional-independence p-value or independent query replication.')
            mechanism.append(record)
            for i in np.flatnonzero((original_hits==0)|(candidate_hits==0)):
                failures.append(dict(dataset=ds,family=family,K=K,L=128,position=int(i),source_row=int(rows[i]),original_hits=int(original_hits[i]),candidate_hits=int(candidate_hits[i]),current_default_ANN_hits=int(default[i]),rescued=bool(original_hits[i]==0 and candidate_hits[i]>0),newly_harmed=bool(original_hits[i]>0 and candidate_hits[i]==0)))
    aligned[ds+'__source_rows']=rows
    verification.append(dict(dataset=ds,methods=len(methods[ds]),query_count=n,independent_set_scoring_queries_per_point=n,float64_distance_queries_per_point=8,float64_full_H_ranking_queries_per_exact_method=16,all_same_entries_same_ID_distance_bits_NDC=True,files=files))
    print(ds,'independent scoring complete',flush=True)
gate=[]
for ds in LOCK['datasets']:
    pp=[r for r in primary if r['dataset']==ds]
    passed=all(r['delta_recall_pp']>=0 for r in pp) and any(r['delta_recall_pp']>=.5 for r in pp) and any(r['CI98_75'][0]>0 for r in pp)
    gate.append(dict(dataset=ds,quality_pass=passed))
status='PASS_GROUPMEAN_EXACT_DEVELOPMENT' if all(r['quality_pass'] for r in gate) else 'STOP_GROUPMEAN_CANDIDATE'
table(RUN/'results/metrics.csv',metrics);table(RUN/'results/candidate_pairs.csv',pairs);table(RUN/'results/failure_queries.csv',failures)
dump(RUN/'results/primary.json',primary);dump(RUN/'results/mechanism.json',mechanism)
np.savez_compressed(RUN/'results/aligned_hits.npz',**aligned)
dump(RUN/'reviews/decision.json',dict(status=status,datasets=gate,primary=primary,mechanism=mechanism,default_changed=False))
dump(RUN/'reviews/numeric_verification.json',dict(status='PASS',method_points=len(metrics),source=identity(Path(__file__)),datasets=verification,seconds=time.time()-start))
fig,axes=plt.subplots(1,3,figsize=(13,4),constrained_layout=True)
families=[(ds,f) for ds,c in LOCK['datasets'].items() for f in c['families']]
for ax,(ds,family) in zip(axes,families):
    for j,K in enumerate([1,100]):
        r=next(x for x in pairs if x['dataset']==ds and x['family']==family and x['K']==K)
        val=r['delta_recall_pp'];lo,hi=r['CI98_75'];ax.errorbar(j,val,yerr=[[max(0,val-lo)],[max(0,hi-val)]],fmt='o',capsize=4,color='#db6b35')
    ax.axhline(0,color='gray',ls='--');ax.set_xticks([0,1],['Recall@1','Recall@100']);ax.set_title(('WebVid' if ds.startswith('webvid') else 'Yandex')+' | '+family);ax.set_ylabel('GroupMean minus original (pp)');ax.grid(alpha=.2)
fig.suptitle('Conditional aggregation | exact profile routing, real NSG L=128\n98.75% paired query intervals; Web hard is auxiliary')
for ext in ['png','pdf']:fig.savefig(RUN/'figures'/('groupmean_quality.'+ext),dpi=170)
plt.close(fig)
fig,axes=plt.subplots(1,3,figsize=(13,4),constrained_layout=True)
for ax,(ds,family) in zip(axes,families):
    for j,K in enumerate([1,100]):
        r=next(x for x in mechanism if x['dataset']==ds and x['family']==family and x['K']==K)
        ax.scatter(np.full(4,j)+np.linspace(-.09,.09,4),r['real_minus_each_permutation_pp'],s=22,color='#386eac')
        v=r['real_minus_permutation_mean_pp'];lo,hi=r['CI95_descriptive'];ax.errorbar(j,v,yerr=[[max(0,v-lo)],[max(0,hi-v)]],fmt='D',color='#152d49',capsize=4)
    ax.axhline(0,color='gray',ls='--');ax.set_xticks([0,1],['Recall@1','Recall@100']);ax.set_title(('WebVid' if ds.startswith('webvid') else 'Yandex')+' | '+family);ax.set_ylabel('Original minus conditional permutation (pp)');ax.grid(alpha=.2)
fig.suptitle('Does within-GT1 query-target correspondence help?\nDots: 4 fixed permutations; diamonds: mean and descriptive paired 95% interval')
for ext in ['png','pdf']:fig.savefig(RUN/'figures'/('conditional_correspondence.'+ext),dpi=170)
plt.close(fig)
protected_check();dump(RUN/'reviews/analysis_complete.json',dict(status='PASS',method_decision=status,created_unix=time.time(),seconds=time.time()-start))
print(json.dumps(dict(status=status,gates=gate,primary=primary,mechanism=mechanism),ensure_ascii=False,indent=2))
