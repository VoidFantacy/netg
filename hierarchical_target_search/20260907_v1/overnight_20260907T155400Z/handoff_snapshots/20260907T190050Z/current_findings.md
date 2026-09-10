# 当前证据与研究判断

本文件汇总已完成的夜间实验与只读诊断，不是截止后的《实验总结》。当前阶段为 **P3 NOPASS**：P0/P1/P2 和 P3 新实现验收通过，P3 完整双数据集 pilot 未通过预注册搜索收益条件。**没有有效端到端性能改善证据。** P4–P8、validation 性能评测和 held-out 均未启动；研究长期目标尚未完成。截止及最终停止核验以 [控制配置](control/config.json)、实时控制状态和截止后报告为准。

## 实际设置与边界

- 数据为 WebVid `webvid2_5m_light_v1`（2,505,000×512）和 Yandex `yandex_t2i_official10M_ip_v1`（10,000,000×200），原 raw-IP base、GT、冻结 directed NSG 保持不变。
- 原 router_train 后20K `[10000,30000)` 用于 fit，前10K `[0,10000)` 是历史已使用的 development pilot。独立 QGT 5K raw hubs 复用；paired Fast 重建同20K prototype，不输入旧30K prototype。P0核验 split 身份/重叠，未读 held-out。
- 全 CPU，搜索16线程，K=10，L=64/128。count一次、纯wall五轮、预选trace独立运行；五轮计时不是五个独立Recall样本。10K逐查询配对 bootstrap 为普通95%探索性区间，不是后续P5/P6的多重校正正式性能结论。
- 真实路由和搜索API无GT。oracle由评测层提供该pilot的真实GT区域占比，只作结构/搜索机制诊断，不是可部署路由。L为保留候选容量，不是距离计算上限；所有队列共享visited和全局top-K，跨区域边仍可访问。
- 同路由统一池/区域池对照同时改变候选保留与队列调度；不能把差值解释为单一保留机制的纯因果效应。跨模型wall为固定顺序实测描述，未作配对显著性结论。

权威入口：[P0](gates/P0.json)、[P1](gates/P1.json)、[P2协议](protocol.json)、[P3协议](p3/protocol.json)、[P3新P1](gates/P1_P3_reacceptance.json)。

## P2：存在 oracle 质量潜力，真实路由失败

已运行64个仅图区域、每区2门户、20K区域查询画像、固定激活4区。比较paired Fast、真实几何路由下统一/均匀/概率池，以及oracle统一/概率池。所有真实方法在当前两点均被paired Fast支配。

| 数据 | L | 真实概率池−同路由统一池 Recall | oracle概率池−同路由统一池 Recall |
| --- | ---: | ---: | ---: |
| WebVid | 64 | −5.431 pp | +5.413 pp |
| WebVid | 128 | −3.640 pp | +5.252 pp |
| Yandex | 64 | −6.867 pp | +3.155 pp |
| Yandex | 128 | −3.488 pp | +3.359 pp |

四个oracle差值的普通95%区间下界为正，但均增加NDC并降低QPS，不能作为有效性能收益。区域选择诊断定位到真实预测与目标区域占比的差距，因而 [P2 gate](gates/P2.json) 仅允许一次表示/划分修订进入P3。P2 gate保留决策时16/23查询trace覆盖；之后用冻结实现补齐原名单，完整23查询、460条trace、276个配对重放均通过，见 [trace完成补充](p2/trace_completion_addendum_v1.json)。它们是固定样本的描述证据，不证明图不可达。

完整Recall/QPS/NDC与28个固定对照见 [P2分析](p2/analysis_v1/report.md)。

## P3：训练结构改善，没有传递成预定搜索收益

共同16×16初始化；在原有向边的叶区域目标 `J=CutFraction+λ·mean((GT10跨叶区数−1)/9)` 下，λ0/λ1各两轮确定性严格下降移动，粗细全局容量均不超过平均值1.2倍。每叶固定3门户、总768；frequency3与greedy3构成固定2×2。greedy3由每区最多8候选、128条fit查询、K10/L32单门户搜索代理选择。两数据集共8模型及256叶区实际入口/纯计时验收均完成。

结构子条件通过：fit平均GT10跨叶区数，WebVid由λ0的4.33285降为λ1的2.60275，Yandex由3.00925降为1.96480。但主对照始终固定为 **oracle_probability下λ1_greedy3−λ0_greedy3**：

| 数据 | L | Recall差 | 普通95%配对区间 |
| --- | ---: | ---: | --- |
| WebVid | 64 | −0.866 pp | [−1.083, −0.647] pp |
| WebVid | 128 | −0.790 pp | [−0.960, −0.621] pp |
| Yandex | 64 | −0.095 pp | [−0.207, +0.016] pp |
| Yandex | 128 | −0.017 pp | [−0.080, +0.048] pp |

WebVid两点明确退化，Yandex未证实改善；四格无一满足预注册的正下界。因此 [P3 gate](gates/P3.json) 为NOPASS，独立 [gate审查](p3/gate_independent_review_v1.json) 通过。全部8个固定门户对照区间含0，未证实收益，也不证明等效。16个同路由oracle区域保护对照虽提高Recall，仍增加NDC、降低QPS，不能抵消主gate失败。不能事后改选λ0为胜出方法。

