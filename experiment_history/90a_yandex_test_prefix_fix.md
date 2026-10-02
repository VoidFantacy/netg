# E97 Yandex公开查询前缀接入修正

2026-09-15 14:09，E97在preflight停止，尚无正式计时。Yandex manifest声明test_rows=10000，但query/GT路径指向100000行原始公开文件。E96 native会读取前10000行，E97严格要求文件行数等于声明，因此正确拦下接入不一致。

修正仅物化原文件前10000行及对应GT100，选择规则与锁定规模、E96前缀一致，不根据查询表现筛选。新文件与原前缀逐位相同；新增物化函数具有幂等性。原公开文件、模型、NSG、HNSW、训练标签及配置均保留，181个原冻结产物完整SHA核验通过。源码仅修复reuse_ip.py的数据接入，其他47个冻结源码/二进制身份不变。

原冻结清单和输入manifest保存后，以显式amendment更新测试文件及接入源码身份，保留原模型冻结时间与模型验收记录。失败前产生的8份不完整评测配置已归档并按新冻结摘要重新生成。五集preflight在15:19通过，15:20由独立systemd服务恢复，实际开始GIST K1单线程计时。中断等待约70分钟，不计作训练/查询计算成本。

范围保持WebVid、Yandex、Deep、SIFT、GIST，排除LAION；只测Recall@1/100，800点/2400次wall。此记录是输入接入修复，不是方法性能结论。

- [限定修订与核验](../entry_method_exploration/20260915_gate_l2_r1_r100_v1/reviews/yandex_test_prefix_correction_v1/correction.json)
- [原冻结记录](../entry_method_exploration/20260915_gate_l2_r1_r100_v1/reviews/yandex_test_prefix_correction_v1/frozen_models.before.json) / [当前冻结记录](../entry_method_exploration/20260915_gate_l2_r1_r100_v1/reviews/frozen_models.json)
- [原失败日志](../entry_method_exploration/20260915_gate_l2_r1_r100_v1/logs/preflight_20260915_140922.log) / [已通过的前置检查](../entry_method_exploration/20260915_gate_l2_r1_r100_v1/reviews/preflight.json)
- [实时状态](../entry_method_exploration/20260915_gate_l2_r1_r100_v1/state.json) / [后台状态](../entry_method_exploration/20260915_gate_l2_r1_r100_v1/ops/background_status.json)
