# E46：完整三入口身份的精确NSG反馈复用

2026-09-12。E45完整反馈的同状态确定单步门通过，但正值小且多数更新不响应；用户20:00持续研究授权保持。本阶段先实现精确反馈复用及实测离线费用，不训练、不改变查询采样或奖励。

## 作用与固定范围

固定E44全部20个context和每个C+八候选，W/图参数/原NSG/原train4096/IP/L128/K10/真实三入口顺序不变，所有原始结果已经存在。完整三个真实入口、query行及vector身份、L/K、原NSG/metric/kernel一致时，原NSG调用的输入一致，允许复用完整返回ID/距离/graph NDC；这不是用近似相关组筛query，也不将未知变化填0。

每图实际route全部4096，获取当前真实三入口及当前route NDC。相对该context当前C三入口逐位相同的query复用C完整NSG返回，发生变化者真实调用原NSG。HNSW新路由次数及NDC全部支付，画像漂移重算，GT在返回后评分。只维护当前context的query→C三入口/完整返回，没有跨query复用或GT引导筛选。

当前C的完整4096反馈种子来自E44且SHA核验，20份共81920已支付历史NSG调用单列；本诊断不将它们记作新查询，也不能把种子视为免费冷启动。候选655360配对中的预期入口变化是已知raw推算WebVid971/Yandex362；运行必须从新native路由重新确定变化，不读旧候选结果指导缓存命中。旧候选raw仅在重构输出完成后逐位验收。

## 独立接口与输出

新版本C++包含原E37 environment源码，新增route-only与显式三入口NSG函数，原run/build/save/verify和实际kernel保持。显式NSG入口要求三个升序、不同、合法真实hub；query行与L128固定，计入原calls cap。route-only不调用NSG，仍计HNSW次数并限制总路由cap。Python分别读取真实路由和新搜索返回，组装全4096五字段；同三入口部分复制C的IDs/float distance bits/graph NDC，不复制route NDC。

每图保留完整重构raw、拓扑、变化行及其新搜索输出、reuse mask/来源身份和成本。全部180图W/完整拓扑恢复E44；首末step20/200的36图保存物理图，前16query原count/serialized plain/kernel三路parity。所有737280重构返回五字段与E44逐位一致，U/J及固定八方向全池梯度须恢复E44。拒绝非法输入的合成接口检查不调用NSG，不能混入真实性能数字。

## 门与费用

恢复门：全部字段、身份、reward/gradient、原kernel parity完全通过。候选补测成本门：真实新NSG/655360≤10%，不把81920旧种子费用隐去；HNSW/构图/查表/复制/压缩/加载分列，计数和进程wall均不是线上QPS。

预计正常新NSG971+362=1333；代表图36×16×3=1728，总3061。每dataset完整预留4000，native cap4000，全局硬限10000；HNSW预计737280+1152=738432、构图180，native每集HNSW cap400000。失败不释放、不自动重试，禁止覆盖。旧种子若全部重新计算，额外81920次费用明确报告，不能由本稀疏补测直接宣称整条链99.8%加速。

只有恢复和补测门均过，才用实测每context（九图）wall估算双集两臂双seed200步：1.5×800×(WebVid每context均值+Yandex每context均值)+600s加载/monitor/导出/审计余量。按查询完成时真实UTC时间推算，预计必须早于19:25，且新训练设置19:35硬截止；否则不启动完整新训练。该保守投影不保证训练中效应数量不增长，新训练须逐步时间/调用/输出预算止损。不得仅据NSG次数下降许诺wall加速。

## 资源与交付

CPU15实际进程/OMP/OpenBLAS/MKL1，方法与两数据集串行；编译/分析CPU8，地址空间32GiB。每dataset timeout600s，19:40查询截止，19:30后不启动。输出256MiB、可用至少9GiB。保护E37–E45及原native/NSG/静态链接依赖，独立源码/binary/构建日志与hash，根文档前件保存。新GT/optimizer/monitor/cal/audit/validation/held-out/QPS均0。

交付原始重构与真实新增返回、全部复用身份/完整费用、独立集合与奖励/梯度核验、代表物理图parity、报告/历史35与四主文档。未来连续全池训练须另立版本：每次确定均值更新也必须真实route全池并补测变化query，更新当前完整缓存；不允许延用过期C。保存增量patch与完整路由NDC，足以重放所有完整反馈，避免重复写入数GB已知相同返回。
