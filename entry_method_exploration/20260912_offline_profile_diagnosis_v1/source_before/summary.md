# ACSG 当前结果摘要

2026-09-12。最近完成E37离线画像策略优化，状态`COMPLETE_OFFLINE_PROFILE_RL`。[完整报告](entry_method_exploration/20260912_offline_profile_rl_v1/report.md)、[历史26](experiment_history/26_offline_profile_rl.md)、[验收](entry_method_exploration/20260912_offline_profile_rl_v1/reviews/final_audit.json)。

离线训练静态画像、再重建普通HNSW的部署形式已实现，但本轮RL没有获得稳定检索增量。所选RL的WebVid cal/audit为−0.1172/−0.0391pp，Yandex为−0.0195/+0.0391pp，双集开发门停止。成对扰动ES在这四项略好，RL对ES的audit配对区间均包含0；不能归因出RL的稳定额外价值。

在线不再运行query MLP；L128相对原GT10的QPS变化仅+0.069%/+0.078%。完整五L中WebVid RL Recall全部略降，Yandex四点微升、L64下降，尚无稳定跨数据集前沿优势。ES也有中高L负点。保留这些局部正值，默认不替换。

| 数据 | cal所选模型 | cal ΔRecall pp | audit ΔRecall pp | audit Δtotal NDC % | audit L128 ΔQPS % |
|---|---|---|---|---|---|
| WebVid | RL_seed21 | -0.117188 | -0.039062 | -0.028363 | 0.068835 |
| WebVid | ES_seed21 | 0.117188 | 0.068359 | 0.191849 | -0.174948 |
| Yandex-IP | RL_seed22 | -0.019531 | 0.039062 | -0.042194 | 0.077532 |
| Yandex-IP | ES_seed22 | 0.048828 | 0.048828 | -0.067028 | -0.029920 |

表为各臂按cal冻结选择、L128相对原GT10；WebVid用GT10-soft-t1，Yandex用GT10-hard。双集开发门`STOP_DUAL_DEVELOPMENT_GATE`。完整50点、五轮单线程Recall–QPS和全部seed正负结果见[曲线](entry_method_exploration/20260912_offline_profile_rl_v1/figures/recall_qps.svg)/[Excel](entry_method_exploration/20260912_offline_profile_rl_v1/results/offline_profile_rl.xlsx)，不以单L或小幅波动声称稳定性能收益。

## 实际执行与证据边界

两集×RL/成对扰动ES×双seed，每次200更新；12800个采样画像都重建普通HNSW并获得原NSG真实反馈。在线为raw query→一次HNSW top3→原NSG，不运行E36的MLP。一步Gaussian参数策略与ES估计同一平滑目标，256个共享系数、rank16固定，不将名称差异写成新表示能力。

每集train4096/monitor1024、cal/audit各1024源行互斥但历史使用；画像也来自历史fit，非盲测。实际NSG2,211,520次，训练/预检HNSW重建12,912次，8次训练进程累计1535.743s；不含历史GT和原画像构建。全部1600更新、88checkpoint、独立部署和250轮wall复核，实际查询线程1。0新validation/held-out原始输入读取/hash，默认未换。

旧源码/图/标签/模型/日志与E36结果保留。E24原GT10的局部贡献和E36 Yandex的局部收益分别成立于各自证据范围，不因E37开发门停止而被抹去。下一步先用本轮已有真实反馈区分估计噪声、画像表达与确定部署差异，详见[s-target](s-target.md)；尚未运行该诊断，无追加训练或排队任务。
