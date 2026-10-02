# 28. E39 固定参数的大批次方向诊断

2026-09-12，状态`COMPLETE_FIXED_PROFILE_BATCH_DIAGNOSIS_STOP_BUDGET_EXPANSION`。[报告](../entry_method_exploration/20260912_fixed_profile_batch_diagnosis_v1/report.md)、[协议](../entry_method_exploration/20260912_fixed_profile_batch_diagnosis_v1/protocol.md)、[配置](../entry_method_exploration/20260912_fixed_profile_batch_diagnosis_v1/config.locked.json)、[验收](../entry_method_exploration/20260912_fixed_profile_batch_diagnosis_v1/reviews/final_audit.json)。用户在E38建议后要求继续，授权执行此前正常36864/硬限40000的最小控制。

## 动机、机制与来源

E38发现batch128反馈稀疏但未证明更大query批量能稳定方向。E39固定WebVid rl_20260921的μ0/step140、Yandex rl_20260922的μ0/step40，并固定对应checkpoint后一步的原八扰动。仅从E37 train4096排除两原批次后另取1024，seed预锁；同名单服务两参数点、8个互斥128块。普通HNSW参数/真实ID/顺序、原NSG/raw IP/L128/K10不变，每个实际静态配置真实搜索；无optimizer、σ/rank/选点更新。

固定参数和八个扰动后，将查询池扩大到1024，四个参数点的两组互斥512-query方向仍全部相反，预设稳定门四点均未通过。当前结果不支持继续增加同一训练器的batch/epoch预算；应先检查这些局部动作的收益为何相互抵消。它没有证明离线画像学习不可行，也没有单独证明共享表示不足。

| 数据集 / 固定点 | 区分命中query / 1024 | 主512方向余弦（data / total） | 35分组中位数（data） | 正余弦比例 | 稳定门 |
|---|---:|---:|---:|---:|---|
| WebVid / 初始化 | 66 | -0.0541 / -0.0699 | 0.1231 | 60.00% | 未过 |
| WebVid / 已选μ | 66 | -0.2389 / -0.3123 | -0.2634 | 0.00% | 未过 |
| Yandex-IP / 初始化 | 29 | -0.3808 / -0.3702 | -0.2597 | 8.57% | 未过 |
| Yandex-IP / 已选μ | 26 | -0.1240 / -0.1139 | -0.1656 | 25.71% | 未过 |


## 结果解释与限制

35个互补512分组中正data余弦比例60%/0%/8.57%/25.71%，是同一池相关重组，不是独立重复。全1024去噪条件信噪估计约0.161/0.071/0.035/−0.051；不能据此证明总体或完整256维梯度不存在。1024没有独立另一半。主/辅助门均在查询前写入协议，四点全未过，停止增加同训练器预算。

WebVid66/66、Yandex29/26条query能区分动作命中，正则仍较小。最大query范数份额降为约5.8%–9.2%，删最大后方向保持约0.89–0.93；不稳并非仅由单条记录造成。WebVid已选中心在本训练池比原画像+0.3125pp，八随机动作均值只+0.0195pp；随机−中心−0.293pp，描述性8块区间[−0.4565,−0.1282]。该局部结果保留，但非盲测/新性能优势，也不支持“采样优于导出中心”的简单解释。其它三个随机−中心区间跨0。

## 执行与保护

两集共36864个正常返回、1728次parity NSG，合计38592次（硬限40000）；HNSW查询38016、普通构建36、optimizer更新0、新GT0。查询均CPU15/实际线程1，两个进程串行耗时34.368s，其中索引加载14.819s、构建1.674s；含诊断计数、保存与检查，不是纯wall/QPS。峰值RSS WebVid 5.448GiB、Yandex 9.950GiB。

36画像/拓扑恢复、576历史query逐位回归、36864独立集合评分、4096逐query梯度/428组方差/1092组对验收通过。没有新validation/held-out原始读取/hash；旧目录保护会读E37已有开发隔离产物，搜索只加载另存train4096。已有历史暴露不称独立验证。E37/E38目录前后SHA保持，根文档前件独立保存；[verify语法与绘图调整](../entry_method_exploration/20260912_fixed_profile_batch_diagnosis_v1/analysis_repair.md)均0额外搜索。

## 尚未执行接续

先做已测动作净收益/逐query收益损伤与入口变化的缓存归因，区分局部动作无空间与共享联动冲突；不凭此直接换自由W、增大batch或训练epoch。新表示前需复盘E22/E28–E32，图学习保留独立备选。E37开发门/默认保持，无排队任务。详见[s-target](../s-target.md)。

[批量表](../entry_method_exploration/20260912_fixed_profile_batch_diagnosis_v1/results/batches.csv)、[query明细](../entry_method_exploration/20260912_fixed_profile_batch_diagnosis_v1/results/queries.csv)、[方向图](../entry_method_exploration/20260912_fixed_profile_batch_diagnosis_v1/figures/batch_diagnosis.svg)、[独立核验](../entry_method_exploration/20260912_fixed_profile_batch_diagnosis_v1/reviews/independent_verification.json)。
