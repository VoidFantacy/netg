#!/usr/bin/env python3
"""Fixed P2 fit-only query profiles and frequency portals; no learned hierarchy."""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import time

os.environ['CUDA_VISIBLE_DEVICES']=''
import numpy as np

ROOT=Path('/data/netg/ACSG')
RUN=Path(__file__).resolve().parents[1]

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for x in iter(lambda:f.read(8<<20),b''):h.update(x)
    return h.hexdigest()

def norm(x):
    return x/np.maximum(np.linalg.norm(x,axis=-1,keepdims=True),1e-12)

def make_profile_and_portals(q,gt,labels,base,regions=64):
    n=len(q); d=q.shape[1]
    unitq=norm(q.astype(np.float64))
    region_gt=labels[gt[:,:10]]
    fractions=np.zeros((n,regions),dtype=np.float64)
    np.add.at(fractions,(np.repeat(np.arange(n),10),region_gt.reshape(-1)),.1)
    sums=fractions.T@unitq
    target_ids,frequency=np.unique(gt[:,:10],return_counts=True)
    target_regions=labels[target_ids]
    portals=np.empty((regions,2),dtype='<i4')
    fallback_portals=[];fallback_profiles=[]
    for r in range(regions):
        mask=target_regions==r; ids=target_ids[mask]; counts=frequency[mask]
        selected=ids[np.lexsort((ids,-counts))[:2]].tolist()
        if len(selected)<2:
            fallback_portals.append({'region':r,'fit_target_count':len(selected)})
            for node in np.flatnonzero(labels==r):
                if int(node) not in selected:selected.append(int(node))
                if len(selected)==2:break
        if len(selected)!=2:raise ValueError('Region cannot supply two distinct portals')
        portals[r]=selected
        if np.linalg.norm(sums[r])<=1e-12:
            fallback_profiles.append(r)
            sums[r]=norm(np.asarray(base[selected],dtype=np.float64)).sum(axis=0)
            if np.linalg.norm(sums[r])<=1e-12:
                sums[r]=0.0
                sums[r,0]=1.0
    profiles=norm(sums).astype('<f4')
    return profiles,portals,{'fit_queries':n,'fit_target_region_mass':fractions.sum(axis=0).tolist(),
                             'distinct_gt10_targets':len(target_ids),'portal_fallbacks':fallback_portals,
                             'profile_fallbacks':fallback_profiles,
                             'fit_mean_distinct_gt10_regions':float(np.count_nonzero(fractions,axis=1).mean()),
                             'fit_top4_oracle_target_mass':float(np.sort(fractions,axis=1)[:,-4:].sum(axis=1).mean())}

