# 13｜固定 H 的 GT1/GT10 × 硬/软画像

2026-09-10，E24。状态`EXPLORATORY_LOCAL_FRONTIER_SIGNAL_NO_FORMAL_GO`。用户在四问题调研和详细交接后明确授权第一方向逐阶段执行；P0输入/协议、P1恢复、P2 cal/audit、P3 validation均完成，本版本收口。原只读调研和文档交接保留未执行原件身份，实际继任实验记于本卡。

## 问题、方法与固定项

检验GT1归属丢失多目标信息及硬分组支持不足，能否通过闭式画像在相同H、相同三个入口、相同路由模型规模下改善真实NSG Recall–QPS。与旧GT1 basin内增加modes、多seed/view、single获胜者centroid和E23真实三入口排序不同；本次只改变GT目标归属。

原WebVid2.5M/official Yandex first10M raw-IP、NSG及QGT seed20260828 H815/821固定。fit为router_train[10000,30000)，cal[0,1024)，audit[1024,2048)；GT100宽度/字节数/行身份与原文件核对。target–hub仍为cosine，query方向累加，每query总质量1，GT1/GT10等权，raw-hub prior1。硬归属ties按真实ID，softmax在全部H稳定计算；最终一单位画像对应一个真实ID。

每数据集8份：GT1硬、GT10硬、GT1/GT10软各3温度。T为fit GT1最高/次高hub cosine差中位数×0.25/1/4；WebVid约0.00405/0.01620/0.06480，Yandex0.01089/0.04357/0.17430。GT1硬保留原float32累加，其他加权累加float64后导出float32；不重跑single/triple标签、不训练Full/rank、不改H、vMF、MLP或HNSW几何。

## 恢复、开发选择和数据访问

GT1硬与E23 paired P0逐位相同。fit32旧/新P0×exact/HNSW的ID、距离bits、入口、命中/mask及NDC全部一致，也与E23历史相同行输出回归通过。两数据集全部8份画像先冻结，再在cal1024 L128评估exact/HNSW各一份。模型按HNSW总hits、graph NDC和冻结ties选择，QPS/exact结果不用于选参。

WebVid cal选GT10软T0.0162011（+0.8203pp），Yandex选GT10硬（+0.0488pp）；均通过至少1个额外总命中的弱探索进入门。audit分别+0.5859/−0.0781pp，只报告，不换模型。另每软族保留其cal赢家：WebVid GT1软T0.0648046，Yandex两软族均T0.0108935。两软族在WebVid最终温度不同，因此是校准后画像族比较，不是同T的纯交互项估计。

双数据集选择/画像/binary冻结后，历史validation前2K、L64/128/256/400/800、NSG/Fast30K/Fast20K/GT10硬/GT1软/GT10软共60点全部执行。fit/cal/audit及validation均有历史使用，不能称新盲测；本轮held-out文件未打开。

## 五点主结果及消融

下表相对同批matched Fast20K-3；每点单线程、独立plain wall一次。

| 数据集 / cal冻结主候选 | L | ΔRecall pp | ΔQPS % |
|---|---:|---:|---:|
| WebVid / GT10软 | 64 | +0.525 | +3.51 |
| WebVid / GT10软 | 128 | -0.070 | +1.55 |
| WebVid / GT10软 | 256 | +0.115 | +3.58 |
| WebVid / GT10软 | 400 | +0.005 | -0.75 |
| WebVid / GT10软 | 800 | +0.040 | +2.18 |
| Yandex-IP / GT10硬 | 64 | +0.120 | -0.07 |
| Yandex-IP / GT10硬 | 128 | +0.335 | +2.56 |
| Yandex-IP / GT10硬 | 256 | +0.035 | +0.56 |
| Yandex-IP / GT10硬 | 400 | +0.080 | -0.01 |
| Yandex-IP / GT10硬 | 800 | +0.060 | +0.80 |

主候选两数据集各3/5点同时提高Recall与QPS；各自五新点均位于与Fast20K五点合并的观测非支配集合，另外点含质量/速度交换，不能称整条新曲线支配旧曲线。9/10项主候选Recall差的未校正95%配对bootstrap跨0，Yandex L128下界也仅约+0.010pp。

GT10硬在Yandex五L Recall均小幅正值，但在WebVid L128/256/400为−0.085/−0.115/−0.110pp；不是统一多目标修复。WebVid GT1软L64为+0.740pp，L800为−0.050pp；软归属不保证更好。GT10软/硬互有高低，不能按validation把主选择切成更好看的消融。

