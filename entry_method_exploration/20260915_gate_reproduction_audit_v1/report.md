# GATE 复现检查与下一轮方法选择

2026-09-15。按用户补充要求，以核心机制正确、合理适配和公平计量为标准，不要求与存在缺陷的作者代码逐行一致。本轮只审源码、冻结结果、训练缓存及合成前向；没有新训练、ANN、构图、GT 或 QPS 测量。

**结论：GATE 的主流程实现基本合理，可以保留为项目内同图适配基线；发现一个应在后继版本修正的正负标签冲突。无需为了论文/代码差异推倒重做，但当前版本不能标为“完全无问题”。新三集建议统一以 GT10-hard 为主方法，soft-t1 留作预先固定的辅助对照。**

## 1. 实际核验结果

- E96 的 40 项源码/受保护依赖 SHA 与正式测试前记录一致；192 个点、576 轮的 QPS 与保存 wall 的算术关系通过。本轮没有重跑性能，也没有重读完整测试 GT 来重复 E96 的逐返回评分。[身份与计时核验](results/identity_and_timing.json)
- 三个最终 checkpoint 与已冻结 SHA 一致，重新前向导出的单位 W 与线上文件一致，最大绝对误差不超过 7.46e-8；单条/批量前向一致性通过。所有 triplet 的查询都来自训练前 10000 行；标签的有效 hop 与对应返回确为 GT1 的关系逐项通过。[缓存核验](results/cached_checks.json)
- 训练 loss 都下降，最佳 checkpoint 选择可以由历史记录重算。没有证据表明训练未执行、模型接错或导出失效。
- 当前使用真实 hub、WL+Doc2Vec 拓扑特征、真实 NSG 首次发现路径监督、对比训练、静态 embedding 小 HNSW 三入口。这保留了 GATE 的主要设计。[E96 源码](../20260914_gate_new_ood_v1/src/train_gate.py)

## 2. 确认的标签冲突：下一版应修

