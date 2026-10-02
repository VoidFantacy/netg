# E55 最终静态方法与NSG/Fast/FastGT完整比较（选型前锁定）

2026-09-12，按用户最终三指标要求。E54协议已在四格查询前固定全候选池：每集匹配默认P/G0 + E47 RL/ES各双seed4模型 + E52/E53各双seedA/S/T共12模型，合计17。所有训练checkpoint保持旧monitor选择，无本次再训再选；S/T是静态图干预模型，不声称由评分W普通重建会产生同图。

先每集17模型在train64+monitor64执行独立普通二进制完整plain/count与16原kernelparity，逐位恢复已有checkpoint/四格raw；然后既有cal1024全17模型，原U均值最大，平分totalNDC较低再预先固定顺序（默认第一，E47按RL/ES再seed，E52/E53按seed再A/S/T）。分别锁best_all及best_new；最终始终展示cal最佳新候选，若默认胜出明示，不把新候选必称最佳。选型不用最终validation或QPS。

最终历史validation2000沿用E34冻结副本；来源E24validation的原validation前2000。cal/audit来自router_train不同源命名空间，局部row IDs不可直接交叉；核验原来源记录、当前复制SHA、实际向量与train/monitor/cal/audit完全无重复，再冻结。历史validation曾用于旧研究，不称项目新盲测。只读E34/E24已复制2000记录和来源文字，不打开原完整validation/held-out，不生成GT。

WebVid五方法NSG、Fast30K、FastGT10-hard、GT10-soft-t1匹配默认、cal最佳新候选；Yandex四方法NSG、Fast30K、FastGT10-hard（同时默认）、cal最佳新候选。NSG原固定入口；Fast30K原GT1闭式30K/seed100/legacyheap；FastGT=E24GT10-hard/20K/seed20260828/sorted3，不能把全部差异归因GT数量。候选映射和普通NSG保持。

同一原生evaluate二进制（复制E37/E49已验收SHA），CPU15进程/OMP/BLAS/MKL实际1线程，所有job及方法串行；无并行训练/分析/编译。L64/128/256/400/800，五轮纯端到端wall中位QPS，所有轮输出与count/plain逐位一致，固定轮换方法顺序。GT在全部raw搜索之后读取计分；不把I/O/GT/count/组件wall放入QPS。Recall@10=返回与GT10集合交集/10；失败查询=GT10零命中，非程序异常。

全部113点：34fit×(2×128+16)+34cal×(2×1024+16)+45final×(7×2000+16)=710144真实NSG；总预留750000，失败不释放，不自动重试；225wall轮，无额外组件计时。每job≤1200s/RSS32GiB/21:40硬停，新阶段artifact384MiB/free7.5GiB。最终窗口21:15前进入，预计总约15分钟，22:00交付。

独立全部129168行集合评分与hitmask/失败，1808原kernelparity、4352fit恢复、原baselinecal恢复、五L图/入口一致、线程/串行/GT时序/预留与实际计数、源SHA、cal选择重放。逐点Recall/QPS五轮范围/失败率、对默认及NSG/Fast/FastGT的配对命中与失败转换、完整曲线和CSV。前沿采用同机端到端质量-速度曲线判断，小于计时波动不称确定加速；插值只作公共域内描述、不冒充实测同Recall点。最终结果不回流换模型。
