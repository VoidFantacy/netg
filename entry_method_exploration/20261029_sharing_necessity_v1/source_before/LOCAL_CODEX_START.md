# ACSG 当前接续入口

工作区/data/netg/ACSG，分支research/state-20261002，HEAD 96cf05d5410cf51272048cd1f90b4bb194e23c62，近期成果主要未提交。E191于2026-10-28启动、2026-10-29完成，无待恢复矩阵，默认E99 GT10保持。

先读[AGENTS](AGENTS.md)、[summary](summary.md)、[spec](spec.md)、[s-target](s-target.md)、[s-experiment](s-experiment.md)，再读[E191报告](entry_method_exploration/20261028_seven_dataset_scoring_v1/report_zh.md)、[原448点](entry_method_exploration/20261028_seven_dataset_scoring_v1/analysis/all_primary_points.csv)、[密集点](entry_method_exploration/20261028_seven_dataset_scoring_v1/analysis/all_dense_points.csv)、[确认筛选](entry_method_exploration/20261028_seven_dataset_scoring_v1/analysis/confirmed_screens.csv)和[state](entry_method_exploration/20261028_seven_dataset_scoring_v1/state.json)。

七集真实K1/K100：原矩阵448点/1344完整T1轮；另一次密集控制541点/1623轮。112个SQ来源/预算点中，原网格66个通过探索筛选，密集同窗口后12个仍通过；默认E99 GT10保持。

七集原metric/图/GT10保持，真实K1/K100，K1只一个主返回；共享强弱只是旧观测。覆盖链、源外救回、费用和预算前沿分别看；MAIN-SQ无训练遗漏表但仍继承GT10监督。不同实现同执行者，公开test历史曝光，无新系统盲确认。

用户明确授权本轮全部完成后制作PDF，现交付详细中文PDF及CSV。新增大产物/root/acsg-e191-storage（storage链接）；首轮actual timed包的原始字节无损保存在各集raw_packets.tar.zst，原轮次SHA不变；packet_archive.py可验证并精确还原。trace无损gzip并保留未压缩SHA。见[存储合同](entry_method_exploration/20261028_seven_dataset_scoring_v1/storage_format_update.md)。旧E190/E191 seal保持，不自动重跑、扩预算或修改默认。

相对密集GT10保留的12点中，5点被同窗口已有B32/PQ的实测Recall与中位QPS共同覆盖；7点未被当前已测方法网格覆盖。B32仅有原四档补全L，没有密集费用匹配的中间L；未覆盖不能写成优于充分调节预算的B32或全局最优。

可复制接续：请只读核当前分支/HEAD与根文档，再读E191报告和确认筛选。448点/1344轮原矩阵与一次密集补充已结束，无待恢复队列。按我的当前明确任务继续，未经要求不生成PDF。

[本轮详细PDF](entry_method_exploration/20261028_seven_dataset_scoring_v1/E191_七数据集_K1_K100_综合测试报告.pdf)（用户后续明确授权）。
