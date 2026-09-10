# C stage 1 v1 — C0/C1/C2 protocol

本版依据本对话明确授权，C 为第一优先级。CPU-only；最多16线程；不开展 A+B、C3、C4、validation、held-out。旧源码、模型、图、GT 和历史产物全部保留。

## Identity and sample

WebVid-2.5M 与 official Yandex first-10M，原始 IP（内部距离为负 IP），原冻结 NSG R64。paired Fast 使用 QGT seed20260828 的既有815/821 hubs和 router_train 后20K `[10000,30000)` 的画像，M16/efConstruction200/efSearch10/seed20260828，顺序插入，不重新训练。

每数据集从 `drl_train`（router_train）前10K，用 numpy PCG64 seed20260909 permutation(10000) 的前2000项，不放回，保持抽样顺序。所有 C0、C1真实样本、smoke和C2均在这一名单内，不自动扩样本。它是历史开发训练池，不能称新鲜独立测试；与 paired prototype 20K fit 行不重叠。前128条仅用于 GT-free 成本校准；C1真实验收前16条；C2 smoke前4条；主诊断仍为全部2000条，无删行。只读 manifest 中的 validation/held-out 元数据，禁止打开这些 split 的向量和GT文件。

## C0 cost-only calibration and irreversible lock

校准只运行原 `search_new_traced` 的 Fast3，不打开任何GT，不保存或评分Recall。记录各query/L的完整 graph NDC和完成扩展数。K10、L64/128。

在看到任何C2质量前，以固定公式锁定：每L一个checkpoint，在完成 `max(1,floor(0.5*min_dataset median(expansions)))` 次完整邻接行后暂停；一个全局额外 graph-NDC cap `B=max(128,64*ceil(max_dataset_L P75(full native NDC)/128))`。分位数使用numpy默认linear。B即校准最大P75成本的一半向上取64倍数，且不低于128；不扫描多个checkpoint/B。`config.locked.json`保存数值，`protocol_lock.json`保存协议、配置与校准文件SHA和UTC。选择只依赖成本分布；不足以建立协议时停止，不扩大范围。

## Starting policy and candidates

原paired Fast3由**直接 top3 HNSW调用**取得，反转maxheap恢复rank顺序。候选由同一固定画像索引上独立top7调用的零基rank3、4、5、6取得。最多四个槽；初始入口和重复ID移除，不补位，不继续扫描H。直接top3与top7前三名的相等性记录，但起始策略始终保持直接top3。两个路由调用的实际NDC/wall分项记录；候选生成不是免费。HNSW导航本身允许访问其小索引，禁止全H在线动作扫描或exact全H候选排名。

候选仅依赖raw query与冻结画像，无GT，无suffix信息。checkpoint时尚未visited、未expanded且真实ID合法才有资格。已visited候选不再次计算距离或强行扩展。C2每query最多9个物理分支：continue + 四个natural insert + 四个force-expand；无资格槽映射continue并记录原因。每分支只注入一个候选，不联合注入四个。

## State and action semantics

独立版本state保存：有序retset的全部L+1槽及ID/distance/pending、num_ids、cursor、updated_pos、当前row/node/neighbor offset、visited与独立expanded、L/K、raw query与入口、base/graph/metric/native和新版kernel身份、已消费和剩余graph NDC、完成扩展数、有界GT-free历史计数。GT不进入状态/API。

checkpoint仅完整row后；在其前已自然结束的query不干预，各分支复制原终态，增量零。无资格和no-op仍进入全部2000条的无条件统计。自然结束包含scheduler无法再找到pending项的状态，不因要凑预算强行工作。

continue恢复原scheduler。natural(e)先消耗一次candidate `dis(e)`并标visited，按原pool bound和插入规则尝试插入，插入成功时将cursor rewind到`min(cursor,r)`，然后原调度继续；拒绝亦付费。force(e)采用同一插入尝试，但将e的pending清除，无论是否留在pool均扫描其邻接行一次，再回原scheduler；其邻居采用原visited/bound/插入/rewind规则。e记录为expanded，永不重复扩展。原scheduler cursor在注入后保留/rewind，不因强制row凭空前进一步。

所有branch从同一完整prefix深clone，各有独立DC和visited/retset；图/base只读共享。candidate距离和所有邻居距离均扣B，未使用的预算不转移给别的branch。若cap在row内耗尽，在下一次合法未visited节点的dis之前停止，不将未评分节点标visited；保存node/offset/updated_pos并返回当前retset topK。允许扫过padding/visited而不扣NDC；无可执行距离时可到达自然终止。不会把partial row改成整行原子扩展。B≥128，足以容纳至多65次距离的独立force row，但suffix仍可能截断。

结果是retset topK，不能换成global topK。逐branch保留prefix/suffix/total graph NDC、remaining、自然结束/cap停止、row offset、返回ID/距离和wall。共同cap不保证实际工作相等；不以same-L或NDC声称等成本或Pareto。

## C1 gate

无cap无注入：pause → clone和serialize/deserialize → resume，必须与未修改原kernel的topK ID、float distance逐位、NDC和扩展顺序一致。原kernel没有顺序输出，使用由冻结源码机械提取、只增加observer的独立reference记录扩展顺序，并先核对它与真正原kernel的ID/distance/NDC一致；不能仅与手写新实现互证。

