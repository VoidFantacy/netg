# 83｜冻结选型后的最终完整性能对照（E94）

Web E92组合相对compact五L Recall +.095/+.270/+.080/+.085/+.030pp、失败−3/−4/−1/−1/−1，质量修复有迁移；相对匹配GT10-soft P，Recall −.340/−.385/−.410/−.125/−.105pp。Y compact对GT10-hard +.090/+.070/+.120/−.030/−.125pp、失败+3/−2/−4/−1/+2。没有稳定整体效率改善，默认保持。

本次两集原NSG/Fast30K/GT10-hard/Websoft与预选实际新方法，Web另compact起点，共50点250轮完整wall。Web best_all=P、best_new=E92（开发门失败反证）；Y两角色均compact，不把开发best_all称部署推荐。77目录/41同aux7952真实评分的E93选择先冻结，再于19:24:33开始最终E34输入hash；最终反馈不回流训练/选择，held-out未开。E34历史validation2000不是全项目盲集。

Web组合/compact的三个共同Recall描述性插值+1.08/+1.34/+1.51%，范围都跨零；组合/P −3.53/−4.02/−2.57%，范围均负。Y compact/P +.15/+.77/+1.19%，范围跨零。插值不是新增实测点或性能GO。完整50原点及所有正负、五轮范围保持，单L或单QPS不能作默认替换依据。

100000返回集合/mask、全plain/count/800原kernel、跨五L图/入口/七slot和同三入口返回通过；70000条原基线全七字段逐位恢复E34。401独立失败query（Web271/Y130）、346方法间状态变化；原812query×L事件4230单元，完整401×五L×各方法10730单元另存。失败严格零GT10命中，GT10/入口/返回全量；例图按源行固定选择救回/新增两个方向，不能把事后案例用来训练。

新增700800NSG/560000HNSW，native操作994.213s、250纯wall695.047s，二者不同；8个源图文件、40plain+40count加载，0新图/模型拟合/GT/编译。所有查询CPU15/进程及数值库单线程，两个工具顺序terminal0。原GT/画像/构图训练费用继承，GT-inclusive总成本未知项保留，组件wall未单测。原NSG/base/rawIP/GT、真实H及Fast历史身份不变。当前整日目标未标完成，后继只继续文档与最终汇报。

[完整报告](../entry_method_exploration/20260913_until2100_v1/stage35_final_comparison_v1/report.md) · [协议](../entry_method_exploration/20260913_until2100_v1/stage35_final_comparison_v1/protocol.md) · [实际选择](../entry_method_exploration/20260913_until2100_v1/stage35_final_comparison_v1/selection.json) · [原始验收](../entry_method_exploration/20260913_until2100_v1/stage35_final_comparison_v1/analysis_v1/verification.json) · [回归/完整失败验收](../entry_method_exploration/20260913_until2100_v1/stage35_final_comparison_v1/supplement_v1/verification.json)。

第12串行会话仅补充描述性复算：50,000条既有返回逐GT10集合评分，15组成员增损/失败转换与E94原paired.csv逐项一致；无新实验、训练或ANN。Web L128组合/compact新增66丢失12成员，救回4新增0；组合/P新增274丢失351，救回14新增13。完整五L正负均保留。[短报告与独立复算](../entry_method_exploration/20260913_until2100_v1/session12_report_v1/report.md)。
