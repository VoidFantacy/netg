# E45 确定均值单步的完整反馈控制

2026-09-12，`COMPLETE_MEAN_UPDATE_CONTROL_SMALL_FULL_FEEDBACK_SIGNAL`，`PASS_FULL_FEEDBACK_SINGLE_STEP_RESEARCH_GATE`。完整反馈保留小的无损单步信号，多数确定更新仍无质量响应。

| 数据集 | 原batch单步G/L/净 | 全池单步G/L/净 | 全池相对原步G/L/净 | 全池正/负状态数 | 全池平均ΔU | 全池graph NDC变化 |
|---|---:|---:|---:|---:|---:|---:|
| WebVid | 0/0/+0 | 1/0/+1 | 1/0/+1 | 1/0 | 0.00002533 | -0.00130% |
| Yandex | 3/5/-2 | 3/0/+3 | 5/0/+5 | 1/0 | 0.00007423 | -0.00111% |

完整训练反馈在同状态单步中产生小正值，不能把它写成训练已成功。WebVid在step60新增1个命中、无新增损伤；Yandex在step40两种更新都增加3个命中，在step100原batch更新损失5而全池更新没有损伤。因而全池相对原步分别+1/+5，而不是Yandex额外获得3个新收益。两集各9/10全池单步命中不变，局部响应依然稀疏。

新旧画像行的平均位移基本同量级：WebVid约0.00346/0.00347、Yandex约0.00306/0.00317。这里改变的是由反馈决定的更新方向/坐标，不是扩大扰动半径或步长。原八采样动作在WebVid7个/Yandex3个状态有正收益，但确定全池单步各只有1个正状态；不能用候选收益代替均值更新收益，也不能断言所有差距都由采样噪声造成。

上述G/L及净值按10个互不传递的context累加，仅作诊断，不能拼成一个部署模型的Recall；每处正信号只涉及一个query。预锁单步门双集通过，允许继续研究可支付的完整反馈，不允许直接宣布RL优势、泛化或性能GO。E44原入口分层失败不被翻案，也不按此结果调分层名额。

## 固定控制

全部沿用E44预锁20状态：E43 RL第一seed step20/40/…/200动作前W/μ/m/v/count及原八方向。由完整checkpoint与中间行更新恢复状态，原Adam/next_row全部逐位恢复。N_full只用E44全4096条件梯度替代原128梯度，原σ.3、cosine步长、clip、Adam局部计数和P/B/尺度不变；仅目标画像行变化，其余行复制当前W字节。

每context独立计算一次新反事实单步，不向下一个context传递；新反事实20，原单步回放20，连续训练0。完整梯度只消除固定八方向的query采样误差，不是离散检索目标解析梯度。GT只作返回后评分，没有新方向、候选选优或步长网格。

当前C复用E44完整raw，每context新build/run16/物理图三路parity恢复身份；N_batch/N_full各真实run4096并16条三路parity。所有60图保存完整拓扑、物理图与身份，40完整更新raw及20当前恢复raw保留。两种更新均报告全池收益/损伤/零命中/U/J/route和graph NDC，漂移计入J。

## 成本和验收

167040 NSG=164160正常新查询+2880三路parity，166080 HNSW、60构图；当前81920行完整结果复用E44已支付反馈。两query进程共92.652s，含加载/构图/计数/写盘/parity，不是QPS；CPU15实际进程/OMP/BLAS/MKL1，双集串行。没有新GT/monitor/cal/audit/validation/held-out/QPS。

独立集合评分245760条完整返回（其中81920复用当前），核验320当前bit回归、960条三路parity、60图/W/topology、40次逐坐标Adam（20历史+20新）、全池梯度身份与原/新行构造；E37–E44和原native/NSG SHA、query前冻结保持。新近完整snapshot使用E44 final_artifact_freeze_v2，首版日志竞争说明与原件都保留。

## 接续与边界

下一目标是精确反馈复用的实现与成本验收。原NSG只消费raw query和三个已排序真实入口，在query/L/K/metric/原图/kernel相同且三入口逐位相同时，复用已有完整ID/距离/graph NDC；HNSW仍须真实查询全部4096，并按当前图支付route NDC。只有入口变化的query重新运行原NSG，不能把未测变化填0。

E44已有80候选/集共327680 candidate-query配对中，入口变化仅WebVid971、Yandex362（事后预算线索，不是已测加速）。必须实现独立的route-only与显式三入口NSG接口，恢复全部原始输出/奖励/梯度，实测实际路由/构图/新NSG和复用成本；初始完整反馈费用单列，不能藏在cache里。该后继E46尚未实现或查询，先验收再按剩余时间决定是否开新的全池反馈训练版本。

默认保持WebVid GT10-soft-t1 / Yandex GT10-hard。E43监控门失败、E44分层失败、旧局部正值与条件责任全部保留。阶段完成不结束20:00持续研究目标。

[协议](protocol.md)、[冻结配置](config.locked.json)、[状态表](results/contexts.csv)、[门](results/gate.json)、[成本](results/cost.json)、[独立核验](reviews/verification.json)、[图](figures/mean_update_control.svg)。
