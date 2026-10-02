# E31 训练有效性检查：执行前协议

2026-09-11。用户同意一次CPU训练合计不超过10分钟的优化检查。独立版本，保持E30共享linear模型、两个教师single/multi、已知C8竞争域、数据、λ100、τ.05、margin.1、初始化、随机seed、full-fit梯度和float64不变。唯一变化是Adam步长日程、步数上限及仅按fit总目标保留最佳迭代。E30的80步最后点保留为历史同目标参照，不覆盖旧模型或结果。

## 实现与参照复核

训练核心set_loss、triple_scores、Transform、load_fit、diagnose逐字复制E30；读取标签与teacher mask字节相同。独立枚举/有限差分检查损失及归一化共享A的累积梯度；NumPy重新读取旧A、复算W与原第80步总目标。原第一步上冲、末段下降不是bug证明，也不是收敛证书。

## 唯一优化方案与停机

两个数据集各single/multi一次，共4次，从A=0开始。Adam默认betas/eps、无weight decay；CPU8、seed20260911、batch1024全量梯度累积，最多1200次更新。

第1–20次更新lr从3e-5线性增加至3e-4；第21–200次保持3e-4；第201–1200次按余弦衰减至3e-6。保留整个轨迹中fit总目标最低的A/W；完全相同值选较早迭代。每步记录data loss、正则位移、总目标、梯度范数、下一步lr、耗时；每100步记录C8选中组合实际缓存hits/NDC、全H精确top3已知覆盖和接受率。额外保存最后迭代，便于区分最佳点和停机点。

训练阶段从第一次新fit前到第4次导出完毕计时，合计硬上限600秒；每轮检查共享deadline，单次进程由外层监控超时停止。预算耗尽时保存当时最佳点并将比较标为预算不完整，不追加训练。1200步是资源停机；末100步的相对最佳目标下降/画像变化是描述性稳定检查，不能声称非凸非光滑问题已全局收敛。没有学习率网格、第二次重启、漂移调参或按效用/开发指标选checkpoint。

## 缓存效用与阶段门

读取E28原真实L128/K10、fit20k×56三元组标签，两集合计224万逻辑标签，新标签0。先以NumPy独立核验4个新A/W和选中迭代目标，再对anchor、E30 single/multi、新single/multi的float32导出统一评分。

分别报告C8最佳得分组合的真实Recall、graph NDC、headroom/no-headroom增益与损害；全H精确top3只有落入已标注56组合时效用已知。未知组合保留unknown，完整fit Recall给出0..10命中最坏/最好界，不能用条件均值替代全量结果。逐query配对bootstrap区间只作描述。

“缓存明显改善”预定为同一种新cell在两个数据集均满足：C8实际Recall相对anchor≥+0.20pp、相对对应E30旧cell>0、graph NDC≤anchor×1.01；全H已知覆盖≥99.5%，且新画像全量Recall下界减anchor上界≥+0.20pp。single或multi任一通过才进入真实检索；两个都失败则在此停止。该资源门基于历史信息，不是泛化或统计显著性定理；单数据集局部收益仍保留。

若缓存门通过：两集GT10 hard与新single/multi共3方法，完整fit20k及cal/audit各1024，L128/相同HNSW3/原NSG，诊断reps0不报告QPS；每点2N+16次原NSG，总正常上限264864次，修复10000，总硬274864。顺序CPU15/实际线程1/OMP-BLAS-MKL1，无训练或重分析并发。至少同一种cell两集fit Recall≥+0.20pp、graph NDC≤+1%，cal/audit均正，才有完整Recall–QPS推进资格。若通过，需要在新正式查询前补充锁定最小同批性能矩阵与预算；未通过不测validation/held-out。

## 保护与交付

复核E30及其原保护manifest全量身份；原base、图、H、GT、query split、标签、模型、日志和报告保持不变。目录上限512MiB，free≥10GiB，RSS40GiB；仅使用历史fit，条件分支才读取开发query；本阶段不读取/hash held-out。

交付优化/实际标签收益图、完整CSV/XLSX、独立模型与最终验收、明确“优化得到改善”和“检索效用得到改善”的边界。按历史20→s-experiment→summary/spec/s-target同步，保留GT10既有成果与E30完整曲线。本次训练耗时不是QPS，未运行的新画像不推算端到端性能。
