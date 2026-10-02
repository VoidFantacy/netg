# ACSG 当前实验总结

> 更新至2026-09-11。最近完成E27 GT10收益机制分析与限定补测。实现见[spec](spec.md)，接续见[s-target](s-target.md)，历史见[s-experiment](s-experiment.md)。E24/E25/E26原资产保留。

## 当前结论

**GT10通过query相关的多目标分数归属改变画像，再改变实际三入口，产生少数query正负命中的净收益。两个已观察正点在精确画像top3下仍有提升，不能主要归因于HNSW近似误差。** 支持扩大也是事实，但填空hub、大ESS或更大GT区域覆盖都不足以单独解释收益。

WebVid hard的小幅速度收益在新三轮计时中保留，五L中位增幅0.34%–1.36%，原若干约3%的幅度未完整复现。Yandex原L128的+2.56%速度在E25/E26仅−0.18%/+0.04%；保留其质量变化，收窄速度解释。状态`GT10_MECHANISM_ANALYSIS_COMPLETE_WITH_BOUNDED_DIAGNOSTICS`，本轮已收口，未选择或启动后续方法分支。

## 完整五L主对照

GT10 hard相对matched GT1 hard；所有正负点保留。WebVid QPS为本轮三次独立warm/plain中位数之比，Yandex为两组已有独立批次的中位数之比，不能跨批次混绝对QPS。

| 数据集 | L | ΔRecall pp | ΔQPS % |
|---|---|---|---|
| WebVid | 64 | +0.285 | E27 +1.360 |
| WebVid | 128 | −0.085 | E27 +0.890 |
| WebVid | 256 | −0.115 | E27 +0.583 |
| WebVid | 400 | −0.110 | E27 +0.484 |
| WebVid | 800 | +0.040 | E27 +0.339 |
| Yandex-IP | 64 | +0.120 | E25 −0.105；E26 +0.760 |
| Yandex-IP | 128 | +0.335 | E25 −0.184；E26 +0.038 |
| Yandex-IP | 256 | +0.035 | E25 +0.228；E26 −0.068 |
| Yandex-IP | 400 | +0.080 | E25 +0.311；E26 +0.103 |
| Yandex-IP | 800 | +0.060 | E25 −0.923；E26 +0.128 |

WebVid新三轮15个对应QPS差均正，但L128/256/400仍有小幅质量损失。L800净增只有8个GT命中；不把观测非支配点或粗L连线升级为整体等Recall实测加速。Yandex validation五L正Recall也不代表跨开发段统一改善。全部NSG/Fast30K/GT1与软消融另存；例如WebVid L64 Fast本身相对NSG已有+3.625pp，GT10增量才是+0.285pp。

## 收益证据链

GT10每条fit query总权重仍1，平均分给WebVid5.993/Yandex4.571个不同hub，离开原GT1 hub的质量71.844%/58.447%。画像mass中位近似不变，ESS中位16→67.361、22→60.082，角位移中位11.66°/11.19°。画像累加unit(query)，GT只决定归属，H和在线入口数不增加。

两数据集78.10%/63.65%的validation query换三入口；同三入口的ID、距离bits、hits/mask、graph NDC全相同。WebVid L64有114条获益、101条受损，正/负命中328/271，净+57；Yandex L128为32/21条、130/63命中，净+67。五L均保留全query分母，且存在同query跨L正负切换。

为两个原正点补exact3后，WebVid L64仍+0.435pp、Yandex L128仍+0.310pp；对应HNSW是+0.285/+0.335pp。后端交互分别−0.150/+0.025pp，不向其它validation L外推，也不把exact画像检索当NSG效用oracle。

固定tail_shuffle保留0.1 GT1项、每rank全局hub频次、每hub总质量与每query质量1，打乱第2–10名与query的对应。shuffle ESS更高77.358/70.251，但8个cal/audit×exact/HNSW比较中7个质量低于真实GT10。该方向性证据支持保留目标对应关系；八个差值区间都跨0，ESS/方向又未完全匹配，信息与一般平滑的独立份额仍未确认。WebVid shuffle cal仍可优于GT1，不能说一般混合没有作用。

## Recall与成本分开解释

WebVid graph NDC五L减少约1.19%→0.12%，route NDC128.549→118.317。L128独立总wall466.300→462.185μs/query；route-only6.964→6.597、graph-only450.165→446.603，分项不相加。路由约占总wall1.49%，其节省量级不足以单独解释主要总wall变化。

命中改善组平均图计算反而增加；WebVid L64的总距离计算减少，部分来自持平和受损query。不能把速度改善统一称为好入口让成功路径更短。Yandex L128 graph NDC微增0.539/query且旧速度幅度未复现；扩展路径/cache原因尚无直接测量证据。

## E25/E26与剩余问题

填空画像不能作为直接入口主解释：WebVid原13个零支持hub没有成为validation新增入口，Yandex原来没有零支持hub。目标hub几何覆盖也不等于有限L效用，Yandex L128正负组甚至出现反向关系。原支持、角位移、入口重合度分层跨段不稳定，尚不能直接部署为选择规则。

E25门控和E26收缩未继续稳定增强，分别存在额外成本、收益流失和新增损伤；不否定GT10原局部提升。其75%/25%只评价增强版本。当前值得保留query相关多目标归属及matched硬/冻结软对照；后续若选2A等分支，仍须独立核对目标、标签和完整wall。没有自动开新训练、标签、rank/温度网格或held-out。

## 执行与证据边界

先完成已有A–C分析：108点169152输出独立评分，新增搜索0；两数据集四份已选画像的原归属digest/support及数值恢复通过。明确缺口后冻结小协议，完成9个job、30点36448输出独立评分，真实调用181376、修复0、合成0。查询进程总242.491s、峰值约9.918GiB，CPU15/实际线程1；进程时间含加载、建图、预热、计数与I/O，不换算QPS。

所有fit/cal/audit/validation均有历史使用，两个补exact正点也是事后选来解释；不称新盲测。一个QGT构建，三次wall不增加Recall样本，query区间仅描述且未多重校正。held-out未读取/hash/测试。原GT/QGT/NSG从零成本未新测。E24/E25/E26原结果、画像和日志完整保留。

## 权威交付与接续

- [E27完整机制报告](entry_method_exploration/20260911_gt10_mechanism_v1/report.md)、[原证据A–C](entry_method_exploration/20260911_gt10_mechanism_v1/existing_report.md)、[完整表](entry_method_exploration/20260911_gt10_mechanism_v1/results/tables.md)、[质量与重复图](entry_method_exploration/20260911_gt10_mechanism_v1/figures/quality_and_timing.svg)。
- [补测协议](entry_method_exploration/20260911_gt10_mechanism_v1/supplement/protocol.md)、[成本](entry_method_exploration/20260911_gt10_mechanism_v1/supplement/reviews/execution_complete.json)、[最终验收](entry_method_exploration/20260911_gt10_mechanism_v1/reviews/final_audit.json)、[历史16](experiment_history/16_gt10_mechanism.md)。
- E24/E25/E26详细原结果分别见[历史13](experiment_history/13_gt_topk_profiles.md)、[14](experiment_history/14_selective_profile_gate.md)、[15](experiment_history/15_profile_shrinkage.md)。下一阶段只按[s-target](s-target.md)和用户明确选择进入一条独立分支。
