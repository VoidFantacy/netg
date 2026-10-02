# E32 缓存门通过后的预锁运行清单

缓存门与独立NumPy复核已通过。本文在首次新候选路由和NSG调用前写入并冻结，继承protocol全部模型/成本/停止合同。训练模型不再改变。

## 路由实现验收

新的C8 Policy只增加固定两HNSW提案→原全H float32分数填满8→8个学习画像的float64分数→56个完整组合argmax→真实ID。候选生成逐条复用E28 propose.cpp的集合/排序/tie语义。学习分数使用unit query、float32 W升double累加、τ.05；不以原画像近似替代学习打分。plain/count加载同一个序列化图。新路由NDC包含两个固定HNSW的所有距离、H次填充得分及8次模型得分；组合加法、query归一化、排序等由完整wall计入。

先进行两集fit20K×teacher/reward全部路由对照：与冻结C8候选、slot和真实三入口逐条一致；plain/count一致。该路由验收调用HNSW但不加载NSG或读取GT。不一致时停止新图查询，保存失败证据，不以宽松阈值替代身份验收。

## 真实检索固定矩阵与预算

WebVid四方法：GT10-hard direct3、GT10-soft direct3（当前默认）、teacher C8、reward C8。Yandex三方法：GT10-hard direct3（同时为当前默认）、teacher C8、reward C8。L128的fit20K必须与全部缓存hits/NDC和原入口一致；cal/audit各1024仅用于预设开发门，不调模型/β/温度/阈值。

每个无wall方法点执行一次plain、一次count、16条原kernel独立回归。开发门为reward在两集cal及audit分别严格胜teacher和各集默认，graph NDC≤默认+1%。不满足即停止validation和QPS，仍报告所有实测结果。

只有开发门通过后才核对/读取历史validation前2K：5个L×7个dataset-method=35点；每点一次2000-query完整warmup、5轮独立plain wall、一次完整count、16条原kernel对照。各轮/各L轮换方法顺序，所有输出跨轮一致；CPU15，实际进程/OMP线程1，OMP/BLAS/MKL1。训练、分析、编译、hash不得与wall并发。

| 阶段 | NSG调用预留 |
|---|---:|
| fit 7点 | 280112 |
| cal+audit 14点 | 28896 |
| 条件validation 35点 | 490560 |
| 正常矩阵合计 | 799568 |
| 包含失败/修复的硬cap | 800000 |

所有成功/失败启动先记账，不通过覆盖目录重跑规避cap。90分钟全阶段wall上限，单job≤2000秒。当前7个方法组合固定，不追加NSG/Fast/自由向量/漂移匹配等新臂；因此不能声称完成所有强基线比较。建图成本另记，不进入QPS。

## 若进入validation，怎样解读

保留所有五点及5轮wall，分开报告Recall、零命中失败、路由/图/总NDC和完整QPS。只以实际非支配点构建Recall–QPS前沿；共同Recall比较使用双方前沿重叠区间的25%/50%/75%三个内部位置，log-QPS线性插值，全部目标和每轮原值保留，不外推区间，不按正收益挑目标。插值明确为描述性分析。

预设下一步证据门：reward相对当前默认，在两集上述全部3个共同Recall位置的五轮QPS比中位数>1.01，且五轮每轮均>1；teacher对照一并完整报告。这只决定是否值得提出独立复现，历史validation反复使用不能升级为盲测/最终性能GO。缓存、开发门或性能门失败均保留局部真实信号，不改写原GT10/E28/E31结论。
