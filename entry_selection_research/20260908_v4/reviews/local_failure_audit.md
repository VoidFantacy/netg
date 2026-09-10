# 本地旧方法失败范围与重复命名审计

状态：`READ_ONLY_AUDIT_COMPLETE`。审计对象是已实现的旧方法及保存结果；新方法尚未训练或测量。本轮只读源码、配置、日志、manifest、聚合报告和既有诊断摘要，未打开 base、NSG 图、原始 query/GT 向量，未运行 ANN、SVD、模型训练或搜索实验。源文件行号均相对 `/data/netg/ACSG` 当前 checkout；旧文件未修改。

## 主要结论

“离线用真实搜索监督、线上不 probe、使用连续 Recall/NDC 效用、soft labels、query/hub 特征、难查询加权、成本优先或 distillation”分别都已有本地先例。不能把这些词换成新名称作为实质区别。旧 NETG 甚至已经遍历全 DPC hub 生成标签，并在离线用非线性 MLP 变换 hub，线上只做固定 embedding 的 HNSW 内积搜索。

旧结果没有证明 query→搜索效用在数学上不可学习，也没有测试过新的完整动作代价向量驱动的 query 决策树。最接近的失败是：Fast top-32 上的低容量对角交互 soft-listwise ranker；Fast top-8 上以 64 个近邻记忆效用的 cost-first atlas；以及把单一 oracle ID 的查询均值压成一个球面 centroid。它们的监督压缩、候选截断、函数类和成本口径必须分别陈述。

若新机制采用全 H 的 native-search 动作代价向量、按真实代价差训练的 query 分支和固定路径预算的小树，其与本地旧实现的区别是上述组合，而不是首次使用全 H、首次使用成本或首次轻量在线。当前主方案已改为允许多 leaf 对应同一 hub 的 TAO 式 utility policy tree；“全 H”仅是每叶可选动作池，不保证所有 H 最终都会被树输出。TAO/FilterTree 等外部已有方法、如何引用及本任务的贡献边界，应由文献审计独立判定；本文件不宣称算法原创。

## 1. Static sparse utility ranker：真实效用和 soft label 都已经做过

### 训练和标签

- 两数据集固定 Fast seed `20260828` 的 hub/prototype、NSG `R64/L_build100/C512`；`drl_train` 前 10K，其中 `[0,8000)` fit、`[8000,10000)` 内部 early-stop dev。独立 validation 前 10K 用于输出路线和报告。三个 seed 只重启参数优化，不是三个独立图/候选构建。证据：`sparse_utility_ranker_results/analysis.md:5–16`；`benches/run/train_sparse_utility_ranker.py:148–157`；两个根目录 `sparse_utility_ranker_variants_*_diag_v1.build.json` 的 `sources` 和 `seeds`。
- 每个 query 的候选是相同 Fast 原型 top-32；单入口在 native `search_new` 上测 `Recall@10`、graph NDC，预算 `L=64/128`。不是几何标签，也不是 GT basin ID 标签。`bench_entry_oracle.cpp:118–146,608–652` 证明 native search 与标签计算边界；`train_sparse_utility_ranker.py:45–62` 读取完整 shortlist 的 Recall/NDC。
- 目标先跨两个 L 平均：`U(q,e)=mean_L R10(q,e;L)-0.05 mean_L[NDC(q,e;L)/max(NDC_Fast3(q;L),1)]`。难度权重 `w(q)=1+(1-mean_L R10_Fast3(q;L))`。训练使用 `softmax(U/0.05)` 的 listwise cross entropy，并加 `1e-4` 对角参数正则。不是唯一 oracle-ID 的硬分类。见 `train_sparse_utility_ranker.py:133–138,171–177`。

### 函数类和线上信息

单位化的 query、prototype、raw hub；参数是两个 d 维对角权重、每 hub bias、每 shortlist rank bias 和一个 scale。分数为

`exp(log_scale) * qᵀ (w_p ⊙ p_e + w_r ⊙ h_e) + b_e + b_rank(q,e)`。

见 `train_sparse_utility_ranker.py:66–84,117–131`。这确实包含 query/entry 交互，但不包含 query MLP、entry-pair 的非线性网络、图 trace 或联合多入口 utility。不要把整套模型误写成纯粹全局 Voronoi：Fast 候选选择和 `b_rank(q,e)` 本身引入分段 query 依赖；在固定候选/排名内分数差仍是线性的。

