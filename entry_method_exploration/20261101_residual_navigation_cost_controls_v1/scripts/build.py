from common import *
import subprocess
argv=read(OLD/'reviews/build.json')['argv'];argv=[str(R/'src/benchmark.cpp')if x==str(OLD/'src/benchmark.cpp')else str(R/'storage/benchmark')if x==str(OLD/'storage/benchmark')else x for x in argv]
t=time.perf_counter();p=subprocess.run(argv,cwd=REPO,capture_output=True,text=True);(R/'reviews/build.log').write_text(p.stdout+p.stderr);dump(R/'reviews/build.json',dict(argv=argv,returncode=p.returncode,seconds=time.perf_counter()-t));assert p.returncode==0,p.stderr[-6000:]
files=[ident(p)for folder in ['src','scripts','configs']for p in(R/folder).glob('*')if p.is_file()]+[ident(R/'protocol.md'),ident(R/'selection_freeze.json'),ident(R/'storage/benchmark'),ident(OLD/'delivery_manifest.json')]
dump(R/'formal_freeze.json',dict(status='FROZEN_BEFORE_ALL_E196_FORMAL',time=time.time(),files=files,selection=read(R/'selection_freeze.json')));print('BUILD_FROZEN',flush=True)
