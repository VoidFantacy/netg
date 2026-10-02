# E122 动作关联的预测函数正则：执行前冻结

动机来自[局部响应结构门](../../research/action_response_locality_v1/report.md)。真实hub几何通过双集双K门；GT10画像几何未通过全部门，不调邻居数/阈值补过。E121上层状态表保持停止，本版不使用z或修改其表，而检验动作侧统计耦合。

## 数据和可检验主模型

仍只用E118历史fit4096全H K1/K100/L128响应，沿用E121预先冻结四折。3072行拟合、1024行外折；每K独立。结构筛选已查看这批的整体响应，因此这些外折结果只算后续开发，不是新盲测。模型参数和时间尺度不得用外折标签。

x为unit raw query，训练侧居中，不做逐维标准化/PCA。y为各单hub相对默认的u=ΔR−0.1ΔT/mean_train(T_default)，T为旧graph-only三次平均。y训练侧逐动作居中，训练均值作为截距；默认始终精确零。

真实hub的8近邻有向关系沿用刚冻结的数组；对称化A=(B+Bᵀ)/2，L=diag(A1)−A，再除以平均度，使tr(L)/H=1。不根据响应学习边或谱。置换关系只重标同一节点，谱相同。

主模型FunctionSmooth：最小化 ||XW−Y||²_F +10||W||²_F +tr(WᵀXᵀXWL)。预测函数的动作图能量受约束，beta=1。三控制：Independent，移除图项；PermutedFunction，用同谱置换关系；CoefficientSmooth，图项改为10 tr(WLWᵀ)，仅诊断函数平滑和系数平滑的区别，不晋升候选。另有Default和训练侧GlobalCost。

使用精确对称特征分解求闭式解，不迭代调参。α10、β1、8邻居和seed均固定，无CV选参、阈值或checkpoint。各query选择预测u最大且严格正的真实hub，否则回退；同分优先默认、再真实ID小者。理论上可把仿射评分编译为静态增广向量，未通过开发门前不建新HNSW或原生部署。

## 门、审计与后续

唯一主候选FunctionSmooth需：两集等K实际外折u的98.75%描述bootstrap下界均>0，各K Recall均值损失≤0.1pp；两集均值分别胜Independent与PermutedFunction，等数据集的两个配对增量98.75%下界均>0。20000次整query bootstrap、seed2026092219。平均MSE/更小图能量仅作诊断，不代替决策门。CoefficientSmooth或Independent正值不能事后晋升为主候选。

失败即STOP_ACTION_COUPLED_RIDGE_V1，不追加alpha/beta/k/特征/网络或谱截断；通过才具体冻结目标预算的真实响应/完整费用协议。完整性能仍需真实K1/K100、同底图/主搜索/固定L、CPU15单线程串行及选择外新来源验证。

先验证小矩阵Kronecker直接解、正规方程残差、β=0等于独立ridge、预测与静态向量等价及折隔离；实际输出另作独立求解/动作核验。<=8离线数值线程、<=2GiB新增、至少6GiB空余，0新ANN/NSG/GT/搜索图/QPS。本轮有闭式模型拟合，不能称0训练。费用标签未含新路由费用，正u也不构成吞吐结论。