完整48个测量行及32个固定对照见 [P3分析](p3/analysis_v1/report.md)。Fast部分扩展/拒绝/淘汰字段是未测量占位，不能当实测零，见 [计数语义补充](p3/measurement_semantics_addendum_v1.json)。bootstrap嵌套状态残留初始值已由全部32文件、完成标记和CI独立核对澄清，原产物未覆写，见 [分析完成补充](p3/analysis_completion_addendum_v1.json)。

## 三项有界失败诊断

诊断在相应协议冻结、实现与独立合成验收之后串行执行；未新增模型、ANN性能点、λ、种子、置信区间或gate。

**门户确实改变了实际入口。** 8格×10K查询中，greedy3与frequency3的实际入口集合全部不同。返回top10集合仍有68.34%–93.36%相同，但这不代表搜索轨迹相同，也不证明门户冗余或连接因果。实测不存在完全相同route样本，不能拿该空集检验充当实值验收。WebVid λ1有6个查询的正权重区域缺fit支持，加权代理记未定义，没有补零。证据：[门户暴露](p3/portal_exposure_diagnosis_v1/analysis.json)、[独立解释](p3/portal_exposure_interpretation_review_v1.json)。

**WebVid有部分集中度传递，却主要丢失seen目标命中。** pilot平均GT10跨叶区数λ0→λ1：WebVid4.3194→4.0209，Yandex3.0181→3.0193；所选4区域承载的绝对目标比例M4分别变化+1.808 pp/−0.004 pp。M4不是Recall上界，搜索可经共享队列和跨区边命中其他区域目标。seen指base目标ID曾出现在fit GT10，不是查询重叠或泄漏；pilot的seen目标槽位占比为57.258%/10.163%，也不是独立节点占比。WebVid主Recall差−0.866/−0.790 pp中，seen贡献−0.870/−0.753，unseen贡献+0.004/−0.037 pp，排除“退化全部来自unseen”的简单解释。Yandex近零变化不证明等效。原GT/返回ID命中、40对照及440固定分组贡献/均值全部复核通过；描述性分组无新CI。证据：[目标泛化](p3/target_generalization_diagnosis_v1/diagnosis.json)、[独立解释](p3/target_generalization_interpretation_review_v1.json)。

**实际fit目标全部满足局部目标尺度的严格条件。** 令Q=20,000，M为原有向有效非自边槽位数，d(u)为节点的入出槽位总数（保留重复边）。只读邻接、fit GT10和已保存标签，核验 `d(u)·9Q<M`；完整索引字节SHA仅用于身份核验，不作向量计算。

| 数据 | M | M/(9Q) | fit见过的独立目标数 | 这些目标最大d | 满足条件比例 |
| --- | ---: | ---: | ---: | ---: | ---: |
| WebVid | 49,611,457 | 275.619206 | 118,811 | 168 | 100% |
| Yandex | 294,844,794 | 1638.026633 | 188,913 | 162 | 100% |

按fit出现次数加权也均为100%；全部λ1/λ0终态标签不同节点52,305/72,107均满足。全库WebVid仅17节点不满足且均未见于fit GT，Yandex全库满足。两数据集各31固定组、节点/次数守恒和压缩度直方图复核通过。该条件首先保证：若已有可行候选使整数GT分散总计ΔS≤−1，该候选必降低λ1目标，即使切边项增加；不保证候选存在或解释搜索失败。证据：[冻结协议](p3/objective_local_scale_protocol_v1.json)、[诊断](p3/objective_local_scale_diagnosis_v1/diagnosis.json)、[独立摘要复核](p3/objective_local_scale_descriptive_review_v1.json)。

进一步的纯代数复核证明：固定同一节点、当前标签、考虑的候选集合与可行性后，当前λ1的候选排序等价于**先比较整数GT分散变化ΔS，再比较切边变化ΔC**。理由是两个目标叶的切边增量之差最多为d(u)，不是2d(u)，而全部fit目标都满足严格尺度界；未见fit目标的节点对任何候选都有ΔS=0，也符合该局部规则。源码用精确整数分数`9Q·ΔC+M·ΔS`。与stay完全零同分时保留原标签，严格改善的移动同分时才按目标叶ID升序取胜。候选生成、容量约束、源叶最小规模和更新顺序仍起作用；这不是全局字典序最优，也不能把λ0/λ1不同轨迹当成同状态反事实。见[纯代数补充](p3/objective_lexicographic_addendum_v1.md)及[独立审查](p3/objective_local_scale_interpretation_review_v1.json)。

## 停止边界与下一行动

本版本已完成一次表示修订，修订计数仍为1。没有证据触发辅助图，不能绕过失败gate进入P4或作第二轮同类划分调参。当前仅整理既有证据、交接与截止核验；到北京时间07:00停止后创建用户要求的《实验总结》。不能将空闲待截止写成持续训练，也不能将该版本负结果或到时停止写成长期研究目标完成。

下一次唯一最高优先行动：依据“WebVid目标更集中但seen命中下降”的反例，先做方法目标与实际有限容量搜索是否一致的设计审查，形成可证伪的小gate后再决定是否另立版本；直接调λ或加预测器都缺乏当前gate支持。

全部72测量行、60固定对照、成本与来源指针见 [核验表](report_preparation/measurement_tables_v1.md) 和 [独立表审查](report_preparation/measurement_tables_independent_review_v1.json)。exact-GT与原NSG构建均复用，历史耗时未知，不能把本次秒级构建称为完整训练；门户probe缓存由frequency/greedy共享，不可重复计费。实现保护见 [截止前保护检查](report_preparation/source_protection_preclose_v1.json)。
