# 原八方法补充成本：账本之外的已知旧窗口

[原记录身份与边界](../../../entry_method_exploration/20261003_all_methods_experiments_v1/reviews/original8_known_prior_cost_windows_ROOT_20261006_v1.json)。用于补充账本前缀表中的覆盖缺口，没有写账本、退款或重分类；没有重跑任何工作。

|方法|数据集|旧工作窗口|秒|计量范围|
|---|---|---|---:|---|
|M5|Web|SELECT K1 全16控制|1630.865067720|原完整monitor|
|M5|Web|SELECT K100 全16控制|2038.278487206|原完整monitor|
|M4|Web|proposal_union_gate|124.710178614|程序自行保存时长，非完整monitor/方法总成本|
|M4|Web|keyfree_union_upper_v2|389.029993868|程序自行保存时长，非完整monitor/方法总成本|
|M5|Yandex|SELECT K1 全16控制|281.236026525|原完整monitor|
|M5|Yandex|SELECT K100 全16控制|505.877810717|原完整monitor|
|M4|Yandex|proposal_union_gate|32.224429369|程序自行保存时长，非完整monitor/方法总成本|
|M4|Yandex|keyfree_union_upper_v2|156.249002957|程序自行保存时长，非完整monitor/方法总成本|

M5四个旧SELECT16完整监控窗口没有同attempt记录在已闭合账本前缀中；不能看到Y的VALIDATION列0就说未花费用。M4这里仅给原必要界程序的自报时长，其前件、cache生成及其他工作成本未由这些时长完整覆盖。不同计量范围不相加为完整方法总成本，也不转成单线程查询QPS。未监控或未索引费用继续记为未知。
