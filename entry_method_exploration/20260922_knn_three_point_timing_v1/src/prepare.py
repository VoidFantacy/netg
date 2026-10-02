from common import *
import shutil

assert not (RUN/'config.locked.json').exists()
for name in ['bin','logs','reviews','results','models','source_before']:
    (RUN/name).mkdir(exist_ok=True)
for name in ['summary.md','spec.md','s-target.md','s-experiment.md','AGENTS.md']:
    shutil.copy2(ROOT/name,RUN/'source_before'/name)
for path in (OLD/'src').rglob('*'):
    if path.suffix in ['.cpp','.hpp','.h'] and path != OLD/'src/evaluate.cpp':
        out = RUN/'src'/path.relative_to(OLD/'src')
        out.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(path,out)
old = read(OLD/'config.locked.json')
datasets = {}
consumed = {OLD/'seal.json',OLD/'config.locked.json',OLD/'analysis/information.json'}
for ds, cfg in old['datasets'].items():
    info_path = OLD/'analysis'/f'{ds}.information.npz'
    response_path = OLD/'analysis'/f'{ds}.npz'
    roles_path = OLD/'analysis'/f'{ds}.information_roles.json'
    consumed.update([info_path,response_path,roles_path])
    info, data, roles = np.load(info_path), np.load(response_path), read(roles_path)
    native = cfg['native']
    q = np.fromfile(native['queries'],'<f4').reshape(4096,native['dimension']).astype('f8')
    q /= np.linalg.norm(q,axis=1,keepdims=True)
    names = [m['name'] for m in native['methods']]
    cols = [names.index(a) for a in old['actions']]
    hits = np.stack([data[f'K{K}_L{cfg["target"][str(K)][1]}'][:,cols] for K in [1,100]],axis=-1)
    labels = hits-hits[:,:1]
    model = RUN/'models'/ds
    model.mkdir()
    info['folds'].astype('<i4').tofile(model/'folds.i32')
    info['TargetKNN_actions'].astype('<i4').tofile(model/'expected_actions.i32')
    info['neighbors'].astype('<i4').tofile(model/'expected_neighbors.i32')
    for f in range(4):
        fit = np.array(roles[str(f)]['fit'])
        assert len(fit)==3072 and np.all(info['folds'][fit] != f)
        q[fit].astype('<f8').tofile(model/f'fit{f}.f64')
        labels[fit].astype('<i2').tofile(model/f'labels{f}.i16')
        data['source_rows'][fit].astype('<i8').tofile(model/f'sources{f}.i64')
        fit.astype('<i4').tofile(model/f'rows{f}.i32')
    all_entries = []
    for action in old['actions']:
        path = E107/'results'/('main_'+ds)/action/'entries.i32'
        consumed.add(path)
        all_entries.append(np.fromfile(path,'<i4').reshape(4096,3))
    entries = np.stack(all_entries,axis=1)
    entries[:,0].tofile(model/'default_entries.i32')
    for k,K in enumerate([1,100]):
        entries[np.arange(4096),info['TargetKNN_actions'][:,k]].tofile(model/f'expected_entries_k{K}.i32')
    grid = {'1':[640,800,1000],'100':[800,1120,1250]} if ds.startswith('web') else {'1':[64,96,128],'100':[128,200,256]}
    for K,Ls in grid.items():
        for L in Ls:
            ref = Path(native['reference'])/f'k{K}'/(native['reference_method']+f'_L{L}')
            for name in ['ids.i32','distances.f32']:
                assert (ref/name).exists()
                consumed.add(ref/name)
    for key in ['queries','GT','rows','hub_ids']:
        consumed.add(Path(native[key]))
    for m in native['methods']:
        for key in ['W','graph','ids']:
            if key in m:
                consumed.add(Path(m[key]))
    index_stat = Path(native['index']).stat()
    datasets[ds] = dict(native=native,grid=grid,model=str(model),
        graph_stat=dict(bytes=index_stat.st_size,mtime_ns=index_stat.st_mtime_ns),
        actions=[native['methods'][names.index(a)] for a in old['actions']])
for item in read(OLD/'reviews/header_dependencies.json')['files']:
    consumed.add(Path(item['path']))
build = read(OLD/'reviews/jobs_v2.json')[0]['argv']
for arg in build:
    if arg.endswith('.a'):
        consumed.add(Path(arg))
dump(RUN/'reviews/inputs.json',dict(files=[identity(p) for p in sorted(consumed)]))
dump(RUN/'config.locked.json',dict(datasets=datasets,n=4096,repeats=3,warmup=128,smoke=16,
    cpu=15,threads=1,expected_calls=298752,seconds_cap=3600,job_seconds_cap=1800,
    max_rss_gib=40,max_new_bytes=1<<30,min_free_gib=6,methods=['DefaultGT10','TargetKNN'],
    formal_evaluation=False,complete_query_wall=True,created_unix=time.time()))
preserve_check()
dump(RUN/'state.json',dict(status='PREPARED',completed=False,pending=['build','two_serial_jobs','analysis','docs']))
print('PREPARED', len(consumed), 'protected inputs', flush=True)
