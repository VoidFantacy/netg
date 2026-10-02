# ACSG 下一阶段方向与实验接续

2026-09-11。E28共享入口变换研究已完成并收口，状态`SHARED_TRANSFORM_EXPLORATION_COMPLETE_NO_FORMAL_GO`。本轮没有建立共享线性或小MLP优于原GT10的稳定双数据证据，保留原已冻结GT10路线。 本轮授权的标注、训练、五L三轮比较、图与报告均已完成；下面是未执行的下一研究建议，不自动借用本轮或历史剩余额度。

## 1. 优先处理监督压缩，暂不增加网络容量

E28完整三元组教师有+4.626/+2.850pp训练侧候选空间，但共享模型的集合CE下降未提高教师top3入口重合度。先检验“哪些教师更改值得学”和“损失是否惩罚真正的top3错误”，比直接扩大MLP/加query塔更有依据。固定H时离线MLP仍导出静态W，并未新增在线非线性边界。

完整证据：[E28报告](entry_method_exploration/20260911_gt10_shared_transform_v1/report.md)、[教师分组](entry_method_exploration/20260911_gt10_shared_transform_v1/results/teacher_diagnostics.json)、[训练核验](entry_method_exploration/20260911_gt10_shared_transform_v1/reviews/model_verification.json)、[完整曲线](entry_method_exploration/20260911_gt10_shared_transform_v1/figures/recall_qps_main.svg)。标签内预测子集带选择偏差，不当作全fit或部署收益。

## 2. 若明确继续，下一版本先作最小监督对照

建议保留GT10锚点、固定H、同原NSG、一次microHNSW top3。研究对象是教师和损失，先固定共享linear及单一事先正则；不同时扩大网络、rank、温度、候选数或query端模型。

| 对照轴 | 未执行的具体比较 | 要解决的问题 |
|---|---|---|
| 教师 | 现有max-hits/min-NDC教师，对比无额外命中空间时保留原GT10三入口的教师 | 大量同命中NDC标签是否稀释少数质量改进信号；新教师可能放弃成本收益，必须计量 |
| 损失 | 当前集合CE，对比完整教师成员与最强非教师入口之间的top3 margin | 单个完整query教师下无旧E23多上下文pair冲突；检查第三入口错误是否真正减少 |

两轴不能一次一起改后把收益全归于其中一项；需冻结最小2×2控制或先选一轴。可复用本轮兼容C8标签，不需要重新全H单入口标注；新模型训练和开发/正式查询比较仍需独立协议及明确预算。SoftSort/SOFT top-k只列为文献备选，不优先加一层复杂松弛；它们不解决教师偏差。

停止规则应在新搜索前定量锁定：先验证导出/梯度和训练侧top3目标确实改善，再看cal真实三入口Recall与完整工作，最后只对冻结配置补完整wall；缺少训练/开发改善就不扩大模型。必须保留旧损失/原教师负结果，不能靠事后换门、换L或挑seed取正点。

## 3. 保持的数据与计量边界

- 继续保留matched GT1 hard、GT10 hard、原cal冻结GT1/GT10 soft；WebVid正式原画像是GT10 soft，Yandex为GT10 hard。NSG/Fast30K保持独立身份。
- E24–E28原源码/图/H/画像/标签/结果/日志均保留。基座、度量、query、GT、图、H或路由参数改变，相关标签/选择/计时随依赖失效，不能直接复用。
- fit/cal/audit/validation均有历史使用。held-out不自动开启，新图/新seed/新数据也不在现有预算中。
- 本轮预算已经收口；actual calls=3,377,147，repair=0。空余预算不转成新网格。
- 只有独立同机完整Recall–QPS证据才能支持性能判断。教师上界、exact ranking、NDC或单次QPS差均不替代它。

## 4. 历史路线与恢复入口

E27机制分析已完成，其余2A/3A等历史建议保存在[E28修改前s-target](entry_method_exploration/20260911_gt10_shared_transform_v1/source_before/s-target.md)，不是当前自动执行队列。E25选择性改道、E26收缩的负结果不抹去E24/GT10局部正信号；本轮共享变换的结果也只约束本教师/目标/容量/样本范围。每次接续先读AGENTS、summary、spec、本文件、s-experiment和相应历史卡，再核对源与原始测量。
