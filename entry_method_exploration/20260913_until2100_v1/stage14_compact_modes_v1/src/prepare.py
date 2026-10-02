from common import *
import subprocess,difflib
threads();resources();assert not (O/'config.locked.json').exists();E70=C/'stage11_width_control_v1';E72=C/'stage13_distinct_hub_width_v1'
check(E72/'reviews/final_artifact_freeze.json');paths=[E72/'reviews/final_artifact_freeze.json']
for x in read(E66/'reviews/dependency_stat_verification.json')['sources']:
 s=Path(x['path']).stat();assert (s.st_size,s.st_mtime_ns)==(x['bytes'],x['mtime_ns'])
shutil.copy2(E66/'reviews/dependency_stat_verification.json',O/'reviews/base_graph_identity.json')
models={};costs=[]
for di,ds in enumerate(DS):
 tick=time.monotonic();original=read(E66/'inputs'/ds/'aux.json');paths.append(E66/'inputs'/ds/'aux.json');src=next(m for m in original['methods'] if m['model_name']=='mode3P')
 W=np.fromfile(src['W'],np.float32).reshape(src['hub_count'],original['dim']);mapping=np.fromfile(src['mapping'],np.int32)
 kept=[];lookup={};old_to_new=[]
 for i,(hub,w) in enumerate(zip(mapping,W)):
  key=(int(hub),w.tobytes())
  if key not in lookup:lookup[key]=len(kept);kept.append(i)
  old_to_new.append(lookup[key])
 keep=np.array(kept,np.int32);o2n=np.array(old_to_new,np.int32);small=W[keep];ids=mapping[keep]
 assert len(keep)==[1771,2067][di] and len(set(ids.tolist()))==src['unique_hub_count']
 assert small[o2n].tobytes()==W.tobytes() and ids[o2n].tobytes()==mapping.tobytes()
 assert len(set((int(h),w.tobytes()) for h,w in zip(ids,small)))==len(keep)
 # Also verify compact duplicate3P is exactly the baseline per-hub byte set.
 dup=next(m for m in original['methods'] if m['model_name']=='duplicate3P');dw=np.fromfile(dup['W'],np.float32).reshape(-1,original['dim']);P=next(m for m in original['methods'] if m['model_name']=='baseline')
 assert dw[::3].tobytes()==Path(P['W']).read_bytes() and dw.reshape(-1,3,original['dim'])[:,0].tobytes()==dw.reshape(-1,3,original['dim'])[:,1].tobytes()==dw.reshape(-1,3,original['dim'])[:,2].tobytes()
 dest=O/'models'/ds;dest.mkdir();small.tofile(dest/'W.f32');ids.tofile(dest/'mapping.i32');np.arange(len(keep),dtype=np.int32).tofile(dest/'tie_ids.i32');keep.tofile(dest/'original_slots.i32');o2n.tofile(dest/'old_to_compact.i32')
 m=dict(src,model_name='compact10',name='compact10_L128',W=str(dest/'W.f32'),mapping=str(dest/'mapping.i32'),tie_ids=str(dest/'tie_ids.i32'),hub_count=len(keep),variable_profiles=True,ef_search=10,reference_graph=True,graph_file=str(dest/'graph.hnsw'))
 dump(dest/'model.json',m);models[ds]=m
 rec=dict(dataset=ds,source=src,physical_before=len(W),physical_after=len(keep),removed=len(W)-len(keep),unique_hubs=src['unique_hub_count'],retained_source_bytes_exact=True,all_source_rows_reconstruct_exact=True,complete_per_hub_score_set_invariant=True,duplicate_compaction_equals_P_byte_set=True,preparation_seconds=time.monotonic()-tick,training_updates=0,new_GT=0);dump(dest/'manifest.json',rec);costs.append(rec)
 for m0 in original['methods']:paths += [Path(m0[k]) for k in ['W','mapping','tie_ids','graph_file']]
 for k in ['queries_file','gt_file','row_ids']:paths.append(Path(original[k]))
