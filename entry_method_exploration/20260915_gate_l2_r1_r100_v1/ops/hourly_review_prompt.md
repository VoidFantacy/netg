用户后续调整：不必每小时都检查，也可估算结束时间再检查。已按实测耗时估算测试在2026-09-16约07:13结束，粗略范围05:30至09:00，下一次实际查看安排06:00；此前定时器仅等待，不读取实验进程/结果。之后保持每小时轻量检查直到完成。这不改变五集测试、绘图与分析的完整目标。

这是用户已授权的每小时后台检查，接续原会话，不是新实验。用户原话：“每隔一小时看一下跑完了吗？跑完就画图分析”。工作目录 /data/netg/ACSG；RUN=/data/netg/ACSG/entry_method_exploration/20260915_gate_l2_r1_r100_v1。无需询问是否继续，不要创建其他 agent 或新后台评测副本。

先读 AGENTS.md、当前 summary/spec/s-target 的 E97 说明和 RUN/handoff.md，核对 RUN/state.json、ops/hourly_status.json、后台服务及实际 /proc 进程。范围锁定为 WebVid、Yandex、Deep、SIFT、GIST，排除 LAION；只测 Recall@1/100 与真实单线程端到端 QPS。五方法 NSG、GT10-hard、固定 GT10-soft-t1、修正 GATE、完整 HNSW；800点、2400次计时。不要追加网格、重训或更换默认方法。

如果正式评测/训练/构图仍在运行，只做 CPU0 上的轻量只读状态检查，简短汇报，结束本轮；不要并发运行分析、大文件哈希或其他重任务。定时器下一小时会再检查。已有 acsg-e97-five-datasets.service 负责冻结流水线，真实 FAILED 不会盲目重试。遇到失败，先读具体日志，在原授权内修正可确认的实现/接入问题，保留旧产物并记录限定的身份修订；不把失败状态伪装为成功。不要停止或重启健康进程。

若 PLOTS_READY_PENDING_VISUAL_CHECK：确认十个 dataset/K 全部 PASS，数值分析 raw_results_verified.json PASS。实际打开 figures/recall_qps_k1.png、recall_qps_k100.png 和两种 K 的失败率图；核对五集、五方法、16预算点、坐标轴、图例、遮挡和计时范围，不能仅根据文件存在宣称图已检查。写 reviews/figures_visual_check.json，包含 status=PASS、实际查看的文件、核验说明、时间。若只完成评测而分析未完成，沿用现有冻结 analyze.py 并记录实际执行，不新增 ANN/QPS。

随后运行 /data/netg/ACSG/.venv_cpu/bin/python RUN/src/closeout.py（把 RUN 展开成绝对路径）。它写 report.md、complete.json、根四文档与历史90，并校验冻结产物。若当前已经 COMPLETE 则不要重复 closeout；继续下面的实际结果分析。

以 results/metrics.csv、recall_targets.csv、paired_queries.csv、wall_rounds.csv 和成本 JSON 为证据，写 RUN/analysis.md，详细比较 hard/soft/GATE 以及 NSG/HNSW：分别给出五集 K1/K100 在相同召回门槛下最快实测点的 QPS/实际Recall/预算、高召回端取舍、覆盖不到的门槛、三次计时波动、失败情况与训练/构建/标签成本；不把同L、monitor准确率、插值或单次QPS差值当作已证收益。明确 hard/soft 推荐的适用范围和证据限制；不根据 public test 调参或自动替换默认。将关键实测结论和分析链接加入 summary.md，s-target/spec/s-experiment 按职责同步。

最终报告保留 Yandex 14:09 前置检查失败、固定前10000行物化修正、15:20恢复和约70分钟等待中断的记录；70分钟不能算计算成本。必须引用 experiment_history/90a_yandex_test_prefix_fix.md 及 reviews/yandex_test_prefix_correction_v1/correction.json。181个原冻结产物先前已核验不变；新的 frozen_models.json 含授权的限定修订，不得恢复旧 hash。旧 E96/原100K query/GT、图、训练与结果均保留。GIST 原下载校验缺失、Web/Y 公共测试历史曝光、SIFT 新BIGANN接入等限制应保留。

closeout.py 当前模板不自动附上这份详细分析/历史90a：先备份生成的 report.md 与 complete.json 到 ops 的带时间修订目录，再给 report.md 添加 analysis.md/历史90a/修正链接及中断说明，并更新 complete.json 的 report_sha256，添加 analysis_sha256 和明确修订时间/原因；同步 state.json 的完成记录。保持 metrics_sha256 和原数据不变。更新历史90指向分析/历史90a，核对所有新增本地链接。

全部核验、图表与分析完成后，写 ops/analysis_done.json，status=PASS，记录 analysis.md 的 SHA256、图表核验位置、完成时间和输出路径。定时器会根据 COMPLETE + numeric PASS + visual PASS + analysis_done PASS 自动关闭；也可只关闭 acsg-e97-hourly-check.timer，不要停止自己的 acsg-e97-hourly-check.service。用中文给出自足的最终回复，包含关键五集结论和两张图/详细分析链接。不要发邮件或 Slack，不要声称已经完成任何未做的验证。
