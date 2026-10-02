# E43运行中的磁盘余量处理

训练期间/data可用空间接近本版本预锁的10GiB底线。未修改训练源码、冻结配置或余盘阈值，也没有终止/重启任何native job。

仅将.venv_cpu中9861份有对应.py源码的可再生成__pycache__字节码归档至/tmp/acsg-e43-environment-bytecode-backup.tar.gz，逐文件SHA核验归档内容与原字节，再释放原缓存131.337MiB；归档约55.087MiB，原路径/大小/mtime/SHA均在[记录](reviews/environment_cache_relocation.json)。这些文件与E37–E42保护集及native依赖集无交集；源码、共享库、模型、图、GT、日志、查询输出均未删除或修改。归档可用于恢复缓存，通常也可由原.py自动再生成。

这项短暂CPU8压缩和I/O发生在Yandex训练期间，所以训练进程wall不作为无干扰速度对比或查询QPS。两个被测训练方法没有并行；原计数/检索结果与训练日程不依赖墙钟，最终全部轨迹/模型仍独立重放核验。
