import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='1'
os.sched_setaffinity(0,{14})
import hashlib,json,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent;C=json.loads((R/'config.locked.json').read_text())
def ident(p):
    p=Path(p);return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(16<<20),b''):h.update(b)
    return h.hexdigest()
def exact_bootstrap_check(strata,samples):
    # Exact empirical-bootstrap distribution via polynomial powers, independent of RNG implementation.
    bounds=[(int(np.min(v)),int(np.max(v)),len(v)) for v in strata];lo=sum(a*n for a,b,n in bounds);width=sum((b-a)*n for a,b,n in bounds)
    nfft=1<<(max(width+1,2)-1).bit_length();character=np.ones(nfft,dtype='complex128')
    for values,(minimum,maximum,n) in zip(strata,bounds):
        pmf=np.bincount(values.astype('i8')-minimum,minlength=maximum-minimum+1)/n
        character*=np.fft.fft(pmf,nfft)**n
    prob=np.fft.ifft(character).real[:width+1];assert prob.min()>-1e-10;prob=np.maximum(prob,0);prob/=prob.sum();cdf=np.cumsum(prob)
    actual,counts=np.unique(samples,return_counts=True);positions=actual.astype('i8')-lo;assert positions.min()>=0 and positions.max()<len(cdf)
    empirical=np.cumsum(counts)/len(samples);before=empirical-counts/len(samples)
    left=np.where(positions>0,cdf[np.maximum(positions-1,0)],0);ks=max(float(np.max(np.abs(empirical-cdf[positions]))),float(np.max(np.abs(before-left))))
    assert ks<.02,(ks,lo,width)
    return ks,[int(np.searchsorted(cdf,q))+lo for q in [.025,.975]]
