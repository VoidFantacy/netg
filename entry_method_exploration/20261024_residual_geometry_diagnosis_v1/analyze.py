#!/usr/bin/env python3
"""Read E183 actual responses; new offline geometry, never execute ANN or fit."""
import os
for _k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[_k] = '1'
import csv
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from scipy.stats import spearmanr, rankdata

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
OLD = REPO/'entry_method_exploration/20261017_gt10_residual_comprehensive_v1'
DATA = [('deep10m_l2_v1','Deep10M','soft'),('sift10m_bigann_l2_v1','SIFT10M','soft'),
        ('gist1m_l2_v1','GIST1M','hard'),('webvid2_5m_light_v1','WebVid','soft'),
        ('yandex_t2i_official10M_ip_v1','Yandex','hard'),('coco','COCO','hard'),('flickr30k','Flickr30k','hard')]
INPUTS = {}

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def remember(p, big=False):
    p=Path(p); st=p.stat()
    item={'bytes':st.st_size,'mtime_ns':st.st_mtime_ns,'inode':st.st_ino,'device':st.st_dev}
    if not big: item['sha256']=sha(p)
    else: item['whole_file_sha256']='INHERITED_E183_NOT_REHASHED'
    if str(p) in INPUTS: assert INPUTS[str(p)]==item
    INPUTS[str(p)]=item
    return p

def js(p): return json.loads(remember(p).read_text())
def rows(p): return list(csv.DictReader(remember(p).open()))
def dump(p,x):
    p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def csvout(p,rr):
    if not rr:return
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rr[0]));w.writeheader();w.writerows(rr)
def frac(a,b): return float(a/b) if b else None
def pct(a,b): return 100*a/b if b else None
def corr(x,y):
    x,y=np.asarray(x),np.asarray(y)
    if len(x)<3 or np.all(x==x[0]) or np.all(y==y[0]):return None
    return float(spearmanr(x,y).statistic)

def vec(d, big=False):
    p=remember(d['path'],big); n=d.get('total_n',d['n']);dim=d['d'];start=d.get('row_start',0)
    if d['format']=='fvecs':
        assert p.stat().st_size==n*(dim+1)*4
        mm=np.memmap(p,'<f4','r',shape=(n,dim+1))
        header_rows=np.linspace(start,start+d['n']-1,min(64,d['n']),dtype=int) if big else np.arange(start,start+d['n'])
        assert np.all(mm[header_rows,0].view('<i4')==dim)
        return mm[start:start+d['n'],1:]
    assert d['format']=='raw_f32' and p.stat().st_size==n*dim*4
    return np.memmap(p,'<f4','r',shape=(n,dim))[start:start+d['n']]

def gtload(d):
    p=remember(d['path']);n=d.get('total_n',d['n']);k=d.get('width',d.get('k',100));start=d.get('row_start',0)
    fmt=d['format']
    if fmt=='ivecs':
        assert p.stat().st_size==n*(k+1)*4
        mm=np.memmap(p,'<i4','r',shape=(n,k+1));assert np.all(mm[:,0]==k)
        return np.asarray(mm[start:start+d['n'],1:101])
    dt='<i8' if fmt=='raw_i64' else '<i4'
    assert p.stat().st_size==n*k*np.dtype(dt).itemsize
    return np.asarray(np.memmap(p,dt,'r',shape=(n,k))[start:start+d['n'],:100])

def mask(ds,method,k,L,g):
    p=remember(OLD/f'results/{ds}/k{k}/{method}_L{L}/raw/ids.i32')
    r=np.fromfile(p,'<i4').reshape(len(g),k); truth=g[:,:k]
    out=np.zeros_like(truth,dtype=bool)
    for lo in range(0,len(g),128):
        hi=lo+128;out[lo:hi]=(truth[lo:hi,:,None]==r[lo:hi,None,:]).any(2)
    return out

def freq(values,targets):
    u,c=np.unique(values,return_counts=True);idx=np.searchsorted(u,targets);safe=np.minimum(idx,len(u)-1)
    ok=(idx<len(u))&(u[safe]==targets)
    return np.where(ok,c[safe],0),u,c

def check(r,**values):
    for k,v in values.items(): assert int(r[k])==int(v),(k,r[k],v)

