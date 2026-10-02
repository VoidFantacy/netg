# E70 单个搜索宽度干预（前瞻协议）

2026-09-13，会话4。E69在Yandex通过有限效用接续门，WebVid未胜精确单画像；原E66门不改。固定P、duplicate3P、mode3P的E66物理图/W/真实H，每项只对照ef10与ef30，不训练/构图，不扫其它ef/seed/模式数。WebVid完整同矩阵作为迁移反证，不按其结果另选参数。已有hnswlib按physical node计搜索宽度，ef30不是等工作量或固定10个不同hub。

E66源码setEf(10)硬编码，旧设计称配置可直接改变的说法有误。独立E70 Policy增加显式ef_search，只允许10/30；reference_graph=true时plain/count直接加载同一已冻结graph_file并逐行验向量/label，不写重复图。其余7slot/距离和slot排序/三hub去重/canonical真实ID及原kernel保持。编译前后源diff保留，不改原hnswlib/ACSG/build。

仅历史aux7952=router_train[2048:10000]，固定3976两半；预检前128原样前缀，然后完整7952六policy。此128为另一次明确收费的预检。两个dataset串行，CPU15/threads1和所有数值库1线程；每个native一次仅测一个policy，无并发训练/分析。新query前冻结全部输入/配置/源/binary/图身份；base/NSG继承已核验SHA并检查stat。GT在原生全部raw后评分，E34最终与held-out不进入。aux所有选型反馈计训练，P-fit/旧cal/audit历史暴露保留。

正常NSG=2*(128+7952)*6*2+4*6*16=194304，HNSW193920，0build；每集预检1632、主批95520。全硬限200000，失败完整预留，不自动重试。每job<=600s、12:45后不启动本阶段查询、12:55硬停；本会话13:20:37前交接。RSS<=32GiB，输出<=48MiB、free>=7GiB，给晚间曲线保留累计空间。大输入和小图引用原路径不复制，不清理旧产物。

验收：原ef10三policy在预检/完整aux全部IDs/距离bits/入口/route与graph NDC/hits/mask/7slot恢复E66；六policy全plain/count+16原kernel；GT10集合独立评分；新slot距离/去重重算；图源前后SHA、进程实际线程与CPU记录。新ef30全部aligned保存，报告完整与两半Recall、strict zero失败救回/新增、GT成员和query净损益、routing/graph/total NDC，以及相对E68完整排名的一致率；排名变准不是NSG更好或加速。

后继完整wall门仅作历史开发选择：mode30相对P10和P30均全量净命中>0、两半各>=0、零命中失败不增，另相对mode10净命中>=0；费用用实际route/graph/totalNDC呈现，不能凭NDC称等成本。按dataset分开；至少一集过门才继续一份双集同条件完整wall（NSG/Fast30K/GT10-hard/Web匹配soft/P30/mode30），未过的另一集保留反证。全部失败则停止此width干预，不接着加ef。该门不替换E66门或默认，也不是最终性能GO。

如继续wall，另建E71锁定所有五L/五轮配置和完整在线计时，不拼E67/E65旧方法曲线；E34最终仍留晚间。完成E70报告/图/历史59及四主文档/状态交接后再进入下一阶段。
