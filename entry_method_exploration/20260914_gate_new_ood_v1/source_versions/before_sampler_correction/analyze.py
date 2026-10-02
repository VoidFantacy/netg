from common import *
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from verify import protected

def csv_file(p,rows):
    with Path(p).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def wilson(k,n):
    z=1.959963984540054;p=k/n;den=1+z*z/n;center=(p+z*z/(2*n))/den;half=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return max(0.,center-half),min(1.,center+half)
def main():
    lock=json.loads((RUN/'config.locked.json').read_text());rows=[];paired=[];hits_all={};cost=[];rounds=0
    for ds in DATASETS:
        inp=RUN/'inputs'/ds;meta=json.loads((inp/'manifest.json').read_text());root=RUN/'results'/ds;complete=json.loads((root/'complete.json').read_text());assert complete['status']=='PASS' and complete['points']==64 and complete['wall_rounds']==192 and complete['formal'];rounds+=192
        gt=np.array(vecs(meta['paths']['gt_path'],'i4')[:10000,:10]);assert ((gt>=0)&(gt<meta['shape'][0])).all()
        assert all(len(set(row))==10 for row in gt.tolist())
        for method in lock['methods']:
            for L in lock['L']:
                p=root/(method+'_L'+str(L));c=json.loads((p/'complete.json').read_text());assert c['status']=='PASS' and c['threads']==1 and c['cpu']==15 and len(c['seconds'])==3
                ids=np.fromfile(p/'ids.i32','i4').reshape(10000,10);dist=np.fromfile(p/'distances.f32','f4').reshape(10000,10);assert ((ids>=0)&(ids<meta['shape'][0])).all() and np.isfinite(dist).all();assert all(len(set(row))==10 for row in ids.tolist())
                # Two independent formulations of set recall, including rank-1 misses.
                masks=(ids[:,:,None]==gt[:,None,:]).any(axis=1);hits=masks.sum(axis=1).astype('i1');independent=np.array([len(set(map(int,a))&set(map(int,b))) for a,b in zip(ids,gt)]);assert np.array_equal(hits,independent)
                hits.tofile(p/'hits10.i8');(hits==0).astype('u1').tofile(p/'failed_zero_hit.u8');(~masks[:,0]).astype('u1').tofile(p/'gt1_miss.u8');hits_all[(ds,method,L)]=hits
                ndc_r=np.fromfile(p/'route_ndc.u64','u8');ndc_g=np.fromfile(p/'graph_ndc.u64','u8');assert ndc_r.shape==ndc_g.shape==(10000,) and (ndc_g>0).all()
                times=np.asarray(c['seconds']);qps=10000/times;lo,hi=wilson(int((hits==0).sum()),10000)
                # Query bootstrap describes sample uncertainty, not timing-repetition uncertainty.
                rng=np.random.default_rng(20260914);hist=np.bincount(hits,minlength=11);boot=rng.multinomial(10000,hist/10000,size=2000);recall_boot=boot@np.arange(11)/100000;ci=np.quantile(recall_boot,[.025,.975])
                row=dict(dataset=ds,method=method,L=L,budget_parameter='efSearch' if method=='HNSW' else 'L',queries=10000,recall_at10=float(hits.mean()/10),recall_bootstrap_lo=float(ci[0]),recall_bootstrap_hi=float(ci[1]),qps_mean=float(qps.mean()),qps_min=float(qps.min()),qps_max=float(qps.max()),wall_mean_seconds=float(times.mean()),qps_from_mean_wall=float(10000/times.mean()),failed_queries=int((hits==0).sum()),failed_query_rate=float((hits==0).mean()),failure_wilson_lo=lo,failure_wilson_hi=hi,gt1_miss_rate=float((~masks[:,0]).mean()),route_ndc_mean=float(ndc_r.mean()),graph_ndc_mean=float(ndc_g.mean()),total_ndc_mean=float((ndc_r+ndc_g).mean()))
                for i in range(3):row[f'qps_round{i+1}']=float(qps[i]);row[f'wall_round{i+1}']=float(times[i])
                rows.append(row)
        model=RUN/'models'/ds;train=json.loads((model/'gate/complete.json').read_text());labels=json.loads((inp/'labels/complete.json').read_text());hnsw=json.loads((model/'hnsw/complete.json').read_text());features=json.loads((inp/'gate_features.json').read_text())
        cost.append(dict(dataset=ds,gate_label_seconds=labels['total_seconds'],gate_training_seconds=train['training_seconds'],gate_feature_stage_seconds=features['seconds'],gate_feature_reused=features['source']['kind']=='verified_reuse',gate_historical_feature_cost_seconds=None if features['source']['kind']=='verified_reuse' else 0,hnsw_build_seconds=hnsw['build_seconds'],hnsw_storage_save_seconds=hnsw['save_seconds'],hnsw_restore_seconds=hnsw['load_seconds'],hnsw_verification_seconds=hnsw['verification_seconds'],hnsw_topology_bytes=hnsw['topology_bytes'],inherited_GT_cost_seconds=None,inherited_NSG_build_seconds=None,inherited_GT10_cost_seconds=None))
        for reference in ['NSG','GT10']:
            for method in lock['methods']:
                if method==reference:continue
                for L in lock['L']:
                    a=hits_all[(ds,reference,L)];b=hits_all[(ds,method,L)];paired.append(dict(dataset=ds,reference=reference,method=method,L=L,rescued_zero_hit=int(((a==0)&(b>0)).sum()),new_zero_hit=int(((a>0)&(b==0)).sum()),improved_queries=int((b>a).sum()),worsened_queries=int((b<a).sum()),same_queries=int((b==a).sum()),recall_delta_pp=float((b.astype('f8')-a).mean()*10),comparison='same parameter value; not equal work'))
    assert len(rows)==192 and rounds==576;csv_file(RUN/'results/metrics.csv',rows);csv_file(RUN/'results/paired_queries.csv',paired);dump(RUN/'results/offline_costs.json',cost)
    targets=[]
    for ds in DATASETS:
        for target in [.7,.8,.9,.95,.99]:
            for method in lock['methods']:
                eligible=[r for r in rows if r['dataset']==ds and r['method']==method and r['recall_at10']>=target];best=max(eligible,key=lambda x:x['qps_mean']) if eligible else None;targets.append(dict(dataset=ds,target_recall=target,method=method,achieved=bool(best),qps=best['qps_mean'] if best else None,L=best['L'] if best else None,measured_recall=best['recall_at10'] if best else None,rule='fastest measured point meeting target; no extrapolation'))
    csv_file(RUN/'results/common_recall.csv',targets)
    colors=dict(NSG='#777777',GT10='#167dba',GATE='#d97816',HNSW='#249257');titles=['WebVid 2.505M','Yandex 10M','LAION 10.004M'];fig,axes=plt.subplots(1,3,figsize=(16,4.8))
    for ax,ds,title in zip(axes,DATASETS,titles):
        for method in lock['methods']:
            rr=[r for r in rows if r['dataset']==ds and r['method']==method];x=np.array([r['recall_at10']*100 for r in rr]);y=np.array([r['qps_mean'] for r in rr]);ax.plot(x,y,'o-',ms=4,label=method,color=colors[method]);ax.fill_between(x,[r['qps_min'] for r in rr],[r['qps_max'] for r in rr],alpha=.12,color=colors[method])
        ax.set_title(title);ax.set_xlabel('Recall@10 (%)');ax.set_ylabel('Queries / second');ax.set_yscale('log');ax.grid(alpha=.2);ax.legend(fontsize=9)
    fig.suptitle('Full search: one CPU thread, 10,000 queries, mean of 3 runs',fontsize=13);fig.text(.5,.01,'16 budgets from 32 to 1500. Shading: observed timing range. WebVid and LAION share the public query source.',ha='center',fontsize=9);fig.tight_layout(rect=[0,.035,1,.94]);fig.savefig(RUN/'figures/recall_qps.png',dpi=190);fig.savefig(RUN/'figures/recall_qps.pdf');plt.close(fig)
    fig,axes=plt.subplots(1,3,figsize=(16,4.8))
    for ax,ds,title in zip(axes,DATASETS,titles):
        for method in lock['methods']:
            rr=[r for r in rows if r['dataset']==ds and r['method']==method];ax.plot([r['L'] for r in rr],[100*r['failed_query_rate'] for r in rr],'o-',ms=4,label=method,color=colors[method])
        ax.set_title(title);ax.set_xlabel('Search budget (L / HNSW efSearch)');ax.set_ylabel('Zero-hit queries (%)');ax.set_xscale('log');ax.grid(alpha=.2);ax.legend(fontsize=9)
    fig.suptitle('Failed query = returned top-10 has no intersection with exact top-10',fontsize=13);fig.text(.5,.01,'Same budget value does not imply equal work. Full paired counts and GT1 miss rates are in metrics.csv.',ha='center',fontsize=9);fig.tight_layout(rect=[0,.035,1,.94]);fig.savefig(RUN/'figures/failed_query_rate.png',dpi=190);fig.savefig(RUN/'figures/failed_query_rate.pdf');plt.close(fig)
    dump(RUN/'results/analysis_complete.json',dict(status='PASS',points=len(rows),wall_rounds=rounds,independent_set_rescoring=True,protected_sources=protected(),files={str(p.relative_to(RUN)):sha(p) for p in (RUN/'figures').iterdir()}))

if __name__=='__main__':main()
