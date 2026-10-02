"""Verify the geometry source against registered full-base checksums."""
from common import *
import importlib.metadata

if __name__ == '__main__':
    start = time.monotonic()
    records = []
    old = read(OLD/'config.locked.json')
    for ds,c in old['datasets'].items():
        base = Path(c['base'])
        manifest = read(base.parent/'manifest.json')
        expected = manifest['files'][base.name]
        actual = identity(base)
        assert actual['bytes'] == expected['bytes'] and actual['sha256'] == expected['sha256']
        graph = Path(c['index'])
        assert graph.stat().st_size == c['index_stat']['bytes']
        assert graph.stat().st_mtime_ns == c['index_stat']['mtime_ns']
        records.append(dict(dataset=ds, base=actual, graph_stat_matches_E118=True,
                            graph_full_hash_recomputed=False))
        print('BASE_SHA_PASS', ds, flush=True)
    dump(RUN/'reviews/asset_audit.json', dict(status='PASS', records=records,
        packages={p:importlib.metadata.version(p) for p in ['numpy','scipy','scikit-learn','torch','matplotlib','threadpoolctl']},
        seconds=time.monotonic()-start, source_vectors_mutated=False))
