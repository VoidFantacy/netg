import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):
    os.environ[key]='1'
from pathlib import Path
import hashlib,json,time
import numpy as np
RUN=Path(__file__).resolve().parents[1]
ROOT=RUN.parents[1]
LOCK=json.loads((RUN/'config.locked.json').read_text())
DS=LOCK['datasets']
def dump(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n');tmp.replace(path)
def read(path):return json.loads(Path(path).read_text())
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(16<<20),b''):h.update(b)
    return h.hexdigest()
def identity(path):
    path=Path(path);s=path.stat()
    return dict(path=str(path),bytes=s.st_size,mtime_ns=s.st_mtime_ns,sha256=sha(path))
def stat_identity(path):
    path=Path(path);s=path.stat();return dict(path=str(path),bytes=s.st_size,mtime_ns=s.st_mtime_ns)
def finite_deadline():
    assert time.time()<LOCK['created_unix']+LOCK['prepare_label_train_seconds'],'preparation/labels/training deadline'

