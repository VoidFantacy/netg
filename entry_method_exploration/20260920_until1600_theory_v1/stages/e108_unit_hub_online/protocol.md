# E108：单位hub的真实小图路由与完整wall对照

2026-09-20，16:00活动目标中的独立接续。前置E107已完成：Web单位hub exact3在全部有效预算上显示较强简单对照，原GT10画像与额外入口的独立收益不能预设。本阶段补实际部署形式，不把简单基线称为新论文算法；0梯度训练、0新GT、底层NSG与原H不变。

## 冻结方法和输入

- 两集各4096条E105已曝光开发query/GT100，来源、原始raw-IP底库、NSG、原hub ID保持。复制E107实际单位hub W的字节，不再采用新的单位化公式。
- 三方法：当前原图GT10Default；同原W但新seed小图GT10Rebuilt；单位原hub的UnitHub。后二者同H、M16/efConstruction200/seed20260920、原升序real ID逐条插入，普通HNSW、efSearch10取3，升序real ID进入原NSG。四个新小图在读取本阶段query载荷前构建、验证与冻结。
- 三方法均用原raw query路由，单位化只发生在已经冻结的W上；进入NSG的仍是同一原raw query。GT10Default逐点恢复E105旧返回/距离bits/入口/route及graph NDC。
- 新编译器逐字继承E103 span+batch4及原Router；两集前16行K1/K100/L128的warm/plain/count全部一致，并与链接E99旧内核的ID/距离bits/图NDC核验。未通过不得进入正式矩阵。

## 比较、计时及计数

K1 L64/128/256/400/800，K100 L128/256/400/800。完整54方法点、162轮plain；每点额外一次完整warm和一次count。每轮在同一进程按预算/轮次/数据集轮换方法次序，方法和数据集均串行；CPU15/实际线程1，OMP/BLAS/MKL/NUMEXPR1。

plain wall包括每query的原HNSW路由、ID映射/排序、visited推进、原NSG和输出写入内存；分配、图加载、warm、计数、GT评分和磁盘输出在计时外。不缓存入口到计时路径，不以NDC或job wall计算QPS。保留每轮秒数/QPS、boot ID、线程及实际CPU。

真实NSG总数1,106,688：正式1,105,920，smoke768（含192次链接旧内核复核）。每次真实在线路由另计；smoke旧内核回归复用当前入口，因此路由计数比NSG少192。新图4个，0新底图/GT/训练/K10。预算上限1,120,000 NSG、600MB新文件、40GiB搜索RSS、磁盘余量4GiB。父timebox总4M NSG/2GiB上限同时成立。

每个新进程独立PID/PGID，硬超时1800秒；15:50前剩余时间不足硬超时+5秒不启动。异常保留全部原件，只终止本阶段拥有的进程组，不重跑同一输出目录。

## 预定分析与停止边界

所有query独立重算两K、失败query、实际目标成员增损；与E107 exact输出逐query对齐，分析普通小图的入口集合恢复和真实命中差，区别于新方法收益。三组全部配对均保留：UnitHub−GT10Default、UnitHub−GT10Rebuilt、GT10Rebuilt−GT10Default。

每个K/L保留三轮QPS均值、范围及比值，完整Recall–QPS图；不插值、不挑预算、不由平均正值宣布全面支配。query配对bootstrap固定10000次/seed20260920、95%描述性区间，已曝光数据不包装成盲测。计时轮次不是新的独立query或新构建。

这是补全基线与机制证据，验收门是源/图/输入/输出/资源/计时合同均通过且完整矩阵分析完成；没有本阶段自动更换默认的性能GO。若简单控制在真实wall仍有竞争力，它必须进入后续论文对照；是否替换默认须独立数据与所需召回范围验证。完成本矩阵即停止该基线分支，不增加seed/ef/L/repeats来追逐正值；用户16:00研究目标另按理论证据接续。

[E107报告](../e107_initialization_factorial/report.md) · [配置](config.locked.json) · [时间/资源总合同](../../config.locked.json)。
