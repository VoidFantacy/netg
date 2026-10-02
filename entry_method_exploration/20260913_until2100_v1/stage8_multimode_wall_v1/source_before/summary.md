# ACSG 当前结果摘要

2026-09-13，第三串行会话完成E66多画像完整开发。真实入口仍815/821，画像容量3倍，原NSG/base/raw-IP不变。整日21:00目标未完成，E34最终validation今日仍待执行。

webvid2_5m_light_v1：mode3P相对原P，fit净-496、历史aux7952净-106命中，aux两半[-38, -68]，失败净+13；相对同容量duplicate的aux净+130。开发门失败。完整损伤/救回与控制见[E66报告](entry_method_exploration/20260913_until2100_v1/stage7_multimode_index_v1/report.md)，尚未有本方法完整QPS。

yandex_t2i_official10M_ip_v1：mode3P相对原P，fit净+164、历史aux7952净+49命中，aux两半[-14, 63]，失败净-4；相对同容量duplicate的aux净+182。开发门失败。完整损伤/救回与控制见[E66报告](entry_method_exploration/20260913_until2100_v1/stage7_multimode_index_v1/report.md)，尚未有本方法完整QPS。

E66原A/P恢复、父子支持/先验守恒、全图bytes、七slot去重、167712开发集合评分、55904旧baseline及288原kernelparity通过。337248新NSG、336960新HNSW、4新3H图；合成另1图/15路由。所有ANN串行CPU15实际线程1，模型构造只用历史fit20K，无新GT。aux7952是历史已暴露选型训练，原cal/audit亦历史使用；E34最终与held-out未进入。

E63的fit局部正值和cal净−1/−2未过门保持；E64 Web纯拓扑净+38但失败+2，Y真实端点均净负，best_all双集baseline。E65已完成45开发点225独立wall：Web相对匹配soft在4/5L上Recall小幅正、伴随失败增加，Y混合；全部QPS交叉范围跨零，无稳定改进结论。此前曲线与本轮不同，不拼接。

[E65完整曲线](entry_method_exploration/20260913_until2100_v1/stage6_development_wall_v1/report.md) · [历史索引](s-experiment.md) · [下一阶段](s-target.md)。
