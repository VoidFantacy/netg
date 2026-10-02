# 76｜完整策略收益提出目标后实际单边筛选（E87）

2026-09-13第9会话，双集预锁门FAIL，停止此效用目标提议/单边筛选版本。Web局部修复保留，Y零更新不称新方法收益。0新QPS。

E86筛选原几何候选，本版只用fit真实P优于compact的完整三入口查询，向P独有hub的最高compact画像slot提出边。源为compact首返回slot，正命中差为提议权重，每源最高票且至少2query支持，最多64/集。完整策略差只提议，不作单边因果信用；候选逐条实际加边测全fit原NSG，再按原全正/两半非负/失败不增/成本门筛选，合并重新实测。在线原compact W、真实H/原NSG/rawIP及原全部边保持，静态图一次路由，无新模型预测。

Web896个P更好query产生1542有效事件/1333票对，53候选，与E84/E86仅6/4重合；Y267产生409事件/384对，9候选，重合0/0。Web53边17正/3负/33平，16接受，独立收益和118、实际合并94，3query非加性；Y9全部命中差0、无接受边，两个最终图逐字等于原compact。完整提议、合法性、权重/支持、目标及近邻控制均独立复算。

| aux7952 | 对P：净命中/失败变化 | 对compact | 对E84 | 对E86 | 对控制 |
|---|---|---|---|---|---|
| Web | −43/+8 | +16/−3 | −26/+1 | −2/0 | +16/−3 |
| Y | +120/−13 | 0/0 | +4/0 | +4/0 | 0/0 |

Web fit并图+94/失败−4、两半41/53；aux对compact两半7/9、救回3/新增0，但不及P/E84/E86。原compact对P正收益820保留809、丢11、新增4；避免原损失26，新增/放大损失3。Y所有相对其它图的改善是回到compact，不是学习增益。原门停止，不扩候选、阈值或按aux重训。

新NSG194718=训练414（111新唯一键plain/count+192回归）+辅助194304；HNSW2914432=训练2720512+辅助193920。6物理导出含4非零边安装（包括2首边回归图）和2个Y零更新副本；0普通构图/编译/GT/梯度。提议进程tool wall0.411s含import/hash/冻结，单独数学时间未知；训练53.401s、辅助150.562s为操作wall，不作QPS。继承GT/P与E86原compact缓存成本分开。

复用同SHA E86 route helper/E69 NSG/E73 evaluator，实际CPU15、进程和各数值库1线程，所有工具退出0。154单边变化patch、111新键、合并图/6图完整bytes、原32三路/首边128真实回归、96960集合/mask、63616四旧对照全字段、80800七slot、384原kernel均通过。413失败并集、173状态变化、2478个六配置全GT/入口/返回单元保存。

fit20K含旧train/monitor；aux7952/两半、cal/audit历史暴露，接受反馈算训练。E34原始query/GT/row未打开，held-out未读。最终准备件只读E34/E74配置、模型及输入stat；查历史23旧汇总在模型冻结后且未回流任何选择。

[报告](../entry_method_exploration/20260913_until2100_v1/stage28_utility_proposals_v1/report.md) · [协议](../entry_method_exploration/20260913_until2100_v1/stage28_utility_proposals_v1/protocol.md) · [提议](../entry_method_exploration/20260913_until2100_v1/stage28_utility_proposals_v1/src/propose.py) · [训练](../entry_method_exploration/20260913_until2100_v1/stage28_utility_proposals_v1/src/train.py) · [门](../entry_method_exploration/20260913_until2100_v1/stage28_utility_proposals_v1/results/gate.json) · [成本](../entry_method_exploration/20260913_until2100_v1/stage28_utility_proposals_v1/results/cost.json) · [独立提议核验](../entry_method_exploration/20260913_until2100_v1/stage28_utility_proposals_v1/reviews/proposals_independent.json) · [训练核验](../entry_method_exploration/20260913_until2100_v1/stage28_utility_proposals_v1/reviews/training_verification.json) · [查询核验](../entry_method_exploration/20260913_until2100_v1/stage28_utility_proposals_v1/reviews/verification.json)
