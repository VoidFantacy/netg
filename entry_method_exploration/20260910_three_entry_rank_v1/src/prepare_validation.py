#!/usr/bin/env python3
import copy
import time
from pathlib import Path
import numpy as np
from common import DATASETS, LS, OLD, RUN, dump, identity, read, sha
from model_config import baseline, method

assert read(RUN/'state.json')['status']=='AUDIT_COMPLETE'
frozen=[]
for dataset in DATASETS:
    complete=read(RUN/'models'/dataset/'complete.json')
    selection=read(RUN/'models'/dataset/'selection.json')
    assert selection['status']=='SELECTED_BEFORE_AUDIT_AND_VALIDATION'
    for model in complete['models']:
        assert sha(model['W'])==model['W_sha256']
        frozen.append(identity(model['W']))
    frozen.extend(identity(RUN/'models'/dataset/x) for x in ['complete.json','selection.json'])
    frozen.extend(identity(RUN/'inputs'/dataset/x) for x in ['P0.f32','hub_ids.i32'])
frozen.extend(identity(RUN/'bin'/x) for x in ['evaluate_v2','evaluate_v2.build.json'])
freeze_file=RUN/'models/frozen_before_validation.json';assert not freeze_file.exists()
dump(freeze_file,{'status':'FROZEN_BEFORE_VALIDATION_RAW_DATA_ACCESS','created_unix':time.time(),
                 'files':frozen,'protocol_sha256':sha(RUN/'protocol.md')})

configs=[];manifest={'status':'PREPARED','freeze_manifest':identity(freeze_file),'datasets':{}}
for di,dataset in enumerate(DATASETS):
    old_dir=OLD/'exploration_5point_v1/inputs'/dataset
    source=read(old_dir/'config.json')
    n,d=2000,source['dim'];assert source['num_queries']==n
    dest=RUN/'inputs'/dataset/'validation';assert not dest.exists();dest.mkdir()
    for name,key,dtype,width in [('queries.f32','queries_file','<f4',d),('gt.i64','gt_file','<i8',100),('row_ids.i64','row_ids','<i8',1)]:
        a=np.fromfile(source[key],dtype=dtype);assert a.size==n*width
        a.tofile(dest/name)
    selected=read(RUN/'models'/dataset/'selection.json')['selected_new_candidates']
    fast30=copy.deepcopy(next(x for x in source['methods'] if x['family']=='fast30k_3'))
    assert fast30['k']==3 and fast30['hnsw_seed']==100 and fast30['legacy_heap_order']
    fast30['canonical_entry_order']=False;fast30['exact']=False
    models=[{'family':'nsg_medoid','seed':20260828,'k':1},fast30,
            method(dataset,baseline(dataset)),method(dataset,selected['full']),method(dataset,selected['rank8'])]
    methods=[]
    for li,L in enumerate(LS):
        offset=(di+li)%len(models)
        for pos in range(len(models)):
            mc=copy.deepcopy(models[(offset+pos)%len(models)])
            mc['L']=L;mc['name']=mc['family']+f'_L{L}';methods.append(mc)
    config={'dataset':dataset,'split':'validation2000_three_entry_exploration','dim':d,'num_queries':n,'gt_k':100,
        'queries_file':str(dest/'queries.f32'),'gt_file':str(dest/'gt.i64'),'row_ids':str(dest/'row_ids.i64'),
        'index_path':source['index_path'],'threads':1,'measure_wall':True,'methods':methods,'L':LS,
        'timing_repeats':1,'protocol_sha256':sha(RUN/'protocol.md')}
    dump(dest/'config.json',config);configs.append(str(dest/'config.json'))
    files=[identity(dest/name) for name in ['queries.f32','gt.i64','row_ids.i64','config.json']]
    files.append(identity(fast30['W']))
    manifest['datasets'][dataset]={'files':files,'source_validation_config':identity(old_dir/'config.json'),
        'selected_models':selected,'heldout_opened':False}
manifest['configs']=configs;dump(RUN/'inputs/validation_manifest.json',manifest)
dump(RUN/'state.json',{'status':'VALIDATION_PREPARED_MODELS_FROZEN','configs':configs})
print('VALIDATION_PREPARED_AFTER_FREEZE',flush=True)
