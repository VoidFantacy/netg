"""Bind a new controlled intervention, preserving sealed E191 bytes."""
import collections,datetime,os,shutil,subprocess,time
from common import *
ROOTS=['summary.md','spec.md','s-target.md','s-experiment.md','LOCAL_CODEX_START.md','experiment_history/README.md','experiment_history/191_seven_dataset_scoring_v1.md','AGENTS.md']
def main():
 t=time.perf_counter();store=Path('/root/acsg-e192-storage');store.mkdir(exist_ok=False)
 for d in ['scripts','configs','source_before','reviews','analysis','src']:(R/d).mkdir(exist_ok=True)
 (R/'storage').symlink_to(store,target_is_directory=True)
 oldseal=read(OLD/'delivery_manifest.json');by_path={x['path']:x for x in oldseal['files']};bridge=[]
 for name in ROOTS:
  src=REPO/name;dst=R/'source_before'/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
  assert sha(src)==sha(dst)==by_path[str(src)]['sha256']
  bridge.append(dict(original_path=str(src),snapshot_path=str(dst),sha256=sha(dst)))
 checked=0
 for x in oldseal['files']:
  assert sha(x['path'])==x['sha256'],x['path'];checked+=1
 dump(R/'reviews/E191_before.json',dict(status='PASS_E191_ALL_SEALED_FILES_BEFORE',files=checked,seal_sha256=sha(OLD/'delivery_manifest.json'),mutable_document_bridge=bridge))
 source=(OLD/'src/benchmark.cpp').read_text();shutil.copy2(OLD/'src/benchmark.cpp',R/'source_before/E191_benchmark.cpp')
 replacements=[
 ('ids,idblock,hubtab,pool','ids,idblock,hubtab,shuffletab,pool'),
 ('hubtab=read_raw<int32_t>(f.at("hub_blocks"));','hubtab=read_raw<int32_t>(f.at("hub_blocks"));shuffletab=read_raw<int32_t>(f.at("shuffled_hub_blocks"));require(shuffletab.size()==hubtab.size(),"matched shuffle table bytes");'),
 ('const int32_t*h,bool mainonly){','const int32_t*h,bool mainonly,bool shuffled){'),
 ('int b=hubtab[it->second*8+a];','int b=(shuffled?shuffletab:hubtab)[it->second*8+a];'),
 ('proposals(R,K,h,method=="MAIN-SQ");','proposals(R,K,h,method=="MAIN-SQ",method=="SHUFFLE-SQ");'),
 ('+hubtab.size()*4+off.size()', '+hubtab.size()*4+shuffletab.size()*4+off.size()')]
 for a,b in replacements:assert source.count(a)==1,(a,source.count(a));source=source.replace(a,b)
 (R/'src/benchmark.cpp').write_text(source)
 (R/'reviews/source_diff.txt').write_text(subprocess.run(['diff','-u',str(OLD/'src/benchmark.cpp'),str(R/'src/benchmark.cpp')],text=True,capture_output=True).stdout)
 permutations=[]
 for ds in DS:
  c=read(OLD/f'configs/{ds}.json');m=read(Path(c['models'])/'model.json');tab=arr(m['files']['hub_blocks'],'<i4').reshape(-1,8);length=(tab>=0).sum(1)
  dest=store/'models'/ds;dest.mkdir(parents=True);maps=[]
  for j in range(32):
   rng=np.random.default_rng(20261029+j);mapping=np.arange(len(tab),dtype='<i4')
   for v in np.unique(length):
    ids=np.flatnonzero(length==v);mapping[ids]=rng.permutation(ids)
   shuffled=tab[mapping];assert np.array_equal((shuffled>=0).sum(1),length);assert sorted(map(tuple,shuffled))==sorted(map(tuple,tab))
   path=dest/f'permutation{j:02d}.i32';mapping.tofile(path);maps.append(dict(seed=20261029+j,path=str(path),sha256=sha(path),fixed_rows=int((mapping==np.arange(len(tab))).sum()),unchanged_content_rows=int((shuffled==tab).all(1).sum())))
  shuffled=tab[arr(dest/'permutation00.i32','<i4')];shuffled.tofile(dest/'shuffled_hub_blocks.i32')
  new=dict(m);new['files']=dict(m['files'],shuffled_hub_blocks=str(dest/'shuffled_hub_blocks.i32'));new['E192_intervention']='only remap complete hub-block rows within row-cardinality strata; seed 20261029'
  dump(dest/'model.json',new)
  permutations.append(dict(dataset=ds,rows=len(tab),row_cardinalities={str(k):v for k,v in collections.Counter(map(int,length)).items()},permutations=maps))
  if ds in ANCHORS:
   c['models']=str(dest);c['K_L']={'100':[160,200,216,232,256,288,320,400]};c['completion_L']={'100':[200]};c['methods']=['GT10','B32','REUSE-PQ','REUSE-SQ','SHUFFLE-SQ','MAIN-SQ'];c['output_dir']=str(store/'results'/ds)
   dump(R/f'configs/{ds}.json',c)
   q=read(R/f'configs/{ds}.json');q['queries']['n']=128;q['test_gt']['n']=128;q['K_L']={'1':[32],'100':[200]};q['completion_L']={'1':[32],'100':[200]};q['output_dir']=str(store/'qualification'/ds);dump(R/f'configs/{ds}.qualification.json',q)
 dump(R/'permutations.json',dict(status='FROZEN_32_REASSIGNMENTS_NO_RESULT_SELECTION',datasets=permutations,formal_permutation_index=0))
 argv=read(OLD/'reviews/build_receipt.json')['argv'];argv=[str(R/'src/benchmark.cpp') if x==str(OLD/'src/benchmark.cpp') else str(store/'benchmark') if x==str(OLD/'storage/benchmark') else x for x in argv]
 bt=time.perf_counter();p=subprocess.run(argv,cwd=REPO,text=True,capture_output=True);(R/'reviews/build.log').write_text(p.stdout+p.stderr);dump(R/'reviews/build.json',dict(argv=argv,returncode=p.returncode,seconds=time.perf_counter()-bt));assert p.returncode==0,p.stderr[-2000:]
 dump(R/'state.json',dict(status='PREPARED_BEFORE_QUALIFICATION',formal_points=39,formal_batches=117,qualification_points=36,default_changed=False))
 print(json.dumps(dict(status='PREPARED_E192',old_seal_files_checked=checked,seconds=time.perf_counter()-t)),flush=True)
if __name__=='__main__':main()
