# E68 冻结画像的完整分数排序诊断（前瞻分析协议）

2026-09-13，会话3。在E67双集原生工具实际terminal退出、独立评分通过后才开始数值分析。本阶段只读E66已有P/W/mapping、历史fit20K/aux7952向量及其实际入口/命中/七slot结果，无HNSW/NSG、无新GT、无画像/图/参数更新、无新QPS。E66/E67失败门和曲线保持，不模拟未测NSG反事实收益。

## 有限问题与方法

E66重复三份P的同容量控制在两集完整fit/aux均退化，但其完整内积评分函数与P相同。新增mode同时改变评分向量和普通图，不能把全部差值唯一归因某个因素。先核对原P/duplicate/mode的实际三hub与完整画像分数排序参照的一致性，补足后续是否研究物理slot近似误差的证据。

每query按raw q和已冻结float32 W的float64值作完整内积。原P对H个真实hub评分；duplicate逐字重复P，完整hub分数与原P相同，直接alias该参照；mode对3H全部slot评分，以每hub最大slot分数聚合，真实hub分数降序、平局按升序真实ID取前三。它是完整画像分数排序，不是GT近邻、不是真实NSG效用oracle或其上界，也不是本轮可部署方法。实际query/GT10命中只从E66既有返回记录读取。

保存逐query原P/新mode完整分数top3hub、实际3hub的重合0..3、相对最优三画像分数和的regret、近tie标志；七slot中独立真实hub数量从原trace统计，不能当visited/expanded的数量。近tie规则固定：第3/4个真实hub分数差<=1e-5*max(1,||raw q||)。全部统计及排除near-tie统计并列；float64参照不声称原SIMD逐位等价。每512行块首条的原P排名另用Python标量完整内积复核，非near-tie才断言同序；每137行核对七slot的原生距离在atol/rtol2e-5内。

三个方法完整fit/aux报告exact三hub集合一致率、平均重合、画像分数regret；按实际是否选中完整排名前三、以及原baseline一致/候选不一致，连接已观测的GT10净命中、失败救回/新增。分组均事后、相关性，不能说精确路由会获得这些增益或以此训练新在线规则。mode与P完整排序的差异单列；不从排序一致率推断检索质量或QPS。

## 角色、预算、保护与接续

两集合计55904源query，P和mode共111808次完整画像分数参照计算，duplicate另55904逻辑alias。fit含原train/monitor；aux7952历史暴露且E64/E66用于辅助选型，本轮诊断也不称盲测。只用E66已验证的命中记录，不打开新的GT文件；E34最终反馈和held-out不进入。原E66/E67源/输入/结果/图字节保持。

只在E67全部原生任务退出后CPU15、OMP/OpenBLAS/MKL/NumExpr/BLIS1串行执行，最长600秒，12:05前停止本阶段数值工作，12:13:18前交接。阶段<=16MiB，free>=7GiB；只保存分数摘要/排名/CSV/NPZ，不保存巨型全分数矩阵、不复制大输入。先保留root source_before及冻结源/输入清单，结束后保留manifest和独立标量/距离/恒等核验，更新详细历史/索引/summary/s-target/spec分析artifact合同。

若重复P的完整排序相同而近似选点一致率明显变差，支持“物理索引/近似路由造成差异”的有限事实；终止位置、候选槽占用还是具体拓扑未单独归因。可据此为下一会话准备单个ef10→ef30的multiplicity控制或实际精确三入口NSG诊断，但这些都须另建前瞻协议、保留duplicate/原P控制和完整在线费用。不得自动扫多个ef/seed/模式数，也不回写E66门；本协议不执行任何新候选。
