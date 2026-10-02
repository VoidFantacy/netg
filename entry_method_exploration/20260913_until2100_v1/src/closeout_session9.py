from pathlib import Path
import json,time,hashlib,shutil,datetime,csv,os
C=Path(__file__).resolve().parents[1];R=C.parents[1];B=C/'session9_closeout';assert (B/'state_before.json').exists();assert not (B/'terminal_ledger.json').exists()
roots=['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md']
for f in roots:shutil.copy2(R/f,B/'source_before'/f)
shutil.copy2(C/'state.json',B/'state_before.json');shutil.copy2(C/'handoff.md',B/'handoff_before.md')
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def ident(p):
 p=Path(p);s=p.stat();h=hashlib.sha256()
 with p.open('rb') as f:
  for z in iter(lambda:f.read(8<<20),b''):h.update(z)
 return dict(path=str(p),bytes=s.st_size,mtime_ns=s.st_mtime_ns,sha256=h.hexdigest())
ST=['stage27_edge_utility_v1','stage28_utility_proposals_v1','stage29_proposal_rank_diagnosis_v1'];cache={};verified=0
for stage in ST:
 for seal in [C/stage/'reviews/final_artifact_freeze.json']+([C/stage/'reviews/supplement_freeze.json'] if stage==ST[-1] else []):
  for x in read(seal)['files']:
   p=Path(x['path']);s=p.stat();key=(str(p),s.st_size,s.st_mtime_ns)
   if key not in cache:cache[key]=ident(p)['sha256']
   assert (s.st_size,s.st_mtime_ns,cache[key])==(x['bytes'],x['mtime_ns'],x['sha256']),str(p);verified+=1
old=read(C/'candidate_inventory_v9.json');new=read(C/'candidate_inventory_v10.json');assert new['candidates'][:60]==old['candidates'] and len(new['candidates'])==68
for row in new['candidates']:
 for k in ['W','graph','mapping','tie_ids','evaluator','development_configuration','protocol','source_protocol']:
  x=row.get(k)
  if isinstance(x,dict) and 'sha256' in x:assert all(ident(x['path'])[field]==value for field,value in x.items() if field in ['path','bytes','mtime_ns','sha256']),(row['name'],k)
newrows=new['candidates'][60:];assert sum(r['selectable_for_final'] for r in newrows)==3 and sum(r['kind']=='mechanism_control' for r in newrows)==4 and sum(r['kind']=='zero_update_alias' for r in newrows)==1
jobs=[];ns=0;hs=0
sessions=[[75345,33265,91148,15054,57030,91000],[15985,46120,31966,56187,23741,12726]]
for si,stage in enumerate(ST[:2]):
 o=C/stage;cost=read(o/'results/cost.json');ns+=cost['NSG'];hs+=cost['HNSW'];jj=read(o/'logs/training_jobs.json')+read(o/'logs/jobs.json');assert len(jj)==6
 assert sum(j['actual_NSG'] for j in jj)==cost['NSG']
 for j,tool in zip(jj,sessions[si]):
  assert j['status']=='COMPLETE' and j['returncode']==0 and j['affinity']==[15] and j.get('actual_threads',j.get('peak_threads'))==1
  jobs.append(dict(stage=stage,dataset=j['dataset'],split=j.get('split','training'),tool_session=tool,actual_tool_terminal_observed=True,returncode=0,started_at=j['started_at'],completed_at=j['completed_at'],actual_NSG=j['actual_NSG'],threads=1,CPU=15))
