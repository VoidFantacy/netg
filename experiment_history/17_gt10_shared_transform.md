# 17 GT10共享入口变换（E28）

状态`SHARED_TRANSFORM_EXPLORATION_COMPLETE_NO_FORMAL_GO`，2026-09-11收口。本轮没有建立共享线性或小MLP优于原GT10的稳定双数据证据，保留原已冻结GT10路线。 原始目录[entry_method_exploration/20260911_gt10_shared_transform_v1](../entry_method_exploration/20260911_gt10_shared_transform_v1/report.md)。

## 动机与实现

延续E27对GT10机制的分析，检验离线共享变换能否让一次microHNSW直接找出更好的三入口。W=normalize(P_GT10+f(P_GT10))，linear无偏置d×d，MLP为d→64→d/ReLU，另有free H×d残差容量参考。在线raw query→HNSW3→真实ID→原NSG，不增加query塔或组合重排，不修改主图、H、metric或base。

fit20k/集，C8由GT1/GT10 hard实际HNSW3并集补齐，枚举56个完整三元组L128真实标签。教师max hits/min graphNDC/anchor score/realID；目标为全H三元素集合似然+画像锚定正则。它的MAP为top3，但不是任意互补性的模型；其normalizer属于diagonal k-DPP已知形式，不宣称新概率理论。

## 实验与冻结

两数据集各3族×λ10/100，固定80epoch、Adam.003、batch1024全fit梯度累积、seed20260911。cal1024 L64/128每族选λ；两集都选linear100/MLP10/free100。audit1024含exact诊断，fitprobe256仅诊断；原使用validation2000×9方法×5L共90正式点，每点三次单线程完整warm/plain。选择前后身份见[freeze](../entry_method_exploration/20260911_gt10_shared_transform_v1/models/frozen_before_validation.json)。

## 完整结果

| 数据集 | L | linear ΔRpp / ΔQPS | MLP ΔRpp / ΔQPS | free ΔRpp / ΔQPS |
|---|---|---|---|---|
| WebVid | 64 | +0.080 / -0.28% | -0.270 / -1.21% | -0.385 / -1.07% |
| WebVid | 128 | +0.070 / -0.26% | +0.030 / -1.18% | -0.075 / -0.64% |
| WebVid | 256 | +0.090 / -0.41% | +0.160 / -1.21% | +0.030 / -0.54% |
| WebVid | 400 | +0.045 / +0.46% | +0.240 / +0.02% | +0.095 / -0.36% |
| WebVid | 800 | -0.040 / -0.24% | +0.120 / -0.39% | +0.000 / -0.29% |
| Yandex-IP | 64 | -0.025 / +0.34% | +0.005 / -0.03% | -0.050 / +0.29% |
| Yandex-IP | 128 | -0.110 / -0.13% | -0.075 / -0.19% | -0.140 / +0.01% |
| Yandex-IP | 256 | -0.070 / -0.01% | -0.090 / -0.19% | -0.100 / -0.10% |
| Yandex-IP | 400 | -0.035 / -0.06% | -0.060 / -0.15% | -0.055 / -0.00% |
| Yandex-IP | 800 | -0.035 / -0.07% | +0.005 / -0.12% | -0.035 / +0.03% |

以上同L对GT10 hard差值；不能解释成等Recall加速。共同原GT10召回点的log-QPS插值描述如下，不外推、不当作新增测试点：

| 数据集 | 模型 | 共同原GT10召回点数 | 插值QPS几何均变 | 同L两指标均升 |
|---|---|---|---|---|
| WebVid | linear | 3 | +0.52% | 1/5 |
| WebVid | mlp | 3 | +0.59% | 1/5 |
| WebVid | free | 3 | -0.29% | 0/5 |
| Yandex-IP | linear | 3 | -1.44% | 0/5 |
| Yandex-IP | mlp | 3 | -1.76% | 0/5 |
| Yandex-IP | free | 3 | -1.96% | 0/5 |

教师候选空间为+4.626/+2.850pp，不能部署。共享模型目标下降而fit精确教师入口重合度未提高；audit与validation的完整正负和exact差异见[报告](../entry_method_exploration/20260911_gt10_shared_transform_v1/report.md)。模型损失/MAP/真实搜索三个层次分别判断。旧E24GT10正信号保留，本版不能否定所有共享表示学习，也不能用MLP组件本身宣称论文创新。

## 成本与核验

224万逻辑标签，新增1971899实际标签调用+256parity，268101缓存复用；全部标签独立GT评分。开发/正式150点235296输出独立评分，原六曲线120000输出回归E24。总NSG调用3,377,147，修复0，合成0，预算收口。训练12次462.03s，CPU8；标注CPU16仅离线，不用其吞吐充查询QPS。正式CPU15/线程1/OMP-BLAS1，GT/计数/I/O在timer外，模型与图加载构建费用另列。

所有fit/cal/audit/validation有历史使用，一个既有hub/图，held-out未访问/hash。先验构建/精确GT从零成本未新测。旧源/图/画像/标签/结果保留，根文档修改前快照在[source_before](../entry_method_exploration/20260911_gt10_shared_transform_v1/source_before/summary.md)。

## 证据入口

- [协议](../entry_method_exploration/20260911_gt10_shared_transform_v1/protocol.md)、[文献与推导](../entry_method_exploration/20260911_gt10_shared_transform_v1/research.md)、[源清单](../entry_method_exploration/20260911_gt10_shared_transform_v1/sources/inventory.json)。
- [所有点](../entry_method_exploration/20260911_gt10_shared_transform_v1/results/all_points.csv)、[图表数据](../entry_method_exploration/20260911_gt10_shared_transform_v1/chart_data.xlsx)、[主图](../entry_method_exploration/20260911_gt10_shared_transform_v1/figures/recall_qps_main.svg)。
- [教师分析](../entry_method_exploration/20260911_gt10_shared_transform_v1/results/teacher_diagnostics.json)、[调用账](../entry_method_exploration/20260911_gt10_shared_transform_v1/logs/evaluation_jobs.json)、[最终验收](../entry_method_exploration/20260911_gt10_shared_transform_v1/reviews/final_audit.json)。

接续只按当前[s-target](../s-target.md)和新明确授权进行；本卡的原命令不自动重启训练或查询。
