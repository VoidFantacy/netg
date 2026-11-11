"""Final requirement audit; run only after numerical, visual and document review."""
from pathlib import Path
import csv
import hashlib
import json
import math
import os
import re
import time
from urllib.parse import unquote

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[1]
OUT = RUN / 'analysis/final_v1'


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024**2), b''):
            h.update(block)
    return h.hexdigest()


def main():
    started = time.time()
    lock = read(RUN / 'config.locked.json')
    assert lock['methods'] == ['NSG', 'GT10', 'GT10+Residual', 'GATE']
    assert len(lock['datasets']) == 4 and lock['timing_repeats'] == 2
    assert lock['threads'] == 1 and lock['cpu'] == 15
    assert not lock['default_change']
    expected = {(ds, k, l, m) for ds in lock['datasets'] for k in [1, 100]
                for l in lock['K_L'][str(k)] for m in lock['methods']}
    assert len(expected) == 640
    assert all(len(lock['K_L'][str(k)]) == 20 for k in [1, 100])
    qualification = read(RUN / 'reviews/qualification.json')
    assert qualification['status'] == 'PASS' and qualification['new_native_points'] == 64
    for name, count in [('old_NSG_GT10_B32_comparisons', 48), ('legacy_GATE_comparisons', 16)]:
        rows = qualification[name]
        assert len(rows) == count
        assert all(all(v['equal'] for v in row['checks'].values()) for row in rows)
    for ds in ['coco', 'flickr30k']:
        inp = RUN / 'inputs' / ds
        model = RUN / 'models' / ds / 'gate_disjoint_labels_v1'
        manifest = read(inp / 'manifest.json')
        assert manifest['exact_vector_and_identity_groups_disjoint_from_test']
        assert manifest['GATE_train_monitor_disjoint'] and manifest['roles_overlap_B32_supervision']
        parity = read(inp / 'labels/parity.json')
        assert parity['status'] == 'PASS' and parity['queries'] == 32 and parity['returned_k'] == 1
        assert read(model / 'independence.json')['status'] == 'PASS'
        done = read(model / 'complete.json')
        assert done['status'] == 'COMPLETE'
        assert sha(model / 'best.pt') == done['checkpoint_sha256']
        assert sha(model / 'W.f32') == done['best']['embedding_sha256']
    measurement = read(RUN / 'reviews/measurement_complete.json')
    assert measurement['status'] == 'PASS' and measurement['all_frozen_inputs_full_sha_after']
    assert (measurement['points'], measurement['batches'], measurement['queries']) == (640, 1280, 11200000)
    with (OUT / 'points.csv').open() as f:
        points = list(csv.DictReader(f))
    assert len(points) == 640
    assert {(p['dataset'], int(p['K']), int(p['L']), p['method']) for p in points} == expected
    with (OUT / 'rounds.csv').open() as f:
        rounds = list(csv.DictReader(f))
    assert len(rounds) == 1280
    assert sum(int(r['n']) for r in rounds) == 11200000
    assert all(int(r['threads']) == 1 and int(r['cpu']) == 15 for r in rounds)
    for p in points:
        mean = (float(p['qps_round0']) + float(p['qps_round1'])) / 2
        assert math.isclose(float(p['qps_mean']), mean, rel_tol=1e-13)
    independent = read(OUT / 'independent_audit.json')
    assert independent['status'] == 'PASS_INDEPENDENT_STDLIB_ALL_POINTS'
    assert independent['points'] == 640 and independent['archive_files_roundtrip_verified'] == 2560
    visual = read(OUT / 'visual_review.json')
    assert visual['status'] == 'PASS_ACTUAL_RENDER_INSPECTION'
    for k in [1, 100]:
        for ext in ['png', 'svg']:
            p = OUT / 'figures' / f'recall_qps_k{k}.{ext}'
            assert p.is_file() and p.stat().st_size > 1000
            assert visual['files'][str(p.relative_to(OUT))] == sha(p)
    review = read(OUT / 'report_review.json')
    assert review['status'] == 'PASS_EVIDENCE_AND_SCOPE_REVIEW'
    assert review['report_sha256'] == sha(OUT / 'report_zh.md')
    assert all(review['checks'].values())
    # Check frozen runtime data and source identity again after postprocessing.
    frozen = read(RUN / 'formal_freeze.json')
    for name, identity in frozen['files'].items():
        p = Path(name)
        assert p.stat().st_size == identity['bytes'] and sha(p) == identity['sha256'], name
    for name, digest in read(RUN / 'reviews/source_origins.json')['E97_sources'].items():
        assert sha(name) == digest, name
    for name, digest in read(RUN / 'reviews/root_snapshot_bridge.json')['snapshots'].items():
        assert sha(RUN / 'source_before' / name) == digest, name
    docs = [ROOT / x for x in ['summary.md', 'spec.md', 's-target.md', 's-experiment.md',
            'LOCAL_CODEX_START.md', 'experiment_history/README.md',
            'experiment_history/200_multimodal_four_method_retest_v1.md']]
    docs += [RUN / 'README.md', OUT / 'report_zh.md']
    sync = read(RUN / 'reviews/document_sync.json')
    assert sync['status'] == 'PASS_CURRENT_VIEWS_REVIEWED'
    assert set(sync['files']) == set(map(str, docs))
    link_count = 0
    for p in docs:
        assert sha(p) == sync['files'][str(p)], str(p)
        for target in re.findall(r'\]\(([^)]+)\)', p.read_text()):
            target = unquote(target.split('#', 1)[0].strip('<>'))
            if not target or '://' in target or target.startswith('mailto:'):
                continue
            assert (p.parent / target).exists(), (str(p), target)
            link_count += 1
    assert not list(RUN.rglob('*.pdf')), 'No PDF was requested'
    seen = set()
    allocated_bytes = 0
    for directory, _, names in os.walk(RUN):
        for name in names:
            s = (Path(directory) / name).stat()
            key = (s.st_dev, s.st_ino)
            if key not in seen:
                seen.add(key)
                allocated_bytes += s.st_blocks * 512
    assert allocated_bytes <= lock['storage_new_budget_GiB'] * 1024**3
    disk = os.statvfs(RUN)
    assert disk.f_bfree * disk.f_frsize >= lock['storage_free_floor_GiB'] * 1024**3
    result = {
        'status': 'PASS_E200_FULL_LOCAL_DELIVERY', 'points': 640, 'rounds': 1280,
        'formal_queries': 11200000, 'datasets': lock['datasets'], 'methods': lock['methods'],
        'budgets_per_K': 20, 'actual_render_reviewed': True, 'report_reviewed': True,
        'frozen_files_full_sha_verified': len(frozen['files']), 'document_links_checked': link_count,
        'default_changed': False, 'seconds': time.time() - started,
        'new_artifact_unique_allocated_bytes': allocated_bytes,
        'postprocessing_source_sha256': {str(p.relative_to(RUN)): sha(p)
             for p in sorted((RUN / 'scripts').rglob('*.py'))},
        'evidence': {str(p.relative_to(RUN)): sha(p) for p in [
            RUN / 'formal_freeze.json', RUN / 'reviews/qualification.json',
            RUN / 'reviews/measurement_complete.json', OUT / 'independent_audit.json',
            OUT / 'visual_review.json', OUT / 'report_review.json',
            RUN / 'reviews/document_sync.json', OUT / 'points.csv', OUT / 'rounds.csv']},
    }
    path = RUN / 'reviews/delivery_validation.json'
    with path.open('x') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
