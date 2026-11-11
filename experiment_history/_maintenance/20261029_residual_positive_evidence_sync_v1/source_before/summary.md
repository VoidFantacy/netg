# ACSG 当前结论

更新于2026-10-29。用户要求验证“优化残差后端＋自适应开关”两方向，E193已完成三集真实K1/K100、固定2048查询窗口的102点/306完整T1轮；另有36资格点和开发动作费用测量。默认E99 GT10保持：WebVid GT10-soft-t1、Yandex GT10-hard。无待恢复矩阵。

收益集中确实成立：E191七集旧实际包复核，Deep/SIFT K100/L200分别仅8.05%/7.42%查询有增益，COCO为71.7%。全开不划算不能否定选择性补全，E192对原全开费用的排除证书也不能外推门控后的费用。

本轮实际门在主搜索后复用route/main的廉价特征，不增加独立probe。合法末4K分成2K拟合、2K校准，模型与阈值在正式前冻结；旧GT10监督重叠保留披露。理想门用GT判断每条query是否有正净收益，真实付出条件执行费用，只作不可部署参考。

| 数据/K | 全开增益pp | 理想启用 | 学习启用 | 学习保留增益 | 全开/理想/学习 QPS | 学习被GT10或B32覆盖 |
| --- | --- | --- | --- | --- | --- | --- |
| COCO/1 | 0.9277 | 0.93% | 74.22% | 89.47% | 1526.4 / 1995.5 / 1625.0 | 是 |
| COCO/100 | 1.9712 | 72.12% | 86.38% | 92.17% | 1353.3 / 1472.8 / 1406.8 | 是 |
| Deep10M/1 | 0.0000 | 0.00% | 0.00% | 无增益 | 1573.7 / 1765.3 / 1765.2 | 是 |
| Deep10M/100 | 0.0962 | 8.59% | 91.36% | 100.00% | 1457.6 / 1724.8 / 1476.5 | 是 |
| SIFT10M/1 | 0.0000 | 0.00% | 0.00% | 无增益 | 1319.4 / 1486.3 / 1482.3 | 是 |
| SIFT10M/100 | 0.0801 | 7.37% | 68.99% | 86.59% | 1247.3 / 1463.1 / 1310.9 | 是 |


以上每行Recall与QPS均来自相同2048查询，QPS为三轮完整wall中位数；保留比例针对补全新增正确成员。学习门6/6组被GT10或已有B32在Recall和中位QPS同时覆盖。有增益的4组中，理想门均未被当前固定GT10/B32网格覆盖，只代表探索空间，不是默认替换证据；零增益两组的微小QPS差不计新潜力。Deep/SIFT K1无增益时模型回退全关，不算预测成功。

当前判断：后端费用/候选收益与开关识别能力应作为两项可分别验证的条件。收益集中已经确认；当前廉价模型仍有大量无效启用，尚未把理想开关空间变成可靠的净收益。不能把当前候选模型未过门说成所有自适应算法不可能，也不要求全开先胜出才准研究开关。各组理想门与GT10、B32的具体关系以报告的同窗口表为准。

E192的严格结论仍有效：新增正确成员必须在候选支持集中；固定训练遗漏ID源受遗漏交集上界约束。块法可以救回旧残差ID源之外的目标，所以“不共享目标ID则所有方法无用”不成立。完整旧结论读[E192报告](entry_method_exploration/20261029_sharing_necessity_v1/report_zh.md)，不将当前开关验证改称分布共享因果实验。

[详细报告](entry_method_exploration/20261029_adaptive_completion_gate_v1/report_zh.md) · [102点](entry_method_exploration/20261029_adaptive_completion_gate_v1/analysis/formal_points.csv) · [六组摘要](entry_method_exploration/20261029_adaptive_completion_gate_v1/analysis/case_summary.csv) · [动作费用](entry_method_exploration/20261029_adaptive_completion_gate_v1/analysis/action_cost.csv) · [冻结协议](entry_method_exploration/20261029_adaptive_completion_gate_v1/protocol.md) · [实现合同](spec.md) · [后继问题](s-target.md)。

证据边界：公共test历史曝光，一套图/画像、2048探索窗口，无新盲确认；同一执行者不同实现核验，非独立人员复现。正式GT不进可部署门；ORACLE明确知情。GT10/B32/SQ与E191同ID实际返回逐字节相同，所有门控分支/三轮包/访问计数核验通过。旧E191 PDF和E192科学原件/seal不回写；根文档旧字节保存于[E193修改前快照](entry_method_exploration/20261029_adaptive_completion_gate_v1/source_before/)，迁移映射见本轮reviews。新增产物/root/acsg-e193-storage经storage链接，无新PDF。
