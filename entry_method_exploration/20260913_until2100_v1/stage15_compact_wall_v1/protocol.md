# E74 精简多画像的完整同批wall（前瞻协议）

2026-09-13，第5串行会话。E73所有构建/接口/开发查询验收后，固定唯一compact10新候选，不再训练/重建/选型；Y历史aux质量门通过、Web未通过保持。此处实测精简的完整费用和质量，不把节点数或NDC代替QPS，不回写E66/E70/E72/E73旧门。

原NSG、Fast30K/GT1、GT10-hard、Web匹配GT10-soft、完整mode10、compact10，同一批L64/128/256/400/800，各一次完整warmup+5轮独立整批wall。Web30点/Y25点，共55点275wall，方法顺序按(dataset_order+repeat+L_ordinal)%方法数轮换；两个dataset严格串行，无同时训练/ANN/重分析。CPU15、配置threads1、OMP/OpenBLAS/MKL/NUMEXPR/BLIS1，监控实际进程线程/affinity/RSS。

直接引用E67/E71相同历史router_train[2048:4096]开发2048，已包含在用于反馈的7952辅助集，非盲集。E73辅助选择计训练，P-fit含旧train/monitor，cal/audit历史暴露。E34最终validation及held-out不读，最终选型仍留晚间，best_new字段只是固定compact展示别名。

使用E73同SHA binary，原eval与旧路径不变；源图graph_file直接引用，plain/count每节点W/外部label逐位核验，0新小图副本。完整raw-query路由/7slot排序去重/映射/原NSG/output在timer内；GT/count/hash/JSON/build/load在外。每点全count与16原kernel、五轮输出及旧基线恢复，所有原生工具实际terminal exit0后才独立集合评分和画图。没有以缓存代替正式搜索。

正常NSG=55*(7*2048+16)=789360，HNSW=45*7*2048=645120，0新build/画像训练/GT。两job完整预留，失败不释放，硬限800000，不自动重试。45 plain+45 count源图加载另计；route-only/graph-only未单测为null+原因，完整wall与原生进程时间分开。新增目录<=64MiB、free>=7GiB，原base/NSG/stat继承核验，保留晚间余量。13:50后不启动，14:05硬停，每job<=1200s/RSS32GiB；本会话14:17:57前安全封存交接。

逐query返回ID/距离bits/真实入口/七slot/hits/mask/两NDC及源行aligned保存。strict failure为零GT10命中，救回/新增、GT成员增损、逐query净命中正负部各自记账。画QPS–Recall、QPS–失败率、按L三指标、配对与完整失败query图表。QPS五轮交叉范围只表示测量范围；query bootstrap只是历史开发的描述区间，不把timing轮当Recall样本。共同Recall插值明确标为描述，不能当实测同Recall提速。

结果全部保留，任何局部质量/QPS正值与损伤、迁移和计时不确定性同时报告；未找到稳定整体改善就明确说明。其它批次可做相同结果身份回归，不拼到本批曲线。结束历史63/四文档/source_before/root_after、campaign handoff/state/实际成本/无遗留进程同步，整日目标未完成。