builds=[]
for name in ['evaluate','build_graph']:
 argv=read(E70/'bin/provenance.json')['argv'];argv=[str(O/'src'/(name+'.cpp')) if x==str(E70/'src/evaluate.cpp') else str(O/'bin'/name) if x==str(E70/'bin/evaluate') else x for x in argv]
 tick=time.monotonic()
 with (O/'logs'/('compile_'+name+'.log')).open('x') as f:p=subprocess.run(argv,stdout=f,stderr=subprocess.STDOUT,timeout=180)
 assert p.returncode==0,name
 builds.append(dict(argv=argv,seconds=time.monotonic()-tick,binary=identity(O/'bin'/name)));paths += [Path(x) for x in argv if Path(x).is_file()]
dump(O/'bin/provenance.json',dict(builds=builds,seconds=sum(x['seconds'] for x in builds)))
diff=''.join(difflib.unified_diff((E70/'src/benchmark_with_nsg.cpp').read_text().splitlines(True),(O/'src/benchmark_with_nsg.cpp').read_text().splitlines(True),fromfile='E70/Policy',tofile='E73/Policy'));(O/'reviews/source_diff.txt').write_text(diff)
assert (O/'src/evaluate.cpp').read_bytes()==(E70/'src/evaluate.cpp').read_bytes()
dump(O/'config.locked.json',dict(datasets=DS,threads=1,CPU=15,NSG_expected=97152,HNSW_expected=96960,builds=2,NSG_hard_cap=100000,output_cap_MiB=64,free_min_GiB=7,latest_launch=1789278300,query_hard_stop=1789278600,per_job_seconds=600,quality_gate='vs P full positive/halves nonnegative/no failure increase; vs fullmode full and halves nonnegative/no failure increase',wall_measurement='after implementation verification, fixed compact candidate including any quality failure, separate E74 protocol'))
paths += list((O/'src').glob('*'))+list((O/'models').rglob('*.*'))+list((O/'bin').glob('*'))+list((R/'ACSG').glob('*.h'))+list((R/'benches/hnswlib').glob('*.h'))+[O/'protocol.md',O/'config.locked.json',O/'reviews/source_diff.txt']
freeze(O/'reviews/prebuild_freeze.json',paths)
for ds in DS:
 dest=O/'models'/ds;tick=time.monotonic();p=subprocess.run([str(O/'bin/build_graph'),str(dest/'model.json'),str(dest/'graph.hnsw')],capture_output=True,text=True,timeout=180)
 (O/'logs'/('graph_'+ds+'.log')).write_text(p.stdout+p.stderr);assert p.returncode==0,p.stderr
 r=json.loads(p.stdout);r['process_seconds']=time.monotonic()-tick;r['graph']=identity(dest/'graph.hnsw');dump(dest/'build.json',r);paths.append(dest/'graph.hnsw')
for di,ds in enumerate(DS):
 original=read(E66/'inputs'/ds/'aux.json');inp=O/'inputs'/ds;inp.mkdir()
 for split,n in [('preflight',128),('aux',7952)]:
  methods=[]
  for name,newname in [('baseline','baseline10'),('mode3P','mode10')]:
   m=dict(next(m for m in original['methods'] if m['model_name']==name),model_name=newname,name=newname+'_L128',ef_search=10,reference_graph=True);methods.append(m)
  methods.append(models[ds]);c=dict(original,methods=methods,split='E73_historical_aux_'+split,num_queries=n,input_total_rows=7952,dataset_order=di,real_call_cap=3*(2*n+16),timing_repeats=0);dump(inp/(split+'.json'),c)
paths+=list((O/'inputs').rglob('*.json'));freeze(O/'reviews/prequery_freeze.json',paths);dump(O/'logs/jobs.json',[]);dump(O/'results/compaction.json',dict(status='PASS',datasets=costs));dump(O/'state.json',dict(status='COMPACT_MODELS_BUILT_UNQUERIED',NSG=0,HNSW=0,builds=2,day_goal_complete=False));resources();print('PREPARED_E73',[(r['physical_before'],r['physical_after']) for r in costs])
