from common import *
import subprocess
finite_deadline()
cmd=read(RUN/'reviews/build_label.json')['argv']
cmd=[str(RUN/'src/quality.cpp') if x==str(RUN/'src/label.cpp') else str(RUN/'bin/quality') if x==str(RUN/'bin/label') else x for x in cmd]
with (RUN/'logs/build_quality.log').open('x') as f:
    t=time.time();p=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
dump(RUN/'reviews/build_quality.json',dict(argv=cmd,exit_code=p.returncode,seconds=time.time()-t))
assert p.returncode==0,'inspect quality build log'
dump(RUN/'reviews/quality_source_lock.json',dict(status='FROZEN',
     sources=[identity(RUN/'src'/x) for x in ['quality.cpp','search_core.hpp','kernels.hpp']],
     binary=identity(RUN/'bin/quality'),WFree_seed=20260920,
     WFree_build='Inherited anchor M/efConstruction, original ascending hub order, no row normalization',
     exact_tie='hnswlib inner-product distance then real ID',online_projection='float32 accumulation, original raw query retained for NSG'))
print('quality binary built and sources frozen')
