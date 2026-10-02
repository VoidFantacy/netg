# E78 固定图上的子质量范数权重

2026-09-13，第6串行会话；构造/查询前锁定。E77球面收缩A停止，不扫alpha或改选其S/T。新方向保持E73 compact图的完整层级/入口/邻接和子画像方向，只把离线子质量折入向量范数。P首槽逐字不动，不提高ESS门槛删模式，不新增训练查询标签。

主候选mass10：每个保留子slot来自E66合格子模态，rho=child_mass/parent_mass，alpha=rho^(1/d)，W_new=float32(alpha*W_old)，**不再单位化**。P及fallback首槽不动，原child direction在float32舍入范围内保持。对照uniform10：所有子槽乘exp(mean_child(log rho)/d)，平均log缩放与mass一致，区分质量分配信息与一般子画像降权。只有这两种权重，不扫指数/温度/seed，不按aux的单hub损益设置权重。rho及全体child名单仅来自P-fit20K已冻结训练support。

1/d沿用旧E10使用的小尺度先验惯例，但旧E10是原top32内加log(rho)/d；本版本是单个小索引内乘rho^(1/d)，**不是旧加法评分的等价变换**，不称校准概率/似然或创新。相对E77，改变范数而不改变方向，也固定邻接；原IP空间不自动归一化。正内积分数会下降，负分数会向0靠近，不能宣称所有分数/入口/NSG单调保护。原NSG始终使用原raw query/base/IP。

不普通重建图。两候选只对E73 compact序列化图向量区域安装新W；反向替换必须全文件逐字恢复，全部非向量字节、slot labels和映射保持。每集2安装、共4新图文件、0build；physical1771/2067、真实H815/821、ef10/7slot去重3入口固定。在线直接引用E73同SHA evaluator，原API已接受finite非单位W。没有新增在线计算或新维度，但真实遍历/NDC/最终wall仍可能变化。

前检：rho在(0,1)、alpha/统一log质量守恒、P不变、范数缩放和逐行标量导出验证；非法shape/NaN/非法rho拒绝在0查询。四方法P10、compact10、mass10、uniform10，每集128预检→aux7952完整plain/count+16原kernel。P/C回归E73全字节，new graph W/label、完整7slot/三唯一真实入口和集合评分验收。

数据只用router_train[2048:10000] aux7952与固定3976两半，历史暴露/选择反馈计训练；P-fit含旧train/monitor，cal/audit已观察。不打开E34最终validation/held-out，不读新原始query/GT。正常NSG=2*4*((2*128+16)+(2*7952+16))=129536，HNSW129280，0build/4向量安装，硬限132000 NSG。失败整预留不释放，不自动重试。0新合成ANN/GT/梯度；既有evaluator合成合同引用。

所有查询CPU15/实际进程及OMP/OpenBLAS/MKL/NUMEXPR/BLIS1线程，方法/数据集串行，每job600秒/RSS32GiB，14:50后不启动本阶段query、15:00硬停。输出<=40MiB，free>=7GiB并另留32MiB晚间产物空间；引用大输入/图，不清理旧字节。双集工具terminal0后独立评分/统计。

固定主候选接续门：mass对P与compact全量净命中>0、两半>=0、zero失败不增；对uniform全量净命中>=0、两半>=0且失败不增。至少一集通过才在独立E79同批五L五轮wall测mass与所有规定基线及compact、另一集原样迁移对照；不改选uniform或改指数来过门。若无通过，停止本范数权重版本。完整wall含在线路由+原NSG+output、排除GT/count/hash/JSON/build/load，不用NDC/同LRecall当方法成功。

保存权重/rho/源slot/原始全返回、成员得失/query净增损/zero救回新增、全量与两半以及所有成本。历史67及四主文档/库存/交接同步，source_before/root_after封存。会话15:21:01前安全结束；整日20:00/20:40/21:00门及晚间最终冻结规则保持，整日目标未完成。
