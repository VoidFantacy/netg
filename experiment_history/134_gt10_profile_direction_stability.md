# 134 GT10归一化画像稳定性和跨半亲和

2026-09-22，固定原20K随机平分，25次闭式画像统计，0新搜索/GT/图/QPS、默认保持。

相同query数下，Web GT1/GT10-hard/soft半样本方向夹角中位24.510°/12.134°/8.540°，去入口公共方向后ρ为0.66934/0.89655/0.93246；Y GT1/GT10-hard为27.232°/16.486°、ρ0.80613/0.92682。共享GT1正支持hub子集结论保持。置换对应后也部分稳定，因此不能把全部稳定性归于语义；十个方向的真实跨半亲和均胜保持质量/ESS的行置换，也胜全局query均值。

不同标签对应不同代理目标，稳定性和亲和均不等于Recall保证；一次划分/历史来源不冒充IID泛化或多个独立样本。400000原rank恢复；Web soft质量SHA、三套GT10全样本画像及当前默认逐位恢复。GT1浮点累加差单列。

分析8.270秒、25聚合；独立20画像和20全query前向核验4.062秒，误差≤9.99e−16，18小源身份保持，大base仅stat/消费target哈希。初版审计语法解析失败保留，v2修正后通过。

证据：[报告](../entry_method_exploration/20260922_until2200_improvement_v1/research/profile_direction_stability_v1/report.md)、[协议](../entry_method_exploration/20260922_until2200_improvement_v1/research/profile_direction_stability_v1/protocol.md)、[独立核验](../entry_method_exploration/20260922_until2200_improvement_v1/research/profile_direction_stability_v1/reviews/independent_audit.json)。
