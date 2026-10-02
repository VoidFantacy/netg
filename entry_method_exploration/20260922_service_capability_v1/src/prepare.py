"""Freeze sources and roles before reading response labels."""
from common import *
import shutil
import subprocess

if __name__ == '__main__':
    assert not (RUN / 'config.locked.json').exists()
    oldlock = read(OLD / 'config.locked.json')
    for name in ['AGENTS.md', 'summary.md', 'spec.md', 's-target.md', 's-experiment.md', 'experiment_history/README.md']:
        out = RUN / 'source_before' / name
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, out)
    roles = {}
    for ds in oldlock['datasets']:
        rng = np.random.default_rng(20260922)
        folds = np.empty(4096, 'i4')
        folds[rng.permutation(4096)] = np.arange(4096) % 4
        roles[ds] = []
        for f in range(4):
            tr = np.random.default_rng(20260922 + f).permutation(np.flatnonzero(folds != f))
            one = dict(support=tr[:1024].tolist(), fit=tr[1024:2816].tolist(), monitor=tr[2816:].tolist(), outer=np.flatnonzero(folds == f).tolist())
            assert sorted(sum(one.values(), [])) == list(range(4096))
            roles[ds].append(one)
    dump(RUN / 'config.locked.json', dict(experiment='E119', created_unix=time.time(), seed=20260922,
         datasets=list(oldlock['datasets']), roles=roles, cost_weight=0.1,
         primary=['GeomMSE', 'CapMSE', 'GeomRank', 'CapRank'], strong=['GBDT', 'TabM'],
         max_seconds=43200, max_rss_gib=40, min_free_gib=6, max_new_bytes=2 << 30,
         new_search_calls=0, new_gt=False, default_change=False,
         protocol=identity(RUN / 'protocol.md'), research=identity(RUN / 'research.md')))
    sources = [OLD / 'config.locked.json', OLD / 'reviews/independent_final_audit.json']
    for ds, c in oldlock['datasets'].items():
        for name in ['queries.f32', 'gt.i64', 'row_ids.i64', 'identity.json']:
            sources.append(OLD / 'inputs' / ds / 'fit' / name)
        sources.extend(Path(c['anchor'][k]) for k in ['W', 'ids', 'graph'])
        sources.extend(sorted((OLD / 'results' / ds / 'labels').rglob('*')))
        sources.append(OLD / 'results' / ds / 'fit_features/graph.features.f32')
    sources = sorted(set(p for p in sources if p.is_file()))
    dump(RUN / 'reviews/source_identity.json', dict(status='FROZEN', created_unix=time.time(), files=[identity(p) for p in sources],
         inherited_base_and_graph={ds: dict(base=c['base'], index=c['index'], index_stat=c['index_stat']) for ds, c in oldlock['datasets'].items()}))
    dump(RUN / 'state.json', dict(status='PROTOCOL_FROZEN', stage='implementation_and_preflight', default_changed=False, new_search_calls=0))
    print('FROZEN', len(sources), 'source files', flush=True)
