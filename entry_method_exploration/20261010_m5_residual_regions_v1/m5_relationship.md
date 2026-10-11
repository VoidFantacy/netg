# E174 与原 M5 的关系

本文只依据冻结协议、原方法源码和分析schema说明关系，未读取或解码本轮GT、返回结果、质量或QPS，不包含实测结论。

## 保留原 M5，扩展其候选范围

原GT10画像路由、原NSG主搜索、原query和rawIP评分保持。原M5冻结posting仍是每行最多8个目标、三路由行并集最多24个C；继续在原GT返回R上排除重复，fresh scalar重评分原R及**全部C**，按原arrival/tie优先级严格TopK合并。Direct M5继续调用原`Posting.apply`，没有用少数seed替换原C。

新增阶段在完整M5阶段成功后，从同一份已评分C中每行选query-best seed，最多3个，去重不补位。沿原NSG物理邻接槽一跳轮转，过滤主搜索已见、C及本次X重复；新X用同一rawIP评分，追加24或96次评分预算，优先级晚于R/C。X非有限时保留完整原M5返回与已付费用。这是一跳候选生成，不是重开入口、恢复主搜索或重新构图。完整C支持保留不保证最终K个ID是原M5返回的超集，须看实际救回/损伤。

源码：[原plan/apply](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_regions_v1/src/runtime.hpp:28)、[完整R/C阶段](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_regions_v1/src/region.hpp:80)、[seed与一跳X](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_regions_v1/src/region.hpp:165)。合同：[protocol.md](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_regions_v1/protocol.md:5)。

## 跨模态性质的实际来源

M5的任务信息来自**原discovery/FIT0 20K跨模态训练query**：使用其真实GT1/GT100，减去原GT10路由、旧`Lminus`主搜索的实际返回，形成训练漏召回目标。漏GT1权重100，漏GT100成员额外权重1，同目标可叠加；整数联合覆盖greedy据此编译冻结`residual_joint.bin`，K1/K100共用一张表。它学习的是这些原训练query下的漏召回覆盖，并非本轮a/b监督，也不是原M5输出上的新漏召回拟合；旧训练预算与当前查询预算的适配仍需实测。

源码：[漏召回及权重](/root/acsg-e172-storage-v2/campaign/m5/compile_postings.py:11)、[联合覆盖greedy](/root/acsg-e172-storage-v2/campaign/m5/compile_postings.py:26)、[原GT/routes/low-L返回及冻结编译](/root/acsg-e172-storage-v2/campaign/m5/compile_postings.py:66)。

每行query-best选择、原图一跳、visited过滤、去重和严格TopK合并都是通用图检索操作，没有显式模态差、均值平移、低秩认证或语义桥模型。MF来自**同一漏召回监督**的逐行频率选择，检验联合覆盖选择的价值，不是去掉监督；GEO使用原冻结full-base geometry，但仍继承共同的已学习GT10画像路由，不能称全流程无监督。三个路由行也不证明三个不同basin。

源码：[MF选择及同监督输入](/root/acsg-e172-storage-v2/campaign/m5/compile_postings.py:40)、[MF导出](/root/acsg-e172-storage-v2/campaign/m5/compile_postings.py:81)；冻结控制身份见[protocol.md](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_regions_v1/protocol.md:15)。

## 分开回答的命题与对照

| 对照 | 能检验的命题 | 解释限界 |
| --- | --- | --- |
| REG96 / 原M5，同L | 区域阶段是否带来真实增量救回、损伤及完整费用变化。 | Recall升/QPS降记取舍；新ID数量不能替代结果。 |
| REG96 / GT10，同L | 完整增强方案相对当前默认的实际价值。 | 不能把原M5贡献全部归给新区域阶段。 |
| 小L REG96 / 大L GT10，同时列小L原M5 | 特定离散跨预算比较是否双升，区域是否跨过原M5仍有的质量缺口。 | 若原小L M5已覆盖质量差额或已有双升，不能把全部速度优势归因于扩展。 |
| MFREG / MFDIRECT、GEOREG / GEODIRECT；REG96 / MFREG、GEOREG | 通用扩展器在不同冻结种子源上的收益，以及M5联合覆盖源的局部差异。 | C/X数量与实际费用可能不同；即使M5更强，也不自动证明跨模态独有机制。 |
| REG96 / FIRST96、REG96 / REG24 | 同份C上的query-best选择和额外预算差异。 | 这两项专门控制只在pilot，不能称confirm重复验证。 |

全部方法的真实质量差异以`comparisons.recall_delta_pp/rescue_members/damage_members`为准；速度使用完整`points.wall_seconds/qps_rounds`，不是256计数替代。参见[analysis_schema.md](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_regions_v1/analysis_schema.md:19)。

## 正负结果如何解释

- 表外X只说明候选源越过冻结表支持；表外**实际救回**进一步说明在这些query上找回了该支持集合未包含的真目标。`X_outside_original_M5_U`与`X_outside_original_TRAIN_GT100_U`不同，均为每query incidence之和，不是全局distinct ID，也不是跨模态泛化证明。
- 正结果须先扣除实际损伤，并支付R/C重评分、seed、邻接、X评分及合并的完整wall。只有两角色的具体比较通过确认门，才支持相应dataset/K/L上的局部复现；MF/GEO若同样有效，应将解释收缩为通用区域扩展。本轮默认保持GT10。
- 负结果或费用取舍限定本冻结一跳/seed/预算版本；停止该版本不等于丢弃M5，也不等于证伪原漏召回监督的全部价值。保留原M5、全部C及历史产物，不从本轮反馈扩展新实验。

机制字段：`new_rescues_vs_M5`及两种U外新增救回只对M5REG24/96/FIRST96计算；MFREG/GEOREG同名字段的初始化0表示未计算。控制实际救回/损伤取`comparisons`或辅助独审明细；U外损伤未单列不能补0。全4096 trace、固定256 NDC、完整wall各自回答不同问题，详见[机制schema](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_regions_v1/analysis_schema.md:32)。
