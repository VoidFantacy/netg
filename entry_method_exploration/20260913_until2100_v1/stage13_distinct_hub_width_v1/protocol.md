# E72 固定画像图的真实hub计宽控制（前瞻协议）

2026-09-13，第5串行会话。仅改小HNSW的结果保留/停止规则，固定E66原P/duplicate3P/mode3P画像、物理图、H815/821、base/raw-IP/原NSG/GT和最终三入口。不是新的概念，使用本地BaseSearchStopCondition接口适配现存float-only图，不改原hnswlib/ACSG，不增加ef或模式网格，不训练或重建实际图。

每query结果堆按真实hub引用计数；width=10。consider=(distinct<10 or distance<lowerBound)，stop=(candidate_distance>lowerBound and distinct==10)，remove_extra=(distinct>10)。add/remove使用实际external label映射，移除dist忽略；无平行影子距离堆。回调对象每query清空全部已触及引用，内部返回ID显式转换external label及画像row。同hub最多3slot，所以最终候选最多30；保存全部候选及实际长度，padding不算候选。mode/duplicate完整候选按(distance,slot)排序，去重取三真实hub后升序。singleton控制保留原堆反向pop前3的子集，再按原external结果堆顺序恢复并canonical；不得先重排全池再截3。singleton恢复必须实测通过。

矩阵固定六policy：P10、P-distinct10、duplicate10、duplicate-distinct10、mode10、mode-distinct10。先合成平分/重复/内外ID不同/加删引用/复位/不足3hub拒绝，以及两集前128 aux真实plain/count+16原kernel；全部通过再各7952完整aux，固定3976两半。旧E70 P30/mode30只作同query同图身份下质量/路由NDC参照，不复用旧QPS。真实额外route-only预检不运行，合成最多4图/1000HNSW，另账0NSG；合成失败只允许身份/代码缺陷修复，保留原件，不改变上述数学规则。

历史aux=router_train[2048:10000]，完整输入直接引用。P-fit20K含旧train/monitor，cal/audit/aux历史暴露；所有动作选择反馈计训练。本阶段不打开E34最终validation或held-out。query/GT/row namespace及所有W/图/mapping/源/binary先SHA冻结，大base/NSG继承已验SHA并比较stat。单线程CPU15、OMP/OpenBLAS/MKL/NUMEXPR/BLIS1；唯一执行者，所有job串行，工具实际terminal0后才评分/作图。GT不进入路由/原kernel。

正常NSG=2*6*(2*128+16)+2*6*(2*7952+16)=194304；HNSW193920，实际图build0。每预检1632、主批95520完整预留，失败不释放，硬限200000，不自动重试。合成4图/1000HNSW硬限独立。每job<=600秒、RSS<=32GiB，13:35后不启动本阶段新query，13:45硬停；本会话14:17:57安全交接。输出<=64MiB、free>=7GiB，保留晚间预算，所有大输入/源图引用，禁止删除/覆盖旧字节。

验收全部singleton P返回/距离bits/入口/路由和图NDC恢复，三个普通控制恢复E66；plain/count/原kernel及GT10集合独立重评分；候选长度<=30、distinct==10、合法唯一slot、距离和映射/排序/去重、padding、每query状态复位。strict failure=0 GT10 hits。报告完整及两半净命中、救回/新增、GT成员与逐query正负部、完整route/graph/total NDC、候选占位及E68完整排序agreement；不将agreement/NDC当性能。

后继完整wall门按dataset分别冻结：新mode对P10全池净命中>0，两半>=0，零命中不增；对原mode10与mode30全池净命中>=0，两半>=0，零命中不增；新mode平均routeNDC<mode30。至少一集通过才另建同批五L五轮完整wall协议，另一集同矩阵保留迁移反证。全部失败则停止本单版本distinct控制，不扫新width/seed或改停止规则。门只是历史辅助接续，E66/E70原门不改，默认不自动替换。若后续wall，包含NSG/Fast30K/GT10-hard/Web匹配起点及真实新方法，全部重新同批计时，不拼旧曲线。

阶段完成保留全raw/配置/调用/候选，报告与图、历史61和四主文档同步，root_after指向快照。整日目标仍未完成；20:00停训练、20:40停新增query、21:00最终交付。
