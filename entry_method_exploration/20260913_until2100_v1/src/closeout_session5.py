"""Finalize a serial-session handoff, not the full day goal. No ANN or final data."""
from pathlib import Path
import json,hashlib,shutil,time,os,re,subprocess
C=Path(__file__).resolve().parents[1];R=C.parents[1]
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def ident(p):
    p=Path(p);h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return dict(path=str(p),bytes=p.stat().st_size,sha256=h.hexdigest())
close=C/'reviews/session5_closeout.json';assert not close.exists()
stages=[C/x for x in ['stage13_distinct_hub_width_v1','stage14_compact_modes_v1','stage15_compact_wall_v1']]
costs=[read(p/'results/cost.json') for p in stages]
jobs=[j for p in stages for j in read(p/'logs/jobs.json')]
assert len(jobs)==10 and all(j['status']=='COMPLETE' and j.get('returncode',0)==0 for j in jobs)
active=[]
for p in Path('/proc').glob('[0-9]*/cmdline'):
    try:
        args=p.read_bytes().split(b'\0');pid=int(p.parent.name)
        if pid==os.getpid() or not args:continue
        exe=Path(args[0].decode(errors='replace')).name
        if exe in ['bash','sh','timeout']:continue
        command=' '.join(x.decode(errors='replace') for x in args)
        if 'entry_method_exploration/' not in command:continue
        if re.search(r'/bin/(evaluate|inject|synthetic|build_graph)(?:\s|$)',command) or re.search(r'/src/(run|run_v2|train|deploy|build|build_modes|prepare|analyze|plot|failure_details|member_deltas|independent_verify)\.py(?:\s|$)',command):active.append(dict(pid=pid,command=command))
    except (OSError,ProcessLookupError):pass