def selftest():
    # Region0 has two tied targets; region1 has only one; region2 has none.
    labels=np.repeat(np.arange(3,dtype=np.uint16),3)
    q=np.array([[1,0],[0,1]],dtype=np.float32)
    gt=np.array([[0,1,0,1,0,1,0,1,3,3],[0,1,0,1,0,1,0,1,3,3]],dtype=np.int32)
    base=np.tile(np.array([[1.,0.],[0.,1.],[1.,1.]]),(3,1))
    profiles,portals,info=make_profile_and_portals(q,gt,labels,base,3)
    assert portals.tolist()==[[0,1],[3,4],[6,7]],portals
    assert np.allclose(np.linalg.norm(profiles,axis=1),1)
    assert info['profile_fallbacks']==[2]
    assert np.allclose(profiles[0],np.array([1,1])/np.sqrt(2))
    assert np.allclose(info['fit_target_region_mass'],[1.6,.4,0])
    tiny=base.copy();tiny[6]=[1,1e-14];tiny[7]=[-1,0]
    fallback,_,_=make_profile_and_portals(q,gt,labels,tiny,3)
    assert np.array_equal(fallback[2],np.array([1.,0.],dtype=np.float32))
    print(json.dumps({'status':'PASS','test':'fit-weighted profiles, frequency tie order, missing-target portal/profile fallbacks','portals':portals.tolist()}))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dataset',choices=['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1'])
    p.add_argument('--audit',type=Path)
    p.add_argument('--labels',type=Path)
    p.add_argument('--partition-report',type=Path)
    p.add_argument('--output',type=Path)
    p.add_argument('--self-test',action='store_true')
    a=p.parse_args()
    if a.self_test:selftest();return
    initial_started=time.perf_counter()
    if not all([a.dataset,a.audit,a.labels,a.partition_report,a.output]):p.error('dataset/audit/labels/partition-report/output required')
    if time.time()>=dt.datetime(2026,9,7,22,59,tzinfo=dt.timezone.utc).timestamp():raise RuntimeError('Deadline closed')
    if json.loads((RUN/'gates/P1.json').read_text())['status']!='PASS':raise RuntimeError('P1 gate required')
    protocol=json.loads((RUN/'protocol.json').read_text())
    pr=protocol['p2_preregistered']
    if pr['region_count']!=64 or pr['portals_per_region']!=2 or pr['active_regions']!=4 or pr['geometric_softmax_temperature']!=1.0 or pr['model_seed']!=2026090711 or protocol['data_contract']['fit']['row_range']!=[10000,30000]:raise ValueError('Protocol mismatch')
    audit=json.loads(a.audit.read_text())
    if audit['status']!='PASS_INPUT_CONTRACT':raise ValueError('P0 audit required')
    ds=next(x for x in audit['datasets'] if x['dataset']==a.dataset)
    n=ds['graph']['header']['n'];d=ds['graph']['header']['d']
    if a.labels.stat().st_size!=n*2:raise ValueError('Region-map shape mismatch')
    labels=np.memmap(a.labels,mode='r',dtype='<u2',shape=(n,))
    if labels.max()>=64:raise ValueError('Invalid region label')
    sizes=np.bincount(labels,minlength=64)
    if sizes.min()<2:raise ValueError('Too-small region')
    partition=json.loads(a.partition_report.read_text())
    if partition.get('status')!='COMPLETE' or partition.get('dataset')!=a.dataset or partition.get('input_graph_sha256')!=ds['graph']['sha256']:
        raise ValueError('Partition report does not bind the current dataset and frozen graph')
    if Path(partition['labels']['path']).resolve()!=a.labels.resolve() or partition['labels']['rows']!=n or partition['labels']['bytes']!=n*2 or partition['labels']['sha256']!=sha(a.labels):
        raise ValueError('Partition label file differs from completed partition manifest')
    if not partition['partition']['all_nodes_covered'] or not partition['partition']['all_regions_nonempty'] or not partition['partition']['capacity_pass'] or partition['partition']['parts']!=64:
        raise ValueError('Partition coverage/capacity contract not accepted')
    # Partition files are separately immutable and checksum-bound here.
    a.output.mkdir(parents=True,exist_ok=False)
    started=time.perf_counter()
    builderpath=ROOT/'benches/run/build_fast_entry_variants.py'
    spec=importlib.util.spec_from_file_location('read_existing',builderpath)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    q=m.read_fvecs(Path(ds['files']['drl_train_query_path']['path']))[10000:30000]
    gt=m.read_ivecs(Path(ds['files']['drl_train_gt_path']['path']))[10000:30000]
    if q.shape!=(20000,d) or gt.shape[0]!=20000 or gt.shape[1]<10:raise ValueError('Fit query/GT shape mismatch')
    for name,array in [('query',q),('gt',gt)]:
        if hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()!=ds['fit'][name+'_values_sha256']:raise ValueError('Fit range changed')
    base_map,dim=m.fvecs_memmap(Path(ds['files']['base_path']['path']))
    if dim!=d or len(base_map)!=n:raise ValueError('Base shape mismatch')
    load_done=time.perf_counter()
    profiles,portals,details=make_profile_and_portals(q,gt,labels,base_map[:,1:])
    compute_done=time.perf_counter()
    profiles.tofile(a.output/'profiles.f32');portals.tofile(a.output/'portals.i32')
    result={'schema_version':1,'status':'COMPLETE','stage':'P2','dataset':a.dataset,'dim':d,
            'region_count':64,'active_regions':4,'portals_per_region':2,'temperature':1.0,
            'fit_range':[10000,30000],'seed':2026090711,'cpu_only':True,'heldout_accessed':False,
            'pilot_labels_used_for_fit':False,'labels_file':str(a.labels.resolve()),
            'prototypes_file':'profiles.f32','portals_file':'portals.i32',
            'labels_sha256':sha(a.labels),'profiles_sha256':sha(a.output/'profiles.f32'),
            'portals_sha256':sha(a.output/'portals.i32'),'source_script_sha256':sha(Path(__file__)),
            'protocol_sha256':sha(RUN/'protocol.json'),'input_audit_sha256':sha(a.audit),
            'partition_report':str(a.partition_report.resolve()),'partition_report_sha256':sha(a.partition_report),
            'fit_query_values_sha256':ds['fit']['query_values_sha256'],'fit_gt_values_sha256':ds['fit']['gt_values_sha256'],
            'graph_sha256':ds['graph']['sha256'],'base_sha256':ds['files']['base_path']['sha256'],
            'definition':{'region_profiles':protocol['p2_preregistered']['region_query_image_definition'],
                          'portals':protocol['p2_preregistered']['portals_definition']},
            'region_sizes':sizes.tolist(),'fit_diagnostics':details,
            'cost':{'initialization_validation_seconds':started-initial_started,'total_model_command_work_seconds':time.perf_counter()-initial_started,'load_seconds':load_done-started,'profile_and_portal_compute_seconds':compute_done-load_done,
                    'post_existing_partition_and_GT_wall_seconds':time.perf_counter()-started,
                    'exact_GT_seconds':None,'exact_GT_reason':'Audited existing GT reused; this task did not compute exact GT'},
            'created_utc':dt.datetime.now(dt.timezone.utc).isoformat()}
    (a.output/'model.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)

if __name__=='__main__':main()
