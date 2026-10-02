"""Safe serial-session handoff. Does not complete the day goal or run ANN."""
from pathlib import Path
import json,hashlib,shutil,time,os,re,subprocess,datetime
from zoneinfo import ZoneInfo
C=Path(__file__).resolve().parents[1];R=C.parents[1]
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def ident(p):
 p=Path(p);s=p.stat();return dict(path=str(p),bytes=s.st_size,mtime_ns=s.st_mtime_ns,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
close=C/'reviews/session6_closeout.json';assert not close.exists()
stages=[C/x for x in ['stage16_preserved_levels_v1','stage17_child_support_diagnosis_v1','stage18_child_shrink_factorial_v1','stage19_child_mass_norm_v1']]
costs=[read(stages[i]/'results/cost.json') for i in [0,2,3]]
jobs=[j for s in stages for j in (read(s/'logs/jobs.json') if (s/'logs/jobs.json').exists() else [])]
assert len(jobs)==12 and all(j['status']=='COMPLETE' and j['returncode']==0 and j['peak_threads']==1 and j['affinity']==[15] for j in jobs)
active=[]
for p in Path('/proc').glob('[0-9]*/cmdline'):
 try:
  args=[a.decode(errors='replace') for a in p.read_bytes().split(b'\0') if a];pid=int(p.parent.name)
  if pid==os.getpid() or not args:continue
  exe=Path(args[0]).name
  if exe in ['bash','sh','timeout']:continue
  if 'entry_method_exploration/' not in ' '.join(args):continue
  native=exe in ['evaluate','build_graph','build_levels'] and 'entry_method_exploration/' in args[0]
  scripts=[Path(a).name for a in args[1:3] if a.endswith('.py') and 'entry_method_exploration/' in a]
  workload=exe.startswith('python') and any(re.fullmatch(r'(run|train|deploy|build|build_modes|prepare|analyze|verify_modes|report_session6)(?:_v[0-9]+)?\.py',s) for s in scripts)
  if native or workload:active.append(dict(pid=pid,command=' '.join(args)))
 except (OSError,ProcessLookupError):pass
assert not active,active
nsg=sum(c['NSG'] for c in costs);hnsw=sum(c['HNSW'] for c in costs);builds=sum(c['builds'] for c in costs);native=sum(c['native_job_seconds'] for c in costs)
assert (nsg,hnsw,builds)==(388608,387840,4)
assert sum(j['actual_NSG'] for j in jobs)==nsg
old=read(C/'reviews/session5_closeout.json');pre=read(C/'reviews/session6_precloseout_verification.json');fail=read(C/'session6_report/failure_summary.json')
now=time.time();local=datetime.datetime.fromtimestamp(now,ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S %z');assert now<1789284061
free_bytes=shutil.disk_usage('/data').free;assert free_bytes>=7*(1<<30)+32*(1<<20)
logical=sum(p.stat().st_size for s in stages for p in s.rglob('*') if p.is_file())
physical={}
for s in stages:
 for p in s.rglob('*'):
  if p.is_file() and not p.is_symlink():
   st=p.stat();physical[(st.st_dev,st.st_ino)]=st.st_blocks*512
sup='2026-09-13 14:59; reviews086..101: E75–E78 raw/source/final seals/figures, inventory_v6 and next design source/budget accepted. Session6 aggregate report/seal newly produced.'
nextcmd='env PYTHONDONTWRITEBYTECODE=1 .venv_cpu/bin/python entry_method_exploration/20260913_until2100_v1/src/resume_inspect_v6.py'
construct77=sum(d['construction_seconds'] for d in read(stages[2]/'results/construction.json')['datasets'])
v=dict(status='PASS_SESSION6_SAFE_BOUNDARY',epoch=now,local_time=local,session_safe_exit_deadline=1789284061,day_deadline=1789304400,day_goal_complete=False,
 native_pids=[],active_native_or_training=active,all_native_and_analysis_tools_terminal=True,native_jobs_complete=12,actual_threads=[1]*12,actual_query_cpu=[15]*12,
 session6_NSG_calls=nsg,session6_HNSW_calls=hnsw,session6_new_builds=builds,session6_vector_installs=8,session6_synthetic_builds=4,session6_synthetic_HNSW=512,session6_synthetic_NSG=0,
 day_NSG_calls=old['day_NSG_calls']+nsg,day_HNSW_calls=old['day_HNSW_calls']+hnsw,day_new_builds=old['day_new_builds']+builds,session6_native_job_seconds=native,
 session6_compile_seconds=None,session6_successful_compile_seconds=costs[0]['compile_seconds'],session6_failed_compile_seconds=None,
 compile_reason='E75 first compile failed and elapsed was not recorded; successful retry is measured separately. E77/E78 reused binaries, 0 new compile.',
 E75_NSG=costs[0]['NSG'],E77_NSG=costs[1]['NSG'],E78_NSG=costs[2]['NSG'],micro_graph_build_seconds=sum(c['micro_graph_build_seconds'] for c in costs),
 E77_profile_construction_seconds=construct77,E78_profile_construction_seconds=costs[2]['profile_construction_seconds'],E77_vector_install_seconds=None,E78_vector_install_seconds=costs[2]['vector_install_seconds'],
 vector_install_reason='E77 independent installation elapsed was not recorded; never substitute zero.',
 E76_cached_set_mask_rows=143616,E76_analysis_seconds=read(stages[1]/'reviews/verification.json')['seconds'],
 stage_return_set_mask_rows=sum(read(s/'reviews/verification.json')['set_scored_rows'] for s in [stages[0],stages[2],stages[3]]),
 E75_E77_E78_original_kernel_rows=768,E75_E77_E78_old_control_recovery_rows=95424,
 session6_report_cached_rows=fail['independently_scored_cached_rows'],session6_report_seconds=fail['seconds'],session6_failure_union_queries=454,session6_changed_failure_queries=237,
 session6_development_QPS_points=0,session6_wall_batches=0,day_development_QPS_points=220,day_wall_batches=1100,final_validation_QPS_points=0,
 new_GT=0,gradient_updates=0,auxiliary_feedback_consumed_as_training=True,inherited_E66_profile_training_seconds=30.2860799959999,
 GT_inclusive_inherited_seconds=None,GT_inclusive_inherited_reason='Inherited prior GT/labels/training not remeasured or counted as zero',
 four_new_stage_logical_bytes=logical,four_new_stage_unique_inode_allocated_bytes=sum(physical.values()),free_GiB=free_bytes/(1<<30),free_bytes=free_bytes,
 final_output_reserve_bytes=32*(1<<20),research_available_before_handoff_overhead_bytes=free_bytes-7*(1<<30)-32*(1<<20),
 checked_file_identities_precloseout=pre['checked_files'],supervisor_review_through=sup,candidate_entries=44,
 scope='Historical router_train auxiliary7952 and P-fit already exposed; all selection feedback is training. E34 historical final validation and heldout not opened in session6.',
 next_command=nextcmd,next_design=str(C/'next_stage_design_session6.md'),compile_cost_correction=str(C/'reviews/e75_compile_cost_scope_session6.json'))
assert (v['day_NSG_calls'],v['day_HNSW_calls'],v['day_new_builds'])==(4705364,5116896,352)
# Protect the current root before adding the combined cached report links.
before=C/'reviews/session6_report_source_before';before.mkdir()
for x in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md']:shutil.copy2(R/x,before/x.replace('/','__'))
for x in ['state.json','handoff.md']:shutil.copy2(C/x,before/x)
p=R/'summary.md';t=p.read_text();needle='[E78报告与失败查询]';assert needle in t
t=t.replace(needle,'本会话另以旧raw生成[综合报告](entry_method_exploration/20260913_until2100_v1/session6_report/report.md)：454个任一主配置零命中query，其中237个失败状态变化，完整GT/入口/返回ID及图保留。此汇总0新ANN、0最终反馈，不增加性能点。\n\n'+needle,1);p.write_text(t)
p=R/'s-experiment.md';p.write_text(p.read_text()+'\n2026-09-13第6会话[E75–E78综合报告](entry_method_exploration/20260913_until2100_v1/session6_report/report.md)汇集四阶段和454个失败query并集（237个失败状态变化），0新ANN；各原实验卡片和seal不改。\n')
p=R/'spec.md';p.write_text(p.read_text()+'''

会话6[report_session6](entry_method_exploration/20260913_until2100_v1/src/report_session6.py)是独立的缓存派生脚本：按dataset/router_train source row对齐P/compact/E75/E77 A/E78 mass五配置，独立集合复评分79520旧返回，保存任一配置零GT10命中的454行完整GT10/三入口/返回ID CSV，changed_zero_status标明其中237行变化。图按源行取每集前24个变化行，全表不截断；派生阶段0ANN/构图/最终输入/选型，不能增加QPS点或把全失败行省去。相关原raw/阶段seal保持。
''')
dump(C/'session6_report/figure_review.json',dict(status='PASS',epoch=time.time(),visual='Both 24-row panels viewed; source IDs, five method columns and red zero-hit cells legible; full CSV includes omitted common failures.'))
dump(close,v)
s=read(C/'state.json');s.update(status='SESSION6_COMPLETE_SAFE_HANDOFF',writer='authorized independent serial session 6',stage='E78_COMPLETE',session6_status='COMPLETE_SAFE_HANDOFF',day_goal_complete=False,native_pids=[],
 session6_NSG=nsg,session6_HNSW=hnsw,session6_builds=4,session6_vector_installs=8,session6_native_job_seconds=native,session6_compile_seconds=None,session6_successful_compile_seconds=costs[0]['compile_seconds'],
 session6_final_feedback_used=False,session6_development_QPS_points=0,session6_wall_batches=0,total_new_NSG=v['day_NSG_calls'],total_HNSW=v['day_HNSW_calls'],total_builds=v['day_new_builds'],formal_QPS_points=220,formal_wall_batches=1100,final_validation_QPS_points=0,
 session_safe_boundary_epoch=now,session_safe_boundary_local_time=local,free_GiB=v['free_GiB'],supervisor_review_through=sup,
 candidate_inventory=str(C/'candidate_inventory_v6.json'),handoff=str(C/'handoff.md'),next_design=str(C/'next_stage_design_session6.md'),session6_report=str(C/'session6_report/report.md'),
 session6_failure_union_queries=454,session6_changed_failure_queries=237,next_action='Read handoff/design and run resume_inspect_v6. Stages1..19 complete. New target-space split feasibility needs its own prospective protocol and full disk budget; evening E34 final remains pending.',
 active_json_scope='Historical process samples only; actual native tools terminal0 and no current experiment process.',session6_compile_cost_correction=str(C/'reviews/e75_compile_cost_scope_session6.json'))
dump(C/'state.json',s)
handoff=f'''# 第6独立串行会话安全交接

{local}，E75–E78已完成并封存，**整日21:00用户目标未完成**。本会话在15:21:01安全边界前返回，由监督器接续下一唯一写入/实验会话；不启动并行CLI或子代理。全部12个真实native及构图/合成/分析工具已终止，返回0；当前无遗留实验、训练或分析进程。

## 结果与失败查询

[E75–E78综合报告](session6_report/report.md) · [完整失败query CSV](session6_report/failure_queries.csv) · [失败图](session6_report/failure_queries.png)。五主配置任一零GT10命中的独立(dataset,source row)共454条：Web251/Y203；其中失败状态变化140/97、五配置全失败111/106。全表保留GT10、三入口和返回ID，图每集按源行选前24个变化行；0新ANN的缓存派生，不能当新样本或性能点。

| aux7952 L128主候选相对compact | Web净GT10命中 / 失败净新增 | Y净命中 / 失败净新增 |
|---|---|---|
| E75原slot随机层级恢复 | −59 / +2 | −22 / +3 |
| E77子方向半收缩A | +58 / 0 | −80 / +6 |
| E78固定图质量范数 | 0 / 0 | −44 / +3 |

三者各自预锁门双集未通过，停止对应版本，**无E75/E77/E78新wall**；不扫层级/alpha/指数，不自动选择S/T/uniform。E75恢复层级不恢复邻接；E76低ESS并非共同损伤原因。E77全干预修复部分旧损失，也抹去Web39.63%/Y43.67%的旧正命中，评分/拓扑/交互分列；E78大多保留旧收益仍不能改进。失败不等于没有局部空间，下一机制须实质区别。

[E75报告](stage16_preserved_levels_v1/report.md) · [E76诊断](stage17_child_support_diagnosis_v1/report.md) · [E77四格](stage18_child_shrink_factorial_v1/report.md) · [E78质量权重](stage19_child_mass_norm_v1/report.md)。四份原协议/source/input/result/seal及历史[64](../../experiment_history/64_preserved_compact_levels.md)、[65](../../experiment_history/65_child_profile_support.md)、[66](../../experiment_history/66_child_shrink_factorial.md)、[67](../../experiment_history/67_child_mass_norm.md)保持，原图/GT/脏源/日志不清理。

E73/E74 compact的Y局部信号仍保留：E74五L对P命中+99/+59/+38/+1/+15、失败−10/−7/−4/−1/0，五轮QPS范围均跨零，约1.9%～3.0%只是描述性共同Recall插值；Web L128−23/失败+6。默认未替换，尚无稳定整体改善。最新完整性能图来自同一E74开发批次，不能把本轮L128结果拼接进去。

[E74 QPS–Recall](stage15_compact_wall_v1/figures/recall_qps.png) · [QPS–失败率](stage15_compact_wall_v1/figures/failure_qps.png) · [按L三指标](stage15_compact_wall_v1/figures/three_metrics_by_L.png) · [E74完整报告](stage15_compact_wall_v1/report.md)。晚间最终对照尚未运行。

## 成本、资源与核验

本会话388608 NSG/387840 HNSW、4真实小图build/8坐标安装；合成另4图/512HNSW/0NSG。12native总{native:.9f}秒含load/count/I/O，不能作QPS；新增正式QPS点0。E75成功重编译5.526952531秒，首次失败编译时长未知，因此总编译为null；[独立更正](reviews/e75_compile_cost_scope_session6.json)保留原E75seal。E77独立安装时长未知，E78四安装0.124121362秒；画像构造与图build各成本原件保存。0新GT/梯度，但所有辅助选择反馈计训练；继承E66画像训练30.286秒和历史GT/标签成本未重测，不记零。

今天累计4705364 NSG/5116896 HNSW/352真实build，开发220点/1100wall分属E65/E67/E71/E74独立批次，最终validation点仍0。E75/E77/E78共193920集合/mask、95424旧P/C全字段回归、768原kernel验收；E76重评分143616旧返回，本综合报告另79520旧集合行，全部都是缓存统计而非追加ANN。

CPU15/实际进程和OMP/OpenBLAS/MKL/NUMEXPR/BLIS1线程、方法/数据集全串行。plain/count与原kernel/图W/slots/labels/映射/独立集合验收全部通过。E78阶段19790相同三入口行只计mass对P/C，监督54717另含uniform配对；E77阶段14448只计A对P/C，监督46978另含S/T，口径均正确，不需重跑。

预交接检查{pre['checked_files']}项身份通过，当前free {v['free_GiB']:.4f} GiB。四新阶段逻辑{logical:,} bytes（含引用symlink目标），去重inode分配{v['four_new_stage_unique_inode_allocated_bytes']:,} bytes；不能把逻辑字节直接作额外磁盘消耗。7GiB下限之外至少32MiB专留晚间，当前研究余量在交接开销前约{v['research_available_before_handoff_overhead_bytes']/(1<<20):.2f} MiB。下一阶段必须现场累计预算，不沿用旧64/128MiB限额、不清理旧文件。

监督截至14:59已完成E75–E78所有source/raw/seal/图和inventory_v6、下一设计源码/最终输出预算核验；本会话综合报告和session seal刚生成，可后续只读复核，不等待批准、不重跑已通过项。

## 角色和接续

P-fit20K包含旧4096train/1024monitor；aux7952是router_train[2048:10000]，固定两半与旧cal/audit均历史暴露，任何选型/动作反馈算训练。E34历史validation2000今天尚未打开，只作晚间冻结后最终对照，不回流训练/选型；held-out不自动打开，元数据余行不能证明全项目未观察。

[inventory_v6](candidate_inventory_v6.json)保留旧32配置，新增6主候选配置和6机制控制，共44。S/T/uniform仍不选入best_new；其他失败新方法只能按独立冻结的最终协议展示，不能绕过原增强wall门。E74展示best_new=compact不是全局最终选择。原NSG/base/rawIP/GT和815/821真实H固定，Micro-HNSW只索引这些入口的画像，不是10M底图。

在项目根目录执行：

```bash
{nextcmd}
```

再读[下一阶段设计](next_stage_design_session6.md)及[监督备注](/data/acsg_sessions/20260913_until2100_v1/supervisor_notes.md)。stage1–19全部完成，不重跑旧runner。下一方向是按已有GT10目标向量拆同hub训练组，再聚合原query画像；**尚未实现/训练/构图/查询**。先独立0ANN可行性协议、A/P及旧query分组复现、RAM流式目标与完整磁盘预算，不能把目标分离度当NSG效用。监督只读确认历史E10/E66组内实际仍按query方向拆，这条源代码上的变化成立，但不称文献创新。

若空间不足容纳一组完整新实验，则先准备最终协议/配置/图表，不开半组实验。最终基础Web5方法/Y4方法、五L五轮共45点/225wall/630720NSG；两集各加独立配置是55点/275wall/770880NSG（N=2000），32MiB预留仍需包含输入引用、raw、图、派生和封存的完整manifest预算。选择best_all/best_new先冻结后读E34；规定NSG/Fast/GT10匹配起点/实际新方法同批完整在线wall，GT/count/hash/JSON/build/load在外。

20:00停止新训练，20:40停止新增query，21:00交付完整QPS–Recall/失败率/按L三指标和失败查询报告。新阶段source_before和独立版本/前瞻门，完成后历史→索引→summary、next同步s-target、接口/计量同步spec。现授权足够串行实施，不重复问批准；禁止删除、外发、发布、推送或改Codex配置。本次完成仅是会话安全交接。
'''
(C/'handoff.md').write_text(handoff);assert not (C/'handoff_session6.md').exists();(C/'handoff_session6.md').write_text(handoff)
docs=[R/x for x in ['summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md','experiment_history/67_child_mass_norm.md']]+[C/'next_stage_design_session6.md',C/'handoff.md',C/'handoff_session6.md',C/'session6_report/report.md']
broken=[];checked=0
for p in docs:
 for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if target.startswith(('https:','http:','#','mailto:')):continue
  target=re.sub(r':\d+$','',target.split('#')[0]);checked+=1
  if not (p.parent/target).resolve().exists():broken.append(dict(file=str(p),target=target))
assert not broken,broken
scope=subprocess.run(['git','diff','--check','--','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/67_child_mass_norm.md'],cwd=R,capture_output=True,text=True)
assert scope.returncode==0,scope.stdout+scope.stderr
for p in [R/'experiment_history/67_child_mass_norm.md',C/'next_stage_design_session6.md',C/'handoff_session6.md',C/'session6_report/report.md']:
 assert not any(line.rstrip()!=line for line in p.read_text().splitlines()),str(p)
dump(C/'reviews/session6_document_verification.json',dict(status='PASS',links_checked=checked,broken=[],scoped_git_diff_check=0,new_documents_trailing_space_check=True,day_goal_complete=False))
snap=C/'reviews/session6_snapshot';snap.mkdir()
for x in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md']:shutil.copy2(R/x,snap/x.replace('/','__'))
for x in ['state.json','handoff.md']:shutil.copy2(C/x,snap/x)
paths=[p for folder in [snap,before,C/'session6_report'] for p in sorted(folder.rglob('*')) if p.is_file()]
paths += [C/'handoff_session6.md',close,C/'next_stage_design_session6.md',C/'candidate_inventory_v6.json',C/'reviews/session6_inventory_verification.json',C/'reviews/e75_compile_cost_scope_session6.json',C/'reviews/session6_precloseout_verification.json',C/'reviews/session6_document_verification.json',C/'src/inventory_session6.py',C/'src/resume_inspect_v6.py',C/'src/close_stage19.py',C/'src/report_session6.py',Path(__file__).resolve()]
seal=C/'reviews/session6_final_artifact_freeze.json';assert not seal.exists()
dump(seal,dict(status='FROZEN_SESSION6_SAFE_HANDOFF_DAY_NOT_COMPLETE',epoch=time.time(),files=[ident(p) for p in paths]))
print(json.dumps(dict(status='SESSION6_SEALED',files=len(paths),bytes=sum(p.stat().st_size for p in paths),local_time=local,NSG=nsg,HNSW=hnsw,native_seconds=native,free_GiB=v['free_GiB'],document_links_checked=checked,active=[]),ensure_ascii=False))
