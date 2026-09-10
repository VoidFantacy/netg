# 12｜真实三入口收益排序：完整W与rank8探索

2026-09-10，E23。[完整报告](../entry_method_exploration/20260910_three_entry_rank_v1/report.md)、[协议](../entry_method_exploration/20260910_three_entry_rank_v1/protocol.md)、[状态](../entry_method_exploration/20260910_three_entry_rank_v1/state.json)。状态`EXPLORATORY_SMALL_RECALL_SIGNAL_NO_CLEAR_QPS_GAIN`：本轮已完成，有小幅Recall正信号，未形成明确整体QPS优势。用户在E22后要求匹配Fast三个入口、复核低秩梯度方法；完成论文研究后另行授权“推进一下这个方案试试”。

## 机制与输入

本版本固定一向量对应一真实hub，使用原kernel实测三入口条件收益构造排序目标，Fast先验二次锚定，比较自由完整W与同目标rank8；不沿用E22自由多对一映射。训练候选可由旧single列提议，但奖励全部重新测量真实三入口搜索。

原raw-IP、原冻结NSG、K10，seed20260828，WebVid H815/d512、Yandex H821/d200。复用E22隔离的fit20K、cal1024、audit1024；paired Fast画像仅由相同fit20K构建。fit每query前三个context分别保留Fast top3中的两个，第四个使用top3外两个入口；每context六个第三入口，由原top3、几何排序、全H single效用及随机项提出。三入口按真实ID升序后调用原kernel，相同有序三元组缓存复用。在线无固定anchor，无C8候选上限。

W=P0+τD；τ为fit Fast top1–top8中位差。Full自由D，rank8为(VZ)ᵀ且以共同fit初始梯度的右奇异方向初始化V、Z=0。固定pairwise logistic、query内归一化真实联合hit差权重、λ||D||²/(2H)，三个λ={0.1,1,10}，同float64 LBFGS；不加bias、归一化W、每步QR或hard fit单调验收。导出float32 W，mapping始终固定真实hub。

## 实际执行、选择与验证

两个数据集各20K fit×24个逻辑组合，缓存后各44万实际搜索。标注阶段不含加载的wall约17.51/23.97秒，整个子进程约22.71/36.18秒；它们是16线程离线标注时间，不是单线程查询QPS。全部96万逻辑标签由完整返回ID独立重算GT10命中数/mask并核对重复组合一致性，另2304次真实parity调用。

12候选全部训练完成，cal1024仅按真实HNSW三入口总hits、再较低graph NDC、再较强λ选每族新候选。Full/rank8在WebVid均选λ10、Yandex均选λ0.1；若允许Fast回退，cal也选上述新候选。audit1024不用于选择。所有模型/选择记录冻结后，validation2K、单构建、NSG/Fast30K3/Fast20K3/Full3/Rank8-3、L64/128/256/400/800共50点全部完成。

所有查询与基线单线程；每点一次完整warmup、一次独立plain wall、另一次全量count和16query原wrapper对照。100000个validation输出独立GT评分通过；NSG/原Fast30K的40000个query输出、入口和距离bits与E22逐位相同。每个数据集每族一份W/映射、每query入口与序列化HNSW图跨五L均相同。

校准诊断v1有一处verification的warmup计数元数据错误，实际未warmup且results.json正确记录0/QPS=null；在audit/validation之前以v2修正，原二进制、源码和输出保留，未改搜索、计时或选择。见[修正记录](../entry_method_exploration/20260910_three_entry_rank_v1/reviews/diagnostic_metadata_correction.json)。

## 五点结果与解释

相对matched Fast20K三入口；每格ΔRecall百分点 / ΔQPS百分比，单次wall只作探索描述。

| 数据集 | L | Full-3 | Rank8-3 |
|---|---:|---:|---:|
| WebVid | 64 | +0.070 / +0.23% | +0.035 / +0.45% |
| WebVid | 128 | +0.160 / +0.59% | +0.140 / −0.09% |
| WebVid | 256 | −0.005 / +0.87% | +0.010 / −1.10% |
| WebVid | 400 | +0.045 / +0.91% | +0.055 / +0.92% |
| WebVid | 800 | +0.030 / −0.95% | +0.045 / −0.07% |
| Yandex-IP | 64 | −0.065 / −0.00% | +0.100 / +0.05% |
| Yandex-IP | 128 | +0.105 / +0.53% | +0.290 / −0.09% |
| Yandex-IP | 256 | +0.005 / −2.96% | +0.120 / −1.50% |
| Yandex-IP | 400 | −0.030 / +0.52% | +0.095 / −0.68% |
| Yandex-IP | 800 | +0.015 / −1.11% | +0.060 / −0.25% |

