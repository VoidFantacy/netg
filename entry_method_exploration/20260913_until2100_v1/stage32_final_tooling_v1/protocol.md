# E91 最终评估工具参数化：前瞻协议

本阶段仅实现和验证晚间最终执行/分析工具，0ANN/训练/构图/GT/QPS，最终query/GT/row载荷不读取、不hash，best_all/best_new不选择。已有E74完整2048原始批只作软件回归，不产生新性能点；在内存截前2000行仅验证评分/形状通路，不能给它重算并称实测2000-QPS。

执行器仅接受另一个独立目录内已冻结的实际selection+config+规则/模型/source/protocol/输入身份；要求实际best_all/best_new明确，禁止控制或零更新充作best_new，所有要求基线同批五L五次完整wall、CPU15各库/实际1线程。E73固定二进制不支持distinct回调，直接拒绝该字段非零或未知在线方式，绝不静默转成普通七slot。任何最终协议/实际选择仍由后继唯一写入者冻结后实施。

评分器参数化n、方法数与L，独立集合/mask、非法/重复ID拒绝、QPS=n/wall五轮和轮换顺序、plain/count/reference、全图向量/映射/slot/五L路由一致、同入口输出相同，保存全部零GT10 query×L×method以及救回/新增、命中正负部与GT成员损益。沿用核验过的graph/slot源实现；不同批次不拼曲线。工具完成不代表最终native实际执行通过。

验证预算：完整E74两dataset55点112640集合评分/45物理图/275既有wall数值和原核验表回归；2000内存评分夹具110000行，不产生文件化ANN输出/新wall，外加明确破坏的ID/mask/callcap/unsupported配置及线程/选择闸检查。全部测试CPU15及库1线程串行，0子进程ANN。预计<120s，16MiB输出封顶，累计192MiB+72MiB备用、6.45GiB floor；实际磁盘约6.627GiB。阶段前保留五根文档及AGENTS/source_before；主要子阶段读监督备注。