Adam `lr=.02`、batch 256、最多 50 epochs、内部 dev patience 8；恢复最优 dev state，WebVid 实际 15/13/11 epochs，Yandex 22/24/24。见 `train_sparse_utility_ranker.py:97–104,157–201` 和两个 build manifest 的 `runs`。没有重 teacher→小 student；就是该对角 ranker 本身。没有 query-noise augmentation。

路由输出模型分数最高的 3 个候选；没有固定保留 rank-0 anchor。源码直接 `order[:,:3]`，见 `train_sparse_utility_ranker.py:203–208`。labels 的所有 shortlist candidate 都保留 soft mass，exact-utility ties 在 soft target 中分配相同目标权重；没有专门的 near-tie 集合/噪声置信带，但不能说旧模型“只学唯一 ID”。

### 结果和失败范围

| 数据集 | 同 L 的 R10 / graph NDC | 近似匹配 graph NDC | 可支持结论 |
|---|---|---|---|
| WebVid | +0.197 至 +0.329 pp / +0.47% 至 +1.03% | L63 对 Fast64：+0.027 至 +0.100 pp，NDC -0.26% 至 -0.62%；L127 对 Fast128：+0.125 至 +0.218 pp，两 seed NDC 更低、一 seed +0.088% | 小幅正信号 |
| Yandex | -0.042 至 +0.202 pp / +1.78% 至 +3.31% | L62 对 Fast64：R -0.158 至 -0.402 pp 且 NDC +0.46% 至 +0.89%；L126 对 Fast128：R -0.070 至 +0.016 pp 且 NDC +0.46% 至 +0.63% | 不通过跨数据集 graph-cost gate |

证据：`sparse_utility_ranker_results/analysis.md:18–48`，三 seed 各自的 `sparse_utility_ranker_results/*/validation_10k_l*.json`。保存 build manifest 中 predicted-top1 平均 U 对两个数据集三个 seed **均低于** Fast rank-0：WebVid Fast `0.649449`，predicted `0.645703–0.646656`；Yandex Fast `0.816569`，predicted `0.811356–0.811697`。这与 top-3 的小幅 recall 变化不是同一指标。

保存路线是提前生成的 `.bin`，评测器在图搜索前读入 `extra_entries`，graph timer 只包住 `search_new`。证据：`train_sparse_utility_ranker.py:203–210`；`bench_entry_oracle.cpp:404–422,139–146`。因此这里**没有验证完整在线 Fast top-32 检索＋ranker 推理＋图搜索的 wall-time/QPS**；不能把 graph-only 计时或近似 NDC 匹配叫作端到端 Pareto 改善。

严格失败范围：这份 top-32、对角交互、两个 L 池化目标、soft-listwise、最终取 top-3 的实现在规定 gate 上失败。不能扩张为“所有静态 query 特征不足”“所有非线性 teacher 都失败”或“完整 H 的 cost-sensitive policy 无法泛化”。旧报告后半段提出的 probe-reroute 是历史后续方向，不构成本轮恢复授权。

## 2. 旧 NETG：全 hub 搜索监督 + 离线 hub MLP，线上没有 query MLP

### 实际配置，不用旧 wrapper 默认值代替运行证据

两个 formal runner 均明确 `--limit 30000 --query_type drl_train --L 300`。`logs/webvid2_5m_light_v1/labels.time.txt:1` 和 Yandex 同名文件 `:1` 保存了实际命令；`benches/run/run_webvid2_5m_light_v1.sh:70–85` 与 `run_yandex_official10m_ip_v1.sh:43–50` 一致。`run_gen_labels.py` 某些旧数据集的默认 L=100 不能代表这两次 formal run。

实际 hub 数为 WebVid 815、Yandex 821；raw query 数均 30K。训练丢弃 `cost==-1` 的 fallback 后分别剩 **25,067 / 29,904** 条；每条 12 倍 augmentation。WebVid 在 epoch 155 停止，Yandex 跑完 300。WebVid 约 2.104M 参数（d=512），Yandex 约 0.323M（d=200）。证据：两数据集 `logs/*/router.log:7–16`；WebVid `:195–210`；Yandex `:55–79`；WebVid `labels.validation.json:1`。

