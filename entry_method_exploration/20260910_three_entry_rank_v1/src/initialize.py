#!/usr/bin/env python3
import shutil
import time
from common import DATASETS, OLD, ROOT, RUN, dump, identity, read, sha

assert not (RUN / 'source_before').exists(), 'refuse reinitialization'
for name in ['source_before', 'inputs', 'labels', 'models', 'diagnostics', 'results', 'logs', 'bin', 'reviews']:
    (RUN / name).mkdir(exist_ok=True)
paths = ['AGENTS.md', 'summary.md', 'spec.md', 's-target.md', 's-experiment.md',
         'experiment_history/11_ab_fixed_slot_exploration.md',
         'entry_method_exploration/20260910_optimizer_research_v1/report.md']
paths += [str((OLD / 'src' / name).relative_to(ROOT))
          for name in ['legacy_reference.cpp', 'benchmark_with_nsg.cpp', 'train.py']]
paths += [x['path'] for x in read(OLD / 'reviews/linked_sources_verified.json')]
protected = []
for name in dict.fromkeys(paths):
    p = ROOT / name
    info = identity(p)
    relative = p.relative_to(ROOT)
    if p.suffix != '.a':
        dest = RUN / 'source_before' / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, dest)
    protected.append(info)
dump(RUN / 'reviews/protected_before.json', protected)
for name in ['legacy_reference.cpp', 'benchmark_with_nsg.cpp']:
    shutil.copyfile(OLD / 'src' / name, RUN / 'src' / name)
shutil.copyfile(OLD / 'exploration_5point_v1/src/quick.cpp', RUN / 'src/evaluate.cpp')
verified = []
started = time.monotonic()
for item in read(OLD / 'reviews/linked_sources_verified.json'):
    now = identity(item['path']); assert now['sha256'] == item['sha256'], item['path']
    verified.append(now)
for dataset in DATASETS:
    for item in read(OLD / 'inputs' / dataset / 'verified_sources.json').values():
        now = identity(item['path']); assert now['sha256'] == item['sha256'], item['path']
        verified.append(now)
    for name in ['queries.f32', 'gt.i64', 'row_ids.i64', 'runner_config.json',
                 'seed20260828/config.json', 'seed20260828/hub_ids.i32',
                 'seed20260828/prototype.f32', 'seed20260828/union_columns.i32']:
        verified.append(identity(OLD / 'inputs' / dataset / name))
    for name in ['hitcount.u8', 'ndc.u32']:
        verified.append(identity(OLD / 'labels' / dataset / 'L128' / name))
dump(RUN / 'inputs/preflight.json', {'status': 'PASS', 'seconds': time.monotonic()-started,
                                    'files': verified, 'validation_opened': False, 'heldout_opened': False})
dump(RUN / 'config.locked.json', {'protocol_sha256': sha(RUN / 'protocol.md'),
    'seed': 20260828, 'label_L': 128, 'rank': 8, 'regularization': [0.1, 1.0, 10.0],
    'fit_queries': 20000, 'cal_queries': 1024, 'audit_queries': 1024, 'fit_diagnostic_queries': 1024,
    'contexts': 4, 'options': 6, 'label_call_cap_per_dataset': 480000,
    'label_threads': 16, 'train_threads': 16, 'query_threads': 1,
    'optimizer': {'name': 'LBFGS', 'max_iter': 300, 'max_eval': 375, 'history_size': 50,
                  'tolerance_grad': 1e-9, 'tolerance_change': 1e-12, 'line_search_fn': 'strong_wolfe'},
    'validation_queries': 2000, 'L': [64, 128, 256, 400, 800], 'timing_repeats': 1})
dump(RUN / 'state.json', {'status': 'PREFLIGHT_COMPLETE_IMPLEMENTING', 'user_authorization': '推进一下这个方案试试',
                         'protocol_sha256': sha(RUN / 'protocol.md'), 'new_search_calls': 0})
print('PREFLIGHT_COMPLETE', flush=True)
