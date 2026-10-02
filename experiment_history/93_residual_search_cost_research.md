# E100：E99 后的剩余搜索成本与库使用核查

2026-09-16完成。用户要求研究为何距离次数少但速度慢，并追问 NSG 是否可以直接使用库。本轮先将 E99 代码和结果 Git 备份至 `7d09367e`，再在独立目录诊断；生产代码和原结果不改。

固定 WebVid 原 10K 公开 query、GT10-soft 与完整 HNSW、K100/L1250，CPU15/单线程/串行。优化内核 warmup、分项、SIGPROF 共 60000 search，独立插桩副本 20000 search。全部返回 ID/距离 bits/入口及计数轮逐 query NDC 与 E99 一致。诊断含加载 311.089 秒，峰值 RSS 15.88 GiB；另有 16384 对 scalar/batch4 比较、全图尾部 padding 只读审计，均无 ANN。没有新训练、图、GT、正式 QPS 或未曝光 held-out。

E99 正式高预算点 GT10/HNSW 分别 12664/13986 次距离、3.719/3.540 ms；GT10 次数少 9.45%，但总 wall 均摊每次距离成本高 16.05%。当前 NSG 每 query 检查 80398 个邻接槽，是 HNSW 实际邻接访问的 3.095 倍；其中 57744 个即 71.82% 为无效槽，未进入距离计数。全图 2505000 行均为有效前缀与连续 -1 尾部，无内部空洞；可研究保序 span 优化，但空槽比例不等于可节省时间。

优化后新采样的距离区域为 63.94%/75.01%，图循环/visited/预取附近为 26.98%/16.95%；不能沿用 E98 的 77.3% 作为当前 GT10 占比。样本包含访存等待和指令位置偏移，不是硬件 cache-miss 测量。路由只有 18.795 us、约 0.50%。候选逻辑复制约 15.29 MB/query，不是 DRAM 字节。16384 对 batch4 数值 bits 全同，仅支持有限数值可行性，未测其速度或全查询替代。

源码确认：项目已链接 Faiss，build_type=1 调用 `faiss::IndexNSG` 后复制邻接并作项目整理/连通性处理；在线由项目 `search_new` 支持最多三入口和 trace。当前实验“NSG”是同一项目内核的固定单入口控制，不是独立原生 Faiss NSG。原生版本初始化会以入口邻居和随机点填满 L，与当前最多三入口不同，且本地原生实现也扫描固定 graph.K。库存在，换库不保证自动加速。

优先建议同图原生 Faiss 对照与最小多入口适配，然后验证跳过尾部空槽、预取/batch4，最后考虑候选与大布局修改。未启动这些后续实验；不能要求语义不同的原生版本逐位复现项目输出，也不能按同 L 速度宣称胜负。后续无语义内核改动应通过原一致性和完整单线程 Recall@1/100 比较，公平应用全部共享 NSG 方法。

默认仍 Web soft/Yandex hard；E99 加速和原备份保留。两张诊断图已生成，详细解释、命令入口、核验与所有原始文件见 [报告](../entry_method_exploration/20260916_residual_cost_research_v1/report.md)、[协议](../entry_method_exploration/20260916_residual_cost_research_v1/protocol.md)、[结果](../entry_method_exploration/20260916_residual_cost_research_v1/results/summary.json)。