### label 的真实含义和损失的信息丢失

1. `bench_generate_labels.cpp:135–153,184–209` 遍历 sorted DPC hub IDs 的全部 hub，逐 hub 独立 `probe_search`。
2. `probe_search` 是一个单独实现的 sorted-vector pool：每次处理后 `sort`/截断，cursor 递增；没有 native `search_new` 的 retained-candidate flag/rewind 语义。成功条件是搜索结束时 `pool[0].id == GT@1`，不是任意命中 top-10，也不是 native finite-beam Recall@10。见 `bench_generate_labels.cpp:35–86`。
3. 在成功 hub 中只保留最小 NDC 的一个 ID；严格 `<` 更新，cost ties 留遍历中的第一个 hub。失败 query 退回最近 hub，标 `min_cost=-1`，随后训练全部丢弃。见 `bench_generate_labels.cpp:192–226`；`train_router.py:174–187`。
4. `min_cost` 数值在训练中只用于有效性过滤，不进入 cost-sensitive loss。没有保存给模型的完整 action cost vector、等价优胜集合或按代价差加权的 regret loss。

该 teacher 的“真实搜索”必须限定为它实际执行的自定义 probe；它确实使用了图结构和搜索结果，但不能把 L300/GT1 的 unique-ID label 当作当前 native L64/128/R10 的完整监督。

### 模型与训练

`LightRouter` 只接受 hub raw vector，宽度 `max(384,2d)`、两个 hidden 的 Linear/LayerNorm/GELU、输出 residual `h+.05*MLP(h)`。见 `train_router.py:125–161`。训练 raw query 做 anchor，正 hub / 一个从 top-15 geometric hard negatives 随机选的 hub 经过 MLP。初始和每 15 epochs 从当前 hub embedding 刷新难负例；只屏蔽唯一 oracle ID。见 `train_router.py:199–224,237–250,364–405`。

损失为 batch 中 `[B positives; B negatives]` 上 temperature `.07` 的 InfoNCE，加 margin `.1` triplet；没有 mask 同一 hub 重复作为其他行 positive 的 false negative，也没有把同效用的其他 hub 标成正例。见 `train_router.py:396–407`。这是结构风险/信息丢失的源码证据，尚未独立消融证明它是性能失败的主因。

每条 query 的增强保留同一 hard ID：原样一条，其余加独立高斯噪声，坐标 std=`.01*mean_query_norm`。这种增强假定局部标签稳定，但没有对噪声 query 重新执行 probe，也没有检验 unique label 的局部稳定性。见 `train_router.py:237–250`。不要据此直接断言噪声造成失败。

AdamW `5e-4`、weight decay `1e-4`、batch 512、OneCycle；early stop 根据训练 loss，未划独立 dev，停止时导出当前 state 而非恢复 best-loss state。见 `train_router.py:19–34,349–360,448–471`。

### 离线重、线上轻早已存在，但表达仍有限

训练后归一化全部 hub embedding 并存 `.bin`，见 `train_router.py:469–498`。正式 C++ 模式将其建 HNSW InnerProductSpace；线上直接 `searchKnn(xq+i*d,3)`，没有调用 query MLP。见 `benches/test.cpp:109–142,351–363,507–512`。源码字符串“0ms inference”只能解读为没有在线神经网络，不能解释为没有 routing cost。

由于 query 没有经过非线性变换，导出的固定 hub embedding 再复杂，每个 score 仍是 `qᵀz_e`；精确 top-1 的 action cell 是球面/线性内积划分，HNSW 再施加近似检索。离线 hub MLP 不等于一个能在 query 空间预测非线性 utility 的重 teacher，也没有额外 student 蒸馏步骤。

### 结果边界

`fast_entry_benchmark_results/benchmark_summary.md:1–10,41–46,75–80,139–145,179–185` 汇总保存的 10K held-out ×3 对比：WebVid Fast 相对 Formal Neural R1 高 `0.80–1.31 pp`、R100 高 `0.21–0.32 pp`，同次 medoid 归一化 QPS 更高；Yandex Recall 基本持平，Fast 有小幅归一化 QPS 优势。这里是在既定 NSG、formal DPC/hub 和该训练流程上的比较，不能归因为“省了在线 query MLP”，也不能说旧 NETG 在任何基线上完全无效。

