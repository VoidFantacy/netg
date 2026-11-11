# E187 自适应补全来源pilot

2026-10-28。用户授权实施E186首轮验证；固定COCO/Deep、真实K100，原46点/138完整T1批次；另冻6个GT10近邻L控制/18轮，共52点/156轮。当前状态以state.json为准，完成后以report_zh.md为结论入口。

- [事前协议](protocol.md)：范围、模型、网格、费用、停止条件与证据边界。
- [正式前冻结](freeze.json)：模型/源程序/binary/静态库/小输入SHA，大资产绑定。
- [中文详细报告](report_zh.md)与[六页图表PDF](ACSG_自适应残差补全_实验对比_20261028.pdf)。
- analysis/points.csv、paired.csv、discrete_comparisons.csv及query_metrics.csv.gz保存全部点和逐query证据。
- results保存实际timed包、原始轮收据和oracle通过状态。reviews保存构建/资格/正式日志、核验和过程记录。
- models保存全库区域/PQ显式布局、训练特征/标签、固定ridge权重及校准描述。原B32/原图/大向量沿E183原路径依赖，不复制或重建。
- source_before只备份本轮前根文档；E183–186原件、seal和科学字节保留。

正式测试必须实际1线程、CPU15，所有OMP/BLAS/MKL/NUMEXPR=1；一次只运行一个被测程序，不并发训练、标签或其他性能任务。脚本中已有环境/亲和性检查；offline编码8线程另记。

源码主线：prepare_backend.py → pilot.cpp features → train_selector.py → qualification → qualify_freeze.py → formal。输出目录要求全新，不能直接覆盖已完成科学结果；重跑另立新目录并重新绑定资产。analyse/report步骤从实际包读取，不重新跑主搜索。

冻结后新增的分析/报告代码不参与在线搜索；最终交付另存manifest与validation。原生B32计数Stats未插桩，不能读原JSON的0作为0精算，第二实现从实际包和表补算。原test已曝光，本轮不是盲确认，也没有实现E186完整动作开关或默认替换。

原46点首次分析在analysis_original_v1；补充控制按controls_v1/protocol.md及独立freeze执行，保持原模型/方法不变，后补窗口限制见报告。汇总技术失败、第一次PDF字体渲染失败均保留reviews/process_notes.md及原件。
