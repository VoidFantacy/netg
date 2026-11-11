# E197新输出的无损存储

磁盘空间紧张，本轮实际timed raw数组、工作量和seed数组按窗口/阶段写入`packets.tar.zst`，原始字节逐文件SHA往返核验后删除本轮未封存临时副本；每条原路径、大小、SHA、archive member与payload SHA保存在`packet_archive.json`。旧实验文件不改。

新候选witness先解gzip，再将完整二进制payload入同一tar，以便跨方法压缩重复事件。完整候选ID、原生float评分、主返回与选中seed一个字节不少；保存原gzip文件SHA和payload SHA，不声称保留原gzip容器字节。只有该可逆表示变更的gzip包装不作为当前科学内容身份；实际timed raw数组全字节保持。

该存储合同在正式输出前制定。读取使用`scripts/archive.py:load_packets`，返回原路径到payload字节，witness直接解析二进制、不再次解gzip。原生JSON计时/环境/校验收据继续原路径。训练labels.gz、模型和角色输入保留原字节；临时大特征可由冻结输入/源码重建，其完整SHA与原生推断核验另存。
