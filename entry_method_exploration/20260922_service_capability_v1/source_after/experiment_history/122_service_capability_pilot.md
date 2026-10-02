# 122 E119：响应定义入口能力与受控评分器检验

日期：2026-09-22。状态：`STOP_CAPABILITY_PILOT`。原目录：`entry_method_exploration/20260922_service_capability_v1/`。这是新的缓存训练与 query-out 检验，不是新端到端性能实验；默认 Web soft / Y hard、生产 E99 保持。

## 动机与先行工作

用户要求摆脱换模型名字和反复调参，寻找成体系的理论及可提升的方法。E118 全 H 事后 oracle 仍有空间，但固定方向加性评分未产生部署净收益。E119 提出由独立支持 query 的真实响应描述入口能力，再学习共享的 query-entry 非线性交互。

先查 UniRoute、decision-focused learning-to-rank、DCNv2、TabM、RouteLLM；补查 ALORS 与双线性算法选择，明确“表现画像、非线性冷启动映射、排序、计入评分成本”均已有前作。没有把嫁接模型称为创新，也没有完整复现上述全部论文。标准评分误差/决策遗憾桥接和 MSE 反例用于组织假设，不称新定理。

## 固定实现与角色

- E118 原 fit4096 全 H 标签，每集 4096 query；真实 K1/K100，L128，原 raw-IP、底图、主搜索不变。Web H815 / Yandex H821，另含原动态 GT10 三入口。
- 四折；每折 support1024、fit1792、monitor256、outer1024，完整 query 切分且逐字节互斥。历史曝光开发资料，不是新盲测；原 GT10 画像亦有历史训练曝光。
- PCA32 仅 support+fit；KMeans16 仅 support；按簇构建 R1/R100/T1/T100 四响应差值能力，16 伪观测向支持全局均值收缩。outer 响应不进入表示。
- 主臂 GeomMSE、CapMSE、GeomRank、CapRank：共享 32 维 `ReLU(u+v+u*v)`，两效用头和真实入口/画像余弦；MSE 对比差值加权排序加 0.1 MSE。默认分数 0，仅严格正分换单入口，同分按真实 ID。
- 对照为原 GT10、BestFixed、ClusterMean、同 fit query 的 E118 ReLU64 ridge；强控制为固定 200 轮 HistGBDT 和作者 TabM k16、2×128。全部预算/角色/停止条件在拟合前冻结，无外折调参。
- 净效用为相对默认的 `ΔRecall - 0.1×归一化搜索时间差`，两 K 等权。旧时间不含路由/新评分，不能报 QPS。参数数量匹配不等于有效容量相同；E118 不同特征家族的对照也不隔离乘性交互的因果贡献。

## 结果

全部六配置的两集 query-out 净效用均为负，主门、H1 双集能力对照、H2 相对加性参考的双集均值条件全部失败。下表为相对 GT10 的 Recall 百分点差。

| 方法 | Web R1 / R100 | Yandex R1 / R100 |
|---|---:|---:|
| GeomMSE | -1.0742 / -0.4331 | +0.0244 / -0.0542 |
| CapMSE | -1.7822 / -0.4355 | -0.3662 / -0.1611 |
| GeomRank | -1.7334 / -0.7314 | -0.5859 / -0.3274 |
| CapRank | -1.8555 / -0.8367 | -0.0488 / -0.3501 |
| GBDT | -0.0488 / -0.1631 | +0.0488 / +0.0183 |
| TabM | -0.2441 / -0.0151 | -0.1709 / -0.0305 |

GBDT / TabM 拟合 U×100 为 Web +2.2392 / +2.4314、Yandex +2.0720 / +2.1452；OOF 为 Web -0.2496 / -0.2981、Yandex -0.1851 / -0.2609。强控制有拟合内收益而未迁移，不支持只追加模型容量。Yandex GBDT Recall 均值略正，但缓存搜索时间增加 2.789% / 1.585%，仍未支付评分开销。Web CapMSE K1 救回/损伤为 46/119，TabM 为 40/50。

保留 Yandex CapRank 相对 GeomRank 的局部改善，但 Web 方向相反；不能选择单集或单 K 宣告 H1。BestFixed 全部回退默认。描述性 query-bootstrap 区间受历史曝光、重叠训练折及多配置比较限制，不当作最终显著性检验。

## 成本、核验与修正

训练控制器 5278.826 秒（87.98 分钟），峰值 RSS 20.009 GiB，离线数值库最多 8 线程；32 主模型、16 GBDT 头、8 TabM。新搜索/GT/图/K10/正式 wall/新鲜测试载荷均为 0。继承标签生成另有 4.776 小时、46,964,928 次搜索的成本。

预检验证输入、全量 top1/GT1 与 K100 mask 计数、角色互斥、外折标签隔离、同分/默认、梯度和独立标量前向。全 H 抽样完整 K100 返回 Web26112/Y26304 及各集4096默认返回按 GT100 重评分一致。独立数值审计重构能力统计、所有外折动作/收益、32主模型前向及监控选择，全部强模型重载抽查通过；920继承文件和冻结训练代码保持。此为同会话独立实现，不声称有独立人员审查。base完整SHA匹配；图只核对继承stat，未重算全图SHA。

拟合前修正多线程KMeans逐位不确定性，保存初版并重新通过隔离测试；来源metadata审查修正字段遍历，未读取新测试payload。正式汇总和数值审计首次通过。完整拟合/监控曲线与全部外折预测均保留，不仅保存最有利结果。

## 判断与边界

停止本版及未触发的原生/新源/完整曲线分支，不追加seed/depth/阈值/cluster/lambda，不改变默认。完整原始query与固定搜索可能是确定性映射，因此不能由本失败声称不可消除的信息噪声；只能说这套支持表示、固定训练预算和信息集没有形成可迁移净收益。强控制不是全部算法家族的上界，也不能唯一定位为缺数据、噪声或优化失败。

后继若存在，须先给实质新廉价信息或结构条件、同监督简单对照及反驳门；不能只是更大模型。当前没有自动后继实验。

## 原始证据

- [最终判断](../entry_method_exploration/20260922_service_capability_v1/decision.md)、[完整报告](../entry_method_exploration/20260922_service_capability_v1/report.md)。
- [理论与历史差异](../entry_method_exploration/20260922_service_capability_v1/research.md)、[条件与反例](../entry_method_exploration/20260922_service_capability_v1/theory_bounds.md)、[前作补充](../entry_method_exploration/20260922_service_capability_v1/prior_work_addendum.md)。
- [冻结协议](../entry_method_exploration/20260922_service_capability_v1/protocol.md)、[配置与角色](../entry_method_exploration/20260922_service_capability_v1/config.locked.json)、[训练前身份](../entry_method_exploration/20260922_service_capability_v1/reviews/pretraining_freeze.json)。
- [全部门与统计](../entry_method_exploration/20260922_service_capability_v1/analysis/results.json)、[指标CSV](../entry_method_exploration/20260922_service_capability_v1/analysis/metrics.csv)、[图](../entry_method_exploration/20260922_service_capability_v1/figures/oof_utility.png)。
- [数值审计](../entry_method_exploration/20260922_service_capability_v1/reviews/independent_audit.json)、[返回/GT审计](../entry_method_exploration/20260922_service_capability_v1/reviews/label_return_audit.json)、[成本](../entry_method_exploration/20260922_service_capability_v1/reviews/training_complete.json)、[训练日志](../entry_method_exploration/20260922_service_capability_v1/training.log)。
