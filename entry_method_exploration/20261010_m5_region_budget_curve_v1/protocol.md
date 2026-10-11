# E175：M5区域扩展的五档公共测试预算曲线

2026-10-10，用户明确要求“多测几个点，最后画一个类似这种图”。本轮在新的独立目录重测 NSG、GT10、原M5与冻结M5REG96，覆盖两集、双K、五个实际L。用户此次授权允许在下述有限范围重新测量同一冻结区域版本；它不回改E174的协议、原结果、锁或STOP，不恢复旧runner，不授权响应调参、追加训练或默认替换。E174原件保持历史身份。

本轮是**已曝光公共test上的描述性budget曲线扩展**。没有新confirm角色，没有新盲测资格，也不以公共test的正信号替代E174未达成的两角色复现证据。当前默认仍为production E99、WebVid GT10-soft-t1、Yandex GT10-hard；原M5继续作为研究方法及独立对照。

## 冻结输入与范围

| 项目 | 预锁值 |
| --- | --- |
| dataset | WebVid `webvid2_5m_light_v1`；Yandex `yandex_t2i_official10M_ip_v1` |
| base | 原WebVid 2,505,000×512；原official Yandex first-10M×200 |
| role / query window | 单一 `public_test`；各自原source-file的行0..9999，保留顺序与重复行 |
| K | 真实K=1、K=100，分别调用搜索；不从K100截断冒充K1 |
| L | 两集、两K均固定 `[200,400,800,1000,1200]` |
| methods | 固定 `[NSG,GT,M5,M5REG96]`；两集两K共享定义、表与额外预算 |
| 正式规模 | 2 dataset×1 role×2 K×5 L×4 methods=80 points；每点3轮，共240正式wall批次 |
| sample / warmup | 每点固定均匀256-query计数；每方法/K/L一次256-query暖机 |
| execution | CPU15；真实单线程；OpenMP/BLAS/MKL等库线程环境均显式设1；串行被测job |

公共输入沿用E173：Web为 `query.test.public10K.fvecs` 与 `gt.test.public10K.ip.top100.ivecs`；Yandex为 `query.test.public100K.fvecs` 与 `gt.test.public100K.ip.ivecs` 的前10000行。源文件、base、原NSG、画像W/Micro-HNSW/hub ID及原residual_joint表的身份由本轮manifest/预检闭合，不能仅凭路径同名替代核验。

本轮行政准备把上述固定窗口复制成原始query f32、GT i32与 `window_rows.i64`。复制会读取、解码**已经曝光的旧GT整数**以核shape、域及窗口；不称GT从未解码，也不新生成精确距离GT。矩阵先于该复制冻结，复制不读取本轮方法响应。`window_rows`只表示这份source-file内的0..9999行号，不是全局source ID；身份/既有字节重叠检查不证明语义IID、全项目未曝光或训练集全语义disjoint。

新增TRAIN、fit、教师、画像/表/主图构建均为0。不拟合μ/V，不重建GT10/M5，不修改base、预处理、归一化、raw-IP或原GT成员/tie定义。历史每dataset跨方法TRAIN≤7200秒的约束与已有超额记录保留，本轮0 TRAIN不重置旧债。

## 冻结方法与原生行为

NSG恢复E173的原图固定enterpoint单入口，路由入口为 `[ep,-1,-1]`，无GT画像路由或posting补全。GT使用原Web soft-t1 / Y hard冻结画像及原三hub顺序、原scalar `search_new`。M5使用完全相同GT路由、主搜索和原残差posting补全。三者均为本轮fresh matched controls，不把E173历史QPS拼入本轮曲线。

M5REG96严格沿用E174的 `region.hpp`、原native/runtime及原M5：保留全部C≤24；R/C沿原fresh scalar重评分和strict TopK合并。从同份已付C分数中，每路由行选不在原GT返回R内的query-best候选；平分沿原arrival，最多3个去重seed，重复不补位。按seed顺序与原物理邻接槽round-robin读取一跳，跳过padding/非法ID、main-vt已见、全部C以及本次X重复；新增scalar距离最多96次，C+X≤120。主vt只读，X严格在R/C之后合并。最多K个R重评分单独计费，不能算入“仅96距离”后漏报。

