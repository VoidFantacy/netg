"""Recompute all Recall@1/100, verify raw outputs, and render measured curves."""
from common import *
import csv, math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

LOCK=json.loads((RUN/'config.locked.json').read_text())
LABELS={'webvid2_5m_light_v1':'WebVid 2.505M · IP','yandex_t2i_official10M_ip_v1':'Yandex 10M · IP','deep10m_l2_v1':'Deep 10M · L2','sift10m_bigann_l2_v1':'BIGANN-SIFT 10M · L2','gist1m_l2_v1':'GIST 1M · L2'}
ORDER=['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1','deep10m_l2_v1','sift10m_bigann_l2_v1','gist1m_l2_v1']
COLORS={'NSG':'#697782','GT10-hard':'#157a6e','GT10-soft-t1':'#4c78a8','GATE':'#d65f36','HNSW':'#9b61a8'}
DISPLAY={'NSG':'NSG','GT10-hard':'GT10 hard','GT10-soft-t1':'GT10 soft (fixed T)','GATE':'GATE (corrected)','HNSW':'Full HNSW'}

def csvfile(path,rows):
    with open(path,'w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def wilson(f,n):
    p=f/n;z=1.96;den=1+z*z/n;center=(p+z*z/(2*n))/den;rad=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return max(0,center-rad),min(1,center+rad)

def analyze():
    rows=[];paired=[];rounds=[];cross=[];hits_all={};costs=[]
    for ds in DATASETS:
        inp=RUN/'inputs'/ds;c=json.loads((inp/'manifest.json').read_text());n=c['test_rows'];base_n,d=c['shape'];base=vecs(c['paths']['base_path']);query=vecs(c['paths']['query_path']);gt=vecs(c['paths']['gt_path'],'i4')
        for k in LOCK['K']:
            root=RUN/'results'/ds/f'k{k}';done=json.loads((root/'complete.json').read_text());assert done['status']=='PASS' and done['K']==k and done['points']==80 and done['wall_rounds']==240 and done['process_threads']==1
            config=json.loads((root/'config.json').read_text());assert config==json.loads((inp/f'eval_k{k}.json').read_text())
            progress=json.loads((root/'timing_progress.json').read_text());assert len(progress)==240
            for p in progress:assert p['process_threads']==1 and p['formal'] and p['seconds']>0
            rounds.extend([dict(dataset=ds,K=k,**p) for p in progress])
            for L in LOCK['L'][str(k)]:
                for method in LOCK['methods']:
                    out=root/(method+'_L'+str(L));m=json.loads((out/'complete.json').read_text());assert m['K']==k and m['n']==n and m['metric_id']==c['metric_id'] and m['threads']==1 and m['plain_count_bit_parity'] and m['warmup_bit_parity'] and len(m['seconds'])==3
                    ids=np.fromfile(out/'ids.i32','i4').reshape(n,k);dist=np.fromfile(out/'distances.f32','f4').reshape(n,k);entries=np.fromfile(out/'entry_ids.i32','i4').reshape(n,3)
                    assert (ids>=0).all() and (ids<base_n).all() and np.isfinite(dist).all() and np.all(np.diff(np.sort(ids,axis=1),axis=1)>0)
                    assert np.all(np.diff(dist,axis=1)>=-1e-5),'results not distance sorted'
                    if method in ['NSG','HNSW']:assert (entries[:,1:]==-1).all()
                    else:
                        assert (entries>=0).all() and (entries<base_n).all() and np.all(np.diff(np.sort(entries,axis=1),axis=1)>0)
                        hubfile=inp/('gate.ids.i32' if method=='GATE' else 'gt10.ids.i32')
                        assert np.isin(entries,np.fromfile(hubfile,'i4')).all(),'router entry is not one of its real hubs'
                    if k==1:hits=(ids[:,0]==gt[:,0]).astype('i2')
                    else:
                        merged=np.sort(np.concatenate([ids,gt[:,:k]],axis=1),axis=1)
                        hits=(np.diff(merged,axis=1)==0).sum(axis=1).astype('i2')
                    assert (hits>=0).all() and (hits<=k).all();hits.tofile(out/'hits.i16');hits_all[(ds,k,method,L)]=hits
                    # Validate native metric and returned distances against raw base/query values.
                    probe=np.unique(np.linspace(0,n-1,8,dtype=int));vectors=np.asarray(base[ids[probe]],'f8');qq=np.asarray(query[probe],'f8')
                    expected=((vectors-qq[:,None,:])**2).sum(axis=2) if c['metric_id']==1 else -np.einsum('nkd,nd->nk',vectors,qq)+(1 if method=='HNSW' else 0)
                    np.testing.assert_allclose(dist[probe],expected,rtol=4e-5,atol=1e-4)
                    route=np.fromfile(out/'route_ndc.u64','u8');graph=np.fromfile(out/'graph_ndc.u64','u8');assert route.shape==graph.shape==(n,) and (graph>0).all()
                    if method in ['NSG','HNSW']:assert (route==0).all()
                    else:assert (route>=3).all()
                    seconds=np.asarray(m['seconds']);qps=n/seconds;failed=int((hits==0).sum());lo,hi=wilson(failed,n)
                    row=dict(dataset=ds,K=k,method=method,L=L,queries=n,recall=float(hits.mean()/k),qps_mean=float(qps.mean()),qps_min=float(qps.min()),qps_max=float(qps.max()),qps_from_mean_wall=float(n/seconds.mean()),failed_queries=failed,zero_hit_rate=failed/n,failure_wilson_lo=lo,failure_wilson_hi=hi,gt1_miss_rate=float((~np.any(ids==gt[:,:1],axis=1)).mean()),route_ndc_mean=float(route.mean()),graph_ndc_mean=float(graph.mean()),total_ndc_mean=float((route+graph).mean()),threads=1,metric_id=c['metric_id'])
                    for rep in range(3):
                        row[f'wall_round{rep+1}']=float(seconds[rep]);row[f'qps_round{rep+1}']=float(qps[rep])
                        pp=[p for p in progress if p['method']==method and p['L']==L and p['repeat']==rep];assert len(pp)==1 and pp[0]['seconds']==seconds[rep] and abs(pp[0]['qps']-qps[rep])<1e-7
                    rows.append(row)
                    if k==100 and L in LOCK['L']['1']:
                        old=RUN/'results'/ds/'k1'/(method+'_L'+str(L));a=np.fromfile(old/'ids.i32','i4');b=np.fromfile(old/'distances.f32','f4')
                        assert np.array_equal(b.view('u4'),dist[:,0].view('u4')) and np.array_equal(np.fromfile(old/'entry_ids.i32','i4').reshape(n,3),entries)
                        changed=a!=ids[:,0]
                        # hnswlib trims an internal-ID heap before converting to an
                        # external-ID heap; equal-distance ties may differ with K.
                        if changed.any():
                            assert method=='HNSW','unexpected NSG cross-K return difference'
                            qa=np.asarray(query[changed],'f8');va=np.asarray(base[a[changed]],'f8');vb=np.asarray(base[ids[changed,0]],'f8')
                            da=((va-qa)**2).sum(axis=1) if c['metric_id']==1 else -np.einsum('ij,ij->i',va,qa)
                            db=((vb-qa)**2).sum(axis=1) if c['metric_id']==1 else -np.einsum('ij,ij->i',vb,qa)
                            np.testing.assert_allclose(da,db,rtol=3e-6,atol=1e-7)
                        cross.append(dict(dataset=ds,method=method,L=L,top1_distance_and_entry_bit_parity=True,top1_ID_bit_parity=not bool(changed.any()),equal_distance_tie_ID_differences=int(changed.sum())))
                for reference in ['NSG','GT10-hard']:
                    a=hits_all[(ds,k,reference,L)]
                    for method in LOCK['methods']:
                        if method==reference:continue
                        b=hits_all[(ds,k,method,L)];paired.append(dict(dataset=ds,K=k,reference=reference,method=method,L=L,rescued_zero_hit=int(((a==0)&(b>0)).sum()),new_zero_hit=int(((a>0)&(b==0)).sum()),improved_queries=int((b>a).sum()),worsened_queries=int((b<a).sum()),equal_queries=int((b==a).sum()),recall_delta_pp=float((b.astype('f8')-a).mean()*100/k),comparison='same L/ef; not equal work'))
        del base,query,gt
        print('RAW_RESULTS_VERIFIED',ds,flush=True)
    assert len(rows)==800 and len(rounds)==2400
    csvfile(RUN/'results/metrics.csv',rows);csvfile(RUN/'results/wall_rounds.csv',rounds);csvfile(RUN/'results/paired_queries.csv',paired)
    targets=[]
    for ds in ORDER:
        for k in LOCK['K']:
            for target in [.5,.6,.7,.8,.9,.95,.99]:
                bests={}
                for method in LOCK['methods']:
                    rr=[r for r in rows if r['dataset']==ds and r['K']==k and r['method']==method and r['recall']>=target]
                    bests[method]=max(rr,key=lambda r:r['qps_mean']) if rr else None
                baseline=bests['NSG']
                for method,b in bests.items():
                    targets.append(dict(dataset=ds,K=k,target_recall=target,method=method,achieved=bool(b),measured_recall=b['recall'] if b else None,L=b['L'] if b else None,qps=b['qps_mean'] if b else None,speedup_over_NSG=(b['qps_mean']/baseline['qps_mean']) if b and baseline else None,rule='fastest measured point meeting threshold; no interpolation or extrapolation'))
    csvfile(RUN/'results/recall_targets.csv',targets)
    for p in sorted((RUN/'reviews').glob('stage_*.json')):
        r=json.loads(p.read_text());costs.append(dict(stage=r['stage'],seconds=r['seconds'],status=r['status'],log=r['log']))
    dump(RUN/'results/offline_and_evaluation_costs.json',costs)
    dump(RUN/'reviews/raw_results_verified.json',dict(status='PASS',points=len(rows),wall_rounds=len(rounds),cross_K_checks=cross,query_distance_probes_per_point=8,all_return_IDs_and_GT_scored=True,metrics_sha256=sha(RUN/'results/metrics.csv')))
    return rows,targets

def draw(rows):
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold'})
    for k in LOCK['K']:
        for failure in [False,True]:
            fig,axes=plt.subplots(2,3,figsize=(15,8.4));axes=axes.ravel()
            for ax,ds in zip(axes,ORDER):
                for method in LOCK['methods']:
                    rr=[r for r in rows if r['dataset']==ds and r['K']==k and r['method']==method]
                    x=[r['L'] if failure else r['recall']*100 for r in rr];y=[r['zero_hit_rate']*100 if failure else r['qps_mean'] for r in rr]
                    ax.plot(x,y,'o-',lw=1.6,ms=3.3,color=COLORS[method],label=DISPLAY[method])
                    if not failure:ax.fill_between(x,[r['qps_min'] for r in rr],[r['qps_max'] for r in rr],color=COLORS[method],alpha=.11)
                n=1000 if ds.startswith('gist') else 10000;ax.set_title(LABELS[ds]+f'\n{n:,} public queries',fontsize=11)
                ax.set_xlabel('Search budget L / ef' if failure else f'Recall@{k} (%)');ax.set_ylabel('Zero-hit queries (%)' if failure else 'Queries / second')
                if not failure:ax.set_yscale('log');ax.set_xlim(max(0,ax.get_xlim()[0]),min(100.4,max(ax.get_xlim()[1],99)))
                else:ax.set_ylim(bottom=0);ax.set_xscale('log')
                ax.grid(alpha=.2,which='both')
            handles,labels=axes[0].get_legend_handles_labels();axes[-1].axis('off');axes[-1].legend(handles,labels,loc='center',frameon=False,fontsize=12)
            note='Five datasets; LAION excluded. One CPU thread, 16 budgets, 3 timing repeats. GATE retrained with disjoint labels.'
            fig.suptitle(f'Recall@{k}: '+('zero-hit query rate' if failure else 'measured recall–throughput curves'),fontsize=17,y=.985)
            fig.text(.5,.015,note,ha='center',fontsize=10)
            fig.tight_layout(rect=[0,.045,1,.95]);stem=('failed_query_rate' if failure else 'recall_qps')+f'_k{k}'
            fig.savefig(RUN/'figures'/(stem+'.png'),dpi=210);fig.savefig(RUN/'figures'/(stem+'.pdf'));plt.close(fig)
        for ds in ORDER:
            fig,ax=plt.subplots(figsize=(7.6,5.3))
            for method in LOCK['methods']:
                rr=[r for r in rows if r['dataset']==ds and r['K']==k and r['method']==method]
                ax.plot([r['recall']*100 for r in rr],[r['qps_mean'] for r in rr],'o-',ms=4,color=COLORS[method],label=DISPLAY[method])
                ax.fill_between([r['recall']*100 for r in rr],[r['qps_min'] for r in rr],[r['qps_max'] for r in rr],color=COLORS[method],alpha=.12)
            ax.set(xlabel=f'Recall@{k} (%)',ylabel='Queries / second',title=LABELS[ds]);ax.set_yscale('log');ax.grid(alpha=.2,which='both');ax.legend(fontsize=9);fig.tight_layout()
            for ext in ['png','pdf']:fig.savefig(RUN/'figures'/f'{ds}_k{k}.{ext}',dpi=200)
            plt.close(fig)
    dump(RUN/'figures/manifest.json',dict(status='PASS',files={p.name:sha(p) for p in (RUN/'figures').iterdir() if p.suffix in ['.png','.pdf']}))

if __name__=='__main__':
    rows,targets=analyze();draw(rows)
    print('ANALYSIS_AND_PLOTS_COMPLETE',flush=True)
