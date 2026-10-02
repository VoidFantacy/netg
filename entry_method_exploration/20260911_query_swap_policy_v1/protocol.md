# E36：查询相关的三入口逐步换点策略

2026-09-11。用户明确同意推进“针对query，换入哪个点、换出哪个点；用实际三入口联合搜索收益反馈”。独立新版本，固定现有H/画像/原HNSW/NSG/真实ID/raw IP，研究每query的三入口选择。E35最小诊断已完成；本轮实际训练和部署新策略，不重启旧删边RL，不改全局候选库。

## 状态、动作与反馈

当前默认：WebVid GT10-soft-t1、Yandex GT10-hard，H815/821，原HNSW M16、efConstruction200、seed20260828、efSearch10。一次原HNSW取8个候选（与直接top3相同搜索预算），初态S0为前三个。56个三元素集合按候选rank字典序编号，S0=0。每态16个动作：action0停止；其余按“选中rank升序×未选rank升序”给出15种换出/换入。至多3步；停止为吸收终态，绝不根据GT自动回退，允许实际质量受损并完整报告。

每query×56个集合都实际执行原NSG L128/K10，三个真实ID升序共享beam；保存原始返回ID/距离/NDC，C++不读取GT。全部返回后独立评分，记hits(q,S)与图NDC。U(q,S)=hits(q,S)−hits(q,S0)−0.1×[(routeNDC+graphNDC(q,S))/(routeNDC+graphNDC(q,S0))−1]。每步奖励U(next)−U(current)，γ=1，无额外熵奖励，累计等于终态U，往返不会重复领取收益。训练使用这些实际完整组合的缓存反馈，逐轨迹保存state/action/reward；复用次数与新增NSG调用分别计费，不伪称每次梯度都新搜索。

查询投影/MLP不是额外base/profile距离计算，MAC/特征费用单列且必须进入实际wall；NDC门只筛距离工作量，不能替代总时间。

## 策略表示与两组训练

固定种子20260917产生16×d高斯投影，离线保存原画像的投影及pair cosine表；线上unit query投影一次。每个完整集合按所选候选rank排序，76维特征为：每个成员[rank/7、query–profile cosine、相对top1 cosine差、16维query投影×画像投影逐元素乘积]×3；3个成员对的画像cosine；16维query投影。无GT、query ID、NSG返回或oracle特征。按训练1792行×56集合的逐维mean/std标准化，std下限1e−6、clip±8；fit monitor/cal/audit不参与统计。

势函数F(q,S)=−.25×(sum ranks−3)+MLP(features)，MLP 76→16→16→1/ReLU，最后一层零初始化；初始贪心停在原三入口。行动概率为16个后继集合F的softmax，stop对应当前集合。在线各步按F最大动作执行，差≤1e−9时取动作序最小（stop优先），最多3步。只有query相关势函数，未实现任意state-action网络或改图；贪心不保证真实收益单调。

两臂相同表示、初始化、mini-batch行序、优化器、标签和日程：
- RL：采样三步轨迹，REINFORCE return-to-go=U(terminal)−U(current)，减去只由以往轨迹更新的query×state EMA baseline（初始0、更新率.05）；baseline不反传，每批完成梯度后按同query/state样本均值更新。没有PPO/critic网络。
- Exact：对相同三步16动作策略做完整56状态的动态规划，最大化同一初态期望终态U，直接精确反传；停止概率吸收，非直接全56终态softmax。此对照用于分离采样方差和表示/泛化瓶颈。

每臂两seed20260917/20260918，两集共8次各3000更新，batch64、float64、AdamW weight_decay1e−4；lr前50步线性3e−4→3e−3，随后cosine到3e−4，梯度clip5。训练CPU8/单线程，全部8次固定顺序，两集各RL seed17/18再Exact seed17/18。每100步保存模型、优化器/EMA、完整fit/monitor期望与贪心收益、改变/停止/步数；RL保存全部采样轨迹，不按开发改日程。checkpoint从step100..3000中选monitor平均U最高且graph NDC≤原+1%的最早点；若无可行点，仍保留最高U训练点并标记成本门失败，不拿未训练初态冒充训练成果。末点另存。

## 样本、控制与预算

每集从E24当前fit20K按PCG64 seed20260917预选2048行（前1792训练、后256 monitor）。cal/audit分别取E24原各1024中的前512，模型训练冻结后才准备cal，seed选择冻结后才准备audit。严格核验行身份、query/GT/H/图/源，所有split均有历史使用，不称盲测。现有E28/E32两路union C8与本轮单张GT10 top8不同，因此生成新完整标签；不用旧C8近似、单入口或未知标签=0。

cal/audit都实际比较6个方法：原top3、均匀16动作随机策略（同3步stop/动作域，按query源row ID的固定hash取动作）、两个RL seed、两个Exact seed。按cal平均U分别选RL/Exact seed，ties先更低总NDC再seed升序，先冻结再audit，不用audit改模型。训练fit另抽64个预定行/模型实际部署核对缓存完整返回，所有count/plain/原kernel以及C++/Python逐步动作须一致。

总新NSG硬上限300000，包括失败/修复；预估fit标签229376，全部fit/development parity约27000，固定L128成本测量约20000，修复余量不扩网格。单集标签任务≤1200s，单次训练≤900s/8次总≤7200s，单评测job≤1200s；RSS40GiB，新产物≤384MiB，磁盘余量≥10GiB。方法串行，查询CPU15且进程/OMP/BLAS/MKL均1线程，不并发训练/重分析/性能测试。训练独立记录时间，不当作QPS。

无论开发正负，均对冻结的原top3、cal所选RL、cal所选Exact在同一audit512的L128做一次完整warmup+五轮轮换独立plain整批wall，另count/plain/reference校验；这是一个L的成本诊断，不能称完整Recall–QPS前沿。在线计时包含一次HNSW、投影/特征/全部56势函数、至多3步选择、映射、原NSG、输出，GT/count/hash/I/O/load在外。没有新validation/held-out、多L前沿或图交换；它们不靠剩余预算自动追加。

报告预定开发门：cal相对原top3 ΔRecall≥+.10pp、audit ΔRecall>0，两集都满足且总NDC≤原+1%；RL另须在两集cal/audit平均U合并后胜随机，及报告相对同表示Exact的增量/完整正负。这些只是下一阶段判断，不据门放宽/扩训练；单Lwall不能替代前沿，任何默认替换保持未授权未执行。

## 验收与产物

查询前冻结协议、源码、二进制、输入/实际依赖身份；训练前复算全标签、动作图、reward telescoping、停止语义，使用完整路径枚举/有限差分验证DP与期望REINFORCE梯度一致和baseline不改期望梯度。GT不得进入在线特征或动作。训练后独立重建模型前向、保存轨迹reward/回报/EMA更新及选择，验证实际原NSG结果和缓存同一完整三元组一致。

完整保存8条训练曲线、checkpoint/末点/选点、RL真实标签轨迹、动作/交换/停止分布、GT-independent原始输出、所有开发正负/失败配对、单L五轮wall、CSV/图/Excel/报告，根四文档与历史25同步。旧E35/E34/E33/E32图/源/标签/模型/结果保护。最终区分“实现/训练完成”“fit收益”“开发泛化”“采样相对精确目标”“同L成本”，负结果也按完整协议收口，不外推所有RL无效。
