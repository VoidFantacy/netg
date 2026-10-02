from common import *
import shutil
E24=ROOT/'entry_method_exploration/20260910_gt_topk_profiles_v1'
E103=ROOT/'entry_method_exploration/20260916_optimized_five_dataset_r1_r100_v1'

def prepare(split):
    assert split in ('fit','cal')
    if split=='cal':
        freeze=read(RUN/'reviews/models_frozen.json')
        assert freeze['status']=='FROZEN' and len(freeze['models'])==6
        for x in freeze['models']:
            assert sha(x['path'])==x['sha256']
    finite_deadline()
    records=[]
    for ds in DS:
        out=RUN/'inputs'/ds/split;assert not out.exists();out.mkdir(parents=True)
        old=read(E24/'inputs'/ds/split/'config.json')
        current=read(E103/'configs'/f'{ds}.json')
        n=LOCK[split+'_n'];d=old['dim'];h=old['hub_count']
        assert old['split']==split and old['num_queries']>=n and old['gt_k']==100
        assert old['index_path']==current['index'] and d==current['dimension'] and current['metric_id']==0
        rows={}
        for role,num in [('fit',LOCK['fit_n']),('cal',LOCK['cal_n'])]:
            c=read(E24/'inputs'/ds/role/'config.json')
            rows[role]=np.fromfile(c['row_ids'],'int64')[:num]
            assert len(rows[role])==num and len(np.unique(rows[role]))==num
        assert not set(rows['fit']).intersection(rows['cal'])
        # Original E24 namespaces: both are router_train source rows.
        assert np.array_equal(rows['fit'],np.arange(10000,10000+LOCK['fit_n']))
        assert np.array_equal(rows['cal'],np.arange(LOCK['cal_n']))
        input_before=[]
        for name,key,dtype,width in [('queries.f32','queries_file','float32',d),('gt.i64','gt_file','int64',100)]:
            path=Path(old[key]);input_before.append(identity(path))
            a=np.memmap(path,mode='r',dtype=dtype,shape=(old['num_queries'],width))[:n].copy()
            if key=='queries_file':assert np.isfinite(a).all() and np.all(np.linalg.norm(a,axis=1)>0)
            else:
                assert a.min()>=0 and a.max()<current['base_n']
                assert all(len(np.unique(x))==100 for x in a)
            a.tofile(out/name)
        rows[split].tofile(out/'row_ids.i64')
        hubs=np.fromfile(old['hub_ids'],'int32');assert len(hubs)==h and np.all(np.diff(hubs)>0)
        hubs.tofile(out/'hub_ids.i32')
        anchor='GT10-soft-t1' if ds.startswith('webvid') else 'GT10-hard'
        names=[anchor,'GT10-hard' if anchor.endswith('soft-t1') else 'GT10-soft-t1']
        routers=[];assets=[]
        for name in names:
            m=next(x for x in current['methods'] if x['name']==name)
            assert np.array_equal(np.fromfile(m['ids'],'int32'),hubs)
            graph=Path(current['reference_results'])/'k100'/(name+'.hnsw')
            assets.extend(identity(Path(m[k])) for k in ['ids','W']);assets.append(identity(graph))
            routers.append(dict(**m,graph=str(graph)))
        cfg=dict(dataset=ds,split=split,n=n,dimension=d,hub_count=h,base_n=current['base_n'],metric_id=0,
                 index=current['index'],queries=str(out/'queries.f32'),gt=str(out/'gt.i64'),hub_ids=str(out/'hub_ids.i32'),
                 routers=routers,threads=1,L=128,K=[1,100],parity_rows=LOCK['fit_parity_positions'] if split=='fit' else [],
                 max_main_search_calls=1100000,root=str(RUN),deadline_unix=LOCK['created_unix']+7200)
        dump(out/'config.json',cfg)
        after=[identity(Path(x['path'])) for x in input_before];assert after==input_before
        rec=dict(dataset=ds,split=split,n=n,role='historically exposed development data',
                 source_inputs=input_before,router_assets=assets,index_stat=stat_identity(current['index']),
                 inherited_data_identity=str(E103/'inputs'/ds/'manifest.json'),
                 source_role_protocol=identity(E24/'protocol.md'),new_inputs=[identity(out/x) for x in ['queries.f32','gt.i64','row_ids.i64','hub_ids.i32','config.json']])
        dump(out/'manifest.json',rec);records.append(rec)
    dump(RUN/'reviews'/f'{split}_prepared.json',dict(status='PASS',datasets=records,eval_test_payload_access=False))
    print(json.dumps(dict(status='PREPARED',split=split,datasets=len(records))))

if __name__=='__main__':
    import sys
    prepare(sys.argv[1])