R/C非有限沿原路径保GT返回；X非有限保成功的完整M5及已付费用；普通异常fatal。预算cap是新增距离次数，不是同wall。不同路由行不证明不同basin，visited不等于已展开；本版是一跳候选生成，不称terminal continuation、暂停/恢复或新主图。只有NSG分支与本轮scope/行政适配允许变化；原GT/M5/region科学函数及三header字节须逐项绑定原E174。

保留C再加X不无条件保证最终GT成员Recall单调。统一精确分数、真实TopK成员及一致tie规则等条件才支持相应论证；本轮有原R重评分、实际FP/strict heap与冻结GT边界。实际损伤必须从逐query输出配对测量，不能用实现结构填0。相对GT的总体救回与相对原M5的区域增量分别报告。

## 完整wall、验证与来源守卫

每(K,L)的四方法按冻结ordinal与round左旋，三轮均完整处理10000条query。timer包括正常输出allocate/init/release、query-loop、实际路由与主搜索、合法域guard、查表/去重、R/C重评分、seed选择、邻接读取/filter/去重、X评分及strict合并。不能以缓存route或先算candidate替代线上路径。加载、身份/hash、GT评价、写盘及独立oracle在wall外，另报实际阶段费用；它们仍计入native job总工期。

每个80 point保存完整10K normal plain，另执行完整独立replay并逐位核返回一致；replay不另存一份packet。核ID域/唯一性及K形状。GT/NSG核原生返回；原M5与M5REG96保留完整10K独立线性merge oracle。20个region point额外保存完整10K×128 i32 trace，布局沿E174：seed3、nC、nX、nSeeds、m5_committed、extension_aborted、C24、X96。原生untimed核C/X实际arrival、seed、main-vt过滤、预算、fresh scalar评分词及独立线性TopK；评分词仅在oracle内核验，trace保存ID/status。

预锁均匀256条另核plain/count words及NDC；计数scope只能写256，不能冒充full10K。`post_dots`覆盖R+C，`new_distances`覆盖X，二者已包含在附加后的graph_ndc，不重复加总。CountDC路径仅作词/计数核验，不作性能。正式timed不采trace/oracle，正常返回在stop前释放、不保留逐轮packet；untimed词核验不称逐timing bits证据。

源码/编译产物/模型与输入hash在性能期前核验并冻结；大base/index完整SHA以及正式前后stat守卫分开记录。窗口提取有完整来源身份与费用收据。正式性能期不并发编译、训练、GT/返回解码、距离、bootstrap、构图或数值分析。行政监控仅看自有进程/phase/终态，不读取本轮partial Recall、比较或QPS响应；出现意外可见需留痕，不改冻结参数。

只有全部两dataset job成功、active为空、80点/240轮及必要原生完整核验均齐备，才解码本轮saved返回与原GT作质量/费用比较。不以部分结果选择L、cap、seed、表、追加角色或改变分析门。runner对自有child的成功、失败、timeout、中断均做明确终态/清理收据，保留partial，不恢复旧runner。

资源约束冻结为RSS≤64GiB、最小free 1GiB、每job≤7200秒、新产物总量≤512MiB。事前artifact估算只作可行性说明，不是实际cap通过证据；10K trace约5.12MB/point，单文件guard必须按新scope适配而不能沿用E174的2MiB。实际超限/失败保原产物与实际费用并停止，不以质量反馈缩窗口、混接旧点或隐性放宽上限。

按冻结schema，80点full plain的ID/距离/entry/profile、256 count与每点audit IDs合计342,809,600 B；20份region trace为102,400,000 B，合计445,209,600 B。两集固定query raw、各10K×100 GT i32与两份window_rows i64共36,640,000 B，主要固定二进制总481,849,600 B，约459.53 MiB；不复制原Yandex完整100K窗口。512 MiB总上限只余55,021,312 B用于scored NPZ、源码/JSON、job层sample IDs、收据、CSV、日志与图。scored NPZ约14 MB、其余约≤30 MB是准备估计，不是实际通过；runner对本轮整个新目录累计bytes实施守卫，报告实际值与估计差异。