ordered=sorted(jobs,key=lambda j:j['started_at']);assert all(a['completed_at']<=b['started_at'] for a,b in zip(ordered,ordered[1:]));assert (ns,hs)==(365054,7756544)
dump(B/'terminal_ledger.json',dict(status='PASS',jobs=ordered,compile_tool_session=91960,compile_terminal_exit=0,all_other_verifier_report_tools_terminal=True,latest_report_tool_session=68002,latest_report_exit=0,pending_tools=[],process_scope='Actual tool completion and experiment ledgers establish owned job completion. Isolated /proc cannot establish host-wide absence; supervisor observes host independently.'))
dump(B/'verification.json',dict(status='PASS',sealed_identity_records=verified,unique_sealed_files=len(cache),all_68_inventory_file_identities=True,old_60_candidate_objects_preserved=True,new_main_nonzero=3,new_controls=4,new_main_zero_alias=1,terminal_native_jobs=12,serial_nonoverlap=True,NSG=ns,HNSW=hs,day_NSG=5360806+ns,day_HNSW=5843808+hs,ordinary_builds=0,new_QPS=0,final_payload_read=False))
nexttext='''# 第9会话后下一阶段（设计，未执行）

E86/E87已完整停止；E88为缓存诊断。先读handoff_session9、root docs和监督记录，再运行resume_inspect_v9.py。不得重跑旧阶段。

优先完成晚间最终对照准备：候选v10保留全部旧60对象，新增3个非零主候选、1个Y零更新别名和4个机制控制。目录不等于选中；E87 Y零更新与所有neighbor控制不得冒充best_new。基于已暴露开发反馈写独立最终协议，冻结best_all/best_new具体配置/模型/图身份、别名去重、选择规则和可报告结论，然后才能读E34历史validation2000输入。最终结果不回流训练/选型，held-out未授权。

元数据草稿session9_final_preparation已核对原NSG、Fast、匹配GT10、Web额外GT10-soft的模型字节、E73完整wall评测器和2000行规模。不是runner。实际每点1warm+5wholewall+1count+16原kernel，14016 NSG；profile每点14000 HNSW。45/55点示例630720/770880 NSG和225/275wall，实际矩阵重算。保留同批所有方法、五L五轮轮换CPU15/线程1；输出完整route+NSG+输出wall，计时外GT/count/hash/序列化/load/build。旧E74的2048/112640/8192等常数及旧deadline必须改成参数；最终query不同，不能套旧aux前缀回归。最终输入打开前冻结选择，之后只做正确性/完整性修正，不能为阳性重新选方法。

若仍有时间开实质新方向，E88支持画像排序是当前提议的限制：先在已暴露fit确认真正优于compact的P独有hub在画像分数中的竞争性，按全部fit统计损伤/支持分布，再考虑固定预算的离线画像/得分目标。只看某条边的支持query会遗漏Web的支持外损伤；更好P完整策略也不等于单目标好。新的动作/训练信号必须对应最终实际三入口，并留全fit/冻结aux接受；不要直接放宽E87支持数/边数/阈值。该方向尚未实现/拟合/评测，不重启旧runner。

硬截止：20:00停新训练、20:40停新增查询、21:00报告。始终串行唯一写者，原底层NSG/base/GT/rawIP不变；大文件只/data，不清旧artifact。当前72MiB晚间与交接预留继续保持，累计新输出以session9_closeout/resource_accounting.json为准。
'''
(C/'next_stage_design_session9.md').write_text(nexttext)
p=R/'summary.md';p.write_text(p.read_text()+'\n第9会话收口：E86–E88完成，综合报告和413条失败全表见[session9 report](entry_method_exploration/20260913_until2100_v1/session9_report/report.md)。候选v10共68对象，旧60保持；新增3非零主候选/1零更新别名/4控制，尚未最终选型。安全接续见[handoff](entry_method_exploration/20260913_until2100_v1/handoff_session9.md)，整日目标未完成。\n')
p=R/'s-target.md';p.write_text(p.read_text()+'\n第9会话E86–E88已收口；下一会话从[handoff_session9](entry_method_exploration/20260913_until2100_v1/handoff_session9.md)和[设计说明](entry_method_exploration/20260913_until2100_v1/next_stage_design_session9.md)接续。原研究阶段均停止，不直接重跑；独立晚间最终协议优先。\n')
now=time.time();local=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat();state=read(C/'state.json');state.update(status='SESSION9_COMPLETE_SAFE_HANDOFF_DAY_ACTIVE',session9_status='COMPLETE_SAFE_HANDOFF',stage='E88_complete',stage27_status='COMPLETE_EDGE_UTILITY_NO_GATE',stage28_status='COMPLETE_UTILITY_PROPOSALS_NO_GATE',stage29_status='COMPLETE_CACHED_PROPOSAL_RANK_DIAGNOSIS',session9_NSG=ns,session9_HNSW=hs,session9_builds=0,session9_graph_supervised_fits=4,session9_edge_installs=10,session9_zero_update_copies=2,session9_final_feedback_used=False,session9_development_QPS_points=0,session9_wall_batches=0,session9_compile_seconds=13.345122270,session9_train_aux_operation_seconds=412.247027098,session9_failure_union_queries=413,session9_changed_failure_queries=173,session9_report=str(C/'session9_report/report.md'),session_safe_boundary_epoch=now,session_safe_boundary_local_time=local,day_goal_complete=False,native_pids=[],offline_pids=[],pending_tool_sessions=[],offline_tool_status='TERMINAL_EXIT0',offline_tool_session=None,candidate_inventory=str(C/'candidate_inventory_v10.json'),handoff=str(C/'handoff.md'),next_design=str(C/'next_stage_design_session9.md'),next_action='Read handoff_session9 and supervisor notes; run read-only resume_inspect_v9. E86-E88 complete; prioritize freezing actual final candidates and preparing E34 complete2000 matrix. No final payload or heldout opened.',supervisor_review_through='2026-09-13 17:59:58 reviews144..157: E86/E87 full source/training/aux/seals and E88 raw diagnosis verified; later notes apply to report/inventory/closeout.')
dump(C/'state.json',state)
for f in roots:shutil.copy2(R/f,B/'root_after'/f)
# Conservative complete session9 accounting: all stage/report/preparation/closeout files even copy2-retained old mtimes, plus all other campaign files newly written this session and current root/history files.
folders=[C/x for x in ST+['session9_report','session9_final_preparation','session9_closeout']];files=set(p for o in folders for p in o.rglob('*') if p.is_file() and not p.is_symlink());files|={p for p in C.rglob('*') if p.is_file() and not p.is_symlink() and p.stat().st_mtime>=1789290509.9};files|={R/f for f in roots};files|={R/'experiment_history'/f for f in ['README.md','75_edge_utility.md','76_utility_proposals.md','77_proposal_rank_diagnosis.md']}
used=sum(p.stat().st_size for p in files);free=shutil.disk_usage('/data').free;assert used<192*2**20 and free-72*2**20>6.55*2**30
remaining=max(0,192*2**20-used);assert free-remaining-72*2**20>6.55*2**30
resource=dict(status='PASS',epoch=time.time(),accounted_bytes=used,accounted_MiB=used/2**20,free_bytes=free,free_GiB=free/2**30,remaining_session_cap_bytes=remaining,evening_reserve_MiB=64,handoff_reserve_MiB=8,free_floor_GiB=6.55,after_remaining_cap_and_reserves_GiB=(free-remaining-72*2**20)/2**30,scope='Conservative cumulative output including retained-mtime snapshots, stage seals, report/preparation/closeout, new campaign scripts/reviews/inventory/state and current roots/history; final seal additions below reserved8MiB.',files=[dict(path=str(p),bytes=p.stat().st_size) for p in sorted(files)])
dump(B/'resource_accounting.json',resource)
handoff=f'''# 第9串行会话交接（E86–E88完成，整日未完成）

安全边界{local}，本会话最迟18:23:29已遵守。唯一写者可退出交监督器接续；无本会话待接管原生任务/未结束工具。12个训练/查询任务与编译均实际terminal0；进程命名空间限制见terminal_ledger，不把局部/proc当全主机无任务证明。

E86真实单边效用筛选几何候选：Web29/Y3接受边，fit并图+191/+13；aux对compact+18/−4命中，失败−3/0，Web对P−41/失败+8，双集门失败。E87从完整P更好策略提议新目标，Web53/Y9候选，16/0接受，fit并图+94/0；aux对compact+16/0、失败−3/0，Web对P−43/+8。Y两导出为原compact零更新，+120/−13对P全部继承原compact。两个旧规则停止，0新QPS。

E88缓存诊断：167/19被测边支持query中，目标固定集前三资格19/0、实际选中19/0、NSG改善17/0。Y10个目标已在七slot仍无前三资格。只描述这组支持query/固定返回集，不推断遍历与一般headroom。完整1951事件中1765未测实际格留空。原报告“无近界”范围写宽，report_v2及supplement更正：186被测0近界，全1951另2个未测近界；原始表/封存保持。

新增NSG365054/HNSW7756544，10非零边安装+2零更新副本，4离线筛边拟合，0普通build/GT/梯度；两版训练/辅助操作412.247s含load/count/cache/I/O，不作QPS。E86编译13.345s，E87复用0编译。日累计NSG5725860/HNSW13600352/普通build360；既有开发QPS220点/1100wall属不同历史批次，最终QPS0。综合413失败并集/173状态变化/2478六方法完整单元复算通过。

累计新输出当前保守{used/2**20:.3f}MiB，free{free/2**30:.3f}GiB；192MiB会话cap和72MiB晚间/交接余量检查通过。以resource_accounting及下一会话现场stat为准，不清理历史。E86/E87各完整sealed；E88原seal+scope supplement。源/根文档before与after均保留，history75–77已同步。

角色：fit20K router_train[10000:30000]含旧train4096/monitor1024；aux[2048:10000]和两半、旧cal/audit历史暴露，接受/诊断算训练。E34历史validation2000输入载荷未读，本会话只读配置/模型身份和query/GT/row stat；查历史23汇总在E87模型冻结后且未回流选择。held-out未开。

[综合报告](session9_report/report.md) · [失败图](session9_report/failure_queries.png) · [完整失败CSV](session9_report/failure_queries.csv) · [最近完整QPS](stage15_compact_wall_v1/report.md) · [E88修正版](stage29_proposal_rank_diagnosis_v1/report_v2.md) · [候选v10](candidate_inventory_v10.json) · [最终准备件](session9_final_preparation/readme.md) · [下一设计](next_stage_design_session9.md) · [任务账](session9_closeout/terminal_ledger.json) · [成本核对](session9_closeout/resource_accounting.json)。

下一条安全命令（只读，不重跑ANN、不打开最终载荷）：

```bash
cd /data/netg/ACSG
python3 entry_method_exploration/20260913_until2100_v1/src/resume_inspect_v9.py
```

随后完整读取AGENTS/summary/spec/s-target/s-experiment，按历史75–77和原协议/配置/结果定位，查最新/data/acsg_sessions/20260913_until2100_v1/supervisor_notes.md。优先独立冻结best_all/best_new实际候选与别名、矩阵/选择规则，再打开最终E34。候选目录不是最终选择；Y E87零更新和控制禁止充新方法。2000行完整wall预算与E73兼容接口已核验，旧2048 runner不可直接复用。若新画像/得分方向有实质证据，独立前瞻协议且不回流最终反馈。20:00停新训练、20:40停新增query、21:00完整报告。
'''
(C/'handoff_session9.md').write_text(handoff);(C/'handoff.md').write_text(handoff);state['free_GiB']=free/2**30;dump(C/'state.json',state);dump(B/'state_after.json',state);shutil.copy2('/data/acsg_sessions/20260913_until2100_v1/supervisor_notes.md',B/'supervisor_notes_observed.md')
print('SESSION9_CLOSEOUT_PASS',used/2**20,free/2**30,verified)
