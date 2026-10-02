# E62：遗漏画像的评分与邻接四格

2026-09-13，`COMPLETE_MISSING_FACTORIAL_NO_CAL_GO`。独立版本在本日campaign的`stage3_missing_factorial_v1`。这是E61固定全fit闭式画像的有限因素干预，沿用E48/E54原接口，不是旧RL训练换名重启。

E61虽然改变大量入口，但训练净Recall负，14/20条原全命中query变为零命中。为定位损伤，将原P/G0和遗漏画像W/G交叉成C=(P,G0)、A=(W,G)、S=(W,G0)、T=(P,G)。全部画像/全层有序邻接/节点层级/真实ID逐字验收，保持H815/821、top3、底层NSG、base、raw-IP、GT和L128。S/T加载实际冻结图，普通按W重建不能替代。

数据为每集历史P-fit20K及历史cal/audit各1024；C/A全量恢复E61，交叉态三入口相同才复用C的NSG返回。所有反馈有开发身份，未读取E34最终validation。本轮不新增训练标签GT或梯度更新。

S的fit/cal/audit ΔRecall：WebVid−0.1085/−0.1855/−0.0488 pp，Yandex−0.0445/−0.1953/−0.1074 pp；T为WebVid+0.0070/−0.1758/−0.0293 pp，Yandex−0.0085/−0.0488/−0.0391 pp。预锁cal净正/失败不增/NDC≤+1%下四个S/T均失败，仍选C。WebVid T的fit小正值不抹掉，但不足支持迁移或性能结论；E61 A audit小正值保留。

原14/20个灾难案例中，仅S零/仅T零/两个单独都零/只有联合A零的数量分别WebVid6/4/1/3、Yandex11/7/1/1。评分和拓扑都有固定背景下独立致损，也有交互，不能全部归因单因素。全部11个原命中组有成员得失恒等与逐query交互；这些事后极端组不能当成已能预测的困难查询类别。本轮没有sham构图控制，不归因遗漏目标身份。

实际19030新NSG、177408HNSW、8小图构建、4静态邻接安装；176384集合/mask/缓存复核、88192 C/A路由恢复、8物理图全字节及512三路parity通过。原生阶段29.754秒含加载；其中Yandex曾与一次提前只读分析短暂重叠，首次分析因结果尚未完成退出，加入完成门后重跑通过，原日志与修正保留。该wall不是独占机器性能；0正式QPS。单原生CPU15/线程1串行，已全部退出。

停止同端点强度和单因素移除网格；下一阶段可另行研究保持GT10归属的query质量重权，尚未实现，不以本轮结果保证它有效。正式交付仍需今天新候选与原方法同批QPS–Recall/零命中对比，失败候选也应诚实展示。

[协议](../entry_method_exploration/20260913_until2100_v1/stage3_missing_factorial_v1/protocol.md)、[报告与图](../entry_method_exploration/20260913_until2100_v1/stage3_missing_factorial_v1/report.md)、[所有指标](../entry_method_exploration/20260913_until2100_v1/stage3_missing_factorial_v1/results/points.csv)、[34案例](../entry_method_exploration/20260913_until2100_v1/stage3_missing_factorial_v1/results/catastrophic_cases.csv)、[验收](../entry_method_exploration/20260913_until2100_v1/stage3_missing_factorial_v1/reviews/verification.json)、[调度修正](../entry_method_exploration/20260913_until2100_v1/stage3_missing_factorial_v1/reviews/execution_note.md)。
