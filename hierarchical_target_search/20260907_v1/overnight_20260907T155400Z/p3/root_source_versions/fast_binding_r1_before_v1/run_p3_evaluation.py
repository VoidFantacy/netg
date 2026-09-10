#!/usr/bin/env python3
"""Run the preregistered four P3 models on one pilot, as one supervised heavy job."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path('/data/netg/ACSG')
RUN = Path(__file__).resolve().parents[1]
MODELS = ('lambda0_frequency3', 'lambda1_frequency3', 'lambda0_greedy3', 'lambda1_greedy3')
SOFT_CLOSE = dt.datetime(2026, 9, 7, 22, 59, tzinfo=dt.timezone.utc).timestamp()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def bound(path):
    return {'path': str(Path(path).resolve()), 'sha256': sha(path)}


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dataset', choices=['webvid2_5m_light_v1', 'yandex_t2i_official10M_ip_v1'], required=True)
    p.add_argument('--models', type=Path, required=True, help='Contains lambda0/frequency3/model.json etc.')
    p.add_argument('--fast-manifest', type=Path, required=True)
    p.add_argument('--audit', type=Path, required=True)
    p.add_argument('--p1-gate', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--evaluator', type=Path, default=ROOT/'build/benches/bench_hierarchical_eval_p3')
    a = p.parse_args()
    require(time.time() < SOFT_CLOSE, 'Research soft deadline closed')
    protocol_path = RUN/'p3/protocol.json'; protocol = read(protocol_path)
    require(protocol['evaluation']['models'] == list(MODELS), 'Model family or order changed')
    require(protocol['evaluation']['methods'] == ['fast', 'oracle_unified', 'oracle_probability'], 'Method family changed')
    require(read(RUN/'gates/P2.json')['status'] == 'PASS', 'P2 PASS required')
    gate = read(a.p1_gate)
    require(gate['status'] == 'PASS' and gate['stage'] == 'P1_P3_REACCEPTANCE', 'New P3 P1 acceptance required')
    source = ROOT/'benches/bench_hierarchical_eval_p3.cpp'
    binary_sha, source_sha = sha(a.evaluator), sha(source)
    require(gate['evaluator_binary_sha256'] == binary_sha and gate['evaluator_source_sha256'] == source_sha,
            'Evaluator differs from accepted version')
    require(gate['protocol_sha256'] == sha(protocol_path), 'P1 acceptance bound to another P3 protocol')
    audit, fast = read(a.audit), read(a.fast_manifest)
    ds = next(x for x in audit['datasets'] if x['dataset'] == a.dataset)
    require(audit['status'] == 'PASS_INPUT_CONTRACT' and fast['status'] == 'COMPLETE' and
            fast['dataset'] == a.dataset and fast['fit_queries'] == 20000 and fast['pilot_queries_used'] == 0,
            'Audited inputs and paired20K Fast required')
    require(fast['fit_query_values_sha256'] == ds['fit']['query_values_sha256'] and
            fast['fit_gt_values_sha256'] == ds['fit']['gt_values_sha256'], 'Fast fit differs from P0')
    model_paths, model_data = {}, {}
    for name in MODELS:
        branch, rule = name.split('_', 1)
        path = a.models/branch/rule/'model.json'; model = read(path)
        require(model['status'] == 'COMPLETE' and model['stage'] == 'P3' and model['schema_version'] == 2 and
                model['dataset'] == a.dataset and model['lambda'] == int(branch[-1]) and model['portal_rule'] == rule,
                'Wrong model identity: ' + name)
        require(model['oracle_diagnostic_only'] is True and model['region_count'] == 256 and
                model['portals_per_region'] == 3 and model['fit_range'] == [10000, 30000], 'Model shape/split mismatch')
        require(model['fit_query_values_sha256'] == fast['fit_query_values_sha256'] and
                model['fit_gt_values_sha256'] == fast['fit_gt_values_sha256'], 'Model and Fast fit differ')
        require(model['input_audit_sha256'] == sha(a.audit) and model['protocol_sha256'] == sha(protocol_path) and
                model['graph_sha256'] == ds['graph']['sha256'], 'Model audit/protocol/graph mismatch')
        for kind in ('labels', 'portals'):
            require(sha(model[kind+'_file']) == model[kind+'_sha256'], 'Model raw file changed')
        model_paths[name], model_data[name] = path.resolve(), model
    for branch in ('lambda0', 'lambda1'):
        require(model_data[branch+'_frequency3']['labels_sha256'] == model_data[branch+'_greedy3']['labels_sha256'],
                'Portal comparison changes region labels')
    a.output.mkdir(parents=True, exist_ok=False)
    record = {'schema_version': 1, 'stage': 'P3', 'status': 'INCOMPLETE', 'dataset': a.dataset,
              'started_utc': now(), 'cpu_only': True, 'heldout_accessed': False, 'validation_accessed': False,
              'scope': 'Fixed 2x2 oracle-only structure/portal development diagnosis, not a deployment frontier',
              'protocol': bound(protocol_path), 'p1_gate': bound(a.p1_gate), 'audit': bound(a.audit),
              'fast_manifest': bound(a.fast_manifest), 'models': {k: bound(v) for k, v in model_paths.items()},
              'source': bound(source), 'binary': bound(a.evaluator), 'runner': bound(__file__),
              'method_order': ['fast', 'oracle_unified', 'oracle_probability'], 'model_order': list(MODELS),
              'timing_scope': 'AB/BA within each model; between-model fixed order, wall comparisons descriptive',
              'thread_environment': {k: os.environ.get(k) for k in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS']},
              'invocations': []}

    def save():
        temp = a.output/'execution.tmp.json'
        temp.write_text(json.dumps(record, indent=2)+'\n'); temp.replace(a.output/'execution.json')

    save()
    try:
        for name in MODELS:
            directory = a.output/name; directory.mkdir(exist_ok=False)
            for measurement, rounds in [('count', 1), ('timing', 5)]:
                require(time.time() < SOFT_CLOSE, 'Soft deadline between P3 cells')
                require(sha(source) == source_sha and sha(a.evaluator) == binary_sha, 'Evaluator changed between cells')
                require(sha(model_paths[name]) == record['models'][name]['sha256'], 'Model changed between cells')
                out = (directory/(measurement+'.json')).resolve()
                command = [str(a.evaluator.resolve()), '--stage', 'P3', '--split', 'pilot', '--measurement', measurement,
                           '--rounds', str(rounds), '--dataset', a.dataset, '--index-file', ds['graph']['path'],
                           '--model', str(model_paths[name]), '--fast-hubs', fast['hubs_file'], '--fast-ids', fast['ids_file'],
                           '--fast-m', '3', '--search-ls', '64,128', '--top-k', '10', '--query-offset', '0',
                           '--hnsw-seed', '100', '--methods', 'fast,oracle_unified,oracle_probability',
                           '--max-queries', '10000', '--threads', '16', '--warmup-queries', '128', '--output', str(out)]
                item = {'model': name, 'measurement': measurement, 'status': 'RUNNING', 'started_utc': now(), 'command': command}
                record['invocations'].append(item); save(); print('P3_BEGIN', a.dataset, name, measurement, flush=True)
                with (directory/(measurement+'.log')).open('xb') as log:
                    child = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
                    item.update(pid=child.pid, pgid=os.getpgid(child.pid)); save(); item['returncode'] = child.wait()
                item.update(status='COMPLETE' if item['returncode'] == 0 else 'FAILED', ended_utc=now()); save()
                require(item['returncode'] == 0, 'P3 cell failed; keep partial output and log')
                require(read(out)['status'] == 'COMPLETE', 'Evaluator did not mark output complete')
                item['output'] = bound(out); save(); print('P3_DONE', a.dataset, name, measurement, flush=True)
        record['status'] = 'COMPLETE_DATASET_MEASUREMENTS'
    except BaseException as error:
        record['error'] = repr(error)
        raise
    finally:
        record['ended_utc'] = now(); save()
    print(json.dumps({'status': record['status'], 'execution': str(a.output/'execution.json')}), flush=True)


if __name__ == '__main__':
    main()
