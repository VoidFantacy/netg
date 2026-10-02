# E84 训练查询排名缺口驱动的小图shortcut（前瞻协议）

2026-09-13，第8唯一串行会话。E83同hub/普通近邻追加几乎无NSG效用，原门停止；本版本改变监督来源和连边对象，不扩大其边数/换seed。固定E73 compact W/mapping/全部原边/上层/层级/入口、真实H815/821与原NSG/base/rawIP/GT。

训练只用P-fit20K router_train[10000:30000]的原raw query，含旧train4096/monitor1024。已有画像由GT构造，但新连边训练不读GT或NSG返回。先用原compact真实HNSW ef10/search7slots得到每query实际排序首slot s及三真实hub；独立float64完整bank perhub-max选排名前三hub，各hub取最高分slot（并列slot小）。对每个不在实际三hub的完整排名目标slot t，若t不是s/原s邻居且s有空底层容量，给(s,t)一票。每query每目标最多一票；不使用GT/NSG效用或aux。每个s只追加最高票数t（平票slot小）且票数>=2，最多一边，不替换旧边，不重建图。不从多个阈值/目标/seed选择。它是几何排名缺口监督，不是NSG效用教师；精确排名并非普遍更好，E69的Web/Y反证保留。

控制neighbor10在完全相同source节点各加一条最高float64画像内积的其他realhub非邻居（平票slot小）。同节点度/原边完全匹配，新增边长度不匹配。主方法shortcut10，控制不能自动晋升。相比E33单画像原边效用RL删除，本版本固定多画像且从fit真实近似缺口投票追加新边、0梯度；相比E83同hub规则，追加是query共同响应驱动的跨hub目标且每节点至多一边。无文献新颖性声明。

A：独立route-only可执行文件调用原E73同源码Policy，plain/count全fit20K及aux前128回归已有compact真实7slot/距离/三入口/routeNDC，读取query前缀但不读GT/NSG/base大图。双集总2*(20000+128)*2=80512 HNSW、0NSG/0build。保存全部aligned slots/distances/entries/NDC及实际线程/CPU。新helper独立编译，不改旧binary/kernel；校验通过后由Python完整排名/投票/2票门输出两主/两控制物理图，共2次离线图监督训练/4边安装/0画像训练/0普通构图。所有几何目标/票/源行/原slot保留，可独立复算；近tie标记、不声称SIMD bit parity。两套模型都完成/冻结并通过全部source/byte/目标/度/原边/原可达集合验收才进入B。

B：双集P/compact/shortcut/neighbor四方法，各128预检后7952辅助plain/count+每方法16原kernel。129536 NSG/129280 HNSW、硬NSG132000；总HNSW209792，失败完整预留无自动query重试。原P/compact全字段回归，图W/labels/7slot/距离/三入口/原kernel/集合mask与相同三入口真值验收。唯一执行者CPU15/所有数值库和实际进程1线程，两个训练route job及四NSG job串行，工具真实terminal0后分析。

主方法对P与compact：全7952净命中>0、两半3976/3976>=0、zero失败不增；对neighbor：全量/两半>=0且zero失败不增。至少一集过门才另立完整双集开发wall，另一集保留迁移反证；六方法级对照、原NSG/Fast/GT10匹配起点与实际新方法、五L五轮完整在线wall。若双集未过，停止这一固定监督/投票规则，不扫阈值/加边数或按aux改投票；任何未来训练需新协议。失败严格GT10零命中，全部旧收益丢失/新损伤、成员得失、路由/图/总NDC分列，无wall不能称QPS。

aux7952/两半已历史暴露且接受反馈算训练；cal/audit历史使用。E34历史validation2000留晚间冻结后最终对照，不回流训练/选型，held-out不打开。A用于回归的aux128只比已有路由，不能把其加入连边票数；没有未观察数据声明。

资源前瞻阶段64MiB（binary4、fit路由/排名/票<=8、四图<=16、raw<=12、源/根前后/表图/冻结<=16、余8），session累计192MiB及晚间64MiB/交接8MiB，free下限6.65GiB。当前之前两阶段约30MB已计入现场free，引用输入/画像/原图不复制；旧预算/seal不改，不清理历史。每A单job<=300s/RSS4GiB（不加载NSG），每B<=600s/RSS32GiB；17:00停止启动B、17:10硬停，会话17:25:25前安全交接。若完整wall赶不上本会话就冻结交接，不跑半组。20:00/20:40/21:00整日门保持。

结束后history73/四根文档/API与offline artifact合同同步，root_after/finalseal/失败图/campaign handoff完善。整日目标未完成。