`release_samples` 先把每 query 的最小 hop hub 设为正样本；构造负样本时，把失败 999 改为 -1，再逐步降低成功 hop 阈值。在成功入口较少时，负样本集合会包含正样本，且可以通过 10–500 个负例的过滤条件。这一规则来自[作者发布代码](https://github.com/jacksondca/gate/blob/229f18dadb791ddede22597e44d5ceb028b104ba/cluster/experiment/combine_ep_gt.py)，本地没有排除交集。

最小复现：512 个入口中，仅 10 个成功且 hop 均为 1，其余失败。原函数把这 10 个入口同时当作正例和负例。这是语义冲突，不能因为沿用作者代码就忽略。[可运行检查](src/check_label_overlap.py) · [完整结果](results/label_overlap_verified.json)

| 数据集 | 存在冲突的训练 query / 10000 | 实际抽样 triplet 中负例也属正例 | 占全部 triplet |
|---|---:|---:|---:|
| WebVid | 875 | 2525 / 624350 | 0.4044% |
| Yandex | 449 | 1783 / 714600 | 0.2495% |
| LAION | 799 | 2630 / 707750 | 0.3716% |

其中正负 query 完全相同的 triplet 分别为 57/30/62，共 149 个。更广的冲突包含不同 query 的配对：一个 query 对该 hub 同时收到拉近和推远的监督。实际抽样占比不足 0.5%，没有证据将全部性能差距归因于此，也不能预测修后收益。

最小修正是 `neg(q) = old_neg(q) - pos(q)`，再做可用性过滤和 triplet 构造，并断言每 query 的正负集合互斥。只要 query/hub/图/kernel/metric/L 身份不变，已有 hop 缓存可复用；triplet、模型、embedding 和受影响评测必须在新版本重新生成。当前 E96 原件未修改，本轮没有执行这个修正的重训练。

作者 dataset 代码还有把 `ep_id` 与 `dummy_query_ids` 比较的类型语义错误；本地按 query 可用性过滤，未照搬该错误。[作者 dataset](https://github.com/jacksondca/gate/blob/229f18dadb791ddede22597e44d5ceb028b104ba/cluster/model/train/dataset.py)

## 3. 合理适配与需保留的局限

| 项目 | 核对结果与判断 |
|---|---|
| 聚类 | 论文为带规模惩罚的 HBKM，发布代码为两层普通 k-means，本地为 32×16 Sinkhorn 平衡近似。都在做分区后选择真实 hub；按本次要求可接受，不能声称逐算法相同。 |
| Transformer 维度 | 作者默认 sequence-first，却输入 batch×2×d；合成例证实一个 hub 输出会受其他 hub 影响。当前修正为 batch-first 是必要修复，不应为复刻错误撤回。 |
| 损失与训练设置 | 当前 cosine triplet、Adam 1e-5、batch16384 接近发布训练脚本/README；论文写的是另一套损失与设置。选定一套合理实现并披露即可。 |
| 监控与提前停止 | 作者 infer 在训练模式调用模型，并使用距最小 hop 至多 1 的比例；本地用 eval 模式、独立 monitor 的严格最小 hop 准确率及 patience20。更可重复，但监控代理不等于最终 Recall。 |
| 同 hub 共享前向 | 保留每个 triplet 的损失权重，但共享 dropout，改变训练噪声相关性。CPU 适配可接受，不是逐 triplet 随机前向的严格等价实现。 |
| 子图截断 | 最终三集各 512 个子图，**全部达到 1000 节点上限**。5近5远仍保留，实际拓扑被截断。是实质的信息限制；当前没测取消上限的影响，不能宣称影响很小或它造成性能退化。 |
| 搜索内核 | 作者从入口 BFS 填满初始 L 个候选，再进行搜索；本地只注入前三入口，调用项目统一 kernel，标签也在同一 kernel 下生成。作为同图入口方法比较是自洽适配，不对应作者整套搜索器的直接复现。 |
| 查询端 | 发布实现本就以 raw query 对 learned hub 做 cosine 路由，没有额外神经 query 塔；本地没有漏掉必需的线上 MLP。 |

依据：[论文方法与设置](https://arxiv.org/html/2506.15986v1)、[发布 README](https://github.com/jacksondca/gate/blob/229f18dadb791ddede22597e44d5ceb028b104ba/README.md)、[fusion](https://github.com/jacksondca/gate/blob/229f18dadb791ddede22597e44d5ceb028b104ba/cluster/model/train/fusion.py)、[train](https://github.com/jacksondca/gate/blob/229f18dadb791ddede22597e44d5ceb028b104ba/cluster/model/train/__main__.py)、[infer](https://github.com/jacksondca/gate/blob/229f18dadb791ddede22597e44d5ceb028b104ba/cluster/model/train/infer.py)、[作者搜索初始化](https://github.com/jacksondca/gate/blob/229f18dadb791ddede22597e44d5ceb028b104ba/src/index_nsg.cpp#L618)、[下载身份](sources/manifest.json)。

这些差异不自动构成重跑 E96 的理由。实际冲突标签应修，子图截断和统一搜索内核应明确写入基线名称/说明；先不增加一整套结构、损失、温度网格来追论文数字。

## 4. 训练是否有效：缓存中的正反证据

只在已有 1024 条 monitor 上，对 raw-hub cosine 选一入口与 learned embedding cosine 选一入口查原 L64/K1 标签。没有执行新搜索。

| 数据集 | 最小 hop 入口准确率：raw → learned | 缓存单入口 GT1 成功率：raw → learned |
|---|---:|---:|
| WebVid | 11.39% → 7.12% | 63.48% → 66.02% |
| Yandex | 16.22% → 9.75% | 84.38% → 85.35% |
| LAION | 13.15% → 5.94% | 66.70% → 68.95% |

第一列仅在可用 monitor 行上算，分母分别 843/1005/859；第二列均为完整 1024。模型在最短 hop 代理上差于几何入口，却在能否找到 GT1 上略好，不能简单叫作“完全没学到”。同样，这些数值不是部署三入口的 Recall@1，不是新性能点，不用于重新选择现有 checkpoint。证据来自 [cached_checks.json](results/cached_checks.json)。

## 5. GT10-hard 还是 soft

**新 Deep/SIFT/GIST 统一主方法推荐 GT10-hard；soft-t1 作为预锁的一份辅助对照。** 这是简洁、可重复的起点选择，不是未经测试就断言 hard 在新数据集最好。

hard 将每个 GT 目标分给一个 hub；soft 按相似度和温度分给多个 hub。hard 没有温度选择，归属容易解释，适合三套新数据、两种新评测 K 的统一主线。soft 可能平滑边界和低支持画像，也可能稀释区分度，两者在线画像规模相同，并非 hard 天然具有明显的查询成本优势。

旧 E24 的校准选择是 WebVid soft-t1、Yandex hard，hard/soft 后续结果互有高低；E96 的 LAION 以旧 Recall@10 校准选 soft-t1，仅多 12 个命中。这些不证明 soft 在新 L2 数据或 Recall@1/100 更好。旧 Web/Y 默认与 E96 封存结果保留，不按此次建议回改。[E24 原结果](../20260910_gt_topk_profiles_v1/report.md) · [历史复盘](../../experiment_history/13_gt_topk_profiles.md)

如后续要逐数据集选择最佳变体，只在独立开发集按预先确定的 Recall@1/100 规则比较 hard 与这一个 soft-t1；正式测试前冻结，不按测试结果或按 L 拼赢家，不追加温度网格。本轮没有执行该比较。

GT10 的 10 是训练归属使用的真近邻数，和评测返回 K 独立。以后不测 Recall@10，不要求把 GT10 方法改名或改成 GT100。

## 6. 新数据集接入检查与新指标合同

当前旧 settings 的 Deep/SIFT/GIST 全部把 QGT/训练/测试查询指向同一个文件，不能直接用来声称泛化。规范 `indices/<dataset>_index/acosp_nsg.json` 路径均不存在；不能用残留图片或旧结果代替索引身份验收。

| 配置名 | 文件头与长度核对得到的 base | 当前查询数 | 主要待处理项 |
|---|---:|---:|---|
| deep10M | 10000000×96 | 10000 | 独立训练来源、L2 图/GT 身份 |
| sift10M | **11164866×128** | 5000 | 名称并非实际 10M；选择完整库或确定子集后核验相应 GT；独立划分 |
| gist1M | 1000000×960 | 1000 | 可另查已有 learn 来源；训练/测试独立划分及 L2 图/GT 身份 |

本轮只读目录、配置和文件头/长度，未验证这些完整 base 的每行格式、来源或 GT 正确性。详细范围见 [dataset_readiness.json](results/dataset_readiness.json)。不应凭现有文件名承诺三个数据集已经准备完毕。

后续主图检索保留数据集原 L2 度量；GATE/GT10 的 cosine 画像路由是独立方法层，不能通过把全库单位化并换 IP 来冒充原 L2 benchmark。现有 E96 native evaluator 强制 IP 且固定返回 K10，不能只换文件路径复用。

从本次用户指令起，新开发选择和正式比较只测 **Recall@1 与 Recall@100**，各自用 K=1/K=100 的真实返回与对应完整端到端 QPS，分别计时。Recall@1 是返回第一名命中 exact GT1；Recall@100 是返回 top100 与 exact GT100 交集数/100。所有方法相同 K、查询和线程条件，L/ef 不低于 K，K100 的预算点从至少 100 开始。旧“GT1 在返回 top10 中出现”不是 Recall@1，旧 K10 结果不能直接补成 Recall@100。历史 Recall@10 数据不删除或重命名，新表不再新增该指标。

执行顺序建议：先在新版本排除冲突标签并完成上述数据/metric/K 接入，再冻结 GATE、GT10-hard、NSG、全量 HNSW 的协议；soft-t1 仅预锁辅助项。当前按“先检查并告知”完成审查，未启动 Deep/SIFT/GIST 训练或性能测试。
