"""Reconstruct and join existing evidence. No ANN or NSG search calls, no old writes."""
import time
import hashlib
from pathlib import Path
import numpy as np
from common import *

def existing_protection():
    target=RUN/'reviews/old_assets_before.json'
    if target.exists():
        return read(target)
    records=[]
    for version,base in VERSIONS.items():
        for p in sorted(base.rglob('*')):
            if p.is_file():
                st=p.stat();records.append({'path':str(p),'bytes':st.st_size,'mtime_ns':st.st_mtime_ns,'sha256':sha(p)})
    dump(target,{'files':records,'total_bytes':sum(x['bytes'] for x in records)})
    return {'files':records}

def reconstruct(ds):
    start=time.monotonic();base=VERSIONS[24];inp=base/'inputs'/ds
    meta=read(inp/'prepared.json');n=20000;h,d=meta['H'],meta['dim']
    for ident in meta['source_train'].values():
        p=track(ident['path']);assert SOURCES[str(p)]['sha256']==ident['sha256']
    q=norm(arr(inp/'fit/queries.f32','<f4',(n,d)))
    gt=arr(inp/'fit/gt.i64','<i8',(n,100));rows=arr(inp/'fit/row_ids.i64','<i8')
    assert np.array_equal(rows,np.arange(10000,30000))
    raw=norm(arr(inp/'raw_hubs.f32','<f4',(h,d)));hids=arr(inp/'hub_ids.i32','<i4')
    assert len(hids)==h and (np.diff(hids)>0).all()
    source=np.memmap(meta['base_file'],mode='r',dtype='<f4').reshape(-1,d+1)
    assert len(source)==meta['base_rows']
    assert np.array_equal(source[hids,1:],arr(inp/'raw_hubs.f32','<f4',(h,d)))
    selection=read(base/'models'/ds/'selection.json')
    names=['gt1_hard','gt10_hard']+[selection['selected_families'][x]['name'] for x in ['gt1_soft','gt10_soft']]
    manifests={name:read(base/'models'/ds/name/'manifest.json') for name in names}
    a={name:np.zeros((n,h),'float64') for name in names}
    rank_hubs=np.empty((n,10),'<i4');rank_norms=np.empty((n,10),'float32');ties=0
    for rank in range(10):
        target=np.asarray(source[gt[:,rank],1:],dtype='float32');rank_norms[:,rank]=np.linalg.norm(target,axis=1);tn=norm(target)
        for st in range(0,n,4096):
            stop=min(st+4096,n);s=tn[st:stop]@raw.T;best=np.argmax(s,axis=1);ix=np.arange(st,stop)
            rank_hubs[st:stop,rank]=best;ties+=int((np.sum(s==s.max(1,keepdims=True),axis=1)>1).sum())
            a['gt10_hard'][ix,best]+=.1
            if rank==0:a['gt1_hard'][ix,best]=1.
            for name in names[2:]:
                m=manifests[name]
                if rank>=m['K_gt']:continue
                z=s.astype('float64');z-=z.max(1,keepdims=True);z/=m['temperature'];np.exp(z,out=z);z/=z.sum(1,keepdims=True)
                a[name][st:stop]+=z/m['K_gt']
    records=[];profile_info={};checks=[]
    for name in names:
        m=manifests[name];w=a[name];p=arr(m['W'],'<f4',(h,d))
        assert SOURCES[str(Path(m['W']).resolve())]['sha256']==m['W_identity']['sha256']
        digest=hashlib.sha256(w.tobytes()).hexdigest()
        expected_digest=m.get('assignments_sha256')
        if expected_digest is None:
            ident=m['assignments_identity'];assert sha(track(ident['path']))==ident['sha256']
            expected_digest=ident['sha256']
        assert digest==expected_digest,(ds,name,'assignment digest')
        assert np.max(np.abs(w.sum(1)-1))<1e-12
        saved=np.load(track(base/'models'/ds/name/'support.npz'))
        mass=w.sum(0);sq=(w*w).sum(0);ess=np.divide(mass*mass,sq,out=np.zeros(h),where=sq>0)
        assert np.array_equal(mass,saved['mass']) and np.array_equal(ess,saved['ess'])
        sums=w.T@q.astype('float64');rebuilt=norm(raw.astype('float64')+sums).astype('float32')
        err=float(np.max(np.abs(rebuilt-p)))
        # Reduction order depends on BLAS threads; the original 32-bit control is separate.
        assert err<2e-6,(ds,name,err)
        concentration=np.divide(np.linalg.norm(sums,axis=1),mass,out=np.zeros(h),where=mass>0)
        p0=arr(base/'models'/ds/'gt1_hard/W.f32','<f4',(h,d))
        angles=np.degrees(np.arccos(np.clip(np.sum(norm(p.astype('float64'))*norm(p0.astype('float64')),axis=1),-1,1)))
        if name=='gt1_hard':angles[:]=0
        support_count=(w>0).sum(0);prior=1/(1+mass)
        for j in range(h):
            records.append({'dataset':ds,'model':name,'hub_id':int(hids[j]),'mass':float(mass[j]),'ESS':float(ess[j]),
              'positive_query_count':int(support_count[j]),'query_direction_concentration':float(concentration[j]),
              'prior_mass_fraction':float(prior[j]),'angle_from_GT1_degrees':float(angles[j]),
              'query_sum_norm':float(np.linalg.norm(sums[j]))})
        profile_info[name]={'mass':mass,'ess':ess,'angle':angles,'concentration':concentration,'W':p}
        checks.append({'model':name,'assignment_digest_match':True,'support_exact_match':True,'max_abs_W_reduction_error':err,
            'mass':desc(mass),'ESS':desc(ess),'positive_query_count':desc(support_count),'direction_concentration':desc(concentration),
            'prior_mass_fraction':desc(prior),'angle_degrees':desc(angles),'zero_support_hubs':int((mass==0).sum()),
            'ESS_lt5_hubs':int((ess<5).sum()),'ESS_lt10_hubs':int((ess<10).sum())})
    hard=a['gt10_hard'];off=1-hard[np.arange(n),rank_hubs[:,0]]
    unique=np.array([len(set(x)) for x in rank_hubs]);trans=np.zeros((h,h),'<i8')
    for rank in range(1,10):np.add.at(trans,(rank_hubs[:,0],rank_hubs[:,rank]),1)
    rankrows=[]
    for rank in range(10):
        rankrows.append({'dataset':ds,'rank':rank+1,'same_hub_as_GT1_fraction':float(np.mean(rank_hubs[:,rank]==rank_hubs[:,0])),
            'distinct_hubs':int(len(np.unique(rank_hubs[:,rank]))),'target_norm_mean':float(rank_norms[:,rank].mean()),
            'target_norm_median':float(np.median(rank_norms[:,rank]))})
    np.savez_compressed(RUN/'results'/f'{ds}_fit_assignments.npz',row_ids=rows,hub_ids=hids,rank_hubs=hids[rank_hubs],
        moved_mass=off,unique_hubs=unique,rank_target_norms=rank_norms,tail_transition_counts=trans)
    csv_write(RUN/'results'/f'{ds}_hub_profiles.csv',records)
    csv_write(RUN/'results'/f'{ds}_rank_to_hub.csv',rankrows)
    summary={'rank_table':rankrows,'distinct_GT_hubs':desc(unique),'all_ten_same_hub_queries':int((unique==1).sum()),
        'off_GT1_mass':desc(off),'total_transferred_query_mass':float(off.sum()),'exact_score_ties':ties,
        'reconstructed_profiles':checks,'seconds':time.monotonic()-start}
    print(ds,'FIT',{'mean_hubs':unique.mean(),'moved_mass':off.mean(),'all_same':int((unique==1).sum())},flush=True)
    return summary,profile_info,hids

