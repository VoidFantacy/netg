# E81 query与条件目标的共享分区（前瞻协议）

2026-09-13，第7串行会话。E79/E80两纯目标分组原门失败已封存。E79对compact只保留旧正命中Web340/820、Y248/545，E80亦有旧收益丢失及新损伤；目标几何替代query几何没有稳定改进。新假设：让同一分区同时保留query和目标两个方向，可能减少纯目标分组抹去有用query模式的程度。该解释待证，不把这些关联说成已确定原因。

## 唯一新构造

原A、P、Q、R、GT/base/rawIP/NSG/H固定；条件目标F_qh严格沿E80 ranka→beta→unit加权目标，全部逐hubF digest恢复。没有新的目标rank数、权重、seed、阈值或NSG奖励。原E66每hub完整Q分配bits作为唯一初始化，不从多个初始分区择优；包括active但子不合格的原分配，父支持门保持。

对同一hub的二元分配g，最大化J(g)=sum_m (||sum_{q:g=m} A_qh Q_q|| + ||sum_{q:g=m} A_qh F_qh||)。两view都是单位方向、系数均1，只有这个固定目标，不扫混合权重。每轮分别单位化两组各view加权和，按Q·query_center + F·target_center选组，平分mode0；从原Q分区固定20轮。保存初始与每轮J以及初/终query与target四项；每轮J必须不下降（1e-9数值容差）。任一view零中心/空类或正支持零F曾发生，整hub回P。J是离线聚类目标，不是NSG效用或其上界。

最终仍按最后g聚合原query U_m=unit(rho_m R+sum A Q)，P首槽逐字保持。原父mass8/ESS16和子mass2/ESS8门、raw-prior按子质量分配、同hub字节去重保持；最多3slot、H815/821不变。它不是E77导出画像向P做后处理收缩，也不是E80纯目标目标的seed/参数扫描；改的是分区目标和初始状态。它不保证保留原入口或NSG收益，不宣称新颖性。

唯一方法joint10。原P、compact（query-only）、E80 conditional（target-only）同批对照；两旧目标分组门不回写，控制不晋升。两新画像模型离线冻结后同SHA E73普通builder两图，仍一小HNSW ef10取7slot→距离/slot排序→去重3真实ID→升序入原NSG L128/K10，无新增在线目标特征/加权/MLP。

## 完整门、角色与验收

双集P-fit20K router_train[10000:30000]离线训练，含旧train/monitor。仅历史aux7952 source[2048:10000]及固定两半3976/3976作接受训练反馈；cal/audit历史使用，E34最终及held-out不打开。GT仅在真实返回后评分，不进入在线动作。原rank/A/P/E79总T/E80全部条件F恢复；原Q分区轴和bits完整绑定，逐rank固定32query×12hub参考、独立query聚合和最终J分项复算。保存原始分配bits/质量/ESS/聚合/目标轨迹/F摘要，RAM流式不落N×H×d大文件。

两新图全部W/labels/邻接独立解析；双集各4方法×128预检后4×7952完整plain/count及每方法16原kernel。原三控制全字段回归，各图/slot距离/去重三入口、aligned集合/mask独立验收。主候选对P与compact全量净命中>0、两半非负且zero失败不增，对conditional全量/两半非负且zero失败不增。至少一集通过才另立完整wall阶段；本会话若不足完成整组wall，则交接冻结模型/门给下一串行会话，不能赶半组或拼旧曲线。双集未过即停止这个固定联合目标，不扫权重/初始化/轮数。

报告旧收益保留/丢失、新增收益、修复旧损失/新损伤；GT成员得失另列。失败严格GT10零命中。聚类目标改善、子支持和NDC均不是性能GO。E79/E80及E73/E74局部正负保持。

## 前瞻资源

正常129536 NSG/129280 HNSW/2真实build，2离线分组训练，0梯度/新GT/编译/合成ANN；硬NSG132000，失败完整预留不释放，不自动重试。每dataset离线<=600秒、总<=900秒且16:00硬停，两个模型都完成/验收才构图与查询。CPU15实际进程/数值库1线程，离线RAM<=16GiB。每native<=600秒/RSS32GiB，16:08停止启动、16:14硬停新增query；16:21:50前会话安全交接。

本新阶段<=64MiB，free>=6.8GiB外64MiB晚间+4MiB交接；现场free约6.96GiB，减本阶段64MiB与68MiB预留后仍约6.83GiB，完整预算足够。预算两W/图16MiB、压缩训练/目标轨迹12MiB、raw12MiB、源/快照/表图12MiB、余12MiB。前两阶段消耗已计入当前free，旧预算/seal不改，不复制旧binary/大输入/底图，不清理任何旧文件。20:00停新训练、20:40停新增query、21:00整日交付仍有效。

阶段完成后历史70/索引/summary/s-target及离线契约spec、root_after和campaign状态/交接同步。全部ANN串行，原生工具实际terminal0后才评分/绘图。整日目标未完成。
