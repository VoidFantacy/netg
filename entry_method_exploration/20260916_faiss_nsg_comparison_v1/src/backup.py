import pathlib,subprocess,os,hashlib,json,datetime
D=pathlib.Path(__file__).resolve().parent.parent;R=D.parent.parent;E=D.parent/'20260916_residual_cost_research_v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip();index=sha(R/'.git/index')
selected=[R/n for n in ['ACSG/ACSG.cpp','ACSG/detail/CandidatePool.h','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/93_residual_search_cost_research.md','experiment_history/README.md']]
for p in E.rglob('*'):
 if not p.is_file() or any(x in p.relative_to(E).parts for x in ['bin','mplconfig','__pycache__']):continue
 if p.suffix.lower() not in ['.py','.cpp','.hpp','.h','.md','.json','.csv','.patch','.log','.png','.pdf']:continue
 if p.stat().st_size>5*1024**2:continue
 selected.append(p)
selected=sorted(set(selected));pathspec=D/'reviews/backup_paths.nul';pathspec.write_bytes(b'\0'.join(str(p.relative_to(R)).encode() for p in selected)+b'\0')
env=dict(os.environ,GIT_INDEX_FILE=str(D/'reviews/backup.git-index'),GIT_AUTHOR_NAME='Codex',GIT_AUTHOR_EMAIL='codex@local',GIT_COMMITTER_NAME='Codex',GIT_COMMITTER_EMAIL='codex@local')
parent='7d09367e85b956f4b4ab67c73e6f2b583ffcee38'
def git(*args,**kw):return subprocess.check_output(['git',*args],cwd=R,env=env,**kw)
git('read-tree',parent);git('add','-f','--pathspec-from-file='+str(pathspec),'--pathspec-file-nul')
tree=git('write-tree',text=True).strip();commit=git('commit-tree',tree,'-p',parent,input=b'Back up E100 diagnosis and current E99 implementation before native Faiss comparison\n').decode().strip()
branch='backup/pre-faiss-nsg-comparison-'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S');git('update-ref','refs/heads/'+branch,commit)
proc=subprocess.Popen(['git','cat-file','--batch'],cwd=R,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
for p in selected:
 proc.stdin.write((commit+':'+str(p.relative_to(R))+'\n').encode());proc.stdin.flush();h=proc.stdout.readline().decode().split();assert h[1]=='blob';b=proc.stdout.read(int(h[2]));assert proc.stdout.read(1)==b'\n' and b==p.read_bytes(),str(p)
proc.stdin.close();assert proc.wait()==0
assert git('rev-parse','HEAD',text=True).strip()==head and sha(R/'.git/index')==index
x={'status':'PASS','commit':commit,'branch':branch,'parent':parent,'files_verified':len(selected),'selected_bytes':sum(p.stat().st_size for p in selected),'main_head_unchanged':head,'index_unchanged_sha256':index,'files':[str(p.relative_to(R)) for p in selected]}
(D/'reviews/git_backup.json').write_text(json.dumps(x,indent=2)+'\n');print({k:v for k,v in x.items() if k!='files'})
