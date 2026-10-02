import pathlib,subprocess,json,os,hashlib,datetime,stat
R=pathlib.Path('/data/netg/ACSG');D=pathlib.Path(__file__).resolve().parent.parent
stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S');branch=f'backup/pre-nsg-optimization-{stamp}'
def git(args,**kw):return subprocess.check_output(['git',*args],cwd=R,**kw)
raw=git(['ls-files','-m','-d','-o','--exclude-standard','-z']).split(b'\0');names=sorted({os.fsdecode(x) for x in raw if x})
exts={'.c','.cc','.cpp','.cxx','.h','.hh','.hpp','.cu','.cuh','.py','.sh','.cmake','.md','.rst','.toml','.yaml','.yml','.ini','.cfg','.html','.css','.js','.ts','.tsx','.jsx','.svg','.ipynb','.service','.timer','.patch','.diff'}
selected=[];skipped=[];total=0
for name in names:
 p=R/name;parts=p.parts[len(R.parts):]
 if name.startswith(str(D.relative_to(R))+'/') or any(x.startswith('.') and x not in {'.gitignore','.gitattributes','.gitmodules'} for x in parts) or 'build' in parts or 'node_modules' in parts or any(x in {'venv','.venv_cpu','__pycache__','bin'} for x in parts):continue
 source=p.suffix.lower() in exts or p.name in {'CMakeLists.txt','Makefile','Dockerfile','.gitignore','.gitattributes','.gitmodules'} or p.name.startswith('requirements') and p.suffix=='.txt'
 config=p.suffix.lower()=='.json' and ('config' in p.name.lower() or p.name.startswith(('eval_', 'manifest', 'settings')) or p.name in {'state.json','complete.json','protocol.json'}) and not any(x in p.name.lower() for x in ['credential','secret','token','auth'])
 if not(source or config):continue
 if not p.exists() and not p.is_symlink():selected.append(name);continue
 if not p.is_file() and not p.is_symlink():continue
 if p.is_symlink():selected.append(name);continue
 z=p.stat().st_size
 if z>(2*1024**2 if source else 256*1024):skipped.append({'path':name,'reason':'size cap','bytes':z});continue
 data=p.read_bytes()
 if b'\0' in data:skipped.append({'path':name,'reason':'binary content','bytes':z});continue
 try:data.decode('utf-8')
 except UnicodeDecodeError:skipped.append({'path':name,'reason':'non UTF-8','bytes':z});continue
 selected.append(name);total+=z
assert 'ACSG/ACSG.cpp' in selected and 'summary.md' in selected
manifest={'branch':branch,'base_commit':git(['rev-parse','HEAD'],text=True).strip(),'files':selected,'selected_count':len(selected),'selected_bytes':total,'skipped_text_candidates':skipped,'scope':'Existing source, scripts, docs, and small text configuration/metadata; excludes E99 new work and data/model/build artifacts.'}
(D/'reviews/backup_selection.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in manifest.items() if k not in ['files','skipped_text_candidates']},ensure_ascii=False,indent=2),flush=True)
if os.environ.get('ACSG_COMMIT_BACKUP')!='1':raise SystemExit(0)
index_path=pathlib.Path(git(['rev-parse','--git-path','index'],text=True).strip());index_path=index_path if index_path.is_absolute() else R/index_path
old_index_hash=hashlib.sha256(index_path.read_bytes()).hexdigest() if index_path.exists() else None
old_head=git(['symbolic-ref','HEAD'],text=True).strip()
tmp_index=D/'reviews/backup.git-index';assert not tmp_index.exists();env=dict(os.environ,GIT_INDEX_FILE=str(tmp_index),GIT_LITERAL_PATHSPECS="1")
subprocess.run(['git','read-tree','HEAD'],cwd=R,env=env,check=True)
paths=D/'reviews/backup_paths.nul';paths.write_bytes(b''.join(os.fsencode(x)+b'\0' for x in selected))
subprocess.run(['git','add','-A','-f','--pathspec-from-file='+str(paths),'--pathspec-file-nul'],cwd=R,env=env,check=True)
tree=git(['write-tree'],env=env,text=True).strip()
message='backup: preserve ACSG source and E98 evidence before NSG optimization\n\nSnapshot existing source, scripts, configurations, and project documentation before E99 edits. Large data, learned weights, native indexes, generated binaries, and build products remain in place. No remote push.\n'
commit_env=dict(env,GIT_AUTHOR_NAME='Codex',GIT_AUTHOR_EMAIL='codex@local',GIT_COMMITTER_NAME='Codex',GIT_COMMITTER_EMAIL='codex@local')
commit=git(['commit-tree',tree,'-p',manifest['base_commit']],env=commit_env,input=message,text=True).strip()
subprocess.run(['git','update-ref','refs/heads/'+branch,commit,'0'*40],cwd=R,check=True)
# Independently read every selected blob back from the committed tree.
entries={os.fsdecode(x.split(b'\t',1)[1]):x.split(b'\t',1)[0].split()[2].decode() for x in git(['ls-tree','-r','-z',commit]).split(b'\0') if x}
proc=subprocess.Popen(['git','cat-file','--batch'],cwd=R,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
verified=0
for name in selected:
 p=R/name
 if not p.exists() and not p.is_symlink():assert name not in entries;verified+=1;continue
 blob=entries[name];proc.stdin.write((blob+'\n').encode());proc.stdin.flush();head=proc.stdout.readline().split();z=int(head[2]);data=proc.stdout.read(z);assert proc.stdout.read(1)==b'\n'
 current=os.fsencode(os.readlink(p)) if p.is_symlink() else p.read_bytes()
 assert data==current,('backup bytes differ',name);verified+=1
proc.stdin.close();assert proc.wait()==0
assert git(['rev-parse','HEAD'],text=True).strip()==manifest['base_commit']
assert git(['symbolic-ref','HEAD'],text=True).strip()==old_head
assert (hashlib.sha256(index_path.read_bytes()).hexdigest() if index_path.exists() else None)==old_index_hash
manifest.update(commit=commit,tree=tree,verified_files=verified,status='PASS',working_branch_unchanged=old_head,original_index_unchanged=True,created_at=datetime.datetime.now().isoformat())
(D/'reviews/git_backup.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'status':'PASS','commit':commit,'branch':branch,'verified_files':verified,'selected_bytes':total,'working_branch_unchanged':old_head,'original_index_unchanged':True},indent=2),flush=True)
