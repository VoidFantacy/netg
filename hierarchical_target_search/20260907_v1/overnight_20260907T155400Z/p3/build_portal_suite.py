#!/usr/bin/env python3
"""Build both fixed portal rules for both lambda branches of one P3 dataset."""
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


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', choices=['webvid2_5m_light_v1', 'yandex_t2i_official10M_ip_v1'], required=True)
    parser.add_argument('--output', type=Path, required=True, help='New execution metadata directory')
    args = parser.parse_args()
    p3 = RUN/'p3'
    protocol = p3/'protocol.json'
    gate = RUN/'gates/P2.json'
    audit = RUN/'p0/full_audit/audit.json'
    partition = p3/'partitions'/args.dataset/'manifest.json'
    require(time.time() < SOFT_CLOSE, 'Research soft deadline closed')
    require(read(gate)['status'] == 'PASS', 'P2 gate required')
    require(read(partition)['status'] == 'COMPLETE', 'Both structure branches must complete')
    require(sha(protocol) == 'fea64bc3c6a8046378849f55508198dcfd9a00df880a74e9d93cf22d051a418f', 'P3 protocol changed')
    py = ROOT/'.venv_cpu/bin/python'
    sources = [p3/'prepare_inputs_and_plans.py', p3/'finalize_portal_models.py',
               ROOT/'benches/bench_hierarchical_portals.cpp', ROOT/'ACSG/RegionalSearch.h',
               p3/'prober_build_manifest_v2.json', ROOT/'build/benches/bench_hierarchical_portals']
    bindings = [bound(path) for path in sources]
    args.output.mkdir(parents=True, exist_ok=False)
    record = {'status': 'INCOMPLETE', 'stage': 'P3_PORTAL_SUITE', 'dataset': args.dataset,
              'started_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
              'cpu_only': True, 'fit_range': [10000, 30000], 'pilot_accessed': False,
              'validation_accessed': False, 'heldout_accessed': False,
              'protocol': bound(protocol), 'partition': bound(partition), 'source': bound(__file__),
              'frozen_sources': bindings, 'fixed_branches': [0, 1], 'fixed_rules': ['frequency3', 'greedy3'],
              'invocations': []}

    def save():
        temporary = args.output/'execution.tmp.json'
        temporary.write_text(json.dumps(record, indent=2)+'\n')
        temporary.replace(args.output/'execution.json')

    def run(name, command, artifact):
        require(time.time() < SOFT_CLOSE, 'Research soft deadline closed between fit tasks')
        for binding in bindings:
            require(sha(binding['path']) == binding['sha256'], 'Frozen fit source/binary changed')
        item = {'name': name, 'status': 'RUNNING', 'command': command,
                'started_utc': dt.datetime.now(dt.timezone.utc).isoformat()}
        record['invocations'].append(item); save()
        print('P3_FIT_BEGIN', args.dataset, name, flush=True)
        started = time.perf_counter()
        with (args.output/(name+'.log')).open('xb') as log:
            child = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
            item.update(pid=child.pid, pgid=os.getpgid(child.pid)); save()
            item['returncode'] = child.wait()
        item.update(wall_seconds=time.perf_counter()-started,
                    status='COMPLETE' if item['returncode'] == 0 else 'FAILED',
                    ended_utc=dt.datetime.now(dt.timezone.utc).isoformat()); save()
        require(item['returncode'] == 0, 'Fit task failed; preserve all partial outputs: '+name)
        require(read(artifact)['status'] == 'COMPLETE', 'Fit artifact incomplete: '+name)
        item['artifact'] = bound(artifact); save()
        print('P3_FIT_DONE', args.dataset, name, item['wall_seconds'], flush=True)

    save()
    try:
        for lam in (0, 1):
            branch = 'lambda'+str(lam)
            plan = p3/'plans'/args.dataset/branch
            probes = p3/'probes'/args.dataset/branch
            models = p3/'models'/args.dataset/branch
            for path in (plan, probes, models):
                require(not path.exists(), 'Output must be new: '+str(path))
                path.parent.mkdir(parents=True, exist_ok=True)
            command = [str(py), str(sources[0]), 'plan', '--dataset', args.dataset,
                       '--protocol', str(protocol), '--gate', str(gate), '--audit', str(audit),
                       '--fit-manifest', str(p3/'fit_inputs'/args.dataset/'manifest.json'),
                       '--partition', str(partition.parent/branch/'manifest.json'), '--output', str(plan)]
            for path in sources[2:]:
                command += ['--source-binding', str(path)]
            run(branch+'_plan', command, plan/'plan.json')
            run(branch+'_probes', [str(sources[-1]), '--plan', str(plan/'plan.json'),
                                  '--output', str(probes), '--threads', '16'], probes/'complete.json')
            run(branch+'_finalize', [str(py), str(sources[1]), '--plan', str(plan/'plan.json'),
                                    '--probe-complete', str(probes/'complete.json'),
                                    '--output', str(models)], models/'complete.json')
        record['status'] = 'COMPLETE'
        record['models'] = {f'lambda{lam}_{rule}': bound(p3/'models'/args.dataset/f'lambda{lam}'/rule/'model.json')
                            for lam in (0, 1) for rule in ('frequency3', 'greedy3')}
    except BaseException as error:
        record['error'] = repr(error)
        raise
    finally:
        record['ended_utc'] = dt.datetime.now(dt.timezone.utc).isoformat(); save()


if __name__ == '__main__':
    main()
