# E29 教师标签与训练目标对齐：执行前协议

2026-09-11。用户授权推进教师/目标对齐并完成真实Recall–QPS分析。固定两数据集、E24 GT10 hard、H815/821、原raw-IP/NSG与一次microHNSW top3；只改离线监督和损失。fit/cal/audit/validation均有历史使用，本版本是有前作信息的本地探索，held-out不读取、不hash。

## 1. 两因素、四个完整对照

全部使用E28相同共享无偏置linear、W=normalize(P+AP)、零初始化、λ=100、温度τ=.05、float64、Adam lr=.003、全fit20k梯度累积、batch1024、80epoch、seed20260911、CPU8。没有MLP/宽度/正则/温度/seed网格，最后epoch导出float32。λ100沿用E28两集已选linear设置，并非本轮重新选择。

教师T0是原E28教师：C8的56个真实三元组中max GT10 hits、min graph NDC、max原画像分数和real-ID字典序选一个。教师T1仅在C8最高hits不大于原GT10实际HNSW3的hits时，保留该原三入口；有额外hits空间时完全使用T0。C8包含原三入口，因此无更低hits教师。T1主动放弃无额外召回空间组的教师成本优化；其影响必须报告，不能当作无代价纠正。所有行仍等权，不额外重加权正例。

损失C为E28完整三元组CE：z=unit(q)·W/τ，C=log Z3−sum(z_T)，Z3覆盖全H所有三元组，以稳定log-prefix计算。

损失M为带漏选成员代价的结构化hinge：

`M(z,T) = max_{|S|=3} [sum(z_S) + μ |S\T|] − sum(z_T)`，固定`μ=.1`。

通过给非教师入口加μ后取top3精确计算；不枚举全H三元组。μ对应单位query分数差.005，是本轮预定的单一margin。M≥μ×实际精确top3的漏选教师数；M=0要求最弱教师至少比最强非教师高μ（边界ties另按稳定real-ID）。该上界针对教师入口错误，不针对NSG Recall损失或QPS。它是标准margin-rescaling结构化hinge的加性集合特例，不宣称新的校准理论。单位化参数模型非凸；CE与hinge的梯度/有效正则强度并不完全等价，保留漂移、梯度和拟合指标，不将同λ视为公平性的充分证明。

四格`cost_ce(T0,C)`、`keep_ce(T1,C)`、`cost_margin(T0,M)`、`keep_margin(T1,M)`，每集四次，共8次训练。cost_ce须恢复E28 linear_r100的导出向量；数值不一致先查实现和输入，不能调模型追验证。全部四格保留，不按正负筛选或事后换epoch。

## 2. 标签与实现核验

复用E28的224万逻辑真实三元组标签，先绑定query/GT/row IDs、H和顺序、图/kernel、K10/L128、C8及真实原始输出身份。重新独立从全部top10 IDs重算hits/masks，核对T0选优与T1只在约定组变更。没有新增全H/single标签，不用缓存外的未知集合填造效用。

训练前独立小H全枚举验证两损失、梯度/有限差分、shift不变性、hinge成员错误上界和零损失margin条件；核对零残差与float32导出。训练后独立NumPy前向、最终损失与教师重合统计；保留每10epoch及最后epoch精确top3/完整集合匹配、边界margin、无/有Recall空间分组。拟合不足是结果，不自动扩大优化预算。

## 3. 冻结与真实评测

8份模型在任何新开发查询前全部冻结；本轮没有超参数选择。cal1024/audit1024只作同query的开发/泛化诊断，不能调模型。全部四格按原定矩阵进入正式比较，负结果同样交付。

1. fit20k：原GT10 hard和四格各L128 HNSW，完整fit真实检索仅诊断，不给计数批次写QPS；同时对照训练精确评分和实际入口，区分代理拟合与搜索效果。
2. cal1024：相同5方法×L64/128 HNSW。
3. audit1024：相同5方法×L64/128 HNSW，另5方法×L128 exact3诊断；exact无QPS。
4. validation2000：原NSG、Fast30K、GT1 hard、GT10 hard、原冻结GT1 soft/GT10 soft、E28已冻结MLP及四格，共11方法×L64/128/256/400/800×两集=110正式点。每点3次独立warm/plain完整单线程wall，方法顺序轮换。所有原始query输出/三次wall均保留。GT10 hard与四格的L128另测route/graph组件，不能相加充作端到端wall。

正式query固定CPU15，实际进程/OMP线程1，OMP/OpenBLAS/MKL1；一次一个方法、与训练及其它性能任务不并发。GT、计数、hash、I/O和建图在timer外；原始query→路由→原kernel→预分配输出写入在内。复制并核对E28已验收评测源码/二进制，原kernel/build不修改。plain/count/reference/repeated结果按bit检查，原方法输出回归E28；同模型五L入口与microHNSW一致。

## 4. 预算和停止边界

诊断点实际调用`2N+16`，正式三轮点`7N+16`，组件额外`2N`。fit共400160，cal41280，audit61920，validation1541760+40000，正常上限2085120。修复预留10000仅限已证实现/核验缺陷，总硬上限2095120；失败job完整预留计入账，不借历史剩余额度。新逻辑训练标签0，复用2240000；训练8次，不扩模型网格。目录≤1GiB，磁盘free≥10GiB，单job1200s、总查询进程3600s、RSS40GiB。无合成NSG搜索。

身份/评分/线程/parity/预算/非有限值异常暂停对应阶段并记录。修复不改变模型定义或借开发/验证结果调参；有有效模型但无拟合或性能改善时仍报告预定四格结果，结束本轮，不自动开下一网格。

## 5. 比较和产物

最终主判断来自同批独立端到端Recall–QPS完整曲线。预先指定共同召回参照：WebVid .75/.80/.85；Yandex .90/.95/.98，来自E28已知覆盖范围，因此不是盲设门。只在实测非支配前沿上对Recall–logQPS插值，不外推，不把插值叫新增实测等Recall点。某方法要建立本地双集性能GO，须各数据集至少两个覆盖参照点中位QPS较GT10 hard≥3%，三次对应比值均>1，并在所有覆盖目标点无≥3%中位退化；覆盖不足单列，不当作方法否定。部署建议同时对照原冻结GT10 soft/MLP及NSG/Fast，不能只在四个新格中选相对不差者。

两因素的教师效应`keep−cost`、损失效应`margin−CE`与交互`(keep_margin−cost_margin)−(keep_ce−cost_ce)`在各L的同query Recall/NDC上分别统计。它们解释本次固定配置的干预，不能当作等Recall加速。配对bootstrap2000次、seed20260911；三次计时不增加Recall样本，区间不校正多重比较。

交付完整中文报告、主/全部Recall–QPS图、明确标记的插值速度图、2×2因素与训练对齐图、PNG/SVG、CSV/XLSX原始图表数据、配置/模型/标签与调用清单、独立验收。同步spec/summary/s-target/s-experiment及历史18，保留E28和更早资产。
