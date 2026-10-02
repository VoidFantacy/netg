# 103｜E108 单位hub真实小图与在线wall

2026-09-20，用户16:00活动目标内进行。E107发现原H单位hub的精确路由已是强简单对照，故先补实际Micro-HNSW形式与完整wall，不直接训练新网络。此为必要基线和机制证据，不声称新算法贡献。

当前原GT10图、同seed重建GT10图、同seed单位hub图三方法；M16/efConstruction200/seed20260920/ef10、同原H升序real ID，取3后原raw query进相同NSG。两集共4个普通小图已构建，标签/向量bits/邻接合法性核验；此前模型和大图保持。两集前16行K1/K100/L128的warm/plain/count及链接E99原内核一致，默认E105旧输出/NDC恢复通过。

当前正式阶段运行中：每集4096条E105已曝光query，K1五L64/128/256/400/800，K100四L128/256/400/800；完整54点、162轮plain，计时含实际每query路由和NSG，0缓存入口。预计1,106,688次NSG，CPU15/实际线程1/方法及数据集串行，旧默认不替换，0新GT/底图/梯度训练/K10。源码、四图和协议在阶段query读取前冻结。

比较UnitHub−原GT10、UnitHub−重建GT10、重建GT10−原GT10全矩阵，并按E107 exact检查近似路由影响。保留每轮wall、失败query和实际GT成员增损；不由NDC/单点/均值推全面性能GO。阶段执行与结果见[协议](../entry_method_exploration/20260920_until1600_theory_v1/stages/e108_unit_hub_online/protocol.md) · [状态](../entry_method_exploration/20260920_until1600_theory_v1/stages/e108_unit_hub_online/state.json)。
