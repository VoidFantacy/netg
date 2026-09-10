# 独立设计复核：v4 utility policy tree

状态：`PASS_DESIGN_ONLY`。初审问题R1–R5已在最终正文复核中解决，见末节。这是只读设计复核；没有实现、实验或方法性能 GO。审阅完整 `report.md`、`method.md`、`minimum_gate.md`，并对照本轮本地源码审计和保存的 Fast / finite-beam 结果。只写本复核文件，未改主报告或方法契约。

本轮未发现否定主方案的数学或数值阻断。发现一处历史结果的指标误称，以及几项应在最终交付/执行协议中统一的表述。尤其旧 finite-beam 的区间是 utility 区间，不是 Recall 区间；全 H 标签不代表叶数覆盖全部动作，当前方案已正确说明这一点。

审阅时文本 SHA256（后续修订应以复核补记为准）：

| 文件 | SHA256 |
|---|---|
| report.md | ee7f0f7c2b7e8049773960d629d0df95d3c0fba308d1bdb9fc61678f31abde1d |
| method.md | 4dbd8f67d0874bab4291c4955e123f057b53fdd163ef7d2a27754dc770d9692d |
| minimum_gate.md | fa3d80e16bc8e5fd53bd66649cc840edb327abade1850cf9121f7dcd9b9ddf71 |

## 必须纠正或统一的问题

### R1：旧 finite-beam 的区间指标写错

`report.md:29` 写“四点质量区间跨0”。实际 `finite_beam_reachability_diagnostics/v2_distillation/decision.json:10–15` 的四点区间对应

`delta_U = delta[Recall@10 − .05 graph_NDC/Fast3_graph_NDC]`，

不是 delta Recall 的区间。请明确改为“四点 utility 差的 95% 区间均跨0”。该版本四点平均Recall非负、graph NDC约束通过，但统计未通过的对象是上述混合utility。此处属于应在交付前修正的事实准确性问题，不否定新设计。

### R2：不要把一次 ANN→exact 检索诊断写成几何模型类上限

`report.md:13` 的“Fast 的当前几何代理接近其可见上限”含义过宽。证据只支持在现有 prototype 和构建下，ANN改为exact原型近邻带来的同L Recall变化较小、跨数据集不一致；它不估计所有几何query模型或几何监督的可见上限。建议直接采用这一具体结论，然后保留GT1 basin oracle仍落后全H oracle的真实数字。

证据：`fast_router_diagnosis/20260908_v1/analysis/v2/analysis.md:10–11,18–19,26–27,34–35`；同报告的 GT1 basin 对照与“几何模型类上限”不是同一对象。

### R3：主契约与gate的同分接受、leaf-min规则需一致

`method.md:11,35,45–54` 有完整约束：leaf累计Recall同分后比NDC，再同分保留旧action；branch同Recall时要求NDC和复杂度均不增，且祖先分支改动后核对全部后代叶支持。

`minimum_gate.md:21,39–47,52` 简写为leaf按NDC/baseID、branch只不降低Recall，并称“非空叶支持约束”。应直接继承主契约完整规则。否则实现者可在Recall持平时接受NDC上升，或保留fit支持0却在线仍可到达的叶子，使min_leaf32和625叶容量解释不成立。

要求是每个仍保留在部署树、能够由合法输入到达的leaf都有至少32个fit支持；拟议固定树更新若制造0支持或不足支持的叶，拒绝更新。若另行剪枝，需要冻结剪枝、重置action和验收规则。不能只数当前两孩子，也不能忽略已经变空的有效leaf。

### R4：高容量参照不是学生训练的必要前置

`report.md:9,67–74` 容易读成“teacher通过才训练tree”，但 `minimum_gate.md:58–64` 的G1先训练T和四种S、G2共同审计，还明确保留T失败/S成功的情况。这一gate安排是正确的，因为T不是函数类/统计上界，S直接优化真实utility并不依赖T输出。

