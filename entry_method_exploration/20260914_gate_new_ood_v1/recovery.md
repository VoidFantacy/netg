# 环境重启后的接续

运行环境在Web全部模型/全量HNSW完成、Y输入准备完成后重启。通过 `/proc/uptime` 仅124s、新boot_id `e40bd4f9-766e-4364-b90e-79500fd1c482`、原PID不存在及工具session40017不存在确认终止，而非把观察超时当退出。新supervisor从现有完成标记接续；未重建Web，没有正式性能点混用不同boot。

后续训练增加每epoch的滚动恢复状态，含完整模型、Adam状态、torch随机状态、已完成epoch/history、最佳epoch和patience。它在成功完成并保存选中模型后删除；最终best.pt、W、配置、训练历史和恢复记录保留。重启后按优化器/RNG精确续训，不以best.pt代替训练状态重开训练。恢复功能不改变网络、优化器、数据、损失或停止规则；新增写盘成本计入实际离线耗时。Web已完整结束，不为这一工程修正重新训练。

HBKM包装保存原始逐轮标签/质心/随机状态；HNSW每百万点保存部分拓扑和构建RNG；完整图完成后删除滚动恢复点。HNSW保存与恢复的中间状态在4096点合成图上与未中断构图逐节点、逐层有序邻接、向量、标签完全相同。正式评测按完整L块恢复，未完整提交的L块四方法重新warmup/三次计时/count，旧raw与计时保留在incomplete_attempts和旧日志，完成点记录boot_id。没有缩减预算点或查询数。

## LAION最终保存时磁盘保护退出

2026-09-14 21:12：supervisor session36835/PID8606已明确以exit1结束，原因是LAION全节点HNSW在最终gzip保存时触发/data剩余1.5GiB下限。三集release10 GATE、标签、LAION GT10开发选择以及Web/Y全量HNSW已完成；public正式矩阵尚未开始。未完成的LAION hnsw目录逐文件SHA校验转存到/root/acsg-artifacts/20260914_gate_new_ood_v1/laion10m_acsg_v1/hnsw，原位置为符号链接；保留全部10004480节点检查点和348345797字节的中断gzip。原base/NSG/历史模型与查询均未移动或删除。data空余恢复到2809409536字节。原编译程序可直接从全节点检查点完成保存与核验，之后preflight/三集192点576wall/分析继续。存储转移证据reviews/storage_recovery_20260914T2113/manifest.json。等待新监督进程终止信号后再读结果/故障日志。

## 2026-09-15完成

三集正式192点/576轮在同一boot一次完成；未使用正式L块恢复。LAION离线全节点检查点恢复验证通过。用户授权清理原归档后，所有本轮主索引已逐文件校验恢复项目/data目录，系统盘副本保留。见reviews/storage_closeout/manifest.json；不再接续历史PID。
