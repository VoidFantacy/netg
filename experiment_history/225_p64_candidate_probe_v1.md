# E225 P64 候选探针分流

2026-11-22。COCO 真 K100，沿 E223 共享图、画像、组池、P64 投影和主搜索。在全池扫描前计算至多八个新候选的粗分，主返回和探针特征用于预测相对完整 B32 的净增。P64 分支复用查询投影和探针粗分，另一分支完成完整 B32。E223 公共第二窗复用 E224 身份拆分，2,048 fit、1,024 cal。11 档结构回放与 E223 分支输出逐字节相同。L184 校准比旧线性门少触发 65 条，多净增 20 个，仍距目标 42 个。探针后走 B32 的回放增量 6.84 μs/query。

正式公共前 3,072 个身份与 fit/cal 和其他模型训练角色互斥，属于历史曾用窗口。11 档 L 两臂、22 点、44 完整 CPU15 单线程批次、135,168 次计时查询。33,792 条诊断的分流输出和探针分数复用通过复核。探针 L184 为 96.6380% / 2,728.2 QPS，GT10+B32 L192 为 96.6247% / 2,797.9 QPS，多 41 个正确成员，QPS 慢 2.49%。L184 开启 77.9%，完整耗时较同 L B32 多 21.75 μs/query，降 L 空间 12.62 μs/query，达标后仍慢 9.13 μs/query。L200 按预锁全关。

八个启用且有同期 B32 达标点中，四个平均快、两个慢遍仍快。B32 实测召回覆盖范围内按连线描述，九点仅一处略高。完整 B32 保留补点基线。

[协议](../entry_method_exploration/20261122_p64_candidate_probe_v1/protocol.md) · [报告及两条曲线](../entry_method_exploration/20261122_p64_candidate_probe_v1/report.md) · [正式点](../entry_method_exploration/20261122_p64_candidate_probe_v1/analysis/points.csv) · [救损](../entry_method_exploration/20261122_p64_candidate_probe_v1/analysis/gate.csv) · [同期配对](../entry_method_exploration/20261122_p64_candidate_probe_v1/analysis/matched.csv) · [封存](../entry_method_exploration/20261122_p64_candidate_probe_v1/seal.json)
