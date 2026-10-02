# ACSG 下一阶段目标与接续

2026-09-13，第5串行会话进行中，E72/E73已完成。整日目标未完成，会话14:17:57前安全交接；唯一写入/实验者，不开并行CLI或子代理。

1. E72 distinct10双集接续门失败，本版本停止，不继续扫宽度/seed。保留Y相对P10 +73命中/失败−6和相对mode30更低路由NDC，但−4命中/失败+1，不能升级为性能GO。
2. E73已完成：仅同hub字节重复画像精简，Web1771/Y2067画像，完整分数集合保持。Y相对P +120/失败−13、对完整mode+71/失败−9，固定两半均正，质量门通过；Web相对P−59/失败+11但对mode+47/失败−2，反证保留。下一E74固定compact唯一新候选，NSG/Fast30K/GT10-hard/Web匹配soft/fullmode10/compact10同历史开发2048五L五轮；实际完整路由/原NSG/output收费，不扫参数、不拼旧速度。该测量按E73前瞻协议执行，不把Web质量门回写通过。
3. 晚间20:00停新训练、20:40停新增query、21:00完整交付。开发反馈先冻结best_all与真实best_new；E34历史validation2000只用于最终对照，不回流训练/选择，held-out不自动打开。所有候选曲线同机同批单线程、五轮轮换，不拼不同批次方法。

所有ANN CPU15/实际threads1、OMP/BLAS/MKL等1线程；完整路由/去重/原NSG/output在独立wall内，GT/count/hash/JSON/build/load在外。原base/rawIP/NSG/GT/真实H815/821固定。画像/构图学习离线；fit/旧train/monitor/cal/audit/aux历史暴露，辅助选择反馈计训练。每阶段source_before/root_after，free>=7GiB并预留晚间，禁止清理旧产物。

[E72报告](entry_method_exploration/20260913_until2100_v1/stage13_distinct_hub_width_v1/report.md) · [campaign状态](entry_method_exploration/20260913_until2100_v1/state.json) · [监督备注](/data/acsg_sessions/20260913_until2100_v1/supervisor_notes.md)。
