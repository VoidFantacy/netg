# E39 固定参数与查询批次诊断

2026-09-12。状态`COMPLETE_FIXED_PROFILE_BATCH_DIAGNOSIS_STOP_BUDGET_EXPANSION`。[冻结协议](protocol.md)、[配置](config.locked.json)、[逐点结果](results/diagnosis.json)、[独立评分](reviews/independent_verification.json)、[最终验收](reviews/final_audit.json)。

## 当前结论

固定参数和八个扰动后，将查询池扩大到1024，四个参数点的两组互斥512-query方向仍全部相反，预设稳定门四点均未通过。当前结果不支持继续增加同一训练器的batch/epoch预算；应先检查这些局部动作的收益为何相互抵消。它没有证明离线画像学习不可行，也没有单独证明共享表示不足。

| 数据集 / 固定点 | 区分命中query / 1024 | 主512方向余弦（data / total） | 35分组中位数（data） | 正余弦比例 | 稳定门 |
|---|---:|---:|---:|---:|---|
| WebVid / 初始化 | 66 | -0.0541 / -0.0699 | 0.1231 | 60.00% | 未过 |
| WebVid / 已选μ | 66 | -0.2389 / -0.3123 | -0.2634 | 0.00% | 未过 |
| Yandex-IP / 初始化 | 29 | -0.3808 / -0.3702 | -0.2597 | 8.57% | 未过 |
| Yandex-IP / 已选μ | 26 | -0.1240 / -0.1139 | -0.1656 | 25.71% | 未过 |


主方向在查询前固定为前512对后512；35组是同一1024池的互补重组，彼此相关，不能当35次独立实验。有限池中两半梯度之和固定，整体信号弱时互补方向容易相反；本结果描述该固定池的稳定性，不能用35组负值制造总体显著性。1024只有一个梯度估计，未测两个独立1024批次。

## 实际做了什么

复用E37 cal冻结的WebVid rl_20260921 step140、Yandex rl_20260922 step40，各加本run初始化μ0；沿用各checkpoint后一步的原八个ε/actions，不更新μ、不更换σ/rank。画像为W=normalize(P+0.25(PB)(tanh(X)/4)Bᵀ)，X=0逐字复制P。每份W普通重建HNSW M16/efConstruction200/seed20260828，在线ef10/direct3→真实ID升序→原NSG L128/K10，无query模型或边hook。

两集分别排除253/252个原动作批次行，从剩余3843/3844条E37 train行中以预定PCG64 seed均匀抽1024，顺序切8个128块。抽样决策未解码或使用GT/奖励；前置保护SHA有既有GT字节读取。搜索只加载另存train4096前缀，不加载monitor；所有样本仍有历史训练暴露，μ/P/B也来自历史训练，故这是回顾性训练诊断。旧E37/E38整目录SHA保护包含历史开发产物的字节读取；没有读取/hash新的原validation/held-out，没有新cal/audit评测。

36份W及有序拓扑SHA全部恢复原轨迹/checkpoint。每份小图保存后以16条旧行复核count、serialized plain和原NSG三路，另与旧输出逐位比较ID、distance bits、入口、route/graph NDC。新μ0中心1024条返回也与旧基线逐位一致。

## 批次、奖励与局部差距

128/256/512/1024的query均值方差估计按批量下降，但1024的去噪条件信噪估计仍仅0.161、0.071、0.035、−0.051；没有观察到稳定方向。负估计不是负真实信号，更不证明完整参数空间没有梯度。这只条件于现有八个扰动（中心化张成至多7维），未识别扰动采样噪声。

WebVid两点仅66/1024条query能区分八动作命中，Yandex29/26条；多数入口变化未形成命中变化。最大单query占逐query命中梯度范数和5.78%/6.58%/9.21%/8.80%，比E38小批次集中度减轻；删掉最大query后全量方向余弦仍为0.934/0.895/0.893/0.903。因此此次不稳不能简单归结为一条极端query。该范数和不等于最终参数贡献或收益份额。

