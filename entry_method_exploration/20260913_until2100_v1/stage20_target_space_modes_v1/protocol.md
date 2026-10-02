# E79 GT10目标空间分组画像（前瞻协议）

2026-09-13，第7独立串行会话，所有新离线分组/构图/查询前锁定。E75–E78停止且旧seal不改；E73/E74 Yandex局部信号与Web损伤保持。当前用户授权足以执行。本会话16:21:50前安全交接，整日21:00目标未完成。无并行CLI/子代理。

## 机制及角色

旧E10与E66源码都在同hub内按query方向拆两组。本版本只改变分组特征：t_q=unit(sum_GT10 unit(base_target))。GT目标先用原float32 normalize，十rank之和及最终unit以float64计算。原base的fvecs维度头、所选行头与ID范围全部验证；目标向量仅在RAM流式读取，不落20K×d大文件。任何零范数目标或和<=1e-12导致可行性STOP，不隐式换目标。归属A和父P严格恢复原E66字节；R与Q均沿原归一化数值。不改变raw-IP大图metric或原NSG。

固定P-fit20K=router_train[10000:30000]，包含旧train4096/monitor1024；旧cal/audit/aux历史暴露。分组仅用此fit的Q/GT/base/A，无NSG效用输入。辅助7952=router_train[2048:10000]及两半3976/3976用于接受检验，反馈计训练。E34历史validation2000只留晚间冻结后最终对照，held-out不打开。读取复用22048输入时只解码前20K；身份SHA读取可能包括容器后cal/audit字节，不将此混称从未I/O。

每hub沿E66父mass>=8、ESS>=16。t空间父方向=unit(A_h^T t)，seed0=argmax A*(1+t·parent_t)，seed1=argmax A*(1−t·t_seed0)，并列按原源行。20轮加权球面两均值，平分归mode0，最终使用第20轮分配；曾空组/零center/零parent的hub回退P。子mass>=2、ESS>=8，不合格两槽复制P。子画像仍为unit(rho*R+sum assigned A*Q)，原P首槽bit保持。之后按(realhub,float32 row bytes)首出现去重，1–3slot/hub，保存original_slots与全bank→compact映射。目标聚类损失/分离度不是NSG效用。

唯一主候选target10；唯一机制对照permuted10：以PCG64 seed20260913固定置换t的行，A/Q/源行身份不动，整个流程同式。置换可改变子支持/合格数/physical count和图，不将差异纯归于目标身份。原query分组compact10与原P baseline10同时实测。不扫seed、阈值、簇数、温度、范数或收缩。

## 子阶段与验收

A：0ANN离线可行性及画像构造。恢复A SHA/P bytes，完整复算E66 Q分组的active/seed/最后assignment bits/child mass/ESS/sums/eligible和W；目标特征分块digest，固定32行独立标量单位化验证。比较分区时每hub同时报原标签差及A加权min(XOR,补集)，避免mode0/1互换误判。目标/置换分组全部先完成并冻结，再考虑查询。该阶段是真实离线分组训练，不能记为0训练；0optimizer、0新GT、0NSG/HNSW/build。

B：仅当A身份、有限性、原Q复现、父/子质量先验恒等与完整资源预算通过，冻结新的prebuild manifest后，复用E73同SHA builder普通构建四小图。冻结prequery后双集各128预检，再各完整7952。原E73 evaluator/原hnswlib/原NSG不改：M16/efConstruction200/seed20260828、ef10、search7slot→distance/slot排序→去重前三真实hub→真实ID升序→NSG L128/K10。所有图逐向量/label/邻接解析、plain/count与每方法16原kernel、完整7slot去重/距离、旧P/compact全部字段回归、aligned集合hits/masks独立复算。

主候选对P和compact均须全量净命中>0、两半>=0、zero失败不增；对permuted须全量及两半>=0且失败不增。至少一集通过才另立完整wall阶段，另一集原样迁移对照；若两集失败停止此目标分组版本，不改选permuted。门非性能GO。必须同时报告原compact正命中保留/丢失、新增收益、避免旧损失/新增损失；GT成员得失和逐query净命中正负部单列。失败严格GT10零命中。

## 资源与成本

正常129536 NSG=2集×4方法×((2×128+16)+(2×7952+16))，HNSW129280，4真实build。失败完整预留不释放，NSG硬限132000，不自动重试；0合成ANN，新builder实际复用其既有形状拒绝检查。CPU15/实际进程与OMP/OpenBLAS/MKL/NUMEXPR/BLIS1，串行且数值分析只在工具terminal0后启动。每集离线<=900秒/RSS16GiB，每query job<=600秒/RSS32GiB；16:00后不启动本阶段query，16:10硬停。

本独立版本在新实验前将磁盘下限设6.9GiB，另留32MiB晚间及4MiB交接。此前7GiB是已完成各版本的自设资源门，旧配置/结果与seal原样保留；当前用户要求保留安全余量，并未指定永久7GiB下限。现场free约7.055GiB，分配本阶段64MiB后仍约6.992GiB，额外晚间/交接36MiB后仍约6.957GiB，高于新下限。预算上界：四W/图<=31MiB，压缩分组/支持<=12MiB，全raw含预检<=12MiB，source/root/输入配置/seal/表图<=9MiB。逐阶段核验实际累计新输出和free；不清理旧件，不复制base/NSG/输入或binary，图直接引用，不以逻辑symlink大小冒充实际新增。晚间20:00停训练/20:40停新增query/21:00交付不变。

训练/目标读取/旧复现/构图/加载/原生诊断/独立评分分别实记，继承GT/P-fit成本未知不填0。B timing_repeats=0，不生成QPS；后续wall须同批NSG/Fast30K/GT10-hard/Web匹配soft/真实新方法，五L五轮完整在线wall，不能拼旧曲线。阶段结束保存原始产物、详细历史/索引/summary/s-target，接口同步spec，root_after封存与campaign handoff/state。
