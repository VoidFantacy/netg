"""Post-search statistics; no native module is imported."""
from control import *

def cosine(a,b):
    den=float(np.linalg.norm(a)*np.linalg.norm(b))
    return float(a@b/den) if den>0 else None

def finite_mean_variance(g,n_population):
    n=g.shape[1];center=g.mean(1)
    return float((1-n/n_population)*np.square(g-center[:,None]).sum()/(n*(n-1)))

def write_csv(path,rows):
    assert not path.exists(),path
    with path.open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def raw_parts(ds,name):
    c=cfg(ds);idx=np.load(O/'inputs'/ds/'rows.npz');rows=idx['rows']
    gt=np.fromfile(c['gt_file'],np.int64).reshape(4096,100)[rows]
    base=dict(np.load(E/'results'/ds/'baseline.npz'))
    base={k:v[rows] for k,v in base.items() if k in FIELDS+['hits']}
    a=[dict(np.load(O/'results'/ds/name/f'action{j}.npz')) for j in range(8)]
    center=dict(np.load(O/'results'/ds/name/'center.npz'))
    for x in a+[center]: assert np.array_equal(x['rows'],rows)
    h=np.stack([score(x['ids'],gt) for x in a]).astype(float)
    hc=score(center['ids'],gt).astype(float);h0=score(base['ids'],gt).astype(float)
    assert np.array_equal(h0,base['hits'])
    ndc=np.stack([x['route_ndc'].astype(float)+x['graph_ndc'] for x in a])
    n0=base['route_ndc'].astype(float)+base['graph_ndc']
    parts=dict(hits=h-h0,cost=-.1*(ndc/n0-1),failure=-.1*((h==0).astype(float)-(h0==0).astype(float)))
    u=sum(parts.values());t=context(ds,name);m=(t['eps']-t['eps'].mean(0)).T/(7*.3)
    drift=np.array([read(O/'models'/ds/name/f'action{j}/identity.json')['drift'] for j in range(8)])
    return c,idx,gt,base,a,center,h,hc,h0,ndc,parts,u,m,drift

