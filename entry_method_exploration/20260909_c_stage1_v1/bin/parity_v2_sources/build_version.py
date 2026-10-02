#!/usr/bin/env python3
import datetime,hashlib,json,shutil,subprocess,sys
from pathlib import Path
V=Path(__file__).resolve().parents[1];R=Path('/data/netg/ACSG')
source,label=sys.argv[1:]
dest=V/'bin'/label;assert not dest.exists()
snapshot=V/'bin'/(label+'_sources');shutil.copytree(V/'src',snapshot)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
files=list((V/'src').glob('*'))+[R/p for p in ['ACSG/ACSG.cpp','ACSG/ACSG.h','ACSG/IndexACSG.h','faiss/faiss/impl/AuxIndexStructures.h',
 'build/faiss/faiss/libfaiss.a','build/ACSG/libACSG.a','build/MRNN_Descent/libmrnndescent.a']]
records=[{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in files if p.is_file()]
argv=['bash',str(V/'src/build.sh'),source,str(dest)]
m={'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'argv':argv,'compiler':subprocess.check_output(['c++','--version'],text=True),
 'source_and_dependencies':records,'cpu_only':True,'flags':'-std=c++17 -O3 -march=native -fopenmp -fPIC -Wall -Wextra'}
rc=subprocess.call(argv,cwd=R)
m.update({'exit_code':rc,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
if rc==0:
 for rec in records:assert sha(Path(rec['path']))==rec['sha256'],'source changed during build'
 m['binary_sha256']=sha(dest)
(V/'bin'/(label+'.build.json')).write_text(json.dumps(m,indent=2)+'\n')
sys.exit(rc)
