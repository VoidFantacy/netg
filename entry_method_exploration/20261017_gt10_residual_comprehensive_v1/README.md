# E183 已完成：GT10与残差的七数据集及失败查询综合评测

2026-10-18 新增[四页简版PDF](analysis/concise_v1/NETG_E183_NSG_GT10_残差_简版报告_20261018.pdf)及[简版文字](analysis/concise_v1/report_zh.md)：每图三线，统一L200失败表，无新实验；详细版保留。

2026-10-17。完成7集、645点、1935完整T1批次、15615000正式查询及独立结果审计；32页详细PDF实际渲染与视觉检查通过。当前默认仍为E99 GT10，本轮固定矩阵结束，无待恢复队列。

- [最终32页详细PDF](analysis/delivery_v2/NETG_E183_GT10与残差_七数据集及失败查询_详细报告_20261017.pdf)
- [最终中文报告](analysis/delivery_v2/report_zh.md)
- [645点](analysis/final_v1/points.csv)、[1935轮](analysis/final_v1/timings.csv)、[失败救损](analysis/final_v1/same_L_deltas.csv)、[候选源分解](analysis/final_v1/candidate_coverage.csv)
- [独立结果审计](reviews/independent_results_audit.json)、[边界诊断](reviews/boundary_diagnostics.json)、[费用账本](analysis/cost_ledger.json)
- [PDF实际视觉检查](analysis/delivery_v2/pdf_visual_review.json)、[完整需求完成审计](reviews/completion_audit.json)、[最终状态](state.json)
- [冻结协议](protocol.md)、[配置目录](configs/)、[真实计时返回](results/)、[合法训练产物](models/)

GT10在Deep/SIFT可迁移；B32在两者K100曲线较低、GIST混合，Web/COCO补全曲线受益，Flickr交叉、Yandex K100较低。完整结果、分母与限制均在报告中。source_before与旧报告及delivery_v1保留，delivery_v2只补充解读，未重测正式点或改科学数组。EXECUTION_HANDOFF为当时运行接续历史；当前以本README和state为准。