日志结尾的 oracle-ID Top1 命中 24.8%/19.6%、平均 rank 37.4/41.3 是从有效训练 pairs 中抽取最多 500 的诊断；不是 held-out routing accuracy，更不是 regret。见 `train_router.py:509–530` 与两份 router.log。

## 3. Search-aware centroid 与 signed utility residual prototype

### Oracle-label centroid

WebVid `drl_train` 前 5K、现有 815 QGT-Cover hub、native single oracle `L64/R10`；809 hub 有至少一个 label，观察 hub 的 label count 最小 1、最大 21。`build_search_aware_prototypes.py:53–72` 将每个 query 的唯一 `selected_single_entry_id` 映射到 hub，用 `normalize(raw_hub_prior_1 + sum unit_query)` 生成一个 prototype；没有 optimizer、query MLP 或 teacher/student。

unique label 来自 `bench_entry_oracle.cpp:762–778` 的“最多 R10 hits，然后最小 NDC，再保持第一个 candidate”，并非所有等价最优 action。源码使用 native search，标签比旧 NETG 的 GT1 custom probe 更接近当前任务，但最终压为单类均值。

独立 validation 1K ×3、L64/128/200/400：top-3 R1/R10 +0.35–0.82 pp，graph NDC +0.36–0.71%；R100 基本平。top-1 对 Fast top-3 的 R1 -0.2–0.7 pp，R100 -0.066–0.379 pp，graph NDC +0.95–3.08%。证据：`search_aware_entry_results/webvid_train5k_l64_r10_prior1_v1/analysis.md:5–21`。三次是同 query 的重复计时；缺 routing cost，不是 build/query 不确定性。见该报告 `:35–37`。

失败范围是一球面 centroid 对 hard oracle label 的压缩，且只有 WebVid 1K 小评估。把“所有单入口在完整 H 上不可学”归给它错误；它也不能支持无监督 query 聚类足以恢复真实 utility。

### Signed residual prototype

WebVid train10K、Fast top-32 单入口 L64/128/R10；先计算两 L mean Recall 与 mean NDC。此处成本归一化分母是该 query **32 候选 mean NDC**，与 ranker 使用 Fast3 NDC 的公式不同。`U=mean R-.05 mean NDC / rowmean(mean NDC)`，减 rowmean U，再乘 `1+(1-mean Fast3 R)`，作为 query 的有符号权重。每 hub 汇总 `sum a_qe * unit_q / sum |a_qe|`，最后 `normalize(old_prototype+.25*residual)`。见 `build_utility_residual_prototypes.py:47–104`。

该方法已有连续 utility、负贡献、query-centered advantage、难度加权，无 unique oracle ID/noise/optimizer，线上还是一个固定 prototype 的 HNSW top-3，没有固定 anchor，也没有重 teacher。

`utility_residual_entry_variants/webvid_train10k_top32_l64_128_r10_a025_c005_t1_v1/manifest.json` 确认 811 hub 获得观察。validation10K ×3 的 R10：L64 `0.65505→0.65615`、L128 `0.74606→0.74683`、L200 `0.79325→0.79439`、L400 `0.85421→0.85506`，即 +0.110/+0.077/+0.114/+0.085 pp；NDC 均极小下降。见 `utility_residual_entry_results/webvid_train10k_top32_l64_128_r10_a025_c005_t1_v1_validation10k/validation_10k_top3_3run.json` 中四个 `top_k=10` 行。

文件中的 graph latency 没计完整 routing，且旧 bench 固定方法顺序/计数搜索不能替代纯 wall 对照。这里只支持非常小的 WebVid Recall/NDC 改动；没有这份 residual 方法的双数据集全成本成功。所谓“用 utility residual 更新 prototype/atlas”已是直接先例。

## 4. finite-beam v1 与 v2 distillation：不能把失败状态名读成普遍不可预测

### v1 的已知信号与尚未部署的部分

`v1/trace_design.md` 冻结两数据集 train `[0,2000)`、Fast geometry top-8、single-entry、L64/128；trace/native 240 smoke cases 全部 ID/distance/NDC parity。fit `[0,1600)`、audit `[1600,2000)`，geometry 和 geometry+trace 同容量 closed-form ridge。trace 是搜索过程后才能见到的信息。

