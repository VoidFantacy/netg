# 108｜E112首行覆盖入口设计

2026-09-20。由单入口首行发现的条件Recall下界推导固定H容量的次模覆盖目标；同原独立QGT5K、H815/821、原底层NSG，比较全base贪心GraphH、原H及GT1频率H。先冻结两集H，再由runner读取完整曝光开发4096/集；不是新盲测。

开发F相对旧H：Web+4.0505pp，98.75%区间[+3.3158,+4.8103]；Y+0.1404pp，区间[−0.0996,+0.3916]。相对频率H：Web+2.2653pp区间正，Y+0.1829pp区间跨0。默认L128失败的条件GT1恢复量Web96/4096=2.3438pp，Y0。Web通过全部信息条件，Y全部失败，整体STOP_ONE_HOP_H_DESIGN_INFORMATION_GATE；不选单集继续、不扩H/跳数/seed/模型。

F是特权条件下界，贪心近似保证仅是标准次模结论，不是新理论、泛化保证或实测Recall。GT1严格性与GT100外部排名条件明确，未改GT/Recall或删query。GraphH中位GT1支持仅2条/入口，Y训练F17.6002%→开发0.8004%；支持稀疏/局部覆盖迁移不足，不等于所有图学习无效。

0新NSG/ANN/GT/图/梯度及画像训练；有新标签与H离线优化。四标签进程49.734秒、编译8.679秒、最大RSS10.169GiB。两次分析布尔序列化错误及修正完整保留，最终CSV逐字相同；独立成员及贪心/来源核验通过，图已检查。原Web soft/Y hard及生产E99保持，整体研究目标仍持续至19:00。

[完整报告](../entry_method_exploration/20260920_until1900_theory_v1/stages/e112_one_hop_hub_design/report.md) · [冻结协议](../entry_method_exploration/20260920_until1900_theory_v1/stages/e112_one_hop_hub_design/protocol.md) · [原始门](../entry_method_exploration/20260920_until1900_theory_v1/stages/e112_one_hop_hub_design/results/gate.json)。
