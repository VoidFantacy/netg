# 74｜路由前query向量选择的缓存可行性

E85，2026-09-13第8串行会话，`COMPLETE_QUERY_GATE_CACHE_FEASIBILITY`。两集接受门FAIL，停止固定query方向线性规则；未进入原生实现或正式wall，0新增ANN。

## 机制及与E25的实质差别

原E25使用GT1/GT10双固定路由的7/13个在线路由特征，完整实验显示额外路由成本和收益保留不稳；本次读取历史14卡片及原protocol/config/train/state/tables追溯后，固定E73 P/compact，以原query单位方向在任何路由前预测实际命中差。拟议只选择完整一路HNSW后执行原NSG，但该在线模块未实现/计时；没有新颖性或部署优势声明。旧E25/E83/E84门不改。

每集router_train[2048:6024]3976行为本版fit、[6024:10000]3976为accept及两个1988子块。所有行均历史已暴露，accept只是不参与本版拟合，不是全项目未见；接受反馈算训练。单向划分，未交叉拟合或再fit。输入原query归一化仅生成特征，不修改下游rawIP；y=compact−P L128真实GT10命中差，含零差，固定岭系数1/d，训练均值/截距，预测>=0选compact。控制仅前半y固定PCG64 seed20260913置换。四模型在accept输出前冻结，无λ/阈值/划分选择。

## 结果、损伤与边界

| 数据 / accept3976 | 对P净命中 / 失败变化 | 对compact | 对置换 | 正命中保留 / 负损失避免 |
|---|---:|---:|---:|---|
| Web | -35 / +3 | +8 / 0 | +7 / +5 | 57.68% / 40.00% |
| Y | +24 / -3 | -57 / +5 | -51 / +3 | 57.92% / 29.21% |

接受门要求对P/compact全量净正、失败不增、两子块非负，对置换不差，且原正收益保留75%和负损失避免25%；两集多项失败。fit保留/避免Web83.92%/83.60%、Y92.31%/80.16%，明显不能用训练收益替代接受表现。fit非零标签仅341/129条，占3976分母，其余零差未被删掉。Y对P小正主要仍有原compact收益，不能掩盖相对compact退步。

缓存规则逐query选择完整原策略的返回/距离/入口/graphNDC，不能据缓存选择宣称新在线已运行。所附selected_policy_route_ndc不含预测norm/dot成本，不是在线总NDC或QPS。原NSG/base/GT/rawIP和小图身份固定。

## 成本与核验

4次固定岭回归，0NSG/HNSW/build/新GT/编译。完整训练成本、独立增广最小二乘解/全部标量预测/选择返回核验耗时见cost。63,616行集合/mask核验，31,808派生完整原策略行，410条失败并集（包括训练段）含所有GT/入口/返回；图只显示最早变化的接受段例。继承标签/GT/画像成本未知；E25历史报告汇总因机制复盘读取，E34最终原始query/GT及held-out未打开。所有数值CPU15/库及实际进程1线程。

[报告](../entry_method_exploration/20260913_until2100_v1/stage26_query_gate_feasibility_v1/report.md) · [协议](../entry_method_exploration/20260913_until2100_v1/stage26_query_gate_feasibility_v1/protocol.md) · [训练](../entry_method_exploration/20260913_until2100_v1/stage26_query_gate_feasibility_v1/src/train.py) · [接受前冻结](../entry_method_exploration/20260913_until2100_v1/stage26_query_gate_feasibility_v1/reviews/before_accept_freeze.json) · [完整配对](../entry_method_exploration/20260913_until2100_v1/stage26_query_gate_feasibility_v1/results/paired.csv) · [门](../entry_method_exploration/20260913_until2100_v1/stage26_query_gate_feasibility_v1/results/gate.json) · [成本](../entry_method_exploration/20260913_until2100_v1/stage26_query_gate_feasibility_v1/results/cost.json) · [失败](../entry_method_exploration/20260913_until2100_v1/stage26_query_gate_feasibility_v1/results/failure_queries.csv)
