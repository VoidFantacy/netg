# E99：NSG邻居预取与候选池复制优化

E99于2026-09-16完成共享NSG实现优化：WebVid四个预算、四种NSG入口方法的新旧对照，QPS变化+10.51%至+13.53%；五集100个组合的返回ID/距离bits/入口和逐query NDC均与E97一致。WebVid K100/L1250优化后soft为268.9 QPS、Recall@100 90.6868%；同轮完整HNSW为282.5 QPS、90.3718%。

用户选择先重点验证WebVid Recall@1/100、其他四集一致性，并要求修改前Git备份。备份分支`backup/pre-nsg-optimization-20260916_103846`、提交`2739b09a67f3ca0b6f145d43690d36345df3182c`保存6115个源码/脚本/配置/文档，全部回读一致；main和原index保持。大型数据/模型/构建产物原位保护。

## 机制与修正

将E98的预取信号实现到共享NSG源代码：每query取得当前存储视图，提前一个邻居预取visited及向量首cache line；不更改Faiss算术或入口策略。候选插入沿用完整L的原定位/重复ID逻辑，仅减少未满池的空槽复制，非有限或sentinel分数退回完整复制。原API/对象布局不变，原库保留，独立优化库可链接。

E98整体缩小插入函数K的实现存在等距顺序反例，已由35,856个候选池差分用例定位并规避。8,656次合成图查询验证返回bits、距离调用顺序和trace，覆盖IP/L2/边界/visited轮回。ASan/UBSan检查新内核及测试通过。初次trace validator对NaN的JSON数值比较误报，已保留失败日志并修正测试比较，生产代码未因此改变。

## 测量与证据

WebVid完整10K query，K1/L96和800，K100/L100和1250；同一进程/同一邻接和storage内存，旧新独立scratch，warmup+三轮plain+count。四种NSG方法都得到同一优化，完整HNSW作同轮参考；CPU15，进程和数值库1线程，方法串行。108轮plain计完整route+search wall，QPS为三次N/wall均值。

Yandex、Deep、SIFT、GIST完整公开query，K1/L96和1250、K100/L100和1250，四方法各一次count。计数包装器显式暴露原FlatCodes视图，实际覆盖向量预取。500份返回/入口/NDC文件逐一比对E97，全部一致；其余四集不声称新吞吐收益。启动真实搜索前把E97中不存在的K1/L100改为既有L96，未增点或按结果调参。

## 成本与边界

合计2,296,000次真实search、108轮plain，含加载主调度73.15分钟。无新训练、GT、索引构建、LAION或Recall@10；Git备份/编译/合成回归/后处理另计。只有Web四个预算点，不构成完整前沿和跨集性能结论；公开测试已有曝光，不称盲测。入口模型默认Web软/Y硬保持，生产源码已优化，旧库及E97/E98结果不覆盖。

[完整报告](../entry_method_exploration/20260916_nsg_search_optimization_v1/report.md) · [协议](../entry_method_exploration/20260916_nsg_search_optimization_v1/protocol.md) · [全部CSV](../entry_method_exploration/20260916_nsg_search_optimization_v1/results/metrics.csv) · [源代码补丁](../entry_method_exploration/20260916_nsg_search_optimization_v1/source_changes.patch) · [核验](../entry_method_exploration/20260916_nsg_search_optimization_v1/reviews/results_audit.json) · [源码及恢复说明](../entry_method_exploration/20260916_nsg_search_optimization_v1/src/README.md)
