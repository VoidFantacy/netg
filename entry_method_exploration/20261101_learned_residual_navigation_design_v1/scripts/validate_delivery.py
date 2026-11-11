"""Validate this design/report delivery, not the proposed algorithm."""
import csv
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
OLD = ROOT.parent / '20261101_residual_navigation_cost_controls_v1'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(path.read_text())


def dump(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


snapshots = read(ROOT / 'source_manifest.json')
manifest = OLD / 'delivery_manifest.json'
assert sha(manifest) == snapshots['manifest_sha256']
bridges = {x['path']: x for x in snapshots['roots']}
unchanged = bridged = 0
for x in read(manifest)['files']:
    path = Path(x['path'])
    if sha(path) == x['sha256']:
        unchanged += 1
    else:
        bridge = bridges[str(path)]
        assert sha(Path(bridge['snapshot'])) == x['sha256'] == bridge['sha256']
        bridged += 1
for x in snapshots['roots']:
    assert sha(Path(x['snapshot'])) == x['sha256']

receipt = read(ROOT / 'analysis/reanalysis_validation.json')
assert receipt['source_rows'] == 10752
assert receipt['original_native_gzip_all_fields_equal']
assert receipt['second_aggregation_equal']
for x in receipt['inputs']:
    assert sha(Path(x['path'])) == x['sha256']
rows = list(csv.DictReader((ROOT / 'analysis/seed_quality_summary.csv').open()))
assert len(rows) == 42
pooled = {(r['dataset'], int(r['K'])): r for r in rows if r['window'] == 'pooled'}
expected = {
    'coco': (132, 54, 36, 33, 92),
    'flickr30k': (113, 52, 38, 25, 71),
    'webvid2_5m_light_v1': (383, 118, 85, 226, 550),
    'yandex_t2i_official10M_ip_v1': (255, 91, 68, 102, 241),
    'deep10m_l2_v1': (115, 52, 30, 29, 69),
    'sift10m_bigann_l2_v1': (65, 40, 30, 14, 46),
    'gist1m_l2_v1': (278, 97, 74, 56, 195)}
report = (ROOT / 'report_zh.md').read_text()
for ds, values in expected.items():
    r = pooled[ds, 100]
    assert int(r['queries']) == 128 and int(r['probes']) == 768
    fields = ['positive_probes', 'any_positive', 'better_than_closest',
              'closest_net_hits', 'best_single_seed_net_hits']
    assert tuple(int(r[f]) for f in fields) == values
    a, b, c, d, e = values
    assert f'| {a} | {b} | {c} | {d} / {e} |' in report
assert sum(int(pooled[ds, 100]['positive_probes']) for ds in expected) == 1341
assert sum(int(pooled[ds, 100]['zero_probes']) for ds in expected) == 4035
assert sum(int(pooled[ds, 1]['positive_probes']) for ds in expected) == 25
assert sum(int(pooled[ds, 1]['any_positive']) for ds in expected) == 13

documents = [ROOT / 'README.md', ROOT / 'report_zh.md'] + [
    REPO / name for name in ['summary.md', 'spec.md', 's-target.md',
                             's-experiment.md', 'LOCAL_CODEX_START.md']]
# Outputs below are already part of the delivery contract, so create state before link validation.
state = dict(
    status='COMPLETED_METHOD_DESIGN_AND_EXISTING_PROBE_REANALYSIS',
    algorithm_status='THEORY_ONLY_UNIMPLEMENTED_UNTESTED',
    requested_report_completed=True, new_experiment_number=None,
    new_training=False, new_ANN=False, new_GT=False, new_QPS=False,
    default_changed=False, new_PDF=False,
    priority='Residual navigation entry quality and filtering; offline training cost not a current constraint')
dump(ROOT / 'state.json', state)
local_links = 0
validation_path = ROOT / 'validation.json'
for doc in documents:
    for target in re.findall(r'\]\(([^)]+)\)', doc.read_text()):
        if target.startswith(('https://', 'http://', '#')):
            continue
        path = (doc.parent / target.strip('<>').split('#')[0]).resolve()
        assert path.exists() or path == validation_path, (doc, target)
        local_links += 1
assert 'THEORY_ONLY_UNIMPLEMENTED_UNTESTED' in report
assert '训练费用' in (REPO / 's-target.md').read_text()
assert not list(ROOT.rglob('*.pdf'))
validation = dict(
    status='PASS_DESIGN_DOCUMENT_DELIVERY',
    E196_manifest_unchanged=True, E196_unchanged_files=unchanged,
    E196_mutable_roots_bridged=bridged, snapshots_verified=len(bridges),
    E195_probe_inputs_unchanged=True, report_table_verified=True,
    local_links_checked=local_links, checks_are_not_algorithm_or_performance_validation=True,
    no_new_training_ANN_GT_QPS=True, default_changed=False)
dump(validation_path, validation)
files = []
for path in sorted(ROOT.rglob('*')):
    if path.is_file() and path.name != 'delivery_manifest.json':
        files.append(dict(path=str(path.relative_to(ROOT)), bytes=path.stat().st_size,
                          sha256=sha(path)))
dump(ROOT / 'delivery_manifest.json', dict(
    status='SEALED_DESIGN_REPORT_DELIVERY', files=files,
    current_root_files=[dict(path=str(p.relative_to(REPO)), sha256=sha(p))
                        for p in documents if p.is_relative_to(REPO) and not p.is_relative_to(ROOT)]))
print(json.dumps(validation, ensure_ascii=False))
