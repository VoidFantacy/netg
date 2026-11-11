# E199 搜索前/查询阶段残差门与精排成本

2026-11-04。用户授权四多模态集实验、成本分析、精排成本与PDF。E199四个多模态数据集的门时机与精排成本实验已完成736点/2208完整单线程批次；主门策略80个窗口点中79个被同期强控制覆盖。 默认保持，固定矩阵已收口。

## 实验问题与机制

STATIC离线固定开关，PRE用query/route22维在主搜前预测，POST增加主返回摘要共28维，在C评分前预测；PRE-LATE使用同PRE模型/阈值只移动位置，结果/动作/工作量相同。没有图循环内早停。

F控制整段Q8＋CASCADE384、off主结果；N保持直接C答案，只控制追加导航，另测CPOST12。固定单入口384预算，学生top5＋最近1去重≤6、104维HGB重排；FAST/DIST/全C教师与B32/SQ均作控制。两拒绝语义独立报告。

四集真实K1/K100、主研究L200与预定强控制L网格、A/B各512旧曝光query。沿E197合法角色，2048学生fit/512开发兼门fit/512独立cal，75/90保留目标正式前固定；COCO/WebVid模型复用E198，Flickr/Yandex同方案新建。画像交叠和共享开发披露，未按正式结果调参。

## 实际结果、成本与边界

具体保留/停止结论读[findings](../entry_method_exploration/20261104_gate_timing_cost_v1/findings_zh.md)。完整Recall/QPS及阶段/精排实际数字读[report](../entry_method_exploration/20261104_gate_timing_cost_v1/report_zh.md)和[PDF](../entry_method_exploration/20261104_gate_timing_cost_v1/E199_残差门控时机与精排成本_20261104.pdf)，合并表仅描述两曝光窗口，不替代逐窗确认。

新标签/模型进程286.38/110.19秒；门标签/拟合74.22/3.29秒。正式batch wall1119.37秒，包含于正式进程1711.39秒，不重复相加。继承图/router/SQ及E198成本未清零；模型文件大小非RSS。

normal不插阶段时钟，含完整Batch生命周期；profile另行测分段并核输出/动作一致，profile batch缺六数组复制销毁且含时钟，不能以阶段和替代QPS或把差额全归给插钟。门特征可复用，入口改变后的扩展量与模型费用分开。辅助精算/邻接与重特征槽分别计，不是总NDC。

资格、三轮包/work/决策、profile、native/NumPy合并与模型/门分支、stdlib整数/hash/wall/强前沿/旧兼容包通过，同执行者不同实现。详细PDF实际渲染核查；所有新证据持久化，旧科学文件/seal/PDF保留，根文档旧字节在source_before。

单图/画像、Q8来源、单入口384/L200门研究、两曝光窗口、K1稀疏事件、共享开发和多比较限制保留。历史有效M5/B32/SQ不被本轮有限结果否定。未做原beam续搜/修图/GNN，未扩大固定矩阵，无待恢复队列。

## 原证据

[协议](../entry_method_exploration/20261104_gate_timing_cost_v1/protocol.md) · [冻结](../entry_method_exploration/20261104_gate_timing_cost_v1/formal_freeze.json) · [全部点](../entry_method_exploration/20261104_gate_timing_cost_v1/analysis/points.csv) · [门](../entry_method_exploration/20261104_gate_timing_cost_v1/analysis/gates.csv) · [阶段成本](../entry_method_exploration/20261104_gate_timing_cost_v1/analysis/stage_costs.csv) · [精排成本](../entry_method_exploration/20261104_gate_timing_cost_v1/analysis/rerank_costs.csv) · [同门位置](../entry_method_exploration/20261104_gate_timing_cost_v1/analysis/placement.csv) · [强前沿](../entry_method_exploration/20261104_gate_timing_cost_v1/analysis/frontier.csv) · [核验](../entry_method_exploration/20261104_gate_timing_cost_v1/delivery_validation.json)。
