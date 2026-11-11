from common import *
phase=sys.argv[1] if len(sys.argv)>1 else 'labels'
argv=read(R.parent/'20261101_residual_navigation_diagnosis_v1/reviews/build.json')['argv']
argv=[str(R/'src/benchmark.cpp') if a.endswith('/20261101_residual_navigation_diagnosis_v1/src/benchmark.cpp') else str(R/'storage'/f'{phase}_benchmark') if a.endswith('/20261101_residual_navigation_diagnosis_v1/storage/benchmark') else a for a in argv]
os.environ['TMPDIR']='/dev/shm'
result=run(argv,R/'reviews'/f'build_{phase}.log')
result['binary_sha256']=sha(R/'storage'/f'{phase}_benchmark')
result['sources']=[dict(path=str(p),sha256=sha(p)) for p in (R/'src').glob('*')]
dump(R/'reviews'/f'build_{phase}.json',result)
print('BUILD_PASS',phase,result['seconds'])