## 预锁分析与图的含义

评价覆盖全部80实测点。每个dataset/K/L的同L六组方向为GT−NSG、M5−GT、M5−NSG、REG96−GT、REG96−M5、REG96−NSG，共120 comparisons。每个dataset/K的全部10个 `small L < big L` 实际档对，报告M5(small)与REG96(small)分别对GT(big)，共80 cross-L comparisons；总200 comparisons。跨L只按同一round index对齐，属于顺序完整wall描述比较，不称同state、同时配对或随机独立速度样本。

对每comparison，令每query真实命中集合为返回ID与冻结GT前K的交集；rescue是candidate独有真成员，damage是reference独有真成员。全窗口整数净值=rescues−damages；Recall变化百分点为 `100×(rescues−damages)/(10000×K)`，同时报query gain/flat/loss。K1/K100各自用真实搜索与对应GT，不能把相同救回数的百分比或预算跨K混比。

点表给三轮 `QPS=n/完整wall` 的中位数和min/max；配对比较给三轮 `QPS_candidate/QPS_reference−1` 的中位变化及每轮方向。**配对比中位与两点QPS中位之比不是同一统计量**。同L区域时间税和增量真救回、原M5已有贡献、跨L减少主搜索后的总费用必须分别解释。一升一降记取舍；正向双升只能称这份曝光窗口内的离散观测。

保留冻结seed、2000次paired-query bootstrap描述区间，完整记录种子/重复数及scope。三轮timing不是三个独立质量样本；200 comparisons未作总体/同时校正，CI不是confirm门，也不据其下界新增“复现合格”标签。独立结果审计核整数成员、救/损、wall/QPS、矩阵、trace与身份；若未独立重生bootstrap端点，必须明确范围。

20条region机制行报告实际C/X数量、状态、sample计数以及相对同L原M5的真实救/损。原M5 posting全并集U与旧20K TRAIN GT100全并集U以原件身份绑定；U外X incidence、U外**实际真救回/损伤**分别统计，均为逐query出现次数而非全局distinct ID。教师U内出现不等于当前query可路由取得；U外候选不等于真救回、净收益或语义泛化。不新造teacher、拟合或通过观察选择支持集。

E175不重测MF/GEO/FIRST/REG24，不能把E174别的角色控制当作本窗口的matched信息/seed/cap控制。本轮用于展现固定四方法随预算变化，不识别跨模态性质、modality gap或联合覆盖是增益的独立原因；原跨模态残差监督只是方法来源。E174控制与停止结果仍按原scope引用。

主图固定四panel：WebVid/Yandex×Recall@1/Recall@100；横轴Recall百分比，纵轴完整T1 QPS。每panel四条方法线，各连五个实际L，marker或邻注标明L；纵向三轮QPS min/max，主坐标是三轮QPS中位数。保留所有实测点，包括非单调/回退；不平滑、拟合、jitter或造中间L，不以连线插值宣称等Recall速度。PNG与SVG均交付，CSV可复核每个点；图注写明公共已曝光10K、原raw-IP/T1和range含义。

E173只能作相同窗口/原GT返回词的来源与回归参照；本轮曲线和费用只用fresh E175 matched wall。若核历史words差异需解释实际source/kernel绑定，不能偷偷换分数/GT。E174各4096角色与本公共窗口不拼合，正结果不抹除其未复现结论。

## 完成与停止

本轮授权终点为有限80点/240轮、必要全量oracle及独立结果审计、200比较/20机制行的完整报告和四panel PNG/SVG完成；如资源/实现失败则保留失败、费用与尚缺范围。没有达成收益也完成研究交付。完成后停止本冻结曲线scope，不随公共响应追加L、cap、seed、训练、方法或角色。原GT10默认及旧训练债保持；新的独立确认或默认替换另需新的明确合同与证据，本协议不授予该资格。
