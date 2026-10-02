# 方法依据与解释边界

本轮采用参数空间的一步 Gaussian 策略搜索。策略动作是一套共享画像变换参数；环境为确定性HNSW构建、当前query批次和原NSG搜索。随机采样只在离线出现，最后导出确定均值画像和普通物理图。

对 μ+σε 的目标 E[R]，Gaussian score-function梯度为 E[R ε]/σ。RL用独立采样与leave-one-out baseline；ES用对称扰动降低部分噪声。二者估计同一平滑目标，不将名称差异包装为不同表示能力。这里没有反向传播穿过HNSW或原NSG，也没有PPO状态价值网络。最终必须另验确定均值画像，不能从随机奖励推导确定部署质量。

主要一手参照：

- Salimans et al., [Evolution Strategies as a Scalable Alternative to Reinforcement Learning](https://arxiv.org/abs/1703.03864)，2017。支持参数扰动黑箱优化和与policy gradient的关系；本轮不是其完整算法/性能复现，只有8候选且严格串行。
- Baranchuk & Babenko, [Towards Similarity Graphs Constructed by Deep Reinforcement Learning](https://arxiv.org/abs/1911.12122)。学习边概率、最终导出静态图的前例；本轮改变画像并重建HNSW，没有沿用只删原边动作。
- Ruan et al., [GATE](https://arxiv.org/html/2506.15986v1)。离线学hub表示、构建高层导航图的前例；本轮监督为部署HNSW实际三入口原NSG联合反馈，而非GT1-hop教师。

当前源码/证据核对：E28的[历史17](../../experiment_history/17_gt10_shared_transform.md)、E32的[历史21](../../experiment_history/21_direct_reward_policy.md)、E33/E34的[历史22](../../experiment_history/22_hnsw_edge_rl.md)/[23](../../experiment_history/23_hnsw_rl_benchmark.md)、E35的[历史24](../../experiment_history/24_hnsw_selection_diagnosis.md)及E36的[历史25](../../experiment_history/25_query_swap_policy.md)。不能把“离线学习画像”“使用真实奖励”单独当作从未做过的新方法。

静态 W 上的 qᵀW 仍然只提供单点打分，无法表达任意三入口组合交互。固定16方向、256系数属于本轮成本限制，不代表最优秩或所有画像学习能力。构图种子固定让差值可复查，也不提供跨构图seed泛化结论。原画像和开发样本的历史使用必须保留披露。

本轮要回答的具体问题是：在最终上线保持原始query→一次HNSW3→原NSG的条件下，直接根据这条实际路径优化画像，能否比锚点获得稳定质量/成本改善；采样RL是否比相同预算的成对扰动提供额外价值。
