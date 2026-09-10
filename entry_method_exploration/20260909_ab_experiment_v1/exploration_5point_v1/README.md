# 五点单线程探索：已完成

NSG、Fast、同一个A+B入口选择模型，两个数据集各2000条validation；L64/128/256/400/800，单seed、单次单线程计时。五L下逐query入口完全相同。

当前判断：`EXPLORATORY_NO_OVERALL_FAST_GAIN`。完整范围已按用户要求完成，不恢复旧大矩阵。

- [完整三指标结果与解释](report.md)、[协议](protocol.md)、[状态](state.json)。
- [原值CSV](results/metrics.csv)、[相对比较CSV](results/comparisons.csv)、[JSON](results/summary.json)。
- [Recall–QPS图](results/recall_qps.png)、[失败率图](results/failure_rate.png)、[完整正确性核验](reviews/final_verification.json)。
- [输入与模型manifest](inputs/manifest.json)、[命令](commands.md)、[成本账](reviews/offline_cost_ledger.json)。
