#!/usr/bin/env python3
"""Gate-aware launcher for this version; all commands use taskctl supervision."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

RUN = Path(__file__).resolve().parents[1]

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stage', choices=[f'P{x}' for x in range(9)], required=True)
    p.add_argument('--split', choices=['none','fit','pilot','validation','heldout'], required=True)
    p.add_argument('--measurement', choices=['audit','correctness','build','count','timing','trace','analysis'], required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--name', required=True)
    p.add_argument('--heavy', action='store_true')
    p.add_argument('--oracle', action='store_true')
    p.add_argument('--expected-seconds', type=float, default=120)
    p.add_argument('--timeout-seconds', type=float, default=3600)
    p.add_argument('--min-ram-gib', type=float, default=4)
    p.add_argument('command', nargs=argparse.REMAINDER)
    a = p.parse_args()
    stage = int(a.stage[1:])
    provenance = []
    for s in range(stage):
        gate = RUN/'gates'/f'P{s}.json'
        if not gate.exists():
            raise RuntimeError(f'Missing upstream gate {gate}')
        g = json.loads(gate.read_text())
        if g.get('status') not in ('PASS', 'GO'):
            raise RuntimeError(f'Upstream {gate.name} is not passed')
        provenance.append({'path':str(gate), 'sha256':hashlib.sha256(gate.read_bytes()).hexdigest()})
    if a.split == 'heldout':
        if stage < 7 or not (RUN/'gates/method_frozen.json').exists():
            raise RuntimeError('Held-out requires P6 PASS and frozen method manifest')
    if a.split == 'validation' and stage < 6:
        raise RuntimeError('Validation performance requires P5 pass; metadata audits use split none')
    if a.oracle and a.split not in ('fit','pilot'):
        raise RuntimeError('Oracle is train/development diagnosis only')
    if a.output.exists():
        raise RuntimeError('Refusing existing output')
    command = a.command[1:] if a.command[:1] == ['--'] else a.command
    if not command:
        raise RuntimeError('Missing executable command')
    # Output is reserved by the invoked program itself. The invocation manifest
    # uses x mode and thus also rejects duplicate job names before execution.
    invocation = RUN/'control'/'invocations'
    invocation.mkdir(exist_ok=True)
    path = invocation/(a.name+'.json')
    with path.open('x') as f:
        json.dump({'stage':a.stage,'split':a.split,'measurement':a.measurement,
                   'output':str(a.output.resolve()),'command':command,'oracle':a.oracle,
                   'upstream_gates':provenance},f,indent=2)
    ctl = [sys.executable,str(RUN/'control/taskctl.py'),'launch','--name',a.name,
           '--expected-seconds',str(a.expected_seconds),'--timeout-seconds',str(a.timeout_seconds),
           '--min-ram-gib',str(a.min_ram_gib)]
    if a.heavy:
        ctl.append('--heavy')
    subprocess.run(ctl+['--']+command,check=True)

if __name__ == '__main__':
    main()
