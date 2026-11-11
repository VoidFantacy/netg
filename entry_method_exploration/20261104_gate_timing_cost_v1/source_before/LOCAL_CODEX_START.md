# ACSG 当前接续入口

2026-11-02，工作区/data/netg/ACSG，HEAD96cf05d5410cf51272048cd1f90b4bb194e23c62。最新E198条件残差导航完成1480点/4440完整T1，默认E99保持，无运行中或待恢复矩阵。先读AGENTS、summary、spec、s-target、s-experiment，再读[验证报告](entry_method_exploration/20261102_conditional_residual_policy_v1/report_zh.md)、[具体方法](entry_method_exploration/20261102_conditional_residual_policy_v1/method_zh.md)、[交付核验](entry_method_exploration/20261102_conditional_residual_policy_v1/delivery_validation.json)。

完成1,480点、4,440轮完整CPU15/T1测量。7种新学习动作共112个窗口点，其中112个被同窗GT10/OPT-B32/REUSE-SQ强控制覆盖。默认保持E99；有限网格未覆盖也不直接成为默认替换证据。 两集两曝光窗口的有限结论，不否定历史M5/B32/SQ正面场景。新方法已实现前置门、双塔、短名单教师和预算选择；不要再当成未实现方案。原主beam pause/resume、图修复和GNN仍未实现。

全部新证据在本轮storage持久目录，raw/witness按payload归档往返核验；旧科学文件/seal/PDF保留，根文档旧字节在source_before。不按旧PID/session重启，不自动扩点、重训、发布、改默认或生成PDF。E197关机恢复已独立收口，其持久来源和限制继续读原卡片与验收，不混拼旧QPS。
