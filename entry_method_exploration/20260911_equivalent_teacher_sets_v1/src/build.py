from common import *

assert read(O/'reviews/preflight.json')['status']=='PASS'
for name in ['evaluate.cpp','benchmark_with_nsg.cpp','legacy_reference.cpp']:
    assert not (O/'src'/name).exists()
    shutil.copy2(E29/'src'/name,O/'src'/name)
old=(E29/'src/evaluate.cpp').read_text()
assert old.count('(reps==0 || reps==3)')==1
(O/'src/evaluate.cpp').write_text(old.replace('(reps==0 || reps==3)','(reps==0 || reps==5)'))
assert (O/'src/evaluate.cpp').read_text().replace('(reps==0 || reps==5)','(reps==0 || reps==3)')==old
build=read(E28/'bin/evaluate.build.json')
argv=[x.replace(str(E28/'src/evaluate.cpp'),str(O/'src/evaluate.cpp')).replace(str(E28/'bin/evaluate'),str(O/'bin/evaluate')) for x in build['argv']]
start=time.time()
with (O/'logs/build.log').open('w') as f:r=subprocess.run(argv,stdout=f,stderr=subprocess.STDOUT)
assert r.returncode==0,'see build.log'
dump(O/'bin/evaluate.build.json',dict(argv=argv,seconds=time.time()-start,exit_code=r.returncode,
    sources=[identity(O/'src'/n) for n in ['evaluate.cpp','benchmark_with_nsg.cpp','legacy_reference.cpp']],
    binary=identity(O/'bin/evaluate'),only_change='timing repetition contract 3 -> 5; identical Policy/kernel/loop',original_build=str(E28/'bin/evaluate.build.json')))
print('BUILD_PASS',flush=True)
