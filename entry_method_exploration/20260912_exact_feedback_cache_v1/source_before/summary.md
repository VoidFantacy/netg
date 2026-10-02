# ACSG 当前结果摘要

2026-09-12，最近完成E45，`COMPLETE_MEAN_UPDATE_CONTROL_SMALL_FULL_FEEDBACK_SIGNAL`，门`PASS_FULL_FEEDBACK_SINGLE_STEP_RESEARCH_GATE`。[报告](entry_method_exploration/20260912_mean_update_control_v1/report.md)、[历史34](experiment_history/34_mean_update_control.md)、[核验](entry_method_exploration/20260912_mean_update_control_v1/reviews/verification.json)。20:00持续研究目标继续，默认保持WebVid GT10-soft-t1 / Yandex GT10-hard。

| 数据集 | 原batch单步G/L/净 | 全池单步G/L/净 | 全池相对原步G/L/净 | 全池正/负状态数 | 全池平均ΔU | 全池graph NDC变化 |
|---|---:|---:|---:|---:|---:|---:|
| WebVid | 0/0/+0 | 1/0/+1 | 1/0/+1 | 1/0 | 0.00002533 | -0.00130% |
| Yandex | 3/5/-2 | 3/0/+3 | 5/0/+5 | 1/0 | 0.00007423 | -0.00111% |

完整训练反馈在同状态单步中产生小正值，不能把它写成训练已成功。WebVid在step60新增1个命中、无新增损伤；Yandex在step40两种更新都增加3个命中，在step100原batch更新损失5而全池更新没有损伤。因而全池相对原步分别+1/+5，而不是Yandex额外获得3个新收益。两集各9/10全池单步命中不变，局部响应依然稀疏。

新旧画像行的平均位移基本同量级：WebVid约0.00346/0.00347、Yandex约0.00306/0.00317。这里改变的是由反馈决定的更新方向/坐标，不是扩大扰动半径或步长。原八采样动作在WebVid7个/Yandex3个状态有正收益，但确定全池单步各只有1个正状态；不能用候选收益代替均值更新收益，也不能断言所有差距都由采样噪声造成。

上述G/L及净值按10个互不传递的context累加，仅作诊断，不能拼成一个部署模型的Recall；每处正信号只涉及一个query。预锁单步门双集通过，允许继续研究可支付的完整反馈，不允许直接宣布RL优势、泛化或性能GO。E44原入口分层失败不被翻案，也不按此结果调分层名额。

167040 NSG、166080 HNSW、60构图；新反事实单步20、历史回放20、连续训练0。245760完整集合评分/320原结果恢复/960三路parity/40 Adam计算及全部图身份通过；CPU15实际单线程、数据集串行，无新GT/开发/QPS。E37–E44原件保留。

E44全池WebVid9/10状态有命中响应、原batch1/10，Yandex3/10与0；原入口分层方差比1.074/0.978未过门。收益损伤多数在补集，不能把原入口相关组当完整影响集。E43 WebVid ES+0.0781pp局部正值保留，Yandex未过monitor门；无RL额外优势。最近完整Recall–QPS仍E37。

下一目标是精确反馈复用的实现与成本验收。原NSG只消费raw query和三个已排序真实入口，在query/L/K/metric/原图/kernel相同且三入口逐位相同时，复用已有完整ID/距离/graph NDC；HNSW仍须真实查询全部4096，并按当前图支付route NDC。只有入口变化的query重新运行原NSG，不能把未测变化填0。

E44已有80候选/集共327680 candidate-query配对中，入口变化仅WebVid971、Yandex362（事后预算线索，不是已测加速）。必须实现独立的route-only与显式三入口NSG接口，恢复全部原始输出/奖励/梯度，实测实际路由/构图/新NSG和复用成本；初始完整反馈费用单列，不能藏在cache里。该后继E46尚未实现或查询，先验收再按剩余时间决定是否开新的全池反馈训练版本。 详细接续见[s-target](s-target.md)。
