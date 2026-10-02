"""GT rank/region diagnostics on already scored queries; no graph or ANN search."""
from common import *

def main():
    assert (RUN/'results/existing_evidence.json').exists()
    rows=[];byrank=[];freqs=[];numeric=[]
    for ds in DATASETS:
        base=VERSIONS[24];inp=base/'inputs'/ds;meta=read(inp/'prepared.json');h,d=meta['H'],meta['dim']
        hids=arr(inp/'hub_ids.i32','<i4');raw=norm(arr(inp/'raw_hubs.f32','<f4',(h,d)))
        bv=np.memmap(meta['base_file'],mode='r',dtype='<f4').reshape(-1,d+1)
        rankfit=np.load(RUN/'results'/f'{ds}_fit_assignments.npz')['rank_hubs']
        fq=norm(arr(inp/'fit/queries.f32','<f4',(20000,d)))
        a0=arr(base/'models'/ds/'gt1_hard/assignments.f64','<f8',(20000,h))
        w0=arr(base/'models'/ds/'gt1_hard/W.f32','<f4',(h,d))
        w64=norm(raw.astype('float64')+a0.T@fq.astype('float64')).astype('float32')
        ess0=np.load(track(base/'models'/ds/'gt1_hard/support.npz'))['ess']
        for stage in ['cal','audit','validation']:
            folder=base/('results' if stage=='validation' else 'diagnostics')/ds
            if stage!='validation':folder/=stage
            c=read(folder/'config.json');n=c['num_queries'];q=arr(c['queries_file'],'<f4',(n,d));gt=arr(c['gt_file'],'<i8',(n,100))
            rankhub=np.empty((n,10),'<i4')
            for rank in range(10):
                target=norm(np.asarray(bv[gt[:,rank],1:],dtype='float32'))
                rankhub[:,rank]=hids[np.argmax(target@raw.T,axis=1)]
            np.savez_compressed(RUN/'results'/f'{ds}_{stage}_GT_target_hubs.npz',row_ids=arr(c['row_ids'],'<i8'),rank_hubs=rankhub)
            # Finite-precision diagnostic only: no new W is deployed or searched.
            score0=q.astype('float64')@w0.astype('float64').T
            score64=q.astype('float64')@w64.astype('float64').T
            top0=np.sort(np.argsort(-score0,axis=1,kind='stable')[:,:3],axis=1)
            top64=np.sort(np.argsort(-score64,axis=1,kind='stable')[:,:3],axis=1)
            numeric.append({'dataset':ds,'stage':stage,'queries':n,'W_max_abs_error':float(np.abs(w64-w0).max()),
                'score64_vs_score32_max_abs_error':float(np.abs(score0-score64).max()),
                'double_score_exact_top3_changed':int(np.any(top0!=top64,axis=1).sum()),
                'scope':'float64 scoring diagnostic, not a new float32-kernel or HNSW deployment'})
            for exact in ([False] if stage=='validation' else [False,True]):
                for L in (LS if stage=='validation' else [128]):
                    pair=np.load(RUN/'results'/f'{ds}_{stage}_{"exact" if exact else "hnsw"}_L{L}_paired.npz')
                    e0,e1=pair['entries0'],pair['entries1'];h0,h1=pair['hits0'],pair['hits1'];delta=pair['delta_hits']
                    cover0=(rankhub[:,:,None]==e0[:,None,:]).any(2);cover1=(rankhub[:,:,None]==e1[:,None,:]).any(2)
                    new=(e1[:,:,None]!=e0[:,None,:]).all(2);old=(e0[:,:,None]!=e1[:,None,:]).all(2)
                    ii0=np.searchsorted(hids,e0);ii1=np.searchsorted(hids,e1)
                    for j in range(h):
                        freqs.append({'dataset':ds,'stage':stage,'exact':exact,'L':L,'hub_id':int(hids[j]),
                          'GT1_frequency':int((e0==hids[j]).sum()),'GT10_frequency':int((e1==hids[j]).sum()),'fit_GT1_ESS':float(ess0[j])})
                    for group,sel in [('all',np.ones(n,bool)),('positive',delta>0),('neutral',delta==0),('negative',delta<0),
                                      ('new_entry_has_ESS0_lt5',np.any(new&(ess0[ii1]<5),axis=1)),
                                      ('new_entry_has_ESS0_lt10',np.any(new&(ess0[ii1]<10),axis=1)),
                                      ('new_entry_has_ESS0_eq0',np.any(new&(ess0[ii1]==0),axis=1))]:
                        rows.append({'dataset':ds,'stage':stage,'exact':exact,'L':L,'group':group,**effect(h0[sel],h1[sel]),
                            'denominator_all_queries':n,
                            'GT_hub_cover_count0_mean':float(cover0[sel].sum(1).mean()) if sel.any() else None,
                            'GT_hub_cover_count1_mean':float(cover1[sel].sum(1).mean()) if sel.any() else None,
                            'GT1_hub_covered0_fraction':float(cover0[sel,0].mean()) if sel.any() else None,
                            'GT1_hub_covered1_fraction':float(cover1[sel,0].mean()) if sel.any() else None,
                            'new_entries_with_low_original_support':int((new[sel]&(ess0[ii1][sel]<5)).sum()),
                            'removed_entries_with_low_original_support':int((old[sel]&(ess0[ii0][sel]<5)).sum())})
                    for rank in range(10):
                        bit0=((pair['masks0']>>rank)&1).astype(bool);bit1=((pair['masks1']>>rank)&1).astype(bool)
                        byrank.append({'dataset':ds,'stage':stage,'exact':exact,'L':L,'GT_rank':rank+1,
                            'found0':int(bit0.sum()),'found1':int(bit1.sum()),'gained':int((~bit0&bit1).sum()),
                            'lost':int((bit0&~bit1).sum()),'net':int(bit1.sum())-int(bit0.sum()),
                            'target_hub_in_entries0':int(cover0[:,rank].sum()),'target_hub_in_entries1':int(cover1[:,rank].sum())})
                    assert sum(r['net'] for r in byrank[-10:])==int(delta.sum())
    for name,records in [('target_region_links',rows),('GT_rank_hit_changes',byrank),('entry_frequencies',freqs),('numeric_control',numeric)]:
        csv_write(RUN/'results'/f'{name}.csv',records)
    dump(RUN/'reviews/target_link_sources.json',{'files':list(SOURCES.values()),'new_search_calls':0,'status':'PASS'})
    print('TARGET_LINK_ANALYSIS_COMPLETE',len(rows),len(byrank),flush=True)

if __name__=='__main__':main()
