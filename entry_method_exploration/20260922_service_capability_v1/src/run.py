from common import *
from features import representation
from models import train_primary
from strong import train_gbdt, train_tabm
import signal
import resource
import shutil

def ridge_reference(ds, rep, roles):
    x = np.fromfile(OLD / 'results' / ds / 'fit_features/graph.features.f32', '<f4').reshape(4096, 64).astype('f8')
    fit, outer = np.asarray(roles['fit']), np.asarray(roles['outer'])
    z, mean, scale = standardize(x, fit)
    z = z.astype('f8')
    y = rep['utility'][:, 1:].reshape(4096, -1).astype('f8')
    intercept = y[fit].mean(0)
    gram = z[fit].T @ z[fit] / len(fit) + 10 * np.eye(64)
    rhs = z[fit].T @ (y[fit] - intercept) / len(fit)
    w = np.linalg.solve(gram, rhs)
    assert np.linalg.norm(gram @ w - rhs) / max(np.linalg.norm(rhs), 1e-30) < 1e-10
    return (z[outer] @ w + intercept).reshape(len(outer), -1, 2).astype('f4')

def guard():
    assert shutil.disk_usage(RUN).free >= 6 << 30
    assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss < 40 * (1 << 20)
    assert sum(p.stat().st_size for p in RUN.rglob('*') if p.is_file()) < 2 << 30

if __name__ == '__main__':
    os.sched_setaffinity(0, set(range(8)))
    lock = read(RUN / 'config.locked.json')
    assert read(RUN / 'reviews/preflight.json')['status'] == 'PASS'
    assert not (RUN / 'reviews/training_complete.json').exists()
    assert not (RUN / 'models').exists(), 'no silent refit or overwrite'
    signal.alarm(lock['max_seconds'])
    start = time.monotonic()
    sources = sorted((RUN / 'src').glob('*.py')) + sorted((RUN / 'vendor').glob('*.py'))
    dump(RUN / 'reviews/pretraining_freeze.json', dict(created_unix=time.time(), files=[identity(p) for p in sources],
        config=identity(RUN / 'config.locked.json'), protocol=identity(RUN / 'protocol.md'),
        implementation_addendum=dict(gradient_clip_norm_primary=10, offline_cpu_affinity=list(range(8)),
        standardization_min_std=1e-6, torch_threads=8, interop_threads=1)))
    dump(RUN / 'state.json', dict(status='RUNNING_CACHED_PILOT', pid=os.getpid(), default_changed=False, new_search_calls=0))
    for ds in lock['datasets']:
        data = load_data(ds)
        for fold, roles in enumerate(lock['roles'][ds]):
            guard()
            output = RUN / 'models' / ds / f'fold_{fold}'
            output.mkdir(parents=True)
            rep = representation(data, roles, fold)
            np.savez_compressed(output / 'representation.npz', **{k:v for k,v in rep.items() if k not in ['utility', 'dr', 'dt', 'cosine', 'cluster_scores']})
            outer = np.asarray(roles['outer'])
            dest = RUN / 'results' / ds / f'fold_{fold}'
            dest.mkdir(parents=True)
            np.savez_compressed(dest / 'labels.npz', rows=outer, source_rows=data['rows'][outer], utility=rep['utility'][outer],
                recall_delta=rep['dr'][outer], time_delta=rep['dt'][outer], tref=rep['tref'])
            controls = {'ClusterMean':rep['cluster_scores'][outer], 'E118Additive':ridge_reference(ds, rep, roles)}
            train = np.r_[roles['support'], roles['fit']]
            fixed = np.broadcast_to(rep['utility'][train, 1:].mean(0), (len(outer), len(data['hubs']), 2)).copy()
            controls['BestFixed'] = fixed
            for name, pred in controls.items():
                np.save(dest / f'{name}.npy', pred)
            for name in lock['primary'] + lock['strong']:
                guard()
                dump(RUN / 'progress.json', dict(dataset=ds, fold=fold, method=name, seconds=time.monotonic() - start))
                print('START', ds, fold, name, flush=True)
                if name in lock['primary']:
                    pred = train_primary(rep, roles, name, data['hubs'], output / name)
                elif name == 'GBDT':
                    pred = train_gbdt(rep, roles, data['hubs'], output / name)
                else:
                    pred = train_tabm(rep, roles, data['hubs'], output / name)
                assert pred.shape == (1024, len(data['hubs']), 2) and np.isfinite(pred).all()
                np.save(dest / f'{name}.npy', pred)
                print('DONE', ds, fold, name, 'total_seconds', time.monotonic() - start, flush=True)
    guard()
    dump(RUN / 'reviews/training_complete.json', dict(status='COMPLETE', seconds=time.monotonic() - start,
        maxrss_gib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/(1 << 20), new_search_calls=0,
        fitted_primary=32, fitted_GBDT_heads=16, fitted_TabM=8))
    dump(RUN / 'state.json', dict(status='TRAINED_PENDING_ANALYSIS', default_changed=False, new_search_calls=0))