正确终态是独立审计的 `NO_GO_NOT_LIGHTWEIGHT / TRACE_INCREMENTAL_PASS_COST_ALIGNMENT_FAIL_COMPRESSION_UNTESTED`，不是原 v1 的字面 `NO_GO_TRACE_NOT_INCREMENTAL`。trace 相对同容量 geometry 的四点 U 增益 CI 下界均正；相对 rank-0，3/4 点不满足 +0.5% mean graph-NDC，收益还高度集中。见 `finite_beam_reachability_diagnostics/v1_audit/analysis.md:5–17,34–59`。

该审计的 cost-constrained top-8 oracle 四点均有正 U CI：R10 +3.125/+1.325/+2.175/+0.500 pp；这是用真实结果标签挑动作的不可部署上限，不是 query-only teacher 成功。见同报告 `:61–78`。

### v2 实际上是近邻记忆，不是已训练过的非线性 teacher→小模型

完整实现 `benches/run/run_cost_constrained_reachability_distillation.py:15–21,63–112,165–188`：

- 仍是上述 train2000/top-8，fit1600、audit400，两个 L 分开建数据。
- 从保存结果读各 entry 的 R10、NDC、Fast3 NDC；`U=R10-.05*NDC/Fast3NDC`，监督量为相对本 query rank-0 的 utility margin 和相对 NDC。
- audit query 用归一化 raw-query exact cosine 找 fit 的 64 近邻。只为 audit Fast top-8 中在近邻候选记录里出现至少 4 次的同一 entry 做预测；权重 `max(cos,0)`，全部非正时均匀。
- 计算两个监督量的加权 mean/SE。候选只有当 `mean(relative NDC)+SE <= .005` 且 `mean(utility margin)-SE > 0` 才可能替代 rank-0；选最大保守 margin。默认回退 rank-0，但最终是 single entry，**不是强制 anchor 与替代入口并存**。
- `atlas_fit.npz` 实质上存 fit query 与每 L 的 entry IDs、relative NDC、margin；没有已学习隐藏表示、神经 teacher、parametric feasibility classifier、树 student，也不使用 trace 的动态统计作为线上输入。在线需要 Fast top-8、query 向量和整个 fit atlas，没有 online graph probe。

| 数据集 / L | R10 delta | mean graph-NDC delta | utility 95% CI | reroute |
|---|---:|---:|---|---:|
| WebVid 64 | +0.200 pp | +0.214% | [-0.001420, +0.006320] | 9.00% |
| WebVid 128 | +0.025 pp | -0.370% | [-0.003999, +0.004588] | 18.00% |
| Yandex 64 | +0.025 pp | +0.420% | [-0.005857, +0.004316] | 11.00% |
| Yandex 128 | +0.050 pp | +0.384% | [-0.000562, +0.001284] | 12.75% |

证据：`finite_beam_reachability_diagnostics/v2_distillation/decision.json:1–30` 及两个 dataset/report.json。四点图成本条件通过，四个 utility CI 均跨 0，所以在冻结 train gate 失败；validation/held-out 未进入，没有可部署 latency 验收。保存 atlas 大小约 3.59MB/1.59MB。

严格失败范围是 fixed 64-NN、min-4、top-8 的局部 query 记忆估计，400 audit rows 和固定一 SE feasibility/margin 门槛。terminal `NO_GO_NOT_PREDICTABLE` 是版本状态，不能推广为任意函数类不可预测。反过来，新名称“cost-sensitive reachability distillation”也不够：必须明确相比这套 near-query mean/SE 方法，新增何种可学习规律、如何避开几何近邻平滑假设、如何量化压缩损失。

## 5. 与旧层级结构的边界

当前本地文档明确旧 P3 是 base 的 16×16 区域、每叶 3 门户、oracle 全局选 4 叶区，以及区域候选容量保护；P4 层次线性预测未实现、未启动。见 `spec.md:238–244,268`，`summary.md:27–31`。因此不能把 P3 NOPASS 称为“成本决策树已经失败”，也不能把 P4 未运行当作轻量层次 policy 的负证据。HBKM/DPC 的 hub/base 几何层次同样不是以每 query 真实 action cost 训练的分支。

