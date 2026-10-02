# E53：保留RL方向、用真实反馈接受确定步长

2026-09-12，用户要求持续至22:00，大胆假设、小心证明，并最终比较最佳方法与NSG/Fast/FastGT的QPS/召回/失败率。E51固定状态控制表明：放大原Adam方向能救回WebVid9/12、Yandex4/4空更新机会，但最大半径又可产生损伤。本轮假设是保留RL方向、用原真实目标接受或拒绝预定步长，能改善“高斯候选有响应、确定均值不跨边界”的转化。E52直接候选择优提交为独立非RL强对照；本轮不能把贪心结果包装成RL优势。

## 方法差异预锁

两个原dataset×两seed20260921/22，共4run；原RL P/B/scale/H×16、σ.3、200步、每步8个独立Gaussian候选、GT无关hub日程、原NSG/IP/L128/K10/三个真实入口/普通HNSW builder保持。每步八候选全部真实build/route完整train4096、精确补测三入口变化，得到原J奖励；原8独立LOO REINFORCE梯度和原Adam状态/梯度clip/局部偏差修正/余弦学习率计算保持。

先计算原Adam临时系数点z_adam（含原±2 clip），方向d=z_adam−当前系数。r为本步八个σ.3扰动系数L2范数中位数，GT无关。构造当前系数+{r/4,r/2,r}×d/||d||，各再clip±2；d=0则都为不动。新增三点D25/D50/D100全部真实普通build/route4096并按当前C完整入口键补测NSG，得到原J。只在这三个确定点+不动中选原J最大者，平分先不动再小半径；原八Gaussian候选只估计RL方向，不能直接提交其中某个候选。原Adam m/v和局部计数每步推进，即使不动也保留该次梯度统计；实际均值系数更新为被接受的确定点。接受后重新普通build当前W，拓扑SHA必须恢复该已测点，不额外route一遍。

这是一种RL梯度指导、真实确定反馈接受步长的优化控制，不声称新的理论算法或收敛保证；Gaussian平滑目标梯度与确定J的接受目标不同。每步确定J不减，但净命中和独立query可有损伤，全部保留。原E47/52训练状态分岔后必须重新计算反馈，不能用旧标签；原梯度/方向/目标各分量独立重放以检查实现。

## 监控、成本与保护

原完整train4096每步训练，monitor1024仅step0/20/…/200固定查询和原非零feasible checkpoint选择（graph NDC≤+1%、monitor U最大、平分较早步）；无cal/audit/原validation/held-out训练反馈，原5120输入文件物理含monitor记录，0新GT。完整checkpoint存W/系数/m/v/局部计数/接受数以及train4096+monitor1024返回，selected/last静态W/普通HNSW各64query三路parity。

每run build=1+200×(8+3+1)+2=2403；HNSW=200×11×4096+4096+11264+256=9026816。四run总9612build/36107264 HNSW，固定NSG62976+真实Gaussian/确定点变化query；每run完整预留150000，总硬限600000，失败不释放/不自动重试。native每dataset cap300000/HNSW19000000。记录8800个逻辑训练图状态、800 RL梯度/接受决策、实际接受和不动分开，不把候选或不动都叫成功更新。

CPU15实际进程/OMP/BLAS/MKL1、dataset和seed串行；每dataset≤2400s、RSS<32GiB，artifact≤384MiB、free≥8GiB。启动前根据E52同四run总时长×(11/8)×1.5+300秒保守估计，并须预计21:10前完成；21:15后不启动新训练、21:35硬停、21:40停止新查询、22:00收口。分析CPU8，不与原生性能工作重叠。保护原E37–E52/source/native/P/B/H/数据/GT/图/日志，独立目录，前后SHA核验。

## 接续与验收

800次原RL四分量梯度/Adam临时点、2400确定步长/clip画像、6400Gaussian候选、完整cache hash/变化patch独立集合评分、原J择优/no-op/tie、每步J非减与逐query命中差守恒、44完整checkpoint/8导出/512三路parity核验。对E52贪心与E47原RL保留同样seed/日程下实际训练/监控结果，不能拿状态分岔后的频次对比当固定状态因果消融。

至少每dataset一个可行selected monitor正Recall才称双集局部信号，不等于正式GO。最终所有候选冻结后按既有独立cal规则择优，与用户指定NSG/Fast/FastGT作完整单线程同机Recall–QPS和失败率比较；不用最终audit/性能再换seed或回流训练。原门失败和局部正值分别保留，若默认GT10仍更好，直接说明。当前仅协议准备，尚未实现、冻结或训练。
