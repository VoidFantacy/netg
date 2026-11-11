"""Seal scientific questions/configurations/code before qualification and formal data."""
import ast,datetime,subprocess
from common import *
def main():
 assert not (R/'freeze.json').exists()
 files=set([R/'protocol.md',R/'theory.md',R/'permutations.json',R/'storage/benchmark'])
 files.update((R/'scripts').glob('*.py'));files.update((R/'configs').glob('*.json'));files.update((R/'source_before').rglob('*.md'));files.add(R/'source_before/E191_benchmark.cpp');files.add(R/'src/benchmark.cpp');files.update((R/'storage/models').rglob('*.*'))
 for p in (R/'scripts').glob('*.py'):ast.parse(p.read_text())
 old=read(OLD/'freeze.json')
 files.update(Path(x['path']) for x in old['files'])
 files.update([OLD/'delivery_manifest.json',OLD/'primary_complete.json',OLD/'dense_complete.json',OLD/'reviews/interpretation.json'])
 for ds in DS:
  root=OLD/'storage/results'/ds;files.update([OLD/f'configs/{ds}.json',root/'complete.json',root/'raw_packets.tar.zst',root/'raw_packet_archive.json'])
  files.update(root.glob('k*/REUSE-SQ_L200/trace.i32.gz'));files.update(root.glob('k*/MAIN-SQ_L200/trace.i32.gz'))
  files.add(R.parent/f'20261024_manifold_residual_probe_v1/analysis/{ds}.npz')
 for name in ['all_primary_points.csv','all_paired.csv','all_coverage.csv']:files.add(OLD/'analysis'/name)
 record=dict(status='FROZEN_BEFORE_E192_QUALIFICATION_AND_FORMAL',created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),question='Candidate-support necessity and controlled hub-table reassignment; permit counterexamples',datasets=DS,formal_datasets=ANCHORS,formal_K=100,formal_points=39,formal_batches=117,qualification_points=36,seeds=list(range(20261029,20261061)),formal_permutation=0,files=[dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(files)],large_assets=old['large_assets'],source_role='Original teacher supervision, test exposure and E191 roles inherited without retraining',no_adaptive_extension=True)
 dump(R/'freeze.json',record);print(json.dumps(dict(status=record['status'],files=len(record['files']))),flush=True)
if __name__=='__main__':main()
