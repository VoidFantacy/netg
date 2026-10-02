# HNSW选点最小验证（E35）

双集各128个预定训练pilot、当前GT10原HNSW、L128。强连通成立；主要保留证据为已评分好点仍未入最终三入口，及当前C8真实联合选择空间。没有新训练或QPS。

- [完整报告](report.md)、[冻结协议](protocol.md)、[状态](state.json)。
- [图](figures/selection_diagnosis.svg)、[逐query CSV](results/query_diagnostics.csv)、[质量CSV](results/quality.csv)、[详细JSON](results/diagnosis.json)。
- [结果核验](reviews/result_verification.json)、[资源与调用](reviews/jobs.json)、[最终验收](reviews/final_audit.json)。

有效准备程序为`src/prepare_v2.py`，首版`prepare.py`在0查询时因pilot/fit行身份检查停止；两版与部分输入均保留。`src/probe.cpp`原生旁路记录画像距离访问，`src/analyze.py`在全部返回后读取GT评分，`src/plot.py`作图。完成产物不可覆盖重跑。
