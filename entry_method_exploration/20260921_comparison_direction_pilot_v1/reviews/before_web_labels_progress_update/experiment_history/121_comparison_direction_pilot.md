# E118：共享比较方向的入口收益预测（进行中）

用户于2026-09-21授权推进实验，并要求负面结果先排查实验错误。新版本以实际搜索比较方向跨节点共享信息，预测全部现有H单入口相对原GT10三入口的真实召回/时间收益。它扩大的是有标签的动作域和输入信息，未重开E117的四动作浅树runner。

协议固定32个projective方向及正负ReLU、64维ridge，真实K1/K100/L128全H标签，GT10回退；同时测试随机方向、图线性、原query线性、召回目标、整query置换，以及GT10/Single1/BestFixed/NSG/计算开销控制。每集方向2048、拟合4096、接受4096，各角色互斥但属于历史曝光开发集。接受载荷须模型冻结后物化。完整L128和冻结策略五预算迁移均须完成，不依赖首轮均值决定是否补测。

当前原生程序已编译，两集各8query的trace/plain/count/链接E99和全H实际K1/K100三重复小检查均通过。正在执行方向发现及后续训练标签；尚无模型训练和新性能结果。聚类/训练Python代码已写出，尚待数值验收。当前状态和进程以独立state/jobs为准，不能把本记录当作实验完成。

接续补充：两集完整2048query的比较方向已采集，Web全H训练标签分块正在执行。合成数值/真实label/前向/所选动作回放/接受恢复、完整比较、成本与报告代码均已写出并通过语法检查，等待标签进程退出后串行执行。首阶段控制器与后续等待器均有真实进程句柄；当前不能把已写代码或等待器算作已完成的模型训练。新增fit正确性回放后预核总计50,541,782次NSG，仍低于原60,000,000预算，见[调用预核](../entry_method_exploration/20260921_comparison_direction_pilot_v1/reviews/planned_call_accounting.json)。

代码与全部新输出位于独立版本；底图、原画像/小图、主搜索及旧产物保持。原生计算必须CPU15/实际线程1、串行；标签时间和离线成本不当作QPS。异常只标记执行问题，不直接判方法失败。

理论说明修正：搜索比较区域内返回ID不变，只有GT也固定时Recall才必然不变。原生标签已按每条query自己的GT评分，该条件遗漏只在文字中；保留修改前文档，补充[推导条件与影响范围](../entry_method_exploration/20260921_comparison_direction_pilot_v1/reviews/recall_region_correction.md)，未改变运行配置或重跑标签。

- [协议](../entry_method_exploration/20260921_comparison_direction_pilot_v1/protocol.md)
- [方法、条件推导及表示限制](../entry_method_exploration/20260921_comparison_direction_pilot_v1/method.md)
- [配置](../entry_method_exploration/20260921_comparison_direction_pilot_v1/config.locked.json)
- [状态](../entry_method_exploration/20260921_comparison_direction_pilot_v1/state.json)
- [小规模一致性检查](../entry_method_exploration/20260921_comparison_direction_pilot_v1/reviews/native_smoke.json)
- [任务与进程](../entry_method_exploration/20260921_comparison_direction_pilot_v1/reviews/jobs.json)
- [原生源码](../entry_method_exploration/20260921_comparison_direction_pilot_v1/src/experiment.cpp)

完成后在本记录补实测表、完整成本、错误修正、独立审计和结论。默认仍Web GT10-soft-t1 / Yandex GT10-hard，生产E99；E103仍是最新完整五集前沿。
