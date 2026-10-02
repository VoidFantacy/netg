# E61：实际遗漏GT10成员驱动的全fit画像重构

2026-09-13，在E60双集0/40支持门后建立独立方法版本。目标是让有真实遗漏信号的完整P-fit20K参与构造，检验局部随机画像行动作覆盖不足是否能被低自由度、全池聚合改善。没有RL成功预设，不扩大E53局部方向/步数。

## 构造与对照（新查询前固定）

每数据集保持当前原P（WebVid GT10-soft-t1，Yandex GT10-hard），同H815/821、raw hubs、原NSG/base/GT/raw-IP、Micro-HNSW M16/efConstruction200/efSearch10/seed20260828、三个真实ID升序。所有新模型仍静态画像→普通HNSW→原NSG，无在线网络或额外搜索。

以E33完整fit20K冻结基线真实top10返回，识别exact GT10各成员是否未命中。逐query遗漏数m_q，原每rank raw-hub hard/soft归属 b_qr 保持。A0=mean_10 b_qr；若m_q>0，Amiss=mean_{遗漏rank} b_qr，否则Amiss=A0。唯一新强度lambda=0.5，A=(1-lambda)A0+lambda Amiss，每query总质量严格1。按原 unit(raw_hub)+Aᵀunit(query) 聚合、L2单位化导出float32 W。每query没有hardness额外倍乘，也没有signed utility或自由slot映射。

三固定模型：lambda0原P、missing_lambda05、sham_lambda05。sham对每query用固定RNG seed20260913给10个rank生成随机顺序，取前m_q个；保留该query遗漏数量和总质量，但移除“究竟遗漏哪些目标”的信息。不根据GT身份/查询响应选择seed，零遗漏和全遗漏查询两个模型按定义相同。sham仍使用query难度（m_q），不是无监督随机图；不保持真实遗漏rank的全局边际频次。它是可证伪机制对照，不参与部署选型。

先重建原A0，要求与E24 assignment SHA完全相同；按原算法重建P，检查float32 bytes。lambda0直接复制原P字节，所有新画像之前先完成原P复原门。若不一致，保留失败并明确修正数值实现；不得带着不匹配起点评价。保存真实/随机遗漏rank mask、m_q、每query质量、hub质量/ESS/方向变化、画像、assignment digest和源身份。

## 标签复用、数据与区别

E33 `results/<dataset>/baseline.npz`的20000行是本轮监督来源，必须核对其config、实际source rows、P/完整微型图、H映射、原NSG/metric/L128/K10/入口次序，逐条独立集合评分。它在E33曾完整回归E32；本轮将原生重新route完整fit+开发池，与基线全量入口/routeNDC比较，并用64固定行三路原kernel parity验证当前实现。身份不一致就停止复用，不能用旧不同P标签冒充当前遗漏。

fit为E24 router_train10000:30000，包含旧E37 train/monitor；E33本身也训练/监控过完整20K。cal router_train0:1024、audit1024:2048均历史使用，且E60刚在二者做过诊断。它们不是新盲集。基线开发输出可在query/GT/图及原生全路由恢复后复用E60原锚点。E34最终validation2000不作为训练/选型或本阶段输入，完整validation与held-out均不打开。

已由history04/11/22回查源码和原产物：E08是全H单入口赢家硬分组；E09是top32单入口Recall/NDC的signed advantage与hardness残差，WebVid有微弱正值，未证跨数据或端到端优势；E22主要学习自由slot→hub映射；E61只调整原GT10成员在同query总质量内的正权归属，监督来自实际原三入口遗漏成员。它属于现有画像聚合改进，不声称方法新颖性或无偏NSG效用教师。若效果为空/损伤转移，保留原因，不换名重启旧路线。

## 有界真实评价与选择

候选完全冻结后，每数据集原P和两个新模型，完整fit20K+cal1024+audit1024只评L128。全部实际HNSW路由，只有与该query固定P的完整三入口不同才新增原NSG；routeNDC总是实际重算。保留完整aligned raw/GT10 mask/入口/距离bits/NDC、缓存变化patch、物理图和逐querygain/loss/救回/新失败。

唯一可选新方法是missing_lambda05，sham只解释。按cal净命中>0、零命中失败数不增加、mean totalNDC≤原P的101%决定冻结候选是否入下一阶段；不调lambda/随机seed/归属公式。audit只报告这一固定选择的迁移和损伤，不回选或训练。fit/cal/audit增损和missing−sham分开；一数据集通过不自动宣称双集方法进步。若都不通过，不做同公式强度网格，以对照证据决定新设计。

本阶段无正式QPS：开发同L质量与计数不能替代今日最终同机五L五轮纯wall。晚间至少最后一小时保留给冻结候选和NSG/Fast/FastGT/匹配GT10起点、失败率（GT10零命中）及独立验收。原默认不在本阶段替换。

## 成本、停止与验收

新GT生成0、梯度更新0。复用历史fit标签40000及开发基线4096行，历史生成成本不得写成免费构建。每集3次普通小图build、3×22048真实HNSW路由；每图固定64行三路parity（32fit+16cal+16audit），额外384 HNSW/576 NSG。合计每集HNSW66528、build3；最坏2×22048+576=44672新NSG，完整预留45000/集，总90000，失败预留不释放、不自动重试。

原生CPU15显式threads1、OMP/OpenBLAS/MKL/NumExpr/BLIS1，每次只有一个native进程；离线聚合及分析CPU8单线程，与native不并发。记录身份核验、缓存处理、target assignment、聚合、构图、route、新增NSG、评分/序列化费用，不用NDC或缓存比例估算QPS。只复制小图/稀疏输出，阶段≤192MiB、free≥7GiB、RSS≤32GiB；每集原生≤600s，09:50后不启动、10:00停止新查询、10:15前安全交接，无遗留进程。上游E60/昨日冻结不变，根文档变更前后分别保存快照。

验收涵盖原A0/P恢复、40000缓存GT集合评分、每query质量1与遗漏数控制、全部模型前向/物理图身份、132288输出集合评分、384三路parity行、缓存合法键与精确复用、cal选择冻结及所有损伤/代价。未测性能或泛化明确留空。当前为预锁协议，执行状态由本目录state/report维护。
