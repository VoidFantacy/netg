# E41：目标入口画像与其余画像的2×2隔离

2026-09-12。用户明确要求执行E40尚未运行的控制。本独立版本实际执行双集四格，不训练模型、不改默认、不扩大原案例/查询池，也不启动后续训练。旧E37–E40与用户工作区保持；历史s-target的“设计未执行”由此次明确授权覆盖，原历史文件仍保留当时身份。

## 冻结案例、数据和四格

原案例直接来自E40 results/attribution_cases.json：WebVid selected/action3/hub42091，正例train row707/source26913，负例3282/source22588；Yandex zero/action0/hub9339959，正例3349/source19628，负例3962/source21906。案例选择使用已有GT，是机制诊断，不是无偏性能验证。查询只使用各自E39已冻结1024行，顺序保持；原数组为E39另存train4096。没有新cal/audit/validation/held-out读取或评测。旧目录SHA保护会读取其中已有隔离开发产物，不沿旧manifest递归读取原validation/held-out。

- C(0,0)：全部画像取原中心。
- F(1,1)：全部画像取原冻结扰动。
- S(1,0)：仅目标hub一行取扰动，其余取中心。
- R(0,1)：目标行取中心，其余取扰动。

每行逐字复制已有单位float32 W，不插值、不改σ或采样，不更新optimizer。S/R未必是原共享变换可达的画像，是独立静态反事实，不冒称原RL checkpoint。固定H815/821、真实ID映射和插入顺序，普通HNSW M16/efConstruction200/seed20260828/efSearch10、direct top3真实ID升序，原raw-IP/embedded NSG L128/K10不变。只复用E37 native已编译环境，无边hook、在线网络或主代码修改。

## 预算、顺序与一致性

双集按WebVid→Yandex串行；每集按C,F,S,R固定顺序，每格重新普通构图并保存W/物理小图。正常2×4×1024=8192 NSG；每图前16个同名单query做count/serialized plain/original NSG三路verify，共384；预计8576 NSG、8448 HNSW、8 builds。总硬限10000，各dataset原生cap4288且外层完整预留4288，失败预留不释放、不自动重试、不借旧预算。新输出/图拒绝覆盖。

每格先正常run1024并保存，再verify前16，count输出与该格正常结果ID/float distance bits/入口/route与graph NDC逐位相同。C/F全部1024输出和W/拓扑/物理graph SHA恢复E39对应原件；S/R完整新返回不能查旧标签代替。GT只在搜索返回后评分，C++不读GT。

启动前SHA核验E37–E40目录、真实NSG及原native依赖，冻结案例/行号/四格W/配置/协议/源码；结束复核。CPU15、显式threads1、OMP/OpenBLAS/MKL1、实际进程线程1，数据集及方法不并发。每查询进程1800s、地址空间32GiB、输出64MiB、free≥10GiB；统计CPU8单线程。执行wall包含索引加载、计数、构图、保存与验收，不作为QPS。

## 预定分析及解释

全1024逐格统计相对C的正命中增量G、损伤L、net=G−L、Recall pp、受益/受损query、零命中挽救/新增失败，以及route/graph/total NDC。每query保存C/F/S/R及交互I=hitsF−hitsS−hitsR+hitsC；相应原E37 U及漂移奖励差单列，NDC分母始终为原anchor，不能偷换分母。完整记录target effect S−C与F−R、rest effect R−C与F−S。

对冻结正例，S hits≥F hits称完整保留原改善，C<S<F称部分保留；负例S hits≥C hits称消除原损伤，F<S<C称部分修复。只有完整保留且消除损伤同时满足才称该案例支持“隔离其余画像可保留收益并消除此损伤”。它不是方法GO；全池新增损伤/G/L和NDC另列，不能只凭两条案例或净命中选新默认。R用于判断其余画像单独作用，交互以逐query实际结果解释。

若S自身复现损伤，不以其它画像解释其必要性；若R自身产生损伤而S不产生，支持其余画像块对该情境的作用。两个因素都是画像字节变化加普通HNSW重建，仍可能同时改变评分和邻接；不能单独归为HNSW访问、直接证明共享表示不足或宣称查询总体因果效应。案例事后选自历史训练数据，无泛化/性能证书。

八格全部完成及独立评分后收口，不按局部正值追加搜索/训练/新图。若隔离不保留收益或无法减少损伤，停止此局部分拆扩展；若有案例信号，只据证据提出一个下一步，并保留跨数据差异及新损伤。产物含原始aligned输出、四格画像/图、逐query CSV/JSON、案例/全池表、图表、独立评分/构造检查/预算审计，及历史30与四主文档同步。
