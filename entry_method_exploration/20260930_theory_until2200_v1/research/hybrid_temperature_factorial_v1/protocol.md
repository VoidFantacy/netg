# 固定2048精确标签：温度与目标替换的最小因素检查

2026-09-30，读取新候选性能前冻结。record143双集方向诊断通过；本阶段检验方向改善能否传到真实路由和主搜索，以及Web低成本冷启动能否去除原20K温度依赖。不是继续调E125教师L，也不把统计收缩称新算法。

训练仅原fit20K，H815/821、QGT5K选择、prior1、十目标总质量1、原底图、搜索及路由规则不变。精确标签只用预定seed0的2048行（PCG64 2026093002+dataset_index），与前阶段相同，不根据16种子结果选择。训练程序只能读取这2048精确目标的独立文件；完整20K精确画像只作冻结后的几何参照，不参与候选计算。

Web固定5方法：原GT10-soft-t1、原ApproxTarget10、HybridFixedTemperature（2048精确归属替换近似归属，原温度）、ApproxPilotTemperature（全部近似归属，同2048精确GT1估计温度）、HybridPilotTemperature（同温度且2048精确替换）。温度严格沿原GT1目标对H的前二余弦差中位数公式，不选择与旧温度最接近的值。Y-hard固定3方法：原GT10-hard、原ApproxTarget10、HybridFixedTemperature；hard无温度，不制造重复方法。共4新画像/小图，原两个方法/集直接复用。

所有画像及图冻结后，评价E105已曝光4096query/集及其原GT；先验证与训练query逐字节无交叠。该来源是开发诊断，不称新盲测或选择外确认。真实K1/K100，固定Web L1000/1250，Y L128/256；所有方法在相同点运行，绝不选L/seed/温度。全query预热1轮、完整wall3轮、count1轮；固定轮换方法顺序。CPU15实际单线程，OMP/BLAS/MKL均1，每次只运行一个方法，无并发训练/标签作业。主核仍为已核验span+batch4，路由、入口映射/排序、NSG和输出写入内存均纳入wall；加载/GT评分/count/磁盘外置。

报告每点真实Recall/QPS三轮、配对query增损、相对默认和旧Approx的差异、95%描述bootstrap区间（固定seed2026093004+dataset_index*100+K，20000次）、实际入口集合/顺序变化及输出变化。Web因素效应用四个非默认方法做配对交互差，不因主效应或区间挑选一种候选。所有区间只描述已曝光开发池，不作多候选确认性显著检验。

主要低成本候选预定为Web HybridPilotTemperature、Y HybridFixedTemperature；FixedTemperature和ApproxPilotTemperature负责区分因素。结果无论正负，先检查warm/plain/count、原默认/Approx全数组恢复、链接E99、返回合法性/GT计分、输入与模型身份、实际单线程/完整费用，再解释。方向改善而Recall不改善不能当作实验错误，也不能未经核验就否定；不调整参数补过。当前0新增GT搜索，只使用缓存模拟2048标签方案，故完整冷启动成本尚未证明，不能按2048/20000线性缩放旧wall充作实测。

预算≤330000新NSG、≤327680 ANN，16方法点/48轮wall，4新画像/图；native总wall≤1800秒，输出≤150MiB、可用磁盘≥6GiB，最迟21:30停止计算。评价结束后先审计和文档，再决定下一项理论工作。无默认替换、无新源确认或后台自动队列。
