# 103｜E108 单位hub真实小图与在线wall

2026-09-20完成，状态COMPLETE_UNIT_HUB_ONLINE_NO_DEFAULT_CHANGE，用户16:00活动目标继续。E107发现原H单位hub精确路由是强简单对照，E108补实际Micro-HNSW及完整wall。单位hub在Web有小幅质量信号，Yandex K100损伤，没有跨集稳定替换；不是新算法创新或默认GO。

当前原GT10图、同seed重建GT10图、同seed单位hub图三方法；新图M16/efConstruction200/seed20260920/ef10、同原H升序real ID，取3后原raw query进相同NSG。4个普通小图标签/向量bits/邻接合法性核验；两集前16行K1/K100/L128的warm/plain/count及链接E99一致，原GT10全部点恢复E105旧输出/入口/距离bits/两类NDC。

每集4096已曝光query，K1五L64/128/256/400/800，K100四L128/256/400/800，54点/162轮plain完成；计时含实际每query路由及NSG，无缓存入口。单位hub对原GT10的L128 R1/R100变化为Web+0.1221/+0.2654pp、QPS+0.23%/+0.32%；Y+0.1953/−0.1692pp、QPS−1.45%/−2.04%。失败数分别1011→1006、5→6、384→376、24→34。Web所有9点召回均值正，但速度范围均重叠；Yandex K100四点均值负，四个K/L的UnitHub速度整段范围更慢。

画像还改变小图可检索性：原GT10与UnitHub的精确top3成员召回为Web93.953%/81.250%、Y97.323%/91.748%；路由NDC112.26/165.17、107.01/215.71。同seed重建GT10与原图接近，单次seed控制不替代构建方差。完整18点验证实际质量差=精确质量差+Unit的ANN作用−GT10的ANN作用；ANN项有正有负，不称非负Recall损失。

Web按K1/K100平均L质量变化+0.2441/+0.1989pp，吞吐比几何均值−0.06%/+0.35%；Y+0.1514/−0.0991pp、−1.13%/−0.84%。WebK100描述性质量区间正，YandexK100区间跨0；保留局部信号与全部负点，不插值或宣称等Recall加速。相对重建GT10结论相近。

实际1,106,688 NSG、1,106,496在线路由，4图构建核验约0.238秒，总编排1174.21秒；0新GT/底图/训练/K10。CPU15/实际线程1/串行，54点独立评分、同K/L和同入口控制、两个PNG/PDF检查完成。模型和源在query数值载入前冻结，此前允许SHA校验；已曝光数据不称盲测。配置前调用数手算和报告初稿速度范围措辞各有一次纠正，原件保留，均0额外搜索。

当前默认及生产E99保持，E103仍是最新完整五集前沿。本简单基线分支不追加seed/ef/L/repeat；接续E109预锁fit完美代理门，先判断目标信息再考虑预测器。

[报告](../entry_method_exploration/20260920_until1600_theory_v1/stages/e108_unit_hub_online/report.md) · [完整配对](../entry_method_exploration/20260920_until1600_theory_v1/stages/e108_unit_hub_online/results/paired.csv) · [质量分解](../entry_method_exploration/20260920_until1600_theory_v1/stages/e108_unit_hub_online/results/quality_decomposition.json) · [协议](../entry_method_exploration/20260920_until1600_theory_v1/stages/e108_unit_hub_online/protocol.md) · [状态](../entry_method_exploration/20260920_until1600_theory_v1/stages/e108_unit_hub_online/state.json)。
