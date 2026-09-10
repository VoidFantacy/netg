# P3 结果解释与归因边界（v1）

记录时间：2026-09-07T17:57:48.614229+00:00。只读审阅已保存 protocol、四模型汇总、门户复核和结构分析；没有读取实际 query/GT/base/graph、重跑 ANN、修改模型或执行下述新诊断。

P3 的必要结构条件通过，搜索传递条件失败。WebVid 在 frequency3 和 greedy3 两套门户规则下，λ1 均降低 oracle 概率区域池的 Recall；Yandex 的对应结果尚不能区分小幅正负变化。这个结果否定本轮“结构训练目标下降即可带来固定搜索配置收益”的预期，不等于否定所有区域保护方法，也不构成进入 P4 或辅助图的依据。

以下全部是固定 10K development pilot、K10、L64/128 的普通配对查询 95% 探索区间；不是 validation/held-out，也没有成本匹配后的部署性能结论。

| 数据集 | L | λ1−λ0，frequency3（pp，95%区间） | λ1−λ0，greedy3（pp，95%区间） |
|---|---:|---:|---:|
| WebVid | 64 | -0.971 [-1.188, -0.756] | -0.866 [-1.083, -0.647] |
| WebVid | 128 | -0.863 [-1.033, -0.693] | -0.790 [-0.960, -0.621] |
| Yandex | 64 | -0.043 [-0.137, +0.052] | -0.095 [-0.207, +0.016] |
| Yandex | 128 | +0.038 [-0.021, +0.097] | -0.017 [-0.080, +0.048] |

训练结构证据本身成立：λ1 相比 λ0 的平均 fit GT10 跨叶区域数，WebVid 4.33285→2.60275，Yandex 3.00925→1.96480；J(λ=1) 分别下降 0.18838、0.11486。与此同时，原图叶区 cut fraction 分别上升 0.003856、0.001187。J 是将目标集中程度与边界切割相加的训练目标；它没有直接约束从门户出发的有限预算搜索覆盖、访问次序或非 GT 桥接节点的保留。

**2×2 能识别什么。**

| 比较 | 固定部分 | 实际一起改变的部分与允许解释 |
|---|---|---|
| 同一 λ：greedy3−frequency3 | 标签、候选集合、预选 fit 查询、oracle 活跃叶区及概率、搜索代码和 L | 有序门户三元组及其带来的入口去重、搜索轨迹/计算量；可判断这一门户选择规则的整体替换效果，不能分离“节点身份”和“入口次序”，也不是等 NDC 对照。 |
| 同一门户规则：λ1−λ0 | 共同初始分区、规则定义、种子、portal 数上限、pilot 查询、原 NSG、K/L | 最终标签、fit GT 频次归属、候选门户身份、eligible fit 查询及 hash 选样、选中门户、oracle 选区/概率和队列容量均可能改变。识别的是整套 λ 分区及重新制备门户流程的效果，不能称为只替换标签的消融。 |
| 同一模型：oracle_probability−oracle_unified | 实际入口、标签、oracle 路由、共享结果/visited、K/L | 区域队列容量与调度共同改变，也改变扩展数和 NDC。可判断固定入口下的队列干预；不能把额外探索排除后单独归因给保护。 |

固定频次对照在 WebVid 也显著退化，说明失败不能仅归咎于 greedy 规则。它仍未排除 λ 导致的候选门户重选、oracle 选区变化或其他搜索交互。两种 λ 不是同一批节点的恒定区域实体；规范编号未变不代表成员未变。λ1 还增加 GT 共现目的区域候选，因此“仅增加目标函数权重”的归因也过窄。

所有 16 个模型内保护对照均显示正 Recall 区间，但付出更多 NDC，QPS 均值比约 0.708–0.855。这保留了固定图上的区域队列机制证据，不能挽救失败的 λ 结构搜索传递 gate。跨模型计时采用固定模型顺序，仅作描述，不能由近似 QPS 或相同 L 宣称匹配成本。

**代理覆盖增加与联合搜索没有明显增益并不矛盾。** 下表的 support 是选定 `(fit query, 目标 GT 排名, 所属叶区)` 的可命中目标数；leaf-query pairs 可跨叶重复同一查询，不是独立样本。

| 数据集/λ | 已选 leaf-query pairs | target support | frequency→greedy 缓存 union hits | 同门户集合叶区数/256 |
|---|---:|---:|---:|---:|
| WebVid/λ0 | 28,876 | 62,511 | 46,358→48,274（+1,916） | 4 |
| WebVid/λ1 | 22,066 | 82,277 | 60,006→62,235（+2,229） | 8 |
| Yandex/λ0 | 30,300 | 102,693 | 88,507→90,313（+1,806） | 5 |
| Yandex/λ1 | 26,829 | 137,395 | 116,349→118,357（+2,008） | 4 |

在同一 λ 内，frequency 与 greedy 使用同一批候选、查询和目标，缓存覆盖增益可直接比较；但选择本身就在这些 fit 掩码上进行，只证明训练代理改进。每分支仍有 1–4 个叶区的 greedy 覆盖低于 frequency，算法没有逐叶必胜保证。跨 λ 的 support 和选样集合明显变化，不能把 raw hits 的大幅增加当作质量提升；即使除以 support，也没有消除查询与目标组成变化。

