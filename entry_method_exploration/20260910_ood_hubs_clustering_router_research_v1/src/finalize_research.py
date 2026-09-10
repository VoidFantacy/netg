#!/usr/bin/env python3
"""Audit a research delivery; reads small existing artifacts, never experimental data."""
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[1]
DOCS = ['summary.md', 'spec.md', 's-target.md', 's-experiment.md',
        'experiment_history/README.md', 'experiment_history/09_research_designs_not_experiments.md']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')


def identity(path):
    return {'path': str(path.relative_to(ROOT)), 'bytes': path.stat().st_size, 'sha256': digest(path)}


before = json.loads((RUN/'local_source_manifest.json').read_text())
unchanged = []
modified_docs = []
for row in before:
    p = ROOT/row['path']
    assert digest(RUN/'source_before'/row['path']) == row['sha256'], row['path']
    if row['path'] in DOCS:
        modified_docs.append(identity(p))
    else:
        assert digest(p) == row['sha256'], ('protected source changed', row['path'])
        unchanged.append(identity(p))

evidence = json.loads((RUN/'local_evidence.json').read_text())
for rel, item in evidence['consumed_aggregate_files'].items():
    assert digest(ROOT/rel) == item['sha256'], rel
assert evidence['new_searches'] == evidence['new_labels'] == evidence['new_model_fits'] == 0
assert evidence['raw_validation_or_heldout_opened'] is False
assert len(evidence['datasets']) == 2
for ds, item in evidence['datasets'].items():
    qgt = item['qgt']
    assert qgt['gt_candidates_per_query'] == 100 and qgt['kmeans_iterations'] == 25
    assert qgt['empty_clusters'] == 0 and qgt['seed'] == 20260828
    assert item['prototype20k']['train_queries'] == 20000
    assert item['prototype30k']['train_queries'] == 30000
    audit = item['e23_selected_diagnostics']['audit']
    assert len(audit) == 6 and all(x['qps'] is None and x['queries'] == 1024 for x in audit)
    for family in ['fast20k_3', 'full', 'rank8']:
        pair = [x for x in audit if x['family'] == family]
        assert len(pair) == 2
    metrics = item['e23_existing_validation_metrics']
    for L in [64,128,256,400,800]:
        rows = {x['family']: x for x in metrics if x['L'] == L}
        assert len(rows) == 5
        if ds.startswith('yandex'):
            assert rows['rank8']['recall_at_10'] > rows['full']['recall_at_10']

sources = json.loads((RUN/'sources/manifest.json').read_text())
sources += json.loads((RUN/'sources/addendum.json').read_text())
assert len(sources) == 15  # Neural LSH is archived as both PDF and HTML.
assert len({x['id'].replace('neural_lsh_html','neural_lsh') for x in sources}) == 14
for row in sources:
    assert digest(RUN/row['path']) == row['sha256'], row['id']
assert next(x for x in sources if x['id'] == 'quodar_abstract')['status'] == 'CHALLENGE_BODY_NOT_PAPER'

docs = [ROOT/x for x in DOCS] + [RUN/x for x in ['README.md','report.md','papers.md']]
links = []
for p in docs:
    content = p.read_text()
    assert '\x00' not in content and content.count('```') % 2 == 0
    for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', content):
        if re.match(r'^[a-z]+://',target) or target.startswith('#'):
            continue
        dst = (p.parent/target.split('#')[0]).resolve()
        if dst != RUN/'reviews/final_audit.json':
            assert dst.exists(), (str(p), target)
        links.append({'document': str(p.relative_to(ROOT)), 'target': target})

report = (RUN/'report.md').read_text()
for phrase in ['问题一', '问题二', '问题三', '问题四', 'A⁻ᵀq', 'GT-topK', 'rank8', '冻结NSG']:
    assert phrase in report, phrase
for p in [ROOT/'summary.md',ROOT/'s-target.md',ROOT/'s-experiment.md',RUN/'report.md']:
    assert 'RESEARCH_COMPLETE_METHOD_UNSELECTED_UNRUN' in p.read_text(), str(p)
assert 'EXPLORATORY_SMALL_RECALL_SIGNAL_NO_CLEAR_QPS_GAIN' in (ROOT/'summary.md').read_text()

stamp = datetime.now(timezone.utc).isoformat()
audit = {
    'status': 'PASS', 'completed_utc': stamp,
    'scope': 'Research delivery/source preservation/local links/existing aggregate consistency; no method performance verification.',
    'requirements': {
        'Q1_GT1_and_connectivity': 'Report section 2 distinguishes two GT1 roles; source lines 144-240 plus manifests; finite-beam/degree limits and E20 source evidence.',
        'Q2_OOD_clustering': 'Section 3 distinguishes query/base OOD, query clustering, target proxy and three approaches; vMF/LIRA/Neural LSH/SOAR sources and local support counts.',
        'Q3_rank8_optimality': 'Section 4 plus E23 source/behavior: preset rank8 versus Full only, same-lambda objective results, singular energy limits; no rank sweep claimed.',
        'Q4_OOD_HNSW_stretch': 'Section 5 separates micro-HNSW and NSG, exact-score versus search utility; paired inverse-transpose derivation, rebuild necessity, cost and normalization boundaries; LeanVec-Sphering primary source.',
        'recommendation_and_scope': 'Three directions, priority, prior-method distinction, bounded falsification logic and all-unrun status; no new experiment protocol or GO.',
        'handoff': 'Four root documents and history index/card synchronized while retaining E23 as last executed experiment.'
    },
    'source_snapshots_verified': len(before),
    'protected_source_and_old_artifacts_unchanged': unchanged,
    'existing_aggregate_files_verified': evidence['consumed_aggregate_files'],
    'large_graphs_and_raw_data': 'No large base/graph/raw split opened or written by this research; no fresh full-file hash claim.',
    'source_downloads_checked': len(sources), 'independent_papers': 14,
    'source_access_limits': 'Quodar abstract only, downloaded challenge body excluded; partition-tree paper abstract/assumptions screening only.',
    'local_links_checked': len(links), 'local_links': links,
    'document_identities': [identity(p) for p in docs],
    'new_experiments': 0, 'performance_go': False,
}
dump(RUN/'reviews/final_audit.json',audit)
dump(RUN/'state.json', {
    'status': 'RESEARCH_COMPLETE_METHOD_UNSELECTED_UNRUN', 'completed_utc': stamp,
    'report': 'report.md', 'papers': 'papers.md', 'local_evidence': 'local_evidence.json',
    'final_audit': 'reviews/final_audit.json', 'method_selected': False,
    'new_searches': 0, 'new_labels': 0, 'new_model_fits': 0, 'new_ann_builds': 0,
    'raw_validation_or_heldout_opened': False, 'performance_go': False,
})
files = [p for p in sorted(RUN.rglob('*')) if p.is_file() and p.name != 'delivery_manifest.json' and '__pycache__' not in p.parts]
dump(RUN/'delivery_manifest.json', {'status': 'COMPLETE', 'files': [identity(p) for p in files], 'root_documents': modified_docs})
print(json.dumps({'status':'PASS','local_links':len(links),'preserved_files':len(unchanged),'source_archives':len(sources),'delivery_files':len(files)}))