请将报告写成共同拟合、分别审计的两个诊断维度。T−S是两个模型的样本外质量差，不是纯蒸馏误差；T成功而S失败只能定位到当前轻量函数类/训练相对重参照的损失，不能证明存在某个必然可恢复的压缩方案。`method.md:70–71` 已正确作出区分，报告应保持一致。

### R5：额外L工作点需要冻结所用policy并另计可能的新标签

`method.md:7,15` 规定每个L独立模型；`minimum_gate.md:68` 允许先登记有限额外L后做完整成本匹配。需要说明额外L是复用冻结L64/128树，还是为新L另训模型，不能看到曲线后随意选择。若另训，则全H标签/teacher/tree成本与新的比较族须另列；当前80M搜索上限中的余额已限定验收/计时，不能暗含授权为额外L生成整套标签。

这是执行前契约完整性要求，不要求本轮开始收集标签或补跑实验。仅有L64/128的同L正收益本身不构成Recall–QPS改善。

## 已核对通过的技术内容

1. **节点损失推导正确。** 固定其余树，对实际到达节点的query，令左右当前子树最终动作分别为a、b。两个真实损失为`R*−R_a`、`R*−R_b`，共同去掉`min(R*−R_a,R*−R_b)`后，剩下恰是`|R_a−R_b|`乘选择较差一边的0/1指示。delta为0无需训练唯一方向。该恒等式不成立于把a/b替换为左右所有动作的免费最优，因此 `method.md:39–54` 禁止这种oracle替换是必要且正确的。
2. **surrogate边界正确。** logistic/hinge只提出分隔面，降低代理loss不保证真实树Recall提高；代码契约要求对真实输出验收后才接受，正确。相同经验目标的更新若不严格提高可以循环，拟议有限sweeps/收敛规则约束该风险；无全局或泛化保证的表述正确。
3. **row recompute正确。** 同深度节点的实际到达行由祖先决定，彼此不重叠；使用当前子树而非旧输出。祖先改动后重算所有后代，并校验最小叶支持，能避免过期行集合和父更新破坏leaf-min。leaf更新后才bottom-up node更新、下一轮重新分配行，也不要求每次父更新后立即重新训练全部后代。
4. **多叶重复action的表示解释正确。** 单个线性路径对应半空间交，同hub多个leaf是这些区域之并。该函数类能力不证明真实数据具有可学的多模态utility，更不证明给定叶数足够。当前报告已经保留这些边界。
5. **容量和算术正确。** 20K/min_leaf32给出625个有支持叶的上界，depth8另受256叶上界；多叶复用减少不同action数。深度10、nnz64为640 MAC；全维WebVid/Yandex为5120/2000 MAC。满树1023节点的float32权重为约1.998/0.7805 MiB，未含索引/阈值/leaf，报告没有把它当实际占用。
6. **初始化的一个补充解释。** 当前中位数递归、20K且min_leaf32、固定树拓扑通常在深度9即停止（约512叶，20K/512≈39）；625只是一般支持量上界，不是保证能得到625叶。文档称“最多”并要求报告实际叶数，因此不是数值错误。执行时应报告初始化/最终实际拓扑，不能把max_depth10直接叫作每条路径10层。
7. **高容量模型信息边界正确。** 预测阶段query-only；GT与完整动作向量只用于训练/评估；重模型不是oracle。学生主模型直接读取实测效用，而非用teacher唯一ID替代全部等价最优动作。
8. **成本口径合理。** method明确C++单路径、无在线teacher/probe/HNSW；纯wall计query预处理/节点判断/ID初始化/原图搜索；GT/hash/JSON/count放独立pass。MAC、graph NDC均不被当成QPS。gate最终要求Fast1与Fast3、正式强基线、独立build、相邻工作点与held-out；当前设计不声称已完成。
9. **“成本敏感”的含义需保持当前定义。** 本轮主C是Recall regret，NDC只做同分选择和后续成本门槛，训练不是直接最小化wall或严格限制每query NDC。报告目前没有宣称这种保证；后续不得把真实Recall目标误写成已经解决完整成本对齐。

## 已核对通过的本地证据和数字

