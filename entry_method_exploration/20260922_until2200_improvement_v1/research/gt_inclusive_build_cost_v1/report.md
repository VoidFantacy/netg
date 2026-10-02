# GT10入口层从训练GT起算的构建成本

2026-09-22，**CURRENT_GT10_REBUILT_WITH_GT_COST**。当前Web GT10-soft-t1 / Yandex GT10-hard的真实H、画像与小图全部恢复；没有修改默认，也没有新线上性能结果。

## 一次完整、固定配置的重建

沿用原base/raw-IP、QGT5K query和画像20K query，重新计算exact top100，随后按原seed20260828、25轮选H、原GT10归属与prior1构造画像，最后用原hnswlib、M16/efConstruction200/seed20260828/ef10串行重建Micro-HNSW。所有输入均为原训练角色，没有打开新测试来源。

| 阶段（秒） | WebVid | Yandex |
|---|---:|---:|
| base加载及Flat建立 | 6.0537 | 9.3790 |
| QGT5K exact top100搜索 | 82.8223 | 352.8323 |
| 画像20K exact top100搜索 | 312.8617 | 1417.2928 |
| QGT真实H选择 | 0.3652 | 0.1767 |
| 目标归属及画像 | 1.8388 | 0.5057 |
| Micro-HNSW构建 | 0.0552 | 0.0452 |
| 上述不重叠核心阶段合计 | **403.9967** | **1780.2319** |
| exact GT占核心阶段 | **97.94%** | **99.43%** |

核心阶段合计约6.73/29.67分钟，排除阶段外校验与I/O。GT/H/画像完整dataset过程为404.378/1780.634秒，后续router过程（含2.5万对路由核验）为0.466/0.253秒。整个双集GT重建脚本2185.114秒，峰值RSS15.338GiB；不要把包含关系的计时再相加。编译、前件试建和独立审计保留在各reviews，均不冒充模型核心构建时间。

这不是最小可能标签费用。为与历史账本完整核验，本轮生成top100，而现有GT10画像只消费前10；没有寻找最佳批大小、并行度或更快GT算法。费用从已有向量和固定训练query开始，排除下载、嵌入提取、公共底层NSG构建及历史方法/温度选择成本。

## 计算环境与费用解释

Python3.10.12、Faiss1.15.0，CPU集合0–7；OMP/BLAS/MKL每池上限8。进程有15个驻留线程（不同线程池），CPU亲和限制为8个核，不能称实际仅8个进程线程。Faiss报告8，OMP动态关闭、最大active levels为1。未主动清缓存，不声称冷启动或生产硬件上的固定成本；这是单次固定配置测量，不择最快重复。

user CPU16878.328秒、system CPU29.303秒为整个GT重建进程，不能与单线程查询wall混为一谈。GT标签阶段和正式查询评测串行。本轮没有NSG或完整QPS测量。

## 一致性核验

5万条新GT的全部top100排名、集合和top10均与旧GT一致，合法性、唯一性、有限分数和排序全部通过。两集新H及float32画像与当前默认逐位相同；Web soft完整质量矩阵SHA也与原件相同。

小图比较所有节点层级、入口、真实标签、向量字节及各层有序邻接；随后各集QGT5K+画像20K的旧/新路由共5万对，heap真实ID、距离bits和NDC均一致，即10万次ANN调用。原图二进制未使用槽位可能含不同padding，故核对语义结构，不声称整文件SHA相同。

独立Python审计不导入重建器，重新比较全部GT/H/W，并按原hnswlib序列化格式解码两对图，排除padding后完整一致；0.176秒，32份消费/冻结小文件身份保持。大base核对stat，原生没有读取或修改底层NSG；未新增全base SHA。原始GT、画像、图及默认全部保留。

## 结论

GT10把较昂贵的一次性监督压缩成便宜在线表示，这是强项之一；“画像几秒”本身不足以描述其总构建成本。若转向降低离线费用，主要优化空间在GT获得阶段；但还没有实测任何廉价标签方案能保住完整Recall–QPS，不能直接宣布成本优化成功。

证据：[冻结协议](protocol.md)、[前件](reviews/preflight.json)、[GT重建与资源](reviews/rebuild_complete.json)、[小图完成](reviews/router_complete.json)、[完整成本表](results/cost_summary.json)、[独立审计](reviews/independent_audit.json)。`rebuild_complete.json`的ROUTER_PENDING是该进程退出时的历史状态，最终完成须联合读取router_complete及cost_summary，原件不回写。
