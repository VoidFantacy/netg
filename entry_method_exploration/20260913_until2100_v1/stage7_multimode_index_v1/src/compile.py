from common import *
import subprocess
threads();resources();provenance=read(D/'20260911_hnsw_rl_benchmark_v1/bin/provenance.json');records=[]
for name in ['evaluate','synthetic']:
    argv=list(provenance['build']['argv']);argv[argv.index(str(D/'20260911_hnsw_edge_rl_v1/src/evaluate.cpp'))]=str(O/'src'/f'{name}.cpp')
    argv[-1]=str(O/'bin'/name);start=time.monotonic()
    with (O/'logs'/f'compile_{name}.log').open('x') as log:r=subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT)
    rec=dict(argv=argv,seconds=time.monotonic()-start,returncode=r.returncode);records.append(rec);assert r.returncode==0
dump(O/'bin/provenance.json',dict(source_version='E34 copied source with isolated E66 Policy and explicit input prefix',builds=records,
    files=[identity(O/'bin'/x) for x in ['evaluate','synthetic']],original_kernel=identity(R/'ACSG/ACSG.cpp')))
print('COMPILE_PASS',records,flush=True)