def verify_e24(ds):
    out={};metrics=[];checks=[]
    for stage in ['cal','audit','validation']:
        folder=VERSIONS[24]/('results' if stage=='validation' else 'diagnostics')/ds
        if stage!='validation':folder/=stage
        result=read(folder/'results.json');config=read(folder/'config.json');tc=read(folder/'thread_contract.json')
        n=config['num_queries'];d=config['dim'];assert tc['actual_openmp_threads']==tc['process_threads']==result['threads']==1
        assert tc['cpu']==15 and config['threads']==1 and config['gt_k']==100 and result['status']=='COMPLETE'
        rows=arr(folder/'row_ids.i64','<i8');assert np.array_equal(rows,arr(config['row_ids'],'<i8'))
        gt=arr(config['gt_file'],'<i8',(n,100));q=arr(config['queries_file'],'<f4',(n,d))
        points={}
        for m in result['methods']:
            z=load_point(folder,m,n);ids=z['ids'];mask=np.zeros(n,'<u2')
            for rank in range(10):mask|=(ids==gt[:,rank,None]).any(1).astype('<u2')<<rank
            hits=np.array([int(x).bit_count() for x in mask],dtype='u1')
            assert np.array_equal(mask,z['masks']) and np.array_equal(hits,z['hits'])
            assert int(hits.sum())==m['total_hits'] and abs(hits.mean()/10-m['recall_at_10'])<1e-12
            assert abs(z['r'].mean()-m['mean_route_ndc'])<1e-12 and abs(z['g'].mean()-m['mean_graph_ndc'])<1e-12
            assert np.isfinite(z['bits'].view('<f4')).all() and (np.diff(np.sort(ids,1),axis=1)>0).all()
            mc=m['configuration'];name=mc.get('model_name',m['family']);exact=mc.get('exact',False)
            if m['family']!='nsg_medoid':
                if mc['canonical_entry_order']:assert (np.diff(z['entries'],axis=1)>0).all()
                if name not in ['fast30k_3']:
                    ident=read(VERSIONS[24]/'models'/ds/name/'manifest.json')['W_identity']
                    assert sha(mc['W'])==ident['sha256']
            else:assert (z['r']==0).all()
            if config['measure_wall']:assert abs(m['qps']-n/m['end_to_end_seconds'])<1e-8
            else:assert m['qps'] is None
            points[(name,exact,m['L'])]=(m,z)
            metrics.append({'dataset':ds,'stage':stage,'model':name,'family':m['family'],'exact':exact,'L':m['L'],
                'recall_percent':float(hits.mean()*10),'qps':m['qps'],'route_ndc':float(z['r'].mean()),'graph_ndc':float(z['g'].mean()),
                'total_wall_seconds':m['end_to_end_seconds'],'route_only_seconds':m['route_only_seconds'],'graph_only_seconds':m['graph_only_seconds'],
                'source_folder':str(folder/m['name'])})
            checks.append({'stage':stage,'method':m['name'],'n':n,'status':'PASS'})
        out[stage]={'points':points,'rows':rows,'gt':gt,'q':q,'folder':folder}
    return out,metrics,checks

