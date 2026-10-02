from pathlib import Path
import shutil,json,time,hashlib
R=Path(__file__).resolve().parents[1];A=R/'reviews/first_compile_failure';assert not A.exists();A.mkdir()
jobs=json.loads((R/'reviews/jobs.json').read_text());assert len(jobs)==1 and jobs[0]['kind']=='build' and jobs[0]['exit_code']==1 and jobs[0]['reserved_calls']==0
shutil.copytree(R/'src',A/'src')
for n in ['reviews/setup_freeze.json','reviews/execution_started.json','reviews/build_source_lock.json','reviews/jobs.json','state.json']:
 p=A/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/n,p)
for p in (R/'logs').glob('*.log'):shutil.copy2(p,A/p.name)
p=R/'src/kernels.hpp';s=p.read_text();old='const std::vector<acsg::EnterPoint>&,int,int,faiss::idx_t*,float*);';assert s.count(old)==1;s=s.replace(old,'const std::vector<acsg::EnterPoint>&,int,int,faiss::idx_t*,float*,int);');p.write_text(s)
def ident(p):p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
fix=dict(created_unix=time.time(),cause='Unused legacy KernelCall member pointer alias omitted the added primary argument; compile failed before all query access/search.',change='Only add int to alias; intervention/formula/protocol unchanged.',old=ident(A/'src/kernels.hpp'),new=ident(p),NSG_calls_before_repair=0,ANN_calls_before_repair=0,preserved_failure=str(A),failed_compile_seconds=jobs[0]['seconds'])
(R/'reviews/compile_signature_correction.json').write_text(json.dumps(fix,indent=2)+'\n')
for n in ['reviews/execution_started.json','logs/build.log','logs/run.log']:(R/n).rename(A/('active_'+Path(n).name))
lock=dict(created_unix=time.time(),files=[ident(p) for p in (R/'src').rglob('*') if p.is_file() and '__pycache__' not in str(p)]+[ident(R/n) for n in ['config.locked.json','protocol.md','research.md']],mechanical_correction=ident(R/'reviews/compile_signature_correction.json'))
(R/'reviews/setup_freeze.json').write_text(json.dumps(lock,indent=2)+'\n')
print(json.dumps(fix,indent=2))
