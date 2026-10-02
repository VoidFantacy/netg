# 26. E37 离线入口画像策略优化

2026-09-12，独立版本`20260912_offline_profile_rl_v1`。状态`COMPLETE_OFFLINE_PROFILE_RL`，开发门`STOP_DUAL_DEVELOPMENT_GATE`，默认未换，无独立正式性能GO。[报告](../entry_method_exploration/20260912_offline_profile_rl_v1/report.md)、[协议](../entry_method_exploration/20260912_offline_profile_rl_v1/protocol.md)、[状态](../entry_method_exploration/20260912_offline_profile_rl_v1/state.json)。

## 动机与实际机制

用户指出E36在每次query中运行选择模型的费用，希望改为离线训练HNSW或入口查询画像，并明确授权推进。E37选择后者：固定当前GT10锚点P和真实H815/821，仅用train4096的单位query二阶矩生成固定16方向B；训练256个共享系数，W=normalize(P+0.25(PB)(tanh(X)/4)Bᵀ)。零参数逐字恢复P。

一次Gaussian策略动作是一份完整静态画像参数；每个候选真实重建M16/efConstruction200/seed20260828的普通HNSW，ef10 direct3进入原NSG L128/K10。奖励来自实际联合命中增量、总NDC与零命中惩罚及画像漂移；C++先搜索，Python后评分GT。没有固定C8代理、未知标签当零、单入口命中相加或旧56组合标签复用。

RL使用8独立扰动/LOO score-function；ES控制使用4对正负扰动，保持相同表示、batch与调用/训练预算。二者估计同一高斯平滑目标，不是PPO与另一种神经模型的对决。E28教师代理、E32旧C8直接奖励、E33只删原边与E36在线换点分别保留历史身份。本次通过画像改变重建后的小图，没有独立边策略或大图训练。[方法依据](../entry_method_exploration/20260912_offline_profile_rl_v1/method_basis.md)、[源码](../entry_method_exploration/20260912_offline_profile_rl_v1/src/train.py)。

## 数据、选择与执行

两集各train4096/monitor1024，来自E24历史fit20K，cal/audit各历史1024；角色源行互斥但上游画像及开发数据均有历史暴露，非全管线盲测。B只用train；8次全部训练及独立复算通过后才准备cal，按cal U/总NDC/seed冻结再准备audit；没有新validation/held-out原始输入读取/hash或新GT。

两集×RL/ES×seed21/22，每次200更新、8候选×batch128；step0和20..200记录确定性train512/monitor1024。monitor U与graph NDC门选非零checkpoint，选中和末点物理画像/图均永久保存；cal只选择臂内seed。开发门要求每集主RL cal≥+0.10pp、audit>0且total NDC≤+1%，没有按结果放宽。

## 结果和解释

离线训练静态画像、再重建普通HNSW的部署形式已实现，但本轮RL没有获得稳定检索增量。所选RL的WebVid cal/audit为−0.1172/−0.0391pp，Yandex为−0.0195/+0.0391pp，双集开发门停止。成对扰动ES在这四项略好，RL对ES的audit配对区间均包含0；不能归因出RL的稳定额外价值。

在线不再运行query MLP；L128相对原GT10的QPS变化仅+0.069%/+0.078%。完整五L中WebVid RL Recall全部略降，Yandex四点微升、L64下降，尚无稳定跨数据集前沿优势。ES也有中高L负点。保留这些局部正值，默认不替换。

| 数据 | cal所选模型 | cal ΔRecall pp | audit ΔRecall pp | audit Δtotal NDC % | audit L128 ΔQPS % |
|---|---|---|---|---|---|
| WebVid | RL_seed21 | -0.117188 | -0.039062 | -0.028363 | 0.068835 |
| WebVid | ES_seed21 | 0.117188 | 0.068359 | 0.191849 | -0.174948 |
| Yandex-IP | RL_seed22 | -0.019531 | 0.039062 | -0.042194 | 0.077532 |
| Yandex-IP | ES_seed22 | 0.048828 | 0.048828 | -0.067028 | -0.029920 |

