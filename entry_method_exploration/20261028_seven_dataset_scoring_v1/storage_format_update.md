# E191 存储格式修订（科学配置不变）

七集原448点/1344轮已全部计时并通过逐文件原包SHA及第二实现复核。冻结的唯一密集控制为541点/1623轮；补充原始文件预计2,239,861,113字节，当前根盘仅1,714,786,304字节可用，另保留0.7GiB余量。实际容量预检见reviews/storage_preflight.json。

仅将本轮尚未封存的actual timed四个raw字节流无损保存为各dataset的raw_packets.tar.zst，先全量逐文件SHA256往返核验，再替换原始存储；每个原文件的逻辑路径、字节数、时间戳和SHA记录在raw_packet_archive.json。采用POSIX tar与系统zstd 1.4.8，固定level6/T1/128MiB长窗口、帧校验。旧科学代码、模型、base、图、配置、全部原始轮次SHA与QPS、CSV及所有旧seal均不改。

每个密集dataset先完成原始计时、原包核验、第二实现与trace无损gzip，再顺序归档。归档、分析与训练均不与正式性能重叠。归档是证据存储适配，不是新方法、新测试或候选选择。

posthoc_scoring.py原件不改，由run_archived_posthoc.py仅适配读取；数据解码后逐文件SHA一致。跨窗口核验采用preseal_checks_v2.py，完整交付采用finalize_v4.py重新计算全部actual packet SHA，所有旧源版本与绑定保留。

读取/核验/还原：在/data/netg/ACSG，使用.venv_cpu/bin/python entry_method_exploration/20261028_seven_dataset_scoring_v1/scripts/packet_archive.py verify results coco核验；把verify换为restore可恢复逻辑raw路径（归档仍保留）。末尾追加目标目录可在独立位置还原。阶段名results或dense_controls；dataset替换为配置中的key。还原需要对应数据集的未压缩容量。归档由标准zstd -dc -M256MB与tar读取，支持脱离Python还原。

原freeze/protocol中“保留raw”指此前物理存储计划；本修订保持actual timed原始字节与全部可复核身份，最终报告明确当前归档形式。用户后续已明确授权完成后交付PDF，相关格式授权另见delivery_authorization_update.json。
