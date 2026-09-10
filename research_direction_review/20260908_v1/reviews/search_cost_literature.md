# 搜索成本与停止规则：两篇 NeurIPS 2025 论文复核

核对日期：2026-09-08。以下页码为下载 PDF 从 1 开始的页码。读了方法、主要实验和相关实现附录；这里的迁移判断是本项目推断，论文没有运行本地 ACSG。PDF、提取文本及 SHA256 在 `../sources/root_*`。

| 论文与一手来源 | 实际方法及证据 | 对当前计划的约束 |
| --- | --- | --- |
| [Distance Adaptive Beam Search for Provably Accurate Graph-Based Nearest Neighbor Search](https://proceedings.neurips.cc/paper_files/paper/2025/hash/904fe070f484231aa26dbdb37816cd40-Abstract-Conference.html)，NeurIPS 2025；方法 §3、定理 §4，PDF pp.4–8；实验 pp.8–10；实现附录 pp.24–25 | 保持按距离扩展的顺序，用当前候选距离与已发现第 k 名距离的关系决定停止。六套 Euclidean 数据，HNSW/Vamana/NSG/EFANNA；主要比较匹配 Recall 的距离计算次数。定理要求 metric 和可导航图；另一停止公式也满足定理，但实际表现更差。 | 支持先研究搜索过程和工作量分配；不支持把“目标区概率”直接当成容量。raw IP 不满足其理论前提，不能直接套乘法距离阈值并声称保证；NDC 节省仍需本地纯计时验证。理论成立也不足以推出实际成本收益。 |
| [Optimistic Query Routing in Clustering-based Approximate Maximum Inner Product Search](https://papers.neurips.cc/paper_files/paper/2025/file/0b2832072ff6df19e586c74e27d90f12-Paper-Conference.pdf)，NeurIPS 2025；方法 §2，PDF pp.4–6；实验 §3，pp.7–10 | 用分片内积的均值、协方差及低秩近似形成乐观分数。固定分片后以区内精确扫描隔离路由误差，再测 PQ 分片从 SSD/S3 读取的总体延迟。含 Text2Image 10M×200；收益依赖数据和存储，DeepImage 的扫描量及延迟反而上升。 | MIPS 路由仍有研究空间，但它控制的是要扫描哪些独立分片，成本与扫描量联系明确。当前跨区 NSG 的候选容量没有这种对应关系。论文的延迟实验也不能替代本地内存图搜索的端到端比较。 |

本地推论：应先把一个决策对应到可实测的搜索成本，再选择监督目标。`GT 落在哪些区`、`区内最大内积`、`继续扩展是否有收益` 是不同问题。后一问题并不因改了名字就成为新方法；它还须与已有搜索停止/困难度研究对照。

检索时先读了 Adaptive Beam 的 [arXiv v1](https://arxiv.org/html/2505.15636v1)，随后以上述正式会议 PDF 复核主要机制、数据、定理边界和实现。网页 PDF 的 P0 页标与本地页码相差 1。下载脚本遇到系统没有 `pdftotext`，保留错误记录；最终借用本目录已有 wheel 的临时 `sys.path` 读取 PDF，未安装或升级项目环境。提取文本存在旋转图和数学排版损失，结论来自可读正文；没有从损坏文本重建数值公式。
