# E64 今日固定候选的扩大历史开发复核

2026-09-13会话2，E63原cal失败保留。真实zero-mass的fit净+32/+120而cal净−1/−2；随机query控制fit负却cal正，稀疏响应和选型稳定性仍不确定。此处冻结现有端点并扩大开发样本，测试方向是否稳定，不改变画像、图、强度、seed，不将旧失败改判成原版本通过。

## 输入与固定矩阵

每集只读router_train[2048:10000]全部7952行，来源由原verified_sources的query/GT SHA和E61完整22048行逐字回归核验。与原P-fit[10000:30000]及今日cal/audit[0:2048]在同namespace互斥。它们曾被Fast30K和早期研究使用，不能由余行元数据称项目盲集。全部7952为辅助选择训练；前后两半3976按原row顺序锁定，不选择子群。没有E34最终validation/held-out输入或反馈。无新GT/训练更新。

固定7模型/集顺序：baseline、E61_missing、E62_score、E62_topology、E63_zero_mass、E61_sham、E63_sham。前四新端点为可选新候选，两个sham仅控制。原base/raw-IP/GT/NSG/H815/821、ef10/top3/升序真实ID不变，交叉态必须加载已存物理图，评分W重建不可替代。全部候选W/graph/mapping在任何本阶段query前冻结。

## 开发规则（所有新反馈前固定）

每新候选相对baseline同时满足：7952净命中>0、两半净命中各≥0、总体zero-hit失败数不增、mean totalNDC≤+1%。达标者按总净命中、较少失败、较低totalNDC、固定顺序选择best_all；无达标则baseline。best_new在四个真实新端点中按同排序选一，用于诚实展示，即使未过门；sham永不参加推荐。保留全部7模型和两半原始值、相对原cal/audit的方向，不能按辅助结果新增参数或挑子集。该门只决定开发候选，不是最终方法GO。

## 实测与预算

复制E34同SHA无hook evaluator，diagnostic timing_repeats=0，每模型完整plain+count7952和16条原kernel parity，GT在所有raw后打开。每集7×(2×7952+16)=111440 NSG；双集222880，硬预算230000、失败完整预留、不自动重试。HNSW查询222656（原wrapper16/点不路由），14源物理图加载/复制、plain/count共28加载，0新构图/梯度/GT/QPS。保存全部aligned ids/distances/entries/masks/route和graphNDC、row namespace、序列化图SHA。

严格串行CPU15、实际native进程/OMP/BLAS/MKL/NUMEXPR/BLIS1，控制器CPU8轻量监控，无其它训练/评分/性能测试并发；两native工具session实际exit后独立重评分。每集600秒，10:45后不启动；10:55停止查询，11:14:29安全交接。free≥7GiB、本阶段≤160MiB、RSS≤32GiB。根文档source_before、原候选与所有E60–E63封存保护。

后续若时间足够，可独立版本固定本次best_new和全部基线，在预定历史开发子集source[2048:4096]做五L五轮完整wall。该测速仍是已暴露开发数据，不替代晚间冻结模型后的E34最终对照；所有方法必须同批，不能拼旧QPS。此处仅预留计划，尚未测量。
