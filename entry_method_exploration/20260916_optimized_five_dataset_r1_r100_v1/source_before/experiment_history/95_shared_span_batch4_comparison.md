# E102：共享span+batch4的统一方法比较

用户在E101之后要求“NSG、GT10、GATE都应用之后测试一下”，本轮补齐共同优化后的NSG基线，区分实现收益与入口方法收益。E102于2026-09-16完成统一优化公平比较：NSG、GT10-hard/soft、GATE均使用相同span+batch4，WebVid四预算各新旧内核及同轮HNSW共36配置108plain。NSG自身四点平均QPS变化+18.58%至+27.28%；K100/L1250从252.11变为320.90QPS，Recall@100保持90.4456%。同内核soft为324.95QPS/90.6868%，GATE为319.69QPS/90.6317%；HNSW为271.54QPS/90.3718%。

四种入口策略使用同一E101 span+batch4研究内核、同一冻结图和向量storage，原入口模型/路由小图保持。NSG为项目固定单入口，GT10-hard/soft为原画像三入口，GATE为原修正标签模型的三入口，不将其改称原生Faiss搜索。每种方法同时测E99 current；HNSW作同轮完整图参照。新内核未合入生产API/trace，默认Web软/Y硬保持。

WebVid完整10K query，K1/L96、K100/L100、K1/L800、K100/L1250，36配置各warm1+plain3+count1，1800000次搜索。CPU15，进程及数值库线程1，方法串行，完整路由/search/output计时，GT、加载、校验、写盘外置。所有warm/plain输出和count逐query NDC对齐E99；新count直接转发Faiss真实batch4，不拆回scalar。所有180份raw文件独立哈希与GT评分验收。

16项方法内新旧平均QPS变化+17.16%至+27.59%，全部原始三轮范围保留。高预算优化后hard 318.62QPS/90.6596%，soft 324.95/90.6868%，GATE 319.69/90.6317%，NSG 320.90/90.4456%。同L质量/时间差不能称等Recall加速，四点不能替代完整前沿；小差异须结合重复范围。公共优化收益不能归为GT10独有方法收益。

同内核低预算K1/L96和K100/L100，GT10-soft相对NSG分别增加4.73/1.64pp Recall与11.68%/11.28%平均QPS；高预算速度差缩小，结合三轮范围判断，不支持“GT10无效”或“全面第一”。一种与结果相符但未经独立因果消融确认的解释是：有限预算下入口选择更关键，预算增大后固定入口NSG能通过充分探索缩小差距。不能用公开点重新挑模型或将此解释写成已证明机制。

主性能之后串行重做其它四集完整10K/10K/10K/1K、四入口×四预算的真实batch4 count，496000次，其它四集64配置的ID/距离bits/入口/逐query NDC全部一致；该阶段0正式QPS。内核与E101逐字相同，继承6480配对普通及ASan/UBSan结果，本轮新合成搜索0。查询总2296000，无训练、新图、新GT、LAION、Recall@10或新held-out；当前公开query已有历史曝光。

修改前Git备份8afd61cd5dae388f15e26890ce75109ffffd0f2f，原main/index、ACSG源和库、旧图/模型/结果均保持。运行成本、输入/源码身份、逐轮指标和失败保留规则见独立报告。本轮验收完成，不自动扩网格或部署。

[报告与图](../entry_method_exploration/20260916_shared_span_batch4_v1/report.md) · [协议](../entry_method_exploration/20260916_shared_span_batch4_v1/protocol.md) · [指标](../entry_method_exploration/20260916_shared_span_batch4_v1/results/metrics.csv) · [共同内核的方法差异](../entry_method_exploration/20260916_shared_span_batch4_v1/results/shared_kernel_comparison.csv) · [输入身份](../entry_method_exploration/20260916_shared_span_batch4_v1/reviews/assets.json) · [最终验收](../entry_method_exploration/20260916_shared_span_batch4_v1/reviews/final_review.json)
