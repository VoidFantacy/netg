# 原论文保证迁移到raw-IP时的边界

2026-10-02理论/论文研究。正文原理实读后再作下面推导；不启动新图、搜索、GT、训练或性能。此文件补足“几何/概率保证为什么不能直接当当前Recall–QPS保证”，没有提议修改原主搜索。

## 1. 自适应入口：更好的hop上界仍不足

Oguri与Matsui的[Adaptive Entry Point Selection原文](https://arxiv.org/html/2402.04713v1)已读§2–4、§5.1及§6。B-MSNET允许有限后退步，Theorem4.4在query与GT的Voronoi关系及局部/全局半径条件下，比较自适应入口与中心入口的hop上界。它是有条件的上界比较；两条上界谁小不等于两条实际路径谁短，更不等于固定有限pool中会发现谁。实验使用8线程；本文没有将其速度搬到当前1线程端到端结果。原结尾也区分满足条件的频率与平均改善证明。

例如实际路径步数a≤10、b≤20并不能推出a≤b：a=9、b=2仍满足两界。再加上不同展开节点的degree、访存与路由费用，hop更不是QPS的充分统计量。当前能更直接连接搜索质量的是[发现/边界闭包机制](search_effect_theory.md)，但其边界依赖真实执行，不是免费入口监督。

## 2. raw-IP不是距离度量

令s(q,x)=qᵀx。当前路由常用float32(1−s)，主图使用负IP评分。可变范数下，这些数可为负，也不满足一般的距离度量条件，因此不能原样代入依赖三角不等式或非负距离比的图搜索定理。逐target单位化还会改变MIPS排名；统一正尺度与逐向量归一化是不同操作。

[Neyshabur与Srebro，ICML2015](https://proceedings.mlr.press/v37/neyshabur15.pdf)已读§1、§4.2（式9–10）、§5.3（式13）。论文以补坐标把有界向量映到单位球，并区分query/data的域与对称/非对称哈希；该变换本身还追溯Bachrach等2014。下面只是其补坐标思想的raw-IP尺度适配，不认领新MIPS规约。

对有限bank取R≥max_x||x||，令

\[
\phi(x)=[x;\sqrt{R^2-\|x\|^2}],\qquad\psi(q)=[q;0].
\]

则精确实数下

\[
\|\psi(q)-\phi(x)\|^2=C(q)-2s(q,x),\quad C(q)=\|q\|^2+R^2.
\]

所以同query的精确排序与IP一致，包含负IP情形。它不保证native float32实现bits一致，一般也不保存原数据点之间的距离或图的导航性质；等范数等特殊情形应另算，不能用特例覆盖当前可变范数合同。

## 3. 保排序不等于保近似因子或搜索合同

若某metric算法保证d_return≤α·d_opt，平方并代入上式只得到

\[
s_{return}\ge\alpha^2s_{opt}-\frac{\alpha^2-1}{2}C(q).
\]

第二项可能很大，不能简写成同样有用的IP乘性近似。任意加大R仍保持精确排序，却使该下界越来越松。这说明“排序等价”与“近似保证有相同效用”是不同命题。

更具体地，[Distance Adaptive Beam Search，Al-Jazzazi等](https://arxiv.org/html/2505.15636v1)已读§3–4及Claim2。其正保证要求metric和该metric下的navigable graph，并改变终止条件；当前冻结raw-IP图没有这份导航证明，转换向量也不会自动赋予它。新停止与新候选队列还会改变实际搜索合同。所以它是值得理解的替代搜索前作，不能从其定理给当前GT10入口版性能GO。对该替代方法的未来实验应另立合同，本轮没有启动。

## 4. 单次路由测试的概率不是整个query的Recall保证

[PEOs，Lu/Xiao/Ishikawa，ICML2024](https://proceedings.mlr.press/v235/lu24l.html)的[原文](https://arxiv.org/html/2402.11354v2)已读§2–4、RoutingTest定义及MIPS扩展说明。它在探索邻居时先做概率测试，再决定是否执行精确距离；“符合当前距离阈值的邻居以至少1−ε概率被接纳”是局部测试性质，不能直接写成每个query只损失ε的Recall。Theorem6.3还要求m足够大，不能默认当前任意有限配置已给同一ε证书；MIPS扩展列在附录D.2，正文将其评测列为后续工作。该机制改变邻居评分/搜索过程，超出当前入口合同。

在一个额外满足耦合条件的模型中，固定query原生参考trace上有m个必须保留的决策，每个相关误拒事件概率≤ε_j。所有这些事件都不发生时，若其余改动严格保决策，可归纳恢复参考输出。于是union bound给

\[
Pr(\text{出现参考决策偏离})\le\min(1,\sum_{j=1}^{m}\epsilon_j).
\]

这里不需假设测试独立，但需要这些局部界确实适用于同一固定参考决策事件；如果只在自适应选中后才宣称条件概率，要另证条件化仍有效。这是对局部保证的审查推导，不是声称原PEOs论文给了当前输出parity界。误拒可能破坏唯一有用桥，而多个不影响GTK的误拒也可能不改变Recall；局部错误数与最终命中损失不能互换。

若这些额外前件均成立，记p为上式概率界，则固定query上R∈[0,1]还给出`E[(R_ref−R_new)_+]≤p`，从而`E[R_new]≥R_ref−p`。这是期望损失的保守界；p可能退化为1，没有保证某一次查询质量不降，也没有给QPS或费用保证。

概率门、变换/测试费用、native误差与完整wall都要各自说明。本轮保留确定性memo/原阈值拒绝的具体合同，不把这些论文的理论或实测倍数当作ACSG新结果。

## 5. 合成代数核验

[algebra_checks.py](algebra_checks.py) / [结果](algebra_checks.json)用Fraction检查450个完整成本/g门案例（含默认memo变慢的反例）及1080个制造的IP-to-L2近似因子案例；另检验阈值收紧后当前pivot球界可能从无间隔转为可拒绝，以及不同float32 dot可折叠到相同`1-dot`距离的例子。结果PASS；0真实数据读取/ANN/NSG/GT/性能。有限例子检查推导和范围，没有替代普遍证明或真实库证据。历史审查代理已独立重读这些原论文关键节并核验公式，没有把局部概率保证写成当前query保证。

## 6. 2025 query-scaled与混合metric补读

[补充原论文笔记](latest_mips_literature.md)核对Query-scaled/PSP及MAG。有限库逐query存在top1对齐缩放不等于全部cutoff/跨前沿比较保真；完整严格IP比较对需满足`2μ·IPgap>norm²差`。仅在原精确IP核正缩放不提供新搜索信息。PSP的AET与MAG的L2前缀/visited重置改变必展开或实际seed前件；本轮没有移植这些方法或运行新性能。
