用户最新授权补充：若空间不足，可以删除原始压缩包。当前已通过本轮LAION未完成构建目录转存解决空间保护退出，未因此追加清理；如再次触发容量不足，先确认具体原始归档身份，再按授权删除归档，保留已展开工程/数据/图/模型/实验结果。此授权不改变三集四方法16点/三次单线程平均、结束后看日志的要求。当前supervisor PID35499/session5625，functions等待cell57；不要从旧PID重新启动。

当前监督进程 PID35499 / session5625；日志 logs/supervisor.storage_resume.log。已验证正在从LAION检查点恢复，等待进程退出后再读取结果或故障日志。

# 最新接续：磁盘保护退出后恢复（优先于下文旧PID）

2026-09-14 21:12：supervisor session36835/PID8606已明确以exit1结束，原因是LAION全节点HNSW在最终gzip保存时触发/data剩余1.5GiB下限。三集release10 GATE、标签、LAION GT10开发选择以及Web/Y全量HNSW已完成；public正式矩阵尚未开始。未完成的LAION hnsw目录逐文件SHA校验转存到/root/acsg-artifacts/20260914_gate_new_ood_v1/laion10m_acsg_v1/hnsw，原位置为符号链接；保留全部10004480节点检查点和348345797字节的中断gzip。原base/NSG/历史模型与查询均未移动或删除。data空余恢复到2809409536字节。原编译程序可直接从全节点检查点完成保存与核验，之后preflight/三集192点576wall/分析继续。存储转移证据reviews/storage_recovery_20260914T2113/manifest.json。等待新监督进程终止信号后再读结果/故障日志。

# 用户最新运行偏好（优先遵守）

用户要求估算实验耗时，不要反复看日志，实验结束再看。已依据E73历史单线程QPS外推：正式矩阵中央估计6.22h，离线剩余35–90min，整理10–20min；2026-09-14约19:30北京时间告知中央剩余7–8h，保守5.5–13h。证据在time_estimate.json。之后等待监督进程完成/失败事件；只在终止后读结果或故障日志，不再每分钟tail。current active supervisor session36835/PID8606，训练子进程会变化；用户偏好不削减三集/四方法/16点/3次计时。

# 最高优先级：release10采样修正已生效

当前supervisor PID8606/session36835，日志logs/supervisor.release10.log；Web新训练PID8878。此前PID3077/5931已明确停止，不再接续其旧模型。发现旧sample_negb_vectorized在n_far=0时[-0:]取全部邻居，Y图min_degree1触发；pinned release实际固定SAMPLE_SIZE10，现三集采用5近+5远并保留cap1000/hop5。见sampling_amendment.md及其锁定SHA。全部仍未public测试。

common.py常量GATE_MODEL=gate_release10_v2，GATE_FEATURE_READY=gate_release10_features.json，GATE_GRAPH_FILE=gate.release10.graph2vec.f32；prepare/train/supervise/verify/analyze均已统一。Web新特征54.31s完成并已训练。原Web/Y gate目录和旧子图/Graph2Vec保留；只在记录SHA/大小后回收明确已取消Y训练的临时latest.resume文件，best/history/labels全部保留。Web/Y labels、hub不依赖Graph2Vec，继续复用；Web完整HNSW已完成；Y完整HNSW未开始。监督顺序改为先完成三集features/labels/new-train（LAION另cal选择GT10），再完成剩余HNSW，最后preflight/正式192点/576wall/分析。根summary/spec和method_notes已修正旧采样模型身份。当前formal/analysis/report仍未完成。

# 最新接续（优先于下面早期记录）

环境已重启一次，旧PID16280/17440和session40017终止，禁止据此再启动。当前新supervisor PID3077，工具session90686，日志 `logs/supervisor.resume_boot2.log`；Y标签子进程PID5163。Web全部离线模型及HNSW已经完成；Y hub/Graph2Vec已完成（features699.37s，HBKM665.79s），正在新标签阶段。以/proc和state再次核验真实进程。

