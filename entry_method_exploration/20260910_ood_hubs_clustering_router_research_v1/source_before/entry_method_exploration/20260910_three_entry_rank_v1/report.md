# 三入口真实收益排序：完整W与rank8探索结果

2026-09-10，E23。状态 **`EXPLORATORY_SMALL_RECALL_SIGNAL_NO_CLEAR_QPS_GAIN`**。用户授权的方案已实现并完成训练、校准、audit与双数据集五点比较。本版本收口，不自动追加MLP、rank、seed或计时。

**结果：相对同训练数据的Fast20K三入口，有小幅Recall正信号，但没有形成明确的整体QPS优势。完整W训练更容易、固定目标更优，却未在最终搜索中胜过rank8；Yandex五点的Recall均是rank8更高。** 这支持继续把梯度学习视为可用工具，也说明降低这份排序损失与改善最终搜索之间仍有距离。

## 实际做了什么

- 两数据集、QGT seed20260828，H=815/821、原raw-IP和冻结NSG、K10；完整W参数417,280/164,200，rank8因子10,616/8,168。
- 固定真实入口身份，全部新方法与matched Fast都选三个互异入口。三个真实ID按升序交给原kernel；原Fast30K保留原heap顺序。只有入口表示改变，主图与搜索过程不变。
- fit20K，每query四个context×六个第三入口；真实三入口搜索产生96万逻辑标签，缓存去重后88万实际标注调用，另2304次标签parity。没有把旧single收益相加当联合收益。
- 每组内作pairwise logistic比较，以真实联合hit差加权、按query归一化；W=P0+τD，二次Fast锚定。Full与rank8使用同目标、同λ候选{0.1,1,10}和LBFGS；没有自由B映射、query端MLP或每个L重训练。
- 每数据集六个候选、每族三个，由cal1024选λ；audit1024不参与选择。双数据集的全部模型和选择记录冻结后才读取validation2K。fit/cal/audit是历史开发池，不称项目级全新未见数据；held-out未打开。
- 最终NSG、Fast30K-3、Fast20K-3、Full-3、Rank8-3，L64/128/256/400/800共50点；每点单线程，一次完整预热和一次独立plain wall，完整count在timer外。GT、hash、文件写盘、加载、建路由索引均不进入QPS。

具体合同见[协议](protocol.md)、[配置锁](config.locked.json)，实际阶段命令见[commands.md](commands.md)。

## 五点结果：先看匹配的Fast20K

下表每格为 **ΔRecall百分点 / ΔQPS百分比**，相对同H、同20K画像输入、同入口数、同HNSW参数/seed和相同入口顺序的Fast20K-3。每点2000query；单次wall的小幅变化不能认定为稳定加速。

| 数据集 | L | Full-3 | Rank8-3 |
|---|---:|---:|---:|
| WebVid | 64 | +0.070 / +0.23% | +0.035 / +0.45% |
| WebVid | 128 | +0.160 / +0.59% | +0.140 / −0.09% |
| WebVid | 256 | −0.005 / +0.87% | +0.010 / −1.10% |
| WebVid | 400 | +0.045 / +0.91% | +0.055 / +0.92% |
| WebVid | 800 | +0.030 / −0.95% | +0.045 / −0.07% |
| Yandex-IP | 64 | −0.065 / −0.00% | +0.100 / +0.05% |
| Yandex-IP | 128 | +0.105 / +0.53% | +0.290 / −0.09% |
| Yandex-IP | 256 | +0.005 / −2.96% | +0.120 / −1.50% |
| Yandex-IP | 400 | −0.030 / +0.52% | +0.095 / −0.68% |
| Yandex-IP | 800 | +0.015 / −1.11% | +0.060 / −0.25% |

Yandex Full在L64的QPS变化为约−0.00134%，表格四舍五入为−0.00%。该细微符号没有稳定性意义。

L128的原值便于理解变化幅度：

