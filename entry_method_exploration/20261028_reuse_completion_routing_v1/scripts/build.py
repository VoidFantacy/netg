import json,subprocess,time,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R.parent/'20261028_completion_cost_budget_v1';REPO=R.parents[1]
old=P/'src/cost_budget.cpp';before=old.read_text();after=before.replace('int main(int argc,char**argv)','int e188_preserved_main(int argc,char**argv)');assert before!=after
(R/'src/e188_snapshot.hpp').write_text(after)
a=json.loads((P/'reviews/build_receipt.json').read_text())['argv'];a=[str(R/'src/reuse.cpp') if x.endswith('src/cost_budget.cpp') else str(R/'bin/reuse') if x.endswith('bin/cost_budget') else x for x in a];t=time.perf_counter()
with (R/'reviews/build.log').open('x') as f:p=subprocess.run(a,cwd=REPO,stdout=f,stderr=subprocess.STDOUT)
v=dict(argv=a,returncode=p.returncode,seconds=time.perf_counter()-t,snapshot_source=str(old),snapshot_source_sha256=hashlib.sha256(old.read_bytes()).hexdigest(),snapshot_edit='rename main only')
(R/'reviews/build_receipt.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v));raise SystemExit(p.returncode)
