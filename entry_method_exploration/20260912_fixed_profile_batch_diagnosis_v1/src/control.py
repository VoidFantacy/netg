"""E39 fixed-action diagnosis. No optimizer or model selection exists here."""
from pathlib import Path
import os, sys, json, time, hashlib, shutil, resource, itertools, csv
import numpy as np

R = Path('/data/netg/ACSG')
E = R/'entry_method_exploration/20260912_offline_profile_rl_v1'
D = R/'entry_method_exploration/20260912_offline_profile_diagnosis_v1'
O = Path(__file__).resolve().parents[1]
DS = ['webvid2_5m_light_v1', 'yandex_t2i_official10M_ip_v1']
MODELS = ['rl_20260921', 'rl_20260922']
SELECTED = [140, 40]
FIELDS = ['ids', 'distances', 'entries', 'route_ndc', 'graph_ndc']
sys.dont_write_bytecode = True
sys.path.insert(0, str(E/'src'))
from common import profiles, digest, sha, identity, read, dump

def files(root):
    return sorted(p for p in root.rglob('*') if p.is_file())

def freeze(path, paths):
    assert not path.exists(), path
    dump(path, {'files': [identity(p) for p in sorted(set(paths))], 'time': time.time()})

def check(path):
    for f in read(path)['files']:
        assert sha(f['path']) == f['sha256'], f['path']

def resources():
    assert shutil.disk_usage(O).free >= 10*(1<<30), 'free disk <10GiB'
    assert sum(p.stat().st_size for p in files(O)) <= 128*(1<<20), 'output >128MiB'

def save_np(path, **arrays):
    assert not path.exists(), path
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, **arrays)

def cfg(ds):
    return read(O/'inputs'/ds/'config.json')

def context(ds, name):
    return dict(np.load(O/'inputs'/ds/(name+'.npz')))

def score(ids, gt):
    return (ids[..., None] == gt[:, None, :10]).any(axis=-2).sum(axis=-1).astype(np.uint8)

def parity_data(native, n):
    return dict(ids=native.data(0,np.int32).reshape(n,10),
                distances=native.data(1,np.float32).reshape(n,10),
                entries=native.data(2,np.int32).reshape(n,3),
                route_ndc=native.data(3,np.uint32), graph_ndc=native.data(4,np.uint32))

def equal(a, b):
    for k in FIELDS:
        assert a[k].dtype == b[k].dtype and a[k].shape == b[k].shape, k
        assert a[k].tobytes() == b[k].tobytes(), k

def prepare():
    assert not (O/'config.locked.json').exists()
    resources()
    for folder in ['reviews','inputs','results','models','logs','source_before','figures']:
        (O/folder).mkdir(exist_ok=True)
    docs = ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md',
            'experiment_history/README.md','experiment_history/27_offline_profile_diagnosis.md']
    for p in docs:
        shutil.copy2(R/p, O/'source_before'/p.replace('/','__'))
    freeze(O/'reviews/old_directories.json', files(E)+files(D))
    upstream = read(E/'reviews/upstream.json')['files']
    # This list is inspected as metadata first; no recursive old evaluation reads.
    deps = [x for x in upstream if str(R/'indices') in x['path'] or
            x['path'].endswith(('.cpp','.hpp','.h','.a','.so'))]
    assert all('validation' not in x['path'] and 'held' not in x['path'] for x in deps)
    for x in deps:
        assert sha(x['path']) == x['sha256'], x['path']
    dump(O/'reviews/native_dependencies.json', {'files': deps})
    records = []
    for i, ds in enumerate(DS):
        old = read(E/'inputs'/ds/'config.json')
        dst = O/'inputs'/ds; dst.mkdir()
        model = E/'models'/ds/MODELS[i]
        selected = read(model/'selected/identity.json')
        assert selected['step'] == SELECTED[i]
        assert read(E/'results/cal_selection.json')['selection'][ds]['rl']['model'] == MODELS[i]
        trajectories = [dict(np.load(model/'trajectory'/f'{s+1:04}.npz')) for s in [0,SELECTED[i]]]
        excluded = np.union1d(trajectories[0]['rows'], trajectories[1]['rows']).astype(np.int32)
        eligible = np.setdiff1d(np.arange(4096,dtype=np.int32), excluded)
        rows = np.random.Generator(np.random.PCG64(2026091201+i)).choice(eligible,1024,replace=False).astype(np.int32)
        save_np(dst/'rows.npz', rows=rows, excluded=excluded, eligible=eligible)
        # Query selection is finalized above before any GT data are opened.
        c = {k:old[k] for k in ['dataset','dim','hub_count','hub_ids','index_path','P','basis']}
        for key, dtype, width, suffix in [('queries_file',np.float32,old['dim'],'queries.f32'),
                                          ('gt_file',np.int64,100,'gt.i64'),
                                          ('row_ids',np.int64,1,'row_ids.i64')]:
            a = np.memmap(old[key],dtype=dtype,mode='r')[:4096*width]
            a.tofile(dst/suffix); c[key]=str(dst/suffix)
        c.update(num_queries=4096,threads=1,query_cpu=15,L=128,native_call_cap=19296)
        dump(dst/'config.json',c)
        p=np.fromfile(c['P'],np.float32).reshape(c['hub_count'],c['dim'])
        b=np.fromfile(c['basis'],np.float64).reshape(c['dim'],16)
        for name,s,t in zip(['zero','selected'],[0,SELECTED[i]],trajectories):
            cp=dict(np.load(model/'checkpoints'/f'{s:04}.npz'))
            assert t['mu_before'].tobytes()==cp['mu'].tobytes()
            assert np.array_equal(t['actions'],t['mu_before']+.3*t['eps'])
            center=profiles(p,b,t['mu_before'])
            meta=next(x for x in read(model/'checkpoints.json') if x['step']==s)
            assert digest(center)==meta['W_sha']
            for j in range(8):
                assert digest(profiles(p,b,t['actions'][j]))==str(t['W_sha'][j])
            save_np(dst/(name+'.npz'),mu=t['mu_before'],eps=t['eps'],actions=t['actions'],
                    original_rows=t['rows'],W_sha=t['W_sha'],topology_sha=t['topology_sha'])
            dump(dst/(name+'.json'),dict(model=MODELS[i],step=s,trajectory=str(model/'trajectory'/f'{s+1:04}.npz'),
                 checkpoint=str(model/'checkpoints'/f'{s:04}.npz'),center_W_sha=meta['W_sha'],center_topology_sha=meta['topology_sha']))
        records.append(dict(dataset=ds,model=MODELS[i],selected_step=SELECTED[i],seed=2026091201+i,
                            excluded=len(excluded),eligible=len(eligible),query_count=1024,rows_sha=digest(rows)))
    dump(O/'config.locked.json',dict(datasets=records,normal_NSG=36864,parity_NSG=1728,expected_NSG=38592,
          hard_cap=40000,expected_HNSW=38016,builds=36,optimizer_updates=0,new_GT=0,threads=1,
          practical_gate=dict(primary_cos_min=.3,balanced_median_cos_min=.3,balanced_positive_fraction_min=.75)))
    freeze(O/'reviews/prequery_freeze.json',files(O/'inputs')+files(O/'src')+[O/'protocol.md',O/'config.locked.json'])
    dump(O/'state.json',dict(status='PREPARED_FIXED_ACTIONS_NO_NEW_SEARCH',NSG_calls=0,optimizer_updates=0))
    print(json.dumps(records),flush=True)