覆盖同state repeated continue、交错branch独立性、plain/count/trace一致、query/DC与L身份绑定、入口前三位置语义、重复/已visited入口、非法入口安全拒绝（原kernel非法输入是未定义行为，不对其执行越界）、fallback、pool拒绝、tie、rewind、partial row、自然终止。保存所有失败与修订；可修复工程问题重复C1，不修改原search_new或C0质量协议。核心parity仍不能通过则停止，只报告工程失败，不进入C2。

## C2 execution, scoring and statistics

C1和独立kernel审阅全部通过才做4-query smoke；只验branch/schema/budget/parity，不据smoke质量调参。再运行全名单2000条×2L×2dataset，每dataset单个CPU进程顺序完成。GT在所有branch结束、原始结果持久化后由**单独离线评分脚本**打开train GT；原始结果runner无GT参数读取路径。每query/branch先保留topK ID和距离，再评分集合交集/10。

主oracle只从 `continue + 合法force(e)` 取最大Recall；natural为独立控制，不混入主oracle。Recall ties先continue，其次候选槽0→3；不按GT预测、不按NDC重选质量ties。该离线oracle是有限动作headroom，非可部署模型。另给natural oracle、每同槽force−natural和主force赢家对同候选natural的描述性机制增量（后者存在GT选择偏差），不得把不同赢家之差称纯机制。

主族仅四个dataset×L的无条件oracle−continue query配对Recall差。numpy PCG64 seed20260909，bootstrap20000次，单位为query，普通95%及Bonferroni族95%双侧区间（每项98.75%，分位0.00625/0.99375）。同query下所有actions一同重采样；不把branch/两L/smoke复跑当新样本。每点至少+0.005 Recall（+0.5pp）、校正区间lower>0、且实际NDC envelope内非零有效动作覆盖，四点全过才可记 `COMMON_CAP_HEADROOM_PASS`。它仅触发停止并向用户报告，**不自动运行C3**。bootstrap只量化固定样本协议下query变异，单个历史构建/开发池限制保留。

分项输出所有action均值、NDC min/p25/p50/p75/p90/p95/p99/max、逐query envelope和oracle成本；只在需相对NDC时用ratio-of-means并明示。覆盖：early_finished、no_eligible、各槽visited/no-op、eligible、executed、trajectory/retset变化、Recall严格提高，分母均为全query；oracle各动作选择比例也用全query。不得仅在survivor子集报告主结果。

clone/serialize/state bookkeeping与branch wall分项：plain独立DC计时重复与count/trace结果逐位核对；timer不含GT/hash/JSON。状态本身用于cap的计数无法去除，明确其实现开销。C2不运行正式整批QPS、不称轻量或性能通过。输出diagnostic wall、prefix、routing、clone和序列化时间及NDC，单线程诊断不是16线程方法QPS。

## Resource and stop contract

最多2000不同query/dataset；总native或branch执行上限200000（C0/C1/C2及重复包括在内），每stage wall≤2h，RSS≤32GiB，新artifact≤5GiB，CPU-only≤16线程；初版worker单线程、BLAS/OMP1，统计可CPU向量化但仍≤16。所有长命令由setsid运行，独立持久日志，前一分钟观察实际吞吐并记录ETA；若一分钟前完成则记录实际完成时间，不虚构估计。执行失败不覆盖已有输出，修订用新路径。

立即停止当前C：C1核心parity/branch/provenance不可靠；无条件oracle未达到上述实质门；收益只来自survivor过滤；需要GT、全H动作扫描、免费候选距离、多checkpoint、多步RL或事后修改B/候选/动作；资源上限到达。C2四点为同一冻结主族，全部完成后一次判gate；不按中途效果提前扩样本或调参。失败不扩模型、候选、预算救场。

## Artifact schema and delivery

`source_before/` 原源码/文档快照与dirty状态；`source_manifest.json`保护SHA；`inputs/<dataset>/`样本row_ids/queries、已验证输入SHA、config；`config.prelock.json`公式，`config.locked.json`数值，`protocol_lock.json`时间/SHA；`src/`独立实现、构建、C0、C1、C2和评分脚本；`bin/`构建身份；`logs/commands.jsonl`实际argv/环境/UTC/退出码，持久stdout和资源日志；`results/calibration*`成本、`results/c1*`parity原始结果和失败、`results/c2_smoke*`及`results/c2*`aligned query×L×branch原始输出；每query保存checkpoint序列化状态或可验证完整状态记录。统计在`results/analysis_v1/`保留原始评分、CI、gate和report；`reviews/`独立kernel、统计及文档审阅。缺项记null+reason，不填假结果。

最后按文档职责同步spec(API/状态/语义)、summary(已完成结果)、s-target(下一gate)、s-experiment/experiment_history(过程证据)。A+B仍设计未运行，未来唯一接口为deployed A+B在t=0供入口和固定shortlist，C在实际诱导状态上决策；不得复用静态u_L作为C标签。未来分别通过后须在最终micro A+B上重新cross-fit，再做{Fast,AB}×{off,policy-specific C}；只有预注册正交互才称协同。
