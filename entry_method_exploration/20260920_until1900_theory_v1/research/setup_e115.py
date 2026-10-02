from pathlib import Path
import json,hashlib,shutil,time
ROOT=Path('/data/netg/ACSG');TB=Path(__file__).resolve().parents[1];OLD=ROOT/'entry_method_exploration/20260920_until1600_theory_v1/stages/e108_unit_hub_online';R=TB/'stages/e115_score_topology_factorial'
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def ident(p):
 p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
assert not R.exists();assert read(OLD/'complete.json')['status']=='COMPLETE';assert time.time()<read(TB/'config.locked.json')['no_new_search_after_unix']
for d in ['src','bin','models','results','reviews','logs','source_before']:(R/d).mkdir(parents=True,exist_ok=True)
shutil.copytree(OLD/'src/common',R/'src/common',ignore=shutil.ignore_patterns('__pycache__','*.py'))
for name in ['kernels.hpp','search_core.hpp']:shutil.copy2(OLD/'src'/name,R/'src'/name)
shutil.copy2(TB/'research/e115_evaluate.cpp',R/'src/evaluate.cpp');shutil.copy2(TB/'research/e115_protocol.md',R/'protocol.md')
for rel in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md']:
 p=R/'source_before'/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/rel,p)
shutil.copy2(TB/'report.md',R/'reviews/overall_report_before_e115.md')
datasets=[];inputs=[OLD/'complete.json',OLD/'report.md',ROOT/'experiment_history/43_learned_model_factorial.md',ROOT/'experiment_history/45_construction_only_rl.md',ROOT/'experiment_history/87_query_moment_graph_and_branch_stop.md',ROOT/'entry_method_exploration/20260912_learned_model_factorial_v1/protocol.md'];large=[]
for ds in ['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1']:
 p=OLD/'reviews'/('formal_'+ds+'.json');c=read(p);inputs.append(p);P,U=c['methods'][0],c['methods'][2]
 methods=[]
 for name,target,source in [('A_P_GP',P,P),('B_U_GP',U,P),('C_P_GU',P,U),('D_U_GU',U,U)]:
  hybrid=target is not source
  m=dict(name=name,W=target['W'],ids=target['ids'],source_W=source['W'],source_graph=source['graph'],hybrid=hybrid,
   graph=str(R/'models'/ds/(name+'.hnsw')) if hybrid else source['graph'],before=str(R/'reviews'/ds/(name+'.before.hnsw')))
  methods.append(m);inputs.extend(Path(m[k]) for k in ['W','ids','source_W','source_graph'])
 x={k:c[k] for k in ['dataset','dimension','H','base_n','index','base','queries','GT','source_rows','dataset_order','points']}
 x.update(methods=methods,threads=1,reference_E108=str(OLD/'results'/('formal_'+ds)),deadline_unix=read(TB/'config.locked.json')['deadline_unix'],seconds_cap=900)
 datasets.append(x);inputs.extend(Path(c[k]) for k in ['queries','GT','source_rows'])
 for key in ['index','base']:
  f=Path(c[key]);s=f.stat();large.append(dict(path=str(f),bytes=s.st_size,mtime_ns=s.st_mtime_ns,role=key,identity_scope='current stat and inherited E108 manifest; native embedded-base sample parity'))
 for point in c['points']:
  for method in ['GT10Default','UnitHub']:
   base=Path(x['reference_E108'])/('k'+str(point['K']))/(method+'_L'+str(point['L']))
   inputs.extend(base/k for k in ['ids.i32','entry_ids.i32','distances.f32','graph_ndc.u64','route_ndc.u64','complete.json'])
src=[p for p in (R/'src').rglob('*') if p.is_file()];inputs.extend(src)
compile_argv=[s.replace(str(OLD),str(R)) for s in read(OLD/'reviews/jobs.json')[0]['argv']]
inputs.extend(Path(s) for s in compile_argv if s.startswith('/') and Path(s).is_file())
locked=dict(stage='E115 score/topology factorial',created_unix=time.time(),status='LOCKED',protocol=ident(R/'protocol.md'),datasets=datasets,
 expected_diagnostic_NSG=295680,expected_diagnostic_ANN=33024,max_stage_NSG=1045000,max_new_bytes=512*1024**2,threads=1,cpu=15,
 candidate='B_U_GP',controls=['A_P_GP','C_P_GU','D_U_GU'],bootstrap_seed=20260920,bootstrap_replicates=20000,individual_CI=.9875,
 primary_K=[1,100],primary_L=128,minimum_gain_pp=.5,gate='Each dataset: both primary K mean deltas >=0; some K gain >=.5pp; some K corrected lower >0; each K across-L mean delta >=0.',
 compile_argv=compile_argv,source_files=[ident(p) for p in dict.fromkeys(inputs)],large_files=large,
 ordinary_graph_builds=0,new_GT=0,new_training=0,formal_QPS=False,data_role='E105 exposed development, never held-out')
dump(R/'config.locked.json',locked);dump(R/'state.json',dict(status='LOCKED_READY',pending=['compile','hybrid serialization identity','smoke','full mechanism matrix','analysis','decision']))
state=read(TB/'state.json');assert state['active_stage_reserved_NSG_calls']==0;state['stage']='E115 frozen score/topology factorial preparation';state['active_stage_reserved_NSG_calls']=295680;state['pending']=['E115 mechanism and quality gate','19:00 closeout'];dump(TB/'state.json',state)
print(json.dumps(dict(status='LOCKED',stage=str(R),source_files=len(locked['source_files']),NSG_reserved=295680),indent=2))
