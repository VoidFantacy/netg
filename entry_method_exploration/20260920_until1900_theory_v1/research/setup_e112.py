import json,time,shutil,hashlib
from pathlib import Path
TB=Path(__file__).resolve().parents[1];ROOT=TB.parents[1];OLD=ROOT/'entry_method_exploration/20260920_until1600_theory_v1';R=TB/'stages/e112_one_hop_hub_design'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ident(p):return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
assert not R.exists();R.mkdir()
for d in ['src','inputs','results','reviews','logs','bin','source_before']:(R/d).mkdir()
for n in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md']:
 p=R/'source_before'/n;p.parent.mkdir(exist_ok=True,parents=True);shutil.copy2(ROOT/n,p)
shutil.copy2(TB/'research/one_hop_design.cpp',R/'src/design.cpp')
shutil.copy2(TB/'research/one_hop_hub_design.md',R/'research.md')
shutil.copy2(TB/'research/e112_protocol_draft.md',R/'protocol.md')
shutil.copy2(TB/'research/run_e112.py',R/'src/run.py')
datasets={};protected=[]
for ds,c in read(OLD/'stages/e107_initialization_factorial/config.locked.json')['datasets'].items():
 mpath=ROOT/'fast_entry_variants'/(ds+'_seed20260828')/'manifest.json';m=read(mpath);s=m['sources'];out=R/'inputs'/ds;out.mkdir()
 qgtq=ROOT/s['aco_queries'];qgtg=ROOT/s['aco_gt'];h=Path(c['fit_input'])/'hub_ids.i32';legacy=ROOT/m['variants']['qgt_cover']['ids_file']
 assert h.read_bytes()==legacy.read_bytes();assert sha(qgtq)==s['aco_queries_sha256'] and sha(qgtg)==s['aco_gt_sha256']
 datasets[ds]=dict(dataset=ds,dimension=c['dimension'],H=c['H'],base_n=c['base_n'],index=c['index'],index_stat=c['index_stat'],QGT_manifest=str(mpath),QGT_queries_source=str(qgtq),QGT_GT_source=str(qgtg),old_hub_ids=str(h),QGT_queries=str(out/'queries.f32'),QGT_GT=str(out/'gt.i32'),development_queries=c['evaluation_queries'],development_GT=c['evaluation_GT'],development_manifest=c['evaluation_manifest'],development_rows=c['source_rows'],default_K1=str(OLD/'stages/e107_initialization_factorial/results'/('main_'+ds)/'DefaultANN/k1_L128/ids.i32'))
 for p in [mpath,qgtq,qgtg,h,legacy,Path(c['evaluation_queries']),Path(c['evaluation_GT']),Path(c['evaluation_manifest']),Path(c['source_rows']),Path(datasets[ds]['default_K1'])]:protected.append(ident(p))
for p in [OLD/'complete.json',OLD/'report.md',OLD/'reviews/completion_audit.json',TB/'config.locked.json']:protected.append(ident(p))
cfg=dict(version='E112_one_hop_hub_design_v1',created_unix=time.time(),datasets=datasets,n_QGT=5000,n_development=4096,K=[1,100],score_denominator=200,methods=['OriginalH','GraphH','FrequencyH'],threads=1,cpu=15,deadline_unix=1789901400,job_seconds_cap=900,max_nonzero_per_dataset=80000000,max_new_bytes=1073741824,max_combined_new_bytes=2147483648,min_free_gib=4,max_rss_gib=40,expected_NSG_calls=0,expected_ANN_calls=0,new_GT=0,new_training=0,new_graphs=0,bootstrap_replicates=10000,bootstrap_seed=20260920,CI_level=.9875,information_gate=dict(each_dataset_F_GraphH_minus_OriginalH_min_pp=2,all_four_comparison_CI_lower_positive=True,each_dataset_default_L128_GT1_conditional_rescue_min_pp=1),previous_phase=str(OLD),data_roles='Same independent QGT5K selects H; all exposed development4096 is read by this runner only after both datasets H frozen; no held-out. Development globally exposed before this stage.')
dump(R/'config.locked.json',cfg);dump(R/'reviews/protected_before.json',protected)
dump(R/'reviews/setup_freeze.json',dict(created_unix=time.time(),files=[ident(R/p) for p in ['config.locked.json','protocol.md','research.md','src/design.cpp','src/run.py']]))
dump(R/'state.json',dict(status='READY_FOR_FROZEN_GRAPH_INFORMATION_GATE',pending=['build','QGT selection','H freeze','development label assessment','independent information gate']))
state=read(TB/'state.json');state.update(stage='E112 frozen one-hop H design information gate',pending=['E112 graph-derived information gate','theory/method decision','19:00 closeout']);dump(TB/'state.json',state)
rel='entry_method_exploration/20260920_until1900_theory_v1/stages/e112_one_hop_hub_design'
for name,text in [('summary.md',f'2026-09-20 E112首行覆盖H设计已冻结准备执行：相同独立QGT5K、相同H815/821、原底图，比较原H、图覆盖贪心H及GT1频率H；先检查图派生信息，不训练画像或执行新NSG。开发4096/集在两集H冻结后由本runner读取，已曝光身份保留。[协议]({rel}/protocol.md)。'),('spec.md',f'2026-09-20 E112新增独立[首行覆盖工具]({rel}/src/design.cpp)：QGT100倒排、全base闭出邻域稀疏整数分数、lazy最大边际贪心、固定H预算与频率控制；原DC检查GT1/GT2严格性。当前尚待执行验收；不修改生产、指标、底层图或默认。')]:
 p=ROOT/name;head,body=p.read_text().split('\n\n',1);p.write_text(head+'\n\n'+text+'\n\n'+body)
print(R)
