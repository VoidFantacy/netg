"""Independent post-search score/identity checks and bounded causal comparisons."""
from common import *
from prepare_supplement import SUP

def load_old(ds,stage,family,exact,L):
    folder=VERSIONS[24]/('results' if stage=='validation' else 'diagnostics')/ds
    if stage!='validation':folder/=stage
    r=read(folder/'results.json')
    m=next(x for x in r['methods'] if x['family']==family and x['L']==L and x['configuration']['exact']==exact)
    return m,load_point(folder,m,r['queries'])

def check_same(z0,z1):
    same=np.all(z0['entries']==z1['entries'],axis=1)
    for key in ['ids','bits','hits','masks','g']:assert np.array_equal(z0[key][same],z1[key][same])
    return int(same.sum())

def compare_row(ds,stage,backend,model,base,z0,z1,L):
    lo,hi=bootstrap(z1['hits'].astype('int16')-z0['hits'].astype('int16'))
    return {'dataset':ds,'stage':stage,'backend':backend,'model':model,'baseline':base,'L':L,
            **effect(z0['hits'],z1['hits']),'CI95_low':lo,'CI95_high':hi,'same_entry_queries':check_same(z0,z1),
            'delta_route_ndc':float(z1['r'].astype('int64').mean()-z0['r'].mean()),
            'delta_graph_ndc_percent':float(100*(z1['g'].mean()/z0['g'].mean()-1))}