原Fast30K和NSG全部原值也保留。WebVid L128，Full R74.420%/QPS2009.57/失败52，matched Fast20K为74.260%/1997.81/54，原Fast30K为73.990%/2011.94/54；Full相对原Fast30K的0.430pp不能全部归于学习，matched Fast20K本身已高0.270pp。Yandex L128，rank8为90.010%/1958.90/34，matched Fast20K为89.720%/1960.73/38。

Full六个固定强凸目标充分优化，目标值均低于同λ rank8；然而Yandex最终五点Recall均是rank8高于Full。这是优化目标更优未转化为更好搜索的实证，不是rank8全局最优或神经网络无效的证明。Full选中残差范数Web0.02922/Yandex1.63584，354/2000和1311/2000条validation query改变了三入口集合，仍只带来小幅总体变化。

graph NDC几乎不变，Yandex路由NDC略增。另在已生成标签中观察到Web319条query/412对、Yandex82条query/97对的同query a/b偏好随context反转；统计范围限于多个context重复出现且收益非零的pair，不能外推全池冲突率或将所有失败归于此。精确top3只是最高模型分数，不是搜索效用oracle；有些HNSW结果反而有更高下游Recall。

## 成本与收口

两数据集训练子进程合计137.45秒；其中Full六模型核心拟合7.35秒、rank8 125.78秒。fit-probe/cal95.68秒，audit29.05秒，最终查询评测过程381.64秒，含加载/构建/预热/计数/I/O等；QPS只取每点独立plain wall。全部新增数据搜索调用1,325,344，细项见成本账。

当前提议器复用旧全H single缓存；按当前实现从零准备还依赖3272万份single标签。新增联合标注88万不代表完整从零成本；旧E22总计169,857,792次/6639.99秒包含其他构建/标签L，不能全归本方法；exact GT/QGT/原图和single子集专属成本未新测。

该版本已完成收口，不自动加MLP/rank/λ/seed/计时。只有一个构建、每dataset2K、单次wall，不作正式显著性、跨构建稳定性或性能GO；held-out未打开，C和旧大矩阵保持停止。后续若继续，先说明如何处理真实联合收益与静态top3代理之间的对应问题，Full与rank8均保留对照身份。

## 原始证据

- [全部50点原值](../entry_method_exploration/20260910_three_entry_rank_v1/results/tables.md)、[结果JSON](../entry_method_exploration/20260910_three_entry_rank_v1/results/summary.json)、[配对比较](../entry_method_exploration/20260910_three_entry_rank_v1/results/comparisons.csv)、[图](../entry_method_exploration/20260910_three_entry_rank_v1/figures/recall_qps.svg)、[成本账](../entry_method_exploration/20260910_three_entry_rank_v1/results/costs.json)。
- [输入核验](../entry_method_exploration/20260910_three_entry_rank_v1/inputs/preflight.json)、[全标签复核](../entry_method_exploration/20260910_three_entry_rank_v1/reviews/labels_verified.json)、[模型冻结](../entry_method_exploration/20260910_three_entry_rank_v1/models/frozen_before_validation.json)、[输出验收](../entry_method_exploration/20260910_three_entry_rank_v1/reviews/result_verification.json)、[最终审计](../entry_method_exploration/20260910_three_entry_rank_v1/reviews/final_audit.json)。
- [实际执行](../entry_method_exploration/20260910_three_entry_rank_v1/commands.md)、[训练器验收](../entry_method_exploration/20260910_three_entry_rank_v1/reviews/trainer_self_test.json)、[搜索接口合成验收](../entry_method_exploration/20260910_three_entry_rank_v1/reviews/synthetic_check.json)、[模型与标签诊断](../entry_method_exploration/20260910_three_entry_rank_v1/reviews/model_behavior.json)。
