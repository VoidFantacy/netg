# E34：冻结 HNSW-RL 图的 QPS、Recall 和失败率比较

用户于2026-09-11明确要求“测试一下 qps recall 查询失败率的变化 相对于 nsg fast fastGT10，画图”。这是独立性能补测授权；E33开发门失败及其零QPS记录保留，不重启训练或改选模型。本协议在本轮新搜索前冻结。

固定 E33 cal 选定图：WebVid seed20260912/step400，Yandex seed20260911/step300。对照 NSG 固定原入口、原 Fast30K（HNSW seed100/legacy堆顺序）、FastGT10-hard。WebVid另列GT10-soft-t1原图，因其才是RL的直接起点；Yandex起点即GT10-hard。Fast30K与GT10的画像训练量和构图seed有历史差异，不能将二者差异全归因GT目标数。所有画像、真实ID、静态小图、NSG/raw-IP保持；没有新的训练、模型选择、标签生成或held-out访问。

两数据集使用E24已有validation前2000条相同query/GT100/row IDs；这些查询曾在多轮研究中使用，不能称新盲测。L固定64/128/256/400/800，K10。WebVid5方法×5L，Yandex4方法×5L，总45点。

计量复用E33已验收、没有训练hook的evaluate二进制（本目录逐字复制并记录来源），加载冻结物理图。CPU15，进程/OMP/OpenBLAS/MKL均1线程；两集串行，一次只测一个方法，不并发训练、编译、数值分析或其它性能实验。每点一次完整warmup后5轮独立plain整批wall，方法顺序按dataset/repeat/L轮换。QPS=2000/整批wall，主值取5轮中位数、同时保存全部原值和min/max。计时包括原始query的路由、真实入口排序/映射、原NSG和预分配输出写入；GT/count/hash/I/O/load/build均在timer外。warmup仅首轮一次，后续轮为轮换方法的warm-cache运行，不称每轮单独预热。另完整count和每点16query原kernel核验，所有轮IDs/距离bits/入口必须一致。

Recall@10=命中数/10；查询失败严格R@10<0.1即hits=0，与程序运行异常分开。保存aligned返回ID/距离bits/入口/hits/mask/路由与NSG NDC。每点核验失败数/率及总NDC；同L对各基线计算ΔRecall百分点、QPS相对变化%、Δ失败率百分点和rescued/newly_failed/still_failed，配对bootstrap2000次seed20260915给Recall/失败差的描述性95%区间。timing轮不是独立Recall样本。

产物包含Recall–QPS、QPS/Recall/失败率对L、RL相对各基线的三指标变化图，PNG/SVG及CSV/Excel。相同Recall比较仅限双方实测非支配点覆盖的共同区间，在25/50/75%位置作明确标注的log-QPS线性插值，不外推、不选择新模型；同时报告5轮范围。全部正负点保留，不因单点QPS差而宣称稳定方法收益或更换默认。

正常原NSG调用45×(7×2000+16)=630720，修复另限16384，硬上限647104；失败完整预留不释放，不覆盖输出。每集查询进程≤1200s、两集总≤2400s、RSS≤40GiB、本目录≤256MiB、/data可用≥10GiB。若身份/输出/资源或重复parity失败，保留失败原件、停止依赖工作，仅允许在修复限内处理实现问题，不扩搜索或训练网格。前后核验实际依赖SHA及E33完整目录，原大型资产不复制、不改写。同步根四文档与新增历史23，E33报告/状态/图/模型不改。
