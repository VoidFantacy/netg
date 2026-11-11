#!/usr/bin/env python3
"""E185 offline local geometry and train-to-test omission continuity; no ANN."""
import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[key]='1'
from pathlib import Path
import csv,hashlib,json,shutil,time
import numpy as np
from scipy.stats import rankdata,spearmanr

ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[1]
OLD=ROOT.parent/'20261017_gt10_residual_comprehensive_v1'
GEOM=ROOT.parent/'20261024_residual_geometry_diagnosis_v1'
DATA=[('deep10m_l2_v1','Deep10M','soft'),('sift10m_bigann_l2_v1','SIFT10M','soft'),
      ('gist1m_l2_v1','GIST1M','hard'),('webvid2_5m_light_v1','WebVid','soft'),
      ('yandex_t2i_official10M_ip_v1','Yandex','hard'),('coco','COCO','hard'),('flickr30k','Flickr30k','hard')]
INPUTS={};BIG={}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def remember(p,big=False):
    p=Path(p);s=p.stat();r=dict(bytes=s.st_size,mtime_ns=s.st_mtime_ns)
    if big:r.update(whole_SHA='INHERITED_E183_NOT_REHASHED');BIG[str(p)]=r
    else:r['sha256']=sha(p);INPUTS[str(p)]=r
    return p
def js(p):return json.loads(remember(p).read_text())
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def csvout(p,rr):
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rr[0]));w.writeheader();w.writerows(rr)
def vec(d,big=False):
    p=remember(d['path'],big);n=d['n'];total=d.get('total_n',n);dim=d['d'];start=d.get('row_start',0)
    if d['format']=='fvecs':
        a=np.memmap(p,'<f4','r',shape=(total,dim+1));assert p.stat().st_size==total*(dim+1)*4
        assert np.all(a[np.linspace(start,start+n-1,min(n,64),dtype=int),0].view('<i4')==dim)
        return a[start:start+n,1:]
    assert d['format']=='raw_f32' and p.stat().st_size==total*dim*4
    return np.memmap(p,'<f4','r',shape=(total,dim))[start:start+n]
def truth(d):
    p=remember(d['path']);n=d['n'];total=d.get('total_n',n);start=d.get('row_start',0);k=d.get('width',d.get('k',100))
    dt='<i8' if d['format']=='raw_i64' else '<i4';header=int(d['format']=='ivecs')
    assert p.stat().st_size==total*(k+header)*np.dtype(dt).itemsize
    a=np.memmap(p,dt,'r',shape=(total,k+header))
    if header:assert np.all(a[:,0]==k)
    return np.asarray(a[start:start+n,header:header+100])
def member(gt,returned):
    out=np.empty(gt.shape,dtype=bool)
    for lo in range(0,len(gt),128):out[lo:lo+128]=(gt[lo:lo+128,:,None]==returned[lo:lo+128,None,:]).any(2)
    return out
def corr(x,y):
    x=np.asarray(x);y=np.asarray(y);sel=np.isfinite(x)&np.isfinite(y)
    if sel.sum()<3 or len(np.unique(x[sel]))<2 or len(np.unique(y[sel]))<2:return None
    return float(spearmanr(x[sel],y[sel]).statistic)
def adjusted(ds,scope,feature,x,hits,delta,freq,minimum):
    bins=[(0,9),(10,49),(50,79),(80,89),(90,94),(95,99)]
    fb=np.minimum(((rankdata(freq,method='average')-1)*4/len(freq)).astype(int),3)
    out=[]
    for control in ['baseline_hits','baseline_hits_and_residual_frequency']:
        w=[];d=[];g=[]
        for lo,hi in bins:
            for band in (range(4) if control.endswith('frequency') else [None]):
                z=(hits>=lo)&(hits<=hi)&np.isfinite(x)
                if band is not None:z &= fb==band
                if not z.any():continue
                cut=np.median(x[z]);l=z&(x<=cut);u=z&(x>cut)
                if l.sum()<minimum or u.sum()<minimum:continue
                w.append(int(z.sum()));d.append(float((delta[u]>0).mean()-(delta[l]>0).mean()));g.append(float(delta[u].mean()-delta[l].mean()))
        out.append(dict(dataset=ds,scope=scope,feature=feature,control=control,included_queries=sum(w),
            eligible_incomplete_queries=int((hits<100).sum()),strata=len(w),
            improved_probability_high_minus_low_pp=float(100*np.average(d,weights=w)) if w else None,
            mean_recall_gain_high_minus_low_pp=float(np.average(g,weights=w)) if w else None))
    return out
