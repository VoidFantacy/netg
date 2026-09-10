# A+B 低秩槽位路由完整实验 v1

冻结日期：2026-09-09；依据用户“完整推进实验，报告相对 Fast 的 QPS、Recall、查询失败率”授权。研究依据为相邻 `20260909_ab_readonly_research_v1/report.md`，不重启已停止的 C。CPU only，原 base/raw IP/冻结 NSG/`search_new(mode=2)` 保持不变。

## 数据、重复与隔离

- WebVid2.5M 与官方 Yandex first10M；K=10，分别训练 L=64/128。
- 三个独立 QGT 构建种子 20260828/29/30，复用经 hash 核验的各自真实 hub 集；所有种子用相同查询。种子影响 hub/prototype 构建，不仅是优化器重启。
- fit：router_train 行 [10000,30000)，20K；校准：[0,1024)；冻结后 audit：[1024,2048)。这都是历史开发池，audit 仅对本次拟合隔离，不能声称项目从未使用。
- 每种子 paired Fast20K 按原 closed-form builder 重建；另保留已有 Fast30K 作为实际历史强基准，明示训练量不同。主配对对照 Fast1/Fast3 均为 direct k=1/3，不能混用 E20 top8 前缀。
- 完整标注三个 H 的并集，查询×入口×L 的搜索结果与种子无关，按每种子的列索引取回；并集只共享标签计算，不扩大任何模型可选动作集。
- 样本外完整 validation10K 与 held-out public10K 在模型冻结后才开放；不用于新增配置或训练。Yandex 只评价 public100K 的前10K。

## 方法与预先固定的训练配置

每种子、每 L：W=P0+VZ，rank=8，V 列正交，||Z||F<=0.5*sqrt(H)，pi:slot→该种子真实 hub。无 bias，不归一化学习后的向量。初始化 V 为固定种子的高斯 QR，Z=0，pi=identity；exact tie 取原真实 hub ID 最小的 slot。

四个因素对照：exact Fast1、仅 W（pi 固定）、仅 mapping（W 固定）、联合 W+mapping；同时保留先 W 后一次 mapping 的分阶段对照。连续更新以 full-H hitcount 的 soft expected regret 作为辅助目标，按原 hard total hits 验收。全部 Recall ties 保留；全相同效用行梯度为零且留在分母中。映射按到达该槽的查询对每个 H 动作总 hits 最大化，平局保留旧动作，然后 real ID 最小，空槽保持原映射。

tau0=max(fit 上 Fast exact top1-top8 gap 中位数,1e-6)。温度 [1,.3,.1]*tau0；每温度最多20轮，每轮最多5个proposal epoch，batch=512，SGD lr=0.05，无动量；最多5次按0.5回退。梯度全局范数裁剪1。每proposal QR重参数化保留乘积后限制Z半径。hard hits 增加，或相同 hits 且 soft regret 下降才接受；每温度连续3轮无接受则停。候选检查点只由预定校准集 exact utility 选择，ties 先较少变化/较早检查点；始终记录原 Fast checkpoint。

连续提案是局部非凸优化，不承诺 generalization。主要部署候选为联合模型中校准最优的新检查点；另报告包含 Fast fallback 的校准选择结果，不能把回退后的 Fast 说成新方法提升。

## 标签正确性与上线

标签 runner 调用原链接库，graph search 函数不接收 GT，搜索返回后评分。保存按 query ID 对齐的 uint8 hitcount、uint16 GT10 hitmask、uint32 graph NDC；留少量完整ID用于独立重放。先做合成 kernel/plain/count parity 和两真实数据集多行、多入口、多 L parity，再进入完整标注。逐块落盘与独立进程日志；不得用标签过程 wall 换算QPS。

离线折叠 W，Micro-HNSW 原维度、M16/efConstruction200/ef10；唯一 slot ID 作索引 label，另表映射 real ID，避免重复 real label 合并槽位。基准使用原真实 hub label。Z=0,pi=identity 的 exact 与原基线一致性必须验证；HNSW实际一致性单独报告。保留 baseline 后端。

## 指标、计时、判定

- Recall@10 平均；失败率严格 Recall@10<0.1，等价 hits=0。命中1个不失败。依据用户澄清和 `benches/run/plot_final_paper.py` 的 THRESHOLD 与严格小于。所查本地 `ACSG/NETG_XM_KDD2026_ (5).pdf` 草稿未明示此阈值，其实验主要使用R@100/R@1，不能称PDF已确认。
- 相对每个Fast基准：QPS百分比变化、Recall pp与相对变化、失败率 pp下降及相对下降；Fast失败率为0时相对下降记null。配对报告 rescued/newly_failed 及全查询Recall gain/harm，所有查询留在分母。
- 单独 count pass 报 route/graph/total NDC。plain full-batch wall 计入路由、映射、原图搜索、正常结果写入预分配输出；排除GT、hash、JSON、计数、装载和建索引。独立 route-only 与graph-only batch仅诊断，不用其相加替代端到端wall。
- 16线程统一；每配置 warmup 后3次测量，方法顺序轮换，三构建结果分别给出并汇总。不与标注/训练同时计时。
- query配对 bootstrap 10000次，跨种子按相同query联合重采样；四 dataset×L 主比较作Bonferroni校正，种子变异另列，不把90K当独立查询。
- 新方法若四点Recall均≥Fast3且至少一点有显著提升，同时同L实测端到端QPS无下降，可记该冻结范围的Pareto改善；不满足就逐点报告收益/损失，不包装成总体GO。不以相同L或NDC推出QPS。
- 质量gate失败不会省略用户要求的最终比较：冻结当前候选后仍完成这组有界benchmark以给出完整负结果；不扩大rank/H/ef、切换树、追加数据来救场。

## 资源与产物

只写本目录及同步四份根文档和历史记录，保留全部旧数据。free disk底线10GiB，available RAM底线12GiB；一次一个重计算进程≤16线程，CPU only；超过阈值安全停在当前块并保留日志。先运行一分钟观察实际吞吐估算时间。label输出不保存完整N×H×10 ID立方体。标签/训练/评估各阶段写manifest、hash、状态和命令。最终交付report.md、JSON/CSV逐点比较、图和所有配对明细。
