# E82 新目标画像的完整排名与真实三入口效用

2026-09-13，第8唯一串行研究会话。本协议在新增排名/查询前冻结。承接E79/E80/E81双集原门失败，三个固定bank均原件复用；不重训，不扫目标权重/seed/ef，也不改旧门。原NSG/base/rawIP/GT/H815/821固定。

完整比较固定三个新bank target10/conditional10/joint10，每hub所有物理画像用raw query与float32 W的float64内积取最大，按分数降序/真实hub ID升序取前三，再canonical升序注入原NSG L128/K10。无几何近似阈值，近tie按1e-5 max(1,||q||)标记但仍完整保留。它是离线诊断，不是可部署扫描、NSG效用oracle或QPS。精确P和原query-mode完整排名及真实NSG来自E68/E69，逐项核验相同query/源行/metric/核；原compact保持全部max分数集合，显式核对旧original-slot重构身份。

缓存池只用五个approx P/compact/target/conditional/joint及E69 exact_P/exact_mode共七项。查询键必须同时绑定dataset源namespace、source row/query bytes、canonical三入口、base/NSG/kernel、rawIP/L128/K10/GT。所有相同键碰撞的返回ID/距离bits/graphNDC/hits/mask须一致；不拼接不同搜索的GT成员，不复用routeNDC。三个新exact的缺失键按query/三入口去重；先冻结coverage和精确预算，再查询。每集对原P前128条plain/count回放并16原kernel，所有missing plain/count并前min(16,M)原kernel；正常调用2*(128+M)+16+min(16,M)，两集上限96192，0HNSW/0构图/0训练/0新GT/0编译。复用E69已验inject.so及native包装器，不执行旧runner的预算/截止。失败完整预留，无自动重试。

只有双集native工具实际terminal0后独立集合评分、重组aligned完整结果。报告三bank相对各自approx、exact_P、exact_mode、approx P与compact的全量/两半净命中、成员得失、救回/新增零命中、graphNDC、近似排名一致/近tie和旧compact收益保留/丢失/新损伤。零失败严格hits=0，固定两半3976/3976。模型选择反馈全部计训练。

前瞻诊断门：每个bank逐dataset独立须相对exact_P和compact全量净命中>0、两半>=0、零失败不增、graphNDC<=1.01；相对本bank approx全量净命中>=0。至少一bank一集通过，才支持为该bank另立轻量近似改进；多个通过按跨两集总净命中（相对compact）、少失败、joint/conditional/target固定顺序冻结一个。另一集保留迁移反证，不只报告阳性。无通过则停止把新目标bank损伤仅归近似误差；原compact单独局部信号不否定。门不是性能GO，不从E34最终反馈选型。

仅历史aux7952=router_train[2048:10000]，含今天既有选择反馈；P-fit20K含旧train4096/monitor1024，cal/audit已暴露。E34历史validation2000留晚间冻结后最终对照，held-out不打开。元数据余行不代表项目未使用。

阶段输出<=32MiB（refs/config/ranking<=5、raw/重组<=12、表图/快照/证据<=15），会话累计新增<=192MiB；现场free约6.934GiB，扣192+64晚间+8交接MiB后仍约6.676GiB>新6.65GiB下限。旧各阶段预算不改，所有旧文件不删不改；大输入/二进制/图引用。CPU15/实际进程与OMP/OpenBLAS/MKL/NUMEXPR/BLIS1，两个dataset串行，进程<=600s/RSS32GiB，16:35停止启动、16:45硬停；会话17:25:25前安全交接，20:00/20:40/21:00整日门不变。

结束后保存独立报告/图/原始结果/source_before/root_after/最终seal，历史71及四主文档同步。新增扫描/补测成本完整分账，继承GT/P及旧训练成本未知，不能以缓存或进程wall构造QPS。
