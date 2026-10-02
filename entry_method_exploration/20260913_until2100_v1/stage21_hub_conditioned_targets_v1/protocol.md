# E80 同hub条件GT10目标分组（前瞻协议）

2026-09-13，第7串行会话。E79原门失败并封存，不能重开全局GT均值分组或扫参数。本版本依据源码可确认的一个信息错位：原A按每个GT目标分别分配hub，但E79给同query的所有hub同一个GT10总均值。Yandex hard归属下，多数(query,hub)只有部分GT属于该hub，其余目标仍进入E79特征；Websoft也没有保留目标与该hub的条件权重。这尚未证明是损伤原因，以下单次受控新方法用于证伪。

E79目标相对置换有正值但相对P/Web−11、Y0，相对compact/Web+48、Y−120；保留正负，不以置换差值称性能改善。新版本固定原A/P、所有实际GT10目标和原NSG/rawIP/H。区别仅在分组特征由同query总均值变为对应hub条件目标均值，最终仍聚合原query画像，在线无新计算。

## 条件特征与固定画像

恢复原E66 rank分配a_qrh（Web原soft-t1、Y hard），A_qh=sum_r a_qrh/10须SHA逐字恢复，P=unit(R+A^TQ)字节恢复。仅使用原P-fit20K=router_train[10000:30000]。T_qr=unit(raw GT target)沿原float32。对A_qh>0：beta_qrh=a_qrh/sum_r a_qrh，F_qh=unit(sum_r beta_qrh*T_qr)。先条件归一化beta避免极小soft质量被1e-12截断改变方向；A=0的query/该hub记F=0，权重为0，不能当0目标监督。存在正支持但条件均值零范数<=1e-12，整个hub标记退化并回P，记录原因。

每hub独立F空间父方向=unit(sum A*F)，seed0=argmax A*(1+F·parent)，seed1=argmax A*(1−F·F_seed0)，平分按原source row。20轮、tie归0，父mass8/ESS16、子mass2/ESS8、曾空/零组整hub回P；全部沿E79既定规则，不扫阈值。最终用第20轮分配聚合原Q：unit(rho R+sum assigned A Q)。P首槽bit保持，同hub精确字节首出现去重，最多3槽，原H815/821不变。

唯一新方法conditional10。对照为原P baseline10、E73 query分组compact10、E79整体GT均值target10（本版本改显示global10）；三对照原物理图引用并全量回归。不会把E79permuted改成主方法；本轮不需要新随机种子，比较条件化与整体目标定义的完整后果（包含支持、容量、画像和图变化），不声称单一纯因果中介或文献新颖性。

## 先0ANN支持/构造，再真实比较

离线阶段rank权重和目标只在RAM，<=16GiB；不写N×H×d特征。按hub流式形成F。核验全部a/A/P和E79总目标特征digest；32固定query×固定12hub的beta/条件均值逐rank独立参考。记录A加权cos(F,T_global)、条件有效目标数、与E79分区消除二元标签后的加权分歧、原子支持/质量/全部分配bits及每hubF digest。它们只检验信息改变，不算NSG效用。

没有支持变化时明确alias/停止，若任何数值/身份或时间/磁盘不通过，在完整离线安全边界停止；不能开展半个双集查询。两个模型全部有限/单位、父P/质量/先验守恒并独立复核后冻结prebuild，复用E73同SHA builder构建两图；prequery后双集4方法各128预检→7952完整辅助查询。旧三对照全字段回归、plain/count及每方法16原kernel、7slot距离/label/去重3真实入口、序列化全W/label/邻接和aligned集合/mask独立评分。原evaluator/NSG/hnswlib不改，ef10/7slot/三真实ID升序/L128/K10。

主方法同时对P与compact全量净命中>0、固定两半3976/3976非负、零GT10失败不增；对global全量与两半非负且失败不增。至少一集全门通过才另立双集同批五L五轮完整wall，另一集原样迁移，不改变已锁模型。双集未过则停止本条件均值版本，不扫参数、目标rank数或改选旧控制。NDC/同LRecall/训练目标不是性能GO；旧门不回写。

辅助source[2048:10000]及两半全部历史暴露，反馈算训练；P-fit含旧train/monitor，cal/audit已观察。E34历史validation留晚间冻结后最终对照，held-out不打开。报告旧收益保留/丢失、避免旧损伤/新损伤、GT成员集合及zero救回/新增；不得只显示被修好的query。

## 预算和截止

正常129536 NSG/129280 HNSW，两真实新build，0optimizer/新GT/编译/合成ANN。4job各完整预留不因失败释放，硬限132000，无自动重试。CPU15、实际进程及所有数值库1线程；方法/数据集串行，查询工具terminal0后评分。每dataset离线<=900s；每native<=600s/RSS32GiB，16:02停止启动本阶段query、16:12硬停；会话16:21:50前交接。若未来完整wall预算无法在该界前完成则安全留冻结结果给下一串行会话，不赶半组曲线。

现场free约7.00GiB；本新版本64MiB上限、下限6.8GiB外另留64MiB晚间和4MiB交接。此分配在新阶段前锁定，不修改E79或旧7GiB预算。估算两W/图<=16MiB，压缩分组/support<=12MiB，4方法全raw<=12MiB，source/root/manifest/表图<=12MiB，另12MiB余量。模型/binary/大输入皆引用旧字节，仅新图/W等落/data；不清理任何历史产物。把此前阶段实际消耗计入现场free，再核对本阶段完整剩余量。20:00/20:40/21:00整日门保持。

完成后详细历史69/索引/summary/s-target，离线数据合同同步spec；source_before/root_after和原协议/源/结果保存，campaign handoff/state列实际成本/进程/下一命令/角色。E79完整seal不改。
