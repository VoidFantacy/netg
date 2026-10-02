from common import *
import subprocess,ast
assert read(RUN/'reviews/models_frozen.json')['status']=='PASS_FIT_DECOMPOSITION_MODELS_FROZEN'
assert not (RUN/'bin/evaluate').exists(),'preserve compiled binary'
old=ROOT/'entry_method_exploration/20260920_query_representation_pilot_v1'
cmd=read(old/'reviews/build_quality.json')['argv']
cmd=[str(RUN/'src/evaluate.cpp') if x==str(old/'src/quality.cpp') else str(RUN/'bin/evaluate') if x==str(old/'bin/quality') else '-I'+str(RUN/'src/common') if x=='-I'+str(old/'src/common') else x for x in cmd]
start=time.time()
with (RUN/'logs/build.log').open('x') as log:p=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
dump(RUN/'reviews/build.json',dict(argv=cmd,exit_code=p.returncode,seconds=time.time()-start))
assert p.returncode==0,'inspect build log'
for path in (RUN/'src').glob('*.py'):ast.parse(path.read_text())
assert sha(RUN/'src/kernels.hpp')==sha(old/'src/kernels.hpp')
print('Mechanism binary built; inherited kernel unchanged.')
