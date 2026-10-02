from common import *

assert (O/'report.md').exists()
conclusion=(O/'conclusion.md').read_text().strip();headline=(O/'results/headline_table.md').read_text();a=read(O/'results/analysis.json');gate=read(O/'results/development_gate.json')
link='entry_method_exploration/20260912_offline_profile_rl_v1';history='experiment_history/26_offline_profile_rl.md'
old=(R/'summary.md').read_text();assert old==(O/'source_before/summary.md').read_text(),'root summary changed during execution'
(R/'summary.md').write_text(f'''# ACSG 当前结果摘要

2026-09-12。最近完成E37离线画像策略优化，状态`COMPLETE_OFFLINE_PROFILE_RL`。[完整报告]({link}/report.md)、[历史26]({history})、[验收]({link}/reviews/final_audit.json)。

{conclusion}

{headline}
表为各臂按cal冻结选择、L128相对原GT10；WebVid用GT10-soft-t1，Yandex用GT10-hard。双集开发门`{gate['status']}`。完整50点、五轮单线程Recall–QPS和全部seed正负结果见[曲线]({link}/figures/recall_qps.svg)/[Excel]({link}/results/offline_profile_rl.xlsx)，不以单L或小幅波动声称稳定性能收益。

## 实际执行与证据边界

两集×RL/成对扰动ES×双seed，每次200更新；12800个采样画像都重建普通HNSW并获得原NSG真实反馈。在线为raw query→一次HNSW top3→原NSG，不运行E36的MLP。一步Gaussian参数策略与ES估计同一平滑目标，256个共享系数、rank16固定，不将名称差异写成新表示能力。

每集train4096/monitor1024、cal/audit各1024源行互斥但历史使用；画像也来自历史fit，非盲测。实际NSG2,211,520次，训练/预检HNSW重建12,912次，8次训练进程累计1535.743s；不含历史GT和原画像构建。全部1600更新、88checkpoint、独立部署和250轮wall复核，实际查询线程1。0新validation/held-out原始输入读取/hash，默认未换。

旧源码/图/标签/模型/日志与E36结果保留。E24原GT10的局部贡献和E36 Yandex的局部收益分别成立于各自证据范围，不因E37开发门停止而被抹去。下一步先用本轮已有真实反馈区分估计噪声、画像表达与确定部署差异，详见[s-target](s-target.md)；尚未运行该诊断，无追加训练或排队任务。
''')
old=(R/'s-target.md').read_text();assert old==(O/'source_before/s-target.md').read_text(),'root target changed during execution'
(R/'s-target.md').write_text(f'''# ACSG 下一阶段方向与实验接续

2026-09-12。E37已完成用户授权的离线画像学习、普通HNSW重建、独立验收及完整五L成本比较；[历史26]({history})、[完整报告]({link}/report.md)。用户意图是把学习放在离线，线上仍由普通HNSW选入口；该部署形式已实现。以下为尚未实施的后续设计，不追加冻结版本预算。

## 当前依据

{conclusion}

{headline}
两臂都是同一256参数静态画像空间，RL与ES的差别是高斯扰动梯度估计器。8次训练已完整结束；单独的monitor正值未建立开发稳定收益。NDC、同L质量、独立完整wall及历史数据暴露必须分开解释。

'''+(O/'src/target_body.md').read_text())
old=(R/'spec.md').read_text();assert old==(O/'source_before/spec.md').read_text(),'root spec changed during execution'
old=old.replace('架构与实现事实核对至2026-09-11（E36 query相关三入口换点训练/部署已验收；原Fast/NSG kernel不变）','架构与实现事实核对至2026-09-12（E37离线画像训练、普通HNSW重建及部署已验收；原Fast/NSG kernel不变）',1)
(R/'spec.md').write_text(old.rstrip()+'\n\n'+(O/'src/spec_addition.md').read_text().lstrip())
card=f'''# 26. E37 离线入口画像策略优化

2026-09-12，独立版本`20260912_offline_profile_rl_v1`。状态`COMPLETE_OFFLINE_PROFILE_RL`，开发门`{gate['status']}`，默认未换，无独立正式性能GO。[报告](../{link}/report.md)、[协议](../{link}/protocol.md)、[状态](../{link}/state.json)。

## 动机与实际机制

用户指出E36在每次query中运行选择模型的费用，希望改为离线训练HNSW或入口查询画像，并明确授权推进。E37选择后者：固定当前GT10锚点P和真实H815/821，仅用train4096的单位query二阶矩生成固定16方向B；训练256个共享系数，W=normalize(P+0.25(PB)(tanh(X)/4)Bᵀ)。零参数逐字恢复P。

一次Gaussian策略动作是一份完整静态画像参数；每个候选真实重建M16/efConstruction200/seed20260828的普通HNSW，ef10 direct3进入原NSG L128/K10。奖励来自实际联合命中增量、总NDC与零命中惩罚及画像漂移；C++先搜索，Python后评分GT。没有固定C8代理、未知标签当零、单入口命中相加或旧56组合标签复用。

RL使用8独立扰动/LOO score-function；ES控制使用4对正负扰动，保持相同表示、batch与调用/训练预算。二者估计同一高斯平滑目标，不是PPO与另一种神经模型的对决。E28教师代理、E32旧C8直接奖励、E33只删原边与E36在线换点分别保留历史身份。本次通过画像改变重建后的小图，没有独立边策略或大图训练。[方法依据](../{link}/method_basis.md)、[源码](../{link}/src/train.py)。

## 数据、选择与执行

两集各train4096/monitor1024，来自E24历史fit20K，cal/audit各历史1024；角色源行互斥但上游画像及开发数据均有历史暴露，非全管线盲测。B只用train；8次全部训练及独立复算通过后才准备cal，按cal U/总NDC/seed冻结再准备audit；没有新validation/held-out原始输入读取/hash或新GT。

两集×RL/ES×seed21/22，每次200更新、8候选×batch128；step0和20..200记录确定性train512/monitor1024。monitor U与graph NDC门选非零checkpoint，选中和末点物理画像/图均永久保存；cal只选择臂内seed。开发门要求每集主RL cal≥+0.10pp、audit>0且total NDC≤+1%，没有按结果放宽。

## 结果和解释

{conclusion}

{headline}
全部seed cal/audit及选中/末点训练曲线见报告，不回写audit选择。NSG/Fast30K/原GT10/主RL/主ES共50点，每集历史audit1024，L64/128/256/400/800各5轮完整plain wall；同模型五L保持画像/物理图/入口相同。失败为GT10零命中，配对挽救和新增失败完整报告。共同Recall区间内log-QPS插值是描述值，不能当新实测。Fast30K沿用不同历史训练量/seed，不能把全部基线差别归给本轮。

## 成本、核验及未测范围

实际NSG2,211,520次/预留2,212,320次/硬上限2,800,000；1600更新、12800采样画像，训练/预检重建12912次普通HNSW。两训练进程802.294/733.449s，累计1535.743s，峰值RSS约5.458/9.956GiB。构图/真实反馈包含在训练进程成本内；原GT/原画像、准备编译、后续复算/评测另计。在线只一次普通HNSW3，不再做E36的query投影/MLP/组合枚举，但画像变化仍可影响原路由/NSG工作量。

正式查询CPU15、实际进程/OMP/BLAS/MKL1线程、方法及数据集串行、无同时训练或重分析。完整timer含路由、映射、NSG和输出；count/GT/hash/IO/build在外。L128 route-only/graph-only单独测量，不相加充当总wall。

预检逐字恢复原GT10 fit10240输出和小图，验证Gaussian/ES/LOO/Adam数学、非法输入与确定构图。独立复算12800动作画像hash、全部真实GT奖励、1600更新、88checkpoint及选择，最大参数重放误差低于5e−16；冻结图在无hook的E34原评测binary中回归1280行，旧cal/audit基线再回归4096行。80部署点和250轮wall输出、五L图/入口、CSV/Excel和图表都保留验收链。

旧E36整目录SHA、实际上游38文件SHA、此前36090文件大小/mtime保护；独立版本不覆盖旧源/图/标签/模型/结果。没有中途改训练预算、重新选audit模型或恢复旧runner。0新validation/held-out、0默认替换；训练完成和历史曲线并不意味着独立性能GO。

## 原件、复核与接续

- [锁定配置](../{link}/config.locked.json)、[源快照](../{link}/source_before/summary.md)、[真实搜索环境](../{link}/src/environment.cpp)、[部署](../{link}/src/deploy.py)。
- [训练审计](../{link}/reviews/training_verification.json)、[模型冻结](../{link}/reviews/models_after_training.json)、[cal选择冻结](../{link}/reviews/selection_before_audit.json)、[开发门](../{link}/results/development_gate.json)。
- [完整原值](../{link}/results/points.csv)、[配对区间](../{link}/results/paired.csv)、[逐query](../{link}/results/query_results.csv)、[Excel](../{link}/results/offline_profile_rl.xlsx)、[Recall–QPS](../{link}/figures/recall_qps.svg)。
- [调用账](../{link}/logs/jobs.json)、[训练进程](../{link}/logs/training_processes.json)、[完整验收](../{link}/reviews/final_audit.json)；最终冻结身份保存为本版本的`reviews/final_artifact_freeze.json`。

冻结版本的prepare/train/deploy拒绝重复job/output，原地命令不可当作新执行授权。下一阶段首先利用已有反馈区分噪声、表示与确定部署差距；具体产物、控制、门和新对话指令见[s-target](../s-target.md)，此诊断未实施、无排队任务。保留E24及E36各自局部正信号；本次停止只约束当前共享画像参数化与预算，不能泛化为所有离线RL/画像学习不可能。
'''
assert not (R/history).exists();(R/history).write_text(card)
p=R/'experiment_history/README.md';t=p.read_text();assert t==(O/'source_before/history_README.md').read_text();needle='\n\n## 写入规则'
t=t.replace(needle,'\n| [26 离线画像RL](26_offline_profile_rl.md) | E37：真实HNSW重建→NSG奖励、Gaussian RL/成对ES双seed、静态画像部署、50点250轮单线程曲线 |'+needle,1);p.write_text(t)
p=R/'s-experiment.md';t=p.read_text();assert t==(O/'source_before/s-experiment.md').read_text();t=t.replace('更新截至2026-09-11','更新截至2026-09-12',1)
row='| E37 离线画像策略优化 | 真实候选画像重建HNSW→原NSG奖励，两臂双seed共8×200更新，静态导出、50点250轮单线程wall | `COMPLETE_OFFLINE_PROFILE_RL`；主RL双集cal负值、audit混合，开发门停止；ES局部正值，无稳定RL增量，默认未换 | [26 离线画像RL](experiment_history/26_offline_profile_rl.md) |\n'
t=t.replace('| E36 query相关三入口换点 |',row+'| E36 query相关三入口换点 |',1).replace('当前最近完成实验已为E36','当前最近完成实验已为E37').replace('二十四份详细卡片','二十六份详细卡片');p.write_text(t)
print('ROOTS_AND_HISTORY_WRITTEN',flush=True)
