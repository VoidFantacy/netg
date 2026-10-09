# 原冻结 M5 构表源码与身份

这里的四份源码/manifest 是原 E172 已存在文件的逐字复制，用于阅读方法和追溯原表，不是新的训练、重新拟合或新的训练审计。E173 五档 L 复测直接复用原表，K1/K100 共用同一张表，没有根据这次公共测试结果换表。

- [实际构表器](compile_postings.py)：生成联合遗漏覆盖 token、全局整数 lazy greedy 和表导出。
- [原独立 TRAIN greedy 核验器](audit_train_greedy.py)：原冻结训练集合上的独立贪心重放逻辑；复制源码不表示本次又执行了训练核验。
- [Web 原 compile manifest](models/webvid2_5m_light_v1/compile_manifest.json) 与 [Yandex 原 compile manifest](models/yandex_t2i_official10M_ip_v1/compile_manifest.json)：保存原训练输入、表 SHA、容量、训练代理目标及阶段耗时。
- [本次在线 Posting 代码](../src/runtime.hpp) 与 [完整测试调用链](../src/benchmark_v2.cpp)：真实 GT10 路由、原 NSG 主搜索及补全成本。

原构表用每集 20000 条 TRAIN 查询、原 GT10 的实际三个标签和已计算的主搜索返回。Web 遗漏教师为 K1/L800 与 K100/L1000；Yandex 为 K1/L100 与 K100/L200。本次实际测试 L=200/400/800/1000/1200，各点使用同一原表；训练教师 L 和测试 L 保持各自身份。

对查询 i 的目标 t，遗漏 GT1 token 权重为 100，遗漏 GT100 token 权重为 1；同一个 (i,t) 同时属于两项遗漏时合并为 101。一个 token 只要被该查询三个标签中的任意一行覆盖就获得一次收益，不因另两行重复存它再加分。每行最多 8 个目标，在线读三行最多 24 个。全局 greedy 每次选当前新增整数收益最大的“标签槽位—目标 ID”，同收益按槽位、目标 ID 决定。

若 N=20000，整数覆盖目标值等于 `200N × ½(已覆盖 GT1 遗漏数/N + 已覆盖 GT100 遗漏数/(100N))`。100/1/101 使两项归一化 Recall 遗漏覆盖等权；这是固定训练反馈上的覆盖代理，不是测试 Recall 或总体改进证明。

| 原冻结表 | 字节 | SHA256 | 原构表脚本阶段秒数 |
|---|---:|---|---:|
| Web residual_joint.bin | 53099 | `d0310bdb136d45595a00c8697c170dc38b6bda07b0090cec64ba00db236dd7ff` | 16.402080515 |
| Yandex residual_joint.bin | 53369 | `032e0c74af93a3278a9b2203b4cf7b7058d29396653749311aeadc4361593d1c` | 19.314452390 |

上述约 16/19 秒是原 manifest 中构表脚本这一阶段的 wall，包含该脚本的主表和简单控制导出及阶段内输入读取/哈希；不是 C++ 编译耗时，也不是整个方法的训练总成本。它未覆盖此前 GT 监督生成、原 NSG 教师返回生成、所有其他拟合/构建/核验费用。原 manifest 的训练目标值、剩余控制和 `actual_merge_audit_pending` 都保留当时身份，不用后来复测覆盖旧记录。

复制源目录是 `/root/acsg-e172-storage-v2/campaign/m5/`。两个 Python 文件保留原相对目录假设，依赖原 config、训练输入和教师返回；这个目录不是可单独启动的训练包。公开包提供算法及计量来源，完整数据、图、表二进制和 native 库保留本地。

实际复制时逐项核对源和目标 SHA256；下面四项的目标 bytes 与原件完全相同。

| 复制目标（相对本目录） | 源 SHA256 | 目标 SHA256 |
|---|---|---|
| `compile_postings.py` | `b697df6fd698eedb805f03fb2402c22789e66a668f3a542d27d1bf7040827741` | `b697df6fd698eedb805f03fb2402c22789e66a668f3a542d27d1bf7040827741` |
| `audit_train_greedy.py` | `1e0f885bd7323d1124492103be698ec4b2510cddee1effee99bea2f2c2373dac` | `1e0f885bd7323d1124492103be698ec4b2510cddee1effee99bea2f2c2373dac` |
| `models/webvid2_5m_light_v1/compile_manifest.json` | `4253bb7a7483dcf774cd7b7af63fdf7489b4782e02d0bf2777bd910437ef30c2` | `4253bb7a7483dcf774cd7b7af63fdf7489b4782e02d0bf2777bd910437ef30c2` |
| `models/yandex_t2i_official10M_ip_v1/compile_manifest.json` | `855c57801f5ab45141c5b17620b875214f8c7cd5849b636a4205ea483215420a` | `855c57801f5ab45141c5b17620b875214f8c7cd5849b636a4205ea483215420a` |
