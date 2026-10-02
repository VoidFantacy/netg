# E98：WebVid GT10与完整HNSW搜索成本诊断

E98于2026-09-16完成WebVid GT10-soft实现诊断：路由仅0.47% wall；距离及访存等待约77.3% CPU样本。固定输出与逐query NDC后，预取、有效候选池、组合相对匹配基线分别提升7.81%/0.95%/13.15% QPS（候选池单独变化在波动范围内）；组合253.2 QPS，原HNSW参考267.4。550000次search/36轮plain，无训练或新构图；仅K100/L1250的局部优化证据，主源码和默认不变。

## 动机与边界

用户问少算距离为何仍较慢，以及是否有实现未优化。以E97已有WebVid公开10K、完整2.505M/512d raw-IP底库、默认GT10-soft画像和冻结NSG/HNSW诊断；不训练、不改图、不更新默认。该公开测试已曝光，本轮不是新的泛化评估。主源码/库/E97历史结果保护SHA全部不变。

## 实际证据

K100/L1250每query约21.6us用于路由、4565us用于NSG搜索。GT10距离段含访存等待占77.31%采样；候选维护与libc复制合计7.66%，不能用候选队列解释全部差距。两种内积均AVX-512；相同随机地址流直接内积微基准约237.39/233.35ns，未见Faiss算术显著落后。

同加载方式原版223.74 QPS，预取241.22、有效候选池225.87、组合253.16。候选池单项0.95%在波动范围内；组合与预取有局部正值。三个控制完整10K返回ID/距离bits/三入口与逐query route/graph NDC均对齐E97，未减少搜索工作或损失召回。

原双方法进程中的HNSW参考267.38 QPS、Recall@100 90.3718%；GT10原/控制Recall@100均90.6868%。这只是单工作点成本诊断，不是优化后完整前沿，更不能外推跨五集。

## 计量修订、成本与后续

先运行双方法基础L100/400/1250与K1/L1250、分项/采样和三局部控制。发现基础与控制的存活内存不同后，追加同一original二进制的NSG-only匹配基线，并独立补全三个count一致性检查；两项修订记录在原协议，未扩方法/预算网格。共550000次search、36轮plain，另1600万次直接距离调用；主调度25.20分钟，匹配基线3.06分钟，编译/计数另记。进程/库1线程、CPU15串行。

优先优化NSG的邻居数据预取；候选维护属于次要工程项。尚未直接测硬件cache miss、TLB或隔离全部数据布局，剩余差距未完整解释。若正式采用，应先补等距/边界回归，再公平重测NSG/GT10/GATE等共用内核的方法，指标仍只Recall@1/100；本轮没有实施生产替换或重启旧研究分支。

[完整报告](../entry_method_exploration/20260916_search_cost_diagnosis_v1/report.md) · [图](../entry_method_exploration/20260916_search_cost_diagnosis_v1/figures/cost_diagnosis.png) · [协议与修订](../entry_method_exploration/20260916_search_cost_diagnosis_v1/protocol.md) · [CSV](../entry_method_exploration/20260916_search_cost_diagnosis_v1/results/timing_summary.csv) · [一致性验收](../entry_method_exploration/20260916_search_cost_diagnosis_v1/reviews/completion_audit.json)