def bootstrap_delta(a,b,den,seed):
    if np.sum(den)==0:return [None,None]
    rng=np.random.default_rng(seed);idx=rng.integers(0,len(a),size=(1000,len(a)))
    ds=den[idx].sum(1);v=100*(a[idx].sum(1)-b[idx].sum(1))/np.maximum(ds,1)
    return np.percentile(v,[2.5,97.5]).tolist()

def main():
    began=time.perf_counter();A=ROOT/'analysis';A.mkdir(exist_ok=False)
    for name in ['summary.md','spec.md','s-target.md','s-experiment.md','LOCAL_CODEX_START.md','readme.md','experiment_history/README.md']:
        dest=ROOT/'source_before'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(REPO/name,dest)
    oldsummary=list(csv.DictReader(remember(GEOM/'analysis/dataset_summary.csv').open()))
    summaries=[];queryrows=[];associations=[];adjustments=[];audits=[]
    for di,(ds,label,rt) in enumerate(DATA):
        t=time.perf_counter();print('START',label,flush=True)
        cfg=js(OLD/f'configs/{ds}.analysis.json');c=cfg['catalogue_entry'];n=c['test_queries']['n']
        old=np.load(remember(GEOM/f'analysis/{ds}.npz'))
        gt=truth(c['test_gt']);tg=truth(c['train_gt']);assert np.array_equal(gt,old['GT'])
        b=vec(c['base'],True);q=vec(c['test_queries']);tq=vec(c['train_queries'])
        td=Path(cfg['models'][rt]['teacher_dir'])
        trainids=np.fromfile(remember(td/'raw/ids.i32'),'<i4').reshape(len(tg),100)
        troutes=np.fromfile(remember(td/'raw/entry_ids.i32'),'<i4').reshape(len(tg),3)
        gm='GT10-soft-t1' if rt=='soft' else 'GT10-hard'
        vroutes=np.fromfile(remember(OLD/f'results/{ds}/k100/{gm}_L200/raw/entry_ids.i32'),'<i4').reshape(n,3)
        tm=~member(tg,trainids)
        sample=np.sort(np.random.default_rng(20261025).choice(n,512,replace=False))
        qq=np.asarray(q[sample],dtype=np.float64);tt=np.asarray(tq,dtype=np.float64)
        if c['metric_id']==1:
            distances=(qq*qq).sum(1)[:,None]+(tt*tt).sum(1)[None,:]-2*qq@tt.T
            nearest=np.argmin(distances,axis=1);qgeom='raw squared L2 between queries'
        else:
            qq=qq/np.maximum(np.linalg.norm(qq,axis=1)[:,None],1e-30)
            tt=tt/np.maximum(np.linalg.norm(tt,axis=1)[:,None],1e-30)
            distances=1-qq@tt.T;nearest=np.argmin(distances,axis=1);qgeom='unit-query cosine diagnostic; retrieval stays raw IP'
        rng=np.random.default_rng(20261026);random=rng.integers(0,len(tg),size=512);matched=np.empty(512,dtype=int)
        route_overlap=np.empty(512,dtype=int)
        for j,qi in enumerate(sample):
            overlap=(troutes[:,:,None]==vroutes[qi][None,None,:]).any(2).sum(1)
            target=overlap[nearest[j]];route_overlap[j]=target
            choices=np.flatnonzero(overlap==target);choices=choices[choices!=nearest[j]]
            assert len(choices)>0;matched[j]=rng.choice(choices)
        near_gt=[];rand_gt=[];match_gt=[];near_miss=[];rand_miss=[];match_miss=[];den=[]
        local={f'local_PR{k}':[] for k in [20,50,100]};local['local_top10_energy100']=[]
        vector_hash=hashlib.sha256();sample_base_ids=[]
        for j,qi in enumerate(sample):
            g=gt[qi];missing=g[~old['GT_mask'][qi]];den.append(len(missing))
            for index,glist,mlist in [(nearest[j],near_gt,near_miss),(random[j],rand_gt,rand_miss),(matched[j],match_gt,match_miss)]:
                glist.append(int(np.isin(g,tg[index]).sum()));mlist.append(int(np.isin(missing,tg[index][tm[index]]).sum()))
            raw=np.asarray(b[g],dtype='<f4');vector_hash.update(raw.tobytes());v=raw.astype(np.float64)
            for k in [20,50,100]:
                x=v[:k]-v[:k].mean(0);gram=x@x.T;e=np.linalg.eigvalsh(gram)
                assert e.min()>-1e-7*max(e.sum(),1);e=np.maximum(e,0);trace=e.sum()
                pr=float(trace*trace/(e@e)) if trace>0 else 0.;local[f'local_PR{k}'].append(pr)
                if k==100:
                    local['local_top10_energy100'].append(float(e[-10:].sum()/trace) if trace>0 else 0.)
                    if j in [0,511]:
                        sv=np.linalg.svd(x,compute_uv=False);direct=float((sv*sv).sum()**2/np.power(sv,4).sum())
                        assert abs(pr-direct)<1e-7;audits.append(dict(dataset=ds,query_row=int(qi),PR100_gram=pr,PR100_SVD=direct))
        local={k:np.asarray(v) for k,v in local.items()}
        near_gt,rand_gt,match_gt,near_miss,rand_miss,match_miss,den=map(np.asarray,[near_gt,rand_gt,match_gt,near_miss,rand_miss,match_miss,den])
        hits=old['GT_mask'].sum(1);delta=old['B32_mask'].sum(1).astype(int)-hits.astype(int)
        assert not (old['GT_mask']&~old['B32_mask']).any()
        freq=old['GT100_mean_residual_frequency']
        for feat in ['background_separation_z','GT100_direction_concentration','top100_relative_span']:
            adjustments+=adjusted(ds,'all_existing_queries',feat,old[feat],hits,delta,freq,8)
        newfeatures={**local,'nearest_training_GT_overlap':near_gt,
            'nearest_training_query_distance':distances[np.arange(512),nearest]}
        for fname,x in newfeatures.items():
            for outcome,y in [('baseline_missing',100-hits[sample]),('net_gain',delta[sample]),('improved',delta[sample]>0),
                              ('nearest_training_missing_coverage',near_miss/np.maximum(den,1))]:
                associations.append(dict(dataset=ds,feature=fname,outcome=outcome,n=512,spearman=corr(x,y)))
            adjustments+=adjusted(ds,'fixed_512_sample',fname,x,hits[sample],delta[sample],freq[sample],4)
        for j,qi in enumerate(sample):
            queryrows.append(dict(dataset=ds,label=label,query_row=int(qi),GT_hits=int(hits[qi]),net_gain=int(delta[qi]),
                residual_frequency=float(freq[qi]),nearest_train_row=int(nearest[j]),random_train_row=int(random[j]),
                matched_train_row=int(matched[j]),nearest_route_overlap=int(route_overlap[j]),
                nearest_query_distance=float(distances[j,nearest[j]]),
                nearest_GT_overlap=int(near_gt[j]),random_GT_overlap=int(rand_gt[j]),matched_GT_overlap=int(match_gt[j]),
                missing_count=int(den[j]),nearest_missing_covered=int(near_miss[j]),random_missing_covered=int(rand_miss[j]),
                matched_missing_covered=int(match_miss[j]),**{k:float(v[j]) for k,v in local.items()}))
        item=next(v for v in oldsummary if v['dataset']==ds)
        lo,hi=bootstrap_delta(near_miss,match_miss,den,20261027)
        summaries.append(dict(dataset=ds,label=label,n=n,sample_n=512,query_geometry=qgeom,
            local_PR20_median=float(np.median(local['local_PR20'])),local_PR50_median=float(np.median(local['local_PR50'])),
            local_PR100_median=float(np.median(local['local_PR100'])),local_top10_energy100_median=float(np.median(local['local_top10_energy100'])),
            nearest_GT_overlap_pct=float(near_gt.mean()),random_GT_overlap_pct=float(rand_gt.mean()),matched_GT_overlap_pct=float(match_gt.mean()),
            nearest_missing_coverage_pct=float(100*near_miss.sum()/max(den.sum(),1)),
            random_missing_coverage_pct=float(100*rand_miss.sum()/max(den.sum(),1)),matched_missing_coverage_pct=float(100*match_miss.sum()/max(den.sum(),1)),
            nearest_minus_matched_missing_coverage_pp=float(100*(near_miss-match_miss).sum()/max(den.sum(),1)),
            paired_query_bootstrap95_low_pp=lo,paired_query_bootstrap95_high_pp=hi,
            sampled_missing_members=int(den.sum()),sampled_improved_queries=int((delta[sample]>0).sum()),
            member_repair_pct=float(item['K100_member_repair_pct']),residual_repeat_factor=float(item['train_residual_repeat_factor']),
            query_exact_training_distance_zero=int((np.abs(distances[np.arange(512),nearest])<1e-12).sum()),
            sampled_vectors_sha256=vector_hash.hexdigest(),seconds=time.perf_counter()-t))
        np.savez_compressed(A/(ds+'.npz'),query_rows=sample,nearest_train=nearest,random_train=random,matched_train=matched,
            nearest_query_distances=distances[np.arange(512),nearest],nearest_GT_overlap=near_gt,random_GT_overlap=rand_gt,
            matched_GT_overlap=match_gt,nearest_missing_covered=near_miss,random_missing_covered=rand_miss,
            matched_missing_covered=match_miss,missing_count=den,**local)
        # Direct query-to-training distances verify matrix nearest lookup for eight fixed sample rows.
        for j in np.linspace(0,511,8,dtype=int):
            direct=np.square(tt-qq[j]).sum(1) if c['metric_id']==1 else 1-np.sum(tt*qq[j],axis=1)
            assert int(np.argmin(direct))==int(nearest[j]);assert np.allclose(direct,distances[j],rtol=1e-7,atol=1e-8)
        print('DONE',label,json.dumps(summaries[-1]),flush=True)
    csvout(A/'dataset_summary.csv',summaries);csvout(A/'sample_query_metrics.csv',queryrows)
    csvout(A/'within_dataset_correlations.csv',associations);csvout(A/'adjusted_associations.csv',adjustments)
    csvout(A/'gram_svd_checks.csv',audits)
    cross=[]
    for feature in ['local_PR20_median','local_PR50_median','local_PR100_median','local_top10_energy100_median',
                    'nearest_GT_overlap_pct','nearest_missing_coverage_pct','matched_missing_coverage_pct']:
        cross.append(dict(feature=feature,outcome='member_repair_pct',datasets=7,
            spearman=corr([r[feature] for r in summaries],[r['member_repair_pct'] for r in summaries]),
            interpretation='seven confounded datasets; descriptive only'))
    csvout(A/'cross_dataset_correlations.csv',cross)
    for path,record in INPUTS.items():assert sha(path)==record['sha256']
    for path,record in BIG.items():
        s=Path(path).stat();assert s.st_size==record['bytes'] and s.st_mtime_ns==record['mtime_ns']
    dump(A/'inputs_manifest.json',dict(small_inputs=INPUTS,inherited_big_inputs=BIG))
    dump(A/'receipt.json',dict(status='PASS_OFFLINE_MANIFOLD_RELATED_GEOMETRY_PROBE',sample_queries=3584,
        existing_queries_adjusted=56000,gram_svd_checks=14,direct_full_training_neighbor_checks=56,
        new_ANN=0,new_GT=0,new_training=0,new_QPS=0,default_changed=False,seconds=time.perf_counter()-began))
    print('PASS E185',time.perf_counter()-began,flush=True)
if __name__=='__main__':main()