def main():
    started=time.time();out=ROOT/'analysis';out.mkdir(exist_ok=False)
    points=rows(OLD/'analysis/final_v1/points.csv');deltas=rows(OLD/'analysis/final_v1/same_L_deltas.csv')
    covers=rows(OLD/'analysis/final_v1/candidate_coverage.csv')
    summaries=[];queries=[];bins=[];relations=[];adjusted=[];stages=[];geometry=[];validation=[]
    curve_rows=[]
    for di,(ds,label,rt) in enumerate(DATA):
        begin=time.time();print('START',ds,flush=True)
        a=js(OLD/f'configs/{ds}.analysis.json');c=a['catalogue_entry'];n=c['test_queries']['n'];N=c['base']['n']
        g=gtload(c['test_gt']);tg=gtload(c['train_gt']);b=vec(c['base'],True);q=np.asarray(vec(c['test_queries']),dtype=np.float64)
        assert q.shape==(n,c['base']['d']) and g.shape==(n,100)
        gm='GT10-soft-t1' if rt=='soft' else 'GT10-hard';post=rt+'-JOINT32'
        bm=mask(ds,gm,100,200,g);pm=mask(ds,post,100,200,g);nm=mask(ds,'NSG',100,200,g)
        b1=mask(ds,gm,1,200,g)[:,0];p1=mask(ds,post,1,200,g)[:,0];n1=mask(ds,'NSG',1,200,g)[:,0]
        miss=~bm;rescue=miss&pm;damage=bm&~pm;bh=bm.sum(1);ph=pm.sum(1);delta=ph.astype(int)-bh.astype(int)
        dr=next(r for r in deltas if r['dataset']==ds and r['method']==post and r['K']=='100' and r['L']=='200')
        cv=next(r for r in covers if r['dataset']==ds and r['method']==post and r['K']=='100' and r['L']=='200')
        check(dr,reference_missing_members=miss.sum(),rescued_members=rescue.sum(),damaged_members=damage.sum(),
              net_improved_queries=(delta>0).sum(),reference_incomplete_queries=(bh<100).sum(),
              reference_below_90pct_queries=(bh<90).sum(),failed_queries_become_full_success=((bh<100)&(ph==100)).sum())
        for k,hh in [(1,int(b1.sum())),(100,int(bm.sum()))]:
            pp=next(r for r in points if r['dataset']==ds and r['method']==gm and int(r['K'])==k and r['L']=='200')
            assert int(pp['hits'])==hh
        source=Path(a['models'][rt]['source_dir']);tokens=np.fromfile(remember(source/'token_targets.i32'),'<i4')
        tf,tu,tc=freq(tg.ravel(),g);rf,ru,rc=freq(tokens,g)
        check(cv,missing_in_full_training_GT=(miss&(tf>0)).sum(),missing_in_global_residual_source=(miss&(rf>0)).sum())
        # Sampled background distribution in the original metric, shared across all q in a dataset.
        sample_ids=np.random.default_rng(20261024).choice(N,min(8192,N),replace=False)
        x=np.asarray(b[sample_ids],dtype=np.float64);mean=x.mean(0);xc=x-mean;cov=xc.T@xc/len(x)
        norm2=np.einsum('ij,ij->i',x,x);evals=np.linalg.eigvalsh(cov)
        mean_norm=float(np.sqrt(norm2).mean());unit_x=x/np.maximum(np.sqrt(norm2)[:,None],1e-30)
        base_R=float(np.linalg.norm(unit_x.mean(0)))
        effrank=float(evals.sum()**2/np.square(evals).sum())
        qnorm=np.linalg.norm(q,axis=1);qvar=np.einsum('ij,ij->i',q@cov,q)
        bgmean=-q@mean;bgvar=qvar.copy()
        if c['metric_id']==1:
            m2=float(norm2.mean());center2=norm2-m2
            cross=xc.T@center2/len(x)
            bgmean=np.square(qnorm)+m2-2*q@mean
            bgvar=float(np.mean(center2**2))+4*qvar-4*q@cross
        dscores=np.empty((n,100));coherence=np.empty(n);target_norm=np.empty(n)
        for lo in range(0,n,64):
            hi=min(lo+64,n);v=np.asarray(b[g[lo:hi]],dtype=np.float64)
            vnorm=np.linalg.norm(v,axis=2);unit=v/np.maximum(vnorm[:,:,None],1e-30)
            coherence[lo:hi]=np.linalg.norm(unit.mean(1),axis=1);target_norm[lo:hi]=vnorm.mean(1)
            if c['metric_id']==1:dscores[lo:hi]=np.square(v-q[lo:hi,None,:]).sum(2)
            else:dscores[lo:hi]=-np.einsum('ijk,ik->ij',v,q[lo:hi])
        z=(bgmean-dscores[:,99])/np.sqrt(np.maximum(bgvar,1e-30))
        span=(dscores[:,99]-dscores[:,0])/np.maximum(np.abs(dscores[:,99])+np.abs(dscores[:,0]),1e-30)
        # Direct explicit background calculation independently checks algebra on eight fixed queries.
        ids8=np.linspace(0,n-1,8,dtype=int)
        for qi in ids8:
            direct=-x@q[qi] if c['metric_id']==0 else np.square(x-q[qi]).sum(1)
            assert np.isclose(direct.mean(),bgmean[qi],rtol=1e-9,atol=1e-8)
            assert np.isclose(direct.var(),bgvar[qi],rtol=1e-8,atol=1e-8)
        feat={'background_separation_z':z,'top100_relative_span':span,'GT100_direction_concentration':coherence,
              'query_norm':qnorm,'GT100_mean_target_norm':target_norm,
              'GT100_mean_training_frequency':tf.mean(1),'GT100_mean_residual_frequency':rf.mean(1)}
        denom=miss.sum(1);supported=(miss&(rf>0)).sum(1)
        feat['missing_source_fraction']=np.divide(supported,denom,out=np.zeros(n),where=denom>0)
        outcomes={'K1_failure':~b1,'K100_missing_count':100-bh,'K100_incomplete':bh<100,
                  'K100_below90':bh<90,'K100_net_improved':delta>0,'K100_gain_count':delta}
        for fname,vals in feat.items():
            for oname,ovals in outcomes.items():
                relations.append({'dataset':ds,'feature':fname,'outcome':oname,'n':n,'spearman':corr(vals,ovals)})
            # Equal-width quantiles of feature ranks; ties stay together, may leave empty bands.
            band=np.minimum((rankdata(vals,method='average')-1)*4/n,3).astype(int)
            for j in range(4):
                sel=band==j;nn=int(sel.sum())
                if not nn:continue
                bins.append({'dataset':ds,'feature':fname,'quartile':j+1,'n':nn,'min':float(vals[sel].min()),'max':float(vals[sel].max()),
                    'K1_failure_pct':pct((~b1[sel]).sum(),nn),'K100_incomplete_pct':pct((bh[sel]<100).sum(),nn),
                    'K100_mean_missing':float(denom[sel].mean()),'K100_improved_query_pct':pct((delta[sel]>0).sum(),nn),
                    'K100_improved_among_incomplete_pct':pct((delta[sel]>0).sum(),(bh[sel]<100).sum()),
                    'K100_member_repair_pct':pct(rescue[sel].sum(),miss[sel].sum()),'mean_gain_members':float(delta[sel].mean())})
            # Standardize low/high halves within baseline missing-count strata (1-4,5-9,10-49,50+).
            high=rankdata(vals,method='average')>(n+1)/2
            strata=[(1,4),(5,9),(10,49),(50,100)];ww=[];diff=[]
            for low,upper in strata:
                ss=(denom>=low)&(denom<=upper);h=ss&high;l=ss&~high
                if h.sum()>=10 and l.sum()>=10:
                    ww.append(int(ss.sum()));diff.append(float((delta[h]>0).mean()-(delta[l]>0).mean()))
            adjusted.append({'dataset':ds,'feature':fname,'outcome':'improved_query_high_minus_low_pp',
                'standardized_delta_pp':float(100*np.average(diff,weights=ww)) if ww else None,
                'included_incomplete_queries':sum(ww),'total_incomplete_queries':int((denom>0).sum()),
                'strata_used':len(ww),'interpretation':'descriptive baseline-missing strata; not causal or deployed'})
        missing_total=int(miss.sum());rescues=int(rescue.sum());global_n=int((miss&(rf>0)).sum())
        route_n=int(cv['missing_in_uncapped_routed_source']);selected=int(cv['missing_in_selected_routed_table'])
        assert selected==rescues and not damage.any() # Only selected L200; E183 other L retain boundary damage.
        train_single=pct(rc[rc==1].sum(),len(tokens));efftargets=float(rc.sum()**2/np.square(rc.astype(float)).sum())
        item={'dataset':ds,'label':label,'router':rt,'n':n,'base_n':N,'dimension':c['base']['d'],'metric':'L2_squared' if c['metric_id'] else 'raw_IP',
            'NSG_K1_failed':int((~n1).sum()),'GT_K1_failed':int((~b1).sum()),'GT_K1_failed_pct':pct((~b1).sum(),n),
            'B32_K1_rescued':int((~b1&p1).sum()),'B32_K1_damaged':int((b1&~p1).sum()),'K1_rescue_of_failed_pct':pct((~b1&p1).sum(),(~b1).sum()),
            'GT_K100_incomplete':int((bh<100).sum()),'GT_K100_incomplete_pct':pct((bh<100).sum(),n),
            'GT_K100_below90':int((bh<90).sum()),'GT_K100_below90_pct':pct((bh<90).sum(),n),
            'K100_improved_queries':int((delta>0).sum()),'K100_improved_all_pct':pct((delta>0).sum(),n),
            'K100_improved_incomplete_pct':pct((delta>0).sum(),(bh<100).sum()),
            'K100_full_repairs':int(((bh<100)&(ph==100)).sum()),'K100_full_repairs_of_incomplete_pct':pct(((bh<100)&(ph==100)).sum(),(bh<100).sum()),
            'K100_cross90':int(((bh<90)&(ph>=90)).sum()),'K100_missing_members':missing_total,'K100_missing_member_pct':pct(missing_total,100*n),
            'K100_rescued_members':rescues,'K100_member_repair_pct':pct(rescues,missing_total),'K100_net_recall_pp':pct(rescues,100*n),
            'GT_K100_recall_pct':float(dr['reference_hits'])/n,'B32_K100_recall_pct':float(dr['hits'])/n,'K100_QPS_delta_pct':float(dr['qps_pct']),
            'K100_missing_train_GT_seen_pct':pct((miss&(tf>0)).sum(),missing_total),'K100_missing_source_seen_pct':pct(global_n,missing_total),
            'route_given_source_pct':pct(route_n,global_n),'selection_given_route_pct':pct(selected,route_n),
            'actual_candidates_per_query':float(cv['actual_candidates_per_query']),
            'train_missing_tokens':len(tokens),'train_missing_unique_targets':len(ru),'train_residual_singleton_token_pct':train_single,
            'train_residual_effective_targets':efftargets,'train_residual_top1pct_unique_token_share':pct(np.sort(rc)[-max(1,int(np.ceil(.01*len(rc)))):].sum(),len(tokens)),
            'train_GT_unique_targets':len(tu),'train_GT_repeat_factor':len(tg.ravel())/len(tu),'train_residual_repeat_factor':len(tokens)/len(ru),
            'base_sample_effective_rank':effrank,'base_sample_direction_concentration':base_R,
            'median_background_z':float(np.median(z)),'median_top100_relative_span':float(np.median(span)),
            'median_GT100_direction_concentration':float(np.median(coherence)),
            'geometry_seconds':time.time()-begin}
        summaries.append(item)
        stages.append({'dataset':ds,'missing':missing_total,'in_train_GT':int((miss&(tf>0)).sum()),'in_global_source':global_n,
            'in_routed_source':route_n,'in_selected_table':selected,'rescued':rescues,'damaged':int(damage.sum()),
            'unseen_source':missing_total-global_n,'route_lost':global_n-route_n,'capacity_lost':route_n-selected,
            'global_source_recall_ceiling_pct':float(item['GT_K100_recall_pct'])+pct(global_n,n*100),
            'routed_source_recall_ceiling_pct':float(item['GT_K100_recall_pct'])+pct(route_n,n*100)})
        geometry.append({'dataset':ds,'sample_n':len(x),'sample_base_sha256':hashlib.sha256(x.astype('<f4').tobytes()).hexdigest(),
            'base_norm_mean':mean_norm,'base_norm_std':float(np.sqrt(norm2).std()),'sample_cov_effective_rank':effrank,
            'sample_cov_definition':'centered population covariance, denominator sample_n',
            'background_moment_direct_checks':len(ids8),'sample_seed':20261024})
        for i in range(n):
            queries.append({'dataset':ds,'query_row':i,'K1_failed':int(not b1[i]),'K1_rescued':int(not b1[i] and p1[i]),
                'GT_K100_hits':int(bh[i]),'B32_K100_hits':int(ph[i]),'K100_rescued':int(rescue[i].sum()),
                'K100_damaged':int(damage[i].sum()),'K100_net_delta':int(delta[i]),**{k:float(v[i]) for k,v in feat.items()}})
        np.savez_compressed(out/f'{ds}.npz',GT=g,GT_mask=bm,B32_mask=pm,NSG_mask=nm,GT_K1=b1,B32_K1=p1,NSG_K1=n1,
            sample_base_ids=sample_ids,training_frequency=tf,residual_frequency=rf,**feat)
        validation.append({'dataset':ds,'status':'PASS','query_rows':n,'GT_masks_vs_E183_CSV':True,'coverage_vs_E183_CSV':True,
            'all_L200_rescued_equal_selected_supported_missing':True,'background_moments_direct_verified':8})
        print('DONE',label,'seconds',round(time.time()-begin,2),'improved_pct',item['K100_improved_all_pct'],flush=True)
    features=['GT_K100_incomplete_pct','K100_missing_member_pct','K100_missing_source_seen_pct','train_residual_repeat_factor',
              'train_GT_repeat_factor','base_n','median_background_z','median_GT100_direction_concentration','base_sample_effective_rank']
    cross=[]
    for f in features:
        x=[s[f] for s in summaries];y=[s['K100_member_repair_pct'] for s in summaries]
        loo=[corr(np.delete(x,i),np.delete(y,i)) for i in range(7)]
        cross.append({'feature':f,'outcome':'K100_member_repair_pct','datasets':7,'spearman':corr(x,y),
            'leave_one_dataset_out_min':min(t for t in loo if t is not None),'leave_one_dataset_out_max':max(t for t in loo if t is not None),
            'interpretation':'seven heterogeneous datasets only; descriptive; no causal or population inference'})
    for ds,label,rt in DATA:
        for r in deltas:
            if r['dataset']==ds and r['method'].endswith('JOINT32'):
                cv=next(v for v in covers if all(v[k]==r[k] for k in ('dataset','method','K','L')))
                curve_rows.append({k:r[k] for k in ['dataset','method','K','L','n','reference_incomplete_queries','net_improved_queries',
                    'reference_missing_members','rescued_members','damaged_members','recall_delta_pp','qps_pct']}|
                    {k:cv[k] for k in ['missing_in_global_residual_source','missing_in_uncapped_routed_source','missing_in_selected_routed_table']})
    for fn,rr in [('dataset_summary',summaries),('query_metrics',queries),('feature_quartiles',bins),('within_dataset_spearman',relations),
                  ('baseline_stratified_associations',adjusted),('coverage_chain',stages),('cross_dataset_associations',cross),('all_L_and_router_sensitivity',curve_rows)]:
        csvout(out/f'{fn}.csv',rr)
    dump(out/'geometry_receipt.json',geometry);dump(out/'validation.json',validation)
    # Recheck every small input hash and every source stat at end. Never claim whole-base fresh SHA.
    for path,item in list(INPUTS.items()):remember(path,'whole_file_sha256' in item)
    dump(out/'inputs_manifest.json',INPUTS)
    dump(out/'receipt.json',{'status':'PASS_OFFLINE_DIAGNOSTICS','new_ANN_calls':0,'new_GT_generation':0,'new_models':0,
        'formal_QPS_remeasured':False,'default_changed':False,'n_queries':len(queries),'datasets':7,
        'protocol_sha256':sha(ROOT/'protocol.md'),'analyzer_sha256':sha(__file__),'elapsed_seconds':time.time()-started,
        'threads':{k:os.environ[k] for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS')},
        'historical_QPS_source':str(OLD/'analysis/final_v1/points.csv'),'geometry_source_scope':'sample8192 plus all original GT100 target vectors',
        'audit_scope':'same executor crosschecks; independent method integer audit supplied separately'})

if __name__=='__main__': main()
