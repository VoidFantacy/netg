# E96：GATE三数据集完整比较

2026-09-14启动，09-15完成。用户授权GATE、当前GT10、NSG、全量HNSW在WebVid/Yandex/LAION比较，16个预算至1500，每点三次单线程平均，交付Recall–QPS与失败率；不以方法质量删点，不追加第四集。它是独立对照实验，不是重启E95固定H增强分支。

实物位于[独立E96目录](../entry_method_exploration/20260914_gate_new_ood_v1/report.md)。输入为三集完整base及公开10K，Y取public100K前10K；原NSG/GT身份冻结。Web/LAION测试query同源，public资产已有项目曝光；最终query未用于本轮模型选择。

GT10沿真实QGT hub→GT10 query画像→Micro-HNSW top3→原NSG。Web/Y沿冻结soft-t1/hard；LAION只按cal1024、L128选soft-t1。GATE用两层32×16 HBKM、512真实hub、release10的5近5远子图、Graph2Vec、GT1首次发现hop监督、cosine triplet tower及静态W导出；线上小HNSW3入口到原NSG。训练10K、monitor1024，与GT10 fit20K不同。全量HNSW在每集完整base构建M32/efC200，保存无损有序拓扑并逐节点/128query核验。详细适配差异和配置见原报告及协议，不能称作者程序逐位复现。

结果：192点、576次plain wall及独立count完成，实际CPU15/线程1/单boot/串行；逐query共192万组输出，两种集合评分及最终配对、均值、身份审计通过。Web和Y的GATE全部16个点均被同预算GT10的Recall/平均QPS直接支配；LAION高预算有较高Recall与较低速度的取舍，L1500 GATE96.287%/145.86QPS/3失败，GT10 96.154%/148.94QPS/6失败。全量HNSW与GT10前沿交叉，不能称GT10处处最快。默认未替换。

最大预算零命中数（NSG/GT10/GATE/HNSW）：Web13/4/6/11，Y18/13/16/29，LAION7/6/3/48，分母各10000；主失败为Recall@10=0，GT1漏失另报。三次计时范围和query描述区间不构成普遍显著性保证。

正式阶段4.758小时，原估计6.22小时；从09-14 21:16:46到09-15 02:02:15。最终GATE tower训练639.97/751.71/1331.11秒；标签151.23/200.82/230.21秒。LAION特征945.11秒已含HBKM922.57秒，成本不得相加。原GT/NSG/继承画像成本未知；被替代训练和在途丢失成本单列。

关键修正保留历史：原HBKM层级误读8×8×8在新hub构建前改32×16；旧动态子图采样[-0:]错误在public测试前修正为固定release10，并重训Web/Y，旧产物不进入正式结果。环境重启增加训练/HBKM/HNSW/按完整L块评测恢复。LAION全节点构建后最终保存触发磁盘下限，检查点转存系统盘续存，全节点未重建；所有正式点一次完成。用户后来授权删除原归档，测试后删除netg.tar.gz并逐文件校验将LAION索引恢复项目目录，旧数据/图/模型/失败产物保留。

主要证据：[报告与图](../entry_method_exploration/20260914_gate_new_ood_v1/report.md)、[锁定协议](../entry_method_exploration/20260914_gate_new_ood_v1/protocol.md)、[采样修正](../entry_method_exploration/20260914_gate_new_ood_v1/sampling_amendment.md)、[完整指标](../entry_method_exploration/20260914_gate_new_ood_v1/results/metrics.csv)、[数值审计](../entry_method_exploration/20260914_gate_new_ood_v1/reviews/final_numeric_audit.json)、[成本](../entry_method_exploration/20260914_gate_new_ood_v1/results/offline_costs.json)、[完成封存](../entry_method_exploration/20260914_gate_new_ood_v1/complete.json)。下一步以新的用户任务为准；本轮没有新增调参或默认部署。
