# ACSG 当前实验总结

> 实测更新截至2026-09-08，计划状态同步至2026-09-09。本文维护最近一轮真实实验的结果、当前判断和证据边界。代码架构/数据/计时契约见[spec.md](spec.md)；下一阶段目标见[s-target.md](s-target.md)；全部历史实验概览与详细复盘见[s-experiment.md](s-experiment.md)。

## 1. 当前状态

最近完成的真实实验是 **Fast入口选择根因诊断**，版本`fast_router_diagnosis/20260908_v1`，机器状态`COMPLETE_FAST_ROUTER_DIAGNOSIS`。它排查输入/画像/搜索实现、近似路由、候选覆盖、入口组合和简单效用迁移，没有训练新方法，也没有产生新的端到端性能GO。

之后的v4效用树、v5四方向、2026-09-09的A+B联合理论及C独立R0都是研究设计，均未实现未训练。A+B把入口动作与可路由表示放在固定容量下共同设计；C只保留同一完整搜索状态上的一次有限入口干预诊断。二者都不改变本文件的E20实测终态，也没有产生性能或原创性实验GO。Fast仍是现有参照方法；下一阶段统一在`s-target.md`管理，不能把设计完成写成实验通过。

## 2. 最近实验实际执行了什么

- 数据：WebVid-2.5M与Yandex official 10M，原始IP、原NSG，QGT5K得到的815/821个真实hubs；同后20K prototype-train重建paired Fast。旧30K Fast单列历史参照。
- 样本：每数据集512条历史开发pilot；另对128条pilot取最近fit与随机fit控制，去重后总行数为767/768。没有读取原始validation/held-out，没有生成新GT。
- 动作：K10、L64/128，全H真实单入口；pilot上C8内28个pair、56个triple及Fast/exact/seed控制。均调用原`search_new(mode=2)`。
- 执行：2,770,770次搜索，含87,072次真实验收调用。输入/画像完整复算、count/plain/repeat、返回ID与GT10命中重算通过；检查项内未发现实现错误。
- 分析：正式使用`analysis/v2`，32项主对比、10,000次query配对bootstrap，同时给普通95%和Bonferroni32区间。历史pilot、单一主构建及bootstrap极尾分辨率限制保留。

## 3. 关键结果

以下为同L、单入口Recall@10；oracle使用真实标签免费事后选择，范围仅限现有H。

| 数据集 | L | Fast1 | exact画像1 | 真实GT1 basin入口 | 全H最佳single |
|---|---:|---:|---:|---:|---:|
| WebVid | 64 | 66.00% | 66.54% | 67.64% | 80.70% |
| WebVid | 128 | 73.87% | 74.49% | 75.61% | 85.96% |
| Yandex | 64 | 82.85% | 82.48% | 85.74% | 93.50% |
| Yandex | 128 | 91.00% | 90.64% | 91.76% | 96.56% |

当前可以确认：

1. **几何代理不等于搜索效用。** 即使免费提供真实GT1 basin，距现有全H最佳single仍差4.80–13.07 pp。当前诊断没有分别干预单均值、多模态、prior和训练密度，不能把缺口全部归因于其中一项。
2. **ANN近似不是主要修复方向。** exact3相对Fast3仅变化WebVid+0.352/+0.625 pp、Yandex−0.449/−0.312 pp，跨数据集方向不一致。
3. **短名单内外都有损失。** exact C8内完美选single仍比全H最佳single低3.16–6.66 pp；不能默认C8/C32覆盖充分或完美重排就够。
4. **固定anchor、固定三个入口不再作为默认。** 强制anchor的最佳triple损失0.84–3.11 pp；四点C8最佳single均值略高于最佳triple，后者是描述性观察，不证明single部署最优。独立single命中并集也不等于真实共享池联合搜索。
5. **没有不可学习结论。** 最近fit相对随机fit入口迁移的四个主区间均跨0；但大量最优ties存在，两L最优集合有交集的query为92.19%/96.09%。唯一入口ID变化或近邻失败不能否定更复杂模型。

## 4. 成本、修正与结论边界

四个搜索进程合计wall150.56秒、控制器跨度150.68秒、峰值RSS约10.01GiB；包含装载、计数、评分与I/O，输入hash已预热，不能换算成方法QPS或冷缓存训练时间。HNSW构建/路由没有独立或联合结束计时，正式`costs_v2.json`以null说明；4.18/11.04秒是路由开始前累计装载时间。

`analysis/v1`的uint32 NDC差被v2修正，并补齐exact C8 oracle NDC；Recall、32项主对比及图不变，没有重跑搜索。`costs_v1`的stage事件误读也由v2更正。旧版本保留，正式解释以v2为准。

本轮支持的当前判断是：**应研究真实搜索效用的表示与可预测性；现有H有机会，但廉价路由能否实现这些收益尚未证明。** 同L不等于同NDC或同wall，oracle不是可部署点或全base上界。没有新方法性能GO，也没有所有query-only方法接近理论上限的结论。

此前Multi-view成本NO-GO、层次搜索P3 NOPASS、静态utility/probe-reroute/BTG/finite-beam等具体失败边界保持，详见历史索引；本总结不再重复各分支流水账。重新评估相关思路前必须进入对应详细复盘，核对当时的监督、成本、数据访问和修正，避免将旧方法换名重做。

C R0 的新增判断同样不是实验结果：E13/E15只支持“搜索进展有增量信息”；E14 最终 v4 在 WebVid 提供“替代入口选择失败”的强负证据，但 Yandex 最终扩展未运行。当前尚未测量同状态有限动作oracle、状态相对query-only的增量、pause/resume parity或完整wall。QING 2012与ANNiE等前作还使其原创性只能落在更窄的成对动作值、共同剩余 graph-NDC cap 与逐分支实际成本合同。详见[C独立评估](entry_method_exploration/20260909_c_r0_v1/assessment.md)。

## 5. 权威证据入口

- 当前实验完整复盘：[历史08：Fast根因诊断](experiment_history/08_fast_router_diagnosis.md)。
- [原报告](fast_router_diagnosis/20260908_v1/report.md)、[协议](fast_router_diagnosis/20260908_v1/protocol.md)、[执行台账](fast_router_diagnosis/20260908_v1/state.json)。
- [正式统计v2](fast_router_diagnosis/20260908_v1/analysis/v2/analysis.md)、[成本v2](fast_router_diagnosis/20260908_v1/results/costs_v2.json)、[独立统计复核](fast_router_diagnosis/20260908_v1/reviews/independent_analysis_review.md)。
- 下一阶段：[s-target.md](s-target.md)。A+B理论：[联合包](entry_method_exploration/20260909_ab_joint_r0_v1/README.md)。C审计：[C R0](entry_method_exploration/20260909_c_r0_v1/README.md)。历史全索引：[s-experiment.md](s-experiment.md)。研究设计与真实实验分流：[历史09](experiment_history/09_research_designs_not_experiments.md)。
