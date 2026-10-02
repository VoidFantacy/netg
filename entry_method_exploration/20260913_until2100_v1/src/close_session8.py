from pathlib import Path
import json,hashlib,shutil,time,datetime
R=Path('/data/netg/ACSG');C=Path(__file__).resolve().parents[1];B=C/'session8_closeout';B.mkdir();(B/'source_before').mkdir();(B/'root_after').mkdir()
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for z in iter(lambda:f.read(8<<20),b''):h.update(z)
 return h.hexdigest()
def identity(p):
 p=Path(p);s=p.stat();return dict(path=str(p),bytes=s.st_size,mtime_ns=s.st_mtime_ns,sha256=sha(p))
roots=['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md']
for f in roots:shutil.copy2(R/f,B/'source_before'/f)
for f in ['handoff.md','state.json']:shutil.copy2(C/f,B/'source_before'/f)
shutil.copy2(R/'experiment_history/README.md',B/'source_before/history_README.md')
stages=['stage23_target_exact_utility_v1','stage24_sibling_links_v1','stage25_query_shortcuts_v1','stage26_query_gate_feasibility_v1'];cost=[read(C/s/'results/cost.json') for s in stages];assert sum(x['NSG'] for x in cost)==266834 and sum(x['HNSW'] for x in cost)==339072
for st in stages:assert (C/st/'reviews/final_artifact_freeze.json').exists()
for st in stages[1:3]:
 jj=read(C/st/'logs/jobs.json');assert len(jj)==4 and all(j['status']=='COMPLETE' and j['returncode']==0 and j['peak_threads']==1 and j['affinity']==[15] for j in jj)
