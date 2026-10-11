# E176 外部资产与本地迁移边界

本快照提供代码、结果汇总、图和审计阅读入口；它不等于可直接复跑的完整数据包。原科学配置与收据保留服务器绝对路径，浏览副本只改文档链接。本说明没有启动或授权新实验、FIT、GT生成或距离计算。

完整登记见 [data preflight](../../entry_method_exploration/20261010_m5_residual_completion_curve_v1/reviews/data_preflight.json)、[FIT preflight](../../entry_method_exploration/20261010_m5_residual_completion_curve_v1/reviews/fit_preflight.json) 与 [编译收据](../../entry_method_exploration/20261010_m5_residual_completion_curve_v1/reviews/build.json)。以下是服务器资产身份提示，不是本地下载/替换指令。

| 类别 | 原位置与用途 |
|---|---|
| base向量 | `/data/netg/ACSG/benches/datasets/WebVid2.5M_light_v1/base.webvid2_5m.fvecs`；`YandexT2I_official10M_ip_v1/base.official_first10M.fvecs` 位于同datasets根。两集保持原raw-IP，不能改归一化/行序。 |
| 原主图 | `/data/netg/ACSG/indices/{dataset}_index/acosp_nsg.json`；这是native二进制索引，不能按文件扩展名当JSON。图携带base域与顺序身份。 |
| 公共窗口 | 原dataset下query/GT文件；E175 `inputs/{dataset}/queries.f32`、`gt.i32`、`window_rows.i64`。Web源10K，Yandex从公共100K取固定前10K；既有GT100，不是新GT。 |
| 合法TRAIN/teacher | `/data/netg/ACSG/entry_method_exploration/20260910_gt_topk_profiles_v1/inputs/{dataset}/fit/` 的query、`gt.i64`、源行；旧teacher responses、画像来源及历史role登记仍是依赖。 |
| GT10画像/原M5 | 原图内画像和Micro-HNSW live域；`/root/acsg-e172-storage-v2/campaign/m5/models/{dataset}/residual_joint.bin` 是原冻结M5表，未因发布重新拟合或搬迁。 |
| 新残差表 | E176 `models/{dataset}/pair.k{K}_L{L}.i32` 与 `route.k{K}_L{L}.i32`，共40小表和compiler manifest；本地是否携带以发布manifest为准。不能拿新路径冒充旧运行身份。 |
| 编译依赖 | `/root/acsg-e172-storage-v2/campaign/common/acsg_current.o`；`build/ACSG/libACSG.a`、`build/MRNN_Descent/libmrnndescent.a`、`build/faiss/faiss/libfaiss.a`；Faiss/header/json依赖、OpenBLAS/z/dl/OpenMP。原命令含`-march=native`，机器/ABI/浮点合同需另核。 |
| Python/资源 | 原分析用本地CPU venv与NumPy/Matplotlib、Noto CJK字体；正式原CPU15/T1、串行，资源和完整Batch wall合同见协议。复制源码不复制环境或进程资格。 |

迁移先建独立配置/新收据，保留冻结原件。核base/graph/query/GT/模型的完整SHA、维度、数量、dtype、行序、metric、角色和目标ID域；device/inode/stat随迁移改变，旧stat不能充当新文件核验。核本地source/library/编译器与加载后live域/word资格；不静默改`/data`或`/root`字符串重写历史锁。

只有阅读图、CSV和已有审计时，不需要加载大向量或执行native。若缺旧raw/teacher资产，应报告该复核缺口，不重建监督补齐。任何新训练、重测或确认需在资产检查之外取得新的执行范围；E176历史每集900秒增量授权已结束，不能自动延用。GT10默认与原M5保留，公共窗口已曝光，迁移后再测也不会变成新盲测。
