from pathlib import Path
import json,hashlib,shutil,time,csv,datetime
R=Path('/data/netg/ACSG');C=Path(__file__).resolve().parents[1];B=C/'session7_closeout';B.mkdir();(B/'source_before').mkdir();(B/'root_after').mkdir()
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def identity(p):
 p=Path(p);s=p.stat();return dict(path=str(p),bytes=s.st_size,mtime_ns=s.st_mtime_ns,sha256=sha(p))
roots=['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md']
for n in roots:shutil.copy2(R/n,B/'source_before'/n)
for n in ['handoff.md','state.json']:shutil.copy2(C/n,B/'source_before'/n)
shutil.copy2(R/'experiment_history/69_hub_conditioned_targets.md',B/'source_before/69_hub_conditioned_targets.md');shutil.copy2(R/'experiment_history/70_joint_view_partition.md',B/'source_before/70_joint_view_partition.md')
stages=['stage20_target_space_modes_v1','stage21_hub_conditioned_targets_v1','stage22_joint_view_partition_v1'];costs=[read(C/s/'results/cost.json') for s in stages];gates=[read(C/s/'results/gate.json') for s in stages];assert all(not g['wall_measurement_allowed'] for g in gates)
for s in stages:
 jobs=read(C/s/'logs/jobs.json');assert len(jobs)==4 and all(j['status']=='COMPLETE' and j['returncode']==0 and j['peak_threads']==1 and j['affinity']==[15] for j in jobs)