def main():
    complete=read(SUP/'reviews/execution_complete.json');assert complete['status']=='COMPLETE'
    lock=read(SUP/'config.locked.json');assert complete['real_calls']==lock['normal_real_call_cap']
    shuffle=[];exact=[];wall=[];components=[];local={}
    for ds in DATASETS:
        for stage in ['cal','audit']:
            folder=SUP/'results'/f'shuffle_{stage}_{ds}';r=read(folder/'results.json')
            for m in r['methods']:
                ex=m['configuration']['exact'];name='exact' if ex else 'HNSW';zs=load_point(folder,m,r['queries'])
                for family in ['gt1_hard','gt10_hard']:
                    _,z=load_old(ds,stage,family,ex,128)
                    shuffle.append(compare_row(ds,stage,name,'tail_shuffle',family,z,zs,128))
                    np.savez_compressed(SUP/'results'/f'{ds}_{stage}_{name}_shuffle_vs_{family}.npz',
                        original_row_ids=arr(folder/'row_ids.i64','<i8'),baseline_hits=z['hits'],shuffle_hits=zs['hits'],
                        baseline_entries=z['entries'],shuffle_entries=zs['entries'])
        folder=SUP/'results'/f'exact_{ds}';r=read(folder/'results.json');L=lock['positive_point_L'][ds]
        pp={m['family']:(m,load_point(folder,m,r['queries'])) for m in r['methods']}
        z0,z1=pp['gt1_hard'][1],pp['gt10_hard'][1]
        row=compare_row(ds,'historical_validation','exact','gt10_hard','gt1_hard',z0,z1,L);exact.append(row)
        _,h0=load_old(ds,'validation','gt1_hard',False,L);_,h1=load_old(ds,'validation','gt10_hard',False,L)
        d_exact=z1['hits'].astype('int16')-z0['hits'].astype('int16')
        d_hnsw=h1['hits'].astype('int16')-h0['hits'].astype('int16')
        for family,hz,ez in [('gt1_hard',h0,z0),('gt10_hard',h1,z1)]:
            exact.append(compare_row(ds,'historical_validation','backend_difference',family+'_exact',family+'_HNSW',hz,ez,L))
        local[ds]={'L':L,'HNSW_effect':effect(h0['hits'],h1['hits']),'exact_effect':effect(z0['hits'],z1['hits']),
            'backend_interaction_net_hits':int((d_hnsw-d_exact).sum()),'backend_interaction_pp':float(10*(d_hnsw-d_exact).mean()),
            'same_effect_sign_query':int((np.sign(d_hnsw)==np.sign(d_exact)).sum()),
            'only_HNSW_positive_query':int(((d_hnsw>0)&(d_exact<=0)).sum()),
            'only_exact_positive_query':int(((d_exact>0)&(d_hnsw<=0)).sum())}
        np.savez_compressed(SUP/'results'/f'{ds}_local_exact_HNSW.npz',row_ids=arr(folder/'row_ids.i64','<i8'),
            gt1_HNSW_hits=h0['hits'],gt10_HNSW_hits=h1['hits'],gt1_exact_hits=z0['hits'],gt10_exact_hits=z1['hits'],
            gt1_HNSW_entries=h0['entries'],gt10_HNSW_entries=h1['entries'],gt1_exact_entries=z0['entries'],gt10_exact_entries=z1['entries'])
    ds=DATASETS[0];folder=SUP/'results'/f'repeat_{ds}';r=read(folder/'results.json');frontier=[]
    for L in LS:
        mm={m['family']:m for m in r['methods'] if m['L']==L};a,b=mm['gt1_hard'],mm['gt10_hard']
        for j in range(3):
            wall.append({'dataset':ds,'L':L,'repeat':j,'GT1_recall_percent':100*a['recall_at_10'],'GT10_recall_percent':100*b['recall_at_10'],
                'GT1_qps':a['qps_runs'][j],'GT10_qps':b['qps_runs'][j],'delta_qps_percent':100*(b['qps_runs'][j]/a['qps_runs'][j]-1),
                'GT1_median_qps':a['qps'],'GT10_median_qps':b['qps'],'median_delta_qps_percent':100*(b['qps']/a['qps']-1),
                'GT1_wall_seconds':a['end_to_end_seconds'][j],'GT10_wall_seconds':b['end_to_end_seconds'][j]})
        for m in [a,b]:
            z=load_point(folder,m,2000);assert np.isin(z['entries'],arr(m['configuration']['mapping'],'<i4')).all()
            components.append({'dataset':ds,'L':L,'model':m['family'],'route_ndc':m['mean_route_ndc'],'graph_ndc':m['mean_graph_ndc'],
               'total_ndc':m['mean_total_ndc'],'median_end_to_end_us':1e6/ m['qps'],
               'route_only_us':m['route_only_seconds']*1e6/2000 if m['route_only_seconds'] is not None else None,
               'graph_only_us':m['graph_only_seconds']*1e6/2000 if m['graph_only_seconds'] is not None else None})
            for j in range(3):frontier.append({'dataset':ds,'L':L,'model':m['family'],'repeat':j,'recall_percent':100*m['recall_at_10'],'qps':m['qps_runs'][j]})
    for x in frontier:
        others=[y for y in frontier if y['repeat']==x['repeat']]
        x['nondominated']=not any(y['recall_percent']>=x['recall_percent'] and y['qps']>=x['qps'] and
             (y['recall_percent']>x['recall_percent'] or y['qps']>x['qps']) for y in others)
    for name,data in [('shuffle_comparisons',shuffle),('local_exact_comparisons',exact),('repeat_wall',wall),
                       ('repeat_components',components),('repeat_frontier',frontier)]:csv_write(SUP/'results'/f'{name}.csv',data)
    dump(SUP/'results/analysis.json',{'status':'COMPLETE','local_exact':local,'shuffle_comparisons':shuffle,
         'wall_repeat':wall,'costs':complete,'shuffle_models':read(SUP/'models/construction.json')})
    dump(SUP/'reviews/analysis_sources.json',{'files':list(SOURCES.values())})
    print('SUPPLEMENT_ANALYSIS_COMPLETE',local,flush=True)
    for x in wall:
        if x['repeat']==0:print('WEBVID_REPEAT',x['L'],x['median_delta_qps_percent'],flush=True)
    for x in shuffle:print('SHUFFLE',x['dataset'],x['stage'],x['backend'],x['baseline'],x['delta_recall_pp'],flush=True)

if __name__=='__main__':main()