def analyze():
    start=time.monotonic();check(O/'reviews/prequery_freeze.json')
    jobs=read(O/'logs/jobs.json');assert len(jobs)==2 and all(j['status']=='COMPLETE' for j in jobs)
    assert sum(j['actual'] for j in jobs)==38592
    summaries=[];batch_rows=[];pair_rows=[];query_rows=[];group_rows=[]
    for di,ds in enumerate(DS):
        for ci,name in enumerate(['zero','selected']):
            c,idx,gt,base,a,center,h,hc,h0,ndc,parts,u,m,drift=raw_parts(ds,name)
            rows=idx['rows'];population=len(idx['eligible']);gs={k:m@v for k,v in parts.items()}
            g=sum(gs.values());reg=-m@drift;full=g.mean(1);total=full+reg
            assert np.allclose(g,m@u,rtol=1e-12,atol=1e-12)
            if name=='zero': equal(center,base)
            entry_changed=np.stack([np.any(x['entries']!=base['entries'],axis=1) for x in a])
            distinguish=np.ptp(h,axis=0)>0
            norms=np.linalg.norm(gs['hits'],axis=0);total_norm=norms.sum();big=int(np.argmax(norms))
            primary_data=cosine(g[:,:512].mean(1),g[:,512:].mean(1))
            primary_total=cosine(g[:,:512].mean(1)+reg,g[:,512:].mean(1)+reg)
            stats={}
            for k in [1,2,4,8]:
                combos=list(itertools.combinations(range(8),k)); means=[]; variances=[]; local_pairs=[]
                for comb in combos:
                    loc=np.concatenate([np.arange(v*128,(v+1)*128) for v in comb])
                    gg=g[:,loc];mean=gg.mean(1);v=finite_mean_variance(gg,population)
                    means.append(mean);variances.append(v)
                    group_rows.append(dict(dataset=ds,context=name,batch=128*k,blocks='-'.join(map(str,comb)),
                         data_norm=float(np.linalg.norm(mean)),total_norm=float(np.linalg.norm(mean+reg)),
                         query_variance_trace=v,conditional_snr=float(mean@mean/v-1) if v else None,
                         discriminating_queries=int(distinguish[loc].sum())))
                for ai,ca in enumerate(combos):
                    for bi in range(ai+1,len(combos)):
                        cb=combos[bi]
                        if set(ca).isdisjoint(cb):
                            v=dict(dataset=ds,context=name,batch=128*k,blocks_a='-'.join(map(str,ca)),
                              blocks_b='-'.join(map(str,cb)),cos_data=cosine(means[ai],means[bi]),
                              cos_total=cosine(means[ai]+reg,means[bi]+reg))
                            pair_rows.append(v);local_pairs.append(v)
                stat=dict(dataset=ds,context=name,batch=128*k,unique_groups=len(combos),
                          disjoint_pairs=len(local_pairs),mean_variance=float(np.mean(variances)),
                          median_data_norm=float(np.median(np.linalg.norm(means,axis=1))))
                for kind in ['data','total']:
                    vals=[x['cos_'+kind] for x in local_pairs if x['cos_'+kind] is not None]
                    stat['median_cos_'+kind]=float(np.median(vals)) if vals else None
                    stat['positive_fraction_'+kind]=float(np.mean(np.array(vals)>0)) if vals else None
                stats[128*k]=stat;batch_rows.append(stat)
            s512=stats[512]
            def gate(kind,primary):
                return bool(primary is not None and primary>=.3 and s512['median_cos_'+kind] is not None
                       and s512['median_cos_'+kind]>=.3 and s512['positive_fraction_'+kind]>=.75)
            sample_gap=h.mean(0)-hc
            rng=np.random.default_rng(2026091210+di*2+ci)
            blockmeans=sample_gap.reshape(8,128).mean(1)*10
            boot=blockmeans[rng.integers(0,8,size=(4000,8))].mean(1)
            oldmeta=read(O/'inputs'/ds/(name+'.json'));old=dict(np.load(oldmeta['trajectory']))
            oldgt=np.fromfile(c['gt_file'],np.int64).reshape(4096,100)[old['rows']]
            oldbase=dict(np.load(E/'results'/ds/'baseline.npz'))
            bh=oldbase['hits'][old['rows']].astype(float)
            oldh=np.stack([score(x,oldgt) for x in old['ids']]).astype(float)
            on=old['route_ndc'].astype(float)+old['graph_ndc']
            bn=oldbase['route_ndc'][old['rows']].astype(float)+oldbase['graph_ndc'][old['rows']]
            old_u=oldh-bh-.1*(on/bn-1)-.1*((oldh==0).astype(float)-(bh==0).astype(float))
            oldg=m@old_u.mean(1)
            variance=finite_mean_variance(g,population)
            st=dict(dataset=ds,context=name,model=oldmeta['model'],step=oldmeta['step'],population=population,
                discriminating_queries=int(distinguish.sum()),discriminating_pct=float(distinguish.mean()*100),
                entry_change_pct=float(entry_changed.mean()*100),hit_change_pct=float(np.mean(h!=h0)*100),
                primary512_cos_data=primary_data,primary512_cos_total=primary_total,
                balanced512_median_data=s512['median_cos_data'],balanced512_median_total=s512['median_cos_total'],
                balanced512_positive_data=s512['positive_fraction_data'],balanced512_positive_total=s512['positive_fraction_total'],
                stable_data=gate('data',primary_data),stable_total=gate('total',primary_total),
                stable=gate('data',primary_data) and gate('total',primary_total),
                full_data_norm=float(np.linalg.norm(full)),full_reg_norm=float(np.linalg.norm(reg)),
                full_total_norm=float(np.linalg.norm(total)),full_query_variance=variance,
                full_conditional_snr=float(full@full/variance-1),old128_new1024_cos_data=cosine(oldg,full),
                largest_query_row=int(rows[big]),largest_query_norm_share=float(norms[big]/total_norm) if total_norm else None,
                drop_largest_cos_data=cosine(full,np.delete(g,big,axis=1).mean(1)),
                sample_minus_center_recall_pp=float(sample_gap.mean()*10),
                sample_minus_center_block_CI_pp=np.quantile(boot,[.025,.975]).tolist(),
                center_minus_anchor_recall_pp=float((hc-h0).mean()*10),
                sample_minus_anchor_recall_pp=float((h-h0).mean()*10),
                sample_minus_center_helped=int((sample_gap>0).sum()),sample_minus_center_harmed=int((sample_gap<0).sum()),
                component_norms={k:float(np.linalg.norm(v.mean(1))) for k,v in gs.items()})
            summaries.append(st)
            source_ids=np.fromfile(c['row_ids'],np.int64)[rows]
            for j,row in enumerate(rows):
                query_rows.append(dict(dataset=ds,context=name,row=int(row),source_row_id=int(source_ids[j]),block=j//128,
                     anchor_hits=int(h0[j]),center_hits=int(hc[j]),sample_mean_hits=float(h[:,j].mean()),
                     discriminating=int(distinguish[j]),hit_gradient_norm=float(norms[j]),
                     data_gradient_norm=float(np.linalg.norm(g[:,j])),sample_center_delta_hits=float(sample_gap[j])))
            save_np(O/'results'/ds/(name+'_derived.npz'),rows=rows,hits=h,center_hits=hc,anchor_hits=h0,
                    U=u,G=g,reg=reg,M=m,drift=drift,full_data=full,full_total=total)
    decision=dict(status='FIXED_BATCH_DIAGNOSIS_COMPLETE',contexts=summaries,
        dataset_stable={ds:all(s['stable'] for s in summaries if s['dataset']==ds) for ds in DS},
        all_four_stable=all(s['stable'] for s in summaries),
        optimizer_updates=0,NSG_calls=sum(j['actual'] for j in jobs),HNSW_calls=sum(j['native']['HNSW_calls'] for j in jobs),
        builds=sum(j['native']['builds'] for j in jobs),analysis_seconds=time.monotonic()-start,
        actual_threads=next(int(line.split(':')[1]) for line in Path('/proc/self/status').read_text().splitlines() if line.startswith('Threads:')))
    assert decision['actual_threads']==1
    dump(O/'results/diagnosis.json',decision)
    for filename,data in [('contexts',summaries),('batches',batch_rows),('disjoint_pairs',pair_rows),('groups',group_rows),('queries',query_rows)]:
        write_csv(O/'results'/(filename+'.csv'),data)
    print(json.dumps(decision,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__': analyze()
