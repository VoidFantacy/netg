# E118：共享比较方向的入口收益预测（已完成）

2026-09-21，用户授权实际推进并要求先排查实验错误。最终状态`COMPLETED_NO_DEFAULT_CHANGE`：全部计划执行并审计完成，本版未取得可替换GT10的净收益。未按首轮均值提前结束，未追加接受后调参。

## 动机、方法与数据

从实际搜索比较方向提取跨节点共享的query信息，预测所有现有H单入口相对原GT10三入口的召回/时间收益。H为Web815/Y821，方向32、正负ReLU64维、多输出ridge、收益不正时回退GT10；它与E117的同次top3四动作浅树在输入和动作域上实质不同。保留底图、原画像/小图、raw-IP、原主搜索及停止规则。

每集方向发现2048、全H拟合4096、接受4096；源行分别10000–12047、12048–16143、25904–29999，query字节互斥。均为历史曝光开发资料，接受与E117相同且旧画像曾使用，不能作为新鲜独立测试。模型全部冻结后才物化接受载荷。四折CV仅fit内选alpha，六学习臂两集共12个最终模型均选10。

## 实际结果

完成11方法实际K1/K100/L128，以及GT10/Single1/BestFixed/GraphCost/GraphRecall/RandomCost的五预算迁移，共140点、420轮完整wall。K1预算64/128/256/400/800，K100为100/128/256/400/800，全部CPU15实际线程1串行。其余预算不按L重训。

| 数据 | GraphCost ΔR1/R100 (pp) | L128 ΔQPS K1/K100 | 接受换入口 K1/K100 |
|---|---:|---:|---:|
| WebVid | 0 / 0 | −2.602% / −2.692% | 6 / 0 |
| Yandex | 0 / 0 | −2.808% / −2.283% | 17 / 0 |

全部20个主匹配点逐query命中无变化、三轮速度范围均更慢，下降0.556%–5.137%；28个共同可达预设Recall门槛无速度收益。[0,0]经验区间来自样本差全0，不是总体等效证明。

GraphRecall在Yandex L128 K1有+0.170898pp、区间跨0、QPS−12.752%；较大L仍有质量均值增益但速度下降，完整曲线保留。Single1四个L128质量区间全跨0；Y K1 85%门槛的74.86%表观差来自稀疏L跳档，不改默认。BestFixed四头实际都选回默认。

## 为什么没有收益，及不能推出什么

全H训练Recall oracle余量Web R1/R100为+17.822266/+5.944580pp，Y为+8.056641/+4.240967pp，动作域有事后选择空间。图方向CV召回MSE相对截距基线下降0.23%–0.42%，幅度高于同容量随机方向，但净效用不足；弱正则CV更差，最终强正则接近各入口的负平均效用。两集K100最大预测收益全负，K1也几乎全回退，独立前向重算与原生完全一致。表示/样本/大量动作最大化选择误差尚未完全分离，不能宣布整个共享方向假设不可能。

## 正确性、修正与成本

全H两K三重复及原核bit/NDC、GT/mask/返回hash、合成与独立最小二乘、输入角色、模型冻结/导出/fit返回回放、旧GT10与Single1接受恢复、原源身份、140点与420轮及CPU/线程审计全部通过。Yandex时间差重复相关0.70–0.72弱于Web约0.94，符号一致率仍约93%，保留计时噪声限制；无已发现的实现错误可解释当前负结果。追加只读诊断0新搜索/拟合。

标签原生任务和后续stage2/analyze/final_audit/report均exit0。Web/Y全量标签分别23,396,448/23,568,480次NSG，正常完成；总50,541,782次NSG、3,289,120次路由，测量历时5.566小时，原生任务5.520小时，训练38.42秒、聚类11.92秒、编译10.14秒单列。最大采样RSS9.987GiB，产物在3GiB上限内；0新GT、底图、小图或K10。完整账本含合成、smoke、标签、fit审计和正式评测。

原理论文字补充GT固定条件、固定L区间与完整前沿关系、域内oracle排除NSG；三项均保留原件，未改变运行标签/策略。收尾前旧进度文档和自动报告另外保存SHA快照。最终默认Web GT10-soft-t1/Y GT10-hard、生产E99保持；E103仍是完整五集前沿。后继应先利用完整标签区分可用信息与排序泛化问题，另立可反驳协议，不按接受结果追调本版。

证据：[协议](../entry_method_exploration/20260921_comparison_direction_pilot_v1/protocol.md) · [方法](../entry_method_exploration/20260921_comparison_direction_pilot_v1/method.md) · [报告](../entry_method_exploration/20260921_comparison_direction_pilot_v1/report.md) · [最终判断](../entry_method_exploration/20260921_comparison_direction_pilot_v1/decision.md) · [完整指标](../entry_method_exploration/20260921_comparison_direction_pilot_v1/results/metrics.csv) · [独立审计](../entry_method_exploration/20260921_comparison_direction_pilot_v1/reviews/independent_final_audit.json) · [诊断](../entry_method_exploration/20260921_comparison_direction_pilot_v1/reviews/review_diagnostics.json) · [成本](../entry_method_exploration/20260921_comparison_direction_pilot_v1/reviews/cost_ledger.json) · [收尾前快照](../entry_method_exploration/20260921_comparison_direction_pilot_v1/reviews/before_final_closeout/identity.json)。
