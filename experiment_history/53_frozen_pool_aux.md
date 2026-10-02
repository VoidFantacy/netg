# E64 今日固定候选扩大历史开发复核

2026-09-13，`COMPLETE_FIXED_POOL_AUX_NO_GATE_PASS`。E63 fit局部正、cal净−1/−2且sham方向反转后，冻结今日7模型，在router_train其余[2048:10000]全7952行复核，不改参数或图。四个可选新端点为E61遗漏、E62评分/拓扑、E63质量；两个sham仅控制。前后3976各自是预锁两半，全部属于辅助选型训练数据。

WebVid四新端点净命中依次+7/−60/+38/−2、失败净+6/+9/+2/+1；Yandex为−74/−78/−24/−18、失败净+8/+8/+2/−2。WebVid纯拓扑的两半+31/+7保留局部收益，但救回11、新增13未过失败门；Yandex所有真实新候选净负。原E63 fit正值及旧cal失败均保留，不从扩样结果推断难度信息本身无效。

预锁门为全池净正、两半非负、失败不增、totalNDC≤+1%；无候选全过，best_all双集baseline。best_new只是四新端点按净命中/失败/成本/固定序诊断排序，WebVid E62_topology、Yandex E63_zero_mass；sham不参与。后续历史开发wall展示这两个真实新候选，晚间最终E34尚未执行。

源query/GT hash及原22048行字节恢复通过，7952与本日fit/cal/audit互斥但已被Fast30K和早期研究使用，不称盲集；任何辅助选型反馈都计训练。0最终validation/held-out访问。

实际222880 NSG/222656 HNSW、14物理源图加载/复制、28 plain/count加载，0新图构建/GT/训练更新/QPS。111328集合/mask、14图字节、224原kernelparity及选择/失败恒等通过，双集native CPU15实际线程1串行，全部退出后分析。首次prepare导入名错误及taskset启动继承CPU8竞态均0查询，后者保留111440预留；一次修正preexec绑核后正常222880，总预留334320，原log/runner/修正封存。

[报告及图](../entry_method_exploration/20260913_until2100_v1/stage5_frozen_pool_aux_v1/report.md) · [协议](../entry_method_exploration/20260913_until2100_v1/stage5_frozen_pool_aux_v1/protocol.md) · [42行指标](../entry_method_exploration/20260913_until2100_v1/stage5_frozen_pool_aux_v1/results/points.csv) · [选择](../entry_method_exploration/20260913_until2100_v1/stage5_frozen_pool_aux_v1/results/selection.json) · [修正](../entry_method_exploration/20260913_until2100_v1/stage5_frozen_pool_aux_v1/launch_repair_amendment.md) · [验收](../entry_method_exploration/20260913_until2100_v1/stage5_frozen_pool_aux_v1/reviews/verification.json)。
