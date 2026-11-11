"""Read-only reanalysis of sealed E195 single-seed probes; no ANN or training."""
import collections
import csv
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT.parent / '20261101_residual_navigation_diagnosis_v1'
DATASETS = ['coco', 'flickr30k', 'webvid2_5m_light_v1',
            'yandex_t2i_official10M_ip_v1', 'deep10m_l2_v1',
            'sift10m_bigann_l2_v1', 'gist1m_l2_v1']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


source = OLD / 'analysis/single_seed.csv'
rows = list(csv.DictReader(source.open()))
inputs = [dict(path=str(source), sha256=sha(source))]
raw_rows = []
for ds in DATASETS:
    for window in ['A', 'B']:
        path = OLD / 'storage/results' / ds / window / 'single_seed.csv.gz'
        inputs.append(dict(path=str(path), sha256=sha(path)))
        with gzip.open(path, 'rt') as stream:
            raw_rows.extend(dict(dataset=ds, window=window, **r)
                            for r in csv.DictReader(stream))

# Verify every field against original native diagnostic files, irrespective of order.
fields = list(rows[0])
canonical = lambda r: tuple(r[f] for f in fields)
assert len(rows) == len(raw_rows) == 10752
assert collections.Counter(map(canonical, rows)) == collections.Counter(map(canonical, raw_rows))
groups = collections.defaultdict(list)
for r in rows:
    assert int(r['L']) == 200
    assert int(r['net_vs_B32']) == int(r['new_hits_vs_B32']) - int(r['lost_vs_B32'])
    groups[r['dataset'], int(r['K']), r['window'], int(r['query'])].append(r)

query_rows = []
for (ds, k, window, query), seeds in groups.items():
    seeds.sort(key=lambda r: int(r['C_rank']))
    assert [int(r['C_rank']) for r in seeds] == list(range(6))
    values = [int(r['net_vs_B32']) for r in seeds]
    best = max(values)
    query_rows.append(dict(
        dataset=ds, K=k, L=200, window=window, query=query, probes=6,
        positive_probes=sum(v > 0 for v in values),
        zero_probes=sum(v == 0 for v in values),
        negative_probes=sum(v < 0 for v in values),
        closest_net_hits=values[0], best_single_seed_net_hits=best,
        best_or_none_net_hits=max(0, best),
        any_positive=int(best > 0), better_than_closest=int(best > values[0])))

result = []
for ds in DATASETS:
    for k in [1, 100]:
        for window in ['A', 'B', 'pooled']:
            part = [r for r in query_rows if r['dataset'] == ds and r['K'] == k
                    and (window == 'pooled' or r['window'] == window)]
            row = dict(dataset=ds, K=k, L=200, window=window, queries=len(part))
            for name in ['probes', 'positive_probes', 'zero_probes', 'negative_probes',
                         'closest_net_hits', 'best_single_seed_net_hits',
                         'best_or_none_net_hits', 'any_positive', 'better_than_closest']:
                row[name] = sum(r[name] for r in part)
            # A second aggregation works directly from raw native rows.
            raw_groups = collections.defaultdict(list)
            for r in raw_rows:
                if r['dataset'] == ds and int(r['K']) == k and (window == 'pooled' or r['window'] == window):
                    raw_groups[r['window'], r['query']].append(r)
            assert row['queries'] == len(raw_groups)
            assert row['best_single_seed_net_hits'] == sum(
                max(int(r['net_vs_B32']) for r in seeds) for seeds in raw_groups.values())
            assert row['closest_net_hits'] == sum(
                int(next(r for r in seeds if int(r['C_rank']) == 0)['net_vs_B32'])
                for seeds in raw_groups.values())
            result.append(row)

for name, data in [('seed_quality_summary.csv', result), ('seed_quality_queries.csv', query_rows)]:
    with (ROOT / 'analysis' / name).open('w') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(data[0]))
        writer.writeheader()
        writer.writerows(data)

assert all(sha(Path(x['path'])) == x['sha256'] for x in inputs)
receipt = dict(
    status='PASS_EXISTING_SINGLE_SEED_REANALYSIS', source_rows=len(rows),
    query_K_instances=len(query_rows), summary_rows=len(result), inputs=inputs,
    original_native_gzip_all_fields_equal=True, second_aggregation_equal=True,
    new_ANN_calls=0, new_training=0, new_QPS_measurements=0,
    scope='Exposed A/B, first 64 queries each, top-six C, L200, single seed, cap384; GT-aware best is diagnostic only')
(ROOT / 'analysis/reanalysis_validation.json').write_text(
    json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k: v for k, v in receipt.items() if k != 'inputs'}, ensure_ascii=False))
