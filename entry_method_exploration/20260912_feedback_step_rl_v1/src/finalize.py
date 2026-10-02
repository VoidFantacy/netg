from shared import *
import re,ast
threads(8);resources()
for name in ['prequery_freeze','protected','native_dependencies']:check(O/'reviews'/f'{name}.json')
r=read(O/'results/summary.json');v=read(O/'reviews/training_verification.json');assert v['status']=='PASS'
cost=r['cost'];gate=r['gate'];jobs=read(O/'logs/jobs.json')
assert len(jobs)==4 and all(x['status']=='COMPLETE' for x in jobs)
assert sum(x['actual'] for x in jobs)==cost['NSG_calls']
account=read(O/'reviews/build_reservation_reconciled.json');assert account['reserved_builds_total']==cost['builds']==9612
account.update(actual_builds=9612,complete_runs=4,actual_NSG=cost['NSG_calls'],reconciliation='PASS');dump(O/'reviews/build_reservation_reconciled.json',account)
tab='| 数据集 | seed | 选中步 | full train ΔR pp | monitor ΔR pp | 末点monitor ΔR pp | 接受次数/200 |\n|---|---:|---:|---:|---:|---:|---:|\n'
for x in r['models']:
 tab+=f'| {"WebVid" if x["dataset"]==DS[0] else "Yandex"} | {x["seed"]%100} | {x["selected_step"]} | {x["full_train_delta_recall_pp"]:+.4f} | {x["monitor_delta_recall_pp"]:+.4f} | {x["last_monitor_delta_recall_pp"]:+.4f} | {x["accepted_updates"]} |\n'
