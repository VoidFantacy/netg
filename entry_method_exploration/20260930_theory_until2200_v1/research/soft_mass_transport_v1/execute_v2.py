import hashlib,json,runpy,sys
from pathlib import Path
R=Path(__file__).resolve().parent
def verify():
    c=json.loads((R/'correction_v2.locked.json').read_text())
    for p,s in c['sources_sha256'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==s
if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1] in ('main','audit');verify()
    runpy.run_path(str(R/('run_v2.py' if sys.argv[1]=='main' else 'audit.py')),run_name='__main__');verify()