- GT1 basin入口与全H single oracle的差距分别13.07/10.35 pp（WebVid）、7.75/4.80 pp（Yandex），范围4.80–13.07成立。见既有 `fast_router_diagnosis/.../report.md:39–47`。
- exact C8 single oracle的全H损失6.660/5.762/4.941/3.164 pp，四项全族区间均正；3.16–6.66的四点范围成立。见 `analysis/v2/analysis.md:13,21,29,37`。
- 旧 NETG formal是30K、L300、hub-side MLP，raw-query online HNSW；新query tree与其固定hub内积表达确有本地函数类区别。
- 旧 static ranker已有连续Recall/NDC、soft labels、hard-query weight与query/hub交互；旧v2确为64-NN/top8效用记忆。报告未把这些作为首次，边界正确。
- 旧 P3分割base/图，P4预测未运行；不能泛化为新query tree的负证据，报告正确。
- 标签总数`22048×2×(815+821)=72,141,056`；80M余额7,858,944，算术正确。一次build gate与未来三独立build/held-out预算明确分开。
- 前10K是历史开发集、排除本轮512不能洗成新held-out；1024 calibration/audit分离是本轮模型选择控制，gate正确保留历史开发边界。

## 结论

主方案可以作为有界的本地新候选继续设计；TAO结构、真实子树delta、重复动作leaf以及完整在线成本的推理没有发现阻断性错误。上述R1–R5已完成统一，本设计交付通过；这不产生训练授权、执行GO或性能成功结论。外部算法新颖性与原文引用由独立文献复核承担，本文件只判本地证据/数值和上述技术契约。

## 最终修订复核

已重读修订后的三份v4正文，结论为 **PASS_DESIGN_ONLY，0项未解决的技术/数值阻断问题**。

| 初审项 | 修订与核对 | 状态 |
|---|---|---|
| R1 | report明确finite-beam v2的四点utility差95%区间跨0 | RESOLVED |
| R2 | report限定为同画像ANN→exact的收益小且方向不一致，不推出几何函数类上限 | RESOLVED |
| R3 | method明确所有在线可达叶至少32fit支持；gate统一旧action tie-break、同Recall时NDC/复杂度不增及整个受影响子树检查 | RESOLVED |
| R4 | report/gate明确T和S共同拟合、分别审计；T诊断失败不否决达到S门槛的树，T/S差不称纯蒸馏误差 | RESOLVED |
| R5 | gate明确额外L复用的policy映射须预登记；另训新L的全H标签/模型成本另列，不挪用验收搜索余额 | RESOLVED |

新增三个归因对照为全局最佳fit hub、全H线性收益模型、同容量teacher唯一ID模仿树；都复用实测标签、限制在fit/calibration选择、计入8小时训练总预算。它们没有暗加online依赖或新增搜索授权。主统计族仍是8项T/S对Fast1；归因对照列为完整描述性报告，不能声称享有该8项主族之外的同时置信保证。

新spec第20节保持设计/实现边界和真实成本要求。最终核对s-target开头和验证步骤2/3、summary开头均已同步T/S共同拟合、分别审计，T失败不否决成功S；交接一致性问题也已解决。

最终核对文本身份：

| 文件 | SHA256 |
|---|---|
| report.md | 26baf754f8bd24c4ee516703ae42423c7cd18e77b50924f0d212a07c73220020 |
| method.md | 6fe4e92b9479b5d67c16d246ab3e4523c6697ce099e4d79bf7e968b2c8be01f0 |
| minimum_gate.md | 43669a2cc05f772c64cab57dabc6d80c36de69e17a17d35b43064d737fcc54fd |

最终交接身份（相同设计复核范围）：

| 文件 | SHA256 |
|---|---|
| spec.md | c4452788c271fae6e1c91aa70ceb34679b2a0684d7eb732bce04ec28c3ab9216 |
| summary.md | 4f3662c342c5c1db0f2454d9d3435cf6669b6c3a4ee6e4a1b1e08905a3d1cdeb |
| s-target.md | 382cb96e0e17ead9c695870d2e02e486b53d2cdd4064b52c6392b2e212ca905d |
