# GT10机制分析的最小补测

2026-09-11。先完成[已有证据报告](../existing_report.md)、108点169152输出重评分及两数据集fit归属digest恢复，再固定本协议。用户本轮已授权对明确缺口冻结小协议与硬预算作最小补测。本版本只用于归因，不启动第一方向重跑或后续方法分支。

## 问题与三个固定诊断

1. **缺少WebVid GT10 hard重复wall。** 只补WebVid原validation前2000、两份冻结GT1/GT10 hard、L64/128/256/400/800；每点3轮独立全批warm/plain。原query顺序、W、H、M16/efC200/ef10、seed20260828、CPU15、原NSG/raw-IP不变。两方法按L/repeat轮换。L128两者各一次独立route-only和graph-only；分项不相加冒充QPS。Yandex复用E25/E26已有重复，不再补曲线。
2. **具体正点是否依赖HNSW近似。** 只在WebVid validation L64、Yandex validation L128，各对冻结GT1/GT10 hard做exact3诊断（各2000 query）；不报QPS，与E24同query HNSW原结果连接。这两个点按已观察到的局部正收益选来解释，属历史validation的事后诊断，不是新盲测或新选择。其它L没有新增exact证据。
3. **目标对应关系与一般支持/平滑混杂。** 每数据集恰好一个`tail_shuffle`。用PCG64 seed20260911的第一份20K行排列π，两数据集同一位置排列，不重抽、不调seed。令

   `a_shuffle(q,h)=0.1 1[b(q,1)=h]+0.1 Σ(j=2..10)1[b(π(q),j)=h]`。

   使用已有fit每rank归属（已与原digest匹配），不重选目标/hub。保留原query自己的0.1 GT1贡献，将另九个名次作为一组来自同一donor query。原unit query/单位raw-hub prior1、float64累加/归一化后float32输出不变。只在E24原cal[0,1024)、audit[1024,2048)的L128，用exact3与HNSW3各诊断一次。对照使用相同身份的原GT1/GT10输出，不给shuffle做validation或正式QPS，不把它选为新方法。

shuffle严格保留每rank全局hub频数、每hub总质量（实数意义，浮点容差1e−9）、每query总质量1、H、GT1的0.1项及tail内部名次组合。它**不保留**每query的GT1–tail重合、每hub squared mass/ESS、方向集中度、画像角位移或在线入口；不能称完全匹配控制。若真实GT10优于shuffle且shuffle ESS更高，只支持“边际质量或更大ESS不足以替代query–目标对应关系”，不证明GT10优于所有仅GT1平滑规则，不估计多目标与平滑各占百分之几。一个排列不作随机化显著性结论。

## 恢复与数值

独立复制E26的已验收GT-free Policy/原kernel wrapper和三次wall评测器；仅在新评测器放行已有Policy的exact3开关。原源码与库hash绑定旧E26保护记录，不改主工程。两数据集各用原cal前32，GT1/GT10×exact/HNSW、L128恢复，完整ID/距离bits/实际入口/hits/mask/route/graph NDC必须等于E24对应原输出。恢复失败停止后续，修复仍须保持协议定义。

GT1 float32恢复原W直接使用。已有float64数值控制max abs为1.19e−7/7.45e−8，在cal/audit/validation以float64重评分的精确top3均未改变；该只读数值证据不冒称另一份W的HNSW建图回归。本补测不把舍入控制加入模型选择。

## 线程、计时与保护

全部真实查询显式threads=1，OMP/OPENBLAS/MKL/NUMEXPR=1、dynamic=false、taskset CPU15，进程监控实际线程1。一次一个方法；计时期间不并发分析/编译/训练/其它性能作业。控制器仅监控/记账。离线新画像构建可8线程，须在查询前完成。

端到端timer含raw query路由、真实ID映射/排序、原NSG与预分配输出。GT、count/trace、hash、JSON、建图/加载均在timer外；每个点全批plain/count比对，前16query与原wrapper比对，三轮返回bits相同。无trace补测，不声称观测到路径长度或cache变化。GT在全部raw输出后由评测层读取；不开held-out、不生成训练标签。

只写supplement目录。输入、模型、源/库、配置、binary、原报告hash在第一次真实调用前冻结；拒绝已有输出。原资产保留，失败按完整预留计账，不能重启扩大预算。

## 硬预算

诊断point为2N+16次原NSG调用；三次wall point为7N+16；L128分项额外2N。

| 项目 | 计算 | 真实调用 |
|---|---|---:|
| 恢复 | 2数据集×4点×(2×32+16) | 640 |
| tail_shuffle | 2数据集×2段×2后端×(2×1024+16) | 16512 |
| 局部正点exact3 | 2数据集×2画像×(2×2000+16) | 16064 |
| WebVid硬画像五L三次wall | 2画像×5L×(7×2000+16) | 140160 |
| WebVid L128分项 | 2画像×2×2000 | 8000 |
| **正常总上限** | | **181376** |
| 仅完整恢复阶段的身份修复预留 | 不用于性能或候选追加 | 640 |
| **真实调用硬上限** | | **182016** |

无新增合成搜索。单job≤1200s，全部查询进程累计≤1800s，RSS≤40GiB，本补测目录≤512MiB，/data剩余≥10GiB。每次预留前检查，运行中监控资源，触限停止并保存partial；没有自动加预算。计划共9个job：两恢复、四shuffle、两exact、一个重复wall。

## 交付与收口

保存原始返回、全部计时轮次、计数、恢复/独立评分、shuffle支持变化、每query连接和完整资源账；正负结果全部报告。分别回答具体正点的exact/HNSW机制、支持与对应关系证据、WebVid重复速度幅度。未区分项原样保留。补测结束即收口，不扩seed/L/query/温度、不开held-out或2A/3A/聚类/rank。
