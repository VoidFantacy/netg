# 同一搜索状态上的入口干预：机制与前作审计

2026-09-08，`DESIGN_ONLY_NOT_IMPLEMENTED_NOT_RUN`。只读本地源码/历史报告、原论文和作者README。本轮未改kernel、未训练、未搜索、未安装依赖、未读取原始validation/held-out。下载原件及SHA见[sources](../sources/adaptive_intervention/manifest.json)。PDF文本通过读取项目已保存的pypdf wheel提取，没有安装。

**候选：在正在进行的同一次图搜索中，只做一次“保持当前搜索，还是注入一个补充入口”的决策，离线监督相同完整状态、相同剩余工作预算下的真实增量。** 它有较大的结构变化，同时背负本地旧rerouter的强负证据。目前只是高风险研究候选，未证实高原创性。该方向改变搜索过程，不属于冻结原kernel的纯初始入口路由。

## 1. 不能把旧rerouter写错

[旧报告](../../../probe_reroute_results/analysis.md)与`benches/bench_entry_oracle.cpp:445–565`显示：旧方法支付Fast3的L10探测，再从Fast32中的候选重新启动搜索，将两次返回结果按距离合并。`benches/run/train_trace_conditioned_rerouter.py:203–215`已经用merged Recall/NDC作为连续目标，并按相对restart的Recall增益加权；其输入已有paid trace、candidate–frontier亲和度及近邻拓扑。因此“加trace”“预测相对增量”“学习真实效用”“显式成本”均不是本候选新点。

旧结果是探测到失败有一定可预测性，但替代入口选择未通过。它不证明所有状态条件策略都不可学；同样，保留状态省去重复工作也不能推出新策略更容易预测。旧报告明确禁止该失败分支继续实现resumable search；本次只根据用户新调研目标评价一个独立候选，没有解除旧执行禁令或恢复实验。

## 2. 近期论文已覆盖什么

