#!/usr/bin/env python3
"""Small rejection-boundary audit; never loads datasets or starts an ANN experiment."""
import hashlib
import json
import argparse
from pathlib import Path
import subprocess

ROOT = Path('/data/netg/ACSG')
RUN = ROOT / 'hierarchical_target_search/20260907_v1/overnight_20260907T155400Z'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output-dir', type=Path, default=RUN / 'p1/evaluator_cli_audit')
DEST = parser.parse_args().output_dir
DEST.mkdir(exist_ok=False)
BIN = ROOT / 'build/benches/bench_hierarchical_eval'
base = ['--stage', 'P1', '--split', 'pilot', '--measurement', 'count', '--rounds', '1', '--output', str(DEST / 'never_created.json'), '--methods', 'fast']

def replace(args, key, value):
    args = list(args)
    if key in args:
        args[args.index(key)+1] = str(value)
    else:
        args += [key, str(value)]
    return args

cases = [
    ('missing_stage', replace(base, '--stage', ''), 'explicit --stage'),
    ('missing_split', replace(base, '--split', ''), 'explicit --split'),
    ('missing_measurement', replace(base, '--measurement', ''), 'explicit --measurement'),
    ('k_above_l', replace(replace(base, '--top-k', 100), '--search-ls', 64), 'K > L'),
    ('early_heldout', replace(base, '--split', 'heldout'), 'heldout requires stage'),
    ('missing_p6_gate', replace(replace(base, '--split', 'heldout'), '--stage', 'P7'), 'heldout requires --p6-gate'),
    ('oracle_validation', replace(replace(base, '--methods', 'oracle_unified'), '--split', 'validation'), 'oracle is train-development-only'),
    ('legacy_top4', replace(base, '--fast-m', 4), 'legacy Fast consumes three'),
    ('four_timing_rounds', replace(replace(base, '--measurement', 'timing'), '--rounds', 4), 'requires five'),
    ('trace_over_budget', replace(replace(base, '--measurement', 'trace'), '--max-queries', 33), 'trace requires max-queries'),
]
marker = DEST / 'existing.txt'
marker.write_text('PROTECTED\n')
cases.append(('output_collision', replace(base, '--output', marker), 'must name a new file'))
results = []
for name, args, expected in cases:
    proc = subprocess.run([str(BIN), *args], cwd=ROOT, capture_output=True, text=True, timeout=10)
    passed = proc.returncode == 2 and expected in proc.stderr and 'Loading' not in proc.stdout
    results.append(dict(name=name, command=[str(BIN), *args], returncode=proc.returncode,
                        stdout=proc.stdout, stderr=proc.stderr, expected=expected, passed=passed))
assert marker.read_text() == 'PROTECTED\n'
assert not (DEST / 'never_created.json').exists()
assert not (DEST / 'never_created.json.parts').exists()
paths = ['benches/bench_hierarchical_eval.cpp', 'ACSG/RegionalSearch.h', 'build/benches/bench_hierarchical_eval']
hashes = {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths}
report = dict(status='PASS' if all(x['passed'] for x in results) else 'FAIL',
              checks=results, protected_marker_unchanged=True, datasets_loaded=False,
              source_and_binary_sha256=hashes)
(DEST / 'report.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps({'status': report['status'], 'checks': len(results), 'report': str(DEST/'report.json')}))
assert report['status'] == 'PASS'
