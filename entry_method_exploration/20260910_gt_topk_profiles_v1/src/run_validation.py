import copy
import time
from pathlib import Path
import numpy as np
from common import DATASETS, E23, ROOT, RUN, check_lock, dump, identity, read, sha
from jobs import model_method, run_job
from run_development import assert_frozen

lock=check_lock()
assert read(RUN/'reviews/cal_gate.json')['validation_allowed'],'cal stop forbids validation access'
assert read(RUN/'state.json')['status']=='AUDIT_COMPLETE_P3_PENDING'
assert_frozen(RUN/'models/frozen_before_cal.json');assert_frozen(RUN/'models/frozen_before_audit.json')
files=read(RUN/'models/frozen_before_audit.json')['files']
files += [identity(RUN/'bin/evaluate'),identity(RUN/'reviews/cal_gate.json'),identity(RUN/'config.locked.json')]
freeze=RUN/'models/frozen_before_validation.json';assert not freeze.exists()
dump(freeze,{'status':'FROZEN_BEFORE_VALIDATION_RAW_ACCESS','unix':time.time(),'files':files,
             'historical_validation_use':'E22/E23 and earlier development, not fresh blind data','heldout_allowed':False})
for di,ds in enumerate(DATASETS):
    assert_frozen(freeze)
    old=read(E23/'inputs'/ds/'validation/config.json')
    inp=RUN/'inputs'/ds;dest=inp/'validation';assert not dest.exists();dest.mkdir()
    n,d=2000,old['dim'];assert old['num_queries']==n and old['gt_k']==100
    for name,key,dtype,width in [('queries.f32','queries_file','<f4',d),('gt.i64','gt_file','<i8',100),('row_ids.i64','row_ids','<i8',1)]:
        a=np.fromfile(old[key],dtype=dtype);assert a.size==n*width
        if key=='row_ids':assert np.array_equal(a,np.arange(n))
        a.tofile(dest/name)
    # Verify the 2K slice against original validation records without reading held-out.
    meta=read(inp/'prepared.json');dataset_dir=Path(meta['base_file']).parent
    qname='query.validation.seed20260826.fvecs' if di==0 else 'query.validation.fvecs'
    gtname='gt.validation.seed20260826.ip.ivecs' if di==0 else 'gt.validation.ip.ivecs'
    source_q=np.memmap(dataset_dir/qname,dtype='<f4',mode='r',shape=(10000,d+1))
    source_gt=np.memmap(dataset_dir/gtname,dtype='<i4',mode='r',shape=(10000,101))
    assert np.all(source_q[:n,0].view('<i4')==d) and np.all(source_gt[:n,0]==100)
    assert np.array_equal(source_q[:n,1:],np.fromfile(dest/'queries.f32',dtype='<f4').reshape(n,d))
    assert np.array_equal(source_gt[:n,1:],np.fromfile(dest/'gt.i64',dtype='<i8').reshape(n,100))
    selected=read(RUN/'models'/ds/'selection.json')['selected_families']
    fast30=copy.deepcopy(next(m for m in old['methods'] if m['family']=='fast30k_3'))
    assert fast30['k']==3 and fast30['hnsw_seed']==100 and fast30['legacy_heap_order']
    assert fast30['canonical_entry_order']==False
    fast30.update({'model_name':'fast30k_3','exact':False,'component_wall':False})
    models=[{'family':'nsg_medoid','model_name':'nsg_medoid','seed':20260828,'k':1},fast30,
            model_method(ds,read(RUN/'models'/ds/'gt1_hard/manifest.json'))]
    models.extend(model_method(ds,selected[key]) for key in ['gt10_hard','gt1_soft','gt10_soft'])
    methods=[]
    for li,L in enumerate(lock['L']):
        offset=(di+li)%len(models)
        for pos in range(len(models)):
            mc=copy.deepcopy(models[(offset+pos)%len(models)])
            mc.update({'L':L,'name':mc['family']+f'_L{L}','component_wall':L==128})
            methods.append(mc)
    config={'dataset':ds,'split':'validation2000_gt_profiles','dim':d,'num_queries':n,'gt_k':100,
            'queries_file':str(dest/'queries.f32'),'gt_file':str(dest/'gt.i64'),'row_ids':str(dest/'row_ids.i64'),
            'index_path':meta['index_path'],'base_count':meta['base_rows'],'threads':1,'measure_wall':True,
            'methods':methods,'timing_repeats':1}
    dump(dest/'config.json',config)
    dump(dest/'provenance.json',{'source_config':identity(E23/'inputs'/ds/'validation/config.json'),
         'old_prepared_files':[identity(old[k]) for k in ['queries_file','gt_file','row_ids']],
         'source_original_files':[str(dataset_dir/qname),str(dataset_dir/gtname)],
         'slice_checked':[0,2000],'source_full_validation_hashed':False,'heldout_opened':False,
         'freeze':identity(freeze)})
    run_job('validation_'+ds,config,RUN/'results'/ds)
dump(RUN/'state.json',{'status':'VALIDATION_COMPLETE_ANALYSIS_PENDING','validation_opened':True,'heldout_opened':False,
                      'tuning_complete':True,'all_60_points_complete':True})
print('ALL_60_VALIDATION_POINTS_COMPLETE',flush=True)