| 数据集/λ | greedy−frequency，L64（pp，95%区间） | L128（pp，95%区间） | Recall 相同查询比例 L64/L128 |
|---|---:|---:|---:|
| WebVid/λ0 | +0.044 [-0.125, +0.213] | -0.018 [-0.130, +0.093] | 76.33% / 85.98% |
| WebVid/λ1 | +0.149 [-0.017, +0.316] | +0.055 [-0.060, +0.168] | 77.19% / 86.93% |
| Yandex/λ0 | +0.039 [-0.070, +0.144] | +0.024 [-0.043, +0.092] | 86.60% / 94.42% |
| Yandex/λ1 | -0.013 [-0.117, +0.091] | -0.031 [-0.090, +0.030] | 87.29% / 94.58% |

八个门户替换区间都包含零，不能宣称等效或完全无效。`query_equal` 只表示 GT 命中个数相同；它没有证明返回节点相同、入口相同或搜索轨迹相同。门户集合大多发生变化也没有证明每条 pilot 查询使用到发生变化的叶区。

训练代理把三个相互独立的“单入口、无 Fast/default、统一池、L32”搜索的目标命中做集合并集；真正评估则把最多 12 个门户与 Fast anchor/default 一起放入共享 visited、共享全局 top10 的联合搜索，并在 L64/128 使用区域队列。单入口并集没有支付联合搜索中的相互替代、路径顺序和预算竞争。训练拟合乐观、pilot 叶区曝光不同、联合搜索冗余与 L 改变都是尚未分离的解释。

**建议仅一个可证伪的既有证据诊断：固定 λ 的“代理增益是否被联合查询实际使用”审计。** 本次未执行，须先由 root 冻结方案；仍使用全部固定八个门户对照，不挑数据集、叶区或 L。

1. 从现有 verification 取每叶 `g_r=(greedy_union_hits−frequency_union_hits)/eligible_target_support`；零 support 单独标记无证据。从已存 pilot evaluator 行读取活跃叶区、oracle 权重、实际有序入口、返回 top10 和 Recall/NDC；不读取原始向量/GT/图，也不运行 ANN。
2. 对相同 pilot query ID 配对，以该查询固定 oracle 权重计算 `x(q)=sum_r weight(q,r)*g_r`，记录实际有序入口是否改变。预先固定 `x<0、=0、>0、含无证据叶区` 分组；无证据组优先单列。对入口改变且 x>0 组，报告平均联合 ΔRecall、正/负/相同 Recall 数，以及有序返回 ID 和无序返回集合真正相同的数量；总量覆盖全部 10K，不把相同 Recall 等同于相同返回。
3. 要检验的方向性假设是：正代理增益被 pilot 实际使用且入口改变时，联合 ΔRecall 均值仍应为正。若这组均值不正，便直接反驳“缓存代理增益在已曝光查询上传递”的描述；若该组为正而曝光极少，则优先支持曝光不匹配的解释；若高曝光仍主要相同返回，则联合搜索冗余是更具体的后续假设。分组结果只作已有证据诊断，不新增性能 gate，不据此调参。

这个诊断不能完全区分训练样本乐观与独立单入口代理对联合搜索的错配；没有同一查询上的两种搜索设置反事实，不能作更强归因。若没有足够既有 per-query 字段就记录缺失，不能偷偷补跑。

**辅助图目前没有触发证据。** 父协议要求“正确区域/门户仍有连接瓶颈”。Oracle 只给真实 GT 叶区质量信息，不证明选出的门户已经正确或充分；单入口 L32 未命中也不能证明图上不可达。当前没有在已证实门户质量、固定入口/区域/预算后定位到缺边的证据，更没有对候选边、几何等边数对照和额外计算成本的验证。P3 失败只能保留负结果与上述代理传递假设；不能直接进入辅助图、P4、validation 或 held-out。

证据文件（本次读取的汇总/元数据 SHA256）：

- [protocol.json](protocol.json): `fea64bc3c6a8046378849f55508198dcfd9a00df880a74e9d93cf22d051a418f`
- [analysis_v1/analysis.json](analysis_v1/analysis.json): `63da6a71425b0dbd6e186db1c608a564b9847c58168b6b56059a9ed2d2f901ae`
- [structure_analysis_v1/analysis.json](structure_analysis_v1/analysis.json): `8b0cec717a14382c5917504e560bcffd732146c517ea9a699b0bb1812463088e`
- [models/webvid2_5m_light_v1/lambda0/verification.json](models/webvid2_5m_light_v1/lambda0/verification.json): `0c3f5610ee27723045da645e6295f0fe9c18408ac6561c3e7e2e05943668d033`
- [models/webvid2_5m_light_v1/lambda1/verification.json](models/webvid2_5m_light_v1/lambda1/verification.json): `2329594de0a72d9eac433d21fee7656ddc0d1513be5ee1ba09f6835bdc7c75b1`
- [models/yandex_t2i_official10M_ip_v1/lambda0/verification.json](models/yandex_t2i_official10M_ip_v1/lambda0/verification.json): `5f306373f208377361efda41acee86d64abd616df22cdc00184f77b459e37a23`
- [models/yandex_t2i_official10M_ip_v1/lambda1/verification.json](models/yandex_t2i_official10M_ip_v1/lambda1/verification.json): `f38a098473ca73eabd3725b53ab55be0643342cac0fa3681c9225fc30942a4e9`
- 辅助图触发契约：父目录 `protocol.json` 的 `failure_actions.connectivity_bottleneck_with_correct_regions_portals`；项目 `s-target.md` 第 5 节。