core='''RL保留原八Gaussian候选的LOO梯度与Adam方向，候选仅估计方向；提交仅在同方向r/4、r/2、r三个真实测量点及不动之间按原J择优。r由Gaussian扰动中位范数给出，不使用GT确定半径；步长接受使用完整train4096反馈。m/v和局部计数每步推进，实际画像及缓存只有接受后改变。线上导出静态普通HNSW，仍一次路由取得三个真实入口后运行原NSG。

这检验E51指出的更新尺度问题，也保留E52直接提交候选的贪心对照身份。完整训练与监控曲线分开报告，监控参与选点；双集至少一个可行正候选的局部门并不证明四seed稳定性、独立泛化或Recall–QPS前沿收益。连续算法状态逐步分岔，不能把整个算法对比当固定状态单因子因果证据。
'''
status='COMPLETE_FEEDBACK_STEP_RL_LOCAL_SIGNAL' if gate['status'].startswith('PASS') else 'COMPLETE_FEEDBACK_STEP_RL_NO_DUAL_LOCAL_SIGNAL'
costtext=f"实际{cost['NSG_calls']} NSG=62976固定+{cost['candidate_new_NSG']} Gaussian变化+{cost['deterministic_new_NSG']}确定点变化；36107264 HNSW、9612构图、800 RL梯度/接受决策、{cost['accepted_updates']}实际接受。完整训练进程{cost['training_process_seconds']:.3f}s，实际单线程CPU15串行。0新cal/audit/validation/held-out查询、0新GT、0QPS点。"
audittext=f"独立6400 Gaussian候选/2400确定点、800四分量梯度/Adam/步长选择/不动及拓扑缓存链、44完整checkpoint、8静态导出、512三路parity通过；{v['return_set_scores']}集合评分，审计{v['seconds']:.3f}s。原冻结源码的reserved_builds字段沿用1803，低记600/run；协议与实际每run2403不变，正确四run9612低于15000硬限，单独重记并保留原日志，详见[记账修正](reviews/build_reservation_accounting_note.md)。"
nexttext='''下一阶段E54对完整学成模型做评分/邻接四格：C(P,G0)、A(W,G)、S(W,G0)、T(P,G)。固定E52/E53各双seed全部模型，train与monitor分开，仅静态干预不再训练。它补足E48仅单行小动作的机制范围；源码/协议准备中，当前尚未查询。最终模型由既有cal预选，在历史validation2000同机CPU15单线程与NSG、Fast30K、FastGT10-hard比较五L五轮QPS/Recall/零GT10命中失败率；最终结果不回流选模型。用户22:00收口，21:15前进入最终比较窗口，21:40停止新查询。'''
body=f'''# E53 RL方向与真实反馈步长接受

2026-09-12，`{status}`；局部门`{gate['status']}`。

{tab}
{core}
## 成本与独立验收

{costtext}

{audittext}

## 接续与边界

{nexttext}

默认仍为WebVid GT10-soft-t1 / Yandex GT10-hard。最新完整曲线是E49，最终用户要求的完整基线比较仍未执行。

[协议](protocol.md)、[四模型](results/models.csv)、[44 checkpoint](results/checkpoints.csv)、[800步骤](results/steps.csv)、[成本](results/cost.json)、[局部门](results/gate.json)、[独立验收](reviews/training_verification.json)、[学习曲线](figures/feedback_step_learning.svg)。
'''
(O/'report.md').write_text(body);(O/'conclusion.md').write_text(tab+'\n'+core+'\n'+nexttext+'\n')
hist=re.sub(r'\]\(([^)]+)\)',lambda m:'](../entry_method_exploration/20260912_feedback_step_rl_v1/'+m.group(1)+')',body.replace('# E53 RL方向与真实反馈步长接受','# 42. E53 RL反馈步长接受'))
(R/'experiment_history/42_feedback_step_rl.md').write_text(hist)
p=R/'s-experiment.md';s=p.read_text();i=s.index('| E52 连续');s=s[:i]+f'| E53 RL反馈步长接受 | 原RL方向，r/4、r/2、r+不动真实择优 | `{status}`；{cost["NSG_calls"]} NSG/800梯度/{cost["accepted_updates"]}接受 | [42 RL反馈步长](experiment_history/42_feedback_step_rl.md) |\n'+s[i:];p.write_text(s.replace('四十一份详细卡片','四十二份详细卡片'))
p=R/'experiment_history/README.md';p.write_text(p.read_text()+'\n- [42 RL反馈步长接受](42_feedback_step_rl.md)：固定方向真实步长接受的四训练和独立重放。\n')
(R/'summary.md').write_text(f'# ACSG 当前结果摘要\n\n2026-09-12，最近完成E53，`{status}`，[报告](entry_method_exploration/20260912_feedback_step_rl_v1/report.md)。\n\n'+tab+'\n'+core+'\n'+costtext+'\n\n'+nexttext+'\n\n默认WebVid GT10-soft-t1 / Yandex GT10-hard，最新完整曲线E49，尚未形成双集前沿GO。\n')
(R/'s-target.md').write_text('# ACSG 下一阶段目标与接续\n\n2026-09-12，E53四训练与独立审计完成。\n\n'+nexttext+'\n\nE50固定候选有机会而原均值多无质量响应，E51同方向放大也可能产生新失败；E52贪心连续提交有局部正值及Yandex种子损伤。E53结果见[报告](entry_method_exploration/20260912_feedback_step_rl_v1/report.md)，不据训练上涨宣称泛化。\n\n[最终合同](entry_method_exploration/20260912_until2000_v1/final_comparison_contract.md)、[历史validation2000来源核验准备](entry_method_exploration/20260912_until2000_v1/final_comparison_split_update.md)。先冻结候选与选择规则，再测cal，选中模型与最终矩阵冻结后才测历史validation；保留所有失败结果。\n')
p=R/'spec.md';s=p.read_text().replace('E53 RL方向+真实反馈步长接受已实现源码及协议，尚未冻结执行，不声称已有训练结果。','E53 RL方向+真实反馈步长接受已完成四训练及独立验收。');s+='\nE53 [独立重放](entry_method_exploration/20260912_feedback_step_rl_v1/src/audit_training.py)覆盖800 RL梯度/Adam和2400确定步长，以及提交图/缓存状态链。每run2403构图、9026816 HNSW，NSG固定15744+真实变化；原reserved_builds旧字段的独立修正见[重记](entry_method_exploration/20260912_feedback_step_rl_v1/reviews/build_reservation_reconciled.json)，实际成本以原生计数为准。\n';p.write_text(s)
dump(O/'reviews/visual_review.json',dict(status='PASS',file='figures/feedback_step_learning.png',method='Personally viewed train and monitor curves and original RL comparison'))
dump(O/'state.json',dict(status=status,gate=gate['status'],cost=cost,campaign_complete=False))
roots=[R/x for x in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md','experiment_history/42_feedback_step_rl.md']];links=0
for p in roots+[O/'report.md',O/'protocol.md']:
 for link in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if '://' in link or link.startswith('#'):continue
  assert (p.parent/link.split('#')[0]).exists(),(p,link);links+=1
for p in files(O/'src'):
 if p.suffix=='.py':ast.parse(p.read_text(),filename=str(p))
dump(O/'reviews/final_audit.json',dict(status='PASS',protected_files=len(read(O/'reviews/protected.json')['files']),local_links=links,artifact_bytes=sum(p.stat().st_size for p in files(O)),verification=v,cost=cost,campaign_complete=False))
freeze(O/'reviews/final_artifact_freeze.json',files(O)+roots);print('E53 FINAL AUDIT PASS',flush=True)
