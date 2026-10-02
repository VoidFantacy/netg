import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='1'
os.sched_setaffinity(0,{15})
from pathlib import Path
import json,hashlib,shutil,time
import numpy as np
ROOT=Path('/data/netg/ACSG');TB=Path(__file__).resolve().parents[1];OLD=ROOT/'entry_method_exploration/20260920_until1600_theory_v1';E104=ROOT/'entry_method_exploration/20260920_query_representation_pilot_v1';R=TB/'stages/e113_comparison_support'
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(16<<20),b''):h.update(b)
 return h.hexdigest()
def ident(p):p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
assert not R.exists();R.mkdir();[ (R/d).mkdir() for d in ['src','inputs','results','reviews','logs','bin'] ]
before=[]
for rel in ['summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md']:
 p=ROOT/rel;dest=R/'reviews/source_before'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest);before.append(dict(**ident(p),snapshot=str(dest)))
dump(R/'reviews/source_before.json',before)
for source,dest in [('e113_protocol.md','protocol.md'),('comparison_support.cpp','src/evaluate.cpp'),('comparison_recorder.hpp','src/comparison_recorder.hpp'),('run_e113.py','src/run.py')]:shutil.copy2(TB/'research'/source,R/dest)
original=OLD/'stages/e107_initialization_factorial/src/kernels.hpp';assert sha(original)==sha(E104/'src/kernels.hpp')
s=original.read_text().split('\nusing KernelCall=',1)[0];s=s.replace('ResearchKernel','TraceKernel');s=s.replace('    int ntotal;','    int ntotal;\n    ComparisonRecorder recorder;')
needle='        std::sort(pool.begin(),pool.begin()+live);';assert s.count(needle)==1;s=s.replace(needle,'        std::sort(pool.begin(),pool.begin()+live,[&](const Neighbor&a,const Neighbor&b){recorder.compare(a.id,a.distance,b.id,b.distance,1);return a<b;});')
needle='                    if(live>=L&&distance>=pool[L-1].distance)return;';assert s.count(needle)==1;s=s.replace(needle,'                    if(live>=L)recorder.compare(id,distance,pool[L-1].id,pool[L-1].distance,2);\n'+needle)
needle='acsg::detail::insert_into_pool_live(pool.data(),L,compact?std::min(L,live):L,Neighbor(id,distance,true))';assert s.count(needle)==1;s=s.replace(needle,'traced_insert_into_pool_live(pool.data(),L,compact?std::min(L,live):L,Neighbor(id,distance,true),recorder)')
(R/'src/trace_kernel.hpp').write_text(s)
dump(R/'reviews/mechanical_kernel_generation.json',dict(original=ident(original),E104_kernel=ident(E104/'src/kernels.hpp'),generated=ident(R/'src/trace_kernel.hpp'),changes=['class rename and recorder member','initial sort pure comparator wrapper','pool bound observer','identical local insertion with comparison observers','remove duplicated global aliases and make_spans']))
datasets={};sources=[];prepared=[]
for ds in read(E104/'config.locked.json')['datasets']:
 cpath=E104/'inputs'/ds/'fit/config.json';c=read(cpath);p=R/'inputs'/ds;p.mkdir();n=c['n'];assert n==2048;d=c['dimension'];lab=E104/'labels'/ds/'fit_labels';ids=np.fromfile(c['hub_ids'],'<i4');triples=np.fromfile(lab/'triples.i32','<i4').reshape(n,56,3);baseline=np.fromfile(lab/'baseline_slots.i32','<i4').reshape(n,2)[:,0];teachers=np.fromfile(lab/'teacher_mask.u8','u1').reshape(n,56).astype(bool)
 h1=np.fromfile(lab/'k1.hits.u8','u1').reshape(n,56).astype('i4');h100=np.fromfile(lab/'k100.hits.u8','u1').reshape(n,56).astype('i4');score=100*h1+h100;assert np.array_equal(teachers,score==score.max(axis=1,keepdims=True));slots=np.empty((n,2),dtype='<i4');slots[:,0]=baseline
 for i in range(n):
  anchor=set(triples[i,baseline[i]].tolist());slots[i,1]=min(np.flatnonzero(teachers[i]),key=lambda j:(3-len(anchor&set(triples[i,j].tolist())),tuple(ids[triples[i,j]].tolist())))
 entries=ids[triples[np.arange(n)[:,None],slots]];assert np.array_equal(entries[:,0],np.fromfile(lab/'anchor_entries.i32','<i4').reshape(n,3));assert np.all(np.diff(entries,axis=2)>0)
 slots.tofile(p/'slots.i32');entries.astype('<i4').tofile(p/'entries.i32');shutil.copy2(c['queries'],p/'queries.f32');gt=np.fromfile(c['gt'],'<i8').reshape(n,100);gt[:,0].astype('<i4').tofile(p/'GT1.i32');teachers.sum(axis=1).astype('<u2').tofile(p/'teacher_count.u16')
 config=dict(dataset=ds,n=n,dimension=d,base_n=c['base_n'],H=len(ids),index=c['index'],index_stat=dict(bytes=Path(c['index']).stat().st_size,mtime_ns=Path(c['index']).stat().st_mtime_ns),queries=str(p/'queries.f32'),entries=str(p/'entries.i32'),GT1=str(p/'GT1.i32'),slots=str(p/'slots.i32'),expected={},deadline_unix=1789901400,seconds_cap=890,max_pairs=30000000)
 source_paths=[cpath,Path(c['queries']),Path(c['gt']),Path(c['hub_ids']),lab/'triples.i32',lab/'baseline_slots.i32',lab/'teacher_mask.u8',lab/'k1.hits.u8',lab/'k100.hits.u8',lab/'anchor_entries.i32']
 for K in [1,100]:
  k=str(K);config['expected'][k]={}
  for suffix,dtype,shape,field in [('ids.i32','<i4',(n,56,K),'ids'),('distances.f32','<f4',(n,56,K),'distances'),('ndc.u64','<u8',(n,56),'ndc')]:
   src=lab/f'k{K}.{suffix}';a=np.memmap(src,dtype=dtype,mode='r',shape=shape);selected=np.asarray(a[np.arange(n)[:,None],slots]);selected.tofile(p/f'k{K}.{suffix}');config['expected'][k][field]=str(p/f'k{K}.{suffix}');source_paths.append(src)
 sources.extend(ident(s) for s in source_paths);prepared.extend(ident(s) for s in p.iterdir() if s.is_file());datasets[ds]=config
 dump(R/'reviews'/('prepared_'+ds+'.json'),dict(n=n,roles=['baseline','nearest_maximum_teacher'],same_baseline_teacher_queries=int(np.all(entries[:,0]==entries[:,1],axis=1).sum()),teacher_selection_rule='maximum cached equal-K utility, max baseline overlap, then real ID lexicographic',no_cal_or_development_payload_access=True))
