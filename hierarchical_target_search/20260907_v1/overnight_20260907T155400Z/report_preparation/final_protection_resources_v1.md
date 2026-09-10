# 截止后保护与资源复核

PASS：7个小源码文件匹配截止前保护SHA；原CMake内容仍是完整前缀，增量仅为3个已接受target及其setup/include块；settings匹配既有P0复核SHA。本次未修改repo、编译或运行实验，未读真实GT/图/base/查询/NPZ内容。

注册任务共54个：COMPLETE 51，LAUNCH_FAILED 1，FAILED 2。
已启动重任务34个，记录的保守起止区间无正长度重叠；截止中断任务0。停止证据时间2026-09-07T23:00:00.312452+00:00，active/signals均为空。全/proc身份复核由root另做，本报告不替代它。

| 阶段 | 注册任务 | 有elapsed记录 | 记录任务耗时合计(s) | 重任务耗时合计(s) | 首任务到末任务跨度(s，含间隔) |
| --- | ---: | ---: | ---: | ---: | ---: |
| P0 | 1 | 1 | 36.160945 | 36.160945 | 36.161075 |
| P1 | 11 | 10 | 132.589100 | 88.390768 | 415.222578 |
| P2 | 14 | 14 | 584.874941 | 584.874941 | 6864.215516 |
| P3 | 28 | 28 | 904.225299 | 843.959238 | 5860.437508 |

阶段合计包含注册的验收、构建、失败尝试和诊断，不是完整训练成本；未注册的文档/小合成操作不在这54条台账内。缺少elapsed的启动失败保留null，没有补0。

最大记录rusage：p3_partition_yandex，37,355,416 KiB（35.624901 GiB）。最大轮询RSS：p3_partition_yandex，37,288,240 KiB（35.560837 GiB）。两者口径不同；轮询会漏掉间隔内峰值，rusage也不是整机并发总内存上界。

非COMPLETE记录均保留：
- p1_evaluator_build_v1: LAUNCH_FAILED, returncode=None, elapsed=None, error=[Errno 2] No such file or directory: 'cmake'
- p2_partition_webvid: FAILED, returncode=1, elapsed=28.123390608998307, error=None
- p2_partition_webvid_diagnostic_v2: FAILED, returncode=3, elapsed=28.123228991997166, error=None

当前/data可用空间17,894,608,896 bytes（16.665653 GiB）；RUN常规文件逻辑大小3,581,638,811 bytes（3.335661 GiB），按唯一inode的分配空间3,598,319,616 bytes。只用文件元数据统计，未跟随软链；统计发生在本报告写入前，root并发写报告可能改变总量。当前快照、任务结束磁盘采样都不能作为整晚资源最坏情况的严格上界。

Git status从1308行到1311行；新增3行，移除0行，新增删除状态0行。完整差异见JSON；status变化不等于完整文件内容保护证明。

主动删除文件：无。本任务无清理、reset、checkout或保护物删除；旧失败产物、日志及快照均保留。大输入未重新读取/校验，继续引用既有绑定证据。未写实验总结、三交接、state或gate。
