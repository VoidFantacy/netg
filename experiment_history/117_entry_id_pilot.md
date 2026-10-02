# 117｜E116：固定GT10路由的H外入口绑定

2026-09-20，用户“测试一下看看”授权的独立试验完成，`STOP_ENTRY_ID_PILOT`。原画像、小图和主搜索不变；只将16个画像槽位的真实入口绑定替换为互异H外节点。不是重启E22的H内单入口重映射，也不是E112的首行覆盖目标。

两集各10K训练查询提出每槽4频率+4几何候选，另10K实际三入口标注并按奇偶分两半。Cost要求两半K1/K100均不损伤且有正平均增量、平均配对搜索耗时均不增加；RecallControl去掉时间条件。每模型至多16编辑，双集4份映射冻结后在E105已曝光4096条/集审计；与本轮训练无字节重叠，但不是新盲测。实际K1/K100、L128、单线程完整wall各3轮。

| 数据 | K | Cost ΔRecall pp | 98.75%配对区间 | ΔQPS |
|---|---:|---:|---|---:|
| WebVid | 1 | −0.073242 | [−0.219727,+0.048828] | +0.179% |
| WebVid | 100 | +0.000977 | [−0.044678,+0.055788] | −0.789% |
| Yandex | 1 | +0.024414 | [−0.097656,+0.170898] | +0.422% |
| Yandex | 100 | −0.007324 | [−0.094606,+0.075684] | −0.305% |

Cost改变Web/Y的259/309条query入口；K1救回/新增失败分别1/4、3/2。K100分别净增4、净减30个GT命中。训练召回条件通过775/783个绑定，加时间条件后只剩44/68个，但并未转成稳定线上增益。RecallControl四项召回区间也跨0；全部速度差不足0.8%，不视为稳定加速/减速。

实际1,711,520次主搜索、345,760次路由，12点/36轮完整wall；控制器484.627秒，编译另18.398秒，最大RSS10.086GiB。无新GT/图/画像或梯度训练，有真实效用/时间标注及离散映射选择。训练K1标签按固定L的K100首返回复用且实际K1/链接E99核验；审计分别实际运行两个K。

全量plain/count、原默认E105恢复、真实入口消费、模型/候选身份、原画像/小图/生产源码、数据角色和独立评分验收通过。当前停止该冻结版本及追加调参，条件五预算比较未启动，默认Web soft/Y hard与生产E99保持。不能由此否定所有H外入口，尚未分离提议器、组合冲突和统计迁移的因果份额。

[完整报告](../entry_method_exploration/20260920_entry_id_pilot_v1/report.md) · [冻结协议](../entry_method_exploration/20260920_entry_id_pilot_v1/protocol.md) · [主门](../entry_method_exploration/20260920_entry_id_pilot_v1/results/gate.json) · [全部原值](../entry_method_exploration/20260920_entry_id_pilot_v1/results/metrics.csv) · [模型选择](../entry_method_exploration/20260920_entry_id_pilot_v1/reviews/models_frozen.json) · [独立核验](../entry_method_exploration/20260920_entry_id_pilot_v1/reviews/completion_audit.json) · [执行账](../entry_method_exploration/20260920_entry_id_pilot_v1/reviews/jobs.json)。