新的 query tree 若每 entry 只对应一个 leaf，节点是线性判别，单 entry 选择域是该路径半空间的交。它比由固定 prototype 内积诱导的球面 Voronoi 更自由，但仍不是任意不连通、多模态 action region。当前主方案明确允许同一 entry 多 leaf，可表达多个区域的并，但这只是函数类能力，不证明真实 utility basin 可学或树容量足够；其 leaf 数、深度、内存、推理路径和训练协议应冻结。非线性节点或树集成若另加，不得隐含在原点积成本声明中。

## 6. 哪些“新点”是已有先例，哪些才是可审查的实质改动

| 拟议表述 | 本地已有先例 | 本轮可以主张的边界 |
|---|---|---|
| 真实图搜索/可达性监督 | NETG custom probe；centroid/ranker native search | 必须明确 native 算法、动作、L、R10/NDC、保留哪些结果 |
| 离线重、线上轻 | NETG 离线 hub MLP、在线固定 embedding HNSW | 若非线性建模发生在 query 端并被蒸馏，才与旧 hub-only MLP 不同 |
| 全 H label | NETG 全 DPC hub；centroid 全当前 QGT hub | 新的完整代价向量与不截候选流程可以有区别；“全 H”独立不新 |
| 连续 utility/soft labels/hard-query weighting | sparse ranker、signed residual prototype | 必须说明为何新损失保留了旧池化/listwise/centroid丢失的信息 |
| 无 online probe | Fast、NETG、ranker、centroid、v2 atlas | 这是部署约束，非机制创新 |
| cost-first / feasibility + margin | v2 atlas 已实现 | 新 query 参数模型、分支加权或经验证的 teacher压缩才可能是实质差别 |
| 学 oracle entry 的分类器 | NETG hard label、centroid | 近似等价 action、代价差、失败样本、预算条件如何保留应具体写出 |
| query近邻存 utility | v2 atlas 64-NN | 与原失败流程近乎直接重复；新名字不能替代新信号 |
| 用 utility residual 修改 prototype | signed residual prototype | 直接重复；单纯更换 alpha/hidden width 无新机制证据 |
| 单入口 top-1 | centroid 已评估；v2 输出单入口 | 当前可作为最小动作，不是首次尝试或保证最优 |
| 成本加权 query 决策树 | 本次核对旧入口实现未见；P4未运行 | 可以列为本地未测试的候选函数类；外部已有 TAO/FilterTree/相关树方法必须引用 |

## 7. 对新设计的证据要求

1. 用与部署相同的 native `search_new` 生成 action-level Recall/NDC/时间边界；不要复用 L300/GT1/custom-probe 的 hard labels。标签和 graph 的版本、split、候选 universe 必须固定。
2. 保留近似 ties/连续 regret，失败或“不比 Fast好”的 query 也要参与；不要凭唯一 oracle-ID accuracy 判断可学习性。soft target 本身已有先例，需比较选中动作的真实代价差。
3. 若重 teacher 输入仅 query，才是在检验部署前可预测信号；若 teacher看 post-search trace/GT，只可作为特权信息上限，不能拿 teacher 成功证明 query-only student 可学。二者必须拆开。
4. 重 teacher→轻 student 应报告独立 pilot 的 teacher regret、student regret、两者差，以及最终与 Fast 的 graph/total/wall 成本。teacher成功、student失败可定位压缩；teacher训练集拟合成功不算泛化。
5. 旧 top-32/rank0/固定3 已有偏差边界。新完整 H 的单入口选择可以避免其候选限制，但全 H 离线开销要如实给出；不保证单入口是最终部署最优，也不恢复固定anchor。
6. 树深度和理论比较次数不等于实际 CPU延迟。query预处理、dot products、分支开销、任何候选检索、回退都须计入纯 wall；相比旧 precomputed route 评测，这是必须补齐的验收。
7. 相对本地旧实现的不同，不自动等于论文新贡献；相对外部成本敏感分类/TAO/FilterTree/learned ANN tree 的新机制和结果应单独论证。

这些要求是对新方案可被证伪和可比较的条件，不是实验已经获 GO 的结论。本审计不启动任何旧或新训练链。
