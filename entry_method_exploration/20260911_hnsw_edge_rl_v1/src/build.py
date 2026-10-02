from common import *
old=read(E32/'bin/evaluate.build.json')['argv']
for name,shared in [('environment',True),('evaluate',False)]:
 target=O/'bin'/(name+('.so' if shared else ''));assert not target.exists()
 argv=[x.replace(str(E32/'src/evaluate.cpp'),str(O/'src'/(name+'.cpp'))).replace(str(E32/'bin/evaluate'),str(target)) for x in old]
 # Training uses the isolated instrumented header; measured deployment compiles original hnswlib.
 if shared:argv[1:1]=['-shared','-I'+str(O/'src')]
 start=time.time()
 with (O/'logs'/(name+'.build.log')).open('x') as f:p=subprocess.run(argv,stdout=f,stderr=subprocess.STDOUT)
 dump(O/'bin'/(name+'.build.json'),dict(argv=argv,seconds=time.time()-start,exit_code=p.returncode))
 assert p.returncode==0,'see '+name+'.build.log'
 print('BUILD_PASS',name,flush=True)
