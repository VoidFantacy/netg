# 136 目标预算的全H单入口余量

2026-09-22完成，固定从E118历史fit4096抽256，不训练新候选、不测QPS。

目标预算Web K1/L1000、K100/L1250及Y K1/L128、K100/L256，默认Recall91.0156/91.0117/92.1875/91.6172%；全H-single+默认事后余量4.6875/1.5859/7.4219/2.6406pp，原top3-single+默认覆盖0%/10.34%/36.84%/24.85%。所以七策略趋同不能当作全H上限，但大部分剩余机会也不能靠原top3选择获得。

相同样本原L128全H余量16.4063/6.4258/7.4219/4.5273pp。原L128最好入口迁到目标预算，K100只保留目标oracle的Web15.76%/Y63.31%；Web K1则保留100%，Y K1预算相同。预算错配证据须按K区分。E123/E124冻结动作只作描述迁移，不改其原门和停止状态。

新增628404 NSG、512路由，0GT/训练/图/新源/K10/QPS；Y K1复用原标签。CPU15实际1线程串行，作业777.022秒，编译7.746秒，峰值约9.923GiB。原默认入口、旧L128完整hash、原核count/plain/E99返回/NDC通过；全部628224输出主重评分及独立Python集合评分、6144方法值、24区间、761身份检查通过。分析2.015秒、独立核验4.855秒。

256条历史样本，K1步长0.390625pp；95%区间为描述性，oracle免费且只含原H单入口及默认，不代表部署收益或所有入口组合。准备v1在复制无用缺失头时0搜索失败，保留v1并用v2同样本配置完成。默认保持。

证据：[报告](../entry_method_exploration/20260922_until2200_improvement_v1/research/target_budget_fullH_v1/report.md)、[原协议](../entry_method_exploration/20260922_until2200_improvement_v1/research/target_budget_fullH_v1/protocol.md)、[数值](../entry_method_exploration/20260922_until2200_improvement_v1/research/target_budget_fullH_v1/results/summary.json)、[核验](../entry_method_exploration/20260922_until2200_improvement_v1/research/target_budget_fullH_v1/reviews/independent_audit.json)。
