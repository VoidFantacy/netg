# 173：NSG、GT10、M5 直接公共测试复测

状态：COMPLETED_TEST_MATRIX。**M5 正在研究**。用户要求两数据集的 NSG 基线、GT 与 M5 在实际 L=200/400/800/1000/1200 完整测试，不使用候选/选择集资格门。本轮独立于旧 E172，复用原冻结模型而不重新训练。

本轮已完成 **60 个实测点、180 批单线程正式计时**，每点全部 10000 条查询计算真实 Recall。**M5 正在研究**，结构为 GT10 入口路由与主搜索之后的冻结残差表补全。

相对 NSG，同 L 的 GT10 和 M5 在 20 个场景点的 Recall 与 QPS 中位数均更高。两者分别有 19/20 点的三轮配对速度均更高；GT 的 WebVid K100 L800、M5 的 WebVid K100 L1200 各有一轮速度低于 NSG，不能说每轮都提高。

相对 GT10，同 L 的 M5 在 20/20 点提高 Recall，真值近邻成员损伤为 0；配对 QPS 中位变化均为负，下降约 0.16%–4.85%。WebVid Recall@1 提高 0.97–1.92 个百分点，Recall@100 提高 0.4134–0.6308 个百分点；Yandex 分别提高 0.01–0.09、0.0042–0.0254 个百分点，增益很小。

WebVid Recall@1 有两个离散实测的综合优势：M5 L800 为 91.94%、414.37 QPS，GT L1000 为 91.66%、333.49 QPS；M5 L1000 为 92.68%、332.23 QPS，GT L1200 为 92.33%、278.59 QPS。按 QPS 中位数比，分别约快 24.25%、19.25%，三轮速度范围分离。其余三个数据集/K 场景没有这样的跨 L 实测优势；未据连线插值推导等 Recall 吞吐。

这次复测支持 M5 的 WebVid Recall@1 局部价值，尚未确立跨数据集、双 K 的稳定综合替代。继续保留 WebVid GT10-soft-t1、Yandex GT10-hard 默认；M5 标为正在研究。本轮没有新增训练、选择集筛选或按 test 调参。测试来自有历史曝光的公共窗口，不称新盲测。

## 方法与执行

M5=GT10路由+原NSG主搜索+冻结补全表。每画像最多8个目标ID，在线同一组三画像三行并集最多24个ID；目标不参与第二次图搜索，按原raw-IP重评分R∪C并返回TopK。教师方法稿采用[3页简洁版](../entry_method_exploration/20261009_nsg_gt_m5_test_v1/advisor_report/concise_v1/GT与M5方法说明.pdf)、[正文](../entry_method_exploration/20261009_nsg_gt_m5_test_v1/advisor_report/concise_v1/method_report.md)，M5标正在研究；只汇报机制。早期6页稿留在本地历史，不作为本次网页阅读入口。

两集各公共test前10K；Yandex取100K源的前10K。冻结模型FIT20K与本轮test真实向量字节重叠0，原SELECT4096、QGT5K、router TRAIN30K重叠也为0；Web test窗口有9行重复，保留原窗口顺序。公共test有历史曝光。输入/GT/图/模型身份见[完整数据预检](../entry_method_exploration/20261009_nsg_gt_m5_test_v1/data_preflight.json)。

实际测60点，每点3轮完整wall，共180批/180万正式查询。原NSG图、scalar search_new、raw-IP、T1/CPU15、实际同L。K1和K100分别真实搜索。加载、GT评分、计数和写盘在wall外，正常输出分配释放与路由、查表、去重、重评分、合并在wall内。

原v1冗余全批audit估计成本过高，在未读质量反馈时停止重排，耗时315.37秒，见[v1费用记录](../entry_method_exploration/20261009_nsg_gt_m5_test_v1/v1_cost_replan.json)。v2正式网格从头跑完，不拼接v1 partial；暖机256，完整plain输出及Recall仍全10K，独立M5线性合并oracle全10K，plain/count parity及NDC只在预锁均匀256条上执行。post_dots包含在graph_ndc。计时返回在stop前释放，未保存逐计时轮bits；不把untimed核验冒充计时轮完整bits证明。

原生作业WebVid2693.72秒、Yandex2770.95秒；正式wall分别1987.31、2039.06秒；完整SHA预检160.77秒，弃用v1费用另列；新增训练0秒。原历史训练成本保持记录，见[本轮费用](../entry_method_exploration/20261009_nsg_gt_m5_test_v1/delivery_costs.json)。

## 结果与证据

[完整实测报告](../entry_method_exploration/20261009_nsg_gt_m5_test_v1/analysis_v2/report.md)、[全部60点CSV](../entry_method_exploration/20261009_nsg_gt_m5_test_v1/analysis_v2/metrics.csv)、[60组配对比较](../entry_method_exploration/20261009_nsg_gt_m5_test_v1/analysis_v2/comparisons.csv)、[Recall–QPS曲线](../entry_method_exploration/20261009_nsg_gt_m5_test_v1/figures_v2/recall_qps_nsg_gt_m5.png)、[按L曲线](../entry_method_exploration/20261009_nsg_gt_m5_test_v1/figures_v2/recall_qps_vs_L_nsg_gt_m5.png)。源码、冻结配置、原生完成receipts和校验记录随本次快照保留。描述bootstrap不作为新质量门，当前模型不按此次结果修改。