jj=read(C/stages[0]/'logs/jobs.json');assert len(jj)==2 and all(j['status']=='COMPLETE' and j['native']['actual_threads']==1 for j in jj)
v=read(C/'session8_report/verification.json');nf=sum(x['union'] for x in v['unions'].values());changed=sum(x['changed'] for x in v['unions'].values());assert nf==413 and changed==173
p=R/'summary.md';p.write_text(p.read_text()+'\n第8会话E82–E85完整接续：新增266834 NSG/339072 HNSW、8静态边安装/2图监督训练/4岭拟合，0普通build与新QPS。四真实方法失败并集413条、状态变化173条；[综合报告](entry_method_exploration/20260913_until2100_v1/session8_report/report.md)及[失败图](entry_method_exploration/20260913_until2100_v1/session8_report/failure_queries.png)保留E84 Web局部修复、各版损伤和训练/接受边界。全部阶段已停止并封存，整日目标未完成，E34最终待做。\n')
p=R/'s-target.md';p.write_text(p.read_text()+'\n第8会话已安全收口，下一独立研究/最终交付的优先次序见[next_stage_design_session8](entry_method_exploration/20260913_until2100_v1/next_stage_design_session8.md)。先读[handoff_session8](entry_method_exploration/20260913_until2100_v1/handoff_session8.md)，用resume_inspect_v8作增量检查；旧E82–E85不重跑、不扩原门。库存v9有60个原生配置目录对象，未冻结最终选择，E85仅离线缓存模型。\n')
p=R/'experiment_history/README.md';s=p.read_text();new='\n2026-09-13第8串行会话：\n\n| 新卡片 | 已执行范围 |\n|---|---|\n| [71 新目标完整排名效用](71_target_exact_utility.md) | E82，3593缺失键真实补齐，六诊断门失败 |\n| [72 同hub补边](72_sibling_links.md) | E83，固定旧边追加与同节点度近邻控制，双集失败 |\n| [73 查询排名补边](73_query_shortcuts.md) | E84，fit排名缺口投票，Web局部修复但完整门失败 |\n| [74 query向量选择缓存](74_query_gate_feasibility.md) | E85，固定岭前3976训练/后3976接受，双集失败，0新ANN |\n';p.write_text(s+new)
free=shutil.disk_usage('/data').free;assert free>=6.65*2**30+72*2**20;files=[p for st in stages for p in (C/st).rglob('*') if p.is_file() and not p.is_symlink()];logical=sum(p.stat().st_size for p in files);inodes={}
for p in files:ss=p.stat();inodes[ss.st_dev,ss.st_ino]=ss.st_size
assert logical<192*2**20
native=cost[0]['native_elapsed_seconds']+sum(x['native_job_seconds'] for x in cost[1:3])
dump(B/'cost.json',dict(NSG=266834,HNSW=339072,ordinary_builds=0,static_edge_installs=8,graph_supervised_fits=2,ridge_fits=4,new_GT=0,new_QPS_points=0,native_operation_seconds=native,compile_seconds=cost[2]['compile_seconds'],E84_graph_supervision_seconds=cost[2]['graph_supervision_seconds'],E84_edge_install_and_verify_seconds=cost[2]['edge_install_seconds'],E85_ridge_stage_seconds=cost[3]['training_seconds'],E85_evaluation_verification_seconds=cost[3]['evaluation_and_independent_verification_seconds'],E83_install_seconds=None,E83_failed_preparations_seconds=None,E84_training_route_RSS_high_water=None,inherited_GT_P_cost=None,render_document_seconds=None,unknown_scope='E83 preparation/installation timers lost after metadata failure; short E84 route polling is not memory high-water; inherited GT/P and rendering/document time not newly measured. Nested operation costs are not additive QPS.',logical_new_stage_bytes=logical,unique_inode_new_stage_bytes=sum(inodes.values()),free_bytes=free,free_GiB=free/2**30))
ledger=dict(status='ALL_SESSION_EXPERIMENT_TOOLS_TERMINAL',E82=read(C/stages[0]/'reviews/terminal_ledger.json'),E83=read(C/stages[1]/'reviews/terminal_ledger.json'),E84=read(C/stages[2]/'reviews/terminal_ledger.json'),E85=read(C/stages[3]/'reviews/terminal_ledger.json'),combined_report=dict(session=63178,exit_code=0),pending_tool_sessions=[],process_scope='Every session-owned long tool actually terminal-exited; original namespace sampled threads/CPU and explicitly waited native children. Supervisor separately checks host processes; empty isolated /proc is not host proof.')
dump(B/'terminal_ledger.json',ledger)
now=time.time();s=read(C/'state.json');s.update(status='SESSION8_COMPLETE_SAFE_HANDOFF',session8_status='COMPLETE_SAFE_HANDOFF',session8_NSG=266834,session8_HNSW=339072,session8_builds=0,session8_edge_installs=8,session8_graph_supervised_fits=2,session8_ridge_fits=4,session8_native_operation_seconds=native,session8_compile_seconds=cost[2]['compile_seconds'],session8_final_feedback_used=False,session8_development_QPS_points=0,session8_wall_batches=0,session8_report=str(C/'session8_report/report.md'),session8_failure_union_queries=nf,session8_changed_failure_queries=changed,session8_terminal_ledger=str(B/'terminal_ledger.json'),total_new_NSG=5360806,total_HNSW=5843808,total_builds=360,candidate_inventory=str(C/'candidate_inventory_v9.json'),native_pids=[],offline_pids=[],pending_tool_sessions=[],offline_tool_status='TERMINAL_EXIT0',day_goal_complete=False,session_safe_boundary_epoch=now,session_safe_boundary_local_time=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),free_GiB=free/2**30,supervisor_review_through='2026-09-13 17:01:15 reviews126..138: E82/E83/E84 full raw/graphs/final, E85 four model spectralfit/scalar prediction/selection/acceptance verified. Check latest notes for final E85/catalogue/combined closeout review.',next_design=str(C/'next_stage_design_session8.md'),next_action='Read handoff_session8 and latest supervisor notes, run read-only resume_inspect_v8. E82-E85 stopped. Fresh utility-supervision design may follow only new protocol; freeze evening final candidates before E34, day goal incomplete.',active_json_scope='Historical process samples only, all actual experiment tools terminal; no live task to adopt.');dump(C/'state.json',s)
handoff=f'''# 第8独立串行会话安全交接

E82–E85全部完成并封存，本会话到达安全边界；整日21:00目标未完成。没有开启并行CLI/子代理，所有自有实验/训练/图表工具已实际退出，没有待接管任务。监督器在本CLI退出后可开启下一唯一写入会话，最迟安全退出17:25:25保持。宿主全局进程检查由只读监督器执行，不能用空的隔离/proc冒充宿主证明。

## 结果和明确停止范围

- E82 target/conditional/joint完整float64画像排名：47,712逻辑输出、43,800缓存复用、3,593唯一新键/319互alias，实际7,762 NSG；六原诊断门FAIL。Web target对compact+256/失败−22，但对精确P+3/+2；Y各bank均不及compact。保留近tie/远tie精度分组，不能只归因于遍历误差。0新HNSW/build。
- E83同hub静态补边：每臂Web1359/Y1285边，全部旧边保持；对compact Web−1/失败−1，Y0/0，routeNDC增加。双集门失败，固定规则停止。4静态安装并非普通build，准备两次元数据失败原件和未知耗时保持。
- E84 fit查询首返回slot→缺失排名目标最高票补一边：Web254/Y47边/臂，2图监督训练/4安装。对compact Web+42/失败−4、两半+22/+20；仍对P−17/+7。Y对compact−4/0、对P+116/−13。双集门FAIL，固定票数/首slot/加边规则停止，不能自动wall。保留Web局部修复：774/820原正收益保留、丢46、新增32、避旧损82、新损26。不是每边因果信用。
- E85query方向岭选择P/compact：前3976fit、后3976accept，单向而非crossfit，固定1/d与零阈值，另固定标签置换。接受对P Web−35/+3，Y+24/−3；对compact Web+8/0，Y−57/+5；正命中仅保留57.68%/57.92%。双集门FAIL，未原生实现，无新ANN。state的native_implementation_feasible=false指质量门不给后续实现依据，不证明API无法实现；非线性/其他选择器未被本线性版本否定。

所有旧门只约束原版本；另立实质新方向/预算已有用户授权，不重复问许可，也不把旧NO_GO换名扩大。E73/E74 Y局部信号保持，默认方法未替换。

## 产物、资源与成本

[综合报告](session8_report/report.md) · [四真实方法失败图](session8_report/failure_queries.png) · [完整413条失败query](session8_report/failure_queries.csv)。其中173条状态变化，240条全四方法零命中。E82的517条精确诊断失败、E85的410条含训练缓存失败分别保留各阶段，不混成新增在线批次。E83/E84同批回归P/compact全字段，原kernel和集合mask均验收。

新增266,834 NSG /339,072 HNSW、8静态边安装、2图监督训练、4岭拟合；0普通build/新GT/新QPS。实际native操作{native:.3f}s，E84编译{cost[2]['compile_seconds']:.3f}s；分项含加载/count/检查/I/O且有包含关系，不是QPS。E83安装/失败prepare耗时、继承GT/P和绘图文档耗时未知；E84短route子进程RSS轮询不是实际峰值。完整[cost](session8_closeout/cost.json)、[工具终止ledger](session8_closeout/terminal_ledger.json)及各阶段cost。当前free{free/2**30:.5f}GiB，四阶段新增逻辑{logical:,}bytes/独立inode{sum(inodes.values()):,}bytes；会话192MiB、晚间64MiB/交接8MiB、6.65GiB前瞻floor均未触线，没有清理历史。新会话再现场核算新预算，旧预算不回改。

[E82](stage23_target_exact_utility_v1/report.md) · [E83](stage24_sibling_links_v1/report.md) · [E84](stage25_query_shortcuts_v1/report.md) · [E85](stage26_query_gate_feasibility_v1/report.md)。四根文档及历史71–74/索引已同步，每阶段source_before/root_after及finalseal保留。E84资源helper旧漏E83由独立补充checker包含全部阶段，不改frozen common；E84第一次封存命令误用无NumPy的系统python，在import处终止且未写seal，用.venv_cpu恢复仅元数据封存，0重跑训练/ANN。

## 角色和接续

P-fit20K=router_train[10000:30000]含旧4096train/1024monitor；aux7952=[2048:10000]、cal/audit历史使用。E84新连边只从fit原query排名投票，但继承W有GT监督。E85新教师读取aux前半[2048:6024]真实命中差，后半[6024:10000]为本版拟合外接受，全部历史暴露，接受反馈算训练。复盘E25读了历史报告汇总，未读E34最终原始query/GT或held-out，不得宣称全项目未见。

库存[candidate_inventory_v9](candidate_inventory_v9.json)有60个原生配置对象，旧52完整保留，新增E83/E84主/控制共8；4主配置只是目录身份而非推荐，控制不晋升。E85四岭模型独立offline条目，不能作为原生best_new。最终best_all/best_new尚未冻结。

下一条命令只读增量验封，不重跑stage1–26或已通过的数值证明：

```bash
cd /data/netg/ACSG
.venv_cpu/bin/python entry_method_exploration/20260913_until2100_v1/src/resume_inspect_v8.py
```

随后完整读四根文档和最新[supervisor notes](/data/acsg_sessions/20260913_until2100_v1/supervisor_notes.md)。[next_stage_design_session8](next_stage_design_session8.md)提供尚未执行的下一优先级：若继续静态小图研究，先追溯E33原边RL及E84几何缺口与实际效用，判断真实NSG教师和实际加边动作是否对应，再另立小预算；不要扩E84几何票或E85固定线性参数。最后优先保证完整最终矩阵。

E34晚间最终仍待执行：先在已暴露开发反馈冻结实际候选/规则，再读历史validation2000，禁止最终回流训练/选型；held-out不自动打开。原NSG/Fast30K/GT10-hard和Web匹配soft/实际新方法同批五L五轮，CPU15/所有库与实际线程1，单方法串行；完整在线route+原NSG+输出独立整批wall，GT/count/hash/JSON/load/build在计时外，aligned逐query集合评分及zero失败救回/新增。最新完整曲线仍[E74](stage15_compact_wall_v1/report.md)，不能拼本会话质量点。20:00停新训练、20:40停新查询、21:00交完整QPS–Recall/QPS–失败率/按L三指标与失败查询报告。
'''
(C/'handoff_session8.md').write_text(handoff);(C/'handoff.md').write_text(handoff)
dump(C/'session8_report/visual_review.json',dict(status='PASS',figure='failure_queries.png',all_labels_readable=True,full_union=nf,changed=changed))
for f in roots:shutil.copy2(R/f,B/'root_after'/f)
for f in ['README.md','71_target_exact_utility.md','72_sibling_links.md','73_query_shortcuts.md','74_query_gate_feasibility.md']:shutil.copy2(R/'experiment_history'/f,B/'root_after'/('history_'+f))
for f in ['state.json','handoff.md']:shutil.copy2(C/f,B/f)
print('SESSION8_CLOSE_PREPARED',dict(NSG=266834,HNSW=339072,free_GiB=free/2**30,bytes=logical,nf=nf))
