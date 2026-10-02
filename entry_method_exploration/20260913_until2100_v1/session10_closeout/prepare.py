from pathlib import Path
import sys,datetime
Q=Path(__file__).resolve().parent;C=Q.parent;sys.path.insert(0,str(C/'stage32_final_tooling_v1/src'))
from common import *
threads();resources();shutil.copy2(C/'state.json',Q/'state_before.json');shutil.copy2(C/'handoff.md',Q/'handoff_before.md');shutil.copy2('/data/acsg_sessions/20260913_until2100_v1/supervisor_notes.md',Q/'supervisor_notes_observed.md');jobs=[]
for dirname,en in [('stage30_local_parent_restore_v1','E89'),('stage31_cross_source_restore_v1','E90')]:
 for kind in ['training_jobs','jobs']:
  path=C/dirname/'logs'/(kind+'.json')
  for j in read(path):
   assert j['status']=='COMPLETE' and j['returncode']==0;th=j.get('actual_threads',j.get('peak_threads'));assert th==1 and j['affinity']==[15];hnsw=j['actual_HNSW'] if kind=='training_jobs' else 10*(128 if j['split']=='preflight' else 7952);jobs.append(dict(stage=en,dataset=j['dataset'],kind='fit' if kind=='training_jobs' else j['split'],started_at=j['started_at'],completed_at=j['completed_at'],seconds=j['seconds'],actual_NSG=j['actual_NSG'],actual_HNSW=hnsw,returncode=0,threads=1,CPU=15,actual_tool_terminal_observed=True,source_ledger=identity(path),independent_terminal_evidence='Supervisor166/167 actual E89 training/aux tools terminal0; supervisor171/172 actual E90 training/aux tools terminal0.',pid_scope='Local job pid belongs to isolated tool namespace; all owning tools observed terminal, not a host PID to adopt.'))
