# E44：局部动作的完整训练池与采样方差诊断

2026-09-12。用户持续研究授权至20:00。E43八次训练已验收但Yandex未过monitor门，0新开发；本版本先验证明确的反馈稀疏问题，不重训、不改σ/方向或扫描采样网格。

## 冻结状态与完整参考

固定E43两数据集RL第一seed20260921，在原step20/40/…/200的动作前状态，各10个context。每个状态W由前一个20步checkpoint及已保存next_row逐字恢复；目标hub、μ行、八ε及候选行沿用原轨迹，不根据本轮完整GT或旧正例挑选。H、P/B、原query/GT/source row、metric/NSG和普通HNSW参数不变。

每context当前C和八原候选A0..A7共9图，全部真实查询E37 train前4096行。GT只在返回后评分。当前图/候选的完整拓扑SHA恢复E43，全部原uniform128返回/距离bits/入口/route与graph NDC必须从新full4096切片逐位恢复；不能用原未观测格填0。只用历史train，monitor/cal/audit/validation/held-out不作新查询。

每图保存完整raw返回、拓扑数组/identity，W由已保存C及原候选行可重建；每集首末context的18个图另保存物理graph，前16query做count/serialized plain/原kernel三路parity。其它图不声称物理序列化parity，全部仍须原uniform128回归和完整拓扑身份。

## 唯一采样控制

总体N4096。对每个目标hub，近组固定为E37原anchor三入口中含该hub的query；它与本轮GT/候选返回无关。近组大小N1>0，补集N0=N−N1。

uniform：全体均匀无放回128。stratified：近组抽n1=min(64,N1)，补集抽n0=128−n1，分别无放回；使用总体权重(N1/N)和(N0/N)，每条样本权重对应(N组/N)/n组，总和1。若补集空则退化uniform128。只比较这一种固定分层，不按结果调64、改query budget或丢弃补集。当前研究不能把最后选中目标hub的query当完整影响集。

用真实全池矩阵计算逐query的hits/总NDC/零命中U以及当前J差，原anchor NDC分母及漂移权重保持。RL条件梯度贡献g_q=(ε−meanε)ᵀU_q/(7σ)，16维；漂移梯度与query无关，单列且不计入query噪声。保存完整true full-train条件梯度与原uniform128估计的差；当前W/目标/ε固定，结论不含方向采样噪声或优化迭代噪声。

均匀SRS均值方差trace=(1−128/N)tr(S_all)/128；分层为Σ_a (N_a/N)^2(1−n_a/N_a)tr(S_a)/n_a，其中S是实际有限总体的样本协方差（分母N_a−1）；空组/单元素census的方差项为0。两者均为正确总体权重的线性无偏估计，故该条件MSE等于方差。以逐维独立标量公式和加权均值恒等式核验，不用少量Monte Carlo近似主结论。

单列命中梯度、总效用U梯度的方差及true梯度，正/负命中变化在近组和补集的全量覆盖。近组能覆盖损伤不代表也能覆盖收益；补集所有收益损伤完整报告。逐候选G/L/net/hit-change query数与完整池oracle只作解释，不选新模型或将免费参考当在线收益。

## 查询前固定的门

各数据集必须至少4/10 context具有非零质量梯度总体方差（阈值1e−18）；分层U方差之和≤uniform的50%，且至少60%的非零uniform U方差context分层不变差。双集同时满足，才允许后续唯一的加权采样训练修订。分母0记undefined，不把0/0算通过。未满足就停止该分层方案，不扫近组大小/新邻居规则。此门只决定研究接续，不构成学习/泛化/部署GO。

## 成本、保护与deadline

正常2×10×9×4096=737280 NSG；首末context36图×16×3=1728 parity；总预计739008 NSG、738432 HNSW、180图，0optimizer/新GT。每集完整预留369504/native cap370000，总硬限760000，失败不释放、不自动重试，拒绝覆盖。重建/核对使用已保存行，不重新优化或采样。

CPU15，实际进程/OMP/OpenBLAS/MKL均1线程，两集和图串行。每dataset timeout900s，19:40查询截止且19:25后不启动完整job；分析CPU8。地址空间32GiB、目录256MiB、最低可用9GiB。9GiB是本独立版本在查询前按小于256MiB产物预算锁定的新余量，不修改E43已完成的10GiB合同，不更改文件系统保留块。所有大向量/图/结果写/data，保留原E37–E43及native依赖SHA，根文档前件另存。

进程wall含加载/构图/计数/写盘/parity，不作为QPS；完整参考标签成本全额报告，不能称等工作方法比较。交付180原始全量结果/拓扑、代表物理图、逐query和context CSV/NPZ、精确条件方差/覆盖表、独立核验、图表及报告；新增历史33并同步四主文档。阶段结束继续20:00目标的下一有证据步骤。