全部seed cal/audit及选中/末点训练曲线见报告，不回写audit选择。NSG/Fast30K/原GT10/主RL/主ES共50点，每集历史audit1024，L64/128/256/400/800各5轮完整plain wall；同模型五L保持画像/物理图/入口相同。失败为GT10零命中，配对挽救和新增失败完整报告。共同Recall区间内log-QPS插值是描述值，不能当新实测。Fast30K沿用不同历史训练量/seed，不能把全部基线差别归给本轮。

## 成本、核验及未测范围

实际NSG2,211,520次/预留2,212,320次/硬上限2,800,000；1600更新、12800采样画像，训练/预检重建12912次普通HNSW。两训练进程802.294/733.449s，累计1535.743s，峰值RSS约5.458/9.956GiB。构图/真实反馈包含在训练进程成本内；原GT/原画像、准备编译、后续复算/评测另计。在线只一次普通HNSW3，不再做E36的query投影/MLP/组合枚举，但画像变化仍可影响原路由/NSG工作量。

正式查询CPU15、实际进程/OMP/BLAS/MKL1线程、方法及数据集串行、无同时训练或重分析。完整timer含路由、映射、NSG和输出；count/GT/hash/IO/build在外。L128 route-only/graph-only单独测量，不相加充当总wall。

预检逐字恢复原GT10 fit10240输出和小图，验证Gaussian/ES/LOO/Adam数学、非法输入与确定构图。独立复算12800动作画像hash、全部真实GT奖励、1600更新、88checkpoint及选择，最大参数重放误差低于5e−16；冻结图在无hook的E34原评测binary中回归1280行，旧cal/audit基线再回归4096行。80部署点和250轮wall输出、五L图/入口、CSV/Excel和图表都保留验收链。

旧E36整目录SHA、实际上游38文件SHA、此前36090文件大小/mtime保护；独立版本不覆盖旧源/图/标签/模型/结果。没有中途改训练预算、重新选audit模型或恢复旧runner。0新validation/held-out、0默认替换；训练完成和历史曲线并不意味着独立性能GO。

## 原件、复核与接续

- [锁定配置](../entry_method_exploration/20260912_offline_profile_rl_v1/config.locked.json)、[源快照](../entry_method_exploration/20260912_offline_profile_rl_v1/source_before/summary.md)、[真实搜索环境](../entry_method_exploration/20260912_offline_profile_rl_v1/src/environment.cpp)、[部署](../entry_method_exploration/20260912_offline_profile_rl_v1/src/deploy.py)。
- [训练审计](../entry_method_exploration/20260912_offline_profile_rl_v1/reviews/training_verification.json)、[模型冻结](../entry_method_exploration/20260912_offline_profile_rl_v1/reviews/models_after_training.json)、[cal选择冻结](../entry_method_exploration/20260912_offline_profile_rl_v1/reviews/selection_before_audit.json)、[开发门](../entry_method_exploration/20260912_offline_profile_rl_v1/results/development_gate.json)。
- [完整原值](../entry_method_exploration/20260912_offline_profile_rl_v1/results/points.csv)、[配对区间](../entry_method_exploration/20260912_offline_profile_rl_v1/results/paired.csv)、[逐query](../entry_method_exploration/20260912_offline_profile_rl_v1/results/query_results.csv)、[Excel](../entry_method_exploration/20260912_offline_profile_rl_v1/results/offline_profile_rl.xlsx)、[Recall–QPS](../entry_method_exploration/20260912_offline_profile_rl_v1/figures/recall_qps.svg)。
- [调用账](../entry_method_exploration/20260912_offline_profile_rl_v1/logs/jobs.json)、[训练进程](../entry_method_exploration/20260912_offline_profile_rl_v1/logs/training_processes.json)、[完整验收](../entry_method_exploration/20260912_offline_profile_rl_v1/reviews/final_audit.json)；最终冻结身份保存为本版本的`reviews/final_artifact_freeze.json`。

冻结版本的prepare/train/deploy拒绝重复job/output，原地命令不可当作新执行授权。下一阶段首先利用已有反馈区分噪声、表示与确定部署差距；具体产物、控制、门和新对话指令见[s-target](../s-target.md)，此诊断未实施、无排队任务。保留E24及E36各自局部正信号；本次停止只约束当前共享画像参数化与预算，不能泛化为所有离线RL/画像学习不可能。