后续恢复支持已经实现：`train_gate.py`逐epoch保存/恢复Adam、torch RNG、模型、history/patience；`resume_hbkm.py`用原计算逐轮保存标签/质心/RNG（小样本与原算法逐位核验通过，当前已跑Y仍为原函数，LAION将使用包装）；`checkpoint.hpp`为HNSW保存部分有序拓扑和构建RNG（2048→4096续建与未中断版全部邻接逐位相同，128query一致）；`evaluate.cpp`支持按完整L块恢复，部分L所有方法的旧raw移入incomplete_attempts并重测该L，保存boot_id，各L仍warmup+3plain+count。初始bin/source已保存在bin/*.initial、source_versions、native_build_identity。新build_hnsw/evaluate已编译替换当前E96二进制，原库/源码未改。

尚无public正式测试。全部三集离线结束后仍需preflight，192点/576wall、独立评分/图表和报告与最终验收。重启丢失的在途离线成本不可冒称完整精确计量；最终应注明不完整部分。

# E96 正在执行；不得重复启动已在运行的阶段

用户最新目标：在 WebVid、Yandex、LAION 比较 GATE、当前 GT10、NSG、完整 HNSW；16 点最大 L/efSearch1500；每点单线程三次平均；最终交付 Recall–QPS 图及失败查询率。主目标尚未完成，不把准备或训练完成当作总任务完成。

有效协议为原 `protocol.md` + `hbkm_provenance_amendment.md`，并见 `config.effective.json`。三集 HBKM 均两层32×16；原8×8×8记录误读在新两集 hub 构建前依据现有 Web manifest 修正。最终失败为 Recall@10=0，补充 GT1 未出现在返回top10的比例。三组public test各10K，Y取前10K，Web/LAION同源查询须披露。

目前实际完成：Web所有输入SHA/全base与原图内向量逐位核验，512子图/3276735内部边/Graph2Vec实物来源核验；992次原search_new与首次发现hop observer返回逐位一致；11024×512新标签搜索151.235s；GATE训练48epoch/739.515s，最佳epoch27，监控可用843query上的RouteAcc0.0711744，只作checkpoint选择，绝非最终Recall；Web完整HNSW正在构建。

2026-09-14当前主要进程：supervisor PID16280（工具session40017；`logs/supervisor.log`），Web HNSW PID17440（它的子进程，`logs/hnsw_webvid2_5m_light_v1.log`）。训练PID15967/session42343已经正常结束。使用/proc真实命令、父子关系和完成marker核验，不能仅依据PID或旧文字重新启动。当前supervisor是在旧环境配置加载的版本，后续 `prepare.py` 已在NumPy导入前显式OPENBLAS16，因此HBKM按16线程执行；其余离线至多16、正式全1/CPU15，单阶段串行。

继续链已排定：Web HNSW保存/全量往返 → Y features/labels/train/HNSW → LAION features/labels/train、GT10候选开发集选择、HNSW → `verify.py preflight` → 三集各64点/192wall → `analyze.py`。全部离线结束前不启动正式public评测。源码已写入，labels/build_hnsw/evaluate编译通过；HNSW4096节点合成完整向量/标签/有序邻接和128query往返通过。大图还须各自完整验收。

`src/supervise.py` 首次加载版本没有单例锁，一次替换waiting-only supervisor时原进程已进入建图；第二次启动被现存output保护拒绝，未重建或覆盖原图，原进程一直保留。失败尝试及纠正分别在 `reviews/rejected_duplicate_supervisor_stage.json`、`reviews/supervisor_correction.json`；state已恢复真实active进程。最新脚本已有进程身份和flock双保护。

最终还需要：确认完整192点/576wall与每轮IDs/distances/entries bit parity、独立set重评分和线程/保护验收；查看实际PNG图；写最终report.md、实验复盘88及根四文档/历史索引；完成审计后才能把goal标complete并给用户图及结果。分析脚本会生成CSV与图，但不会替代这些最后的人工结果解读/验收。

文件均在独立E96目录。不要触碰原源码、GT、旧图/画像、dirty内容。/data空余较小，阶段要求保留>=1.5GiB；HNSW使用gzip完整有序拓扑并绑定base SHA，向量从原base逐位恢复。可选Yi/Llama下载留作获取记录，本次不追加评测。
