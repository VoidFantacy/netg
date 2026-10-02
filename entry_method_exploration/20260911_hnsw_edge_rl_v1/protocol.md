# E33：用真实检索收益训练 HNSW 边

2026-09-11。用户明确希望强化学习改变 HNSW 图，并授权“推进这个实验，方法可以自己研究”。本独立版本实现该方向；不延续 E32 的 C8 重排。协议在任何新真实搜索和优化之前冻结。

## 研究问题与作用位置

当前的小 HNSW 是 815/821 个真实 NSG 入口的导航图。固定当前默认画像（WebVid GT10-soft-t1，Yandex GT10-hard）、真实 ID、M16/efConstruction200/efSearch10/seed20260828、raw query/IP 与 NSG。只学习 HNSW **底层有向边**，上层、节点坐标、入口映射、NSG 搜索均保持。导出保留边后，线上使用原 hnswlib 搜索和原 NSG，不执行策略网络或 C8 生成。此轮是边删除，不是坐标位移或新增边；“最合适”以有限预算下实际 NSG Recall@10 衡量，不承诺全局最优。

依据 Baranchuk & Babenko, *Towards Similarity Graphs Constructed by Deep Reinforcement Learning*，https://arxiv.org/abs/1911.12122 ：将搜索过程中遇到边的 keep/remove 当作动作，终局奖励反馈到边概率。原文主要实验证据为 NSW/NSG、Recall@1–距离计算量，未实测完整分层 HNSW，也不能直接推出本任务的 QPS 收益。本轮保留完整 HNSW 上层，奖励改为三入口进入原 NSG 后的真实质量及总成本；采用表格化 Bernoulli 策略与 REINFORCE，非原论文 TRPO/神经网络复现。

## 策略、状态、转移和奖励

在原底层邻接表按 source/原邻接顺序编号边。保护从原 enterpoint 出发的 BFS 出树，以及反图 BFS 所对应的入树；二者必须覆盖全部 H，保证强连通。每个节点另外保护距离最近的两条原出边（ties 按真实 ID），全部原边顺序不变。若原图不满足这些条件，停止并报告，不能暗中新增连接。

其余每条边有独立 logit θ_e，p_e=sigmoid(θ_e)，初始化 θ=0。一条 query 的 episode 包括 HNSW 上层定位、底层 beam 遍历和原 NSG 搜索。底层某节点展开时，对其未访问目标的非保护边抽样 keep/remove；丢弃不标 visited、不算距离，保留则继续原搜索。只把真正会影响转移的抽样动作计入轨迹，每条边每 episode 至多一次。query、队列与 visited 构成环境状态；策略仅依赖边 ID，与 query 无关，因此能导出静态图。保护边不参与梯度。

R(q)=hits(q)−hits_base(q)−0.1×(totalNDC(q)/totalNDC_base(q)−1)。hits 是 exact GT10 中真实返回的命中数；totalNDC 是完整 HNSW+NSG 距离调用。即 1 个命中的奖励等于总 NDC 增加 10 倍的惩罚；它优先质量，成本是较小连续反馈。不能把该奖励或 NDC 当 QPS。基线逐 query 固定，GT 只在真实输出返回后由 Python 评分，搜索过程没有 GT。

REINFORCE loss = −mean[(R−b_q) sum_e log πθ(a_e)] − 0.001 mean_episode[sum_e entropy(p_e)]。b_q 为该 query **此前**奖励的 EMA，初始化 0，更新率 .1，当前动作梯度完成后更新。Adam lr=.025，600 更新余弦到 .0025，batch128，梯度范数 clip1，logit clamp±4；无 PPO、critic、教师标签或可微搜索代理。两个种子 20260911/20260912，双数据集共4次，顺序执行，不按结果扩超参或追加种子。

## 数据、选点与对照

复用原 fit20K，固定 numpy PCG64 seed20260913 的排列，前16000用于 rollout，后4000用于内部 monitor。所有这些 query 有历史训练使用；monitor 只是本轮不更新梯度的选点集，不是独立盲测。每更新从 train16000 均匀无放回抽128；每100步及0步，将 p≥.5 的边和全部保护边导出静态 HNSW，使用 monitor4000 真正执行 HNSW→NSG。保存每次静态图、全部 aligned IDs/入口/距离调用和导出几何身份。

每种子选择 monitor 奖励均值最高的非零 checkpoint，tie 最早；若它低于原图，仍报告并作有限开发诊断，不自动把原图称为训练成功。终点独立保留。原图是质量和成本基线；每份选中图生成一个确定性随机对照：每个节点保留与学习图**相同数量**的非保护边，使用 seed=训练seed+100，全部保护边/原边顺序同样保持。无训练随机图，用来区分学习与删边本身的影响。

cal/audit 各原1024，原图+两个选中 RL 图+各自 degree-matched 随机图，共5方法/集，L128。模型全部冻结后才读开发向量/GT；cal 在两种子中按同一奖励选一个主图（tie 小 seed），其随机对照绑定同一 seed。audit 不选点。全部方法都完成并独立重评分，不因单点差两命中就否定整个方向。

## 条件性能阶段与停止

主图在两集的 cal 与 audit 每一点，相对原图满足以下任一路径：A) Recall至少 +.05pp 且 totalNDC≤原图1.01倍；B) Recall损失≤.02pp 且 totalNDC≤原图.99倍。同时每集 cal+audit 合并奖励严格胜 degree-matched 随机图。全部实现/输入/输出验收通过，才进入性能阶段。任一点失败即停止后续 validation；保留所有训练、开发、成本与随机对照信号，不扩网格。

条件性能：原历史 validation 前2K，两集各原图/主RL图/对应随机图，L64/128/256/400/800。CPU15、进程和OMP/BLAS/MKL均1线程，每点一次完整warmup、五次轮换独立plain端到端wall、另一次count及16条原NSG核验。线上计时使用没有抽样/轨迹hook的原 hnswlib，GT/hash/I/O/构建不进入timer。各方法串行，训练/编译/分析不与wall并发。共同Recall重叠区间25/50/75%三个位置报告log-QPS插值及全部原始点，不把单个正点或插值称为正式GO。所有split有历史使用，不读/hash held-out。

## 预算、保护与验收

真实NSG调用硬上限1,200,000，含训练、基线、monitor、开发、条件性能、失败及修复；每job启动前预留，失败保留完整预留，不覆盖重跑。4次训练各最多600步，训练/monitor每job≤600s，全部运行≤3600s；RSS≤40GiB，新目录≤768MiB，/data剩余≥10GiB。未完成按真实状态保存，不靠剩余预算扩实验。

新源码、二进制、协议、输入、图与模型都绑定SHA256。原E32全目录及实际依赖做身份保护；更早保护链只比较已记录stat身份，避免为保护而读取无关旧validation内容。本轮读取阶段分别记录，未执行不写成0收益。原ACSG源码/主build/大图/旧标签和模型均只读。

必做验收：all-keep hook 与原HNSW逐query入口/计数一致；固定mask hook 与物理删边原HNSW一致；强连通/保护边/原顺序/每点≥3唯一入口；真实NSG与原wrapper IDs/float bits/NDC一致；小图枚举的REINFORCE梯度和有限差分、baseline不变性；训练原始返回独立GT重评分、query split隔离；导出图只改底层边、上层/坐标/映射不变；开发plain/count一致、五轮结果一致、旧基线回归。产物包括轨迹、模型/图、aligned结果、成本/门槛、图PNG/SVG/CSV/Excel、完整报告及四份根文档同步。
