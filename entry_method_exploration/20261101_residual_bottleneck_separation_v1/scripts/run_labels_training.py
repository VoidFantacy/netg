from common import *
started = time.perf_counter()
progress = R / 'reviews/labels_training_progress.json'
records = read(progress) if progress.exists() else []
for ds in DS:
    c = read(R / 'configs' / f'{ds}.labels.json')
    label_info = Path(c['output_dir']) / 'complete.json'
    model_info = R / 'storage/models' / ds / 'selected.json'
    stages = [('labels', ['taskset','-c','15',str(R/'storage/labels_benchmark'),
                          'labels',str(R/'configs'/f'{ds}.labels.json')], label_info),
              ('train', [str(REPO/'.venv_cpu/bin/python'),str(R/'scripts/train.py'),ds], model_info)]
    for stage, argv, completion in stages:
        if completion.exists():
            info = read(completion)
            if stage == 'labels': assert info['queries']==3072 and info['status']=='PASS_ACTUAL_SINGLE_SEED_LABELS'
            else: assert info['fit_queries']==2048 and info['cal_queries']==1024
            print('REUSE_COMPLETED',ds,stage,flush=True)
            continue
        log_path = R/'reviews'/f'{ds}.{stage}.log'
        if log_path.exists(): log_path.rename(log_path.with_name(log_path.stem+f'.attempt_{time.time_ns()}.log'))
        t=time.perf_counter()
        with log_path.open('w') as log:
            p=subprocess.Popen(argv,cwd=REPO,stdout=log,stderr=subprocess.STDOUT)
            dump(R/'live_process.json',dict(stage=stage,dataset=ds,pid=p.pid,argv=argv,started_unix=time.time()))
            code=p.wait()
        records.append(dict(dataset=ds,stage=stage,pid=p.pid,argv=argv,returncode=code,seconds=time.perf_counter()-t))
        dump(progress,records)
        print(ds,stage,code,records[-1]['seconds'],flush=True)
        assert code==0,(ds,stage)
dump(R/'reviews/labels_training_complete.json',dict(status='PASS_ALL_SEVEN_LABELS_AND_MODELS',
    records=records,continuation_process_seconds=time.perf_counter()-started))
