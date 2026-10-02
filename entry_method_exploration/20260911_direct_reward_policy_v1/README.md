# E32 直接真实收益策略优化

状态：`DIRECT_REWARD_POLICY_COMPLETE_FIT_GAIN_MIXED_DEVELOPMENT_STOP`。双集fit缓存门与完整路由/NSG验收通过；开发集相对教师四点为正，但WebVid cal未胜当前默认，按预设门停止。新validation/QPS为0。

入口：[报告](report.md)、[原协议](protocol.md)、[部署清单](deployment_plan.md)、[配置修正](configuration_repair.md)、[开发门](results/development_gate.json)、[Excel](chart_data.xlsx)、[最终验收](reviews/final_audit.json)。

图：[训练策略与贪心收益](figures/reward_and_greedy.svg)、[优化与最终缓存](figures/objective_and_final_utility.svg)、[开发集与路由成本](figures/development_and_cost.svg)。

源码和日志保存实际执行路径。`run_deployment.py`和`deployment_common.py`为初始原件，`*_v2.py`为修正后的有效控制器；共享同一已验收evaluate二进制。`final_audit.py`仅用于缓存门停止分支，本次实际进入部署后的首次结构验收由`final_audit_deployment.py`完成，访问表述更正后的最终验收为`final_audit_deployment_v2.py`。旧输出不可覆盖，未运行的validation入口不应直接启动。

[访问范围更正](access_scope_clarification.md)：旧validation输入曾做保护性SHA256读取，没有用于本轮训练、选点或新检索评测；held-out未读/hash。最终有效验收为`final_audit_deployment_v2.py`，它同时核对原冻结文件的修改前副本与更正后身份。
