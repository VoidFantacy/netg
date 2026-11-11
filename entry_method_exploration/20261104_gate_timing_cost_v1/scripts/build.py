from common import *
old=R.parent/'20261102_conditional_residual_policy_v1'
argv=read(old/'reviews/build_formal.json')['argv']
argv=[str(R/'src/benchmark.cpp') if x==str(old/'src/benchmark.cpp') else str(R/'storage/benchmark') if x==str(old/'storage/formal_benchmark') else x for x in argv]
os.environ['TMPDIR']='/dev/shm'
r=run(argv,R/'reviews/build.log');r['binary_sha256']=sha(R/'storage/benchmark');r['sources']=[dict(path=str(p),sha256=sha(p)) for p in (R/'src').glob('*')];dump(R/'reviews/build.json',r);print('BUILT',r['seconds'],flush=True)
