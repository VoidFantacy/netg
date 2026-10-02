# ACSG 当前结果摘要

2026-09-12，最近完成E46，`COMPLETE_EXACT_FEEDBACK_CACHE_FULL_RECOVERY`。[报告](entry_method_exploration/20260912_exact_feedback_cache_v1/report.md)、[历史35](experiment_history/35_exact_feedback_cache.md)、[验收](entry_method_exploration/20260912_exact_feedback_cache_v1/reviews/verification.json)。用户持续研究至20:00，并要求大胆假设、小心证明；当前默认保持WebVid GT10-soft-t1 / Yandex GT10-hard。

精确反馈复用通过：180张固定图的737280行完整返回五字段与E44逐位一致，20个全池奖励/梯度恢复。候选655360配对只新增1333次NSG（WebVid971/Yandex362），为完整候选调用的0.2034%；全部HNSW路由仍真实执行，当前route NDC没有复制旧值。只在三个升序真实入口与query/原NSG/L/K/metric/kernel身份完全一致时复用完整ID/距离/graph NDC，入口变化则新搜索；没有GT引导筛选或未知补0。

20份当前C种子复用E44已支付的81920次完整反馈，若全部新冷启动则正常NSG为83253次；1333仅为候选补测，不能据此宣称整条链99.8%加速。新真实NSG共3061（正常1333+parity1728），HNSW742528、构图181，其中包含失败尝试的4096路由/1图。两个成功进程共34.410s，含14.711s加载；新NSG约0.578s、route约4.117s、含检查的build约9.821s，查表/复制及I/O另列。计数进程成本不是线上QPS。

冻结状态下的保守训练投影为2951.912s（约49.2分钟，已含1.5倍余量和600s加载/monitor/导出/审计），通过截止门。它不保证学习中入口变化率不增长；新训练仍须实时限制调用、输出与19:35截止。E45的小单步正值可据此进入一次真正的完整反馈RL/ES对照，而不是再改相关性采样。

当前研究假设是完整质量反馈能缓解局部画像学习失效，而非预先认定表示没有空间。E45同状态单步WebVid净0→+1、Yandex−2→+3（主要避开5命中损伤），各9/10全池更新仍无质量响应，信号小。E44原入口分层失败（方差比1.074/0.978）仍成立；E43未过Yandex monitor门，WebVid ES局部+0.0781pp保留。最近完整Recall–QPS仍E37，无RL额外优势或默认替换。

下一步E47保持E43原P/B/H/局部行参数化、σ.3、200步、两臂双seed及hub/ε日程；唯一反馈变化是每候选使用完整train4096。每次确定均值更新后也真实route全池、补测入口变化并替换当前缓存，杜绝过期C。初始全池结果实际重算并计费；轨迹保存完整route NDC和新增返回patch、原状态/方向/梯度/Adam/身份，独立重放全部逻辑反馈。按原monitor门决定后续，不扩大epoch或幅度。当前E47尚未运行，准备完成并核对剩余时间后直接执行。 详细协议与进退条件见[s-target](s-target.md)。
