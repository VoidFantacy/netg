# E24：固定 H 的 GT-topK 硬/软画像小型协议

2026-09-10。用户明确授权按阶段持续执行第一方向；本协议在任何新画像构建、cal搜索及validation数据读取之前锁定。独立目录保存源码、配置、输入身份、日志、逐query结果与停止记录。其余方向、旧大实验和C均不进入本队列。

## 1. 问题、固定项和输入身份

检验多个GT目标和软归属能否在相同画像数量及三个真实入口下提高NSG的Recall–QPS。原base、raw-IP、预处理、NSG、QGT seed20260828、WebVid H815/d512和Yandex H821/d200不变；不生成全H single/三入口训练标签，不训练Full、rank、MLP，不换H、不用vMF、不作HNSW拉伸。

fit为router_train原行[10000,30000)，cal为[0,1024)，audit为[1024,2048)。从原fvecs/ivecs逐项核对E23隔离输入；GT真实宽100，以行ID、形状、字节数及hash绑定。本轮只有fit参与画像构建，cal GT仅在搜索返回后评分和选择，audit GT仅在选定后报告。P0已核对原base/NSG/训练输入hash、raw hub与base行、唯一升序ID和固定seed；见[preflight](inputs/preflight.json)。原NSG是二进制，不根据扩展名解释。

历史使用：fit/cal/audit均为多次使用过的开发池，Fast30K还用过其中cal/audit query。validation前2000条已经被E22/E23及更早开发使用，绝非新鲜盲测。本轮仅在两数据集模型/选择均冻结后读取这2000条。held-out query/GT文件不打开、不hash、不重测；历史manifest中的元数据不等于访问样本。

## 2. 精确画像定义与有限候选

目标分数s(q,t,h)=unit(base[GT_t(q)])·unit(raw_hub[h])，沿用目标–hub cosine以隔离归属变化，不同时修改Yandex范数规则。硬归属取最高分，ties按升序真实ID取第一项；软归属在全部H上计算stable softmax((s-max(s))/T)，不截断。GT名次等权，每query的a(q,h)=mean_t b(q,t,h)，所有hub权重和为1。

画像p_h=unit(unit(raw_hub[h])+sum_q a(q,h)unit(q))，prior权重固定1。每数据集恰好8份：GT1硬（matched Fast20K）、GT10硬、GT1软×3温度、GT10软×3温度。两种软画像共用该数据集同一温度表。T尺度为fit全部GT1目标最高与次高hub cosine差的中位数，下限1e-4；倍率固定{0.25,1,4}。数值在cal之前已确定：

| 数据集 | T低 | T中 | T高 |
|---|---:|---:|---:|
| WebVid | 0.0040502846240997314 | 0.016201138496398926 | 0.0648045539855957 |
| Yandex-IP | 0.010893512517213821 | 0.043574050068855286 | 0.17429620027542114 |

数值：原builder的normalize、目标分数及GT1硬累加保持float32，batch4096，以恢复P0逐位身份。其余画像在相同float32单位向量和分数上，权重、softmax与加权query累加用float64，最终单位化后导出float32。另计算同分组float64的GT1硬数值控制，只报告相对恢复P0的误差（max abs<=2e-6），不作为可选候选、不额外搜索。零query贡献零方向但其权重仍入支持统计；零target按ties规则；零hub/最终和使用原normalize的1e-12保护；无query支持保留raw-hub方向。真实数据遇非finite即停止依赖阶段修复。禁止给每query更多总权重或增设prior网格。

按最多4096个目标评分批次处理，不驻留N×K×H×d张量。允许保存N×H归属权重以审计；float64累加可离线16线程。记录每hub质量sum(a)、sum(a²)、ESS=sum(a)²/sum(a²)、query侧熵/有效hub数、最大权重、hard计数、目标与hub范数、画像位移以及时间。全非零权重不等于有充分有效支持。

## 3. 阶段与不可更改的选择/停止规则

P1先复算GT1硬并要求与E23 matched P0逐位相同。再在fit前32条，L128、exact/HNSW两路，分别评估旧P0和恢复P0；返回ID、距离bits、入口、NDC均须相同，并与旧E23对应前32条输出回归。原kernel/count/plain逐query验收同时进行。恢复失败先保留记录、修实现，不运行cal；通过后构建其余候选。

P2：cal1024，L128，对8份画像各做exact3与HNSW3，共每数据集16点。每点一次整批warmup、一次独立plain wall、一次全量count；时间只作描述，不用于选温度。所有32点完整保存后，每软族按HNSW总hits降序、总graph NDC升序、较低温度决胜。主候选从GT10硬及两份软族赢家中按同一hits/NDC规则选择，再并列时优先硬、GT1软、GT10软，最后较低温度。

开发推进门为两数据集各自主候选HNSW总hits严格大于matched Fast20K（至少1个额外GT命中，即1024条上的0.009765625pp；这是探索进入门，绝非实质或显著性门）。若任一数据集未满足，状态STOP_NO_CROSS_DATASET_CAL_GAIN：保存完整cal比较与单点Recall–QPS图，完成冻结候选audit后收口，不读取validation、不扩温度。Fast回退只记录，不冒充新方法改善。

