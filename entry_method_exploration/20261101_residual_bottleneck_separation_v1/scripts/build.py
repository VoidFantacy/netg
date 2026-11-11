from common import *
import shutil
started = time.perf_counter()
phase = sys.argv[1] if len(sys.argv)>1 else 'labels'
source = R / 'src/benchmark.cpp'
if phase=='decision':source=R/'src/decision_audit.cpp'
if phase != 'labels':
    for path in [R/'reviews'/f'build_{phase}.json',R/'reviews'/f'build_{phase}.log']:
        if path.exists():path.rename(path.with_name(path.stem+f'.attempt_{time.time_ns()}'+path.suffix))
if phase == 'labels':
    frozen = R / 'src/labels_frozen.cpp'
    if frozen.exists():
        prior = R / 'reviews/build_labels.json'
        assert prior.exists() and read(prior)['returncode'] != 0
        suffix = str(time.time_ns())
        frozen.rename(R / 'src' / f'labels_failed_{suffix}.cpp')
        for path in [prior, R / 'reviews/build_labels.log']:
            path.rename(path.with_name(path.stem + '_failed_' + suffix + path.suffix))
    shutil.copy2(source, frozen); source = frozen
argv = read(OLD / 'reviews/build.json')['argv']
argv = [str(source) if x.endswith('/20261101_residual_navigation_diagnosis_v1/src/benchmark.cpp')
        else str(R / 'storage' / f'{phase}_benchmark') if x.endswith('/20261101_residual_navigation_diagnosis_v1/storage/benchmark')
        else x for x in argv]
sources=[source]+list((R/'src').glob('*.inc'))
identities=[dict(path=str(p),sha256=sha(p)) for p in sources]
p = subprocess.run(argv, cwd=REPO, capture_output=True, text=True)
(R / 'reviews' / f'build_{phase}.log').write_text(p.stdout+p.stderr)
dump(R / 'reviews' / f'build_{phase}.json', dict(argv=argv, returncode=p.returncode,
    seconds=time.perf_counter()-started,source_files=identities))
assert p.returncode == 0, p.stderr[-10000:]
assert all(sha(Path(x['path']))==x['sha256'] for x in identities),'source changed while compiling'
print('BUILD_PASS', phase, flush=True)
