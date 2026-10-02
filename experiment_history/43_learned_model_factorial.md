# 43. E54 完整模型画像/邻接四格

2026-09-12，`COMPLETE_WHOLE_LEARNED_MODEL_FACTORIAL`。

完整模型四格把训练收益和跨查询损伤进一步分开。WebVid四个模型的S与T在train/monitor都为正；E52第一seed完整A在monitor净增32 hits，只换画像S或只换图边T各净增19 hits，二者都有贡献，不能统一丢掉一项。第二个RL seed的S比A多2个monitor hits（+0.1758 vs +0.1563pp），只是小局部差异。

Yandex呈现不同趋势：四个模型的T在monitor依次净增5、3、2、6 hits（+0.0488/+0.0293/+0.0195/+0.0586pp），S依次+1、−9、0、−3 hits。E52第二seed完整A净−10 hits，拆开S−9、T+3，再加交互−4，精确守恒；这支持在这些固定学成端点上，画像评分变化及其交互是监控损伤来源，学成邻接仍有局部正信号。E53第二seedA+3=S−3+T6，纯图边比完整模型少受画像损伤。

这些效应稀疏，不能把四个端点与历史monitor说成普遍规律或新盲测；训练集各分量均有收益，也不能保证独立query受益。逐query S/T主效应符号相反的事件本次为0，画像与图边的净方向差异主要发生在不同查询以及联合非线性交互上，而非已证明同一query的两主效应相互抵消。共享修改同时产生gain/loss是真实现象，保留每个模型的完整损伤和失败转换。

因此“只学习图边、保留原画像评分”成为有证据的静态候选，不再只是想法；但没有据此重训或按本次结果筛掉其他候选，所有A/S/T仍按预锁方案进入cal选型。E48单行动作中无统一单因素通过的旧结论保持，两次干预的范围不同。

| 数据集 | 模型 | 干预 | train ΔR pp | monitor ΔR pp | monitor gain/loss hits |
|---|---|---|---:|---:|---:|
| WebVid | E52_seed21 | A | +0.6250 | +0.3125 | 48/16 |
| WebVid | E52_seed21 | S | +0.2856 | +0.1855 | 38/19 |
| WebVid | E52_seed21 | T | +0.2515 | +0.1855 | 26/7 |
| WebVid | E52_seed22 | A | +0.2490 | +0.2051 | 30/9 |
| WebVid | E52_seed22 | S | +0.1221 | +0.0781 | 19/11 |
| WebVid | E52_seed22 | T | +0.0732 | +0.0488 | 11/6 |
| WebVid | E53_seed21 | A | +0.1514 | +0.1270 | 21/8 |
| WebVid | E53_seed21 | S | +0.1001 | +0.0684 | 9/2 |
| WebVid | E53_seed21 | T | +0.0464 | +0.0586 | 13/7 |
| WebVid | E53_seed22 | A | +0.3052 | +0.1562 | 27/11 |
| WebVid | E53_seed22 | S | +0.1733 | +0.1758 | 29/11 |
| WebVid | E53_seed22 | T | +0.1562 | +0.0488 | 9/4 |
| Yandex | E52_seed21 | A | +0.2515 | +0.0586 | 6/0 |
| Yandex | E52_seed21 | S | +0.1587 | +0.0098 | 1/0 |
| Yandex | E52_seed21 | T | +0.0757 | +0.0488 | 5/0 |
| Yandex | E52_seed22 | A | +0.1831 | -0.0977 | 1/11 |
| Yandex | E52_seed22 | S | +0.0781 | -0.0879 | 0/9 |
| Yandex | E52_seed22 | T | +0.0928 | +0.0293 | 5/2 |
| Yandex | E53_seed21 | A | +0.1489 | +0.0195 | 2/0 |
| Yandex | E53_seed21 | S | +0.0708 | +0.0000 | 0/0 |
| Yandex | E53_seed21 | T | +0.0781 | +0.0195 | 2/0 |
| Yandex | E53_seed22 | A | +0.1294 | +0.0293 | 6/3 |
| Yandex | E53_seed22 | S | +0.0391 | -0.0293 | 0/3 |
| Yandex | E53_seed22 | T | +0.0635 | +0.0586 | 6/0 |


C(P,G0)为匹配起点，A(W,G)完整学成模型，S(W,G0)只换评分画像，T(P,G)只换实际邻接。固定E52/E53所有四模型/集，selected点不再变化。所有26物理静态图实际查询，全部向量字节/拓扑身份和64条三路parity通过；S/T不是用其评分W普通构图会得到的图，部署时载入已导出实际图。

实际12424 NSG=7432变化query补测+4992parity，136448 HNSW、18普通构图、16邻接安装，进程累计22.647s。133120独立集合评分、51200 C/A五字段逐位恢复、1664物理parity行，以及全部patch复用/逐query交互身份通过。0训练更新/0cal或最终validation查询/0新GT/0QPS。

监控参与旧checkpoint选择，不能称盲测。本实验固定学成端点的静态因果干预，不推断所有训练步骤机制相同，不撤销E48旧单因子门失败；默认保持WebVid GT10-soft-t1 / Yandex GT10-hard。

E54首次prepare在任何原生调用前检查到E53冻结v1收尾日志失配，改引用稳定v2后完成；原失败日志保留，无查询重试。

下一阶段E55固定17候选/集：匹配默认、E47 RL/ES各双seed，以及本次E52/E53双seed的全部A/S/T共12模型；候选池在四格查询前已经锁定，不按此处结果删选。先独立128条普通二进制恢复，再cal1024原U/低NDC/固定序择优，冻结best_all和best_new。最终WebVid五方法/Yandex四方法与NSG、Fast30K、FastGT10-hard同机单线程五L五轮，历史validation2000，Recall/QPS/零GT10失败率三指标；总710144 NSG/225wall轮。若默认优于新候选，明确说明；最终结果不回流换模型。21:40停止新查询，22:00交付。

[协议](../entry_method_exploration/20260912_learned_model_factorial_v1/protocol.md)、[逐模型/阶段指标](../entry_method_exploration/20260912_learned_model_factorial_v1/results/metrics.csv)、[交互项](../entry_method_exploration/20260912_learned_model_factorial_v1/results/interactions.csv)、[完整结果](../entry_method_exploration/20260912_learned_model_factorial_v1/results/summary.json)、[独立验证](../entry_method_exploration/20260912_learned_model_factorial_v1/reviews/verification.json)、[四格图](../entry_method_exploration/20260912_learned_model_factorial_v1/figures/whole_model_factorial.svg)。