全量data梯度范数约0.257/0.243/0.236/0.247，正则约0.0227/0.0204/0.0128/0.0151，命中项仍占主导；加上正则，主512余弦依然全负。不支持先取消惩罚作为直接补救。

八个随机动作平均相对确定中心Recall分别为−0.0024、−0.2930、−0.0134、−0.0208pp；描述性8-block bootstrap区间分别为[−0.2698,0.2698]、[−0.4565,−0.1282]、[−0.1904,0.1587]、[−0.2161,0.1660]pp。这是固定八动作/训练query上的条件差，不代表完整Gaussian期望或泛化结论。WebVid已选μ中心本身相对原画像+0.3125pp，但随机均值只+0.0195pp；局部随机扰动反而稀释中心收益，不支持将E37整体问题直接解释为“采样有效但导出μ损失收益”。Yandex已选中心在这1024上相对原画像0pp。原E37 cal/audit负值和微小QPS变化原样保留。

## 成本、核验和产物

两集共36864个正常返回、1728次parity NSG，合计38592次（硬限40000）；HNSW查询38016、普通构建36、optimizer更新0、新GT0。查询均CPU15/实际线程1，两个进程串行耗时34.368s，其中索引加载14.819s、构建1.674s；含诊断计数、保存与检查，不是纯wall/QPS。峰值RSS WebVid 5.448GiB、Yandex 9.950GiB。

主统计约0.629s、独立复核约1.186s，均单线程；这些不含编写、保护hash、绘图或人工阅读。独立集合评分36864返回，旧结果逐位回归576条，独立LOO公式重建4096逐query梯度，检查428个组方差和1092个互斥组对。首版verify括号笔误及绘图轴标签调整保留在[修正记录](analysis_repair.md)，不增加查询或训练。

[批量表](results/batches.csv)、[全部组](results/groups.csv)、[互斥组对](results/disjoint_pairs.csv)、[query明细](results/queries.csv)、[梯度图](figures/batch_diagnosis.svg)、[固定点图](figures/fixed_contexts.svg)。全部W/物理图/原始返回保留在models/results；输入身份与旧目录保护在reviews，根文档前件在source_before。

## 接续

本版本停止扩大预算，没有追加训练/评测任务。下一步先用这些既有返回比较同一静态动作的净收益与逐query可达改进，检查收益/损伤是否在入口画像或query群之间系统冲突；该分析尚未执行。有限已测动作的最佳值不能叫全局oracle，也不能作为可部署策略。只有证据指向共享联动限制，才设计单项画像自由度修订，并先复盘E22/E28–E32；若已测动作本身几乎无改进，则不继续扩大这组局部扰动。构图策略保留独立备选，不自动重启E33删边。用户“离线训练画像、在线普通HNSW”的目标保持，当前默认未换。

## 复现入口

原目录为一次性不可覆盖产物；以下为实际阶段命令的结构，重新执行须新建独立版本并调整O，不能在当前目录重跑搜索：

```bash
env PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 taskset -c 8 timeout 1800 .venv_cpu/bin/python entry_method_exploration/20260912_fixed_profile_batch_diagnosis_v1/src/control.py prepare
env PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 taskset -c 15 timeout 1800 .venv_cpu/bin/python entry_method_exploration/20260912_fixed_profile_batch_diagnosis_v1/src/control.py run webvid2_5m_light_v1
env PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 taskset -c 15 timeout 1800 .venv_cpu/bin/python entry_method_exploration/20260912_fixed_profile_batch_diagnosis_v1/src/control.py run yandex_t2i_official10M_ip_v1
```

统计、独立复核、绘图分别为src/analyze.py、src/verify.py、src/plot.py，只读已有搜索返回。第一次绘图使用CPU9，后续修正CPU8，实际差异已记录；所有查询保持CPU15单线程串行。
