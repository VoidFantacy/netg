#!/usr/bin/env python3
"""Run the locked n16 qualification after FIT/build/static review, before formal.

Only serialized native return/trace words are compared with E175 prefixes. This
script never opens ground-truth vectors/IDs or computes Recall, QPS comparisons,
distances, bootstrap, fitting or new model selection. Children run serially.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT.parent / '20261010_m5_region_budget_curve_v1'
DATASETS = ('webvid2_5m_light_v1', 'yandex_t2i_official10M_ip_v1')
METHODS = ('NSG', 'GT', 'M5', 'M5OPT', 'M5REG96', 'REGOPT96', 'WIDE12', 'M5RES12')
OLD_METHODS = ('NSG', 'GT', 'M5', 'M5REG96')
KS = (1, 100)
LS = (200, 400, 800, 1000, 1200)
SOURCES = ('native.hpp', 'runtime.hpp', 'region.hpp', 'optimized.hpp', 'residual.hpp', 'benchmark.cpp')
ENV = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1',
           NUMEXPR_NUM_THREADS='1', OMP_DYNAMIC='FALSE')


def load(path):
    return json.loads(Path(path).read_text())


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def stat4(path):
    s = Path(path).stat()
    return [s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns]


def write(path, value, exclusive=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if exclusive:
        with path.open('x') as f:
            json.dump(value, f, indent=2, allow_nan=False)
            f.write('\n')
    else:
        tmp = path.with_suffix(path.suffix + '.tmp')
        tmp.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
        tmp.replace(path)


def unchanged(expected):
    for path, before in expected.items():
        if stat4(path) != before:
            raise RuntimeError('protected input changed: ' + path)


def resource_guard():
    st = os.statvfs(ROOT)
    if st.f_bavail * st.f_frsize < 1073741824:
        raise RuntimeError('qualification 1GiB free-space reserve')
    total = sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file())
    if total > 1610612736:
        raise RuntimeError('qualification campaign 1536MiB artifact cap; partial preserved')
    return total


def check_prefix(new, old, new_bytes, old_bytes, evidence):
    new, old = Path(new), Path(old)
    old_before = stat4(old)
    new_before = stat4(new)
    if new_before[2] != new_bytes or old_before[2] != old_bytes:
        raise ValueError('native serialized word file size: ' + str(new))
    a = new.read_bytes()
    with old.open('rb') as f:
        b = f.read(new_bytes)
    if len(a) != new_bytes or a != b:
        raise ValueError('frozen original native prefix differs: ' + str(new))
    if stat4(old) != old_before or stat4(new) != new_before:
        raise RuntimeError('word identity changed while comparing')
    evidence.append({'new': str(new), 'old': str(old), 'bytes_compared': new_bytes,
                     'new_stat4': new_before, 'old_stat4': old_before,
                     'prefix_sha256': hashlib.sha256(a).hexdigest(), 'bytes_equal': True})


def run_child(binary, job_path, config, state, state_path, protected, timeout_seconds):
    log = ROOT / 'logs' / ('qualification.' + config['dataset'] + '.log')
    log.parent.mkdir(exist_ok=True)
    if log.exists() or Path(config['out']).exists():
        raise FileExistsError('preserve qualification log/output')
    argv = [str(binary), str(job_path)]
    begun = time.monotonic()
    receipt = {'dataset': config['dataset'], 'argv': argv, 'log': str(log),
               'job_sha256': sha(job_path), 'timeout_seconds': timeout_seconds,
               'exit_code': None, 'max_threads_observed': None, 'peak_rss_bytes_observed': None,
               'rss_scope': 'sampled /proc VmRSS at ~0.25s, not exact peak'}
    proc = None
    error = None
    try:
        with log.open('x') as f:
            proc = subprocess.Popen(argv, env=ENV, stdout=f, stderr=subprocess.STDOUT,
                                    preexec_fn=lambda: os.sched_setaffinity(0, {15}))
            state['active'] = {'dataset': config['dataset'], 'pid': proc.pid, 'argv': argv}
            write(state_path, state)
            last_resources = time.monotonic()
            try:
                while proc.poll() is None:
                    if time.monotonic() - begun > timeout_seconds:
                        raise TimeoutError('qualification child cap exceeded; partial preserved')
                    try:
                        fields = dict(line.split(':', 1) for line in Path(f'/proc/{proc.pid}/status').read_text().splitlines() if ':' in line)
                        if 'Threads' in fields and 'VmRSS' in fields:
                            threads = int(fields['Threads'])
                            rss = int(fields['VmRSS'].split()[0]) * 1024
                            receipt['max_threads_observed'] = max(receipt['max_threads_observed'] or 0, threads)
                            receipt['peak_rss_bytes_observed'] = max(receipt['peak_rss_bytes_observed'] or 0, rss)
                            if threads != 1 or os.sched_getaffinity(proc.pid) != {15}:
                                raise RuntimeError('actual qualification thread/CPU violation')
                            if rss > config['maxrss_bytes']:
                                raise MemoryError('actual qualification RSS cap')
                    except (FileNotFoundError, ProcessLookupError):
                        pass
                    if time.monotonic() - last_resources > 5:
                        resource_guard()
                        unchanged(protected)
                        last_resources = time.monotonic()
                    time.sleep(.25)
                proc.wait()
            finally:
                # Only terminate this owned child. Wait/kill/wait finishes even
                # when persistence fails; no old runner/process is touched.
                if proc.poll() is None:
                    proc.terminate()
                    try:
                        proc.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        proc.wait()
                    receipt['owned_child_cleanup'] = {'pid': proc.pid, 'returncode': proc.returncode,
                                                       'terminated_then_waited': True, 'partial_preserved': True}
                else:
                    proc.wait()
                receipt['exit_code'] = proc.returncode
                state['active'] = None
    except BaseException as e:
        error = e
    finally:
        # Handles a failure immediately after Popen, before the inner monitor's
        # finally is entered (e.g. state write failed). Preserve the primary error.
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
            receipt['owned_child_cleanup'] = {'pid': proc.pid, 'returncode': proc.returncode,
                                               'terminated_then_waited': True, 'partial_preserved': True}
        if proc is not None:
            proc.wait()
            receipt['exit_code'] = proc.returncode
        state['active'] = None
        receipt['elapsed_seconds'] = time.monotonic() - begun
        if error is not None:
            receipt['error'] = repr(error)
        state['jobs'].append(receipt)
        try:
            write(state_path, state)
        except BaseException as persistence_error:
            receipt['persistence_error'] = repr(persistence_error)
            if error is None:
                error = persistence_error
    if error is not None:
        raise error
    if receipt['exit_code'] != 0:
        raise RuntimeError('qualification child exit !=0; partial preserved: ' + str(log))
    unchanged(protected)
    resource_guard()
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-receipt', type=Path, default=ROOT / 'reviews/build.json')
    parser.add_argument('--source-review', type=Path, default=ROOT / 'reviews/benchmark_source_review.json')
    parser.add_argument('--timeout-seconds', type=float, default=10800)
    args = parser.parse_args()
    if not 0 < args.timeout_seconds <= 10800:
        raise ValueError('qualification timeout must not exceed the frozen query job cap')
    os.sched_setaffinity(0, {14})
    started = time.monotonic()
    state_path = ROOT / 'qualification_state.json'
    final_path = ROOT / 'reviews/native_qualification.json'
    if state_path.exists() or final_path.exists() or (ROOT / 'smoke_jobs').exists() or (ROOT / 'smoke_results').exists():
        raise FileExistsError('preserve all previous qualification state/jobs/partial/results')
    state = {'status': 'QUALIFICATION_METADATA_GATES', 'started_unix': time.time(),
             'active': None, 'jobs': [], 'comparisons': [], 'whole_elapsed_seconds': None}
    write(state_path, state, exclusive=True)
    try:
        fit = load(ROOT / 'fit_state.json')
        if fit['status'] != 'FIT_COMPLETE_ALL_MODELS_FROZEN' or fit['active'] is not None:
            raise RuntimeError('formal FIT must be completely finished before any qualification query')
        if len(fit['completed']) != 2 or {r['dataset'] for r in fit['completed']} != set(DATASETS) or any(not r['model_eligible'] or r['elapsed_seconds'] > 900 for r in fit['completed']):
            raise RuntimeError('all two dataset <=900s complete eligible fitted models required')
        build = load(args.build_receipt)
        review = load(args.source_review)
        if build['status'] != 'PASS_E176_NATIVE_BUILD' or build['exit_code'] != 0:
            raise RuntimeError('successful current native build receipt required')
        if not review['status'].startswith('PASS'):
            raise RuntimeError('complete native source static review PASS required')
        source_identity = {}
        for name in SOURCES:
            path = str((ROOT / 'src' / name).resolve())
            digest = sha(path)
            if build['source_sha256'].get(path) != digest or review['source_sha256_at_review'].get(path) != digest:
                raise RuntimeError('build/static-review source identity changed: ' + path)
            source_identity[path] = digest
        binary = Path(build['binary']).resolve()
        if binary != (ROOT / 'bin/benchmark').resolve() or sha(binary) != build['binary_sha256']:
            raise RuntimeError('current built native binary identity required')
        source_identity[str(binary)] = build['binary_sha256']
        source_identity[str(Path(__file__).resolve())] = sha(__file__)
        protocol_sha = sha(ROOT / 'protocol.md')
        source_identity[str((ROOT / 'protocol.md').resolve())] = protocol_sha
        if review['protocol_sha256_at_review'] != protocol_sha:
            raise RuntimeError('source-review protocol identity changed')
        params = load(ROOT / 'parameter_lock.json')
        preflight = load(ROOT / 'reviews/data_preflight.json')
        if not preflight['status'].startswith('PASS') or params['protocol_sha256'] != protocol_sha or preflight['protocol_sha256'] != protocol_sha:
            raise RuntimeError('locked public input/model/protocol identity required')
        expected_job_paths = {str(ROOT / 'jobs' / f'public_test.{ds}.json') for ds in DATASETS}
        if set(params['jobs']) != expected_job_paths:
            raise RuntimeError('exact two frozen formal jobs required')
        protected = {path: entry['current_stat'] for path, entry in preflight['registered_input_files'].items()}
        gates = [args.build_receipt, args.source_review, ROOT / 'parameter_lock.json', ROOT / 'reviews/data_preflight.json', ROOT / 'fit_state.json']
        gate_identity = {str(p.resolve()): {'sha256': sha(p), 'stat4': stat4(p)} for p in gates}
        protected.update({p: stat4(p) for p in source_identity})
        protected.update({p: item['stat4'] for p, item in gate_identity.items()})
        unchanged(protected); resource_guard()
        smoke_jobs = []
        for ds in DATASETS:
            formal_path = ROOT / 'jobs' / f'public_test.{ds}.json'
            if sha(formal_path) != params['jobs'][str(formal_path)]:
                raise RuntimeError('formal source job changed')
            formal = load(formal_path)
            if formal['dataset'] != ds or formal['n'] != 10000 or tuple(formal['K_values']) != KS or tuple(formal['L']) != LS or tuple(m['name'] for m in formal['methods']) != METHODS:
                raise ValueError('qualification preserves all frozen 10KL/eight methods')
            if formal['cpu'] != 15 or formal['threads'] != 1 or not formal['no_training']:
                raise ValueError('only single-thread frozen model query qualification')
            protected[str(formal_path)] = stat4(formal_path)
            smoke = dict(formal)
            smoke.update(n=16, warmup_n=16, warmup_batches=1, timing_repeats=1, audit_n=256,
                         out=str(ROOT / 'smoke_results' / ds), check_region_zero=True,
                         qualification_only=True, source_formal_job=str(formal_path), source_formal_job_sha256=sha(formal_path))
            path = ROOT / 'smoke_jobs' / f'{ds}.json'
            write(path, smoke, exclusive=True)
            protected[str(path)] = stat4(path)
            smoke_jobs.append((path, smoke))
        state['status'] = 'RUNNING_SERIAL_N16_QUALIFICATION'
        state['source_identity'] = source_identity
        state['gate_identity'] = gate_identity
        write(state_path, state)
        for path, smoke in smoke_jobs:
            job_receipt = run_child(binary, path, smoke, state, state_path, protected, args.timeout_seconds)
            complete = load(Path(smoke['out']) / 'complete.json')
            if complete['status'] != 'PASS_E176_SMOKE_NATIVE_ORACLES' or not complete['smoke_only'] or len(complete['results']) != 80:
                raise RuntimeError('complete current smoke native oracle scope required')
            keys = {(r['method'], r['K'], r['L']) for r in complete['results']}
            if keys != {(m, k, l) for m in METHODS for k in KS for l in LS} or complete['wall_rounds'] != 80:
                raise RuntimeError('missing/duplicated smoke methods/points/one-round batches')
            for r in complete['results']:
                if r['n'] != 16 or not r['original_scalar_main_kernel'] or not r['plain_count_bits_equal'] or r['count_audit_n'] != 16 or r['full_plain_independent_replay_bits_equal'] or r['full_plain_independent_replay_n'] != 0:
                    raise RuntimeError('smoke full-plain/oracle/sampled-count contract')
                if r['method'] not in ('NSG', 'GT') and not r['full_plain_independent_scalar_linear_oracle']:
                    raise RuntimeError('full smoke post oracle missing')
                if r['method'] in ('M5OPT', 'REGOPT96') and not r['optimized_reference_packet_bits_equal']:
                    raise RuntimeError('native optimization packet parity missing')
                if r['method'] in ('M5OPT', 'REGOPT96', 'M5RES12', 'WIDE12') and (not r['cached_main_R_fresh_score_words_equal'] or r['cachedmain_R_word_mismatches'] != 0):
                    raise RuntimeError('native whole-window cached R qualification missing')
            job_receipt['native_calls'] = complete['native_calls']
            job_receipt['native_complete_sha256'] = sha(Path(smoke['out']) / 'complete.json')
            job_receipt['points'] = len(complete['results'])
            job_receipt['timed_batches'] = complete['wall_rounds']
            job_receipt['word_regression_points'] = 0
            for K in KS:
                for L in LS:
                    for method in OLD_METHODS:
                        new = Path(smoke['out']) / f'k{K}' / f'{method}_L{L}' / 'raw'
                        old = OLD / 'results/public_test' / smoke['dataset'] / f'k{K}' / f'{method}_L{L}' / 'raw'
                        for name, width in [('ids.i32', K), ('distances.f32', K), ('entry_ids.i32', 3), ('profile_distances.f32', 3)]:
                            check_prefix(new / name, old / name, 16 * width * 4, 10000 * width * 4, state['comparisons'])
                        if method == 'M5REG96':
                            check_prefix(new / 'region_trace.i32', old / 'region_trace.i32', 16 * 128 * 4, 10000 * 128 * 4, state['comparisons'])
                        job_receipt['word_regression_points'] += 1
            unchanged(protected)
            write(state_path, state)
        if len(state['comparisons']) != 340 or len(state['jobs']) != 2 or any(r['exit_code'] != 0 for r in state['jobs']):
            raise RuntimeError('qualification complete 340 byte-file checks/two successful jobs required')
        unchanged(protected)
        for p, expected in source_identity.items():
            if sha(p) != expected:
                raise RuntimeError('qualification source/binary identity changed after child')
        state.update(status='PASS_E176_N16_ORACLES_AND_FROZEN_ORIGINAL_WORD_REGRESSION',
                     active=None, finished_unix=time.time(), whole_elapsed_seconds=time.monotonic() - started,
                     source_identity=source_identity, protocol_sha256_at_review=protocol_sha,
                     native_calls=sum(r['native_calls'] for r in state['jobs']),
                     matched_original_methods=list(OLD_METHODS), compared_query_prefix_n=16,
                     points=160, timed_batches=160, word_file_comparisons=340,
                     count_audit_scope='all16 of each smoke point; formal still fixed uniform256, not full NDC',
                     full_native_oracles='all n16 per post method; OPT packets equal original M5/REG; cached R fresh-word qualification precedes timing',
                     no_public_GT_read=True, no_quality_or_old_new_timing_comparison=True,
                     no_fitting=True, partial_preserved=True,
                     limits='finite n16 prefix qualification only; not full public10K equality, performance gain, Recall or independent semantic/IID evidence',
                     cost_scope='elapsed through metadata/hash/job generation/two complete serial child lifecycles/resource guards/prefix comparisons, measured immediately before final receipt serialization; root external process elapsed supplies the complete script lifecycle; child elapsed separately nested, not additive')
        write(state_path, state)
        write(final_path, state, exclusive=True)
        print(json.dumps({'status': state['status'], 'native_calls': state['native_calls'],
                          'word_file_comparisons': state['word_file_comparisons'], 'whole_elapsed_seconds': state['whole_elapsed_seconds']}))
    except BaseException as e:
        state.update(status='FAILED_QUALIFICATION_PARTIAL_PRESERVED', active=None,
                     error=repr(e), whole_elapsed_seconds=time.monotonic() - started)
        # No success receipt or artificial PASS is written on any partial path.
        write(state_path, state)
        raise


if __name__ == '__main__':
    main()
