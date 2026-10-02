# ACSG 当前实验总结

> 更新至2026-09-10夜间。最近E26已完成；本轮E25/E26共同检验选择性保留改道。实现见[spec.md](spec.md)，接续见[s-target.md](s-target.md)，历史见[s-experiment.md](s-experiment.md)。

## 当前结论

**尚未得到稳定保留有效改道、减少受损查询并改善端到端性能的方法。** E25门控在WebVid小幅修复质量但增加时间，在Yandex丢掉大多数收益；E26单路画像收缩消除了双路结构成本，却同时损失有效改道并产生新损伤。E26状态`SHRINKAGE_DID_NOT_STABILIZE_SELECTIVITY_NO_FORMAL_GO`，全部预定阶段收口。

## E26实际方法与选择

固定A0=E24 matched Fast20K/GT1硬，A1=E24按旧cal选定WebVid GT10软、Yandex GT10硬。只测试`normalize((1−α)W0+αW1)`的α0.25/0.50/0.75，在线一份画像图、一次路由、一次原NSG；H/base/raw-IP/NSG不变，没有新训练或全H标签。两数据集均按cal规则冻结α0.75，但三个候选在cal都未达目标，audit与validation也未达标。

## 收益保留与损失迁移

validation合并L64/128，单位query×L事件。R/Rh分别为原正事件/正命中保留；A_all/Ah_all为包含新增损伤的全部受损事件/负命中净减少。目标前两项≥75%、后两项≥25%，且净命中≥max(0,A1净命中)。

| 数据集 | R | Rh | A_all | Ah_all | 净命中 vs A0 / A1原净命中 |
|---|---|---|---|---|---|
| WebVid | 64.62% | 61.07% | 14.02% | 9.28% | -28 / +91 |
| Yandex-IP | 68.92% | 68.48% | 22.58% | 24.32% | +66 / +91 |

WebVid：原正命中619保留378，另产生73新/放大正命中；原负命中528避免153，但新增/加重104，最终损失479。
Yandex-IP：原正命中276保留189，另产生17新/放大正命中；原负命中185避免87，但新增/加重42，最终损失140。

按两个L任一受损去重，WebVid144→124条、Yandex45→33条，但原有效query仅保留103/158、33/47。事件数、幅度和独立query口径分开，不能只报“受损更少”。新画像可产生第三套入口；相同实际三入口的所有结果bits和graph NDC相同已验收。

## 单线程五点性能

相对本轮同时重测的A1/E24；QPS为三次独立warm/plain中位数。

| 数据集 | L | ΔRecall pp | ΔQPS % |
|---|---|---|---|
| WebVid | 64 | -0.495 | -0.85 |
| WebVid | 128 | -0.100 | -0.39 |
| WebVid | 256 | -0.170 | -0.21 |
| WebVid | 400 | -0.045 | -0.13 |
| WebVid | 800 | +0.005 | -0.20 |
| Yandex-IP | 64 | -0.055 | -0.14 |
| Yandex-IP | 128 | -0.070 | -0.38 |
| Yandex-IP | 256 | -0.065 | +0.31 |
| Yandex-IP | 400 | -0.105 | -0.90 |
| Yandex-IP | 800 | -0.060 | +0.08 |

十点九个Recall下降，唯一正值WebVid L800仅+0.005pp且QPS下降；无稳定同L双升。WebVid L64描述性95%配对query区间[−0.940,−0.085]pp，其余九点跨0；未多重校正，单构建历史validation不足以正式GO。NSG/Fast30K/Fast20K和全部原值、每轮前沿均保留，不用粗网格连线宣称等Recall加速。

## 与E25合看

E25状态`SELECTIVITY_NOT_GENERALIZED_NO_FORMAL_GO`。WebVid主DualGate在validation保留80.66%有效事件、避免24.77%受损事件，相对A1五L质量+0.025～+0.090pp，但QPS−1.01%～−6.50%。Yandex主BaseGate避免62.90%受损事件，却只保留31.08%有效事件。E25全部20个门控vsA1 Recall差区间跨0，无三轮一致同L双升。两版本质量用同query/A0/A1连接，计时仍各自独立。

## 执行、成本和证据边界

E26 cal为router_train[6144,8192)2048，audit[8192,10000)1808，均不参与E24 fit20K；W先冻结，cal选择后全局冻结，再audit，最后历史validation前2000。cal/audit有历史开发使用，validation已用于E24/E25并启发本追问；held-out未打开。所有三alpha开发点及冻结选择保留。

E26五方法×五L×两数据集50点，各三次计时；110点177760输出独立评分，四条原曲线80000输出与E25逐位回归，115项上游hash与数值/选择/入口/图/线程均通过。E26真实调用897280、修复0、合成2268；8个真实job一次完成。搜索进程总计1000.25s、最高RSS10.038GiB，包含加载/构建/预热/计数/I/O，不能换算QPS。

L128 A1→Shrink路由单测WebVid6.432→6.562μs、Yandex4.410→4.375μs；分项不能相加为QPS。新三alpha及端点产物构建0.0733/0.0263s。原GT/QGT/NSG/E24从零成本未新测。E25真实调用1089152、合成5144、修复0；原结果完整封存。

## 权威交付与接续

- [E26完整报告](entry_method_exploration/20260910_profile_shrinkage_v1/report.md)、[全部原值](entry_method_exploration/20260910_profile_shrinkage_v1/results/tables.md)、[Recall–QPS](entry_method_exploration/20260910_profile_shrinkage_v1/figures/recall_qps.svg)、[损失分解](entry_method_exploration/20260910_profile_shrinkage_v1/figures/gain_loss_decomposition.svg)、[最终验收](entry_method_exploration/20260910_profile_shrinkage_v1/reviews/final_audit.json)、[历史15](experiment_history/15_profile_shrinkage.md)。
- [E25完整报告](entry_method_exploration/20260910_selective_profile_gate_v1/report.md)、[历史14](experiment_history/14_selective_profile_gate.md)；E24局部正信号见[历史13](experiment_history/13_gt_topk_profiles.md)。

用户最新要求接近结束则当晚给短结论、明天继续，见[时间更新](entry_method_exploration/20260910_profile_shrinkage_v1/authorization_update.md)。今晚收口，不继续等待原07:00或扩alpha/模型。明日先判断正负改道是否存在稳定可区分信号，再决定新机制；长期分支保留在s-target，未自动启动。
