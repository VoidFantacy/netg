# ACSG 当前实验总结

> 更新至2026-09-11。最近完成E28 GT10共享入口变换研究；状态`SHARED_TRANSFORM_EXPLORATION_COMPLETE_NO_FORMAL_GO`。实现合同见[spec](spec.md)，接续见[s-target](s-target.md)，历史见[s-experiment](s-experiment.md)。

## 当前结论

**本轮没有建立共享线性或小MLP优于原GT10的稳定双数据证据，保留原已冻结GT10路线。** 两数据集、原GT10 hard锚定的共享linear/小MLP/free同目标训练已经完成，并与NSG、原Fast30K、GT1 hard、GT10 hard及原cal冻结GT1/GT10 soft同批比较，完整90点各三次单线程wall。不能从候选教师上界、训练损失下降或同L增量代替完整Recall–QPS判断。

当前匹配比较均以GT10 hard作锚点；历史正式画像仍是WebVid GT10 soft、Yandex GT10 hard。Fast30K保留其30K/seed100/旧入口顺序身份。

## 完整五L新模型变化

同一批次相对GT10 hard；R为Recall@10百分点，QPS为同L三轮中位数之比。全部正负点保留。配对95%区间和原六基线的绝对值见[完整报告](entry_method_exploration/20260911_gt10_shared_transform_v1/report.md)。

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

下表仅对四主方法共同覆盖的原GT10实测Recall点作log-QPS插值，是粗网格描述，不是新增实测等Recall点或新选择规则。

| 数据集 | 模型 | 共同原GT10召回点数 | 插值QPS几何均变 | 同L两指标均升 |
|---|---|---|---|---|
| WebVid | linear | 3 | +0.52% | 1/5 |
| WebVid | mlp | 3 | +0.59% | 1/5 |
| WebVid | free | 3 | -0.29% | 0/5 |
| Yandex-IP | linear | 3 | -1.44% | 0/5 |
| Yandex-IP | mlp | 3 | -1.76% | 0/5 |
| Yandex-IP | free | 3 | -1.96% | 0/5 |

## 机制上新增的认识

fit20k/集的C8教师比原GT10 hard有+4.626/+2.850pp Recall空间，同时平均graph NDC由1642.94/2862.29降至1621.29/2822.89。但教师逐query使用GT从56个完整三元组中选优，不能部署，也不是全H或等工作上界。

固定H的MLP只是在离线生成静态W；上线仍为qᵀW，不能声称具有比自由W更大的query函数族。12次训练都使目标下降，独立NumPy前向/归一化重算通过，但共享linear/MLP的fit精确top3教师入口重合度没有提升。模型MAP等于top3不意味着每次代理损失下降都会改善top3；报告给出可复算反例。

cal两集均选linear λ100、MLP λ10、free λ100，冻结后才执行audit/validation。audit呈数据集/L差异；HNSW与exact诊断单列，不把精确画像排名当作真实有限L入口oracle。教师命中空间与同命中下NDC选优的分组分析见[teacher_diagnostics](entry_method_exploration/20260911_gt10_shared_transform_v1/results/teacher_diagnostics.json)；标签内预测评价是条件子集，不外推到全fit或HNSW性能。

## E24–E27结论保留

E24 GT10的局部正信号不因E25/E26/E28增强未稳定成功而消失。E27原机制链为query相关多目标归属→画像变化→实际三入口变化→少量正负query净收益；两个原正点在exact3下仍保留。其WebVid五L速度+0.34%–1.36%是旧独立批次结论，Yandex原+2.56%未稳定复现；不与E28混拼绝对QPS。详见[历史16](experiment_history/16_gt10_mechanism.md)。

## 执行与证据边界

本轮224万逻辑三元组标签独立GT重评分；新标注1,971,899、标注parity256，268,101次复用兼容缓存。开发/正式评测150点、235,296个query输出独立评分，原六曲线120,000个输出回归E24。实际NSG调用3,377,147，修复0，合成搜索0；训练12次，共462.03s（8线程）。正式查询CPU15/实际线程1/OMP与BLAS1，原kernel、图、base、H和旧标签/画像/结果保持身份。

fit/cal/audit/validation均有历史使用，一个hub/图构建；三次wall不增加Recall样本，bootstrap未做多重校正。held-out未访问/hash。精确GT、QGT、原画像和主图从零成本未新测。当前结果是本地探索，不是新盲测或论文等级结论。

## 交付

- [研究与全部实测报告](entry_method_exploration/20260911_gt10_shared_transform_v1/report.md)、[四主方法图](entry_method_exploration/20260911_gt10_shared_transform_v1/figures/recall_qps_main.svg)、[全部基线图](entry_method_exploration/20260911_gt10_shared_transform_v1/figures/recall_qps_all.svg)、[数据工作簿](entry_method_exploration/20260911_gt10_shared_transform_v1/chart_data.xlsx)。
- [协议](entry_method_exploration/20260911_gt10_shared_transform_v1/protocol.md)、[原始数据](entry_method_exploration/20260911_gt10_shared_transform_v1/results/all_points.csv)、[最终验收](entry_method_exploration/20260911_gt10_shared_transform_v1/reviews/final_audit.json)、[历史17](experiment_history/17_gt10_shared_transform.md)。
- 原E27 summary完整保存在[E28修改前快照](entry_method_exploration/20260911_gt10_shared_transform_v1/source_before/summary.md)；旧实验各自原产物继续保留。
