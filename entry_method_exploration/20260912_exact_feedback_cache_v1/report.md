# E46 完整三入口身份的精确反馈复用

2026-09-12，`COMPLETE_EXACT_FEEDBACK_CACHE_FULL_RECOVERY`，门`PASS_EXACT_FEEDBACK_CACHE_AND_TRAINING_PROJECTION`。实现/成本验收通过，不是新学习或性能GO。

精确反馈复用通过：180张固定图的737280行完整返回五字段与E44逐位一致，20个全池奖励/梯度恢复。候选655360配对只新增1333次NSG（WebVid971/Yandex362），为完整候选调用的0.2034%；全部HNSW路由仍真实执行，当前route NDC没有复制旧值。只在三个升序真实入口与query/原NSG/L/K/metric/kernel身份完全一致时复用完整ID/距离/graph NDC，入口变化则新搜索；没有GT引导筛选或未知补0。

20份当前C种子复用E44已支付的81920次完整反馈，若全部新冷启动则正常NSG为83253次；1333仅为候选补测，不能据此宣称整条链99.8%加速。新真实NSG共3061（正常1333+parity1728），HNSW742528、构图181，其中包含失败尝试的4096路由/1图。两个成功进程共34.410s，含14.711s加载；新NSG约0.578s、route约4.117s、含检查的build约9.821s，查表/复制及I/O另列。计数进程成本不是线上QPS。

冻结状态下的保守训练投影为2951.912s（约49.2分钟，已含1.5倍余量和600s加载/monitor/导出/审计），通过截止门。它不保证学习中入口变化率不增长；新训练仍须实时限制调用、输出与19:35截止。E45的小单步正值可据此进入一次真正的完整反馈RL/ES对照，而不是再改相关性采样。

## 实现与验证

[cache_environment.cpp](src/cache_environment.cpp)包含冻结E37 environment，新增e46_route（真实全池HNSW）和e46_search（显式合法升序三入口的原NSG），原kernel/库/旧binary不变。有效封装为[native_cached_v2.py](src/native_cached_v2.py)与[run_v2.py](src/run_v2.py)。当前C种子有完整query/图身份；候选重构完成后才打开旧候选raw做验收。保存全部raw、变化行/新返回、完整拓扑和每图时间；首末context36物理图×16query三路parity通过。

独立集合评分737280条、全部cache identity和raw bits、20个LOO梯度、180图身份、576条三路parity通过，8个非法输入批次在零NSG前拒绝，空增量返回正确类型空数组。奖励包含新的route NDC、原graph NDC、命中/失败/漂移，无代理标签。有效分析为[analyze_verify_v3.py](src/analyze_verify_v3.py)。

首attempt在首C空patch返回时触发ctypes NULL错误，原现场保留；新增NSG0、HNSW4096、build1由trace/控制流重建，未捕获该进程最终native计数。失败4000预留保留，两个修复job各2000，总预留8000/硬限10000。v2只修零长度输出，原二进制不变。分析v2完成数值核验后因NumPy bool JSON失败，v3只改标量类型与派生目录；无新查询。详见[空增量修正](empty_delta_repair.md)、[分析修正](analysis_serialization_repair.md)，原件不覆盖。

CPU15实际进程/OMP/BLAS/MKL1、串行；编译/分析CPU8。E37–E45及实际native/NSG/链接依赖保护，根文档前件保存。0 optimizer/新GT/monitor/cal/audit/validation/held-out/QPS。

## 接续

下一步E47保持E43原P/B/H/局部行参数化、σ.3、200步、两臂双seed及hub/ε日程；唯一反馈变化是每候选使用完整train4096。每次确定均值更新后也真实route全池、补测入口变化并替换当前缓存，杜绝过期C。初始全池结果实际重算并计费；轨迹保存完整route NDC和新增返回patch、原状态/方向/梯度/Adam/身份，独立重放全部逻辑反馈。按原monitor门决定后续，不扩大epoch或幅度。当前E47尚未运行，准备完成并核对剩余时间后直接执行。

默认保持WebVid GT10-soft-t1 / Yandex GT10-hard；E43、E44失败门与E45小正值保留。阶段完成不结束20:00持续研究目标。

[协议](protocol.md)、[配置](config.locked.json)、[逐图成本](results_v2/points.csv)、[完整成本](results_v2/cost.json)、[门](results_v2/gate.json)、[独立核验](reviews/verification.json)、[图](figures/exact_feedback_cache.svg)。
