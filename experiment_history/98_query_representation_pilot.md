# 98｜E104 查询侧非线性表示 pilot

2026-09-20，用户明确“验证吧”后执行。状态 **STOP_REPRESENTATION**：两集各2048 fit、512历史cal，真实K1/K100、L128；联合效用余量通过，但固定r16查询MLP未通过开发门，按预锁协议不进入完整QPS。默认Web soft/Yandex hard、生产E99保持，E103仍是最新完整前沿。

固定底库/raw-IP/NSG/P与原Micro-HNSW；QLinear/QMLP同参数量，WFree为不逐行归一化的自由静态画像控制。三者同56实测集合监督、分数anchor、seed20260920、Adam1e-3、40epoch；六模型只训练一次。全部模型冻结后才打开cal query/GT。WFree单独按原M16/efConstruction200构建普通HNSW，query模型复用原图。

cal真实ANN结果相对当前GT10：QMLP的Web R1/R100 −0.9766/−0.1152pp，Yandex −1.3672/−1.0527pp。WFree分别+0.7813/+0.6074pp、+1.1719/+0.4902pp；四个WFree正值及QMLP变化的描述性95%区间均跨0，且没有完整wall，不能宣布稳定替换。QMLP在Web救回/新增K1失败17/22，Yandex为5/12；Yandex K100零命中4→8。

真实收益余量仍存在，训练loss均下降；但QMLP的全P精确路由在cal也不及精确Identity，因此不能只归因于小图近似。QMLP实际ANN有93.95%/61.13%动作不在原56集合内。事后只读缓存诊断中，把同一模型限制在C8，得到很小的开发正值；WFree反而全H更好，故“走出候选池必然损伤”不成立。该诊断不训练/不新增搜索、不改变停止门。

实际655808次NSG、36000次小图路由、6次训练、2次WFree小图构建；0新GT/大图/K10/正式QPS。训练11.61秒、搜索子进程含加载约314.80秒、搜索峰值RSS约9.96GiB。顺序/原kernel一致性、独立GT重评分、Identity原样恢复、C++/PyTorch编码一致性及实际支持动作的ID/距离bits/NDC回归通过。数据角色、成本与保护范围见原报告，不使用旧性能改名。

证据：[协议](../entry_method_exploration/20260920_query_representation_pilot_v1/protocol.md) · [报告和图](../entry_method_exploration/20260920_query_representation_pilot_v1/report.md) · [完整CSV](../entry_method_exploration/20260920_query_representation_pilot_v1/results/quality_metrics.csv) · [表示门](../entry_method_exploration/20260920_query_representation_pilot_v1/reviews/representation_gate.json) · [缓存诊断](../entry_method_exploration/20260920_query_representation_pilot_v1/results/cached_support_diagnostic.json) · [完成审计](../entry_method_exploration/20260920_query_representation_pilot_v1/reviews/completion_audit.json)。