def run(ds):
    assert ds in DS
    check(O/'reviews/prequery_freeze.json'); resources()
    assert os.sched_getaffinity(0)=={15}
    for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:
        assert os.environ[key]=='1'
    resource.setrlimit(resource.RLIMIT_AS,(32*(1<<30),32*(1<<30)))
    jobs_path=O/'logs/jobs.json'
    jobs=read(jobs_path) if jobs_path.exists() else []
    assert not any(j['dataset']==ds for j in jobs), 'job already reserved; no automatic retry'
    assert sum(j['reserved'] for j in jobs)+19296<=40000
    job=dict(dataset=ds,reserved=19296,status='RUNNING',started_at=time.time(),pid=os.getpid())
    jobs.append(job);dump(jobs_path,jobs)
    from native import Native
    c=cfg(ds); start=time.monotonic(); native=Native(c); loaded=time.monotonic()-start
    p=np.fromfile(c['P'],np.float32).reshape(c['hub_count'],c['dim'])
    b=np.fromfile(c['basis'],np.float64).reshape(c['dim'],16)
    rows=np.load(O/'inputs'/ds/'rows.npz')['rows']
    metadata=[]
    try:
        for name in ['zero','selected']:
            t=context(ds,name); meta=read(O/'inputs'/ds/(name+'.json'))
            old_t=dict(np.load(meta['trajectory'])); old_cp=dict(np.load(meta['checkpoint']))
            for j in range(9):
                resources(); label='center' if j==8 else f'action{j}'
                outdir=O/'models'/ds/name/label; outdir.mkdir(parents=True)
                x=t['mu'] if j==8 else t['actions'][j]
                w=profiles(p,b,x); topo=native.build(w)
                expected_w=meta['center_W_sha'] if j==8 else str(t['W_sha'][j])
                expected_t=meta['center_topology_sha'] if j==8 else str(t['topology_sha'][j])
                assert digest(w)==expected_w and topo==expected_t
                w.tofile(outdir/'W.f32');native.save(outdir/'graph.hnsw')
                parity_rows=np.arange(16,dtype=np.int32) if j==8 else t['original_rows'][:16]
                native.verify(outdir/'graph.hnsw',parity_rows)
                observed=parity_data(native,16)
                reference={k:old_cp[k][:16] if j==8 else old_t[k][j,:16] for k in FIELDS}
                equal(observed,reference)
                save_np(outdir/'parity.npz',rows=parity_rows,**observed)
                raw=native.run(rows)
                save_np(O/'results'/ds/name/(label+'.npz'),rows=rows,**raw)
                st=native.stats(); assert st['actual_threads']==1
                rec=dict(dataset=ds,context=name,label=label,W_sha=digest(w),topology_sha=topo,
                         graph_file_sha=sha(outdir/'graph.hnsw'),drift=float(np.square(w.astype(float)-p).sum(1).mean()),
                         original_parity='PASS',stats=st,elapsed_seconds=time.monotonic()-start)
                metadata.append(rec);dump(outdir/'identity.json',rec)
                print(json.dumps({k:rec[k] for k in ['dataset','context','label','stats']}),flush=True)
        st=native.stats();assert st['NSG_calls']==19296 and st['HNSW_calls']==19008 and st['builds']==18
        job.update(status='COMPLETE',actual=st['NSG_calls'],native=st,load_seconds=loaded,
                   wall_seconds=time.monotonic()-start,peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                   completed_at=time.time())
        dump(jobs_path,jobs);dump(O/'results'/ds/'execution.json',metadata)
    finally:
        native.close()

if __name__=='__main__':
    if sys.argv[1]=='prepare': prepare()
    elif sys.argv[1]=='run': run(sys.argv[2])
    else: raise ValueError(sys.argv[1])
