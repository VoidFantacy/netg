# E75 精简画像保留原随机层级：前瞻协议

2026-09-13，第6独立串行研究会话。本版本在任何构图/新查询之前锁定。承接E73字节精简与E74 Yandex局部信号；旧E72停止与所有已封存门不变。仅保留E66 full bank中每个保留slot的原随机层级，区分普通精简重新分配层级的影响；这是一次离线构图控制，不是层级/seed网格，不宣称保留原邻接或性能。

输入完全引用E73 compact W/mapping/tie/original_slots和E66原full图。Web1771/Y2067画像，真实H815/821、原base/NSG/raw-IP/GT不变。先独立std::default_random_engine(seed20260828)与uniform_real_distribution(0,1)恢复全部原slot的floor(-log(u)/log(16))，逐外部slot核对原序列化层级。此步骤0构图/0ANN/0NSG/0训练，最多120秒/16MiB；未通过不构图。原图与普通compact层级变化引用并实核对应身份，最高入口必须映射回原slot，不能按header数字比较。

唯一新图：原完整slot顺序推进，被删除slot在同一新图上getRandomLevel(mult_)一次，保留slot正常addPoint（自行消费一次，不传level覆盖）。保持保留顺序与紧凑外部slot标签。先验证删除/保留映射，构图后全部element_levels等于source_levels[original_slots]，包括零层。剩余节点决定合法entry/maxlevel；若删除原最高入口，允许入口变化。画像每字节/标签/每层邻接合法性独立解析核对，不改原hnswlib/NSG。在线直接使用E73同SHA evaluator，variable 1–3槽、ef10、search7slot→去重3真实ID升序→原NSG，0新增在线学习代码。

合成上限4小图/512HNSW/0NSG：同seed full、普通compact、保留层级compact及其重复构建。覆盖零/正层、跳过随机流、最高入口删除、非同一内外label、距离tie与重复返回；空/越界/乱序/重复keep映射必须实际拒绝。合成计数单列，不冒充真实NSG验收。

开发矩阵每集原P10、E73 compact10、新preserved10，先128预检再完整aux7952；所有反馈均源router_train[2048:10000]历史辅助，固定3976两半，选择反馈计训练。P-fit含旧train4096/monitor1024，cal/audit已历史使用；本版本不新用fit/cal/audit查询，不打开E34最终validation/held-out。不能从元数据余行推断全项目未使用。

正常调用2*3*(2*128+16)+2*3*(2*7952+16)=97152 NSG、96960 HNSW、2真实构图，硬限100000 NSG，失败保留全预留且不自动重试。每job600秒/RSS32GiB、14:40后不启动E75新query、14:50硬停；15:21:01会话安全交接。输出<=64MiB、free始终>=7GiB；不复制大输入/底图，不删除旧artifact。所有原生任务串行、CPU15/进程threads1、OMP/OpenBLAS/MKL/NUMEXPR/BLIS1，GT在搜索后独立集合评分。工具terminal exit0后才开始分析。

原P/compact控制须对E73完整IDs/距离bits/三入口/两NDC/hits/mask恢复，全部plain/count及每点16原kernel通过。保存aligned返回、7slot/距离、源行、图与层级身份、GT成员找回/丢失、query净命中正负部、zero失败救回/新增、全量/两半Recall和NDC。层级身份通过不意味着更接近几何排名或更高NSG效用。

固定每集接续门：新候选相对P10及compact10均全量净命中>0，各自两半净命中>=0，零命中失败数不增加。任何一集通过即可在独立E76完整wall版本测该候选，并将另一集同配置作为诚实迁移对照；无一集通过则停止此控制，不追加其wall/扫seed/ef/层级。NDC不作性能GO。完整wall若执行，必须原NSG/Fast30K/GT10-hard/Web匹配soft/compact/新候选同批五L五轮，完整路由+NSG+output独立计时、GT/count/hash/JSON/build/load在外，不拼旧曲线。

本阶段完成后新增历史64、同步索引/summary/s-target及构图artifact合同spec，保留source_before/root_after与封存。整日20:00停新训练、20:40停新增query、21:00最终交付仍未完成；E34只在晚间最终模型冻结后用于最终对照，不回流选型。