def same_entries(z0,z1):
    same=np.all(np.sort(z0['entries'],1)==np.sort(z1['entries'],1),axis=1)
    for field in ['ids','bits','hits','masks','g']:
        assert np.array_equal(z0[field][same],z1[field][same]),('same_entries_result',field)
    return same

def make_pairs(ds,data,profiles,hids):
    pairs=[];groups=[];cases=[];features={};ann=[]
    for stage,item in data.items():
        n=len(item['rows']);qnorm=norm(item['q'].astype('float64'));points=item['points']
        for exact in [False,True]:
            if stage=='validation' and exact:continue
            for L in (LS if stage=='validation' else [128]):
                m0,z0=points[('gt1_hard',exact,L)]
                for (name,ex,l),(m1,z1) in points.items():
                    if ex!=exact or l!=L or name=='gt1_hard':continue
                    ef=effect(z0['hits'],z1['hits']);dd=z1['hits'].astype('int16')-z0['hits'].astype('int16')
                    same=same_entries(z0,z1);over=(z0['entries'][:,:,None]==z1['entries'][:,None,:]).any(2).sum(1)
                    rec={'dataset':ds,'stage':stage,'model':name,'exact':exact,'L':L,**ef,
                         'changed_entries':int((~same).sum()),'mean_entry_overlap':float(over.mean()),
                         'same_entries_nonzero_effect':int(np.count_nonzero(dd[same])),
                         'delta_route_ndc':float(z1['r'].astype('int64').mean()-z0['r'].mean()),
                         'delta_graph_ndc_percent':float(100*(z1['g'].mean()/z0['g'].mean()-1)),
                         'delta_qps_percent':100*(m1['qps']/m0['qps']-1) if m0['qps'] is not None else None}
                    if name=='gt10_hard':
                        lo,hi=bootstrap(dd);rec.update(CI95_low=lo,CI95_high=hi)
                        idx0=np.searchsorted(hids,z0['entries']);idx1=np.searchsorted(hids,z1['entries'])
                        feat={'base_logESS_mean':np.log1p(profiles['gt1_hard']['ess'][idx0]).mean(1),
                              'base_angle_mean':profiles['gt10_hard']['angle'][idx0].mean(1),'overlap':over}
                        features[(stage,exact,L)]=feat
                        scores0=qnorm@profiles['gt1_hard']['W'].astype('float64').T
                        scores1=qnorm@profiles['gt10_hard']['W'].astype('float64').T
                        sorted0=np.sort(scores0,axis=1)[:,-4:];sorted1=np.sort(scores1,axis=1)[:,-4:]
                        margin0=sorted0[:,-3]-sorted0[:,-4];margin1=sorted1[:,-3]-sorted1[:,-4]
                        np.savez_compressed(RUN/'results'/f'{ds}_{stage}_{"exact" if exact else "hnsw"}_L{L}_paired.npz',
                            row_ids=item['rows'],entries0=z0['entries'],entries1=z1['entries'],hits0=z0['hits'],hits1=z1['hits'],
                            masks0=z0['masks'],masks1=z1['masks'],route_ndc0=z0['r'],route_ndc1=z1['r'],
                            graph_ndc0=z0['g'],graph_ndc1=z1['g'],delta_hits=dd,margin0=margin0,margin1=margin1,**feat)
                        for sign,selected in [('positive',dd>0),('neutral',dd==0),('negative',dd<0)]:
                            groups.append({'dataset':ds,'stage':stage,'exact':exact,'L':L,'group_type':'effect','group':sign,
                                **effect(z0['hits'][selected],z1['hits'][selected]),'denominator_all_queries':n,
                                'mean_overlap':float(over[selected].mean()) if selected.any() else None,
                                'base_logESS_mean':float(feat['base_logESS_mean'][selected].mean()) if selected.any() else None,
                                'base_angle_mean':float(feat['base_angle_mean'][selected].mean()) if selected.any() else None,
                                'margin0_mean':float(margin0[selected].mean()) if selected.any() else None,
                                'margin1_mean':float(margin1[selected].mean()) if selected.any() else None,
                                'delta_graph_ndc_mean':float((z1['g'].astype('int64')-z0['g'])[selected].mean()) if selected.any() else None})
                        # Case rule: largest gain and largest loss; ties smallest original row ID.
                        for sign,value in [('positive',dd.max()),('negative',dd.min())]:
                            if (sign=='positive' and value<=0) or (sign=='negative' and value>=0):continue
                            ii=np.flatnonzero(dd==value);i=ii[np.argmin(item['rows'][ii])]
                            cases.append({'dataset':ds,'stage':stage,'exact':exact,'L':L,'case':sign,'row_id':int(item['rows'][i]),
                                'delta_hits':int(dd[i]),'entries0':z0['entries'][i].tolist(),'entries1':z1['entries'][i].tolist(),
                                'hits0':int(z0['hits'][i]),'hits1':int(z1['hits'][i]),'mask0':int(z0['masks'][i]),'mask1':int(z1['masks'][i]),
                                'graph_ndc0':int(z0['g'][i]),'graph_ndc1':int(z1['g'][i])})
                    pairs.append(rec)
        if stage!='validation':
            for name in sorted({k[0] for k in points}):
                mh,zh=points[(name,False,128)];me,ze=points[(name,True,128)]
                same=same_entries(zh,ze)
                ann.append({'dataset':ds,'stage':stage,'model':name,**effect(zh['hits'],ze['hits']),
                            'same_exact_HNSW_entries':int(same.sum()),'changed_entries':int((~same).sum())})
    boundaries={name:np.quantile(features[('cal',False,128)][name],[.25,.5,.75]).tolist()
                for name in ['base_logESS_mean','base_angle_mean']}
    for (stage,exact,L),feat in features.items():
        z0=data[stage]['points'][('gt1_hard',exact,L)][1];z1=data[stage]['points'][('gt10_hard',exact,L)][1]
        for name,values in feat.items():
            bins=values if name=='overlap' else np.searchsorted(boundaries[name],values,side='right')
            for group in range(4):
                sel=bins==group
                groups.append({'dataset':ds,'stage':stage,'exact':exact,'L':L,'group_type':name,'group':group,
                    **effect(z0['hits'][sel],z1['hits'][sel]),'denominator_all_queries':len(sel)})
    z0=[data['validation']['points'][('gt1_hard',False,L)][1] for L in LS]
    z1=[data['validation']['points'][('gt10_hard',False,L)][1] for L in LS]
    for z in [z0,z1]:
        assert all(np.array_equal(z[0]['entries'],item['entries']) for item in z)
    dd=np.stack([b['hits'].astype('int16')-a['hits'].astype('int16') for a,b in zip(z0,z1)],axis=1)
    cross={'any_positive_query':int((dd>0).any(1).sum()),'any_negative_query':int((dd<0).any(1).sum()),
           'both_signs_query':int(((dd>0).any(1)&(dd<0).any(1)).sum()),'all_L_neutral_query':int((dd==0).all(1).sum()),
           'net_hits_by_L':dd.sum(0).tolist()}
    return pairs,groups,ann,boundaries,cases,cross

