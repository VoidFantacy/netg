# 75｜真实单边效用筛选静态小图（E86）

2026-09-13第9串行会话，双集预锁接受门FAIL，本固定64/47几何候选与筛边版本停止，0新QPS。Web对compact局部修复保留，训练收益不当性能结论。

固定E73 compact全部W/真实H/映射/原边/上层及原NSG/rawIP，取E84按票数排序前64/47边。每条独立实际加边、全fit20K真实HNSW→原NSG响应；全量净命中正、两半非负、失败不增、总NDC≤1.01筛选。合格边合并后重新实际测量，并在相同源节点加最近其他hub边作度匹配控制。E33是原边删除，E84是几何投票，本版直接测加边效果；候选来源仍受几何排名限制，不能把完整三入口教师直接当单边信用。

Web64边31正/13负/20平，29条接受，单边相对原compact净命中之和235、合并实测191；16query非加性，含重复作用与交互。Y47边3正/1负/43平，3条接受，单边和/合并均13。并图fit两半Web97/94、Y9/4；失败−13/−1。训练全池筛选及继承画像都有历史暴露。

| aux7952 | 对P：净命中/失败变化 | 对compact | 对E84 | 对度匹配控制 |
|---|---|---|---|---|
| Web | −41/+8 | +18/−3 | −24/+1 | +18/−3 |
| Y | +116/−13 | −4/0 | 0/0 | 0/0 |

Web对compact救回4/新增1；小幅修复不足超过原P/E84。Y主要继承原compact收益，训练新增正值未迁移。全部GT成员增损、query净增损、原收益保留/丢失、新损伤与各半门保留，不扫阈值/边数。完整413失败并集、173状态变化、2065个五方法完整GT/入口/返回单元保存。

新NSG170336=训练8416+辅助161920；HNSW4842112=训练4680512+辅助161600。6静态安装含2首边回归图，2离线筛边拟合，0普通构图/梯度/新GT。编译13.345s，训练操作77.107s、辅助操作131.177s，均不当QPS；继承GT/P总成本未知。原kernel不改，CPU15/实际进程及各库1线程，完整真实工具terminal0。

effective native_training.json使用既有exact20K文件，与E66前缀query/GT/rows逐字一致；原准备native.json的22048容器模板未执行且保留。111候选全route plain/count、合法缓存完整键/全部新增4112唯一三入口、合并图和6图字节恢复/旧边可达性、原32三路与首边128物理回归通过；独立集合/mask、全部7slot、47712旧P/compact/E84输出恢复通过。图初版负值标签留白修正保存initial源/图，不改raw。

P-fit20K=router_train[10000:30000]含旧train/monitor；aux=[2048:10000]、两半、cal/audit历史暴露，接受反馈计训练。E34最终原始输入/held-out本版未打开。原E86门保持，后续若改变候选来源必须独立前瞻协议，不扩本版候选。

[完整报告](../entry_method_exploration/20260913_until2100_v1/stage27_edge_utility_v1/report.md) · [协议](../entry_method_exploration/20260913_until2100_v1/stage27_edge_utility_v1/protocol.md) · [训练源码](../entry_method_exploration/20260913_until2100_v1/stage27_edge_utility_v1/src/train.py) · [原配置](../entry_method_exploration/20260913_until2100_v1/stage27_edge_utility_v1/config.locked.json) · [门](../entry_method_exploration/20260913_until2100_v1/stage27_edge_utility_v1/results/gate.json) · [训练核验](../entry_method_exploration/20260913_until2100_v1/stage27_edge_utility_v1/reviews/training_verification.json) · [查询核验](../entry_method_exploration/20260913_until2100_v1/stage27_edge_utility_v1/reviews/verification.json) · [成本](../entry_method_exploration/20260913_until2100_v1/stage27_edge_utility_v1/results/cost.json)
