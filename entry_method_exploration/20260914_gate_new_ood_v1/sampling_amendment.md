# 正式测试前的 GATE 子图采样修正

直接核对 pinned release `cluster/embadding/subgraph2json.py` 后确认其 `SAMPLE_SIZE=10`，选择5近邻与5远邻。旧本地适配器使用动态样本数，当远邻数为0时写成 `sorted_indices[-n_far:]`，而Python的`[-0:]`返回整个数组。Yandex原图的min_degree=1/max_degree=64，因此动态x在所有有效度数上为1，实际遍历了全部邻居。这是适配器错误，不能作为作者采样实现。

新版本固定采用release的10邻居规则：邻居数≤10时全部去重保留，否则5近+5远，按原L2几何排序，保留已锁定的最大5hop/1000节点上限。上游片段的distance函数未定义、无1000点上限，因此这仍是明确的CPU/IP与规模适配，不宣称完整逐位复制作者仓库。Graph2Vec算法、维度、迭代、seed均不变。

修正不由最终测试或模型监控优劣驱动。尚无public测试。已完成Web旧采样模型、已停止Y旧采样模型及旧子图/Graph2Vec保留历史身份；正式模型统一放在`models/<dataset>/gate_release10_v2/`，图特征在`inputs/<dataset>/graph2vec_release10_v2/`。复用真实hub、原NSG和全部已验证标签，因为它们不依赖Graph2Vec。受影响Web/Y训练从同一seed和初始配置重做，LAION直接采用正确采样。

取消训练的滚动optimizer恢复文件属于临时恢复状态，在记录大小/SHA后回收；对应最佳模型、画像、训练历史、取消原因、所有图特征和搜索标签完整保留。完成所有三集训练后再构建尚未完成的大HNSW，避免临时恢复文件与大图写盘峰值叠加。

直接来源文件和URL/SHA保存在`sources/gate_upstream_subgraph2json.py`及其`.source.json`。旧冻结协议和HBKM修正均保留，新增此修正及独立锁定记录。
