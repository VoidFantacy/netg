# E198 条件残差导航验证

2026-11-02。用户授权“验证吧，后面介绍方法具体是什么，GT10不用再讲”。固定COCO/WebVid四状态、A/B各512已曝光查询，完成1,480点/4,440完整CPU15/T1，默认保持，无新PDF。

## 动机与实现

E197显示有限候选里有入口空间，但全C重评分费用和拒绝位置受限。本轮保持Q8直接答案及单seed辅助后端，分别训练K100/L100、200、400和K1/L200两预算真实效用。HGB教师、双塔学生、最近1＋学生前5的短名单、前置深度3门和0/96/384动作全部实现；另保留完整B32/SQ、同池距离种子、原MODEL1和返回等价的共享特征缓存对照。新DIST96/384是全C最近单seed，不与旧同名多seed混淆。

角色2048fit、512开发兼门fit、512独立cal，Q8银行/选择器沿E197合法分离；画像监督交叠和开发共享披露。预算比例惩罚不是实测wall预测。正式点表由cal完整费用提出邻近GT10/OPT-B32控制并冻结，未用正式Recall追加点或调阈值。

## 结果与费用

完成1,480点、4,440轮完整CPU15/T1测量。7种新学习动作共112个窗口点，其中112个被同窗GT10/OPT-B32/REUSE-SQ强控制覆盖。默认保持E99；有限网格未覆盖也不直接成为默认替换证据。

最终POLICY质量门槛强控制QPS变化-47.11%至-2.81%；相对ADAPT正增量保留80.55%至100.00%。旧MODEL1共享特征缓存返回字节等价，QPS变化+10.74%至+36.70%，工程省费不自动成为强前沿胜利。详细每窗Recall、QPS、救损、预算、门保留、短名单及失败查询在报告/CSV。

标签2,187,156候选行、4,374,312动作；标签进程415.91秒，训练进程196.46秒，正式batch wall1817.20秒。batch wall包含于正式进程，不重复相加。计数区分C/辅助精算和辅助邻接，非总NDC或全部扫描。

## 验证与边界

八状态全标签Python/native推断一致，三轮包/work/决策一致，native线性merge和NumPy全排序、独立Python策略、stdlib整数/hash/wall/强前沿及旧兼容包通过。同执行者不同实现，不独立人员复现。原标签源码与二进制有精确SHA桥接；原科学文件、seal和PDF只读保留，根文档修改前字节在本轮source_before。全部新证据持久化，无RAM依赖，无待恢复矩阵。

两集、单图/画像、固定单入口后端/预算、两曝光窗口、K1稀疏正例、共享开发和多比较描述区间均限制外推。未重做公开GT穷举入口oracle，学习教师不充当GT上界；未实现主beam续搜、图修复或GNN。历史条件有效M5/B32/SQ继续保留。新问题另建协议，不自动扩大本轮。

## 原始证据

[方法](../entry_method_exploration/20261102_conditional_residual_policy_v1/method_zh.md) · [报告](../entry_method_exploration/20261102_conditional_residual_policy_v1/report_zh.md) · [协议](../entry_method_exploration/20261102_conditional_residual_policy_v1/protocol.md) · [冻结](../entry_method_exploration/20261102_conditional_residual_policy_v1/formal_freeze.json) · [全部点](../entry_method_exploration/20261102_conditional_residual_policy_v1/analysis/points.csv) · [强控制](../entry_method_exploration/20261102_conditional_residual_policy_v1/analysis/comparisons.csv) · [门机制](../entry_method_exploration/20261102_conditional_residual_policy_v1/analysis/mechanisms.csv) · [成本](../entry_method_exploration/20261102_conditional_residual_policy_v1/analysis/cost_ledger.json) · [主核验](../entry_method_exploration/20261102_conditional_residual_policy_v1/analysis/analysis_receipt.json) · [stdlib](../entry_method_exploration/20261102_conditional_residual_policy_v1/analysis/stdlib_audit.json) · [交付](../entry_method_exploration/20261102_conditional_residual_policy_v1/delivery_validation.json)。
