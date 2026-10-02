# E97 修正GATE后的五数据集 Recall@1/100 对照

用户于2026-09-15授权修正、训练、测试及绘图，并明确排除LAION。新版本独立于E96和审查原件；不用旧K10输出冒充K1/K100。

数据：GIST1M本地原始960维L2；Deep官方10M/96维L2；SIFT使用BIGANN官方前10M/128维L2，独立learn/public query，替代旧本地非标准11.16M及从base抽query的输入；WebVid/Yandex使用E96已冻结原IP数据/NSG、训练分区及兼容资产。SIFT来源变更明确标为BIGANN-SIFT10M，不与旧SIFT数值拼接。

新三集从独立learn取5000 QGT、20000 fit、1024 monitor、1024 cal，排除与public query的精确重复并保存原行。GATE训练使用fit前10000；GT10使用全部20000，每query总质量1。精确GT100以完整base计算，分片保存及核验；新三集不复用来历或base规模不明的旧GT。测试使用全部公开query：GIST1000，Deep/SIFT各10000。Web/Y原训练角色和test10K保持；存在历史曝光如实记录。

方法：NSG原固定入口；GT10-hard主线和固定GT10-soft-t1辅助；GATE修正版；完整HNSW。新三集GT10固定H800，旧Web/Y复用E24 H815/821画像；GATE各512真实hub。soft温度仅由fit的GT1目标到hub最高/次高cosine差中位数确定，不看测试选择温度。所有模型、配置、种子在性能测试前冻结。

GATE修正仅从每query负例中去除全部正例，再执行可用性过滤和triplet配对，断言正负互斥。保持真实路径hop、32×16聚类、5近5远/5hop/1000节点子图、WL2/Doc2Vec、batch-first网络、cosine triplet、Adam1e-5、batch16384/max200/patience20和同hub共享前向。1000节点上限及统一项目kernel属于披露适配。Web/Y兼容hop及特征可复用，但triplet/模型重建；不根据public结果改网络或超参。

新三集底图调用原IndexACSGFlat的NSG构建链，R64/Lbuild100/C512及原连接性处理；主图距离保留原L2。HNSW使用同一完整base、原metric、M32/efConstruction200、seed20260828。画像路由仍为cosine方向代理，不对整个L2底库作单位化。库和原kernel不改。

每数据集、每方法分别K1/K100。K1预算沿E96的16点32..1500；K100的16点100..1500以config.locked.json为准。每点一次完整warmup、三次独立plain wall、一次count，重复输出ID/距离/入口bits一致；QPS报告三次N/wall均值及范围。CPU15、进程及OMP/BLAS/MKL1线程、方法串行，无并发训练/构图/下载/分析。计时包含完整路由、映射、搜索与预分配输出，排除GT评分/计数/磁盘IO/加载/构建。

Recall@1为返回top1与exact GT1相同；Recall@100为top100集合交集/100。仅在训练监控使用hop标签，不新增Recall@10性能或开发测试。按query保存aligned完整返回、三入口、NDC、失败配对；完整800点/2400次wall（五集×五方法×二K×16L），不得按结果隐藏预算点或拼接赢家。

离线可16线程，峰值RSS上限96GiB，磁盘free至少2GiB。已有资产不覆盖；中断阶段保留日志/部分产物并按阶段身份恢复，失败不得冒充完成。首次编译、合成L2/K1/K100/metric拒绝/标签交集修复必须通过，再进入真实数据；任何修正用新源码身份及修订记录，不静默替换已训练模型。每阶段记录实际wall/线程/RSS，已有未知成本标null。

结果交付：完整CSV/逐轮时间与逐query数组；两张五集Recall–QPS主图及单集PNG/PDF，失败率图；模型/数据/源/索引身份、成本与报告。验收覆盖全部预算、所有返回/GT合法性与评分、单线程、重复一致性、模型冻结、图可读性。性能没有改善也完整报告，不以无收益为由停测其余方法。
