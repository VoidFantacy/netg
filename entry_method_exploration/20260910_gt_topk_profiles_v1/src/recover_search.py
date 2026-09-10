import numpy as np
from common import DATASETS, E23, RUN, check_lock, dump, identity, read
from jobs import model_method, run_job

lock=check_lock();assert read(RUN/'reviews/synthetic_gate.json')['status']=='PASS'
checks=[]
for dataset in DATASETS:
    inp=RUN/'inputs'/dataset;meta=read(inp/'prepared.json');part=inp/'recovery';assert not part.exists();part.mkdir()
    c=read(inp/'fit/config.json');d=c['dim'];n=lock['recovery_queries']
    for name,dtype,width in [('queries.f32','<f4',d),('gt.i64','<i8',100),('row_ids.i64','<i8',1)]:
        np.fromfile(inp/'fit'/name,dtype=dtype,count=n*width).tofile(part/name)
    c.update({'split':'fit_recovery32','num_queries':n,'base_count':meta['base_rows'],
              'queries_file':str(part/'queries.f32'),'gt_file':str(part/'gt.i64'),'row_ids':str(part/'row_ids.i64'),
              'measure_wall':False})
    model=read(RUN/'models'/dataset/'gt1_hard/manifest.json')
    old={'name':'old_P0','family':'old_P0','W':str(inp/'P0_reference.f32')}
    c['methods']=[model_method(dataset,m,exact=exact) for m in [old,model] for exact in [False,True]]
    result=run_job('recovery_'+dataset,c,RUN/'diagnostics'/dataset/'recovery')
    oldresult=read(E23/'diagnostics'/dataset/'fit_probe/results.json')
    for exact in [False,True]:
        names=[model_method(dataset,m,exact=exact)['name'] for m in [old,model]]
        first,second=[RUN/'diagnostics'/dataset/'recovery'/name for name in names]
        fields=['ids.i32','distances.f32','entry_ids.i32','router_labels.i32','hits.u8','hitmask.u16','route_ndc.u32','graph_ndc.u32']
        for field in fields:
            assert (first/field).read_bytes()==(second/field).read_bytes(),(dataset,exact,field)
        historical=next(x for x in oldresult['methods'] if x['configuration']['model_name']=='fast20k_3' and x['configuration']['exact']==exact)
        olddir=E23/'diagnostics'/dataset/'fit_probe'/historical['name']
        for field in fields:
            current=(second/field).read_bytes()
            with (olddir/field).open('rb') as stream:expected=stream.read(len(current))
            assert current==expected,(dataset,exact,field,'E23 regression')
        checks.append({'dataset':dataset,'exact':exact,'queries':n,'new_old_P0_bits':True,'E23_output_bits':True,'fields':fields})
dump(RUN/'reviews/recovery_gate.json',{'status':'PASS','checks':checks,
     'numeric_checks':[read(RUN/'reviews'/f'{ds}_P0_numeric.json') for ds in DATASETS],
     'real_search_calls':768,'raw_validation_opened':False,'heldout_opened':False})
dump(RUN/'state.json',{'status':'P1_RECOVERY_PASS_BUILD_CANDIDATES_PENDING','validation_opened':False,'heldout_opened':False})
print('P1_RECOVERY_GATE_PASS',flush=True)
