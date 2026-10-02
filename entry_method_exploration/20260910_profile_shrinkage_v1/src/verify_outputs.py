"""Independent GT scoring of actual single-route outputs."""
from pathlib import Path
import numpy as np
from common import read,dump


def load_arrays(folder,name,n):
    p=Path(folder)/name
    return {'ids':np.fromfile(p/'ids.i32',dtype='<i4').reshape(n,10),
            'distances':np.fromfile(p/'distances.f32',dtype='<f4').reshape(n,10),
            'entries':np.fromfile(p/'entry_ids.i32',dtype='<i4').reshape(n,3),
            'hits':np.fromfile(p/'hits.u8',dtype='u1').astype('int16'),
            'mask':np.fromfile(p/'hitmask.u16',dtype='<u2'),
            'route_ndc':np.fromfile(p/'route_ndc.u32',dtype='<u4'),
            'graph_ndc':np.fromfile(p/'graph_ndc.u32',dtype='<u4')}


def verify_folder(folder):
    folder=Path(folder);c=read(folder/'config.json');r=read(folder/'results.json');n=c['num_queries']
    assert r['status']=='COMPLETE' and r['threads']==1 and r['GT_opened_after_all_raw_search']
    assert np.array_equal(np.fromfile(c['row_ids'],dtype='<i8'),np.fromfile(folder/'row_ids.i64',dtype='<i8'))
    gt=np.fromfile(c['gt_file'],dtype='<i8').reshape(n,100)[:,:10]
    for m in r['methods']:
        a=load_arrays(folder,m['name'],n)
        assert a['ids'].shape==(n,10) and (a['ids']>=0).all() and np.isfinite(a['distances']).all()
        assert (np.diff(np.sort(a['ids'],axis=1),axis=1)>0).all()
        mask=np.zeros(n,'<u2')
        for k in range(10):mask|=(a['ids']==gt[:,k,None]).any(axis=1).astype('<u2')<<k
        assert np.array_equal(mask,a['mask'])
        assert np.array_equal([int(v).bit_count() for v in mask],a['hits'])
        assert int(a['hits'].sum())==m['total_hits'] and int((a['hits']==0).sum())==m['failed_queries']
        assert abs(a['route_ndc'].mean()-m['mean_route_ndc'])<1e-9 and abs(a['graph_ndc'].mean()-m['mean_graph_ndc'])<1e-9
        if m['family']!='nsg':
            assert (a['entries']>=0).all() and (np.diff(np.sort(a['entries'],axis=1),axis=1)>0).all()
            if m['configuration'].get('canonical_entry_order'):assert (np.diff(a['entries'],axis=1)>0).all()
        else:assert np.all(a['route_ndc']==0)
        if r['timing_repeats']:
            assert len(m['qps_runs'])==3 and np.allclose(m['qps_runs'],n/np.asarray(m['end_to_end_seconds']),rtol=1e-12)
            assert m['qps']==float(np.median(m['qps_runs'])) and m['qps_min']==min(m['qps_runs']) and m['qps_max']==max(m['qps_runs'])
    check={'status':'PASS','points':len(r['methods']),'independently_scored_outputs':n*len(r['methods']),
           'raw_ID_distance_entry_scoring_and_costs':True,'three_walls_checked':r['timing_repeats']==3}
    dump(folder/'independent_verification.json',check)
    return check
