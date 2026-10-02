# 142 廉价教师信号预测方向残差

2026-09-30，原fit20K随机冻结2048 pilot / 17952接受，8个GT-free特征、depth2/min-leaf128风险树，与均匀、近似杠杆、同标签四分位表、打乱树及不可部署oracle比较。固定50%均匀混合，无参数扫描。

主候选接受池HH方向方差为均匀的Web0.9133/Y0.7386，两个固定半池方向一致；打乱约0.9955/0.9940、四分位表约0.9936/0.9933。Y保留局部信息信号，Web未达0.8投入参考，非跨来源或Recall收益。预测主信息为前十教师距离均值，Web另有归属熵。即使方差下降也未证明放大纠偏优于直接近似；需要比较偏差—方差取舍。

计算7.752秒/审计6.787秒；8万树标量前向、pilot均值、64条能量、36方差分子及身份/角色核验通过。0新GT/ANN/NSG/画像/图/QPS；使用历史训练标签，独立指同一agent另一套实现。

[报告](../entry_method_exploration/20260930_theory_until2200_v1/research/cheap_residual_information_v1/report.md) · [协议](../entry_method_exploration/20260930_theory_until2200_v1/research/cheap_residual_information_v1/protocol.md) · [原结果](../entry_method_exploration/20260930_theory_until2200_v1/research/cheap_residual_information_v1/results/summary.json) · [审计](../entry_method_exploration/20260930_theory_until2200_v1/research/cheap_residual_information_v1/reviews/independent_audit.json)