def repetition(ds,data):
    rows=[];checks=[];development=[]
    primary='gt10_hard' if ds==DATASETS[1] else read(VERSIONS[24]/'models'/ds/'selection.json')['primary']['name']
    for version in [24,25,26]:
        folder=VERSIONS[version]/'results'/ds;result=read(folder/'results.json');config=read(folder/'config.json')
        tc=read(folder/'thread_contract.json');assert result['threads']==config['threads']==1
        assert tc['process_threads']==tc['actual_openmp_threads']==1
        n=result['queries'];rr=arr(folder/'row_ids.i64','<i8')
        assert np.array_equal(rr,data['validation']['rows'])
        for L in LS:
            methods={m['family']:m for m in result['methods'] if m['L']==L}
            b=methods['gt1_hard' if version==24 else 'fast20k'];m=methods['gt10_hard' if version==24 and ds==DATASETS[1] else ('gt10_soft' if version==24 else 'e24')]
            for name,point in [('gt1_hard',b),(primary,m)]:
                z=load_point(folder,point,n);old=data['validation']['points'][(name,False,L)][1]
                for field in z:assert np.array_equal(z[field],old[field]),(ds,version,name,L,field)
                checks.append({'version':version,'model':name,'L':L,'all_seven_raw_fields_bit_equal':True})
            q0=b.get('qps_runs',[b['qps']]);q1=m.get('qps_runs',[m['qps']])
            for i,(x,y) in enumerate(zip(q0,q1)):
                rows.append({'dataset':ds,'version':version,'model':primary,'L':L,'repeat':i,
                    'GT1_qps':x,'GT10_qps':y,'delta_qps_percent':100*(y/x-1),
                    'batch_median_delta_qps_percent':100*(m['qps']/b['qps']-1),
                    'GT1_recall_percent':100*b['recall_at_10'],'GT10_recall_percent':100*m['recall_at_10'],
                    'GT1_route_only_seconds':b['route_only_seconds'],'GT10_route_only_seconds':m['route_only_seconds'],
                    'GT1_graph_only_seconds':b['graph_only_seconds'],'GT10_graph_only_seconds':m['graph_only_seconds']})
        if version>24:
            for stage in ['cal','audit']:
                f=VERSIONS[version]/'diagnostics'/ds/stage;r=read(f/'results.json')
                for L in [64,128]:
                    points={m['family']:m for m in r['methods'] if m['L']==L};b=points['fast20k'];m=points['e24']
                    h0=load_point(f,b,r['queries'])['hits'];h1=load_point(f,m,r['queries'])['hits']
                    development.append({'dataset':ds,'version':version,'stage':stage,'L':L,'model':primary,**effect(h0,h1)})
    return rows,checks,development

