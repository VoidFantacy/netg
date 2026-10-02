# E34 HNSW-RL性能补测

[完整报告](report.md) · [协议](protocol.md) · [Recall–QPS](figures/recall_qps.svg) · [三指标曲线](figures/metrics_by_search_L.svg) · [相对变化](figures/rl_changes.svg) · [Excel](chart_data.xlsx) · [状态](state.json)

两数据集45点、每点2000历史validation query/五轮单线程wall，冻结E33图，不新增训练。失败=Recall@10<0.1（零命中）。原始aligned结果保存在results/数据集/方法_L目录，派生表和所有计时原值保存在results/*.csv。
