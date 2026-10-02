from common import *
from analyze_labels import vectors_in_nsg
import csv

def ci(delta,bootstrap):
    means=delta[bootstrap].mean(1)*100
    return [float(x) for x in np.quantile(means,[.025,.975])]

def analyze():
    metrics=[];checks=[];gates=[];aligned={};contrasts=[]
    families=['Identity','QLinear','QMLP','WFree']
    for ds in DS:
        root=RUN/'results'/ds/'quality';complete=read(root/'complete.json');assert complete['status']=='PASS'
        fit_c=read(RUN/'inputs'/ds/'fit/config.json');d=fit_c['dimension'];h=fit_c['hub_count']
        hubs=np.fromfile(fit_c['hub_ids'],'int32');base=vectors_in_nsg(fit_c['index'])
        for family in families:
            encoded=np.fromfile(root/f'{family}.encoded.f32','float32').reshape(2560,d)
            if family=='Identity':
                q=np.fromfile(fit_c['queries'],'float32').reshape(2048,d).astype('float64')
                reference=(q/np.linalg.norm(q,axis=1,keepdims=True)).astype('float32')
                weights=np.fromfile(fit_c['routers'][0]['W'],'float32').reshape(h,d)
            else:
                model=RUN/'models'/ds/family;mc=read(model/'model.json')
                reference=np.fromfile(model/'fit.encoded.f32','float32').reshape(2048,d)
                weights=np.fromfile(mc['W'],'float32').reshape(h,d)
            error=float(np.max(np.abs(encoded[:2048]-reference)))
            assert error<=2e-6,(ds,family,'C++/torch forward',error)
            score_error=None
            if family!='Identity':
                stored=np.fromfile(model/'fit.scores.f32','float32').reshape(2048,h)
                scores=encoded[:2048].astype('float64')@weights.astype('float64').T
                score_error=float(np.max(np.abs(scores-stored)));assert score_error<=1e-5
            checks.append(dict(dataset=ds,family=family,cpp_torch_encoded_max_error=error,score_max_error=score_error))
        offset=0
        for split in ['fit','cal']:
            c=read(RUN/'inputs'/ds/split/'config.json');n=c['n'];sl=slice(offset,offset+n)
            label=RUN/'labels'/ds/(split+'_labels')
            gt=np.fromfile(c['gt'],'int64').reshape(n,100);q=np.fromfile(c['queries'],'float32').reshape(n,d)
            candidates=hubs[np.fromfile(label/'triples.i32','int32').reshape(n,56,3)]
            slots=np.fromfile(label/'baseline_slots.i32','int32').reshape(n,2)[:,0]
            anchor_entries=np.fromfile(label/'anchor_entries.i32','int32').reshape(n,3)
            boot=np.random.default_rng(20260920).integers(0,n,size=(2000,n),dtype='int32')
            hits={};recalls={};graph_ndcs={};failures={};entry_by_method={}
            for K in [1,100]:
                hh=np.fromfile(label/f'k{K}.hits.u8','uint8').reshape(n,56)[np.arange(n),slots]
                hits[('GT10',K)]=hh;recalls[('GT10',K)]=hh.astype('float64')/K
                graph_ndcs[('GT10',K)]=np.fromfile(label/f'k{K}.ndc.u64','uint64').reshape(n,56)[np.arange(n),slots]
            support_fraction={};exact_ann_entry_difference={}
            for family in families:
                ae=np.fromfile(root/(family+'ANN')/'entries.i32','int32').reshape(2560,3)[sl]
                ee=np.fromfile(root/(family+'Exact')/'entries.i32','int32').reshape(2560,3)[sl]
                exact_ann_entry_difference[family]=float((ae!=ee).any(1).mean())
                for route in ['ANN','Exact']:
                    method=family+route;sub=root/method
                    entries=np.fromfile(sub/'entries.i32','int32').reshape(2560,3)[sl];entry_by_method[method]=entries
                    matches=(entries[:,None,:]==candidates).all(2);supported=matches.any(1);matchslot=matches.argmax(1)
                    support_fraction[method]=float(supported.mean());ids_by_k={};dist_by_k={};ndc_by_k={}
                    for K in [1,100]:
                        ids=np.fromfile(sub/f'k{K}.ids.i32','int32').reshape(2560,K)[sl]
                        dist=np.fromfile(sub/f'k{K}.distances.f32','float32').reshape(2560,K)[sl]
                        ndc=np.fromfile(sub/f'k{K}.ndc.u64','uint64')[sl]
                        assert np.isfinite(dist).all() and ids.min()>=0 and ids.max()<c['base_n']
                        assert np.all(np.diff(dist,axis=1)>=0)
                        if K>1:assert np.all(np.diff(np.sort(ids,axis=1),axis=1)>0)
                        hh=np.array([np.isin(ids[i],gt[i,:K]).sum() for i in range(n)],dtype='uint8')
                        hits[(method,K)]=hh;recalls[(method,K)]=hh.astype('float64')/K;graph_ndcs[(method,K)]=ndc
                        cached_ids=np.memmap(label/f'k{K}.ids.i32',mode='r',dtype='int32',shape=(n,56,K))
                        cached_dist=np.memmap(label/f'k{K}.distances.f32',mode='r',dtype='float32',shape=(n,56,K))
                        cached_ndc=np.fromfile(label/f'k{K}.ndc.u64','uint64').reshape(n,56)
                        rr=np.flatnonzero(supported);tt=matchslot[rr]
                        assert np.array_equal(ids[rr],cached_ids[rr,tt]),'same ordered action ID regression'
                        assert np.array_equal(dist[rr].view('uint32'),cached_dist[rr,tt].view('uint32')),'same ordered action distance bits'
                        assert np.array_equal(ndc[rr],cached_ndc[rr,tt]),'same ordered action NDC regression'
                        for i in np.linspace(0,n-1,8,dtype=int):
                            true_dist=-(base[ids[i]].astype('float64')@q[i].astype('float64'))
                            assert np.allclose(dist[i],true_dist,rtol=2e-5,atol=2e-5),'NSG must still use raw query'
                        ids_by_k[K]=ids;dist_by_k[K]=dist;ndc_by_k[K]=ndc
                        aligned[f'{ds}.{split}.{method}.K{K}.hits']=hh
                    assert np.array_equal(ids_by_k[1][:,0],ids_by_k[100][:,0])
                    assert np.array_equal(dist_by_k[1][:,0].view('uint32'),dist_by_k[100][:,0].view('uint32'))
                    assert np.array_equal(ndc_by_k[1],ndc_by_k[100])
            # Identity conversion has to reproduce the actual deployed anchor on this data.
            assert np.array_equal(entry_by_method['IdentityANN'],anchor_entries)
            for K in [1,100]:
                assert np.array_equal(hits[('IdentityANN',K)],hits[('GT10',K)])
                assert np.array_equal(graph_ndcs[('IdentityANN',K)],graph_ndcs[('GT10',K)])
            for method in ['GT10']+[f+r for f in families for r in ['ANN','Exact']]:
                for K in [1,100]:
                    rr=recalls[(method,K)];anchor=recalls[('GT10',K)];delta=rr-anchor;interval=ci(delta,boot)
                    row=dict(dataset=ds,split=split,n=n,method=method,K=K,L=128,recall=float(rr.mean()),
                             delta_gt10_pp=float(delta.mean()*100),ci95_low_pp=interval[0],ci95_high_pp=interval[1],
                             improved_queries=int((delta>0).sum()),harmed_queries=int((delta<0).sum()),
                             zero_queries=int((rr==0).sum()),rescued_zero=int(((anchor==0)&(rr>0)).sum()),
                             newly_zero=int(((anchor>0)&(rr==0)).sum()),graph_ndc_mean=float(graph_ndcs[(method,K)].mean()),
                             outside_label_pool_fraction=1-support_fraction.get(method,1.),
                             exact_ann_entry_difference_fraction=exact_ann_entry_difference.get(method.replace('ANN','').replace('Exact',''),0.))
                    metrics.append(row)
            gate_by_route={}
            for route,baseline in [('ANN','GT10'),('Exact','IdentityExact')]:
                method='QMLP'+route
                changes=[int(hits[(method,K)].sum())-int(hits[(baseline,K)].sum()) for K in [1,100]]
                gains=[changes[j]/n/K*100 for j,K in enumerate([1,100])]
                base_pass=min(changes)>=0 and max(gains)>=.5
                control_checks=[]
                for other in ['QLinear'+route,'WFree'+route]:
                    dsums=[int(hits[(method,K)].sum())-int(hits[(other,K)].sum()) for K in [1,100]]
                    control_checks.append(dict(control=other,delta_hits=dsums,pass_gate=min(dsums)>=0 and max(dsums)>0))
                    if split=='cal':
                        for K in [1,100]:
                            delta=recalls[(method,K)]-recalls[(other,K)]
                            contrasts.append(dict(dataset=ds,split=split,route=route,K=K,comparison=method+' minus '+other,
                                                  delta_pp=float(delta.mean()*100),ci95_pp=ci(delta,boot)))
                gate_by_route[route]=dict(baseline=baseline,delta_pp=gains,anchor_pass=base_pass,controls=control_checks,
                                           passed=base_pass and all(x['pass_gate'] for x in control_checks))
            if split=='cal':gates.append(dict(dataset=ds,primary_ANN_gate=gate_by_route['ANN'],exact_diagnostic_gate=gate_by_route['Exact']))
            offset+=n
    np.savez(RUN/'results/quality_aligned.npz',**aligned)
    with (RUN/'results/quality_metrics.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=list(metrics[0]));writer.writeheader();writer.writerows(metrics)
    dump(RUN/'results/quality_metrics.json',metrics);dump(RUN/'results/control_contrasts.json',contrasts)
    passed=all(g['primary_ANN_gate']['passed'] for g in gates)
    result=dict(status='PASS_REPRESENTATION_GO_WALL' if passed else 'STOP_REPRESENTATION',datasets=gates,
                implementation_checks=checks,identity_ANN_matches_original_GT10=True,
                supported_actions_match_cached_ID_distance_bits_NDC=True,new_model_main_search_calls=81920,
                descriptive_query_bootstrap=dict(repeats=2000,seed=20260920,independent_fresh_test=False),
                source=identity(Path(__file__)))
    dump(RUN/'reviews/representation_gate.json',result)
    for row in metrics:
        if row['split']=='cal' and row['method'] in ('GT10','QLinearANN','QMLPANN','WFreeANN'):
            print(json.dumps(row),flush=True)
    print('GATE',json.dumps(result),flush=True)
    return result

if __name__=='__main__':analyze()
