# E69 完整画像前三入口的真实 NSG 效用（前瞻协议）

2026-09-13，第4串行会话。新查询前冻结；前件已保存。E66–E68均完成，不重跑旧阶段。固定原base/raw-IP/NSG/kernel、H815/821、GT10、L128/K10，唯一实验执行者CPU15/threads1，OMP/OpenBLAS/MKL/NUMEXPR/BLIS1，无并行训练或评测。

研究问题：E68完整P/mode评分前三是否实际有更好的NSG命中与失败表现。使用E68既存float64评分前三，升序三真实hub注入原NSG。精确分数不是NSG效用上界，也不是新可部署路由。保留E66 approx P、duplicate、mode结果；不训练、不构图、不调用HNSW、不产生QPS。不能用离线查表/注入wall估计线上完整扫描成本。

数据仅原router_train[2048:10000]7952/集，固定前后3976；全部历史辅助/选择训练反馈。P-fit20K含旧train/monitor；cal/audit已有使用。E34最终validation与held-out不进入本阶段。冻结query/GT/row namespace及SHA、W与E68排序、E66三方法完整返回。base/NSG按已完整验收SHA继承并验证size/mtime；源码及实际静态链接依赖重新SHA。

只在同dataset namespace/source row/query bytes、canonical真实三入口、base/NSG/kernel/rawIP/L128/K10/GT身份相同时复用IDs/距离bits/graph NDC，route NDC不复用。准备阶段独立复核全部碰撞；31808逻辑精确输出预计28102可从E66复用、3706逻辑缺口中171条互相alias，仅3535唯一缺口（Web2308/Y1227）。不以GT筛缺口，不填未知结果。若覆盖不符，查询前停止重新核对，不隐式扩大预算。

注入接口独立包含E46/E37已验源码，count调用原e46_search；新增plain/reference只接受同样已整批验证的row/三入口。每集先回放完整7952 approx P，plain/count逐位恢复E66 ID/距离/graph NDC；首128为预检，属于整批，不额外收费。然后缺口plain/count，baseline与缺口各固定前16条使用Work原wrapper对照。空输入和非法row/entry/重复/非升序整批拒绝须为0调用。正常总NSG=2*(2*7952+3535)+2*2*16=38942；Web20552/Y18390，各完整预留，失败不释放。硬限40000，技术修复不自动重试；无额外预热或隐藏parity，0HNSW/0build/0新GT/0optimizer。

每集保存baseline回放、缺口raw、完整exact-P/mode aligned输出与来源method/row/alias，GT在两个native进程实际退出后独立集合评分。报告全7952及固定两半：精确mode−精确P、精确mode−原approx mode、精确mode−匹配approx P，另精确P−approx P；完整GT成员增损、逐query净命中增损、strict zero失败救回/新增、graph NDC，失败案例保留namespace/入口/返回。原E66门不改。

接续信号预锁：精确mode相对精确P及approx P的全量净命中均>0、两半各>=0、失败不增，graphNDC<=各参照1.01；相对approx mode全量净命中>=0。按dataset分别报告。至少一集过上述有限质量门才开展一项新的可部署近似修正；另一集仍保留迁移反证，不要求两集同时阳性。若无一集通过，停止只修近似这一解释，不扫ef找阳性。门通过仍不是正式性能GO。

阶段新输出<=32MiB，free>=7GiB，RSS<=32GiB，单job<=600s，12:40后不启动本阶段查询、12:50硬停；本会话最迟13:20:37安全退出。query/大图按冻结路径引用不复制；每阶段保留全部旧字节。编译与数值分析仅在native全部退出时进行。完整成本含编译/load/操作/回放/补测/复用/alias分别记录。结束验收、图、报告、历史58、四主文档及handoff，整日21:00目标保持未完成。