| 数据集 | 方法 | Recall@10 | QPS | 零命中失败 |
|---|---|---:|---:|---:|
| WebVid | NSG | 70.940% | 1834.51 | 103 |
| WebVid | 原Fast30K-3 | 73.990% | 2011.94 | 54 |
| WebVid | matched Fast20K-3 | 74.260% | 1997.81 | 54 |
| WebVid | Full-3 | 74.420% | 2009.57 | 52 |
| WebVid | Rank8-3 | 74.400% | 1995.95 | 52 |
| Yandex-IP | NSG | 88.660% | 1761.76 | 59 |
| Yandex-IP | 原Fast30K-3 | 89.830% | 1919.54 | 37 |
| Yandex-IP | matched Fast20K-3 | 89.720% | 1960.73 | 38 |
| Yandex-IP | Full-3 | 89.825% | 1971.16 | 38 |
| Yandex-IP | Rank8-3 | 90.010% | 1958.90 | 34 |

原Fast30K仍是需要展示的项目基线，但不能把相对它的全部差值归于学习器。例如WebVid L128，Full比原Fast30K高0.430pp，其中matched Fast20K本身已经高0.270pp，新增学习差值为0.160pp。Yandex Rank8的同点相对原Fast30K为+0.180pp/+2.05% QPS，相对matched Fast20K则为+0.290pp/−0.09% QPS。

完整50点、所有失败数、各基线配对挽救/新增失败和NDC见[原值表](results/tables.md)、[metrics.csv](results/metrics.csv)、[comparisons.csv](results/comparisons.csv)。没有挑选最有利的L作为整体结论，也没有对未测L作等Recall插值。

![Recall–QPS实测曲线](figures/recall_qps.png)

独立矢量图：[recall_qps.svg](figures/recall_qps.svg)。曲线连接实测点仅帮助阅读；Fast与两新方法大部分位置接近重合。

## 训练、校准与泛化

两个数据集各六候选完成后才校准；Full/rank8在WebVid都选λ=10，在Yandex都选λ=0.1。两族若允许Fast回退，cal也选择这些新候选；最终主表仍明确报告新模型，未利用validation重新选λ。

| 数据集 | 方法 | 选中λ | 固定训练目标 | cal R@10 | audit R@10 |
|---|---|---:|---:|---:|---:|
| WebVid | Fast20K-3 | — | — | 74.5312% | 75.0195% |
| WebVid | Full-3 | 10 | 0.639066 | 74.8145% | 75.1953% |
| WebVid | Rank8-3 | 10 | 0.639288 | 74.8047% | 75.1953% |
| Yandex-IP | Fast20K-3 | — | — | 89.6875% | 88.7695% |
| Yandex-IP | Full-3 | 0.1 | 0.269570 | 89.9902% | 88.9062% |
| Yandex-IP | Rank8-3 | 0.1 | 0.277147 | 89.9707% | 88.7109% |

训练目标包含数据损失及同样的正则项，不能跨数据集比较数值；所有表中cal/audit均为实际HNSW三入口搜索。另有fit前1024条的诊断，它不是完整20K的搜索质量均值。

六个Full求解的强凸梯度残差上界均小于3×10⁻¹²，固定目标已充分优化。对应同λ下Full目标均低于rank8。Full六个模型的核心拟合时间合计约7.35秒，rank8约125.78秒；含输入、初始化、SVD、导出及启动的全部训练子进程合计137.45秒。这个速度关系仅针对当前实现/目标，不推广为任意低秩训练都更慢。[训练明细](models/jobs.json)、[模型行为](reviews/model_behavior.json)

完整W的更低训练目标没有换来一致的最终优势。尤其Yandex，rank8在最终五个L上Recall都高于Full，同时它相对matched Fast20K的Recall五点都为正。可能解释包括低秩带来的正则效果、有限校准样本及训练代理与部署目标的差异；本轮无法把这些原因逐一量化分离，不能声称rank8是最优维数。

