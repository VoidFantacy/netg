# GT10共享入口变换实验

`SHARED_TRANSFORM_EXPLORATION_COMPLETE_NO_FORMAL_GO`。本轮没有建立共享线性或小MLP优于原GT10的稳定双数据证据，保留原已冻结GT10路线。

- [完整研究与实测报告](report.md)
- [主Recall–QPS图](figures/recall_qps_main.svg)、[全部基线](figures/recall_qps_all.svg)、[相对速度插值图](figures/interpolated_speed.svg)
- [Excel图表数据](chart_data.xlsx)、[全部点CSV](results/all_points.csv)
- [冻结协议](protocol.md)、[方法/文献依据](research.md)、[最终验收](reviews/final_audit.json)

输入按绝对路径绑定既有E24/E23数据和原NSG，身份见reviews/protected_before.json；依赖环境见reviews/machine.json，编译参数见bin/*.build.json。脚本拒绝覆盖已有搜索和训练输出。本版本真实NSG调用3,377,147次，训练12次，held-out未访问。
