# E73 同hub字节重复画像精简（前瞻协议）

2026-09-13，第5串行会话，E72已按原门停止。新版本只删除E66 mode bank中同一真实hub、float32整行字节完全相同的重复slot，保留最早slot与其原向量字节，原有顺序不变。预期Web2445→1771、Y2463→2067，构建前逐键独立核对；不删不同向量或跨hub相同向量，不调阈值、支持门、模式数、seed。所有hub至少一行、最多三行，H815/821不变；原P仍在每hub中。完整每hub max画像评分对任意query保持，近似图、路由与NSG结果不保证保持。

compact slot重新编号0..n−1，映射指向原真实hub，另存original_slots.i32与全部duplicate→retained映射。普通M16/efConstruction200/seed20260828按保留原序重建一图/集，ef10、search7slot、distance/slot排序去重3真实hub、真实ID升序入原NSG。最多3slot/hub仍保证7slot至少3hub；variable_profiles=true只放行1–3个slot，旧strict3路径保持。原P、完整mode10与compact mode10三policy。duplicate3P压缩的精确字节集合就是原P，原P控制直接复用已冻结P图，不声称对duplicate近似拓扑有逐位等价。

不改变原base/raw-IP/GT/NSG/kernel/H；不新训练聚类/画像/GT。读取E66已学成W，全部离线来源P-fit20K及历史暴露明确。只用历史aux7952=router_train[2048:10000]及固定3976两半；前128为独立收费预检。fit包含旧train/monitor，cal/audit/aux历史观察，所有选择反馈计训练。E34最终validation与held-out不打开。

构建前冻结所有源、配置、W/映射、保留键、协议/binary；先形状测试1/2/3槽、非法0/4及H不匹配，再构图。两集128预检全部plain/count+16原kernel，通过原P/fullmode旧返回恢复与新slot映射/图bytes后，才各7952主批。所有query CPU15/进程及数值库1线程，串行，无并发训练/分析；工具实际terminal0后独立评分。GT只在原生全部搜索完成后读取。

正常NSG=2*3*(2*128+16)+2*3*(2*7952+16)=97152，HNSW96960，实际构图2。每集预检816/主批47760完整预留，失败不释放，NSG硬限100000。辅助形状检查无构图/查询；不额外运行合成ANN。每job<=600秒/RSS32GiB、13:45后不启动本阶段query，13:50硬停，14:17:57前会话交接。输出<=64MiB，free>=7GiB；大图/输入引用，保留晚间产物余量，不删旧字节。

保存全raw/七slot/返回/两NDC/hits/mask，独立集合评分、旧两控制全恢复、原kernel、graph W/label与7slot距离/去重验证。比较compact对P/fullmode的全量及两半净命中、零命中救回/新增、GT成员增损、route/graph/totalNDC；对应E68完整mode评分参照保持，近似agreement仅诊断。

开发质量标记预锁：对P全量净命中>0、两半>=0、失败不增；对fullmode全量净命中>=0、两半>=0、失败不增。不由此或NDC给性能GO。由于此版本主要假设是在线费用下降，接口/身份验收通过后即准备独立E74同批完整wall，质量门失败仍保留实际compact候选成本反证，不更换向量/参数或放宽原质量门。E74另冻结原NSG/Fast30K/GT10-hard/Web匹配soft/fullmode10/compact10，五L五轮轮换、完整路由+NSG+output独立wall，不能拼旧速度。若实测没有稳定改善就明确报告。

完成E73后报告/图/历史62及四文档、root_after封存，再进入E74。E72与E66/E70旧门保持。整日仍未完成，20:00停训练、20:40停新增query、21:00最终交付。
