"""Bind E24 assets and new disjoint selector partitions; never open held-out."""
import argparse
import os
import shutil
import time
from pathlib import Path
import numpy as np
from common import ROOT,RUN,E24,DATASETS,FEATURES,read,dump,sha,identity,check_lock,frozen_gate_check,update_state

def raw_rows(ds,positions,folder):
    meta=read(E24/'inputs'/ds/'prepared.json')
    source=meta['source_train'];d=meta['dim']
    qpath=source['query_train']['path'];gpath=source['gt_train']['path']
    q=np.memmap(qpath,mode='r',dtype='<f4').reshape(-1,d+1)
    g=np.memmap(gpath,mode='r',dtype='<i4').reshape(-1,101)
    assert q.shape[0]==g.shape[0]==30000
    assert np.all(q[positions,0].copy().view('<i4')==d) and np.all(g[positions,0]==100)
    queries=np.ascontiguousarray(q[positions,1:],dtype='<f4');gt=np.ascontiguousarray(g[positions,1:],dtype='<i8')
    assert np.isfinite(queries).all() and (gt>=0).all() and (gt<meta['base_rows']).all()
    assert all(len(set(row[:10]))==10 for row in gt)
    folder.mkdir(parents=True,exist_ok=False)
    queries.tofile(folder/'queries.f32');gt.tofile(folder/'gt.i64');positions.astype('<i8').tofile(folder/'row_ids.i64')
    c={'dataset':ds,'split':folder.name,'dim':d,'num_queries':len(positions),'gt_k':100,
       'index_path':meta['index_path'],'base_count':meta['base_rows'],
       'queries_file':str(folder/'queries.f32'),'gt_file':str(folder/'gt.i64'),'row_ids':str(folder/'row_ids.i64')}
    dump(folder/'config.json',c)
    dump(folder/'provenance.json',{'source_query':source['query_train'],'source_gt':source['gt_train'],
         'row_ids':identity(folder/'row_ids.i64'),'outputs':[identity(folder/x) for x in ['queries.f32','gt.i64']],
         'source_header_and_rows_verified':True,'historical_development_pool':True})
    return c

