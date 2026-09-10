#!/usr/bin/env python3
"""Complete only the seven original P2 trace IDs missing from the first16 batch."""
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
SOFT_CLOSE = dt.datetime(2026, 9, 7, 22, 59, tzinfo=dt.timezone.utc).timestamp()
FIELDS = ('query_id', 'recall', 'result_ids', 'entry_ids', 'fast_anchor_id', 'shared_seed',
          'actual_entry_count', 'regions', 'weights', 'routing_ndc', 'graph_ndc', 'total_ndc',
          'routing_mac', 'graph_mac', 'total_mac', 'expanded', 'rejected', 'evicted_unexpanded')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def bound(path):
    return {'path': str(Path(path).resolve()), 'sha256': sha(path)}


def verify(binding):
    require(sha(binding['path']) == binding['sha256'], 'Frozen input changed: '+binding['path'])


def command_for(template, qid, output):
    command = list(template)
    require(len(command[1:]) % 2 == 0 and len(set(command[1::2])) == len(command[1::2]), 'Malformed frozen command')
    for key, value in {'--query-offset': str(qid), '--max-queries': '1', '--warmup-queries': '1',
                       '--output': str(output.resolve())}.items():
        require(key in command, 'Missing original command flag')
        command[command.index(key)+1] = value
    return command


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(time.time() < SOFT_CLOSE, 'Trace completion soft deadline closed')
    protocol = read(args.protocol)
    for key in ('parent_protocol', 'original_analysis', 'original_trace_analysis', 'P3_negative_gate'):
        verify(protocol[key])
    parent = read(protocol['parent_protocol']['path'])
    require(protocol['query_ids'] == parent['p2_preregistered']['trace_query_ids'][16:] ==
            [157, 631, 2003, 4093, 6007, 8009, 9967], 'Only original remaining seven trace IDs allowed')
    require(read(protocol['P3_negative_gate']['path'])['status'] == 'NOPASS', 'This completion must preserve P3 NOPASS')
    binary, source = ROOT/'build/benches/bench_hierarchical_eval', ROOT/'benches/bench_hierarchical_eval.cpp'
    require(sha(binary) == protocol['evaluator_binary_sha256'] and sha(source) == protocol['evaluator_source_sha256'],
            'P2 frozen evaluator source/binary changed')
    analysis = read(protocol['original_analysis']['path'])
    require(analysis['status'] == 'COMPLETE', 'Original full pilot analysis incomplete')
    args.output.mkdir(parents=True, exist_ok=False)
    record = {'status': 'INCOMPLETE', 'stage': 'P2_TRACE_COMPLETION', 'protocol': bound(args.protocol),
              'source': bound(__file__), 'binary': bound(binary), 'evaluator_source': bound(source),
              'started_utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'invocations': [],
              'cpu_only': True, 'validation_accessed': False, 'heldout_accessed': False,
              'new_performance_or_method_gate': False, 'matched_original_count_rows': 0, 'datasets': []}

    def save():
        temporary = args.output/'execution.tmp.json'
        temporary.write_text(json.dumps(record, indent=2)+'\n'); temporary.replace(args.output/'execution.json')

    save()
    try:
        for dataset, alias in zip(protocol['datasets'], ('webvid', 'yandex')):
            ds = next(x for x in analysis['datasets'] if x['dataset'] == dataset)
            evidence = ds['evidence']
            for key in ('count', 'model', 'paired_fast20k'):
                verify(evidence[key])
            for binding in evidence['model_files'].values():
                verify(binding)
            original_path = RUN/'p2'/(alias+'_eval')/'execution.json'
            original = read(original_path)
            require(original['status'] == 'COMPLETE_DATASET_MEASUREMENTS' and original['dataset'] == dataset and
                    original['actual_trace_query_ids'] == list(range(16)), 'Original trace subset changed')
            require(original['model_sha256'] == evidence['model']['sha256'] and
                    original['fast_manifest_sha256'] == evidence['paired_fast20k']['sha256'], 'Original model/Fast binding differs')
            template = next(x['command'] for x in original['invocations'] if x['name'] == 'trace')
            flags = dict(zip(template[1::2], template[2::2]))
            for key, value in {'--stage': 'P2', '--split': 'pilot', '--dataset': dataset, '--measurement': 'trace',
                               '--rounds': '1', '--threads': '1', '--search-ls': '64,128', '--top-k': '10',
                               '--fast-m': '3', '--hnsw-seed': '100', '--methods': ','.join(protocol['methods'])}.items():
                require(flags[key] == value, 'Original trace command differs: '+key)
            fast = read(evidence['paired_fast20k']['path'])
            fast_raw = [bound(fast[k+'_file']) for k in ('hubs', 'ids')]
            require(fast_raw[0]['sha256'] == fast['hubs_sha256'] and fast_raw[1]['sha256'] == fast['ids_sha256'], 'Frozen Fast raw files changed')
            require(flags['--fast-hubs'] == fast_raw[0]['path'] and flags['--fast-ids'] == fast_raw[1]['path'] and
                    flags['--model'] == evidence['model']['path'] and Path(template[0]).resolve() == binary,
                    'Original trace command paths differ from frozen files')
            counted = read(evidence['count']['path'])
            reference = {(x['method'], x['search_L']): {q['query_id']: q for q in x['per_query']} for x in counted['results']}
            directory = args.output/dataset; directory.mkdir()
            ds_record = {'dataset': dataset, 'original_execution': bound(original_path), 'original_evidence': evidence,
                         'fast_raw': fast_raw, 'query_ids': protocol['query_ids'], 'outputs': []}
            record['datasets'].append(ds_record); save()
            for qid in protocol['query_ids']:
                require(time.time() < SOFT_CLOSE, 'Soft deadline between original trace IDs')
                for binding in (record['binary'], record['evaluator_source'], record['protocol'], evidence['model'],
                                evidence['paired_fast20k'], *fast_raw, *evidence['model_files'].values()):
                    verify(binding)
                output = directory/f'q{qid}.json'
                command = command_for(template, qid, output)
                item = {'dataset': dataset, 'query_id': qid, 'status': 'RUNNING', 'command': command,
                        'started_utc': dt.datetime.now(dt.timezone.utc).isoformat()}
                record['invocations'].append(item); save(); print('TRACE_COMPLETION_BEGIN', dataset, qid, flush=True)
                started = time.perf_counter()
                with (directory/f'q{qid}.log').open('xb') as log:
                    child = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
                    item.update(pid=child.pid, pgid=os.getpgid(child.pid)); save(); item['returncode'] = child.wait()
                item.update(status='COMPLETE' if item['returncode'] == 0 else 'FAILED', wall_seconds=time.perf_counter()-started); save()
                require(item['returncode'] == 0, 'Trace completion failed; preserve partial output')
                result = read(output)
                require(result['status'] == 'COMPLETE' and result['dataset'] == dataset and result['measurement'] == 'trace' and
                        result['source_query_range'] == [qid, qid+1] and result['num_queries'] == 1 and
                        result['model_manifest'] == read(evidence['model']['path']), 'Completed trace metadata differs')
                expected = {(m, l) for m in protocol['methods'] for l in protocol['Ls']}
                require({(x['method'], x['search_L']) for x in result['results']} == expected and len(result['results']) == 10,
                        'Trace missing one fixed method/L')
                for cell in result['results']:
                    require(cell['round'] == 0 and len(cell['per_query']) == len(cell['trace_files']) == 1, 'Invalid single-query trace batch')
                    row, old = cell['per_query'][0], reference[(cell['method'], cell['search_L'])][qid]
                    require(all(row[k] == old[k] for k in FIELDS), 'Trace differs from original full10K count row')
                    record['matched_original_count_rows'] += 1
                item['output'] = bound(output); ds_record['outputs'].append(bound(output)); save()
                print('TRACE_COMPLETION_DONE', dataset, qid, item['wall_seconds'], flush=True)
            del reference, counted
        require(record['matched_original_count_rows'] == protocol['expected_new_trace_files'] == 140, 'Incomplete fixed trace coverage')
        record['status'] = 'COMPLETE'
        record['P2_and_P3_gates_unchanged'] = True
    except BaseException as error:
        record['error'] = repr(error)
        raise
    finally:
        record['ended_utc'] = dt.datetime.now(dt.timezone.utc).isoformat(); save()


if __name__ == '__main__':
    main()
