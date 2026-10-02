# E28：GT10 锚定的共享入口变换（搜索和训练前锁定）

研究问题：在固定 H、原始 query、一次 microHNSW top3、原 NSG 不变时，共享线性/小 MLP 是否改善真实 Recall–QPS？本轮是探索性方法比较；历史 cal/audit/validation 已被多轮使用，不构成新的独立泛化检验。held-out 禁止读取。

## 模型与共同目标

两数据集都取 E24 的 GT10 hard 单位原型 P 为锚点，保持真实 hub 顺序。模型输出 W=normalize(P+f(P))。linear：无偏置 d×d 矩阵，零初始化。MLP：d→64→d，隐藏 ReLU，有隐藏偏置，无输出偏置，输出层零初始化，隐藏层固定种子初始化。free 参考：每个 hub 独立 d 维残差，零初始化。原型原件直接用于 unchanged 对照。

每条 fit query 从 GT1 hard HNSW3 与 GT10 hard HNSW3 并集出发，以 GT10 精确分数递减补齐 8 个真实 hub；分数同分按真实 ID。枚举 56 个无序三元组，实际注入时按真实 ID 升序。L=128 原 NSG 给出原始 top10、命中掩码、图距离计数。相同 fit 行、图、L、顺序的 E23 缓存可以复用；必须检验查询/GT/hub 身份，并抽查缓存与原生 kernel 一致。没有全 H 单入口标注。

每条 query 的唯一教师三元组：先最大 GT10 hits，再最小 graph NDC，再最大 GT10 原型分数之和，最后真实 ID 字典序。它是 C8 内的教师，不是全 H oracle。所有训练行等权，不用验证结果筛行。训练概率为 P(S|q)=exp(sum_{h∈S} z_h)/Z3(q)，|S|=3，z_h=unit(q)·W_h/0.05，归一化遍历全部 H 的三元组。损失 mean(log Z3−sum_teacher z)+λ mean_h ||W_h−P_h||²。Z3 用三级 elementary-symmetric-polynomial 的稳定 log-prefix 计算。其 MAP 是全 H 精确 top3；HNSW 是近似实现。该分布是 diagonal k-DPP 特例，并非新概率模型；加性分数不能表达任意条件互补关系。

每族只有 λ∈{10,100}，共 2 数据集×3 族×2=12 个训练任务。CPU、固定种子 20260911、float64 损失、batch=1024、完整 fit20k 梯度累积、Adam lr=0.003、固定 80 epochs，最后 epoch 导出，不根据 cal 选 epoch；不作 seed/rank/width/temperature 扩网。模型导出 float32 单位向量；记录损失曲线、参数量、漂移、训练 wall 和导出成本。优化未收敛如实列为限制。

## 阶段与选择

1. fit20k 每集，仅 fit 标签训练。cal1024：6 候选和 GT10 hard，各测 L64/128 HNSW；每族按两 L 平均 Recall 最大选一个 λ，精确相同时取平均总 NDC 更小，再取 λ=100。三个候选都保留，无论输赢。选择冻结后才读取 audit/validation 结果。
2. audit1024：三族胜出配置与 GT10 hard，各 L64/128 HNSW，另 L128 exact3 诊断；不再调参。fit 前256行：相同4方法的 L128 HNSW 只作训练侧诊断。
3. validation2000：NSG、原 Fast30K、GT1 hard、GT10 hard、原 cal 冻结的 GT1 soft/GT10 soft、linear、MLP、free。全部 L∈{64,128,256,400,800}，每点 3 次独立完整 warm+plain wall，轮换方法顺序。原 soft 与 Fast 身份单列，不能更名为 matched hard。
4. 仅 validation L128 额外报告分离 route/graph wall（4 主方法），总 wall 仍独立测量。各方法整个原始查询→入口→NSG→结果流程计入 timer，GT/计数/I/O/索引加载构建在外。threads=1，OMP/BLAS/MKL=1，固定 CPU15，一次一个查询方法。训练/标注不得与正式计时并发。instrumented/plain/reference、重复结果逐位一致；另 Python 重算 hits/masks/Recall。

## 预算与停止规则

新版本独立预算：fit 逻辑标签 2,240,000；物理标签最多同数，另每集最多 256 次 parity（新/native/plain/reference/cache）预留，合计 512。cal 57,792；audit HNSW+exact 49,536；fit probe 4,224；validation 1,261,440 加组件 32,000，共计划最大 3,645,504 次原 NSG 调用。另 10,000 次只用于修复明确实现错误/核验，不用于试新方法。总硬上限 3,655,504，未用不自动转给新网格。纯路由不算 NSG 调用，但单独记录。每个二进制调用前生成准确 cap；失败部分调用也记账。目录上限 2 GiB，数据盘空闲不足 10 GiB 时停止产生大文件。

非有限值、重复入口、GT 提前进入计时、身份不符、线程/计数/parity 不符立即停止相应阶段并保留失败结果；修复需记录修订且不得通过验证结果改变方法。

## 判断与产物

主要结论来自 validation 同机完整 Recall–QPS 前沿，画全 L 点及三次 wall 范围，另给共同召回区间的 log-QPS 线性插值并明确为插值。逐 query 配对 bootstrap (2000 draws,seed20260911) 给同 L Recall 差区间，不将其当作同 Recall 加速证据。只有当共享变换在两数据集共同召回区间至少两个预先指定点（0.90/0.95/0.98 中实际共同覆盖者）中位 QPS 提升 ≥3%，三次比值均>1，且无明显前沿退化时，才称本地双集性能 GO；否则保留局部信号或 NO_GO。无跨机器/新 held-out/论文充分性宣称。

产物：可追溯源/输入/二进制清单、候选/原始标签/缓存命中、训练/选择冻结、原始结果/完整调用账、独立核验、PNG/SVG图、CSV/XLSX 图表数据、详细中文 research/report、E28 历史卡与 root 文档同步。所有历史资产保持不变。