这次W确实更新了：选中Full的残差范数为WebVid0.02922、Yandex1.63584，约为P0范数的0.102%/5.709%；validation中354/2000和1311/2000条query改变了三入口集合。它不再是E22“W几乎不变、主要改mapping”的情况，但大量入口变化仍只带来小幅总体质量变化。

## 目前能定位的问题

**图搜索成本基本没有下降。** 相对matched Fast，Full的逐点graph NDC变化约−0.263%至+0.011%，rank8约−0.382%至+0.025%。Yandex路由NDC从110.14增加到Full115.03、rank8 114.10；图搜索的细小节省可能被路由成本抵消。最终判断取独立wall，不能用NDC代替QPS，也不能据这些计数精确解释单次wall的全部波动。

**精确评分与HNSW部署之间存在变化，但精确评分不是搜索效用oracle。** 例如WebVid的弱正则Full在cal中，精确三入口R为74.8926%，HNSW三入口为74.3164%；而某些Yandex点HNSW反而比精确top3的下游Recall更高。模型分数最高不等于实际搜索最好，不能把所有差值统一称为ANN召回损失。[完整诊断](results/summary.json)

**固定单项分数不能同时满足所有条件偏好。** 对同一query、同一对a/b，在不同另外两入口context下，已观察到收益方向反转。WebVid有319条fit query、412个冲突query–action pair；Yandex为82条query、97对。分母分别只有8444/2904个在多个context重复出现且收益非零的pair，不能外推全H的冲突率。这证明当前采样排序标签中存在不能同时满足的要求，不证明静态评分无法选出某个好三元组，也不能单独解释全部性能差距。[只读统计](reviews/model_behavior.json)

因此，后续若继续，优先处理“训练奖励怎样对应最终top3的联合搜索收益”以及泛化/部署差异。完整W保留为优化参考，rank8保留为正则化对照；当前证据不支持直接丢弃低秩，也不支持仅换优化器或加入MLP就会解决问题。本轮未执行这些后续假设。

## 验收、成本与证据边界

- 单线程合同、三个互异入口、每点16query原wrapper比较、全量plain/count的ID/距离bits/入口一致性、100000个validation输出的独立GT10评分全部通过。NSG与原Fast30K共40000个query输出及入口/距离bits与E22逐位相同。
- 两dataset的各模型W、mapping及每query三入口在五个L下保持不变。所有50点完成，没有重训、追加λ或根据validation换候选。
- 标注核心wall41.48秒，含加载的标注子进程58.89秒；训练137.45秒；fit-probe/cal95.68秒；audit29.05秒；最终评测子进程381.64秒。它们都不等于查询QPS。本轮数据上的真实搜索调用总数1,325,344，包含标注、parity、诊断、预热和独立count；细项见[成本账](results/costs.json)。
- **新增标注88万次不是从零构建的完整成本。** 当前候选提议复用了旧全H single标签。按现有提议器直接从零复现，还需要20K×(815+821)=3272万份single入口标签；本轮新增single调用为0。旧E22的169,857,792次/6639.99秒覆盖更多构建和标签L，不能全部归为本方法专属费用。exact GT、QGT、原图等成本复用且未新测，完整从零成本保留未知。
- 一处诊断元数据继承错误已在audit/validation前修正：v1 verification中的warm_timed_queries误写为n，但实际诊断没有warmup，results.json中的0和QPS=null均正确。旧二进制、源快照、输出和选择保留，v2只改验收元数据，没有改变数值结果。[修正记录](reviews/diagnostic_metadata_correction.json)
- 本轮只有一个构建、每dataset2000条validation、每点一次wall；不作正式显著性、跨构建稳定性或完整部署GO。没有held-out、MLP、C联动或大矩阵恢复。

主要入口：[最终结果核验](reviews/result_verification.json)、[冻结模型manifest](models/frozen_before_validation.json)、[最终完整性检查](reviews/final_audit.json)、[全部原始结果JSON](results/summary.json)。原E22的负结果及本轮所有局部正负值均保留。