| 一手工作 | 已读机制与范围 | 新候选必须明确的差别 |
|---|---|---|
| [DARTH，SIGMOD2026 / PACMMOD 2025](https://helios2.mi.parisdescartes.fr/~themisp/publications/sigmod26-darth.pdf)，原文§3及[作者仓库](https://github.com/MChatzakis/DARTH)README | 用搜索进展/邻居距离预测当前Recall，并调整预测调用间隔决定停或继续 | 预测“换入口能增加多少收益”与预测“当前Recall多少”是不同目标；在线状态和自适应调用本身已知 |
| [NGFix/RFix，SIGMOD2026 / PACMMOD 2025](https://arxiv.org/abs/2510.22316)，§4–5.4与算法2–4 | Escape Hardness刻画query邻域可达难度；RFix和NGFix利用历史query修复图 | 本候选不增删图边，只改变当次搜索动作；不能将EH保证直接套到ACSG的有限pool/kernel |
| [SHEAF，2026-07预印本](https://arxiv.org/html/2607.12229v1)，§3及算法1 | 两次窄beam结果集合变化和距离特征预测搜索所需beam，论文还讨论了未实现的warm-start改进 | “利用结果变化估难度”和“复用probe工作”都已有讨论；其集合变化界仅覆盖两次结果之间的Recall变化，不保证未来提升或目标Recall已达成 |
| [CRINN，2025-08预印本](https://arxiv.org/html/2508.02091v1)，§6.1–6.2 | LLM/RL生成ANN实现；示例已有多入口、按搜索预算加入二/三级入口及收敛停止 | 加入更多入口/按预算分层不是新机制。本文未审计其完整生成代码，不能把文中示例当本地可运行实现 |
| [Learning to Route in Similarity Graphs，ICML2019](https://proceedings.mlr.press/v97/baranchuk19a/baranchuk19a.pdf)，复用v4一手审计 | 离线学习节点/query表示并改变逐跳路由 | 学习搜索策略已存在；必须说明只在一次干预点评估“相对原样继续的剩余效用”，且完整支付控制成本 |

原稿年份与会议年份分开记录。SHEAF/CRINN仅按预印本使用；不引用作者跨数据集加速倍数作为ACSG性能预期。DARTH代码只读README，未声称逐行实现复现；NGFix原稿/作者代码核查范围另见[joint review](joint_entry_design.md)。

## 3. 真正改变的数学对象

设在固定L的正常搜索中，到预登记的某个扩展计数t时得到完整状态`S_t`，包含候选pool、frontier、visited、已扩展标记、当前答案和距离缓存。动作是`a=continue`或`a=inject(e)`。离线从同一S_t克隆分支，在相同剩余实际工作上限B内执行，定义：

`Delta(q,S_t,e;B) = R10(continue_from(S_t, inject(e), B)) - R10(continue_from(S_t, continue, B))`。

它不同于从e独立重启后的R10，也不同于重启结果与probe返回结果的合并；旧完整状态不被丢弃。GT只用于离线为两支计算结果，在线不可读。剩余B是拟议真实距离计算等工作约束，**不是把L误当调用次数**；L仍是pool容量。最终必须实测wall，因为等NDC并非等时间。检查点只设在一次扩展完成的边界；原搜索若此前已结束就直接返回，不强迫延长到检查点。工作上限B的邻接扫描中途耗尽规则、结果返回与计数粒度须事前冻结，不能只写“同预算”省略截断语义。

动作语义不能含糊：若e已扩展则为no-op；若只是scored/visited而未扩展，是否允许强制扩展需要独立状态标记。仅将e插入按距离截断的pool可能立即丢掉它，无法跨障碍；若规定强制扩展一次e，则这次扩展及其邻居距离全部扣除B。选用哪一种必须在实现前冻结，不得看结果后替换。首轮建议只研究“未扩展e的一次强制扩展后返回原调度”这个明确定义动作，同时保留自然插入对照。

新算法若要有论文意义，需要做到：以同状态成对干预标签学习相对continue的动作价值；明确何时不应干预；限制一次判断与有限备选；分析重复访问/剪枝使独立入口效用失效的条件。泛称强化学习/动态路由或把旧chooser换一个MLP不够。

## 4. 最小研究设计与停止条件

1. **no-op先行。** 暂停后原样恢复的结果、扩展顺序、距离调用与未暂停执行一致；在不触及B上限时复现原kernel。计数版与纯wall版分开验收。否则先定位实现，不能评价方法。
2. **只一次干预。** 不上来做多步RL。冻结checkpoint、L、B、最多4个由query-only模型提出的备选及一个continue动作。候选模型的训练仅用fit，在线生成备选的费用全部计算；备选不以audit GT挑选。这个家族的oracle只表示有限动作空间。
3. **分辨状态信息和复用收益。** 在相同候选/相同总预算下比较原样continue、无状态的query-only干预、state条件干预和免费动作oracle；再单独比较restart/merge与共享状态，避免把kernel节省误说成预测机制收益。
4. **最早否决点。** 若原位有限动作oracle相对continue没有值得覆盖控制成本的空间，停止；若oracle有空间但学习器在隔离开发audit仍不胜query-only/continue，停止当前动作与模型设置，不扩大到全H通用chooser扫参；若选择改进被状态维护/推理wall抵消，也停止。
5. **线上边界。** 只允许query与执行中已经得到的状态摘要；任何新topology查询、额外距离、候选生成、风险门控、分支判断和缓存操作都要付费。离线克隆大state的标签生成开销单列，不能算作线上零开销理由。

若n条训练query、每条a个补充入口、两个L，则需要`2n(1+a)`条剩余搜索分支，加`2n`次共享前缀生成及状态复制/特征/训练成本。这个数量不能和v4的完整单入口调用直接按次数比较：每支成本不同，原标签也不能代替新S_t/B标签。原base/图/有效train GT可以保留；kernel、状态、动作和计时验收须另版本建立。

## 5. 判断

相对初始入口树，它研究的是更有区别的决策问题；相对旧rerouter，它仍未解决“哪一个替代入口有增益”的可预测性。因此列为**高风险候选，优先级不由结构新奇度单独决定**。本地已有失败证据比“近期自适应ANN很热门”更重要。没有同状态增量可预测性证据时，不建议把它当确定主线，也不建议实现多步控制器。