def main():
    started=time.monotonic();assert not (RUN/'results/existing_evidence.json').exists(),'refuse overwrite completed analysis'
    old=existing_protection();allmetrics=[];allpairs=[];allgroups=[];allann=[];allrep=[];alldev=[];allcases=[];report={};verify=[]
    for ds in DATASETS:
        fit,profiles,hids=reconstruct(ds)
        data,metrics,checks=verify_e24(ds)
        pairs,groups,ann,bounds,cases,cross=make_pairs(ds,data,profiles,hids)
        rep,repchecks,dev=repetition(ds,data)
        report[ds]={'fit':fit,'cal_feature_quartile_boundaries':bounds,'cross_L':cross,
                    'hard_pair_summary':[x for x in pairs if x['model']=='gt10_hard'],'repeat_checks':repchecks}
        allmetrics+=metrics;allpairs+=pairs;allgroups+=groups;allann+=ann;allrep+=rep;alldev+=dev;allcases+=cases;verify+=checks
        print(ds,'PAIRS',report[ds]['hard_pair_summary'],flush=True)
    frontier=[]
    for ds in DATASETS:
        mm=[m for m in allmetrics if m['dataset']==ds and m['stage']=='validation' and m['model'] in ['gt1_hard','gt10_hard']]
        for m in mm:
            dominated=any(x['recall_percent']>=m['recall_percent'] and x['qps']>=m['qps'] and (x['recall_percent']>m['recall_percent'] or x['qps']>m['qps']) for x in mm)
            frontier.append({**m,'nondominated_in_hard_pair':not dominated})
    for name,rows in [('all_metrics',allmetrics),('all_pairs',allpairs),('query_groups',allgroups),('exact_HNSW',allann),
                      ('repetition',allrep),('later_development',alldev),('hard_frontier',frontier)]:csv_write(RUN/'results'/f'{name}.csv',rows)
    dump(RUN/'results/cases.json',allcases)
    dump(RUN/'results/existing_evidence.json',{'status':'EXISTING_EVIDENCE_COMPLETE','datasets':report,'new_search_calls':0,
       'analysis_seconds':time.monotonic()-started,'historical_validation':True,'heldout_access':False})
    dump(RUN/'reviews/existing_verification.json',{'status':'PASS','points':len(verify),'rescored_outputs':sum(x['n'] for x in verify),
        'points_detail':verify,'source_files':len(SOURCES),'new_search_calls':0})
    dump(RUN/'reviews/existing_sources.json',{'files':list(SOURCES.values())})
    print('EXISTING_ANALYSIS_COMPLETE',len(verify),sum(x['n'] for x in verify),time.monotonic()-started,flush=True)

if __name__=='__main__':main()