L128零命中，WebVid Fast20K→主候选54→51（挽救15/新增失败12），Yandex38→32（10/4）。各自83.75%/63.65%的validation query更换三入口，入口跨L一致。原Fast30K独立列出：WebVid主候选相对原Fast30K的+0.200pp包含Fast20K输入差异；Yandex主候选L128 QPS仍略低于原Fast30K。

## 支持、近似检索与计时解释

WebVid GT1硬有802/815个画像有query质量，中位ESS16；GT10硬覆盖全部、ESS67.36，主候选GT10软ESS132.28。支持变充分未保住validation L128收益；高T还可能使query权重近乎广泛摊薄。Yandex GT10硬ESS22→60.08。

audit主候选exact3−HNSW3最终Recall为WebVid+0.146pp、Yandex−0.020pp，ANN top3集合覆盖约94.24%/97.85%。精确画像检索不是finite-L入口效用oracle。L128 Fast20K route-only约7.166/4.535μs/query，主候选6.521/4.391μs；该量级仅约独立端到端wall的1%，分项wall不能相加作总wall。Yandex主候选graph NDC微增而QPS较高，不能把全部速度差归为更少距离计算。

## 成本、验收和收口

真实调用543296（恢复768、cal99328、audit33280、validation含分项409920），正常预算完全执行，修复预留8192未用；另1500次合成fixture调用。训练标注0，不依赖E22全H single或E23 triple训练标签。

输入核对/准备22.41s；两数据集GT1硬恢复核心0.447s；其余候选构建阶段合计15.30s。搜索子进程恢复16.63s、cal70.52s、audit34.26s、validation484.65s，含加载/建图/验收/计数/I/O，不能换算查询QPS。已有exact GT、QGT和NSG从零成本未新测，null+reason。观测峰值RSS约9.920GiB，全部查询进程实际1线程、CPU15。

全部116点、169408个输出独立GT10重评分通过；NSG/Fast30K/Fast20K三基线30点60000输出与E23逐位相同。五L图/入口一致，选择独立重算通过；63个绑定上游文件和全部冻结画像/选择/二进制已核验。原资产和修改前文档保留。

局部前沿信号不升级为正式GO：一个构建、validation2K、单次wall、历史使用及cosine丢失raw-IP范数仍是限制。此版本结束，不扩温度/GT数、不看held-out、不恢复旧大实验/C。下一研究建议为固定H的真实finite-L效用分组2A，保留本轮冻结画像；不是已自动启动的新阶段。

## 原始证据

- [完整报告](../entry_method_exploration/20260910_gt_topk_profiles_v1/report.md)、[协议](../entry_method_exploration/20260910_gt_topk_profiles_v1/protocol.md)、[冻结配置](../entry_method_exploration/20260910_gt_topk_profiles_v1/config.locked.json)、[状态](../entry_method_exploration/20260910_gt_topk_profiles_v1/state.json)、[实际命令](../entry_method_exploration/20260910_gt_topk_profiles_v1/commands.md)。
- [全部原值](../entry_method_exploration/20260910_gt_topk_profiles_v1/results/tables.md)、[指标CSV](../entry_method_exploration/20260910_gt_topk_profiles_v1/results/metrics.csv)、[配对变化](../entry_method_exploration/20260910_gt_topk_profiles_v1/results/comparisons.csv)、[Recall–QPS](../entry_method_exploration/20260910_gt_topk_profiles_v1/figures/recall_qps.svg)、[差值图](../entry_method_exploration/20260910_gt_topk_profiles_v1/figures/deltas.svg)。
- [近似检索](../entry_method_exploration/20260910_gt_topk_profiles_v1/results/ann_diagnostics.csv)、[支持统计](../entry_method_exploration/20260910_gt_topk_profiles_v1/results/profile_support.csv)、[前沿实测点](../entry_method_exploration/20260910_gt_topk_profiles_v1/results/frontier_points.csv)、[明确标记的插值](../entry_method_exploration/20260910_gt_topk_profiles_v1/results/frontier_interpolation.csv)、[成本账](../entry_method_exploration/20260910_gt_topk_profiles_v1/results/costs.json)。
- [输入](../entry_method_exploration/20260910_gt_topk_profiles_v1/inputs/preflight.json)、[恢复](../entry_method_exploration/20260910_gt_topk_profiles_v1/reviews/recovery_gate.json)、[cal门](../entry_method_exploration/20260910_gt_topk_profiles_v1/reviews/cal_gate.json)、[validation前冻结](../entry_method_exploration/20260910_gt_topk_profiles_v1/models/frozen_before_validation.json)、[输出核验](../entry_method_exploration/20260910_gt_topk_profiles_v1/reviews/result_verification.json)、[保护与选择审计](../entry_method_exploration/20260910_gt_topk_profiles_v1/reviews/immutable_integrity.json)。