assert not active,active
old=read(C/'reviews/session4_closeout.json');pre=read(C/'reviews/session5_precloseout_verification.json')
nsg=sum(c.get('NSG',c.get('NSG_calls',0)) for c in costs)
hnsw=sum(c.get('HNSW',c.get('HNSW_calls',0)) for c in costs)
builds=sum(c.get('builds',c.get('new_builds',0)) for c in costs)
native=sum(c['native_job_seconds'] for c in costs);compile_sec=sum(c.get('compile_seconds',c.get('new_compile_seconds',0)) for c in costs)
assert (nsg,hnsw,builds)==(1080816,936000,2)
now=time.time();local=time.strftime('%Y-%m-%d %H:%M:%S %z',time.localtime(now));assert now<1789280277
free=shutil.disk_usage('/data').free/(1<<30);assert free>=7
new_bytes=sum(p.stat().st_size for s in stages for p in s.rglob('*') if p.is_file())
sup='2026-09-13 14:01; E72/E73 raw and seals, E74 raw/timing/figures, inventory_v5 and scope correction passed; E74 final seal may be reviewed separately'
nextcmd='env PYTHONDONTWRITEBYTECODE=1 .venv_cpu/bin/python entry_method_exploration/20260913_until2100_v1/src/resume_inspect_v5.py'
v=dict(status='PASS_SESSION5_SAFE_BOUNDARY',epoch=now,local_time=local,session_safe_exit_deadline=1789280277,day_deadline=1789304400,day_goal_complete=False,native_pids=[],active_native_or_training=active,all_native_and_analysis_tools_terminal=True,native_jobs_complete=10,session5_NSG_calls=nsg,session5_HNSW_calls=hnsw,session5_new_builds=builds,session5_synthetic_builds=4,session5_synthetic_HNSW=512,session5_synthetic_NSG=0,day_NSG_calls=old['day_NSG_calls']+nsg,day_HNSW_calls=old['day_HNSW_calls']+hnsw,day_new_builds=old['day_new_builds']+builds,session5_native_job_seconds=native,session5_compile_seconds=compile_sec,E72_NSG=costs[0]['NSG'],E73_NSG=costs[1]['NSG'],E74_NSG=costs[2]['NSG_calls'],E74_HNSW=costs[2]['HNSW_calls'],E74_independent_plain_wall_seconds=costs[2]['independent_plain_wall_seconds'],E74_plain_count_loads=90,session5_development_QPS_points=55,session5_wall_batches=275,day_development_QPS_points=220,day_wall_batches=1100,final_validation_QPS_points=0,E74_unique_failure_queries=91,E74_failure_L_events=174,E74_failure_five_L_cells=455,new_GT=0,gradient_updates=0,new_training_seconds=0,compaction_seconds=costs[1]['compaction_seconds'],micro_graph_build_seconds=costs[1]['micro_graph_build_seconds'],inherited_E66_profile_training_seconds=30.2860799959999,GT_inclusive_inherited_seconds=None,GT_inclusive_inherited_reason='Historical dependencies are not remeasured or treated as zero',free_GiB=free,three_new_stage_bytes=new_bytes,campaign_bytes_before_session5_final_seal=sum(p.stat().st_size for p in C.rglob('*') if p.is_file()),checked_file_identities_precloseout=pre['checked_files'],supervisor_review_through=sup,scope='All historical fit/cal/audit/aux selection is training exposure. E74 is development, no E34 final or heldout input today.',next_command=nextcmd,E72_synthetic_scope_correction=str(C/'reviews/e72_synthetic_scope_correction_session5.md'))
dump(close,v)
s=read(C/'state.json');s.update(status='SESSION5_COMPLETE_SAFE_HANDOFF',writer='authorized independent serial session 5',day_goal_complete=False,stage='E74_COMPLETE',stage15_status='COMPLETE_DEVELOPMENT_WALL_VERIFIED',session5_status='COMPLETE_SAFE_HANDOFF',native_pids=[],session5_NSG=nsg,session5_HNSW=hnsw,session5_builds=builds,session5_native_job_seconds=native,session5_compile_seconds=compile_sec,session5_final_feedback_used=False,session5_development_QPS_points=55,session5_wall_batches=275,total_new_NSG=v['day_NSG_calls'],total_HNSW=v['day_HNSW_calls'],total_builds=v['day_new_builds'],formal_QPS_points=220,formal_wall_batches=1100,formal_QPS_scope='E65/E67/E71/E74 are separate historical development batches, never concatenate curves; final E34 still pending',final_validation_QPS_points=0,E74_unique_failure_queries=91,E74_failure_L_events=174,candidate_inventory=str(C/'candidate_inventory_v5.json'),session_safe_boundary_epoch=now,session_safe_boundary_local_time=local,free_GiB=free,supervisor_review_through=sup,handoff=str(C/'handoff.md'),next_design=str(C/'next_stage_design_session5.md'),next_action='Read handoff/design and run read-only resume_inspect_v5; stage1..15 complete. New independent protocol for source-level-preserving compact graph control; no automatic rerun.',E72_synthetic_scope_correction=str(C/'reviews/e72_synthetic_scope_correction_session5.md'))
dump(C/'state.json',s)
handoff=f'''# 第5独立串行会话安全交接

{local}，E72–E74已完成并封存，**整日21:00用户目标未完成**。本会话14:17:57前结束；监督器安全接续下一唯一写入/实验会话，不开并行CLI或子代理。所有10个真实native job及编译/合成/分析工具均已terminal exit0，当前无遗留实验/训练/分析进程。磁盘{free:.4f} GiB，新三个阶段合计{new_bytes:,} bytes；free门仍7GiB，不清理旧产物。

## 当前结论

E72真实hub计宽distinct10保留Y对P局部正值，但双集原接续门失败，停止该版本，0QPS。E73同hub字节精简把2445/2463画像变成1771/2067，完整每hub max评分集合保持；Y完整aux7952对P +120命中/失败−13、对fullmode +71/−9，两半均正，质量门过；Web对P−59/失败+11，未过门。

E74固定精简候选同批55点275轮完整wall。Y对GT10-hard/P10五L净命中+99/+59/+38/+1/+15，失败−10/−7/−4/−1/0，QPS中位−1.565/−.961/−1.204/−.043/−.195%；QPS范围均跨零，描述性共同Recall插值+1.873/+2.455/+2.965%。保留Y局部前沿信号，未成为实测等Recall或独立最终验证。Web对匹配soft/P10五L+9/−23/+2/+28/+2、失败+2/+6/0/−1/+1，QPS中位略负、范围跨零；L128损伤明确，无稳定整体改善或默认替换。

[E74完整报告](stage15_compact_wall_v1/report.md) · [判断](stage15_compact_wall_v1/assessment.md) · [QPS–Recall](stage15_compact_wall_v1/figures/recall_qps.png) · [QPS–失败率](stage15_compact_wall_v1/figures/failure_qps.png) · [按L三指标](stage15_compact_wall_v1/figures/three_metrics_by_L.png) · [配对图](stage15_compact_wall_v1/figures/paired_deltas.png) · [失败query图](stage15_compact_wall_v1/figures/failure_query_cases.png)。五图另有SVG/PDF，均亲自查看且主监督独立验收。

失败严格零GT10命中，91个独立query、174个跨L事件、455个五L格。Web52/Y39个query、事件92/82；图每集24例，全量[失败CSV](stage15_compact_wall_v1/results/failure_query_summary.csv)保留。Y row2769全零变8/9/10/10/10，row3846全10变全0；Web3524全零变全7，2391变全零。救回和损伤都保留，事后案例不作在线选择器。

## 实际成本和验收

本会话新增{nsg:,} NSG、{hnsw:,} HNSW、2真实小图；合成另4图/512HNSW/0NSG。10native总{native:.6f}秒、编译{compile_sec:.6f}秒，E73精简{costs[1]['compaction_seconds']:.9f}秒、两图build{costs[1]['micro_graph_build_seconds']:.9f}秒。E74其中789360 NSG/645120 HNSW、275次独立完整wall合计{costs[2]['independent_plain_wall_seconds']:.6f}秒，45plain+45count源图加载、0复制/新build。没有新画像训练、GT或梯度；继承E66画像训练30.286秒和早期GT等成本不记零，未重测项null+reason。

今日累计{v['day_NSG_calls']:,} NSG、{v['day_HNSW_calls']:,} HNSW、{v['day_new_builds']}真实build，220开发点/1100wall；**final validation点仍0**。各阶段/批次成本分列，曲线不跨批拼接。所有真实查询CPU15/进程threads1和OMP/OpenBLAS/MKL/NUMEXPR/BLIS1；方法串行，完整路由/映射/原NSG/output在wall内，GT/count/hash/JSON/build/load在外。两个E74工具terminal0后才评分/绘图。

E74独立112640集合/mask、880原kernel、40960整行slot及五L身份、45图、275轮计时恒等和旧输出回归通过；本会话只读接续检查{pre['checked_files']}身份通过，最终session seal后再核查新增快照。主监督13:56已通过E72/E73原始与最终seal及E74raw/计时/五图，14:01通过32候选库存与更正；E74最终seal主监督可随后只读验收，不需等待许可。

**覆盖更正**：E72协议的“不足3hub拒绝”没有实际合成调用；末尾只测引用计数下溢，运行时有require不等于负例已测。[独立记录](reviews/e72_synthetic_scope_correction_session5.md)保留原E72封存，不为补标签重跑。E73/E74普通variable路径不含distinct回调。

根文档已同步；详细历史为[61](../../experiment_history/61_distinct_hub_width.md)、[62](../../experiment_history/62_compact_modes.md)、[63](../../experiment_history/63_compact_wall.md)。每阶段source_before/root_after和final_artifact_freeze均保留。原脏代码、旧图、GT、日志和全部原始结果未清理；全树git diff --check仍有既有源码/构建空白告警，本轮文档另作范围检查，不改无关脏源。

## 角色和下一命令

P-fit20K包含旧4096train/1024monitor；旧cal/audit/aux7952均历史暴露，任何辅助选择反馈都算训练。E74 source router_train[2048:4096]包含于已用aux7952；不能当新盲集。E34历史validation2000今天尚未进入，只供晚间冻结后最终对照，不回流训练/选型；held-out不自动打开，元数据余行不能证明全项目未使用。

[candidate_inventory_v5](candidate_inventory_v5.json)逐项保留v4旧24，另6个distinct配置和2个compact，共32且含控制；E74显示best_new=compact不是全局最终重选。原NSG/base/rawIP/GT/815或821真实H固定，Micro-HNSW只有这些真实hub的画像，非10M底图。

在项目根目录执行只读接续检查：

```bash
{nextcmd}
```

然后读[下一阶段设计](next_stage_design_session5.md)及[监督备注](/data/acsg_sessions/20260913_until2100_v1/supervisor_notes.md)。阶段1–15全部完成，禁止重跑旧runner。监督review_078已经做compact排序/实际效用分组，先读原记录而不重复分析。

最有依据的下一受控方向：先0ANN核对保留slot随机层级，再独立版本实现“删槽时消耗原随机数、保留槽普通addPoint”的唯一新图控制；注意level=0接口不强制零层，保留层级不保持邻接，最高入口被删除时header可变。完整协议/预算/门已在design写成未运行草案，后继启动前冻结；不扫seed/ef，不要求本会话赶新实验。第二方向是Web画像实际损伤与支持关联的缓存诊断，第三是晚间冻结并完成最终对照。

20:00停止新训练，20:40停止新增查询，21:00完整报告。最终包含NSG/Fast30K/GT10-hard/Web匹配起点/best_all/真实best_new，在同批五L五轮完整计时并绘图，先冻模型再开E34反馈。现授权足够串行实施，不重复问批准；不得删除、外发、发布、推送或改Codex配置。
'''
(C/'handoff.md').write_text(handoff);assert not (C/'handoff_session5.md').exists();(C/'handoff_session5.md').write_text(handoff)
docs=[R/x for x in ['summary.md','spec.md','s-target.md','s-experiment.md']]+[R/'experiment_history/63_compact_wall.md',C/'next_stage_design_session5.md',C/'handoff.md',C/'handoff_session5.md',stages[2]/'report.md',stages[2]/'assessment.md']
broken=[];checked=0
for p in docs:
    for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
        if target.startswith(('https:','http:','#','mailto:')):continue
        target=target.split('#')[0];target=re.sub(r':\d+$','',target)
        if not (p.parent/target).resolve().exists():broken.append(dict(file=str(p),target=target))
        checked+=1