jobs.sort(key=lambda j:j['started_at']);assert len(jobs)==12 and all(a['completed_at']<=b['started_at'] for a,b in zip(jobs,jobs[1:]));assert sum(j['actual_NSG'] for j in jobs)==346556 and sum(j['actual_HNSW'] for j in jobs)==3578928;dump(Q/'terminal_ledger.json',dict(status='PASS_ALL12_SERIAL_TERMINAL0',jobs=jobs,pending_tools=[],pending_experiments=[],new_NSG=346556,new_HNSW=3578928,new_QPS_points=0))
source=read(C/'state.json');source.update(status='SESSION10_COMPLETE_SAFE_HANDOFF',stage='E89_E90_E91_complete',session10_status='COMPLETE_SAFE_HANDOFF',session10_active_stage=None,session10_terminal_ledger=str(Q/'terminal_ledger.json'),session10_report=str(C/'session10_report/report.md'),session10_pending_tasks=[],pending_tool_sessions=[],native_pids=[],offline_pids=[],session_safe_boundary_epoch=time.time(),session_safe_boundary_local_time=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),free_GiB=shutil.disk_usage('/data').free/2**30,supervisor_review_through='181: E89/E90 all source/raw/gates/seals verified; E91 v3 raw arrays/metadata eligibility/reanalysis checked. Later notes should be read on resume.',handoff=str(C/'handoff_session10.md'),next_design=str(C/'stage32_final_tooling_v1/readme.md'),session10_vector_installs=8,session10_zero_update_copies=2,session10_offline_utility_fits=4,session10_failure_union_queries=428,session10_changed_failure_queries=194,day_goal_complete=False)
dump(C/'state.json',source)
text='''# 第10会话安全交接：E89–E91

本会话完成，整日目标未完成。没有需续跑的实验、后台训练或ANN；所有12个原生训练/辅助工具均实际terminal0、严格串行CPU15/线程1，详见session10_closeout/terminal_ledger.json。监督器须在本CLI实际退出后再开后继唯一写入者；本文件不是CLI已退出的证明。

首先读本文件、state.json与监督备注最新增量，再按用户契约完整读五主文件。无需重跑E89/E90训练/辅助或E91软件回归。首条只读接续检查：

```bash
python3 -B entry_method_exploration/20260913_until2100_v1/src/resume_inspect_v10.py
```

E89 stage30_local_parent_restore_v1：固定32hub/集，两子行复制父P，实际fit筛13/8；真实合并224/114净命中，aux对compact Web+18/失败−6、Y−39/+5，双集完整门FAIL。训练收益和损伤同时存在；父恢复保持原图全部非向量bytes。原报告/seal不变，supplement_training_v1补足训练图；显式非候选原因表是查询后从冻结事件补录，时间边界已披露。

E90 stage31_cross_source_restore_v1：只用原13/8固定动作，aux前3976明确加入训练；接受后半3976仅整体预冻模型。筛5/0，Web支持+49/fit+61；接受对compact+21/失败−1，但对P−22/+2、对随机+4/+1，分半不稳，完整门FAIL。Y零更新逐字compact，不能把相对P+81/失败−8包装为新方法。固定E89/E90版本都停，不扫动作子集/阈值/强度。

E91 stage32_final_tooling_v1：0ANN，已准备run_frozen_v3/analyze_frozen_v3（依赖contracts_v3/scoring_v3/plot_results_v2）。原E74全部55点112640返回/275旧wall回归；内存2000评分110000行，无2000计时。32负例与额外资格/先拒绝后hash/固定3和variable1..3通过，源版本v1/v2/v3各冻件保留。E73 unsupported distinct明确拒绝，evaluator SHA不等是语义兼容审查门，不能由此宣称旧方法本质不支持或默默排除。

实际best_all/best_new、评分表、规则/tie和最终协议尚未冻结，最终输入载荷未读取/hash。E91的non_executable_metadata_fixture*只是mock hash、只stat最终路径的软件夹具，伪规则/伪分数且故意无效，不能复制为真实选择。请按E91 readme的逐步schema创建新的实际最终目录；现有工具没有替你做实际选型或最终数据准备。所有新增模型含best_all须是合格非零主方法，要求基线同批；45/55点真实预算分别630720/770880 NSG与490000/630000 HNSW，225/275完整wall。实际别名与方法数决定费用，不套旧2048 cap。真实final controller运行和方法结论仍待完成。

candidate_inventory_v11保留68旧对象+8新=76：3非零main、1Y零main、4控制；491嵌套identity/213文件verified。目录不是实际选择，也不能声称全部76都排名。保留原NSG/Fast/GT10-hard/Websoft匹配P和实际新方法；有理由只比较部分候选时列出完整资格/排除原因。若仍探索新方向，要基于证据另立版本/预算，避免继续局部阈值追逐；当前优先预留足够时间完整最终矩阵。

本会话新增346556NSG=22716训练+323840辅助；3578928HNSW=3255728训练+323200辅助；10物理导出=8非零向量安装+2零副本，4离线筛选拟合，0普通build/梯度/GT/QPS。E89编译13.194s；训练操作104.978s、辅助260.991s，含load/count/cache/I/O不是QPS。继承P/GT成本未知。日累计6072416NSG/17179280HNSW/360普通build，开发QPS220点/1100wall分属E65/E67/E71/E74独立批，final0。

综合报告session10_report/report.md将七配置同源质量独立评分111328行，428失败query并集/194变化/2996完整方法单元；不能相加E89/E90各自失败数。报告引用E74原QPS曲线，明确旧2048批，不混入新质量点。E91额外补齐E74全方法零失败414query/825query×L事件/4627cells，旧91只是配对变化子集。图已目检。

P-fit20K=router_train[10000:30000]含旧4096train/1024monitor；E90支持[2048:6024]训练，接受[6024:10000]及所有aux/cal/audit均历史使用。任何接受或选型反馈算训练；E34历史validation2000可最终对照，不回流训练，held-out未开。基础base/rawIP/NSG/GT固定，815/821真实入口画像，不是10M小图。

资源使用session10_resource_protocol_v4（v1/v2/v3冻结不改）：三阶段+综合报告+closeout及新目录/交接文件累计192MiB上限，额外64MiB最终+8MiB备用，floor6.45GiB。最终实测另立实际预算，先现场检查剩余磁盘，不清理旧结果。大文件只/data。20:00停新训练、20:40停新增query、21:00交完整报告，本会话安全截止19:21:48。

非实验更正：E90首个源生成调用无python命令，随后python3生成成功，无失败ANN；E89 wrapper草稿pretrain前修正、0失败ANN。E90接受图v2仅修正零标签顶端余量，原图保留；Y别名说明在综合图和报告明确。综合报告生成后E91 readme追加二进制兼容限制；旧说明按原SHA原样保留在session10_report/source_before，input_freeze_v2只更新文档引用，全部原数值/返回不变。旧实验全封存保持。

[综合报告](session10_report/report.md) · [失败全表](session10_report/failure_queries.csv) · [E91实际使用步骤](stage32_final_tooling_v1/readme.md) · [候选目录](candidate_inventory_v11.json) · [最新完整QPS旧批](stage15_compact_wall_v1/report.md) · [监督备注](/data/acsg_sessions/20260913_until2100_v1/supervisor_notes.md)
'''
p=C/'handoff_session10.md';assert not p.exists();p.write_text(text);shutil.copy2(p,C/'handoff.md')
for f in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md']:
 p=Q/'root_after'/f;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/f,p)
dump(Q/'state_after.json',source);print('SESSION10_HANDOFF_PREPARED')
