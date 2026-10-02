# 104｜E109 完美目标代理信息门

2026-09-20，用户16:00目标中的理论接续，当前执行中。E107/E108已经区分自适应入口、精确表示、小图可检索性与有限beam反馈；本阶段检验新的学习目标是否先有足够信息价值。

仅用原E24 fit20K的预锁2048个等间隔位置，固定原H/NSG/raw-IP/GT。TargetMean用真实GT10目标单位方向均值对单位hub取top3；Coverage按E27冻结的GT10→原hub质量取top3，并列用原GT10 exact分数。对照原GT10 exact3及单位hub exact3，真实K1/K100/L128；不新增K10评测。两个代理均不可部署，只最大化自己的代理，不是实际Recall oracle或上界。

源码/协议/两理论快照在fit数值处理前冻结；源行/real hub ID对齐、整数质量和10、32行×10目标的独立方向/归属及均值检查已通过，约9.6秒，无新GT搜索。当前smoke/main按单线程CPU15串行推进；预定66304 NSG、0新图/梯度训练/正式QPS。

投入门预锁：每个代理在两集两K上对两个控制均值均非负，且每集至少一个共同K对两控制均≥1pp并有校正区间下端>0。16项主对照固定20000次paired bootstrap/99.6875%描述性区间；若都通过优先Coverage，若都失败不训练这两个目标。fit已用于原画像，不能当泛化验证。

[协议](../entry_method_exploration/20260920_until1600_theory_v1/stages/e109_perfect_proxy_gate/protocol.md) · [状态](../entry_method_exploration/20260920_until1600_theory_v1/stages/e109_perfect_proxy_gate/state.json)。