assert not broken,broken
scope=subprocess.run(['git','diff','--check','--','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/63_compact_wall.md'],cwd=R,capture_output=True,text=True)
assert scope.returncode==0,scope.stdout+scope.stderr
dump(C/'reviews/session5_document_verification.json',dict(status='PASS',links_checked=checked,broken=broken,scoped_git_diff_check=0,whole_tree_diff_check='Existing unrelated source/build whitespace warnings preserved',day_goal_complete=False))
snap=C/'reviews/session5_snapshot';snap.mkdir()
for x in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md']:shutil.copy2(R/x,snap/x.replace('/','__'))
shutil.copy2(C/'state.json',snap/'state.json');shutil.copy2(C/'handoff.md',snap/'handoff.md')
paths=sorted(p for p in snap.rglob('*') if p.is_file())+[C/'handoff_session5.md',close,C/'next_stage_design_session5.md',C/'candidate_inventory_v5.json',C/'reviews/session5_inventory_verification.json',C/'reviews/e72_synthetic_scope_correction_session5.md',C/'reviews/session5_precloseout_verification.json',C/'reviews/session5_document_verification.json',C/'src/inventory_session5.py',C/'src/resume_inspect_v5.py',Path(__file__).resolve()]
seal=C/'reviews/session5_final_artifact_freeze.json';assert not seal.exists()
dump(seal,dict(status='FROZEN_SESSION5_SAFE_HANDOFF_DAY_NOT_COMPLETE',epoch=time.time(),files=[ident(p) for p in paths]))
print(json.dumps(dict(status='SESSION5_SEALED',files=len(paths),bytes=sum(p.stat().st_size for p in paths),cost=v),ensure_ascii=False,indent=2))
