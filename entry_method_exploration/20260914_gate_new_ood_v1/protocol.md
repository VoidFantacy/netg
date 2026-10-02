# E96：GATE / GT10 / NSG / HNSW 三 OOD 数据集完整比较

用户要求：GATE与我们的方法、NSG、HNSW比较；预算点较密，最大1500；每点三次平均。用户随后指定WebVid、Yandex、LAION，最多额外一集。此版本主要求为这三集完整base及public test前10000行；Yi仅可选扩展，Llama不训练/评测。已有下载单列获取成本。本协议在任何本轮画像、GATE标签/训练、HNSW构建或方法查询前锁定。

## 数据与固定项

- WebVid 2505000×512，原始IP；Yandex official first10M×200，原始IP；LAION 10004480×512，沿既有manifest的unit-IP。使用原NSG R64/Lbuild100/C512及原search_new，不改变主图或归一化。已有固定底图包含原构建期连接性处理，四方法明确记录该身份。
- QGT来源独立5000；GT10画像fit=router_train[10000:30000]；cal=router_train[0:1024]。Web GT10-soft-t1、Y GT10-hard复用冻结原画像。LAION按原公式构建GT10-hard/GT10-soft-t1，T只从fit GT1 target-hub cosine gap中位数确定；cal L128按hits降序、graphNDC升序、hard优先选择并冻结一份。
- GATE固定512真实hub；训练router_train[10000:20000]，与GT10 fit重叠的10000；checkpoint monitor=router_train[2048:3072]。GT10和GATE训练量不同，均按方法实际量/标签成本报告，不称同离线工作量。所有方法测试前冻结，test只用于最终查询/评分，不用来选择模型或调参；已有public测试历史曝光如实记录，不称全项目新盲集。
- 原manifest及split来源、文件shape/hash、query跨split字节去重核验。LAION/Web公开query同源，作为跨base规模/语料控制，不计独立第三query分布。测试前仅允许test文件身份/去重核验，不进行质量评测。

## 方法

1. NSG：原固定enterpoint，以原search_new(mode2)单真实入口搜索。
2. GT10：原QGT H815/821，单位画像一真实ID；M16/efConstruction200/efSearch10/seed20260828小HNSW top3、真实ID升序、原NSG。
3. GATE CPU/IP适配：512 HBKM真实hub，文档化Sinkhorn平衡近似、8叉三层、20轮、seed42；可复用已验Web512 hub/拓扑Graph2Vec，Y/LAION同参数新建。每hub至多1000节点、最多5hop拓扑子图，Graph2Vec WL2/PV-DBOW、维度等于d、epochs10/mincount5/worker1/seed42；不使用均值池化替代。标签为每训练/monitor query×512 hub的原NSG L64/K1首次发现路径hop；仅返回GT1时为有效hop，否则999。独立observer须与原kernel返回及距离逐位一致，不能以扩展数/NDC代替hop。正负样本按作者release每query最小hop及尾部规则，保留过滤、无命中和全部原始hop/返回。
   模型采用作者release hub tower：fusion Transformer两层（8heads、FF2048），hidden2024、hidden Transformer两层（4heads、FF2048），ReLU/dropout.05，输出d；修正batch维度以保证不同hub独立，不引入query塔。Adam lr1e-5，cosine triplet margin1，batch16384，max200epoch，monitor RouteAcc最早最佳checkpoint，patience20。每hub正负各最多50 query配对，seed42；每batch唯一hub共享前向，记录共享dropout随机性这一CPU适配。输出静态单位hub embedding。线上按release M256/efConstruction256/默认ef10/seed100的cosine HNSW取3真实入口，原NSG；query归一化/路由/映射均计在线wall。以上是明确适配，不冒称作者论文逐位复现。
4. HNSW：完整base独立索引，原IP，M32/efConstruction200/seed20260828，单次构图，最多16离线线程；并行插入调度非确定，保存真实完整有序拓扑/层级/标签。为避免重复存储数十GB原向量，使用gzip无损拓扑文件并绑定base SHA；加载恢复原base向量的float32 bytes。必须全节点检查向量/标签/有序邻接，且序列化往返查询结果/距离一致。该存储不改变搜索算法、精度或计时内流程。

## 性能矩阵与计时

搜索预算固定[32,48,64,96,128,160,200,256,320,400,512,640,800,1000,1250,1500]。NSG/GATE/GT10为L，HNSW为efSearch，两者不等于相同工作量。主指标Recall@10；所有16点完整报告，不能以性能失败为由删点或提前结束方法。3集×4方法×16点=192点，每点3轮完整wall，共576个计时。一次全批warmup、三次轮换方法顺序的独立全批plain wall、一次独立count，分别保存raw IDs/distances/真实入口和route/graph/total NDC；每轮结果一致性核验。QPS每轮=N/wall，主表报告三轮QPS算术平均，同时提供平均wall、N/平均wall、三轮原值/范围，避免混同两个平均定义。

全部性能比较CPU15、进程/OMP/OpenBLAS/MKL均1线程，串行；不与训练/构建/下载/分析并发。计时含query路由、归一化/映射/排序、原图搜索与预分配输出内存写入，不含GT评分/count/hash/文件I/O/模型加载/建图。方法初始化在计时前完成。L不是NDC预算，必须比较实测完整Recall-QPS曲线；不按L的同值宣布公平算力或总体优胜。

报告零命中失败数/率、相对NSG及GT10的配对挽救/新增、query bootstrap描述区间。三轮计时不是独立query样本。所有原值/负点保留。训练时间、标签搜索、GT继承、聚类/Graph2Vec、HNSW构建、准备/核验分账；未知历史从零成本null+原因，不当免费。

## 资源、验收与完成

新目录独立，旧源/模型/底图/GT/封存只读。最多16离线线程、单native作业RSS96GiB。新增持久产物预计4GiB；每阶段检查free>=1.5GiB（准备记录2GiB是早期估算，本锁定值为实际三大库拓扑预算）。不删旧资产；若无损压缩仍不足，保留进度并解决具体存储缺口，不缩减base或方法冒充完成。训练/构图可跨会话持续，实际进程handle/日志核验后接续，不因观察超时重复启动。

先完成输入/GT/源码合同、构图与标签parity、模型导出独立性和序列化核验，再打开最终测试执行；质量结果不作为是否跑全矩阵的门。完整任务只有在三主集四方法192点576wall及独立重评分/线程/原kernel/源码保护验收和图表报告、根四文档/历史卡同步全部完成后结束。可选Yi不替代三主集。

## 一手来源

- GATE release固定commit 229f18dadb791ddede22597e44d5ceb028b104ba：https://github.com/jacksondca/gate
- GATE原论文：https://arxiv.org/abs/2506.15986
- 三主集来源及metric遵循各本地dataset manifest，RoarGraph数据发布：https://github.com/matchyc/RoarGraph
- 可选Yi来源：https://huggingface.co/datasets/vector-index-bench/vibe ，revision 07b387891a221b7b073b83d2f752b76462e5fa03。