def initialize():
    started=time.monotonic()
    assert not any((RUN/'inputs'/ds).exists() for ds in DATASETS), 'input preparation already started'
    assert 15 in os.sched_getaffinity(0)
    expected=3200+131200+32896+32896+840960+48000
    lock={'experiment':'E25_selective_profile_gate_v1','protocol_sha256':sha(RUN/'protocol.md'),
          'seed':20260910,'fit_n':8192,'cal_n':2048,'audit_n':2048,'validation_n':2000,
          'label_L':[64,128],'L':[64,128,256,400,800],'timing_repeats':3,'feature_names':FEATURES,
          'lambda':[.01,.1,1.],'fit_logit_quantiles':[.10,.25,.50,.75],
          'gain_retention_target':.75,'harm_reduction_target':.25,
          'query_cpu':15,'normal_real_call_cap':expected,'repair_real_call_cap':16384,
          'total_real_call_cap':expected+16384,'synthetic_call_cap':10000,
          'rss_limit_bytes':40<<30,'output_limit_bytes':1610612736,'min_free_bytes':10<<30,
          'job_timeout_seconds':1800,'total_search_seconds':7200,'heldout_allowed':False}
    assert shutil.disk_usage(ROOT).free>=lock['min_free_bytes']
    if (RUN/'config.locked.json').exists():assert check_lock()==lock
    else:
        dump(RUN/'config.locked.json',lock)
        dump(RUN/'reviews/protocol_lock.json',{'locked_unix':time.time(),'config_sha256':sha(RUN/'config.locked.json'),
             'protocol_sha256':lock['protocol_sha256'],'before_new_pair_labels_and_cal_audit':True})
    protected={};checks=[]
    def protect(path,expected_sha=None):
        path=str(Path(path).resolve())
        if path not in protected:protected[path]=identity(path)
        if expected_sha:assert protected[path]['sha256']==expected_sha,path
        return protected[path]
    # Current source, binary dependencies and original E24 evaluation artifacts stay immutable.
    for rel in ['ACSG/ACSG.cpp','ACSG/ACSG.h','ACSG/IndexACSG.cpp','ACSG/IndexACSG.h',
                'build/faiss/faiss/libfaiss.a','build/ACSG/libACSG.a','build/MRNN_Descent/libmrnndescent.a',
                'benches/hnswlib/hnswalg.h','benches/hnswlib/space_ip.h']:
        protect(ROOT/rel)
    for rel in ['protocol.md','config.locked.json','state.json','models/frozen_before_validation.json',
                'reviews/final_audit.json','report.md','results/summary.json','bin/evaluate',
                'src/benchmark_with_nsg.cpp','src/legacy_reference.cpp']:
        protect(E24/rel)
    for f in read(E24/'models/frozen_before_validation.json')['files']:protect(f['path'],f['sha256'])
    for ds in DATASETS:
        old=read(E24/'inputs'/ds/'prepared.json')
        for rec in old['source_train'].values():protect(rec['path'],rec['sha256'])
        oldhub=E24/'inputs'/ds/'hub_ids.i32';protect(oldhub)
        ids=np.fromfile(oldhub,dtype='<i4');assert len(ids)==old['H'] and np.all(np.diff(ids)>0)
        selection=read(E24/'models'/ds/'selection.json');primary=selection['primary']
        expected_name='gt10_soft_t1' if ds.startswith('webvid') else 'gt10_hard'
        assert primary['name']==expected_name
        profiles={}
        for name in ['gt1_hard',expected_name]:
            folder=E24/'models'/ds/name
            manifest=read(folder/'manifest.json');protect(folder/'manifest.json');protect(folder/'W.f32',manifest['W_identity']['sha256']);protect(folder/'support.npz')
            w=np.fromfile(folder/'W.f32',dtype='<f4').reshape(old['H'],old['dim'])
            support=np.load(folder/'support.npz');ess=np.asarray(support['ess'],dtype=np.float64)
            assert ess.shape==(old['H'],) and np.isfinite(ess).all() and (ess>=0).all()
            assert np.isfinite(w).all() and np.max(np.abs(np.linalg.norm(w,axis=1)-1))<2e-6
            profiles[name]=(w,ess)
        inp=RUN/'inputs'/ds;inp.mkdir()
        shutil.copy2(oldhub,inp/'hub_ids.i32')
        p0,ess0=profiles['gt1_hard'];p1,ess1=profiles[expected_name]
        cosine=np.sum(p0.astype('float64')*p1,axis=1)/(np.linalg.norm(p0.astype('float64'),axis=1)*np.linalg.norm(p1.astype('float64'),axis=1))
        features=np.column_stack([np.log1p(ess0),np.log1p(ess1),1-np.clip(cosine,-1,1)]).astype('<f8')
        features.tofile(inp/'hub_features.f64')
        model={'dataset':ds,'dim':old['dim'],'hub_count':old['H'],'k':3,'seed':20260828,'hnsw_seed':20260828,
          'mapping':str(inp/'hub_ids.i32'),'tie_ids':str(inp/'hub_ids.i32'),
          'slot_labels':False,'exact':False,'legacy_heap_order':False,'canonical_entry_order':True}
        models={'A0':{**model,'W':str(E24/'models'/ds/'gt1_hard/W.f32'),'family':'fast20k','name':'fast20k'},
                'A1':{**model,'W':str(E24/'models'/ds/expected_name/'W.f32'),'family':'e24','name':'e24'},
                'hub_features':str(inp/'hub_features.f64'),'primary_E24':expected_name}
        dump(inp/'policies.json',models)
        positions=np.sort(np.random.Generator(np.random.PCG64(20260910)).choice(20000,8192,replace=False))+10000
        fit=raw_rows(ds,positions,inp/'fit');cal=raw_rows(ds,np.arange(2048,4096),inp/'cal')
        recovery=raw_rows(ds,np.arange(32),inp/'recovery')
        assert not np.intersect1d(positions,np.arange(2048,6144)).size
        eq=np.fromfile(E24/'inputs'/ds/'fit/queries.f32',dtype='<f4').reshape(20000,old['dim'])
        eg=np.fromfile(E24/'inputs'/ds/'fit/gt.i64',dtype='<i8').reshape(20000,100)
        assert np.array_equal(np.fromfile(fit['queries_file'],dtype='<f4').reshape(8192,old['dim']),eq[positions-10000])
        assert np.array_equal(np.fromfile(fit['gt_file'],dtype='<i8').reshape(8192,100),eg[positions-10000])
        checks.append({'dataset':ds,'H':old['H'],'primary':expected_name,'fit_n':8192,'cal_rows':[2048,4096],
             'audit_rows_deferred':[4096,6144],'fit_rows_disjoint_from_cal_audit':True,'fit_bit_equal_E24':True,
             'hub_features':identity(inp/'hub_features.f64'),'source_hashes_verified':True})
    for p in (RUN/'source_before').iterdir():protect(p)
    dump(RUN/'reviews/protected_before.json',list(protected.values()))
    dump(RUN/'inputs/preflight.json',{'status':'PASS','datasets':checks,'seconds':time.monotonic()-started,
         'protected_files':len(protected),'large_base_graph_train_hashes_verified':True,'validation_opened':False,'heldout_opened':False,
         'whole_train_hash_includes_audit_bytes_for_identity_only':True})
    update_state(status='PROTOCOL_LOCKED_INPUTS_READY',validation_opened=False,heldout_opened=False)
    print('PROTOCOL_AND_INPUTS_READY',round(time.monotonic()-started,2),len(protected),flush=True)

def later(stage):
    check_lock();frozen_gate_check()
    if stage=='audit':
        for ds in DATASETS:raw_rows(ds,np.arange(4096,6144),RUN/'inputs'/ds/'audit')
    else:
        assert read(RUN/'reviews/audit_report.json')['status']=='REPORT_ONLY_COMPLETE'
        for ds in DATASETS:
            src=E24/'inputs'/ds/'validation';c=read(src/'config.json');out=RUN/'inputs'/ds/'validation'
            out.mkdir(exist_ok=False)
            records=[]
            for key,filename in [('queries_file','queries.f32'),('gt_file','gt.i64'),('row_ids','row_ids.i64')]:
                original=Path(c[key]);records.append(identity(original));shutil.copy2(original,out/filename)
                assert sha(out/filename)==records[-1]['sha256'];c[key]=str(out/filename)
            assert c['num_queries']==2000
            dump(out/'config.json',{k:c[k] for k in ['dataset','split','dim','num_queries','gt_k','index_path','queries_file','gt_file','row_ids']})
            dump(out/'provenance.json',{'E24_input_config':identity(src/'config.json'),'sources':records,
                 'historical_validation':True,'copied_only_after_gate_freeze_and_audit':True})
        update_state(validation_opened=True)
    print(stage.upper()+'_INPUTS_READY',flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('stage',choices=['initialize','audit','validation']);a=ap.parse_args()
    initialize() if a.stage=='initialize' else later(a.stage)