v=read(C/'session7_report/verification.json');nf=sum(x['any_zero'] for x in v['union'].values());nc=sum(x['changed_zero'] for x in v['union'].values());assert nf==503 and nc==319
with (C/stages[2]/'results/paired.csv').open() as f:pair=list(csv.DictReader(f))
yhalves=[next(int(r['net_hits']) for r in pair if r['dataset'].startswith('yandex') and r['candidate']=='joint10' and r['reference']=='baseline10' and r['split']==s) for s in ['first_half','second_half']]
p=C/'session7_report/report.md';p.write_text(p.read_text()+f'\nE81局部信号单独保留：Yandex相对P+58命中/失败−11，相对E80+70/−8，但相对compact−62/+2，对P两半{yhalves[0]:+d}/{yhalves[1]:+d}。联合分组保留compact正收益Web601/820、Y396/545，高于E80的356/820、183/545；同时减少了旧损失修复，净结果仍未过门。联合目标J提升不等于检索效用。Web仍对P−78/+8。\n\nE81独立目标检查首版因重建布局/归约路径未匹配而在F哈希处失败，原件保留；v2在原严格digest和独立数值容差下通过，无模型/ANN重跑。首次检查耗时未恢复；v2和分析耗时见阶段验收，绘图/文档耗时未单独计量。[检查器更正](../stage22_joint_view_partition_v1/reviews/objective_checker_correction.json)。\n')
p=R/'summary.md';p.write_text(p.read_text()+f'\n第7会话综合汇报：五主方法零命中并集{nf}条、失败状态变化{nc}条，全量GT10/入口/返回保存；E81 Yandex对P+58/失败−11、对条件目标+70/−8是局部修复，仍不及compact且对P两半{yhalves[0]:+d}/{yhalves[1]:+d}，原门失败。[综合报告](entry_method_exploration/20260913_until2100_v1/session7_report/report.md) · [失败图](entry_method_exploration/20260913_until2100_v1/session7_report/failure_queries.png)。E80封存图的标签留白修正版在综合报告，原图及seal不动。E81独立检查器修正不改任何模型/查询结果。\n')
p=R/'s-target.md';p.write_text(p.read_text()+'\n第7会话接续：三个原门均失败，E81 Yandex局部修复与原compact信号保留。[下一未执行设计](entry_method_exploration/20260913_until2100_v1/next_stage_design_session7.md)按新bank完整排名/近似误差这个待证问题给出原证据回溯入口，需独立协议，不直接扫ef/权重。库存v8是52对象目录，尚未冻结晚间最终候选。用resume_inspect_v7做增量封存检查，不重复已验旧19阶段的全量扫描。\n')
p=R/'experiment_history/69_hub_conditioned_targets.md';p.write_text(p.read_text()+'\n2026-09-13 第7会话显示修正：原E80图及finalseal保留，Yandex零柱标注留白修正版见[session7独立图](../entry_method_exploration/20260913_until2100_v1/session7_report/conditional_modes_v2.png)。只修改新图轴范围，0ANN。\n')
p=R/'experiment_history/70_joint_view_partition.md';p.write_text(p.read_text()+f'\n第7会话五主方法综合失败并集{nf}条、变化{nc}条，缓存质量诊断无新增ANN/QPS，见[综合报告](../entry_method_exploration/20260913_until2100_v1/session7_report/report.md)。\n')
now=time.time();free=shutil.disk_usage('/data').free;assert free>=6.8*(1<<30)+68*(1<<20);ns=sum(x['NSG'] for x in costs);hs=sum(x['HNSW'] for x in costs);bs=sum(x['builds'] for x in costs);native=sum(x['native_job_seconds'] for x in costs);offline=sum(x['offline_total_seconds'] for x in costs)
newpaths=[p for s in stages for p in (C/s).rglob('*') if p.is_file() and not p.is_symlink()];logical=sum(p.stat().st_size for p in newpaths);inodes={}
for p in newpaths:s=p.stat();inodes[(s.st_dev,s.st_ino)]=s.st_size
ledger=dict(status='ALL_SESSION_OWNED_TOOLS_TERMINAL',E79_E80='Actual native tools and offline/build/report/close accepted by supervisor107/108/111/112/113; current jobs each returncode0.',E81=dict(offline=dict(session=76999,exit_code=0),native=[dict(session=s,exit_code=0) for s in [87414,98966,92152,2824]],analyze=dict(session=62034,exit_code=0),independent_checker_original=dict(session=92887,exit_code=1,preserved=True),independent_checker_v2=dict(session=83045,exit_code=0),report=dict(session=58749,exit_code=0),build_and_close='synchronous tool exit0'),combined_report=dict(session=5476,exit_code=0),scope='Exec PID namespaces are isolated. Every session-owned long job was resumed to actual terminal; native thread/affinity checked within its original namespace. Supervisor host-wide check is separate.',pending_tool_sessions=[],new_ANN_after_E81=0);dump(B/'terminal_ledger.json',ledger)
dump(B/'cost.json',dict(NSG=ns,HNSW=hs,builds=bs,offline_fits=8,old_Q_reconstructions=2,native_job_seconds=native,offline_total_seconds=offline,micro_graph_build_seconds=sum(x['micro_graph_build_seconds'] for x in costs),analysis_seconds=sum(x['analysis_seconds'] for x in costs),objective_verifier_v2_seconds=read(C/stages[2]/'reviews/joint_objective_verification.json')['seconds'],objective_verifier_failed_seconds=None,render_document_seconds=None,inherited_GT_P_cost=None,unknown_scope='Failed checker timer and render/document wall not individually recorded; inherited GT/P not remeasured.',new_QPS_points=0,new_GT=0,new_optimizer_updates=0,new_compile_seconds=0,logical_new_stage_bytes=logical,unique_inode_new_stage_bytes=sum(inodes.values()),free_bytes=free,free_GiB=free/(1<<30)))
s=read(C/'state.json');s.update(status='SESSION7_COMPLETE_SAFE_HANDOFF',session7_status='COMPLETE_SAFE_HANDOFF',session7_NSG=ns,session7_HNSW=hs,session7_builds=bs,session7_offline_fits=8,session7_native_job_seconds=native,session7_offline_total_seconds=offline,session7_development_QPS_points=0,session7_wall_batches=0,session7_final_feedback_used=False,session7_report=str(C/'session7_report/report.md'),session7_failure_union_queries=nf,session7_changed_failure_queries=nc,session7_terminal_ledger=str(B/'terminal_ledger.json'),total_new_NSG=4705364+ns,total_HNSW=5116896+hs,total_builds=352+bs,candidate_inventory=str(C/'candidate_inventory_v8.json'),native_pids=[],offline_pids=[],offline_tool_status='TERMINAL_EXIT0',pending_tool_sessions=[],day_goal_complete=False,session_safe_boundary_epoch=now,session_safe_boundary_local_time=datetime.datetime.now().astimezone().isoformat(),free_GiB=free/(1<<30),supervisor_review_through='E79/E80 final raw/model/seals accepted through review113; inventory_v7 review114, E81 source/budget117 and model/objective119 accepted. New E81 raw/final and combined report pending independent review when this snapshot was written.',next_design=str(C/'next_stage_design_session7.md'),next_action='Read handoff_session7 and supervisor notes, run scoped resume_inspect_v7. E79/E80/E81 old gates failed and no wall authorized within them. New version/protocol may study new-bank exact vs approximate routing; final E34 still pending.');dump(C/'state.json',s)
handoff=f'''# 第7独立串行会话安全交接

E79–E81完整完成并封存，双集原预锁门均失败；整日21:00目标未完成。本会话提前到达安全边界，未启动新CLI或子代理，所有自有工具已实际退出，无待接管实验任务。宿主全局进程核验由只读监督器接续；独立exec的/proc不能互见，不用单独空进程扫描冒充宿主证明。

- E79目标全均值：Web对P−11/失败+7，对compact+48/−4；Y对P0/−2，对compact−120/+11。置换仅控制不晋升。
- E80同hub条件均值：Web对P−39/+17，对compact+20/+6；Y对P−12/−3，对compact−132/+10。
- E81原Q初始化等权联合分组：Web对P−78/+8、对compact−19/−3；Y对P+58/−11、对compact−62/+2，对E80+70/−8。Y相对P两半{yhalves[0]:+d}/{yhalves[1]:+d}，原门仍FAIL。保留更多旧compact正收益，仍有新损伤；不扫权重/seed或忽略compact。E73/E74原Y局部信号继续保留。

本会话新增{ns:,} NSG/{hs:,} HNSW/{bs}真实构图/8离线训练；另2原Q复现。离线操作wall{offline:.3f}s、native{native:.3f}s，0新QPS/GT/梯度/编译。失败并集{nf}、变化{nc}。继承GT/P和第一次失败检查耗时未知，绘图/文档未逐项计时；全部操作成本均非QPS。完整数字见[cost](session7_closeout/cost.json)，工具终止见[ledger](session7_closeout/terminal_ledger.json)。当前free{free/(1<<30):.5f}GiB；没有删除/清理历史。E81阶段封存新逻辑输出纳入三阶段合计{logical:,}bytes，不重复计算bin符号链接；晚间64MiB及交接4MiB在6.8GiB下限外保留。

[E79报告](stage20_target_space_modes_v1/report.md) · [E80报告](stage21_hub_conditioned_targets_v1/report.md) · [E81报告](stage22_joint_view_partition_v1/report.md) · [综合报告/失败图](session7_report/report.md)。E80标签修正另存conditional_modes_v2，不动其seal。E81独立检查首版布局差异致F哈希失败，旧源保留，v2严格哈希及独立求和通过，无模型/ANN重跑。监督模型独立复核119通过；后续监督审阅以最新notes为准。

P-fit20K=router_train[10000:30000]包含旧4096train/1024monitor；aux7952=router_train[2048:10000]及两半已用于选择，算训练。cal/audit历史暴露。E34历史validation2000与held-out本会话未打开，不能因元数据余行就称全项目未使用。库存v8增加8个对象于v6（6个主候选、2置换控制），旧44对象保留，总52，未冻结最终best_all/best_new。

下一命令只读增量验封，不重跑stage1–22：

```bash
cd /data/netg/ACSG
.venv_cpu/bin/python entry_method_exploration/20260913_until2100_v1/src/resume_inspect_v7.py
```

随后读[next_stage_design_session7](next_stage_design_session7.md)、当前四根文档和[supervisor notes](/data/acsg_sessions/20260913_until2100_v1/supervisor_notes.md)。旧E79–E81不进入enhancement wall；可按新bank的完整排名与近似误差待证问题另冻实质新协议，不直接换名重启E69/E70 runner。这个后续方向尚未执行，也未证明有新增效用。

晚间最终仍必须完成：20:00停新训练，20:40停新增查询，21:00交QPS–Recall/QPS–失败率/按L三指标与失败查询报告。在已观察开发反馈上先冻候选/规则，再读E34；原NSG/Fast/GT10匹配P/实际新方法同批单线程完整在线wall，五L五轮、轮换顺序、aligned集合评分，禁止拼接旧QPS批次或读最终再调参。原图/base/GT/rawIP固定，小HNSW仍只覆盖815/821真实入口。新资源合同可在新阶段前瞻核算，旧阶段门不追改。
'''
(C/'handoff_session7.md').write_text(handoff);(C/'handoff.md').write_text(handoff)
for n in roots:shutil.copy2(R/n,B/'root_after'/n)
for n in ['README.md','68_target_space_modes.md','69_hub_conditioned_targets.md','70_joint_view_partition.md']:shutil.copy2(R/'experiment_history'/n,B/'root_after'/('history_'+n))
for n in ['state.json','handoff.md']:shutil.copy2(C/n,B/n)
dump(C/'session7_report/visual_review.json',dict(status='PASS',epoch=time.time(),images=['conditional_modes_v2.png','failure_queries.png'],review='Viewed both; zero bar has positive headroom, all labels clear, full failure CSV source row ordering preserved.',new_ANN=0))
# Snapshot live roots/state/handoff, never put their mutable paths in immutable seal.
files=[p for p in B.rglob('*') if p.is_file()]+[p for p in (C/'session7_report').rglob('*') if p.is_file()]+[C/'handoff_session7.md',C/'next_stage_design_session7.md',C/'candidate_inventory_v8.json',C/'reviews/inventory_v8_verification.json',C/'reviews/session7_process_namespace_note.json',C/'src/close_session7.py',C/'src/resume_inspect_v7.py',C/'src/update_inventory_session7.py',C/'src/update_inventory_session7_e81.py']+[C/s/'reviews/final_artifact_freeze.json' for s in stages]
assert not (C/'reviews/session7_final_artifact_freeze.json').exists();dump(C/'reviews/session7_final_artifact_freeze.json',dict(epoch=time.time(),files=[identity(p) for p in sorted(set(files))],accepted_old_scope='E79/E80 payloads previously verified by supervisor; retain seal anchors here. E81 payload checked by scoped resume.'))
print('SESSION7_SAFE_CLOSED',json.dumps(dict(NSG=ns,HNSW=hs,builds=bs,native_seconds=native,offline_seconds=offline,free_GiB=free/(1<<30),failure_union=nf,changed=nc,seal_files=len(set(files))),ensure_ascii=False))
