# E86：用单边真实NSG效用筛选静态新增连接

2026-09-13，第9唯一串行会话。前瞻冻结后执行，不改E33/E84或其停止门。原compact画像/W/真实H815/821/slot映射、原NSG/base/rawIP/GT均固定。E33学删原边，E84按几何缺口投票加边；本版逐条实际加一边，测量完整训练池原NSG响应，再离线筛选静态新边。完整三入口教师不是加边效果，本版直接测实际加边动作。无新颖性或性能预承诺。

候选固定为E84 additions中按(votes降序,source slot升序,target slot升序)排序的前min(64,N)条，Web64/Y47；名单在任何新响应前冻结。每条相对原compact独立干预，不顺序传播。只在原底层空槽追加该一边，保留全部旧边顺序/画像/labels/上层/层级/入口。不扫边数、票数、顺序、阈值或seed。

训练源为全部P-fit20K router_train[10000:30000]，包含旧train4096/monitor1024，非未观察。原E84训练路由全量恢复。逐候选执行全20K真实HNSW plain/count并核验全部入口与7slots/距离bits；保存相对原compact变化patch和完整routeNDC，原始图可由源图+冻结一条边逐字重构。新离线helper只暴露原Policy字段及严格追加/恢复，仍调用原HNSW。单边内存图与首个单边物理图128query回归，各实际新增边与还原字节均检查。

NSG结果仅按相同dataset/router_train源行/query bytes/完整升序三入口/原NSG/kernel/rawIP/L128/K10/GT键复用。先核验E66 fit原P/mode的完整raw，原compact及每条新路由只补缺失完整三元组，所有新查询plain/count一致、每集原compact前32与原wrapper回归；routeNDC总是实际新路由。GT只由Python在原生返回后集合评分。保存缓存源/别名/新patch和成本，不能把旧label或不变query当新增NSG。

边的接受条件预锁：全fit净命中>0，两固定10000半区净命中均>=0，zero失败总数不增加，平均totalNDC<=原compact的1.01倍。平/负边不选；无lambda/连续梯度或按辅助反馈回改。导出所有合格边的并图utility10，另在完全相同source各加一条E84已定nearest其他hub边形成neighbor10控制，度完全匹配但边长不匹配。每source原来最多一候选。若无合格边，仍导出原compact字节作为零更新结果，不称新方法成功。两并图再完整fit真实路由及合法NSG补缺，报告交互，不因并图损伤重新筛边。

所有模型与训练报告在辅助接受前冻结。辅助aux7952=router_train[2048:10000]、固定两半3976均有历史暴露；本版不入边教师，接受反馈算训练。cal/audit历史已用。本版不读E34最终原始query/GT及held-out。仅旧报告摘要有历史最终信息，不宣称全项目隔离盲测。

接受：两集各P/compact/E84完整几何图/utility/匹配neighbor五方法，先128预检后7952，L128/K10/ef10/7slot去重3/原NSG。主utility对P、compact、E84全量净命中>0、两半>=0、zero失败不增；对neighbor全量与两半>=0、zero失败不增，且该集至少一条接受边及并图fit相对compact全量>0/两半>=0/失败不增。至少一集全门通过才另立完整开发wall；另集作为迁移反证。两集全失败即停止本固定候选/筛边版本，不据接受反馈扫门。没有wall不能声称QPS。独立集合评分、zero失败救回/新增、GT成员与query净增损、原compact收益保留/丢失、新损伤、路由/图/总NDC均保存。

预算：训练新增NSG<=32768（各16384，含所有补缺plain/count、基线及reference）；超过则在新批前停止并保留部分状态，不缩样本/抹掉已花预算重启。HNSW训练上限4700000；候选和基线4520000、并图160000、首边物理回归512，共4680512。辅助NSG161920/HNSW161600；本版总NSG<=194688/HNSW<=4861600，失败全额预留且无自动查询重试。全部ANN/训练串行CPU15，各数值库及实际进程threads=1，RSS32GiB，每训练job<=1200s，17:55停止新训练job，18:02停止新辅助job，18:10硬停query，18:23:29前安全交接。若时间不足，固定完整模型交接，不跑半组wall。整日20:00/20:40/21:00合同保持。

资源：本阶段96MiB，session9全部新输出192MiB，额外晚间64MiB/交接8MiB，现场free约6.869GiB，新floor6.55GiB；检查当前余量扣未用阶段额度和晚间预留。所有旧源/图/GT/日志/脏文件保护，source_before/root_after独立，输入与大型二进制引用，不清理。继承GT/P/旧候选生成成本单列未知或原E84测量；新编译/标签/路由/安装/辅助分别记账，operation wall含load/count/I/O不当QPS。

结束同步history75/s-experiment/summary/s-target；新离线安装接口和patch合同同步spec。原阶段不覆盖，完整gate/report/failure图与campaign state/handoff封存。会话完成不代表整日目标完成。
