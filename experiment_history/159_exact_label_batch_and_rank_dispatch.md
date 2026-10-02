# 159 精确标签批处理和消费长度的共享工程检查

2026-09-30，固定两集旧fit各1024条、batch256/1024×k100/10，1预热+3轮交错起点。主比较batch1024/k100费用门通过。Web/Y均值费用比为0.979572/0.348884，消费前10有序ID改变0/0条。

所有四格和计时轮保留；原baseline全100 ID/距离bits恢复154，同配置重复hash一致。全部81920个消费距离单元及32条独立float64全库top11核验通过。32768精确query调用含预热/重复；独立float64另记，0新NSG/ANN/画像/图。

这是8线程离线标签search-loop，不是ANN QPS或完整构建费用；样本身份不等于完整20K身份。主批处理费用门通过，可进入另行冻结的共享完整构建检查。必须对Default与低标签候选一致应用，并核验完整H/W/小图；本阶段不能直接更新旧总费用或引用旧线上质量为新模型质量。

[完整报告](../entry_method_exploration/20260930_theory_until2200_v1/research/exact_label_dispatch_v1/report.md) · [全部结果](../entry_method_exploration/20260930_theory_until2200_v1/research/exact_label_dispatch_v1/results/summary.json) · [核验](../entry_method_exploration/20260930_theory_until2200_v1/research/exact_label_dispatch_v1/reviews/independent_audit.json)。
