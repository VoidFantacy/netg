from common import *
import datetime,re,shutil,subprocess
roots=['summary.md','spec.md','s-target.md','s-experiment.md','LOCAL_CODEX_START.md','AGENTS.md','experiment_history/README.md']
# Verify the original measurement code, fixed roles, threshold/model blobs and masks.
frozen=read(R/'formal_freeze.json')['files']
for x in frozen:assert sha(x['path'])==x['sha256'],x['path']
for x in read(R/'input_manifest.json'):assert sha(x['path'])==x['sha256'],x['path']
assert sha(R/'protocol.md')==read(R/'freeze.json')['protocol_sha256']
pts=batches=qual=dev=0;runtime=0;peak=0
for ds in ANCHORS:
 for mode in ['formal','qualification','labels']:
  c=read(R/f'configs/{ds}.{"dev" if mode=="labels" else mode}.json');done=read(Path(c['output_dir'])/'complete.json');receipt=read(R/f'reviews/{mode}_{ds}.receipt.json');assert receipt['returncode']==0 and receipt['max_observed_threads']==1 and receipt['affinity']==[15];runtime+=receipt['seconds'];peak=max(peak,receipt['peak_rss'])
  if mode=='formal':pts+=done['points'];batches+=done['batches']
  elif mode=='qualification':qual+=done['points']
  else:dev+=done['points']
  if mode!='labels':assert read(R/f'reviews/{ds}.{mode}.audit.json')['status'].startswith('PASS_')
assert (pts,batches,qual,dev)==(102,306,36,12)
for v in read(R/'reviews/inherited_assets.json'):
 p=Path(v['path']);st=p.stat();assert (st.st_size,st.st_ino,st.st_mtime_ns)==(v['bytes'],v['inode'],v['mtime_ns']),p
 if 'sha256' in v:assert sha(p)==v['sha256'],p
# Build closure identity audit: preserved sources and compiled native libraries.
argv=read(R/'reviews/build.json')['argv'];srcs=[REPO/'entry_method_exploration/20261028_seven_dataset_scoring_v1/src/benchmark.cpp'];seen=set();inc=[REPO,REPO/'benches',REPO/'faiss',REPO/'build/_deps/json-src/single_include']
def add(p):
 p=p.resolve()
 if p in seen:return
 seen.add(p)
 if p.suffix in ['.cpp','.hpp','.h']:
  for z in re.findall(r'^\s*#\s*include\s*["<]([^">]+)[">]',p.read_text(),re.M):
   for q in [p.parent/z]+[d/z for d in inc]:
    if q.is_file():add(q);break
for p in srcs+[R/'src/benchmark.cpp']:add(p)
for s in argv:
 if s.endswith(('.o','.a')):
  p=Path(s);add(p if p.is_absolute() else REPO/p)
prevfreeze={x['path']:x['sha256'] for x in read(R.parent/'20261029_sharing_necessity_v1/freeze.json')['files']};closure=[]
for p in sorted(seen):
 digest=sha(p);expected=prevfreeze.get(str(p));assert expected is None or digest==expected,p
 closure.append(dict(path=str(p),sha256=digest,matched_E192_preexisting_freeze=expected is not None))
dump(R/'reviews/build_closure_after.json',dict(status='PASS_POST_FORMAL_BUILD_CLOSURE_AUDIT',files=closure,note='Post-formal source identity audit; not misrepresented as pre-formal freeze for unlisted transitive files.'))
# Verify old scientific seal using original byte snapshots for mutable root documents.
prev=R.parent/'20261029_sharing_necessity_v1';old=read(prev/'delivery_manifest.json');bridge=[]
for f in old['files']:
 original=Path(f['path']);rel=None
 try:rel=str(original.relative_to(REPO))
 except ValueError:pass
 effective=R/'source_before'/rel if rel in roots else original
 assert effective.stat().st_size==f['bytes'] and sha(effective)==f['sha256'],original
 if effective!=original:bridge.append(dict(original=str(original),effective=str(effective),sha256=f['sha256'],bytes=f['bytes']))
dump(R/'reviews/E192_seal_bridge.json',dict(status='PASS_ALL_PREVIOUS_SEALED_BYTES_WITH_ROOT_SNAPSHOT_MAPPING',files=len(old['files']),old_manifest_sha256=sha(prev/'delivery_manifest.json'),mapped_roots=bridge,old_manifest_modified=False))
# New links and document role wiring.
bad=[]
for p in [R/'report_zh.md',REPO/'summary.md',REPO/'s-target.md',REPO/'LOCAL_CODEX_START.md',REPO/'experiment_history/193_adaptive_completion_gate_v1.md']:
 for url in re.findall(r'\[[^\]]*\]\(([^)]+)\)',p.read_text()):
  if url.startswith(('http:','https:','#')):continue
  target=(p.parent/url.split('#')[0]);
  if not target.exists():bad.append(dict(file=str(p),link=url))
assert not bad,bad
assert not list(R.rglob('*.pdf'))
for f in ['summary.md','spec.md','s-target.md','s-experiment.md','LOCAL_CODEX_START.md','experiment_history/README.md']:assert 'E193' in (REPO/f).read_text()
check=subprocess.run(['git','diff','--check','--',*roots,'experiment_history/193_adaptive_completion_gate_v1.md'],cwd=REPO,capture_output=True,text=True);assert check.returncode==0,check.stdout+check.stderr
storage=[p for p in (R/'storage').rglob('*') if p.is_file()];owned_bytes=sum(p.stat().st_size for p in storage);disk={p:shutil.disk_usage(p).free for p in ['/data','/root']};assert disk['/data']>.65*2**30 and disk['/root']>.7*2**30
validation=dict(status='PASS_E193_COMPLETE_LOCAL_DELIVERY',formal_points=pts,formal_batches=batches,qualification_points=qual,development_points=dev,action_microtimings=72000,frozen_files_checked=len(frozen),previous_sealed_files_checked=len(old['files']),threads=1,cpu=15,all_native_seconds=runtime,peak_native_rss_bytes=peak,new_storage_bytes=owned_bytes,disk_free_bytes=disk,default_changed=False,new_PDF=False,scope='102 fixed points only; no blind confirmation; full-gain ideal reference is not an all-policy upper bound')
dump(R/'validation.json',validation);dump(R/'state.json',dict(status='COMPLETED_ADAPTIVE_GATE_PILOT_NO_DEFAULT_CHANGE',completed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),formal_points=pts,formal_batches=batches,default_changed=False,pending_work=False))
paths=[p for p in R.rglob('*') if p.is_file() and '__pycache__' not in str(p) and p.name!='delivery_manifest.json']+storage+[REPO/x for x in roots]+[REPO/'experiment_history/193_adaptive_completion_gate_v1.md'];paths=sorted(set(paths),key=str)
dump(R/'delivery_manifest.json',dict(status='SEALED_E193_COMPLETE_LOCAL_DELIVERY',files=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in paths]))
print(json.dumps(validation,ensure_ascii=False,indent=2))
