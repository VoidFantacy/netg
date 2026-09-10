# 加入NSG固定入口基线（2026-09-09）

用户要求最终同时与Fast、NSG比较Recall、QPS和失败查询。原28方法配置已包含Fast20K/30K direct1/3及新方法/因素对照，但没有NSG。本修订新增同批单线程基线比较，不改变已冻结模型、超参数、L或测试集。

## NSG定义

沿用项目`benches/bench_per_query_recall.cpp`的`NSG_Medoid`和`benches/test.cpp`的`Medoid (Baseline)`：从所加载冻结NSG的`index.acsg.enterpoint`固定起跑，调用同一原`search_new(mode=2)`，只有一个入口。无Micro-HNSW和query条件路由；routing NDC为0，入口到query的距离计入graph NDC。K10、L64/128、raw IP、base和图身份与Fast/新方法完全相同。本次没有另建NSG图，也不声称覆盖其他NSG实现/初始化方式。

## 完整比较与计时

现有单线程因素评测正常完成后，顺序运行补充比较，期间不并发训练、编译或其他重任务。新入口复用相同benchmark/search/timing函数，增加固定入口分支；Fast和联合新候选也重新在这个入口计时，避免将新增NSG与旧计时直接拼成主比较。

每个数据集、每个QGT构建，对`validation10K`及`heldout10K`分别同批运行四种方法：NSG-Medoid、历史Fast30K direct3、paired Fast20K direct3、冻结联合候选A+B；每种方法包含L64/128两点。统一单线程，3次独立plain full-batch wall、全批warmup及方法换序，count与GT评分另做。NSG是同一冻结图固定入口，在三个比较批次中重复测量；不能称为三个独立NSG构建。Fast与A+B使用三个独立QGT构建。

所有方法输出按query对齐的Recall@10/hitcount、失败标记及数量/率、route/graph/total NDC。失败严格`Recall@10<0.1`（hits=0）；与两种基线逐query统计rescued/newly_failed，并给出Recall pp、QPS相对变化、失败率pp与相对变化。对当前新候选不增加回退或重新选择。原始Fast1、因素和exact对照完整保留在首轮单线程结果中。

补充NSG先验收：固定入口policy无距离路由、plain/count一致，独立直接调用原kernel的返回ID、距离bits、graph NDC逐项相同。Fast和A+B在新入口的结果必须与已完成单线程结果完全一致；QPS重新测量，不要求相同。

## 输出和状态

新结果保存`baseline_comparison_v1/`，不覆盖`single_thread_v1/`。主报告最终采用四方法同批测量值；原单线程因素报告保留为附录。最终仍按原四点Fast3判定门评估A+B，另外完整列出相对NSG和Fast的三项指标，不因加入较弱基线而改变对Fast的成功标准。
