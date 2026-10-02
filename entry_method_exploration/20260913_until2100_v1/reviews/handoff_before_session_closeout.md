# 2026-09-13 campaign阶段交接

E60完成封存，双集支持0/40，原J+辅助约束全部no-op，不扩大同类连续训练。实际17830 NSG/660640 HNSW/322build；659488集合评分、576三路parity通过。所有native已退出，当前无遗留PID。根四文档及历史49同步；E60冻结引用root_after，后续根文档可合法继续更新。昨日history README恢复原字节，E60只在根s-experiment登记。

输入角色：P-fit router_train10000:30000含旧train4096/monitor1024；辅助旧cal0:1024用于动作选择训练诊断，迁移旧audit1024:2048只描述规则、但历史已暴露，本轮又使用。Fast30K曾使用全部router_train，不宣称其余行为全新。E34最终validation不进入本轮输入或选择。

WebVid9个辅助正动作均train-J负：7个训练命中受损、2个训练命中不变而其它项负；Yandex无辅助正动作。门空不能泛化为全空间不可兼容。完整证据见stage1_support_v1/report.md及results/actions.csv。

当前准备第二个独立阶段：完整fit20K的冻结基线遗漏GT10成员驱动画像聚合，固定小强度和同query同遗漏数量的随机目标对照。已找到E33全20K原始基线缓存，正在核对复用身份。该阶段还未启动，不能执行旧E53/当天旧runner继续扫描。下一命令将随新协议/prepare实际实现写入本文件。

复查E60可读：cat entry_method_exploration/20260913_until2100_v1/stage1_support_v1/results/gate.json。

资源起点7.984GiB空余，阶段限制384MiB、free>=7GiB，不删除历史。当前会话最迟10:15安全交接；全天目标未完成，20:00训练停止/20:40新增查询停止/21:00交付窗口保留。

## E61已完成（约09:36）

真实遗漏画像cal −0.3906/−0.1465 pp且各净增3零命中；audit+0.0195/+0.0684 pp不回选，仍原P。全fit也净负；原全命中14/20条变零命中，原零命中45/32条获救。新增28484 NSG/133056 HNSW/6build，六图/132288集合评分/384parity全部验收。E61已封存，当前无native。下一步拟用E48安装器补E61端点S/T四格定位损伤，尚未运行；不做lambda扫描。
