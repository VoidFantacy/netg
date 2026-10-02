from common import *
threads();resources();check(O/'reviews/prebuild_freeze.json');check(O/'reviews/models_before_queries.json')
assert read(O/'reviews/profile_verification.json')['status']=='PASS'
assert read(O/'reviews/synthetic/verification.json')['status']=='PASS'
for ds in DS:
    c=read(O/'inputs'/ds/'construction.json');aux=read(O/'inputs'/ds/'aux_source.json');h=c['hub_count'];d=c['dim']
    baseline=dict(aux['methods'][0]);baseline.update(model_name='baseline',name='baseline_L128')
    methods=[baseline]
    for model in ['duplicate3P','mode3P']:
        f=O/'models'/ds/model
        methods.append(dict(baseline,model_name=model,name=model+'_L128',W=str(f/'W.f32'),mapping=str(f/'mapping.i32'),tie_ids=str(f/'tie_ids.i32'),
            hub_count=3*h,unique_hub_count=h,slot_labels=True,multi_profile=True))
        methods[-1].pop('graph_file')
    for split,n in [('preflight',128),('fit',20000),('aux',7952)]:
        ms=[dict(m) for m in methods]
        if split!='preflight':
            for m in ms:m['graph_file']=str(O/'results'/ds/'preflight'/(m['name']+'.hnsw'))
        src=aux if split=='aux' else c
        cfg=dict(aux,split='E66_historical_'+split,num_queries=n,input_total_rows=src['num_queries'],queries_file=src['queries_file'],gt_file=src['gt_file'],row_ids=src['row_ids'],
            methods=ms,timing_repeats=0,real_call_cap=3*(2*n+16))
        dump(O/'inputs'/ds/(split+'.json'),cfg)
paths=[p for f in ['src','bin','inputs','models'] for p in (O/f).rglob('*') if p.is_file()]
paths+=[O/'protocol.md',O/'config.locked.json',O/'reviews/prebuild_freeze.json',O/'reviews/profile_verification.json',O/'reviews/synthetic/verification.json']
dump(O/'reviews/prequery_freeze.json',dict(epoch=time.time(),files=[identity(p) for p in sorted(paths)]))
dump(O/'state.json',dict(status='FROZEN_BEFORE_PREFLIGHT',new_NSG=0,day_goal_complete=False));print('JOBS_PREPARED',flush=True)
