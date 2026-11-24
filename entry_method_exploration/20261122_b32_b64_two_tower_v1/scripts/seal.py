"""Close the completed experiment and verify every archived file."""
import csv
from pathlib import Path
import sys

from run import DATASETS, ROOT, cfg, digest, read, verify, write


def finish():
    analysis = ROOT/'analysis'
    outcomes=read(analysis/'outcomes.json')
    data={}
    for ds in DATASETS:
        formal = Path(read(cfg(ds,'formal'))['output_dir'])
        replay = Path(read(cfg(ds,'replay'))['output_dir'])
        native = read(formal/'complete.json')
        diagnosis = read(replay/'complete.json')
        assert native['status']=='PASS_E226_FORMAL' and diagnosis['status']=='PASS_E226_REPLAY'
        data[ds] = dict(points=native['points'],batches=native['batches'],
                        replay_points=diagnosis['points'],replay_checks=diagnosis['query_merge_checks'],
                        outcomes=outcomes[ds])
    with (analysis/'points.csv').open() as f:
        assert sum(1 for _ in csv.DictReader(f))==132
    with (analysis/'rounds.csv').open() as f:
        assert sum(1 for _ in csv.DictReader(f))==264
    write(ROOT/'state.json', dict(status='COMPLETE_E226',production='E99/E211',
          residual_reference='original GT10+B32',K=100,formal_queries_per_dataset=3072,
          formal_points=132,formal_batches=264,formal_native_scalar_audits=132*256,
          native_replay_points=112,native_replay_checks=114464,
          datasets=data,figure='analysis/recall_qps.png',report='report.md'))
    candidates=sorted(p for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    files={str(p.relative_to(ROOT)):{'bytes':p.stat().st_size,'sha256':digest(p)} for p in candidates}
    write(ROOT/'seal.json',dict(status='SEALED_E226',files=files))


def audit():
    for kind in ('input','pools','models'):
        verify(ROOT/f'{kind}_freeze.json')
    seal=read(ROOT/'seal.json')
    for rel,ref in seal['files'].items():
        item = ROOT/rel
        assert item.stat().st_size == ref['bytes'] and digest(item)==ref['sha256'],rel
    print(seal['status'],len(seal['files']),'files verified')


if __name__=='__main__':
    if 'verify' not in sys.argv:
        finish()
    audit()
