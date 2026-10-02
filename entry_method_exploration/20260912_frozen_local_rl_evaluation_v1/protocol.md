# E49：冻结局部RL画像的开发与完整Recall–QPS验证

2026-09-12。用户要求大胆假设、小心证明并持续至22:00。E47统一训练门因WebVid ES两seed monitor无正增量而停止预算扩展，但RL在两集有选中正候选。新假设是这些已经冻结的RL候选能否保住隔离query收益；它不是重启训练、修改旧门或部署替换。E48四格结果已完成，不能用固定评分或固定邻接统一消除两集冲突。

## 模型、数据与顺序预锁

两个原数据集，当前GT10基线及E47两arm×两seed的全部selected模型共十个。全部W/普通HNSW/selected step/源checkpoint身份在cal前冻结，不能依新GT再调参数或换checkpoint。baseline来自E37原P和图；线上raw query→一次普通HNSW top3→排序三个真实ID→原NSG，静态部署无在线策略网络。原IP/base/NSG/H/层级/ef/K保持，L128质量对照；完全相同普通静态评测二进制来自E37。

先10个fit parity点，各128query=原train0:64与monitor4096:4160，返回ID/距离/入口/route和graph NDC逐位恢复E47当前选中checkpoint。E47 checkpoint原始行布局是train4096+monitor1024，必须使用4096起点，不沿用旧E37 train512 checkpoint偏移。

然后全部十模型在已有隔离cal1024评测。每dataset/arm以cal平均原U最大选择seed，平分按较低total NDC、较小seed。选择及全部模型SHA冻结后才准备audit。再测全部十模型audit1024质量，保留未选seed结果。cal/audit直接使用E37已隔离历史文件，source row IDs不交于原train/monitor5120且两开发池互不交；它们在历史方法探索中已曝光，不是全项目盲测。不得打开或hash原validation/held-out query/GT；原Fast30K已冻结静态图路径含历史validation目录名不等于读取该目录query/GT。

最后两dataset固定五方法：NSG、原Fast30K、当前GT10、cal选择RL、cal选择ES。使用原L64/128/256/400/800，每点五次独立plain端到端wall。方法顺序按原评测器dataset/repeat/L轮转，逐方法串行，线程/OMP/BLAS/MKL实际1、CPU15，无并发训练/重分析。计时raw query→路由→映射/排序→原NSG→预分配输出；build/load/GT/count/I/O在计时外，L128单独测组件时间，不把其和当端到端wall。所有轮输出与count/前16query原kernel逐位核验，audit128与frontier128一致，各L入口/静态图一致。

## 成本与判断预锁

fit10×(2×128+16)=2720；cal/audit各10×(2×1024+16)=20640；frontier50×(7×1024+16)+10×2048=379680；共423680新增NSG，硬限500000。每个job全矩阵预留且失败不释放，不自动重试。原训练/构建费用单列，0新训练/GT/validation/held-out；模型已经存在，不重复build模型。资源新阶段独立锁：artifact≤256MiB，free≥8.5GiB，进程RSS<32GiB、每job600s；21:30后不启动job、21:40停止查询、22:00前收口。原E48的20:00协议作为历史冻结记录保留，本阶段按用户延长后的截止时间执行。

完整报告gain/loss/net、新增零命中/救回、原U、route/graph/total NDC，以及5000次query配对bootstrap95%区间（seed20260912）。预锁开发门沿用可比E37标准：选中RL每dataset cal≥+0.1pp、audit>0，且两split total NDC≤+1%；两个数据集都满足才标开发门通过。该门不自动等于正式独立GO。五L全部真实点及五轮范围保留；共同非劣域内log-QPS插值仅作描述，不能以same-L Recall、单点QPS或cost替代Recall–QPS结论。对RL/ES和全部seed的负结果同样报告，不按audit换seed。

若信号不保留，继续定位从已见局部候选到静态确定更新的转化障碍，而非扩展旧训练轮数；后继另立协议，不用本轮audit作训练反馈。交付80质量/性能点、250wall、逐query配对、完整审计/图/报告、历史38及四主文档。
