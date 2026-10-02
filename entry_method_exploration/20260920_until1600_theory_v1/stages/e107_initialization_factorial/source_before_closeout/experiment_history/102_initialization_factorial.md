# 102｜E107 表示与入口数的系统因素对照

2026-09-20，在用户持续推进到16:00的活动目标内执行，当前真实矩阵进行中。本轮机制问题是区分GT10相对固定NSG入口的整体收益、查询画像的作用、多入口的作用、GT10相对GT1的多目标增量；不是E106 GroupMean重跑，也没有新候选训练。

原H、NSG、raw-IP、E105各4096已曝光query/GT固定，UnitHub/GT1/默认GT10三表示×1/3入口，加固定NSG单入口与默认ANN；K1五L64/128/256/400/800，K100四L128/256/400/800。全H exact用来剥离路由近似，缓存入口无新在线QPS。单入口包含于相同表示的三个入口，但实际搜索未必单调。

已在原span+batch4内核上核验五节点强连通反例：L2/K1，新增更近入口导致正确分支被挤出，Recall下降。该2次合成搜索说明一般单调保证不存在，不证明实际数据普遍发生同一结构。两集前16行smoke全部方法与原E99链接内核的ID/距离bits/NDC一致；全量预定1181184次真实NSG，0新GT/图/训练/K10/正式QPS。使用独立进程组、CPU15/线程1/串行及15:50搜索截止。

论文的路径上界、度量可导航假设与当前raw-IP/有限beam分开解释。真实结果须保留全部K/L、表示与交互、逐query收益/损害、零命中和NDC，不能按较好预算回填故事。完整状态与证据：[研究推导](../entry_method_exploration/20260920_until1600_theory_v1/stages/e107_initialization_factorial/research.md) · [协议](../entry_method_exploration/20260920_until1600_theory_v1/stages/e107_initialization_factorial/protocol.md) · [状态](../entry_method_exploration/20260920_until1600_theory_v1/stages/e107_initialization_factorial/state.json)。