dump(R/'reviews/input_sources.json',dict(created_unix=time.time(),files=sources))
cfg=dict(version='E113_comparison_support_v1',created_unix=time.time(),datasets=datasets,threads=1,cpu=15,expected_NSG_calls=32768,max_NSG_calls=36000,max_stage_bytes=800*2**20,max_combined_bytes=2*2**30,min_free_gib=4,max_rss_gib=40,deadline_unix=1789901400,seconds_per_dataset=900,previous_phase=str(OLD),feature_gate=dict(dictionary_size=32,min_query_support=32,min_positive_distinct_GT1=8,min_negative_distinct_GT1=8,min_query_coverage=.5,both_datasets_required=True),new_ANN=0,new_GT=0,new_graphs=0,new_training=0,scope='Fit-only shared-comparison information; no deployable policy or QPS')
dump(R/'config.locked.json',cfg)
protected=[ROOT/'ACSG/detail/CandidatePool.h',ROOT/'ACSG/ACSG.h',original,OLD/'stages/e107_initialization_factorial/src/search_core.hpp',E104/'config.locked.json',E104/'reviews/completion_audit.json',OLD/'complete.json',OLD/'report.md',TB/'stages/e112_one_hop_hub_design/complete.json']
dump(R/'reviews/protected_before.json',[ident(p) for p in protected]);dump(R/'reviews/setup_freeze.json',dict(files=[ident(R/p) for p in ['protocol.md','config.locked.json','src/evaluate.cpp','src/comparison_recorder.hpp','src/trace_kernel.hpp','src/run.py']]+prepared))
dump(R/'state.json',dict(status='READY_FROZEN',pending=['compile','two serial fit trace jobs','shared support analysis','stage closeout']))
state=read(TB/'state.json');state.update(stage='E113 frozen actual-comparison shared support diagnostic',active_stage_reserved_NSG_calls=32768);dump(TB/'state.json',state)
for name,text in [('summary.md','2026-09-20 E113训练内比较对支持诊断已冻结：原E104 fit2048/集、固定baseline与最优teacher动作，记录真实有限池数值比较，先核验跨目标重复支持；预计32768重复NSG核验，0新ANN/GT/图/模型，当前待执行。[协议](entry_method_exploration/20260920_until1900_theory_v1/stages/e113_comparison_support/protocol.md)。'),('spec.md','2026-09-20 E113新增独立比较记录fork：保持原pool插入/排序/拒绝语义，记录实际节点比较对及符号；原kernel与E104 SHA一致，全K1/K100控制及历史输出parity为执行前置。尚待执行验收，不修改生产或默认。[协议](entry_method_exploration/20260920_until1900_theory_v1/stages/e113_comparison_support/protocol.md)。')]:
 p=ROOT/name;head,rest=p.read_text().split('\n\n',1);p.write_text(head+'\n\n'+text+'\n\n'+rest)
p=ROOT/'s-target.md';s=p.read_text().replace('尚无新模型或运行队列；','E113比较对支持诊断已冻结，先完整parity/支持门，无新模型队列；',1);p.write_text(s)
print(json.dumps(dict(status='READY_FROZEN',source_files=len(sources),prepared_files=len(prepared),NSG_calls_reserved=32768),indent=2))
