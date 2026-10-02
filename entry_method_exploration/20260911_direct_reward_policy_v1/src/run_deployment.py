from deployment_common import *
import argparse

def route_parity():
    assert read(O/'reviews/deployment_build.json')['status']=='PASS'
    build=read(O/'bin/evaluate.build.json');argv=[x.replace(str(O/'src/evaluate.cpp'),str(O/'src/route_parity.cpp')).replace(str(O/'bin/evaluate'),str(O/'bin/route_parity')) for x in build['argv']]
    assert not (O/'bin/route_parity').exists()
    with (O/'logs/route_parity.build.log').open('x') as log:r=subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT)
    assert r.returncode==0
    dump(O/'bin/route_parity.build.json',dict(argv=argv,exit_code=r.returncode,binary=identity(O/'bin/route_parity')))
    files=[O/'protocol.md',O/'deployment_plan.md',O/'results/cache_gate.json']+[p for p in (O/'src').glob('*') if p.is_file()]+[p for p in (O/'bin').glob('*') if p.is_file()]
    configs=[]
    for ds in DS:
        c=read(O/'inputs'/ds/'fit/config.json')
        c={k:c[k] for k in ['dataset','dim','num_queries','queries_file','hub_count','threads']}
        c['expected_candidates']=str(E28/'inputs'/ds/'proposals/candidates.i32');c['methods']=[]
        mapping=np.fromfile(E24/'inputs'/ds/'hub_ids.i32',np.int32)
        for p in policies(ds):
            if p['family']!='c8':continue
            name=p['model_name'];z=np.load(O/'results'/ds/(name+'.npz'));dest=O/'inputs'/ds/'route_reference';dest.mkdir(exist_ok=True)
            sf=dest/(name+'.slots.i32');ef=dest/(name+'.entries.i32')
            z['slot'].astype(np.int32).tofile(sf);mapping[z['selected_triples']].astype(np.int32).tofile(ef)
            p.update(expected_slots=str(sf),expected_entries=str(ef));c['methods'].append(p);files.extend([sf,ef])
        path=O/'inputs'/ds/'route_parity.json';dump(path,c);configs.append(path);files.extend([path,Path(c['queries_file']),Path(c['expected_candidates'])])
    dump(O/'reviews/deployment_matrix.json',dict(methods_per_dataset=[4,3],fit_calls=280112,development_calls=28896,conditional_validation_calls=490560,
        planned_total=799568,hard_cap=DEPLOY_CAP,validation_access=False))
    files.append(O/'reviews/deployment_matrix.json');freeze(O/'reviews/frozen_before_deployment.json',files)
    jobs=[]
    for ds,cfg in zip(DS,configs):
        argv=['taskset','-c','15',str(O/'bin/route_parity'),str(cfg),str(O/'reviews'/('route_parity_'+ds))]
        env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
        start=time.time()
        with (O/'logs'/('route_parity_'+ds+'.log')).open('x') as log:r=subprocess.run(argv,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=300)
        jobs.append(dict(dataset=ds,argv=argv,exit_code=r.returncode,seconds=time.time()-start,NSG_calls=0,HNSW_queries=160000))
        dump(O/'logs/route_parity_jobs.json',jobs)
        assert r.returncode==0,'route parity failed; stop before graph queries'
        assert read(O/'reviews'/('route_parity_'+ds)/'results.json')['status']=='PASS'
    dump(O/'reviews/route_parity.json',dict(status='PASS',queries=80000,HNSW_queries=320000,NSG_calls=0,GT_opened=False))
    print('ROUTE_PARITY_PASS',flush=True)

def execute(phase):
    assert read(O/'reviews/route_parity.json')['status']=='PASS';check_freeze(O/'reviews/frozen_before_deployment.json')
    if phase=='fit':
        for ds in DS:run(stage_config(ds,'fit'))
        dump(O/'results/fit_gate.json',dict(status='PASS',full_cache_parity=True,original_kernel_parity=True))
        dump(O/'state.json',dict(status='FIT_VERIFIED_DEVELOPMENT_PENDING',heldout_access=False))
    elif phase=='development':
        assert read(O/'results/fit_gate.json')['status']=='PASS'
        files=[];configs=[]
        for ds in DS:
            for split in ['cal','audit']:
                c=stage_config(ds,split);configs.append(c)
                files.extend(Path(c[k]) for k in ['queries_file','gt_file','row_ids','hub_ids'])
        freeze(O/'reviews/frozen_development_inputs.json',files)
        rows=[]
        for c in configs:
            result=run(c);ds=c['dataset'];default='gt10_soft' if ds==DS[0] else 'gt10_hard'
            metrics={m['model_name']:m for m in result['methods']};r,t,b=[metrics[k] for k in ['reward','teacher',default]]
            conditions=dict(reward_beats_teacher=r['total_hits']>t['total_hits'],reward_beats_default=r['total_hits']>b['total_hits'],graph_ndc_le_default_plus1pct=r['mean_graph_ndc']<=b['mean_graph_ndc']*1.01)
            rows.append(dict(dataset=ds,split=c['split'],conditions=conditions,passed=all(conditions.values()),reward_delta_teacher_pp=(r['recall_at_10']-t['recall_at_10'])*100,
                reward_delta_default_pp=(r['recall_at_10']-b['recall_at_10'])*100,graph_ndc_change_pct=(r['mean_graph_ndc']/b['mean_graph_ndc']-1)*100))
        passed=all(x['passed'] for x in rows)
        dump(O/'results/development_gate.json',dict(status='PASS_VALIDATION_ALLOWED' if passed else 'STOP_DEVELOPMENT_GATE',by_dataset_split=rows))
        dump(O/'state.json',dict(status='DEVELOPMENT_COMPLETE',gate='PASS_VALIDATION_ALLOWED' if passed else 'STOP_DEVELOPMENT_GATE',heldout_access=False))
        print(json.dumps(rows,indent=2),flush=True)
    elif phase=='validation':
        assert read(O/'results/development_gate.json')['status']=='PASS_VALIDATION_ALLOWED'
        files=[];configs=[]
        for ds in DS:
            c=stage_config(ds,'validation',5);assert c['num_queries']==2000;configs.append(c)
            files.extend(Path(c[k]) for k in ['queries_file','gt_file','row_ids','hub_ids'])
        freeze(O/'reviews/frozen_validation_inputs.json',files)
        for c in configs:run(c)
        dump(O/'state.json',dict(status='VALIDATION_COMPLETE_ANALYSIS_PENDING',heldout_access=False))
    else:raise ValueError(phase)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['parity','fit','development','validation']);args=parser.parse_args()
    if args.phase=='parity':route_parity()
    else:execute(args.phase)
