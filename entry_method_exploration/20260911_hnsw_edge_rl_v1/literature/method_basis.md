# 方法依据与本轮选择

主要一手来源：[Baranchuk & Babenko, Towards Similarity Graphs Constructed by Deep Reinforcement Learning, arXiv:1911.12122v2](https://arxiv.org/abs/1911.12122)、[论文PDF](https://arxiv.org/pdf/1911.12122)、[作者代码](https://github.com/dbaranchuk/nns-meets-deep-rl)。已核对论文第3节的方法、3.5的候选边范围及4.3的实验对象，另核对作者README的图删边/MDP/TRPO说明。

论文将图边表示为独立Bernoulli变量，通过搜索终局反馈学习保留概率，最终导出确定性子图。其大规模版本限制在初始图已有边中删除，采用端点特征网络和TRPO；主要实验为NSW/NSG、Recall@1与距离计算量。论文明确将附加分层索引的完整HNSW实测留作后续，因此不能称其已经验证本项目的分层入口路由和端到端QPS。

本轮采用这一问题建模，做任务适配：对已有小HNSW底层边直接设置参数，用REINFORCE估计真实HNSW→NSG终局收益的梯度；固定上层和画像，增加出树/入树保护，导出后回到原hnswlib。表格参数避免在小固定图上先增加神经网络容量；每条边的梯度能直接检查。使用每query历史奖励基线减少方差，均匀随机删边作同逐节点出度的控制。

未选“只训练坐标再按普通规则建图”：它会同时改变画像分数和拓扑，难以在第一轮分离两者。未选“在线RL逐跳导航网络”：线上推理成本和静态图方案不同。此处选择的是直接训练图边，不是证明其它两种方向不可行。

本轮新增的状态/动作/奖励、骨架规则、超参、预算与门槛属于预先制定的实验设计，详见[协议](../protocol.md)和[训练前结构修正](../structural_preflight_repair.md)；不是对原论文结果的复现承诺。