audit：每数据集仅报告GT1硬、GT10硬、cal选定的GT1软和GT10软，各exact/HNSW两路L128，8点；不计独立QPS，不重新选择，不据audit取消负点。两数据集所有候选和选择hash先冻结，audit只报告。只有上述cal门通过才进入P3。

P3：模型/选择/可执行文件冻结后，validation前2000条、L={64,128,256,400,800}；每点六方法：NSG固定入口、原Fast30K-3、matched Fast20K-3（GT1硬）、GT10硬、已选GT1软、已选GT10软，共60点。主候选是其中固定的一行，不多加重复方法。每数据集每画像跨五L保持同一W、H、serialized HNSW及query入口；L仅影响主图搜索。无论audit/validation正负均跑完这些预定点，之后本版本收口，不追加seed/计时/调参。

## 4. 路由、单线程和计时

matched画像固定一画像一真实ID，raw query→Micro-HNSW direct3→原search_new(mode=2)。M16/efConstruction200/ef10、seed20260828；三个互异真实ID升序消费，排序成本在端到端timer内。exact3用同一HNSW距离函数精确评分并按真实ID处理ties，只是画像分数参考，非搜索效用oracle。原Fast30K保留原seed100/heap顺序，输入差异另列；归因主对照是matched Fast20K。

正式查询及cal/audit：显式threads=1、OMP/OPENBLAS/MKL=1、OMP dynamic=false；taskset固定至CPU15（如不在当前affinity则在锁定配置选最大可用CPU），记录实际OpenMP team和/proc进程线程数均为1。一次一个被测方法，不并发编译、构建、训练、标签或其它性能进程。逐点原kernel16query验收，正式点一整批warmup、一次独立plain wall、全量count在timer外。plain timer包含raw query路由、三入口排序、原NSG和输出写入预分配内存；不含GT评分、NDC、hash、JSON、输入加载或微型建图。每数据集/L轮换方法顺序；没有cold-cache控制，单次wall不构成稳定加速证明。

P3 L128的六方法另各做一次route-only与graph-only整批warmup和独立wall，query路由/排序及原NSG成本分列，不能将它们相加冒充独立端到端wall；其余L这两项为null+reason。每次微型图构建/加载单列，成本不混入查询QPS。记录Recall@10、QPS、零命中、相对NSG及matched Fast的挽救/新增失败、route/graph/total NDC。

## 5. 冻结调用与资源上限

实际原NSG调用为计量单位；每point的前16query原kernel/count各一次共32。measured point另warm/plain/count共3N；diagnostic point另plain/count共2N。route-only不调用NSG，graph-only warm+wall额外2N。

| 阶段 | 固定最大真实调用 |
|---|---:|
| P1 两数据集×4点×(2×32+32) | 768 |
| P2 cal两数据集×16点×(3×1024+32) | 99,328 |
| P2 audit两数据集×8点×(2×1024+32) | 33,280 |
| P3 两数据集×30点×(3×2000+32) | 361,920 |
| P3 L128 route/graph分项：12点×2×2000 | 48,000 |
| 正常全部通过合计 | 543,296 |
| 仅身份/parity修复重试预留，禁止方法调参使用 | 8,192 |
| **全版本硬上限** | **551,488** |

合成fixture验收单独记账，不计真实数据调用，上限10,000，不生成训练标签。控制器在每job启动前按方法数和样本数预留完整调用，子进程核验自身上限；失败job按预留全额计入预算。恢复修正可用预留，超出即停止报告，不默认增加预算。

单个真实子进程最长1800秒，所有真实搜索子进程合计最长7200秒；RSS<=40GiB，新产物<=2GiB，/data剩余>=10GiB。触限保留partial/failed产物并收口。代码/身份/parity失败优先修复，但不得在修复名义下改变候选、选择规则或读取新split。

## 6. 交付与结论合同

全部cal/audit及（若进入）60点原值、逐query输出/GT独立重评分、配对Recall描述与固定PCG64 seed20260910的2000次query bootstrap95%区间、零命中迁移、完整Recall–QPS PNG/SVG、路由与图成本、画像构建/重复建图/实验过程耗时、停止状态和保护校验。区间仅描述历史query样本变化，未校正多重比较，不作确认性结论。

离线成本拆成既有exact GT、QGT、NSG（未新测用null+reason）、新画像、Micro-HNSW、准备/核对和本轮真实评估；从零成本不把旧GT/图算免费。新方法不依赖E22 single/E23 triple标签。相同L正值、NDC降低或单次wall微差不足以宣布整体性能GO。保持原raw-IP使Yandex范数代理问题仍未解决；单画像仍有单峰表达限制。

更新experiment_history详细卡及s-experiment索引，再同步summary、s-target和已实现接口对应的spec。旧文档快照及所有原资产保留。最终先总体结论，再给详细结果、成本与局限。