def main():
    start=time.perf_counter();summary=json.loads((R/'results/summary.json').read_text());boot=np.load(R/'results/aligned_hits_and_bootstrap.npz')
    complete=json.loads((R/'reviews/run_complete.json').read_text());assert complete['status']=='COMPUTED_PENDING_INDEPENDENT_AUDIT'
    hits={};ids_by_case={};recall_queries=0;distance_query_groups=0;comparisons=0;ksmax=0.;native_calls=router_calls=0;source_records={};gap_records={}
    for case,c in C['cases'].items():
        inp=R/'inputs'/case;manifest=json.loads((inp/'manifest.json').read_text());n,d=c['n'],c['dimension']
        query=np.fromfile(inp/'queries.f32','<f4').reshape(n,d);rows=np.fromfile(inp/'source_rows.i64','<i8');candidate=np.fromfile(inp/'candidate_source.f32','<f4').reshape(20000,d)
        assert len(rows)==n and (np.diff(rows)>0).all() and rows.min()>=c['source_start'] and rows.max()<c['source_start']+20000
        assert np.array_equal(query,candidate[rows-c['source_start']]) and np.isfinite(query).all() and (np.linalg.norm(query,axis=1)>0).all()
        excluded=set()
        for item in manifest['excluded_files']:
            p=Path(item['path']);assert sha(p)==item['sha256']
            if p.suffix=='.fvecs':a=np.memmap(p,'<f4',mode='r').reshape(-1,d+1)[:,1:]
            else:a=np.fromfile(p,'<f4').reshape(-1,d)
            excluded.update(hashlib.sha256(row.tobytes()).digest() for row in a)
        actualhashes=[hashlib.sha256(row.tobytes()).digest() for row in query];assert len(set(actualhashes))==n and not (set(actualhashes)&excluded)
        # Verify earliest valid rows, including within-window duplication, without trusting stored skip counts.
        expected=[];duplicate=invalid=0
        for i,row in enumerate(candidate):
            if not np.isfinite(row).all() or np.linalg.norm(row)==0:invalid+=1;continue
            h=hashlib.sha256(row.tobytes()).digest()
            if h in excluded:duplicate+=1;continue
            excluded.add(h);expected.append(c['source_start']+i)
            if len(expected)==n:break
        assert expected==rows.tolist() and duplicate==manifest['duplicates_skipped'] and invalid==manifest['invalid_skipped']
        for name,expected_sha in manifest['files'].items():assert sha(inp/name)==expected_sha
        gtmeta=json.loads((inp/'gt_manifest.json').read_text());assert gtmeta['status']=='PASS_EXACT_GT' and gtmeta['GT_sha256']==sha(inp/'gt.i32') and gtmeta['query_sha256']==sha(inp/'queries.f32')
        assert len(gtmeta['independent_float64_checks'])==8 and gtmeta['affinity']==list(range(8)) and gtmeta['GT_threads']==8
        gt=np.fromfile(inp/'gt.i32','<i4').reshape(n,100);gt_dist=np.fromfile(inp/'gt_ip.f32','<f4').reshape(n,100)
        assert (np.diff(gt_dist,axis=1)<=0).all() and (np.diff(np.sort(gt,axis=1),axis=1)>0).all()
        base=np.memmap(c['base'],'<f4',mode='r').reshape(c['base_n'],d+1)[:,1:];results=R/'results'/case;meta=json.loads((results/'complete.json').read_text())
        assert meta['threads']==1 and meta['cpu']==15 and meta['formal'] and meta['graph_builds']==0 and meta['wall_rounds']==len(c['methods'])*6
        assert complete['jobs'][case]['single_thread_samples']>0 and complete['jobs'][case]['max_threads']==1
        native_calls+=meta['search_calls'];router_calls+=meta['router_calls'];hits[case]={};ids_by_case[case]={};gap_records[case]={}
        for point in summary['cases'][case]['points']:
            k,L=point['K'],point['L'];point_hits={};point_ids={};entries={};dists={};ndcs={}
            for method in point['methods']:
                name=method['method'];p=results/f'k{k}'/f'{name}_L{L}';ii=np.fromfile(p/'ids.i32','<i4').reshape(n,k);dd=np.fromfile(p/'distances.f32','<f4').reshape(n,k)
                ee=np.fromfile(p/'entry_ids.i32','<i4').reshape(n,3);nn=np.fromfile(p/'graph_ndc.u64','<u8');rr=np.fromfile(p/'route_ndc.u64','<u8');pm=json.loads((p/'complete.json').read_text())
                assert pm['warm_plain_count_bit_parity'] and pm['formal'] and pm['threads']==1
                if k==1:h=(ii[:,0]==gt[:,0]).astype('i2')
                else:h=np.array([np.intersect1d(row,truth,assume_unique=True).size for row,truth in zip(ii,gt)],dtype='i2')
                assert np.array_equal(h,boot[f'{case}__K{k}__{name}__hits']) and int(h.sum())==method['hits']
                assert method['recall']==float(h.sum()/(n*k));np.testing.assert_allclose(method['QPS'],n/np.mean(pm['seconds']),rtol=1e-14)
                assert method['seconds']==pm['seconds'] and method['graph_ndc_mean']==float(nn.mean()) and method['route_ndc_mean']==float(rr.mean())
                for qid in np.arange(0,n,n//8):
                    calc=-np.array(base[ii[qid]],dtype='f8')@query[qid].astype('f8');np.testing.assert_allclose(calc,dd[qid],rtol=1e-5,atol=3e-5);distance_query_groups+=1
                point_hits[name]=h;point_ids[name]=ii;entries[name]=ee;dists[name]=dd;ndcs[name]=nn;recall_queries+=n
            for row in point['comparisons']:
                a,b=row['method'],row['reference'];delta=point_hits[a]-point_hits[b];key=f'{a}__vs__{b}';samples=boot[f'{case}__K{k}__{key}__boot_sums']
                assert row['delta_recall_pp']==float(delta.sum()/(n*k)*100)
                assert row['positive_queries']==int(np.sum(delta>0)) and row['negative_queries']==int(np.sum(delta<0))
                if k==1:rescue=int(np.sum(delta>0));damage=int(np.sum(delta<0))
                else:
                    rescue=damage=0
                    for ai,bi,truth in zip(point_ids[a],point_ids[b],gt):
                        ah=np.intersect1d(ai,truth,assume_unique=True);bh=np.intersect1d(bi,truth,assume_unique=True)
                        rescue+=np.setdiff1d(ah,bh,assume_unique=True).size;damage+=np.setdiff1d(bh,ah,assume_unique=True).size
                assert row['rescue_members']==rescue and row['damage_members']==damage and rescue-damage==int(delta.sum())
                same=np.all(entries[a]==entries[b],axis=1);assert np.array_equal(point_ids[a][same],point_ids[b][same])
                assert np.array_equal(dists[a][same].view('u4'),dists[b][same].view('u4')) and np.array_equal(ndcs[a][same],ndcs[b][same])
                assert int((~same).sum())==row['entry_changes'] and int(np.any(point_ids[a]!=point_ids[b],axis=1).sum())==row['output_id_changes']
                np.testing.assert_array_equal(np.quantile(samples,[.025,.975])/(n*k)*100,row['descriptive_95_interval_pp'])
                ks,_=exact_bootstrap_check([delta],samples);ksmax=max(ksmax,ks);comparisons+=1
                if k==1:
                    changed=np.flatnonzero(delta);gaps=(gt_dist[changed,0]-gt_dist[changed,1]).astype('f8')
                    gap_records[case][key]={'changed_hit_queries':len(changed),'GT1_minus_GT2_min':float(gaps.min()) if len(gaps) else None,'gap_le_2e_5':int(np.sum(gaps<=2e-5))}
            hits[case][k]=point_hits;ids_by_case[case][k]=point_ids
        source_records[case]={'rows':n,'byte_overlap':0,'duplicates_skipped':duplicate,'source_range':[c['source_start'],c['source_start']+20000]}
    for ds,record in summary['pooled_equal_batches'].items():
        cases=[f'{ds}_b0',f'{ds}_b1'];n=8192
        for point in record['points']:
            k=point['K']
            for m in point['methods']:
                name=m['method'];expected=sum(int(hits[case][k][name].sum()) for case in cases);assert expected==m['hits'] and m['recall']==expected/(n*k)
                raw=[next(x for p in summary['cases'][case]['points'] if p['K']==k for x in p['methods'] if x['method']==name) for case in cases]
                sums=np.array(raw[0]['seconds'])+np.array(raw[1]['seconds']);np.testing.assert_array_equal(sums,m['seconds_combined_per_round']);np.testing.assert_allclose(n/sums.mean(),m['QPS'],rtol=1e-14)
            for row in point['comparisons']:
                a,b=row['method'],row['reference'];strata=[hits[case][k][a]-hits[case][k][b] for case in cases];key=f'{a}__vs__{b}';samples=boot[f'{ds}__pooled__K{k}__{key}__boot_sums']
                assert row['delta_recall_pp']==sum(int(x.sum()) for x in strata)/(n*k)*100
                np.testing.assert_array_equal(np.quantile(samples,[.025,.975])/(n*k)*100,row['stratified_descriptive_95_interval_pp'])
                ks,_=exact_bootstrap_check(strata,samples);ksmax=max(ksmax,ks);comparisons+=1
    identities=0
    for fn,key in [('models_before_source.json','files'),('frozen_before_source.json','files')]:
        for p,v in json.loads((R/'reviews'/fn).read_text())[key].items():assert ident(p)==v;identities+=1
    for path,v in json.loads((R/'reviews/models_before_source.json').read_text())['large_stat_only'].items():
        s=Path(path).stat();assert s.st_size==v['bytes'] and s.st_mtime_ns==v['mtime_ns']
    assert ident(R/'bin/evaluate')==json.loads((R/'reviews/binary_before_source.json').read_text())['binary']
    assert native_calls==655872 and router_calls==655360 and recall_queries==131072 and comparisons==72
    assert recall_queries==summary['returned_query_vectors_rescored']
    result={'status':'PASS','seconds':time.perf_counter()-start,'source':ident(__file__),'identities':identities,'source_audit':source_records,
        'new_NSG_calls':native_calls,'new_ANN_calls':router_calls,'returned_query_vectors_rescored':recall_queries,'float64_return_distance_query_groups':distance_query_groups,
        'bootstrap_distribution_checks':comparisons,'maximum_bootstrap_CDF_KS_difference':ksmax,'K1_changed_hit_GT_gaps':gap_records,'default_changed':False}
    with (R/'reviews/independent_audit.json').open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print('AUDIT PASS',result['seconds'],'seconds',flush=True)
if __name__=='__main__':main()
